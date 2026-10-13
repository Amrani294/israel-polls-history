"""Make the site fully self-contained: download the fonts and the portraits once,
store them inside the site folder, and lock the Content-Security-Policy to the
site's own files.

After this runs, nothing the site shows comes from another server, so the only
way to change what visitors see is to change the files themselves.

Run from the site folder, on a computer with internet access (Python 3, standard library only):

    python3 tools/scripts/localize_assets.py .

It can be run again safely: files already downloaded are skipped.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

UA_FONTS = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")   # makes Google Fonts answer with woff2
UA_WIKI = "IsraelPollsHistory/1.0 (static site; one-time download of portrait thumbnails)"
FONT_CSS = ("https://fonts.googleapis.com/css2?family=Karantina:wght@300;400;700"
            "&family=IBM+Plex+Sans+Hebrew:wght@400;500;600;700&display=swap")
GOOGLE_LINKS = [
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n',
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n',
]
GOOGLE_CSS_RE = re.compile(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^"]*">\n')
LOCAL_CSS_LINK = '<link rel="stylesheet" href="assets/css/fonts.css">\n'
REMOTE_ORIGINS = ["https://fonts.googleapis.com", "https://fonts.gstatic.com",
                  "https://commons.wikimedia.org", "https://upload.wikimedia.org",
                  "https://thumb.wikimedia.org"]


def local_image_name(commons_file):
    """Stable local file name for a Commons file (shared with build_site_data.py)."""
    ext = os.path.splitext(commons_file)[1].lower()
    ext = ".jpg" if ext in (".jpg", ".jpeg") else ext
    return hashlib.md5(commons_file.encode("utf-8")).hexdigest() + ext


def get(url, ua, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def read_js(path):
    s = open(path, encoding="utf-8").read()
    head, _, rest = s.partition("window.")
    var, _, body = rest.partition(" = ")
    return head + "window." + var + " = ", json.loads(body.rstrip().rstrip(";"))


def write_js(path, prefix, obj):
    with open(path, "w", encoding="utf-8") as f:
        f.write(prefix)
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")


def fonts(site):
    out_dir = os.path.join(site, "assets", "fonts")
    os.makedirs(out_dir, exist_ok=True)
    css = get(FONT_CSS, UA_FONTS).decode("utf-8")
    urls = sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)))
    if not urls:
        raise SystemExit("Google Fonts returned no font files; nothing changed.")
    for u in urls:
        name = u.rsplit("/", 1)[1]
        dest = os.path.join(out_dir, name)
        if not os.path.exists(dest):
            data = get(u, UA_FONTS)
            open(dest, "wb").write(data)
        css = css.replace(u, "../fonts/" + name)
    open(os.path.join(site, "assets", "css", "fonts.css"), "w", encoding="utf-8").write(
        "/* downloaded from Google Fonts by tools/scripts/localize_assets.py (SIL Open Font License) */\n" + css)
    print("fonts: %d files" % len(urls))


def images(site):
    out_dir = os.path.join(site, "assets", "img", "people")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(site, "data", "people.js")
    prefix, people = read_js(path)
    failed = []
    for title, p in people.items():
        if not p.get("file"):
            continue
        name = local_image_name(p["file"])
        dest = os.path.join(out_dir, name)
        if not os.path.exists(dest):
            url = "https://commons.wikimedia.org/wiki/Special:FilePath/%s?width=330" % \
                urllib.request.quote(p["file"].replace(" ", "_"))
            try:
                data = get(url, UA_WIKI)
                if len(data) < 200:
                    raise ValueError("response too small")
                open(dest, "wb").write(data)
                time.sleep(0.2)          # be gentle with Wikimedia
            except Exception as err:     # keep the remote URL for this one
                failed.append((title, str(err)))
                continue
        p["img"] = "assets/img/people/" + name
    write_js(path, prefix, people)
    print("images: %d local, %d failed" % (sum(1 for p in people.values() if p.get("img", "").startswith("assets/")), len(failed)))
    for t, e in failed:
        print("  failed:", t, e)
    return not failed


def html(site, images_ok):
    for name in os.listdir(site):
        if not name.endswith(".html"):
            continue
        path = os.path.join(site, name)
        s = open(path, encoding="utf-8").read()
        for line in GOOGLE_LINKS:
            s = s.replace(line, "")
        if LOCAL_CSS_LINK not in s:
            s = GOOGLE_CSS_RE.sub(LOCAL_CSS_LINK, s)
        drop = REMOTE_ORIGINS if images_ok else REMOTE_ORIGINS[:2]
        for origin in drop:
            s = s.replace(" " + origin, "")
        open(path, "w", encoding="utf-8").write(s)
    print("html: fonts linked locally; CSP " + ("now allows only the site's own files" if images_ok
                                                 else "still allows Wikimedia for the images that failed"))


def main(site):
    fonts(site)
    ok = images(site)
    html(site, ok)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")

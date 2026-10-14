"""Make the site fully self-contained: download the fonts and the portraits once,
store them inside the site folder, and lock the Content-Security-Policy to the
site's own files.

After this runs, nothing the site shows comes from another server, so the only
way to change what visitors see is to change the files themselves.

Run from the site folder, on a computer with internet access (Python 3, standard library only):

    python3 tools/scripts/localize_assets.py .        (Windows: py tools/scripts/localize_assets.py .)

It can be run again safely: files already downloaded are skipped, so after new people are
added (for example a 2026 update) running it again downloads only the new portraits.
If Wikimedia refuses some downloads, the script waits and retries; whatever still fails
keeps loading from Wikimedia, and the CSP keeps allowing Wikimedia until a later run
gets everything.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

UA_FONTS = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")   # makes Google Fonts answer with woff2
UA_WIKI = ("IsraelPollsHistory/1.0 (https://pollsisraelhistory.netlify.app; "
           "one-time download of portrait thumbnails) python-urllib")
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


def get(url, ua, timeout=60, tries=4):
    """Download with retries: Wikimedia answers 429 when asked too fast."""
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as err:
            if err.code not in (429, 500, 502, 503, 504) or attempt == tries - 1:
                raise
            wait = int(err.headers.get("Retry-After", "0") or 0) or 5 * (attempt + 1)
            time.sleep(min(wait, 60))
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))


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
                time.sleep(0.5)          # be gentle with Wikimedia
            except Exception as err:     # keep the remote URL for this one
                failed.append((title, str(err)))
                continue
        p["img"] = "assets/img/people/" + name
    write_js(path, prefix, people)
    print("images: %d local, %d failed" % (sum(1 for p in people.values() if p.get("img", "").startswith("assets/")), len(failed)))
    for t, e in failed:
        print("  failed:", t, e)
    return not failed


def headers(site, images_ok):
    """Narrow the Netlify CSP in _headers the same way as the pages."""
    path = os.path.join(site, "_headers")
    if not os.path.exists(path):
        return
    s = open(path, encoding="utf-8").read()
    for origin in (REMOTE_ORIGINS if images_ok else REMOTE_ORIGINS[:2]):
        s = s.replace(" " + origin, "")
    open(path, "w", encoding="utf-8").write(s)


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
    headers(site, ok)
    print("done. Check the site in the browser (open index.html), then commit the changes.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")

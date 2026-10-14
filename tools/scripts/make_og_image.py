"""Render the link-preview image (assets/img/og.png, 1200x630) shown when the
site is shared on WhatsApp, Facebook, X, Telegram and similar.

The image is drawn by the site's own code (the hemicycle from common.js and the
latest election in data/elections.js), so it stays in the site's style.

Run from the site folder (needs Python 3 + Playwright with Chromium):

    python3 tools/scripts/make_og_image.py .

Fonts are loaded from Google Fonts. Without internet access, pass a folder
with the woff2 files (kar_he, kar_lat, plex500_he, plex500_lat):

    python3 tools/scripts/make_og_image.py . --font-dir /path/to/fonts
"""
import argparse
import os
import pathlib
import tempfile

from playwright.sync_api import sync_playwright

GOOGLE = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Karantina:wght@700'
          '&family=IBM+Plex+Sans+Hebrew:wght@500&display=swap">')

LOCAL_FACES = """
@font-face { font-family: Karantina; font-weight: 700; src: url("{d}/kar_he.woff2"); unicode-range: U+0590-05FF, U+200C-2010; }
@font-face { font-family: Karantina; font-weight: 700; src: url("{d}/kar_lat.woff2"); unicode-range: U+0000-00FF, U+2000-206F; }
@font-face { font-family: "IBM Plex Sans Hebrew"; font-weight: 500; src: url("{d}/plex500_he.woff2"); unicode-range: U+0590-05FF, U+200C-2010; }
@font-face { font-family: "IBM Plex Sans Hebrew"; font-weight: 500; src: url("{d}/plex500_lat.woff2"); unicode-range: U+0000-00FF, U+2000-206F; }
"""

PAGE = """<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">{fonts}
<style>{faces}
html, body {{ margin: 0; }}
body {{ width: 1200px; height: 630px; overflow: hidden; background: #18203a; color: #fff;
       font-family: "IBM Plex Sans Hebrew", sans-serif; position: relative; }}
.band {{ position: absolute; inset: auto 0 0 0; height: 14px;
        background: linear-gradient(90deg, #c42a3c 0 33%, #e9e7ef 33% 67%, #2350b8 67% 100%); }}
.txt {{ position: absolute; top: 70px; right: 72px; width: 560px; }}
h1 {{ font-family: Karantina, sans-serif; font-weight: 700; font-size: 132px; line-height: .86; margin: 0; letter-spacing: -.01em; }}
p {{ font-size: 30px; line-height: 1.35; color: #dfe3ee; margin: 30px 0 0; }}
.url {{ position: absolute; bottom: 44px; right: 72px; font-size: 24px; color: #9aa3b8; direction: ltr; }}
.parl {{ position: absolute; left: 50px; top: 150px; width: 520px; }}
.parl svg {{ width: 100%; height: auto; display: block; }}
.parl .sum {{ display: none; }}
.parl text {{ display: none; }}
.cap {{ position: absolute; left: 50px; top: 445px; width: 520px; text-align: center; font-size: 22px; color: #9aa3b8; }}
</style></head><body>
<div class="txt"><h1>היסטוריית<br>הסקרים<br>של ישראל</h1>
<p>מה חזו הסקרים, ומה קרה בקלפי: תוצאות, רשימות וגושים בכל מערכת בחירות לכנסת</p></div>
<div class="parl" id="parl"></div><div class="cap" id="cap"></div>
<div class="url">pollsisraelhistory.netlify.app</div><div class="band"></div>
<script src="data/meta.js"></script><script src="data/elections.js"></script><script src="data/people.js"></script>
<script src="assets/js/common.js"></script>
<script>
var withResults = App.ELECTIONS.filter(function (e) {{ return e.lists.some(function (l) {{ return l.seats > 0; }}); }});
var e = withResults[0];
document.getElementById("parl").innerHTML = App.hemicycle(e, {{ center: false }});
document.getElementById("cap").textContent = App.electionTitle(e) + ", " + App.shortWhen(e);
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?", default=".")
    ap.add_argument("--font-dir")
    args = ap.parse_args()
    site = pathlib.Path(args.site).resolve()
    if args.font_dir:
        fonts, faces = "", LOCAL_FACES.replace("{d}", pathlib.Path(args.font_dir).resolve().as_uri())
    else:
        fonts, faces = GOOGLE, ""
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=site)
    os.close(fd)
    try:
        pathlib.Path(tmp).write_text(PAGE.format(fonts=fonts, faces=faces), encoding="utf-8")
        out = site / "assets" / "img" / "og.png"
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page(viewport={"width": 1200, "height": 630})
            page.goto(pathlib.Path(tmp).as_uri())
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            page.screenshot(path=str(out))
            b.close()
        print("wrote", out)
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    main()

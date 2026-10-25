"""Instagram content for "היסטוריית הסקרים של ישראל".

Every number comes from the site's own data files (data/*.js in the main branch);
nothing is typed in by hand. Posts are 1080x1080 JPEG, reels 1080x1920 MP4.

usage:
  python3 gen.py SITE_DIR FONT_DIR OUT_DIR list            # catalog ids
  python3 gen.py SITE_DIR FONT_DIR OUT_DIR render ID [ID...]
  python3 gen.py SITE_DIR FONT_DIR OUT_DIR caption ID      # prints the caption

FONT_DIR holds Karantina-*.ttf and IBMPlexSansHebrew-*.ttf (Google Fonts, OFL).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SITE_URL = "pollsisraelhistory.netlify.app"
OUTLETS = ["11", "12", "13", "MAARIV", "HAARETZ"]
OUTLET_HE = {"11": "כאן 11", "12": "חדשות 12", "13": "חדשות 13", "MAARIV": "מעריב", "HAARETZ": "הארץ"}
PRED_HE = {"11": "ערוץ 1", "12": "ערוץ 2", "13": "ערוץ 10"}
OLD = {"2009", "2013", "2015"}
MONTHS = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
# Required by s. 16e(h) of the Elections (Propaganda) Law when an old poll is republished
# during the ban period; shown prominently on every 2026 item.
BAN_NOTE = ("הסקרים פורסמו עד 23.10.2026, לפני תקופת איסור הפרסום. הם אינם עדכניים, "
            "ואין ללמוד מהם על דפוסי הצבעה או על עמדות הציבור ביום הפרסום.")
TAGS = "#סקרים #בחירות #פוליטיקה #ישראל #כנסת"


# ------------------------------------------------------------------ data
def load_js(path):
    s = open(path, encoding="utf-8").read()
    i = min(x for x in (s.find("["), s.find("{")) if x >= 0)
    j = max(s.rfind("]"), s.rfind("}"))
    return json.loads(s[i:j + 1])


class Data:
    def __init__(self, site):
        self.E = load_js(os.path.join(site, "data/elections.js"))
        self.P = load_js(os.path.join(site, "data/polls.js"))
        self.by = {e["key"]: e for e in self.E}

    def results(self):
        return [e for e in self.E if any((l.get("seats") or 0) > 0 for l in e["lists"])]


STOPS = [(-3, (142, 22, 40)), (-2, (196, 42, 60)), (-1, (160, 52, 114)), (0, (123, 63, 168)),
         (1, (79, 72, 176)), (2, (35, 80, 184)), (3, (22, 51, 122))]


def party_color(lst):
    """Same formula as App.partyColor in assets/js/common.js."""
    pos = lst.get("position") or {}
    if pos.get("lo") is None:
        return "#a7adb7"
    x = (pos["lo"] + pos["hi"]) / 2
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if a <= x <= b:
            t = (x - a) / (b - a)
            return "rgb(%d,%d,%d)" % tuple(round(u + (v - u) * t) for u, v in zip(ca, cb))
    return "rgb(142,22,40)" if x < -3 else "rgb(22,51,122)"


def outlet_name(e, o):
    return PRED_HE[o] if e["key"] in OLD and o in PRED_HE else OUTLET_HE[o]


def when(e):
    y, m, _ = e["date"].split("-")
    return MONTHS[int(m) - 1] + " " + y


def fmt(v):
    if v is None:
        return "—"
    v = round(v, 1)
    return str(int(v)) if v == int(v) else "%.1f" % v


def signed(v):
    v = round(v, 1)
    if v == 0:
        return "0"
    return ("+" if v > 0 else "−") + fmt(abs(v))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


# ------------------------------------------------------------------ metrics (as on the site)
def poll_score(e, p):
    """accuracy.js pollScore: half the sum of absolute differences; untracked lists = one group."""
    seats = {l["name"]: l["seats"] for l in e["lists"]}
    s = tp = tr = 0
    for n in e["tracked"]:
        v = p["values"].get(n)
        if v is None:
            return None
        s += abs(v - seats[n]); tp += v; tr += seats[n]
    s += abs((p["total"] - tp) - (120 - tr))
    return s / 2


def exit_score(e, x):
    s = 0
    for l in e["lists"]:
        v = x["seats"].get(l["name"]) or 0
        if not v and not l["seats"]:
            continue
        s += abs(v - l["seats"])
    return s / 2


def last_polls(D, e):
    """Per outlet: mean score of its last poll(s) in the window (accuracy.js lastPolls + cellFor)."""
    out = []
    for o in OUTLETS:
        ps = [p for p in D.P if p["e"] == e["key"] and p["outlet"] == o]
        if not ps:
            continue
        last = max(p["end"] for p in ps)
        sc = [poll_score(e, p) for p in ps if p["end"] == last]
        sc = [x for x in sc if x is not None]
        if sc:
            out.append({"o": o, "date": last, "moved": sum(sc) / len(sc), "n": len(sc)})
    return sorted(out, key=lambda r: r["moved"])


def compare_rows(e, limit):
    rows = []
    for l in e["lists"]:
        avg = (l.get("polls") or {}).get("overall")
        if avg is None or l["name"] not in e["tracked"]:
            continue
        rows.append({"l": l, "avg": avg, "res": l["seats"] or 0, "diff": (l["seats"] or 0) - avg})
    rows.sort(key=lambda r: -max(r["avg"], r["res"]))
    return rows[:limit]


def src_line(D, e):
    os_ = [o for o in OUTLETS if any(p["e"] == e["key"] and p["outlet"] == o for p in D.P)]
    names = [outlet_name(e, o) for o in os_]
    return "מקור: סקרי " + (", ".join(names[:-1]) + " ו" + names[-1] if len(names) > 1 else names[0]) + "; ועדת הבחירות"


def le(name):
    """Hebrew prefix "to": ל + ה at the start of a name merges (לליכוד, not להליכוד)."""
    return "ל" + (name[1:] if name.startswith("ה") else name)


def joined(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " ו" + names[-1]


def date_he(iso):
    y, m, d = iso.split("-")
    return "%d.%d.%s" % (int(d), int(m), y)


# ------------------------------------------------------------------ page shell
LOGO = ('<svg viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#18203a"/>'
        '<path d="M8 44a24 24 0 0 1 24-24v24z" fill="#c42a3c"/><path d="M32 20a24 24 0 0 1 24 24H32z" fill="#2350b8"/>'
        '<rect x="8" y="46" width="48" height="4" rx="2" fill="#fff"/></svg>')


def shell(font_dir, w, h, css, body, script=""):
    f = lambda n: "file://" + os.path.join(font_dir, n)
    faces = "".join(
        '@font-face{font-family:"%s";src:url("%s");font-weight:%d;}' % (fam, f(fn), wt)
        for fam, fn, wt in [("Karantina", "Karantina-Regular.ttf", 400), ("Karantina", "Karantina-Bold.ttf", 700),
                            ("Plex", "IBMPlexSansHebrew-Regular.ttf", 400), ("Plex", "IBMPlexSansHebrew-Medium.ttf", 500),
                            ("Plex", "IBMPlexSansHebrew-SemiBold.ttf", 600), ("Plex", "IBMPlexSansHebrew-Bold.ttf", 700)])
    base = """
:root{--paper:#f3f4f7;--slip:#fff;--ink:#18203a;--ink-2:#4a5268;--mute:#6b7385;--rule:#d8dce4;--rule-2:#e8eaef;
--right:#2350b8;--left:#c42a3c;--centre:#7b3fa8;--flag:#fff4cc;--flag-b:#e9d48a;}
*{box-sizing:border-box}
html,body{margin:0;width:%dpx;height:%dpx;overflow:hidden}
body{direction:rtl;background:var(--paper);color:var(--ink);font-family:Plex,sans-serif;position:relative}
.d{font-family:Karantina,Plex,sans-serif}
.band{background:var(--ink);color:#fff;display:flex;align-items:center;gap:18px;position:relative}
.band::after{content:"";position:absolute;inset:auto 0 0 0;height:10px;
  background:linear-gradient(90deg,var(--left) 0 33.3%%,var(--centre) 33.3%% 66.6%%,var(--right) 66.6%% 100%%)}
.band .logo svg{display:block;width:100%%;height:auto}
.band .brand{font-family:Karantina;font-weight:700;line-height:1;white-space:nowrap}
.band .tag{margin-inline-start:auto;border:2px solid rgba(255,255,255,.4);border-radius:999px;white-space:nowrap;font-weight:500;color:#dfe3ee}
.slip{display:inline-flex;align-items:center;justify-content:center;background:#fff;border:1px solid var(--rule);
  border-radius:4px;font-family:Karantina;font-weight:700;line-height:1;position:relative;
  box-shadow:0 1px 0 rgba(24,32,58,.08),0 6px 18px -10px rgba(24,32,58,.35)}
.slip::after{content:"";position:absolute;inset:auto 0 0 0;height:6px;background:var(--pc);border-radius:0 0 4px 4px}
.ban{background:var(--flag);border:2px solid var(--flag-b);border-radius:8px;color:var(--ink);font-weight:600}
""" % (w, h)
    return ('<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>%s%s%s</style></head>'
            '<body>%s<script>%s</script></body></html>') % (faces, base, css, body, script)


POST_CSS = """
.band{height:118px;padding:0 60px 10px}
.band .logo{width:62px}.band .brand{font-size:50px}.band .tag{font-size:25px;padding:4px 20px}
.main{position:absolute;top:118px;bottom:0;inset-inline:0;padding:40px 60px 0}
h1{font-family:Karantina;font-weight:700;font-size:100px;line-height:.88;margin:0;letter-spacing:-.01em}
h1 em{font-style:normal;color:var(--hl,var(--left))}
.sub{font-size:28px;line-height:1.4;color:var(--ink-2);margin:14px 0 0;font-weight:500}
.foot{position:absolute;bottom:26px;inset-inline:60px;display:flex;justify-content:space-between;align-items:baseline;
  font-size:22px;color:var(--mute)}
.foot b{font-family:Karantina;font-size:34px;color:var(--ink);font-weight:700;direction:ltr}
.legend{display:flex;gap:28px;font-size:22px;color:var(--ink-2);margin:22px 0 10px;font-weight:500}
.legend i{display:inline-block;width:30px;height:16px;vertical-align:-2px;margin-inline-end:8px;border-radius:2px}
.legend .p i{background:repeating-linear-gradient(135deg,#9aa1b0 0 4px,transparent 4px 8px);border:2px solid #9aa1b0}
.legend .r i{background:var(--ink)}
.rows{display:flex;flex-direction:column;gap:9px}
.row{display:grid;grid-template-columns:92px 200px 1fr;align-items:center;gap:16px}
.row .slip{height:50px;font-size:34px;padding-bottom:6px}
.row .nm{font-size:23px;font-weight:600;line-height:1.15}
.bars{display:flex;flex-direction:column;gap:5px}
.bar{display:flex;align-items:center;gap:10px;height:20px}
.bar span{height:100%;border-radius:2px}
.bar .pp{background:repeating-linear-gradient(135deg,var(--pc) 0 4px,transparent 4px 9px);border:2px solid var(--pc);opacity:.75}
.bar .rr{background:var(--pc)}
.bar b{font-family:Karantina;font-size:30px;line-height:1;font-weight:700}
.bar .pv{color:var(--mute)}
.row.hot{background:#fff;border-radius:8px;box-shadow:0 0 0 3px var(--ink);padding:4px 8px;margin:0 -8px}
.card{background:#fff;border:1px solid var(--rule);border-radius:10px;box-shadow:0 6px 18px -10px rgba(24,32,58,.35)}
"""


def post_shell(font_dir, tag, body, foot_left="", hl=None):
    band = ('<div class="band"><span class="logo">%s</span><span class="brand">היסטוריית הסקרים של ישראל</span>'
            '<span class="tag">%s</span></div>') % (LOGO, esc(tag))
    foot = '<div class="foot"><span>%s</span><b>%s</b></div>' % (foot_left, SITE_URL)
    css = POST_CSS + (":root{--hl:%s}" % hl if hl else "")
    return shell(font_dir, 1080, 1080, css, band + '<div class="main">' + body + "</div>" + foot)


def slip(l):
    return '<span class="slip" style="--pc:%s">%s</span>' % (party_color(l), esc(l["letters"]))


# ------------------------------------------------------------------ posts
def post_gap(D, fd, key):
    e = D.by[key]
    rows = compare_rows(e, 9)
    big = max(rows, key=lambda r: abs(r["diff"]))
    mx = max(max(r["avg"], r["res"]) for r in rows)
    if big["diff"] < 0:
        title = '<h1><em>%s</em>:<br>%s מנדטים מתחת לסקרים</h1>' % (esc(big["l"]["name"]), fmt(-big["diff"]))
    else:
        title = '<h1><em>%s</em>:<br>%s מנדטים מעל הסקרים</h1>' % (esc(big["l"]["name"]), fmt(big["diff"]))
    sub = '<p class="sub">ממוצע הסקרים בשלושת החודשים שלפני הבחירות, מול התוצאה בקלפי</p>'
    leg = '<div class="legend"><span class="p"><i></i>ממוצע הסקרים</span><span class="r"><i></i>התוצאה</span></div>'
    out = []
    for r in rows:
        w = lambda v: "%.1f%%" % (82 * v / mx)
        out.append(
            '<div class="row%s" style="--pc:%s">%s<span class="nm">%s</span><div class="bars">'
            '<div class="bar"><span class="pp" style="width:%s"></span><b class="pv">%s</b></div>'
            '<div class="bar"><span class="rr" style="width:%s"></span><b>%s</b></div></div></div>'
            % (" hot" if r is big else "", party_color(r["l"]), slip(r["l"]), esc(r["l"]["name"]),
               w(r["avg"]), fmt(r["avg"]), w(r["res"]) if r["res"] else "0", fmt(r["res"])))
    body = title + sub + leg + '<div class="rows">' + "".join(out) + "</div>"
    html = post_shell(fd, "הכנסת ה-%s · %s" % (e["knesset"], when(e)), body,
                      src_line(D, e), party_color(big["l"]))
    cap = ("%s, %s: בממוצע הסקרים, %s %s מנדטים. בקלפי: %s.\n\n"
           "ככה נראה ממוצע הסקרים של שלושת החודשים האחרונים מול התוצאה, רשימה אחרי רשימה.\n\n"
           "כל הסקרים, כל המערכות מ-2009 והשוואה מלאה באתר. הקישור בביו 🗳️\n\n%s"
           % ("הבחירות לכנסת ה-" + e["knesset"], when(e), le(big["l"]["name"]), fmt(big["avg"]), fmt(big["res"]), TAGS))
    return html, cap


def post_accuracy(D, fd, key):
    e = D.by[key]
    rows = last_polls(D, e)
    best = rows[0]
    mx = max(r["moved"] for r in rows)
    tied = [outlet_name(e, r["o"]) for r in rows if abs(r["moved"] - best["moved"]) < 1e-9]
    if len(tied) == 1:
        title = '<h1>הסקר האחרון של<br><em>%s</em> היה הכי קרוב</h1>' % esc(tied[0])
    elif len(tied) == len(rows):
        title = '<h1>כל הגופים פספסו<br>ב-<em>%s</em> מנדטים</h1>' % fmt(best["moved"])
    else:
        title = '<h1>הכי קרובים:<br><em>%s</em></h1>' % esc(joined(tied))
    sub = '<p class="sub">כמה מנדטים צריך להזיז בסקר האחרון של כל גוף כדי להגיע לתוצאה</p>'
    out = []
    for i, r in enumerate(rows):
        out.append(
            '<div class="arow%s"><div class="on"><b>%s</b><span>%s%s</span></div>'
            '<div class="abar"><span style="width:%.1f%%"></span></div><b class="av">%s</b></div>'
            % (" best" if i == 0 else "", esc(outlet_name(e, r["o"])), date_he(r["date"]),
               " · ממוצע %d סקרים מאותו יום" % r["n"] if r["n"] > 1 else "", 78 * r["moved"] / mx, fmt(r["moved"])))
    css = """
.alist{margin-top:34px;display:flex;flex-direction:column;gap:16px}
.arow{display:grid;grid-template-columns:260px 1fr 110px;align-items:center;gap:18px;background:#fff;border:1px solid var(--rule);
  border-radius:8px;padding:14px 22px;box-shadow:0 6px 18px -12px rgba(24,32,58,.35)}
.arow .on b{display:block;font-family:Karantina;font-size:46px;line-height:.95}
.arow .on span{font-size:20px;color:var(--mute)}
.abar{height:26px;background:var(--rule-2);border-radius:3px;overflow:hidden}
.abar span{display:block;height:100%;background:#9aa1b0;margin-inline-start:0}
.arow .av{font-family:Karantina;font-size:64px;line-height:1;text-align:left}
.arow.best{box-shadow:0 0 0 4px var(--ink)}
.arow.best .abar span{background:var(--centre)}
.unit{font-size:22px;color:var(--mute);margin-top:14px}
"""
    if len(rows) >= 5 or any(r["n"] > 1 for r in rows):
        css += """.alist{margin-top:22px;gap:10px}.arow{padding:8px 22px}.arow .on b{font-size:38px}
.arow .on span{font-size:18px}.arow .av{font-size:54px}.abar{height:22px}"""
    body = ("<style>%s</style>" % css) + title + sub + '<div class="alist">' + "".join(out) + "</div>" + \
        '<div class="unit">המספר = מנדטים שהוזזו (חצי מסכום הפערים בכל הרשימות). פחות = מדויק יותר.</div>'
    html = post_shell(fd, "הכנסת ה-%s · %s" % (e["knesset"], when(e)), body, "החישוב המלא בעמוד \"דיוק הסוקרים\"", "#7b3fa8")
    worst = rows[-1]
    lead = ("הסקר האחרון של %s היה הכי קרוב: %s מנדטים מהתוצאה." % (tied[0], fmt(best["moved"]))) if len(tied) == 1 else \
        ("הכי קרובים היו %s, %s מנדטים מהתוצאה." % (joined(tied), fmt(best["moved"]))) if len(tied) < len(rows) else \
        ("הסקר האחרון של כל אחד מהגופים (%s) היה במרחק של %s מנדטים מהתוצאה. תיקו מושלם." % (joined(tied), fmt(best["moved"])))
    if worst["moved"] > best["moved"]:
        lead += " הכי רחוק: %s, %s מנדטים." % (outlet_name(e, worst["o"]), fmt(worst["moved"]))
    cap = ("מי צדק בבחירות של %s?\n\n%s\n\nהמדד: כמה מנדטים צריך להזיז בסקר כדי לקבל את מה שקרה בקלפי. "
           "הטבלה המלאה, לכל מערכות הבחירות מ-2009, בעמוד \"דיוק הסוקרים\" באתר. הקישור בביו 📊\n\n%s" % (when(e), lead, TAGS))
    return html, cap


def post_exits(D, fd, key):
    e = D.by[key]
    xs = sorted(({"x": x, "moved": exit_score(e, x)} for x in e["exitPolls"]), key=lambda r: r["moved"])
    best = xs[0]
    name = lambda x: x["actual"].split(" (")[0]
    top = sorted((l for l in e["lists"] if l["seats"]), key=lambda l: -l["seats"])[:5]
    head = "<tr><th></th><th>בקלפי</th>" + "".join("<th>%s</th>" % esc(name(r["x"])) for r in xs) + "</tr>"
    trs = []
    for l in top:
        tds = []
        for r in xs:
            v = r["x"]["seats"].get(l["name"]) or 0
            d = v - l["seats"]
            tds.append('<td>%s<small class="%s">%s</small></td>' % (fmt(v), "up" if d > 0 else ("dn" if d < 0 else "eq"), signed(d) if d else "בול"))
        trs.append('<tr><td class="ln">%s<span>%s</span></td><td class="res">%s</td>%s</tr>' % (slip(l), esc(l["name"]), fmt(l["seats"]), "".join(tds)))
    score = "<tr class=\"sc\"><td>מנדטים שהוזזו</td><td></td>" + "".join("<td>%s</td>" % fmt(r["moved"]) for r in xs) + "</tr>"
    css = """
table{width:100%;border-collapse:separate;border-spacing:0;margin-top:24px;background:#fff;border:1px solid var(--rule);border-radius:10px;
  box-shadow:0 6px 18px -10px rgba(24,32,58,.35);overflow:hidden}
th{font-size:22px;font-weight:600;color:var(--ink-2);padding:14px 10px;border-bottom:2px solid var(--ink);text-align:center}
td{padding:6px 10px;border-bottom:1px solid var(--rule-2);text-align:center;font-family:Karantina;font-size:46px;line-height:1;font-weight:700}
td.ln{display:flex;align-items:center;gap:14px;font-family:Plex;font-size:22px;font-weight:600;text-align:right}
td.ln .slip{height:44px;min-width:76px;font-size:30px;padding-bottom:6px}
td.res{background:#eef0f5}
td small{display:block;direction:ltr;unicode-bidi:isolate;font-family:Plex;font-size:17px;font-weight:600;margin-top:2px}
small.up{color:var(--right)}small.dn{color:var(--left)}small.eq{color:#2f8a4a}
tr.sc td{border-bottom:0;background:var(--ink);color:#fff;font-size:44px}
tr.sc td:first-child{font-family:Plex;font-size:22px;text-align:right;padding-inline-start:20px}
"""
    tied = [name(r["x"]) for r in xs if abs(r["moved"] - best["moved"]) < 1e-9]
    if len(tied) == 1:
        title = "<h1>המדגמים בלילה ההוא:<br><em>%s</em> הכי מדויק</h1>" % esc(tied[0])
    else:
        title = "<h1>המדגמים בלילה ההוא:<br>הכי מדויקים: <em>%s</em></h1>" % esc(joined(tied))
    sub = '<p class="sub">הגרסה האחרונה של כל מדגם באותו לילה, מול התוצאה הרשמית</p>'
    body = ("<style>%s</style>" % css) + title + sub + "<table>" + head + "".join(trs) + score + "</table>"
    html = post_shell(fd, "הכנסת ה-%s · %s" % (e["knesset"], when(e)), body, "מקור: כתבות החדשות מליל הבחירות; ועדת הבחירות", "#7b3fa8")
    cap = ("ליל הבחירות, %s: כמה קרובים היו המדגמים?\n\n%s, %s מנדטים מהתוצאה. "
           "בטבלה: חמש הרשימות הגדולות, הגרסה האחרונה של כל מדגם באותו לילה, מול התוצאה הרשמית.\n\n"
           "כל המדגמים והתוצאות מ-2009 באתר. הקישור בביו 🗳️\n\n%s" % (when(e), ("המדגם של %s היה הכי מדויק" % tied[0]) if len(tied) == 1 else ("המדגמים של %s היו הכי מדויקים" % joined(tied)), fmt(best["moved"]), TAGS))
    return html, cap


def post_2026_avg(D, fd):
    e = D.by["2026"]
    rows = sorted((l for l in e["lists"] if (l.get("polls") or {}).get("overall")), key=lambda l: -l["polls"]["overall"])
    mx = rows[0]["polls"]["overall"]
    out = []
    for l in rows:
        v = l["polls"]["overall"]
        out.append('<div class="r6" style="--pc:%s">%s<span class="nm">%s</span><div class="b6"><span style="width:%.1f%%"></span><b>%s</b></div></div>'
                   % (party_color(l), slip(l), esc(l["name"]), 80 * v / mx, fmt(v)))
    css = """
h1{font-size:84px}
.rows6{margin-top:20px;display:flex;flex-direction:column;gap:5px}
.r6{display:grid;grid-template-columns:80px 300px 1fr;align-items:center;gap:14px}
.r6 .slip{height:36px;font-size:26px;padding-bottom:5px}
.r6 .nm{font-size:21px;font-weight:600;white-space:nowrap}
.b6{display:flex;align-items:center;gap:10px;height:24px}
.b6 span{height:100%;background:var(--pc);border-radius:2px}
.b6 b{font-family:Karantina;font-size:32px;line-height:1}
.ban{position:absolute;bottom:78px;inset-inline:60px;padding:12px 18px;font-size:19px;line-height:1.4}
"""
    n = sum(1 for p in D.P if p["e"] == "2026")
    title = "<h1>ממוצע הסקרים לכנסת ה-26</h1>"
    sub = '<p class="sub">%d סקרים של כאן 11, חדשות 12, חדשות 13 ומעריב, %s עד %s. ממוצע לכל גוף, ואז ממוצע של הגופים.</p>' % (
        n, date_he(e["windowStart"]), date_he(e["lastPoll"]))
    body = ("<style>%s</style>" % css) + title + sub + '<div class="rows6">' + "".join(out) + "</div>" + \
        '<div class="ban">⚠ %s</div>' % esc(BAN_NOTE)
    html = post_shell(fd, "הכנסת ה-26 · אוקטובר 2026", body, "מקור: סקרים שפורסמו עד 23.10.2026", "#7b3fa8")
    cap = ("ככה נראו הסקרים לכנסת ה-26: ממוצע של %d סקרים מ-%s עד %s.\n\n"
           "⚠️ %s\n\nביום שלישי נדע כמה הם צדקו. בינתיים, באתר: כל סקר עם המקור שלו, ומה קרה לסקרים במערכות הקודמות. הקישור בביו 📊\n\n%s"
           % (n, date_he(e["windowStart"]), date_he(e["lastPoll"]), BAN_NOTE, "#בחירות2026 " + TAGS))
    return html, cap


def post_2026_blocs(D, fd):
    e = D.by["2026"]
    bo = e["blocs"]["pollsByOutlet"]
    rows = [("כל הגופים", e["blocs"]["polls"], e["blocs"]["pollsUsed"])] + \
        [(OUTLET_HE[o], bo[o], bo[o]["n"]) for o in ["11", "12", "13", "MAARIV"] if o in bo]
    out = []
    for name, d, n in rows:
        c, o = d["C"], d["O"]
        out.append('<div class="br%s"><div class="bn"><b>%s</b><span>%d סקרים</span></div><div class="bb">'
                   '<span class="c" style="width:%.2f%%">%s</span><span class="o" style="width:%.2f%%">%s</span></div></div>'
                   % (" all" if name == "כל הגופים" else "", esc(name), n, 100 * c / 120, fmt(c), 100 * o / 120, fmt(o)))
    css = """
.leg2{display:flex;gap:30px;margin-top:26px;font-size:23px;font-weight:600}
.leg2 i{display:inline-block;width:26px;height:18px;border-radius:2px;margin-inline-end:8px;vertical-align:-2px}
.leg2 .c i{background:var(--ink)}.leg2 .o i{background:#b9bfcc}
.blist{position:relative;margin-top:16px;display:flex;flex-direction:column;gap:12px}
.br{display:grid;grid-template-columns:200px 1fr;align-items:center;gap:18px}
.bn b{display:block;font-family:Karantina;font-size:42px;line-height:.95}.bn span{font-size:19px;color:var(--mute)}
.bb{display:flex;height:52px;border-radius:4px;overflow:hidden;position:relative}
.bb span{display:flex;align-items:center;padding:0 14px;font-family:Karantina;font-weight:700;font-size:40px}
.bb .c{background:var(--ink);color:#fff}.bb .o{background:#b9bfcc;color:var(--ink);justify-content:flex-end}
.br.all .bb{height:74px}.br.all .bb span{font-size:58px}
.l61{position:absolute;top:-12px;bottom:-12px;width:0;border-inline-start:4px dashed var(--left);
  inset-inline-start:calc(200px + 18px + (100% - 218px) * 61 / 120)}
.l61 b{position:absolute;top:-34px;transform:translateX(50%);font-family:Karantina;font-size:30px;color:var(--left);white-space:nowrap}
.ban{position:absolute;bottom:78px;inset-inline:60px;padding:12px 18px;font-size:19px;line-height:1.4}
"""
    title = "<h1>הממשלה היוצאת<br>מול <em>61</em></h1>"
    sub = '<p class="sub">ממוצע הסקרים לכנסת ה-26: מפלגות הממשלה ה-37 (הליכוד, הציונות הדתית וזהות, עוצמה יהודית, ש"ס, יהדות התורה) מול שאר הרשימות</p>'
    leg = '<div class="leg2"><span class="c"><i></i>הממשלה היוצאת</span><span class="o"><i></i>שאר הרשימות</span></div>'
    body = ("<style>%s</style>" % css) + title + sub + leg + '<div class="blist"><div class="l61"><b>61</b></div>' + "".join(out) + "</div>" + \
        '<div class="ban">⚠ %s</div>' % esc(BAN_NOTE)
    html = post_shell(fd, "הכנסת ה-26 · אוקטובר 2026", body, "\"שאר הרשימות\" אינו גוש אחד", "#c42a3c")
    a = e["blocs"]["polls"]
    cap = ("61 זה המספר. בממוצע הסקרים לכנסת ה-26, מפלגות הממשלה היוצאת קיבלו %s מנדטים, ושאר הרשימות %s.\n\n"
           "חשוב: \"שאר הרשימות\" זה לא גוש אחד. יש בהן רשימות שלא ישבו יחד בשום ממשלה.\n\n⚠️ %s\n\n"
           "הפירוט לפי כל גוף וכל סקר באתר. הקישור בביו 🗳️\n\n%s" % (fmt(a["C"]), fmt(a["O"]), BAN_NOTE, "#בחירות2026 " + TAGS))
    return html, cap


def post_alltime(D, fd):
    agg = {}
    for e in D.results():
        for r in last_polls(D, e):
            agg.setdefault(r["o"], []).append(r["moved"])
    rows = sorted(({"o": o, "m": sum(v) / len(v), "n": len(v)} for o, v in agg.items()), key=lambda r: r["m"])
    mx = max(r["m"] for r in rows)
    lab = {"11": "כאן 11 / ערוץ 1", "12": "חדשות 12 / ערוץ 2", "13": "חדשות 13 / ערוץ 10", "MAARIV": "מעריב", "HAARETZ": "הארץ"}
    out = []
    for i, r in enumerate(rows):
        out.append('<div class="arow%s"><div class="on"><b>%s</b><span>%d מערכות בחירות</span></div>'
                   '<div class="abar"><span style="width:%.1f%%"></span></div><b class="av">%s</b></div>'
                   % (" best" if i == 0 else "", esc(lab[r["o"]]), r["n"], 78 * r["m"] / mx, fmt(r["m"])))
    css = """
.alist{margin-top:30px;display:flex;flex-direction:column;gap:14px}
.arow{display:grid;grid-template-columns:330px 1fr 110px;align-items:center;gap:18px;background:#fff;border:1px solid var(--rule);
  border-radius:8px;padding:12px 22px;box-shadow:0 6px 18px -12px rgba(24,32,58,.35)}
.arow .on b{display:block;font-family:Karantina;font-size:40px;line-height:.95}.arow .on span{font-size:19px;color:var(--mute)}
.abar{height:24px;background:var(--rule-2);border-radius:3px;overflow:hidden}.abar span{display:block;height:100%;background:#9aa1b0}
.arow .av{font-family:Karantina;font-size:60px;line-height:1;text-align:left}
.arow.best{box-shadow:0 0 0 4px var(--ink)}.arow.best .abar span{background:var(--centre)}
.unit{font-size:21px;color:var(--mute);margin-top:12px}
"""
    first = min(e["date"][:4] for e in D.results())
    title = "<h1>מי הסוקר המדויק<br>ביותר מאז %s?</h1>" % first
    sub = '<p class="sub">הסקר האחרון של כל גוף לפני הבחירות, מול התוצאה. ממוצע על כל המערכות.</p>'
    body = ("<style>%s</style>" % css) + title + sub + '<div class="alist">' + "".join(out) + "</div>" + \
        '<div class="unit">המספר = מנדטים שהוזזו בממוצע. פחות = מדויק יותר.</div>'
    html = post_shell(fd, "%d מערכות בחירות" % len(D.results()), body, "החישוב המלא בעמוד \"דיוק הסוקרים\"", "#7b3fa8")
    cap = ("מי הסוקר המדויק ביותר מאז %s?\n\nלקחנו את הסקר האחרון של כל גוף לפני כל מערכת בחירות, ובדקנו כמה מנדטים צריך להזיז בו כדי להגיע לתוצאה. "
           "%s הוביל, עם %s מנדטים בממוצע.\n\nשימו לב: לא כל גוף פרסם בכל המערכות, אז המספרים לא מבוססים על אותו מספר בחירות.\n\n"
           "הטבלה המלאה בעמוד \"דיוק הסוקרים\" באתר. הקישור בביו 📊\n\n%s" % (first, lab[rows[0]["o"]], fmt(rows[0]["m"]), TAGS))
    return html, cap


# ------------------------------------------------------------------ reels
REEL_CSS = """
.band{height:150px;padding:30px 64px 10px}
.band .logo{width:66px}.band .brand{font-size:54px}.band .tag{font-size:27px;padding:4px 20px}
.top{position:absolute;top:210px;inset-inline:64px}
h1{font-family:Karantina;font-weight:700;font-size:118px;line-height:.88;margin:0}
h1 em{font-style:normal;color:var(--hl)}
.phase{margin-top:24px;height:62px;position:relative}
.phase span{position:absolute;inset-inline-start:0;top:0;font-family:Karantina;font-size:58px;line-height:1;
  background:var(--ink);color:#fff;padding:4px 20px 8px;border-radius:6px;white-space:nowrap}
.chart{position:absolute;top:620px;inset-inline:64px;display:flex;flex-direction:column;gap:24px}
.rw{display:grid;grid-template-columns:104px 1fr;gap:16px;align-items:center;transition:none}
.rw .slip{height:70px;font-size:46px;padding-bottom:8px}
.rw .nm{font-size:26px;font-weight:600;line-height:1;margin-bottom:6px;white-space:nowrap}
.trk{position:relative;height:42px}
.trk .bar{position:absolute;inset-block:0;inset-inline-start:0;background:var(--pc);border-radius:3px}
.trk .ghost{position:absolute;inset-block:-4px;inset-inline-start:0;border:3px dashed var(--ink);border-radius:3px;opacity:0}
.trk .val{position:absolute;top:50%;transform:translateY(-52%);font-family:Karantina;font-weight:700;font-size:56px;line-height:1;white-space:nowrap}
.trk .dl{direction:ltr;unicode-bidi:isolate;display:inline-block;font-family:Plex;font-size:24px;font-weight:700;margin-inline-start:12px;padding:2px 10px;border-radius:999px;vertical-align:6px}
.dl.up{background:#e3eafc;color:var(--right)}.dl.dn{background:#fbe4e7;color:var(--left)}
.call{position:absolute;top:1520px;inset-inline:64px;font-size:40px;font-weight:600;line-height:1.3;opacity:0}
.call b{font-family:Karantina;font-size:64px}
.end{position:absolute;inset:0;background:var(--ink);color:#fff;opacity:0;display:flex;flex-direction:column;
  justify-content:center;align-items:center;text-align:center;gap:26px;padding:0 80px}
.end::before{content:"";position:absolute;top:0;inset-inline:0;height:14px;
  background:linear-gradient(90deg,var(--left) 0 33.3%,var(--centre) 33.3% 66.6%,var(--right) 66.6% 100%)}
.end .lg{width:150px}.end .lg svg{width:100%;display:block}
.end h2{font-family:Karantina;font-weight:700;font-size:112px;line-height:.9;margin:0}
.end p{font-size:38px;line-height:1.4;color:#dfe3ee;margin:0}
.end .u{font-family:Karantina;font-size:70px;direction:ltr;border:3px solid rgba(255,255,255,.5);border-radius:999px;padding:6px 36px 12px}
.ban{position:absolute;top:1430px;inset-inline:64px;padding:16px 22px;font-size:27px;line-height:1.4}
"""

REEL_JS = r"""
const D = window.__D;
const ease = x => x<0?0:x>1?1:(x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2);
const seg = (t,a,b) => ease((t-a)/(b-a));
const lin = (t,a,b) => Math.max(0,Math.min(1,(t-a)/(b-a)));
const fmt = v => { const r = Number(v.toFixed(1)); return Number.isInteger(r) ? String(r) : r.toFixed(1); };  // = fmt() in Python
const rows = [...document.querySelectorAll('.rw')];
const W = () => document.querySelector('.trk').clientWidth * 0.80;
window.draw = function(t){
  const T = D.T, w = W();
  document.querySelector('h1').style.opacity = lin(t,0,.6);
  const p1 = document.getElementById('ph1'), p2 = document.getElementById('ph2');
  p1.style.opacity = lin(t,.6,1) * (1-lin(t,T.morph-1.2,T.morph-.8));
  if (p2) p2.style.opacity = lin(t,T.morph-.8,T.morph-.4);
  const g = seg(t,1,T.grow), m = D.final ? seg(t,T.morph,T.morph+3) : 0;
  rows.forEach((r,i) => {
    const a = D.rows[i].a, b = D.rows[i].b, v = a*g + (b-a)*m, x = w*v/D.max;
    r.querySelector('.bar').style.width = x+'px';
    const val = r.querySelector('.val'); val.style.insetInlineStart = (x+14)+'px';
    val.querySelector('i').textContent = fmt(v);
    const dl = val.querySelector('.dl');
    if (dl) dl.style.opacity = lin(t,T.morph+3,T.morph+3.6);
    const gh = r.querySelector('.ghost');
    if (gh) { gh.style.width = (w*a/D.max)+'px'; gh.style.opacity = lin(t,T.morph,T.morph+.5)*.55; }
    const dim = D.final ? lin(t,T.focus,T.focus+.6) : 0;
    r.style.opacity = (i===D.hot) ? 1 : 1-.65*dim;
    const sl = rows[i].querySelector('.slip');
    if (sl) sl.style.opacity = lin(t,.2+i*.07,.7+i*.07);
  });
  const c = document.querySelector('.call'); if (c) c.style.opacity = lin(t,T.focus+.3,T.focus+.9);
  document.querySelector('.end').style.opacity = lin(t,T.end,T.end+.6);
};
"""


def reel_html(fd, tag, title, ph1, ph2, rows, mx, final, hot, call, end_title, end_text, hl, ban=False):
    rws = []
    for i, r in enumerate(rows):
        d = r["b"] - r["a"]
        dl = ('<span class="dl %s">%s</span>' % ("up" if d > 0 else "dn", signed(d))) if final and abs(d) >= 0.05 else ""
        rws.append('<div class="rw" style="--pc:%s">%s<div><div class="nm">%s</div><div class="trk"><span class="ghost"></span>'
                   '<span class="bar"></span><span class="val"><i>0</i>%s</span></div></div></div>'
                   % (party_color(r["l"]), slip(r["l"]), esc(r["l"]["name"]), dl))
    T = {"grow": 4.0, "morph": 6.6, "focus": 10.8, "end": 13.4, "len": 16.0} if final else \
        {"grow": 4.6, "morph": 99, "focus": 99, "end": 10.6, "len": 13.2}
    data = {"rows": [{"a": r["a"], "b": r["b"]} for r in rows], "max": mx, "final": final, "hot": hot, "T": T}
    body = ('<div class="band"><span class="logo">%s</span><span class="brand">היסטוריית הסקרים של ישראל</span><span class="tag">%s</span></div>'
            '<div class="top"><h1>%s</h1><div class="phase"><span id="ph1">%s</span>%s</div></div>'
            '<div class="chart">%s</div>%s%s'
            '<div class="end"><span class="lg">%s</span><h2>%s</h2><p>%s</p><span class="u">%s</span></div>') % (
        LOGO, esc(tag), title, esc(ph1), ('<span id="ph2" style="opacity:0">%s</span>' % esc(ph2)) if ph2 else "",
        "".join(rws), ('<div class="call">%s</div>' % call) if call else "",
        ('<div class="ban">⚠ %s</div>' % esc(BAN_NOTE)) if ban else "", LOGO, end_title, end_text, SITE_URL)
    html = shell(fd, 1080, 1920, REEL_CSS + ":root{--hl:%s}" % hl, body,
                 "window.__D=%s;%s" % (json.dumps(data), REEL_JS))
    return html, T["len"]


def reel_gap(D, fd, key):
    e = D.by[key]
    rows = compare_rows(e, 9)
    hot = max(range(len(rows)), key=lambda i: abs(rows[i]["diff"]))
    big = rows[hot]
    mx = max(max(r["avg"], r["res"]) for r in rows)
    rr = [{"l": r["l"], "a": r["avg"], "b": r["res"]} for r in rows]
    title = "מה חזו הסקרים<br>ב%s?" % ("בחירות של " + when(e))
    call = "<b>%s</b>: %s בממוצע הסקרים, <b>%s</b> בקלפי" % (esc(big["l"]["name"]), fmt(big["avg"]), fmt(big["res"]))
    nel = len(D.results())
    html, length = reel_html(fd, "הכנסת ה-%s · %s" % (e["knesset"], when(e)), title, "ממוצע הסקרים", "ובקלפי...",
                             rr, mx, True, hot, call, "ומה קרה<br>בשאר הבחירות?",
                             "%d מערכות בחירות, %d סקרים, כל אחד עם המקור שלו" % (nel, sum(1 for p in D.P if p["e"] != "2026")),
                             party_color(big["l"]))
    cap = ("%s: ככה נראה ממוצע הסקרים... ומה קרה בקלפי.\n\n%s: %s מנדטים בממוצע הסקרים, %s בפועל.\n\n"
           "כל הסקרים של כל מערכות הבחירות מ-2009 באתר. הקישור בביו 🗳️\n\n%s"
           % ("הבחירות לכנסת ה-" + e["knesset"] + ", " + when(e), big["l"]["name"], fmt(big["avg"]), fmt(big["res"]), TAGS))
    return html, cap, length, 12000


def reel_2026(D, fd):
    e = D.by["2026"]
    ls = sorted((l for l in e["lists"] if (l.get("polls") or {}).get("overall")), key=lambda l: -l["polls"]["overall"])
    rr = [{"l": l, "a": l["polls"]["overall"], "b": l["polls"]["overall"]} for l in ls]
    html, length = reel_html(fd, "הכנסת ה-26 · אוקטובר 2026", "ככה נראו<br>הסקרים לכנסת ה-26", "ממוצע %d סקרים" % sum(1 for p in D.P if p["e"] == "2026"),
                             None, rr, rr[0]["a"], False, 0, None, "ביום שלישי<br>נדע מי צדק",
                             "וכבר עכשיו אפשר לבדוק מי צדק בכל הבחירות מאז 2009", "#7b3fa8", ban=True)
    # 13 lists: compact rows so the chart ends above the ban note
    html = html.replace("</style>", ".chart{top:560px;gap:10px}.rw .slip{height:50px;font-size:34px}.rw .nm{font-size:22px;margin-bottom:4px}"
                        ".trk{height:28px}.trk .val{font-size:42px}.ban{top:1420px}</style>", 1)
    cap = ("הממוצע של כל הסקרים לכנסת ה-26, מסוף יולי ועד 23.10.\n\n⚠️ %s\n\n"
           "ביום שלישי בלילה נדע כמה הם צדקו. באתר אפשר לראות מה קרה לסקרים בכל מערכת בחירות מאז 2009. הקישור בביו 📊\n\n%s"
           % (BAN_NOTE, "#בחירות2026 " + TAGS))
    return html, cap, length, 6000


# ------------------------------------------------------------------ catalog
def catalog(D):
    items = {}
    keys = [e["key"] for e in D.results()]
    for k in keys:
        items["reel-gap-" + k] = ("reel", lambda fd, k=k: reel_gap(D, fd, k))
        items["post-gap-" + k] = ("post", lambda fd, k=k: post_gap(D, fd, k))
        items["post-acc-" + k] = ("post", lambda fd, k=k: post_accuracy(D, fd, k))
        if D.by[k]["exitPolls"]:
            items["post-exit-" + k] = ("post", lambda fd, k=k: post_exits(D, fd, k))
    items["post-alltime"] = ("post", lambda fd: post_alltime(D, fd))
    if "2026" in D.by and not any(l.get("seats") for l in D.by["2026"]["lists"]):
        items["post-2026-avg"] = ("post", lambda fd: post_2026_avg(D, fd))
        items["post-2026-blocs"] = ("post", lambda fd: post_2026_blocs(D, fd))
        items["reel-2026"] = ("reel", lambda fd: reel_2026(D, fd))
    return items


# ------------------------------------------------------------------ rendering
def render(items, ids, fd, out):
    from playwright.sync_api import sync_playwright
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp()
    with sync_playwright() as p:
        br = p.chromium.launch()
        for iid in ids:
            kind, make = items[iid]
            res = make(fd)
            html = res[0]
            hp = os.path.join(tmp, iid + ".html")
            open(hp, "w", encoding="utf-8").write(html)
            w, h = (1080, 1080) if kind == "post" else (1080, 1920)
            pg = br.new_page(viewport={"width": w, "height": h})
            errs = []
            pg.on("pageerror", lambda ex: errs.append(str(ex)))
            pg.goto("file://" + hp)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            bad = pg.evaluate("[...document.fonts].filter(f=>f.status!=='loaded').map(f=>f.family+f.weight)")
            if bad and any(b for b in bad):
                # fonts only load when used; check that both families are in use and loaded
                used = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)")
                if "Karantina" not in str(used) or "Plex" not in str(used):
                    raise SystemExit("fonts not loaded for %s: %s" % (iid, bad))
            over = pg.evaluate("""(() => {
              const lim = Math.min(...[...document.querySelectorAll('.foot,.ban')].map(x => x.getBoundingClientRect().top), innerHeight) - 4;
              const els = [...document.querySelectorAll('.main *, .chart *, .top *')].filter(x => !x.closest('.ban'));
              const low = Math.max(...els.map(x => x.getBoundingClientRect().bottom));
              const wide = els.some(x => { const b = x.getBoundingClientRect(); return b.left < -1 || b.right > innerWidth + 1; });
              return (document.querySelector('.foot') || document.querySelector('.ban')) && low > lim ? 'low ' + low + ' > ' + lim : (wide ? 'wide' : '');
            })()""")
            if over:
                raise SystemExit("content overflows the frame in %s: %s" % (iid, over))
            if kind == "post":
                if errs:
                    raise SystemExit("js error in %s: %s" % (iid, errs))
                pg.screenshot(path=os.path.join(out, iid + ".jpg"), type="jpeg", quality=93)
            else:
                length, fps = res[2], 30
                fdir = os.path.join(tmp, iid)
                os.makedirs(fdir)
                for f in range(int(length * fps)):
                    pg.evaluate("draw(%f)" % (f / fps))
                    pg.screenshot(path=os.path.join(fdir, "%04d.jpg" % f), type="jpeg", quality=95)
                if errs:
                    raise SystemExit("js error in %s: %s" % (iid, errs))
                mp4 = os.path.join(out, iid + ".mp4")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(fdir, "%04d.jpg"),
                                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
                                "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart", mp4], check=True)
                # still frame for checking the layout
                shutil.copy(os.path.join(fdir, "%04d.jpg" % int(res[3] / 1000 * fps)), os.path.join(out, iid + ".cover.jpg"))
            pg.close()
        br.close()
    shutil.rmtree(tmp)


def main():
    site, fd, out, cmd = sys.argv[1:5]
    D = Data(site)
    items = catalog(D)
    if cmd == "list":
        for k, (kind, _) in items.items():
            print(kind, k)
    elif cmd == "render":
        render(items, sys.argv[5:], fd, out)
    elif cmd == "caption":
        res = items[sys.argv[5]][1](fd)
        print(res[1])
    elif cmd == "meta":
        # caption + reel cover time as JSON, for the scheduler
        res = items[sys.argv[5]][1](fd)
        print(json.dumps({"kind": items[sys.argv[5]][0], "caption": res[1],
                          "cover_ms": res[3] if len(res) > 3 else None}, ensure_ascii=False))


if __name__ == "__main__":
    main()

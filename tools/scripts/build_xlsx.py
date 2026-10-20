"""Build the Excel workbook: data sheets + one sheet and chart per election."""
import os
import re
import sys
from datetime import timedelta

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(__file__))
from build_data import build, summarize  # noqa: E402
from config import ELECTIONS  # noqa: E402
from blocs import (FINAL, EXIT_FULL, BLOC_ORDER, KIND, labels, RES_SRC, GOV_SRC,  # noqa: E402
                   BLOC_COL_NOTES, self_check)
from build_data import poll_blocs  # noqa: E402
from openpyxl.chart import PieChart
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
EXIT = EXIT_FULL

OUT = sys.argv[1] if len(sys.argv) > 1 else "polls.xlsx"

ORDER = ["2022", "2021", "2020", "2019b", "2019a", "2015", "2013", "2009"]
SHEET = {"2022": "2022", "2021": "2021", "2020": "2020", "2019b": "ספטמבר 2019",
         "2019a": "אפריל 2019", "2015": "2015", "2013": "2013", "2009": "2009"}
OUTLET_LABEL = {"11": "כאן 11", "12": "חדשות 12", "13": "חדשות 13",
                "MAARIV": "מעריב", "HAARETZ": "הארץ"}
PRED = {"11": "ערוץ 1", "12": "ערוץ 2", "13": "ערוץ 10"}
OLD = {"2009", "2013", "2015"}
OUTLETS = ["11", "12", "13", "MAARIV", "HAARETZ"]
COLORS = {"11": "1F77B4", "12": "D62728", "13": "2CA02C", "MAARIV": "FF7F0E",
          "HAARETZ": "9467BD", "EXIT": "404040"}

FONT = "Arial"
F = Font(name=FONT, size=10)
FB = Font(name=FONT, size=10, bold=True)
FT = Font(name=FONT, size=14, bold=True)
FS = Font(name=FONT, size=9, italic=True, color="555555")
FLINK = Font(name=FONT, size=10, color="0563C1", underline="single")
HEAD_FILL = PatternFill("solid", fgColor="DDE5F0")
EXIT_FILL = PatternFill("solid", fgColor="EDEDED")
FLAG_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Side(style="thin", color="B0B0B0")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top", horizontal="right")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def header_label(key, o):
    if key in OLD and o in PRED:
        return "%s (במקום %s)" % (PRED[o], OUTLET_LABEL[o])
    return OUTLET_LABEL[o]


# ------------------------------------------------------------ note translation
OUTLET_NOTE_HE = {
    "published as 'Keshet' (counted as Channel 12 by user decision)": "פורסם תחת 'קשת' - נספר כחדשות 12 (החלטתך)",
    "Mako (Keshet's website) with Knesset Channel - counted as Channel 12 by user decision": "Mako (אתר קשת) יחד עם ערוץ הכנסת - נספר כחדשות 12 (החלטתך)",
    "Mako (Keshet's website) - counted as Channel 12 by user decision": "Mako (אתר קשת) - נספר כחדשות 12 (החלטתך)",
    "Kan radio - counted as Kan 11 by user decision": "רדיו כאן - נספר ככאן 11 (החלטתך)",
    "Reshet Bet (Kan radio) - counted as Kan 11 by user decision": "רשת ב' (רדיו כאן) - נספר ככאן 11 (החלטתך)",
    "joint Maariv/Jerusalem Post publication": "פרסום משותף מעריב/ג'רוזלם פוסט - נספר כמעריב (החלטתך)",
    "joint 103FM/Maariv publication": "פרסום משותף 103FM/מעריב - נספר כמעריב (החלטתך)",
    "joint Walla/Maariv publication": "פרסום משותף וואלה/מעריב - נספר כמעריב (החלטתך)",
    "Nana 10 (Channel 10's website) - counted as Channel 10 by user decision; Channel 10 = predecessor of 13": "Nana 10 (אתר ערוץ 10) - נספר כערוץ 10 (החלטתך)",
    "Channel 2 (predecessor of 12)": "",
    "Channel 10 (predecessor of 13)": "",
    "Channel 1 / IBA (predecessor of Kan 11)": "",
    "IBA radio (Reshet Bet / Kol Israel) - counted as Kan 11 predecessor by user decision": "רדיו רשות השידור (רשת ב'/קול ישראל) - נספר כערוץ 1 (החלטתך)",
    "Channel 2 with Mako (predecessor of 12)": "ערוץ 2 יחד עם Mako",
    "Mako (Keshet's website) - counted as Channel 2 by user decision; Channel 2 = predecessor of 12": "Mako (אתר קשת) - נספר כערוץ 2 (החלטתך)",
    "joint Haaretz/Channel 10 poll - counted for both by user decision; Channel 10 = predecessor of 13": "סקר משותף הארץ/ערוץ 10 - נספר לשניהם (החלטתך)",
    "IBA radio (Kol Israel) - counted as Kan 11 predecessor by user decision": "רדיו רשות השידור (קול ישראל) - נספר כערוץ 1 (החלטתך)",
    "Channel 2 (predecessor of 12) (programme 'Mishal Cham')": "תוכנית 'משעל חם' של ערוץ 2",
    "Channel 1 / IBA (predecessor of Kan 11) (programme 'Friday Diary')": "תוכנית 'יומן שישי' של ערוץ 1",
}
SCEN_HE = {
    0: None,
}
COLNOTE_HE = {
    "Religious Zionist Party alone: Zehut was not a separate column in this table (before the 1 Sep 2026 union)":
        "הציונות הדתית בלבד: זהות לא הופיעה כעמודה נפרדת בטבלה זו (לפני האיחוד ב-1.9.2026)",
    "Zionist Home (Hendel and Tropper, until 6 Sep 2026) counted as the Reservists by user decision":
        "'הבית הציוני' (הנדל וטרופר, עד 6.9.2026) נספר כמילואימניקים (החלטתך)",
    "listed as 'Winter party' before the name Amcha Yisrael (25 Aug 2026)":
        "מופיע כ'מפלגת וינטר', לפני השם עמך ישראל (25.8.2026)",
    "Religious Zionist list incl. Otzma Yehudit, before Otzma's temporary separate run (15-26 Aug 2022)":
        "רשימת הציונות הדתית כולל עוצמה יהודית, לפני ההיפרדות הזמנית של עוצמה (15-26.8.2022)",
    "Blue and White-New Hope list, before Eisenkot joined and it was renamed National Unity (14 Aug 2022)":
        "רשימת כחול לבן-תקווה חדשה, לפני הצטרפות איזנקוט והשינוי לשם 'המחנה הממלכתי' (14.8.2022)",
    "listed as Likud-Kulanu (Kulanu had already merged into Likud in May 2019)":
        "מופיע כ'ליכוד-כולנו' (כולנו כבר התמזגה לליכוד במאי 2019)",
}


def value_note_he(note):
    if not note:
        return ""
    parts = []
    for part in note.split("; "):
        m = re.fullmatch(r"below threshold (\(.*?\)) = 0 seats", part)
        if m:
            parts.append("מתחת לאחוז החסימה %s = 0 מנדטים" % m.group(1))
            continue
        m = re.fullmatch(r"range (\S+) -> midpoint", part)
        if m:
            parts.append("טווח %s - נלקח אמצע הטווח (החלטתך)" % m.group(1))
            continue
        m = re.fullmatch(r"pre-merger sum of (.*)", part)
        if m:
            parts.append("לפני האיחוד - סכום הרכיבים: %s (החלטתך)" % m.group(1))
            continue
        if part == "pre-split entity (different list) - not counted":
            parts.append("לפני הפיצול: רשימה משותפת אחרת - לא נספר למפלגה (החלטתך)")
            continue
        m = re.fullmatch(r"joint cell with (.*) - not counted", part)
        if m:
            parts.append("הערך משותף עם %s - לא נספר" % m.group(1))
            continue
        m = re.fullmatch(r"not reported: (.*)", part)
        if m:
            parts.append("לא דווח עבור: %s" % m.group(1))
            continue
        if part in COLNOTE_HE:
            parts.append(COLNOTE_HE[part])
            continue
        raise SystemExit("untranslated note: %r" % part)
    return "; ".join(parts)


SCENARIO_HE = {
    "2 scenario rows; kept the one with Hadash-Ta'al and Balad joint (the Joint List re-formed on 19 Aug 2026)":
        "הסקר הציג 2 תרחישים; נבחר התרחיש עם חד\"ש-תע\"ל ובל\"ד יחד (הרשימה המשותפת שקמה מחדש ב-19.8.2026)",
    "2 scenario rows; kept the one with Ofer Winter's party (it ran, as Amcha Yisrael)":
        "הסקר הציג 2 תרחישים; נבחר התרחיש עם המפלגה של עופר וינטר (שרצה בפועל, כעמך ישראל)",
    "2 scenario rows; kept the one with the Religious Zionist Party and Zehut joint (the union of 1 Sep 2026); most lists were not reported in it":
        "הסקר הציג 2 תרחישים; נבחר התרחיש עם הציונות הדתית וזהות יחד (האיחוד של 1.9.2026). בתרחיש זה רוב הרשימות לא דווחו",
    "3 scenario rows; kept the one with New Right + National Union + United Jewish Home joint (the Yamina union that formed on 14-15 Jan 2020; it still included Otzma, which ran alone)":
        "הסקר הציג 3 תרחישים; נבחר התרחיש עם איחוד הימין החדש + האיחוד הלאומי + הבית היהודי המאוחד (האיחוד שקם כ'ימינה' ב-14-15.1.2020; בתרחיש נכללה גם עוצמה, שבפועל רצה לבד)",
    "2 scenario rows; neither shows a union that happened (the other joins National Union with United Jewish Home) - kept the base row":
        "הסקר הציג 2 תרחישים; באף אחד אין איחוד שקרה בפועל (השני מאחד את האיחוד הלאומי עם הבית היהודי המאוחד) - נבחר התרחיש הבסיסי",
    "2 scenario rows; kept the one with Labor-Gesher + Democratic Union joint (the merger that formed on 13 Jan 2020)":
        "הסקר הציג 2 תרחישים; נבחר התרחיש עם העבודה-גשר + המחנה הדמוקרטי ברשימה אחת (האיחוד שקם ב-13.1.2020)",
}


def fmt_num(v):
    return ("%g" % v) if isinstance(v, float) else str(v)


BLOC_COLORS = {"C": "2F5597", "O": "C55A11", "N": "7F7F7F", "X": "BFBFBF"}
BLOC_COL_LETTER = {"C": "E", "O": "F", "N": "G", "X": "H"}


def style_cell(c, font=F, fill=None, align=None, border=BOX, fmt=None):
    c.font = font
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if border:
        c.border = border
    if fmt:
        c.number_format = fmt


def main():
    polls = build()
    summary = summarize(polls)
    top4 = {}
    for key in ORDER:
        per = summary[key]
        ranked = sorted(per.items(), key=lambda kv: -kv[1]["overall"])
        top4[key] = [n for n, _ in ranked[:4]]
        for ent in EXIT[key]:
            assert set(top4[key]) <= set(ent["seats"]), (key, top4[key])
    self_check()
    pblocs = poll_blocs(polls)
    ptotal = {id(x["poll"]): x["total"] for x in pblocs}

    wb = Workbook()
    readme = wb.active
    readme.title = "הסבר"

    # ------------------------------------------------------------ poll data
    ds = wb.create_sheet("סקרים")
    ds.sheet_view.rightToLeft = True
    cols = ["מערכת", "תאריך פרסום (סיום העבודה)", "תאריך כפי שבמקור", "גוף (לגרף)", "גוף בפועל",
            "מכון סקרים", "מפלגה", "מנדטים", "נכלל בממוצע", "הערה על הערך", "הערה על הגוף", "מקור",
            "סכום כל המפלגות בסקר"]
    ds.append(cols)
    for i, _ in enumerate(cols, 1):
        style_cell(ds.cell(1, i), FB, HEAD_FILL, CENTER)
    r = 2
    for key in ORDER:
        rows = [p for p in polls if p["election"] == key]
        rows.sort(key=lambda p: (p["end"], p["outlet"]))
        for p in rows:
            for party in [pp["name"] for pp in ELECTIONS[key]["parties"]]:
                val, note = p["values"][party]
                onote = OUTLET_NOTE_HE[p["outlet_note"]] if p["outlet_note"] else ""
                if p.get("scenario_note"):
                    onote = (onote + "; " if onote else "") + SCENARIO_HE[p["scenario_note"]]
                actual = p["publisher"] if ELECTIONS[key]["fmt"] != "B" else p["publisher"]
                vals = [SHEET[key], p["end"], p["date_text"],
                        OUTLET_LABEL[p["outlet"]], actual, p["firm"] if ELECTIONS[key]["fmt"] != "B" else "",
                        party, val, "כן" if val is not None else "לא", value_note_he(note), onote,
                        p["source"], ptotal[id(p)]]
                if ptotal[id(p)] != 120:
                    vals[10] = (vals[10] + "; " if vals[10] else "") + "סכום הסקר %s ולא 120 - כנראה ערך חסר או שגוי במקור; הערך נשאר בממוצע (החלטתך)" % fmt_num(ptotal[id(p)])
                for ci, v in enumerate(vals, 1):
                    c = ds.cell(r, ci, v)
                    style_cell(c, F, None, WRAP if ci in (10, 11) else None)
                    if ci == 2:
                        c.number_format = "yyyy-mm-dd"
                    if ci == 8 and isinstance(v, float):
                        c.number_format = "0.0"
                if note or vals[10]:
                    for ci in (8, 10, 11):
                        ds.cell(r, ci).fill = FLAG_FILL
                r += 1
    last_data = r - 1
    widths = [12, 13, 16, 11, 34, 22, 16, 9, 9, 50, 45, 30, 12]
    for i, w in enumerate(widths, 1):
        ds.column_dimensions[get_column_letter(i)].width = w
    ds.freeze_panes = "A2"
    ds.auto_filter.ref = "A1:M%d" % last_data

    # ------------------------------------------------------------ exit data
    xs = wb.create_sheet("מדגמים")
    xs.sheet_view.rightToLeft = True
    xcols = ["מערכת", "גוף (לגרף)", "ערוץ בפועל", "מפלגה", "מנדטים", "גרסה", "שעה", "הערה", "מקור", "גוש"]
    xs.append(xcols)
    for i, _ in enumerate(xcols, 1):
        style_cell(xs.cell(1, i), FB, HEAD_FILL, CENTER)
    xr = 2
    for key in ORDER:
        bloc_of = {n: b for n, _, b, _ in FINAL[key]}
        for ent in EXIT[key]:
            for party, seats in ent["seats"].items():
                vals = [SHEET[key], OUTLET_LABEL[ent["channel"]], ent["actual"], party,
                        seats, ent["version"], ent["time"], ent["note"], ent["source"],
                        labels(key)[bloc_of[party]]]
                for ci, v in enumerate(vals, 1):
                    c = xs.cell(xr, ci, v)
                    style_cell(c, F, None, WRAP if ci in (6, 8) else None)
                if ent["version"] != "עדכון לילי (הגרסה המאוחרת ביותר שנמצאה)":
                    for ci in (5, 6):
                        xs.cell(xr, ci).fill = FLAG_FILL
                xr += 1
    last_exit = xr - 1
    for i, w in enumerate([12, 11, 24, 16, 9, 30, 16, 60, 40, 18], 1):
        xs.column_dimensions[get_column_letter(i)].width = w
    xs.freeze_panes = "A2"

    D = "'סקרים'!"
    X = "'מדגמים'!"
    rng = lambda col: "%s$%s$2:$%s$%d" % (D, col, col, last_data)
    xrng = lambda col: "%s$%s$2:$%s$%d" % (X, col, col, last_exit)

    # ------------------------------------------------------------ bloc data per poll
    bs = wb.create_sheet("גושים בסקרים")
    bs.sheet_view.rightToLeft = True
    bcols = ["מערכת", "תאריך פרסום", "גוף (לגרף)", "גוף בפועל",
             "קואליציה / המליצו על נתניהו", "אופוזיציה / המליצו על גנץ",
             "לא המליצו (2019)", "לא נכנסו לכנסת", "סכום", "נכלל במפת הגושים", "הערה", "מקור"]
    bs.append(bcols)
    for i, _ in enumerate(bcols, 1):
        style_cell(bs.cell(1, i), FB, HEAD_FILL, CENTER)
    bs.row_dimensions[1].height = 30
    br = 2
    for key in ORDER:
        items = [x for x in pblocs if x["poll"]["election"] == key]
        items.sort(key=lambda x: (x["poll"]["end"], x["poll"]["outlet"]))
        for x in items:
            p = x["poll"]
            ok = x["total"] == 120
            note = "; ".join(x["notes"])
            if not ok:
                note = (note + "; " if note else "") + "הסכום אינו 120 - הסקר לא נכלל במפת הגושים (החלטתך)"
            vals = [SHEET[key], p["end"], OUTLET_LABEL[p["outlet"]], p["publisher"],
                    x["sums"]["C"], x["sums"]["O"], x["sums"]["N"] if KIND[key] == "rec" else None,
                    x["sums"]["X"], x["total"], "כן" if ok else "לא", note, p["source"]]
            for ci, v in enumerate(vals, 1):
                c = bs.cell(br, ci, v)
                style_cell(c, F, None, WRAP if ci == 11 else None)
                if ci == 2:
                    c.number_format = "yyyy-mm-dd"
                if ci in (5, 6, 7, 8, 9) and isinstance(v, float):
                    c.number_format = "0.0"
            if not ok or x["notes"]:
                for ci in (9, 10, 11):
                    bs.cell(br, ci).fill = FLAG_FILL
            br += 1
    last_bloc = br - 1
    for i, w in enumerate([12, 12, 11, 34, 14, 14, 12, 12, 8, 10, 50, 30], 1):
        bs.column_dimensions[get_column_letter(i)].width = w
    bs.freeze_panes = "A2"
    bs.auto_filter.ref = "A1:L%d" % last_bloc
    B = "'גושים בסקרים'!"
    brng = lambda col: "%s$%s$2:$%s$%d" % (B, col, col, last_bloc)

    # ------------------------------------------------------------ official results
    rs = wb.create_sheet("תוצאות")
    rs.sheet_view.rightToLeft = True
    rcols = ["מערכת", "רשימה", "מנדטים בפועל", "גוש", "הערה", "מקור התוצאות", "מקור הרכב הממשלה / ההמלצות"]
    rs.append(rcols)
    for i, _ in enumerate(rcols, 1):
        style_cell(rs.cell(1, i), FB, HEAD_FILL, CENTER)
    rr_ = 2
    for key in ORDER:
        for name, seats, bloc, note in FINAL[key]:
            vals = [SHEET[key], name, seats, labels(key)[bloc], note, RES_SRC[key], GOV_SRC[key]]
            for ci, v in enumerate(vals, 1):
                style_cell(rs.cell(rr_, ci, v), F, None, WRAP if ci == 5 else None)
            if note:
                for ci in (4, 5):
                    rs.cell(rr_, ci).fill = FLAG_FILL
            rr_ += 1
    last_res = rr_ - 1
    for i, w in enumerate([12, 20, 11, 20, 60, 40, 40], 1):
        rs.column_dimensions[get_column_letter(i)].width = w
    rs.freeze_panes = "A2"
    R = "'תוצאות'!"
    rrng = lambda col: "%s$%s$2:$%s$%d" % (R, col, col, last_res)

    # ------------------------------------------------------------ election sheets
    for key in ORDER:
        cfg = ELECTIONS[key]
        ws = wb.create_sheet(SHEET[key])
        ws.sheet_view.rightToLeft = True
        name = SHEET[key]
        ws["A1"] = "בחירות %s - ממוצע סקרים ב-3 החודשים שלפני הבחירות, לפי גוף, וממוצע המדגמים" % cfg["label"]
        ws["A1"].font = FT
        last_day = cfg["date"] - timedelta(days=1)
        ws["A2"] = "חלון הסקרים: %s עד %s (כולל). יום הבחירות: %s." % (
            cfg["start"].strftime("%d.%m.%Y"), last_day.strftime("%d.%m.%Y"),
            cfg["date"].strftime("%d.%m.%Y"))
        ws["A2"].font = FS
        # name cell used by formulas
        ws["A3"] = "מערכת:"
        ws["B3"] = name
        ws["A3"].font = FS
        ws["B3"].font = FS

        # main table
        hr = 5
        heads = ["מפלגה"] + [header_label(key, o) for o in OUTLETS] + ["ממוצע מדגמים (ליל הבחירות)"]
        for ci, h in enumerate(heads, 1):
            style_cell(ws.cell(hr, ci, h), FB, EXIT_FILL if ci == len(heads) else HEAD_FILL, CENTER)
        ws.row_dimensions[hr].height = 32
        for i, party in enumerate(top4[key]):
            rr = hr + 1 + i
            style_cell(ws.cell(rr, 1, party), FB)
            for j, o in enumerate(OUTLETS):
                f = ('=IFERROR(AVERAGEIFS(%s,%s,$B$3,%s,"%s",%s,$A%d,%s,"כן"),"")'
                     % (rng("H"), rng("A"), rng("D"), OUTLET_LABEL[o], rng("G"), rr, rng("I")))
                style_cell(ws.cell(rr, 2 + j, f), F, None, CENTER, fmt="0.0")
            f = ('=IFERROR(AVERAGEIFS(%s,%s,$B$3,%s,$A%d),"")'
                 % (xrng("E"), xrng("A"), xrng("D"), rr))
            style_cell(ws.cell(rr, 2 + len(OUTLETS), f), FB, EXIT_FILL, CENTER, fmt="0.0")

        # counts table
        cr = hr + 6
        ws.cell(cr, 1, "מספר הסקרים שנכללו בממוצע").font = FB
        for ci, h in enumerate(heads[:-1], 1):
            style_cell(ws.cell(cr + 1, ci, h), FB, HEAD_FILL, CENTER)
        for i, party in enumerate(top4[key]):
            rr = cr + 2 + i
            style_cell(ws.cell(rr, 1, party), F)
            for j, o in enumerate(OUTLETS):
                f = ('=COUNTIFS(%s,$B$3,%s,"%s",%s,$A%d,%s,"כן")'
                     % (rng("A"), rng("D"), OUTLET_LABEL[o], rng("G"), rr, rng("I")))
                style_cell(ws.cell(rr, 2 + j, f), F, None, CENTER, fmt="0")

        # exit polls per channel
        er = cr + 7
        ws.cell(er, 1, "המדגמים לפי ערוץ (הגרסה המאוחרת ביותר שנמצאה - פירוט וגרסה בגיליון 'מדגמים')").font = FB
        ehead = ["מפלגה"] + [header_label(key, o) for o in ["11", "12", "13"]] + ["ממוצע"]
        for ci, h in enumerate(ehead, 1):
            style_cell(ws.cell(er + 1, ci, h), FB, EXIT_FILL, CENTER)
        for i, party in enumerate(top4[key]):
            rr = er + 2 + i
            style_cell(ws.cell(rr, 1, party), F)
            for j, o in enumerate(["11", "12", "13"]):
                crit = '%s,$B$3,%s,"%s",%s,$A%d' % (xrng("A"), xrng("B"), OUTLET_LABEL[o], xrng("D"), rr)
                f = '=IF(COUNTIFS(%s)=0,"",SUMIFS(%s,%s))' % (crit, xrng("E"), crit)
                style_cell(ws.cell(rr, 2 + j, f), F, None, CENTER, fmt="0")
            f = "=IFERROR(AVERAGE(B%d:D%d),\"\")" % (rr, rr)
            style_cell(ws.cell(rr, 5, f), FB, None, CENTER, fmt="0.0")

        # selection of top 4 (formulas over every party that was checked)
        sr = er + 8
        ws.cell(sr, 1, "בחירת ארבע המפלגות הגדולות: ממוצע הממוצעים של הגופים (כל גוף במשקל שווה), לכל המפלגות שנבדקו").font = FB
        ranked = sorted(summary[key].items(), key=lambda kv: -kv[1]["overall"])
        sheads = ["מפלגה"] + [header_label(key, o) for o in OUTLETS] + ["ממוצע כולל", "בגרף"]
        for ci, h in enumerate(sheads, 1):
            style_cell(ws.cell(sr + 1, ci, h), FB, HEAD_FILL, CENTER)
        for i, (party, d) in enumerate(ranked):
            rr = sr + 2 + i
            style_cell(ws.cell(rr, 1, party), F)
            for j, o in enumerate(OUTLETS):
                f = ('=IFERROR(AVERAGEIFS(%s,%s,$B$3,%s,"%s",%s,$A%d,%s,"כן"),"")'
                     % (rng("H"), rng("A"), rng("D"), OUTLET_LABEL[o], rng("G"), rr, rng("I")))
                style_cell(ws.cell(rr, 2 + j, f), F, None, CENTER, fmt="0.0")
            style_cell(ws.cell(rr, 7, "=IFERROR(AVERAGE(B%d:F%d),\"\")" % (rr, rr)), FB, None, CENTER, fmt="0.00")
            style_cell(ws.cell(rr, 8, "כן" if party in top4[key] else ""), F, None, CENTER)
        ranked_len = len(ranked)

        # notes for this election
        nr = sr + 3 + ranked_len
        notes = election_notes(key)
        ws.cell(nr, 1, "הערות למערכת זו").font = FB
        for i, t in enumerate(notes):
            c = ws.cell(nr + 1 + i, 1, "• " + t)
            c.font = F
            c.alignment = Alignment(wrap_text=False, horizontal="right")
        c = ws.cell(nr + 2 + len(notes), 1, "מקור הסקרים: " + cfg["source"])
        c.font = FLINK
        c.hyperlink = cfg["source"]

        ws.column_dimensions["A"].width = 22
        for j in range(2, 9):
            ws.column_dimensions[get_column_letter(j)].width = 16

        # chart: series = outlets with data in this election + exit average
        chart = BarChart()
        chart.type = "col"
        chart.grouping = "clustered"
        chart.title = "בחירות %s" % cfg["label"]
        chart.y_axis.title = "מנדטים"
        chart.y_axis.scaling.min = 0
        chart.y_axis.number_format = "0"
        chart.y_axis.majorUnit = 5
        chart.y_axis.majorGridlines = chart.y_axis.majorGridlines
        chart.y_axis.delete = False
        chart.x_axis.delete = False
        chart.height = 10
        chart.width = 22
        cats = Reference(ws, min_col=1, min_row=hr + 1, max_row=hr + 4)
        present = {p["outlet"] for p in polls if p["election"] == key}
        for j, o in enumerate(OUTLETS + ["EXIT"]):
            if o != "EXIT" and o not in present:
                continue
            col = 2 + j
            data = Reference(ws, min_col=col, min_row=hr, max_row=hr + 4)
            chart.add_data(data, titles_from_data=True)
            s = chart.series[-1]
            s.graphicalProperties = GraphicalProperties(solidFill=COLORS[o])
            s.graphicalProperties.line.solidFill = COLORS[o]
        chart.set_categories(cats)
        chart.legend.position = "b"
        ws.add_chart(chart, "I5")
        # ---------------------------------------------------- bloc map
        b0 = nr + len(notes) + 5
        kind = KIND[key]
        codes = BLOC_ORDER[kind]
        lab = labels(key)
        if kind == "rec":
            title = "מפת גושים: המלצות לנשיא על מועמד להרכבת הממשלה (לא הוקמה ממשלה אחרי בחירות אלה)"
        else:
            title = "מפת גושים: קואליציה מול אופוזיציה, לפי הרכב הממשלה הראשונה שהושבעה אחרי הבחירות"
        ws.cell(b0, 1, title).font = Font(name=FONT, size=12, bold=True)
        ws.cell(b0 + 1, 1, "ממוצע הסקרים: סכום הגוש בכל סקר, ממוצע לכל גוף, ואז ממוצע הגופים. נכללים רק סקרים שמסתכמים ב-120. רשימה שהתפצלה שויכה לפי רוב חבריה.").font = FS
        th = b0 + 3
        bheads = ["גוש"] + [header_label(key, o) for o in OUTLETS] + ["ממוצע סקרים", "ממוצע מדגמים", "תוצאה סופית"]
        for ci, h in enumerate(bheads, 1):
            style_cell(ws.cell(th, ci, h), FB, EXIT_FILL if ci >= 7 else HEAD_FILL, CENTER)
        ws.row_dimensions[th].height = 32
        ex0 = th + len(codes) + 5          # per-channel exit table header row
        for i, code in enumerate(codes):
            r_ = th + 1 + i
            style_cell(ws.cell(r_, 1, lab[code]), FB)
            col = BLOC_COL_LETTER[code]
            for j, o in enumerate(OUTLETS):
                f = ('=IFERROR(AVERAGEIFS(%s,%s,$B$3,%s,"%s",%s,"כן"),"")'
                     % (brng(col), brng("A"), brng("C"), OUTLET_LABEL[o], brng("J")))
                style_cell(ws.cell(r_, 2 + j, f), F, None, CENTER, fmt="0.0")
            style_cell(ws.cell(r_, 7, "=IFERROR(AVERAGE(B%d:F%d),\"\")" % (r_, r_)), FB, EXIT_FILL, CENTER, fmt="0.0")
            er_ = ex0 + 1 + i
            style_cell(ws.cell(r_, 8, "=IFERROR(AVERAGE(B%d:D%d),\"\")" % (er_, er_)), FB, EXIT_FILL, CENTER, fmt="0.0")
            style_cell(ws.cell(r_, 9, '=SUMIFS(%s,%s,$B$3,%s,$A%d)' % (rrng("C"), rrng("A"), rrng("D"), r_)),
                       FB, EXIT_FILL, CENTER, fmt="0")
        tr = th + 1 + len(codes)
        style_cell(ws.cell(tr, 1, "סה\"כ"), FB)
        for ci in range(2, 10):
            L = get_column_letter(ci)
            style_cell(ws.cell(tr, ci, '=IF(COUNT(%s%d:%s%d)=0,"",SUM(%s%d:%s%d))' % (L, th + 1, L, tr - 1, L, th + 1, L, tr - 1)),
                       FB, None, CENTER, fmt="0.0")
        cr_ = tr + 1
        style_cell(ws.cell(cr_, 1, "סקרים בחישוב"), FS)
        for j, o in enumerate(OUTLETS):
            f = '=COUNTIFS(%s,$B$3,%s,"%s",%s,"כן")' % (brng("A"), brng("C"), OUTLET_LABEL[o], brng("J"))
            style_cell(ws.cell(cr_, 2 + j, f), FS, None, CENTER, fmt="0")
        # per-channel exit polls by bloc
        ws.cell(ex0 - 1, 1, "מדגמים לפי גוש וערוץ (מגיליון 'מדגמים')").font = FB
        for ci, h in enumerate(["גוש"] + [header_label(key, o) for o in ["11", "12", "13"]], 1):
            style_cell(ws.cell(ex0, ci, h), FB, EXIT_FILL, CENTER)
        for i, code in enumerate(codes):
            r_ = ex0 + 1 + i
            style_cell(ws.cell(r_, 1, lab[code]), F)
            for j, o in enumerate(["11", "12", "13"]):
                crit = '%s,$B$3,%s,"%s"' % (xrng("A"), xrng("B"), OUTLET_LABEL[o])
                f = '=IF(COUNTIFS(%s)=0,"",SUMIFS(%s,%s,%s,$A%d))' % (crit, xrng("E"), crit, xrng("J"), r_)
                style_cell(ws.cell(r_, 2 + j, f), F, None, CENTER, fmt="0")
        # list assignment
        la = ex0 + len(codes) + 3
        ws.cell(la - 1, 1, "שיוך הרשימות לגושים (תוצאות מגיליון 'תוצאות')").font = FB
        for ci, h in enumerate(["רשימה", "מנדטים בפועל", "גוש", "הערה"], 1):
            style_cell(ws.cell(la, ci, h), FB, HEAD_FILL, CENTER)
        for i, (lname, seats, bloc, note) in enumerate(FINAL[key]):
            r_ = la + 1 + i
            style_cell(ws.cell(r_, 1, lname), F)
            style_cell(ws.cell(r_, 2, '=SUMIFS(%s,%s,$B$3,%s,$A%d)' % (rrng("C"), rrng("A"), rrng("B"), r_)), F, None, CENTER, fmt="0")
            style_cell(ws.cell(r_, 3, lab[bloc]), F, None, CENTER)
            c = ws.cell(r_, 4, note)
            c.font = FS
        nn = la + len(FINAL[key]) + 2
        for i, t in enumerate(BLOC_COL_NOTES.get(key, [])):
            ws.cell(nn + i, 1, "• בסקרים: " + t).font = FS
        c = ws.cell(nn + len(BLOC_COL_NOTES.get(key, [])), 1, "מקור הרכב הממשלה / ההמלצות: " + GOV_SRC[key])
        c.font = FLINK
        c.hyperlink = GOV_SRC[key]

        # pies
        for k, (col, ttl) in enumerate([(7, "ממוצע הסקרים"), (8, "ממוצע המדגמים"), (9, "תוצאה סופית")]):
            pie = PieChart()
            pie.title = ttl
            data = Reference(ws, min_col=col, min_row=th, max_row=th + len(codes))
            cats_ = Reference(ws, min_col=1, min_row=th + 1, max_row=th + len(codes))
            pie.add_data(data, titles_from_data=True)
            pie.set_categories(cats_)
            ser = pie.series[0]
            for idx, code in enumerate(codes):
                pt = DataPoint(idx=idx)
                pt.graphicalProperties.solidFill = BLOC_COLORS[code]
                pt.graphicalProperties.line.solidFill = "FFFFFF"
                ser.dPt.append(pt)
            ser.dLbls = DataLabelList()
            ser.dLbls.showVal = True
            ser.dLbls.showPercent = False
            ser.dLbls.showCatName = False
            ser.dLbls.showSerName = False
            ser.dLbls.showLeaderLines = False
            ser.dLbls.showLegendKey = False
            ser.dLbls.numFmt = "0.0"
            pie.legend.position = "b"
            pie.height = 8
            pie.width = 8.5
            ws.add_chart(pie, "%s%d" % (["K", "P", "U"][k], b0))

        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0

    # ------------------------------------------------------------ readme
    write_readme(readme, polls, top4)
    wb.save(OUT)
    print("saved", OUT, "data rows", last_data - 1, "exit rows", last_exit - 1)


def election_notes(key):
    n = {
        "2026": [
            "אין סקרים של הארץ בחלון.",
            "הציונות הדתית וזהות: לפני האיחוד ב-1.9.2026 נסכמו הרכיבים; בטבלאות שבהן זהות לא הופיעה בנפרד נספרה הציונות הדתית בלבד.",
            "הרשימה המשותפת: לפני 19.8.2026 נסכמו חד\"ש-תע\"ל + בל\"ד.",
            "המילואימניקים-המפלגה הכלכלית: לפני 6.9.2026 נספר 'הבית הציוני' (הנדל וטרופר), לפי החלטתך. ישר! לפני 6.9 נספרה כמו שהיא (בלי טרופר).",
            "עמך ישראל: לפני 25.8.2026 מופיעה כ'מפלגת וינטר'.",
            "בסקרים עם שני תרחישים נבחר התרחיש עם מה שקרה בפועל (פירוט בהערה של כל סקר).",
            "כחול לבן: הודיעה ב-19.10.2026 על פרישה מהמרוץ. היא נשארת ברשימות, והסקרים שלה עד אז נכללים (בכולם הייתה מתחת לאחוז החסימה).",
        ],
        "2022": [
            "אין סקרים של הארץ בחלון.",
            "הציונות הדתית: לפני 26.8.2022 (ריצה נפרדת של עוצמה יהודית) נסכמו הציונות הדתית + עוצמה; לפני 15.8 מופיעה הרשימה המשותפת המקורית.",
            "המחנה הממלכתי: עד 14.8.2022 מופיעה כ'כחול לבן-תקווה חדשה' (אותה רשימה, לפני הצטרפות איזנקוט).",
            "נכללו גם 'קשת' (סקר אחד) ו-Mako/ערוץ הכנסת (7 סקרים) כחדשות 12, לפי החלטתך.",
        ],
        "2021": [
            "אין סקרים של הארץ בחלון.",
            "יש עתיד: עד 10.1.2021 נסקרה 'יש עתיד-תל\"ם' - לפי החלטתך זו רשימה אחרת ולא נספרה.",
            "ימינה: עד הפיצול מהציונות הדתית (טבלאות ויקיפדיה שבהן אין עמודת הציונות הדתית) - לא נספר.",
            "נכלל סקר Mako אחד כחדשות 12, וסקר משותף אחד של מעריב/ג'רוזלם פוסט כמעריב.",
        ],
        "2020": [
            "אין סקרים של הארץ בחלון.",
            "העבודה-גשר-מרצ: לפני האיחוד ב-13.1.2020 נסכמו העבודה-גשר + המחנה הדמוקרטי.",
            "בסקרים עם כמה תרחישים נבחר התרחיש עם האיחוד שקרה (פירוט בגיליון 'סקרים').",
            "סקר אחד של רדיו כאן נספר ככאן 11.",
        ],
        "2019b": [
            "אין סקרים של הארץ בחלון.",
            "ימינה: לפני 29.7.2019 נסכמו איחוד מפלגות הימין + הימין החדש.",
            "סקרי 103FM/מעריב נספרו כמעריב; סקר רשת ב' נספר ככאן 11.",
        ],
        "2019a": [
            "כחול לבן: לפני 21.2.2019 נסכמו יש עתיד + חוסן לישראל (חוסן-תל\"ם).",
            "חד\"ש-תע\"ל: לפני הפירוק של הרשימה המשותפת (21.2.2019) - רשימה אחרת, לא נספר (לכן פחות סקרים).",
            "מדגמים: כאן 11 - נמצאה רק גרסת 22:00. חדשות 13 - עודכן בגרסה זו לעדכון הלילי המלא (העבודה 6, חד\"ש-תע\"ל 6; בגרסה הקודמת 7 ו-7 מגרסת 22:00).",
        ],
        "2015": [
            "ערוץ 2, ערוץ 10 וערוץ 1 מוצגים במקום חדשות 12, חדשות 13 וכאן 11.",
            "הרשימה המשותפת: לפני 22.1.2015 נסכמו חד\"ש + רע\"מ-תע\"ל + בל\"ד.",
            "סקרי רשת ב'/קול ישראל נספרו כערוץ 1; סקרי Nana 10 כערוץ 10; פרסומים משותפים של מעריב כמעריב.",
        ],
        "2013": [
            "ערוץ 2, ערוץ 10 וערוץ 1 מוצגים במקום חדשות 12, חדשות 13 וכאן 11.",
            "מדגמים: נמצאה רק גרסת 22:00.",
            "סקרי רשת ב'/קול ישראל נספרו כערוץ 1; סקרי Mako כערוץ 2.",
        ],
        "2009": [
            "ערוץ 2, ערוץ 10 וערוץ 1 מוצגים במקום חדשות 12, חדשות 13 וכאן 11.",
            "סקרים עם טווח (למשל 9-10) נספרו לפי אמצע הטווח.",
            "סקר משותף הארץ/ערוץ 10 נספר לשניהם; סקרי קול ישראל נספרו כערוץ 1.",
            "מדגמים: נמצאה גרסה אחת בלבד, ולא ברור אם היא העדכון האחרון.",
        ],
    }
    return n[key]


def write_readme(ws, polls, top4):
    ws.sheet_view.rightToLeft = True
    lines = [
        ("סקרי בחירות לכנסת - ממוצע 3 החודשים שלפני הבחירות לפי גוף, ומדגמי ליל הבחירות", FT),
        ("", F),
        ("מה יש בקובץ", FB),
        ("גיליון לכל מערכת בחירות (2009-2022): טבלה, גרף עמודות, מספר הסקרים בכל ממוצע, המדגמים לפי ערוץ, ואופן בחירת ארבע המפלגות.", F),
        ("גיליון 'סקרים': כל סקר שנכלל, לכל אחת מ-4 המפלגות, עם התאריך, הגוף, מכון הסקרים, הערך, הערה וקישור למקור. כל הממוצעים בגיליונות מחושבים בנוסחאות מגיליון זה.", F),
        ("גיליון 'מדגמים': ערכי המדגמים לפי ערוץ, הגרסה (עדכון לילי / 22:00 בלבד), השעה והמקור.", F),
        ("תאים בצבע צהוב = ערך שעבר טיפול מיוחד (סכימה, אמצע טווח, פרסום משותף, גרסה לא מעודכנת וכו'), עם הסבר בעמודת ההערה.", F),
        ("", F),
        ("כללי החישוב", FB),
        ("חלון הסקרים: מאותו תאריך שלושה חודשים לפני יום הבחירות ועד יום לפניו. סקר משויך לתאריך סיום העבודה עליו.", F),
        ("ממוצע לגוף: ממוצע פשוט של כל הסקרים של אותו גוף בחלון (כל סקר במשקל שווה). נבחר על פני ממוצע חודשי כי חודש עם סקר יחיד היה מקבל משקל מופרז.", F),
        ("ארבע המפלגות הגדולות: לפי ממוצע הממוצעים של הגופים (כל גוף במשקל שווה), מתוך הרשימות שהתמודדו בפועל.", F),
        ("מפלגה מתחת לאחוז החסימה בסקר = 0 מנדטים. סקר שלא הציג את המפלגה כלל - לא נספר.", F),
        ("איחוד במהלך החלון: סקרים מלפני האיחוד = סכום הרכיבים, מסומן (החלטתך).", F),
        ("פיצול במהלך החלון: הרשימה שלפני הפיצול היא רשימה אחרת ולא נספרת למפלגה שהתמודדה (החלטתך).", F),
        ("סקר עם כמה תרחישים: התרחיש עם האיחוד שקרה בפועל (החלטתך). טווח מנדטים: אמצע הטווח (החלטתך).", F),
        ("ממוצע המדגמים: ממוצע הגרסה המאוחרת ביותר שנמצאה של מדגם כל ערוץ טלוויזיה. למעריב ולהארץ אין מדגמים.", F),
        ("", F),
        ("גופים", FB),
        ("כאן 11, חדשות 12, חדשות 13, מעריב, הארץ. ב-2009-2015 מוצגים הקודמים: ערוץ 1 (רשות השידור) במקום כאן 11, ערוץ 2 במקום חדשות 12, ערוץ 10 במקום חדשות 13.", F),
        ("נספרו לפי החלטתך ומסומנים: פרסומים משותפים של מעריב; סקר משותף הארץ/ערוץ 10 (לשניהם); רדיו ציבורי (רשת ב', קול ישראל, רדיו כאן) ככאן 11/ערוץ 1; 'קשת', Mako ו-Nana 10 כערוץ שלהם.", F),
        ("", F),
        ("היקף ומגבלות", FB),
        ("הסקרים נלקחו מטבלאות ויקיפדיה האנגלית (Opinion polling for the ... Israeli legislative election); כל טבלה הועתקה ונבדקה מול גיבוב (hash) של הנתונים בדף.", F),
        ("ויקיפדיה היא אוסף משני: ייתכן שחסרים בה סקרים, וייתכנו בה טעויות שלא ניתן לאתר בלי ארכיוני המקור.", F),
        ("לפני 2009 לא נמצא תיעוד מסודר של סקרים לפי גוף לאורך 3 חודשים (ל-2006 יש רק את השבוע האחרון, בלי ציון הגוף), ולכן הקובץ מתחיל ב-2009.", F),
        ("בחירות 2026 (27.10.2026) עדיין לא התקיימו.", F),
        ("המדגמים אומתו מול כתבות חדשות מליל הבחירות (קישור לכל ערך). ערכי ויקיפדיה למדגמים הם לרוב גרסת 22:00, ולכן לא נלקחו ממנה כשנמצא עדכון.", F),
        ("", F),
        ("מפת הגושים (חדש בגרסה זו)", FB),
        ("בכל גיליון מערכת: טבלת גושים ו-3 עוגות - ממוצע הסקרים, ממוצע המדגמים והתוצאה הסופית.", F),
        ("קואליציה/אופוזיציה: לפי הרכב הממשלה הראשונה שהושבעה אחרי הבחירות. באפריל ובספטמבר 2019 לא הוקמה ממשלה, ולכן הגושים הם לפי ההמלצות לנשיא.", F),
        ("רשימה שהתפצלה אחרי הבחירות (2020: כחול לבן, העבודה-גשר-מרצ, ימינה; ספטמבר 2019: הרשימה המשותפת) שויכה לפי רוב חבריה. אותו כלל שימש לישויות שבסקרים לפני איחוד או פיצול.", F),
        ("ב-2020 השיוך לפי רוב חברי הרשימה נותן 85 מנדטים לקואליציה, אף שהממשלה בפועל נשענה על 73 ח\"כים - ראו הערות בגיליון 2020.", F),
        ("ב-2009 הממשלה הושבעה ב-31.3; יהדות התורה הצטרפה למחרת, ולכן לפי כלל ההשבעה היא באופוזיציה.", F),
        ("רשימות שלא עברו את אחוז החסימה מופיעות כפרוסה 'לא נכנסו לכנסת' (מנדטים שקיבלו בסקרים ובמדגמים).", F),
        ("ממוצע הסקרים בגושים: סכום הגוש בכל סקר, ממוצע לכל גוף, ואז ממוצע הגופים. רק סקרים שמסתכמים ב-120 (23 סקרים לא הסתכמו ב-120 ולא נכללו בגושים; ממוצעי המפלגות לא שונו). פירוט בגיליון 'גושים בסקרים'.", F),
        ("גיליון 'מדגמים' כולל עכשיו את כל המפלגות בכל מדגם (כל מדגם מסתכם ב-120); גיליון 'תוצאות' כולל את התוצאות הרשמיות ואת שיוך כל רשימה לגוש.", F),
        ("", F),
        ("סקרים לפי מערכת וגוף:", FB),
    ]
    for i, (t, f) in enumerate(lines, 1):
        c = ws.cell(i, 1, t)
        c.font = f
        c.alignment = Alignment(horizontal="right")
    r = len(lines) + 1
    heads = ["מערכת"] + [OUTLET_LABEL[o] for o in OUTLETS]
    for ci, h in enumerate(heads, 1):
        style_cell(ws.cell(r, ci, h), FB, HEAD_FILL, CENTER)
    for key in ORDER:
        r += 1
        style_cell(ws.cell(r, 1, SHEET[key]), F)
        for j, o in enumerate(OUTLETS):
            n = len([p for p in polls if p["election"] == key and p["outlet"] == o])
            style_cell(ws.cell(r, 2 + j, n), F, None, CENTER)
    ws.cell(r + 1, 1, "(מספר הסקרים הכולל לגוף; לחלק מהמפלגות נכללו פחות סקרים - ראו טבלת הספירה בכל גיליון)").font = FS
    ws.column_dimensions["A"].width = 14
    for j in range(2, 7):
        ws.column_dimensions[get_column_letter(j)].width = 12


if __name__ == "__main__":
    main()

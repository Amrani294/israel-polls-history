"""The 2026 election (Knesset 26, 27 Oct 2026): results and election-night exit polls.

Read on 30 Oct 2026, the day after the Central Elections Committee published the final
results ("תוצאות האמת הסופיות", night of 29-30 Oct). Every figure has its source next to it.

Seats   : identical in every report of the final results (Arutz 7, JDN, Calcalist, Haaretz,
          Kikar HaShabbat, i24NEWS). 11 lists passed the threshold; all others got 0.
Totals  : from the committee's statement, as quoted in the same reports.
Votes   : NOT on the site yet. The committee's results site (votes26.bechirot.gov.il) renders in
          the browser only and could not be read in this session, and the news reports give
          partial or disagreeing per-list counts (e.g. the Reservists: 154,585 in Haaretz,
          154,950 in Kikar HaShabbat). VOTES stays None until the committee's table is read.
Members : the first N candidates of each list in he26_candidates_raw.txt (N = seats), checked
          name by name against the list of the 120 elected in data/mk26_raw.txt (Kipa).
Exit    : the latest version of the night for Kan 11, N12 and N13 (user decision: only the three
          tracked channels, not Channel 14 or i24NEWS).
Blocs   : no government yet (user decision, 30 Oct 2026): the parties of the outgoing 37th
          government against all the other lists, as before the election (KIND "pre").
"""

FINAL_AS_OF = "2026-10-30"      # the night the committee published the final results

RESULTS_SRC = "https://www.inn.co.il/news/709660"
RESULTS_LINKS = [
    {"label": "ערוץ 7: פורסמו תוצאות האמת הסופיות (30.10.2026, 00:46)",
     "url": "https://www.inn.co.il/news/709660", "orig": ""},
    {"label": "JDN: תוצאות האמת הסופיות (30.10.2026, 07:41)",
     "url": "https://www.jdn.co.il/news/2757397/", "orig": ""},
    {"label": "תוצאות הבחירות לכנסת ה-26 (ועדת הבחירות המרכזית)",
     "url": "https://votes26.bechirot.gov.il/", "orig": ""},
]

# poll list name (config.py) -> seats. Sum 120.
SEATS = {
    "הליכוד": 27, "ישר!": 21, "ביחד": 12, "הרשימה המשותפת": 11, "הדמוקרטים": 8, "רע\"ם": 8,
    "ישראל ביתנו": 7, "עוצמה יהודית": 7, "יהדות התורה": 7, "ש\"ס": 6, "הציונות הדתית וזהות": 6,
    "המילואימניקים-המפלגה הכלכלית": 0, "עמך ישראל": 0, "הציבור החרדי": 0, "כחול לבן": 0,
}

TOTALS = dict(
    voters=5716665, valid=5690778, invalid=25887, turnout="77.9%",
    threshold="3.25% (184,947 קולות)",
    eligible=None,      # not in the committee's statement as reported
)

VOTES = None            # list name -> votes, once read from the committee's table

# Elected list: spelling differences between Kipa and the he-wiki candidate names
# (normalised: no spaces, quotes, apostrophes or hyphens). (list, place) -> reason.
SPELLING = {
    ("ישר!", 13): "כמיל אבו רוקן / כמיל אבו רוקון",
    ("ישר!", 16): "ענבר יחזקאלי / ענבר יחזקאלי בליליוס",
    ("הרשימה המשותפת", 10): "חסן אלנסאסרה / חסן נסאסרה",
    ("הרשימה המשותפת", 11): "היתם זחאלקה / הייתם זחאלקה",
    ("רע\"ם", 7): "איברהים אלטורי / אברהים אל טורי",
}
# he26 section -> list name used in mk26_raw.txt
MK_LIST = {"מפלגת ש\"ס": "ש\"ס", "הרשימה הערבית המאוחדת": "רע\"ם"}

# ------------------------------------------------------------ exit polls
U = "עדכון לילי (הגרסה המאוחרת ביותר שנמצאה)"

S12_ZMAN = "https://www.zman.co.il/live/737252/"
S12_WALLA = "https://www.walla.co.il/news/politics/383959142"
S12_MAARIV = "https://www.maariv.co.il/breaking-news/article-1382116"
S13 = "https://13tv.co.il/item/news/politics/politics/midgam-905425191/"
S_IH = "https://www.israelhayom.co.il/news/politics/article/21720077"

ZERO = {"המילואימניקים-המפלגה הכלכלית": 0, "עמך ישראל": 0, "הציבור החרדי": 0, "כחול לבן": 0}


def _ex(channel, actual, time, source, seats, note):
    s = dict(seats)
    s.update(ZERO)
    return dict(channel=channel, actual=actual, version=U, time=time, source=source,
                seats=s, note=note)


EXIT = [
    _ex("12", "חדשות 12", "02:28", S12_ZMAN,
        {"הליכוד": 27, "ישר!": 21, "ביחד": 12, "הרשימה המשותפת": 12, "הדמוקרטים": 9,
         "ישראל ביתנו": 7, "ש\"ס": 7, "רע\"ם": 7, "יהדות התורה": 6, "עוצמה יהודית": 6,
         "הציונות הדתית וזהות": 6},
        "עדכון 02:28 (זמן ישראל, 8 רשימות וגושים 52/49/19). יהדות התורה, עוצמה יהודית והציונות הדתית 6 כל אחת "
        "לפי וואלה ומעריב (שבו הציונות הדתית ירדה ל-6). וואלה מביא באותו עדכון ישראל ביתנו 8, בסתירה לגושים "
        "שבאותה כתבה; נלקח 7 (זמן ישראל, מעריב, מאקו). גרסת 22:00: הליכוד 24, ישר! 22 (ynet)."),
    _ex("13", "חדשות 13", "01:00", S13,
        {"הליכוד": 27, "ישר!": 22, "ביחד": 13, "הרשימה המשותפת": 11, "הדמוקרטים": 9,
         "ישראל ביתנו": 7, "רע\"ם": 7, "ש\"ס": 6, "יהדות התורה": 6, "עוצמה יהודית": 6,
         "הציונות הדתית וזהות": 6},
        "עדכון 01:00 מאתר חדשות 13. בטקסט של הכתבה כתוב שישר! קיבלה 23, אבל בפירוט המנדטים 22, "
        "וכך גם הגושים (51/51/18) וישראל היום; נלקח 22. גרסת 22:00: הליכוד 25, ישר! 23, ביחד 14."),
    _ex("11", "כאן 11", "לילה (לא צוינה שעה)", S13,
        {"הליכוד": 27, "ישר!": 21, "ביחד": 13, "הרשימה המשותפת": 11, "הדמוקרטים": 9,
         "ישראל ביתנו": 8, "רע\"ם": 7, "ש\"ס": 6, "יהדות התורה": 6, "עוצמה יהודית": 6,
         "הציונות הדתית וזהות": 6},
        "העדכון האחרון של כאן 11, כפי שפורט באתר חדשות 13; הגושים (51/51/18) אומתו בישראל היום. "
        "גרסת 22:00: הליכוד 25, ביחד 14, הדמוקרטים 10, עוצמה יהודית 7."),
]
EXIT_SRC_EXTRA = {"12": [S12_WALLA, S12_MAARIV], "13": [S_IH], "11": [S_IH]}


def self_check(tracked):
    assert sum(SEATS.values()) == 120, sum(SEATS.values())
    assert sorted(SEATS) == sorted(tracked), set(SEATS) ^ set(tracked)
    for e in EXIT:
        assert sum(e["seats"].values()) == 120, (e["channel"], sum(e["seats"].values()))
        assert sorted(e["seats"]) == sorted(tracked), (e["channel"], set(e["seats"]) ^ set(tracked))
    assert TOTALS["voters"] == TOTALS["valid"] + TOTALS["invalid"]
    if VOTES is not None:
        assert sorted(VOTES) == sorted(tracked)
    return True

"""The three-axis map of the 2026 lists (tools/data/axes_2026.txt -> data/axes.js).

Decisions (Yonatan, 23-24 Oct 2026):
- Three axes, each 0-10, integers only. 10 is always the "right" end: hawkish, conservative,
  capitalist. Every list that reached 4 seats in at least one 2026 poll on the site is scored.
- Each axis is split into indicators, each scored against fixed anchors (0/3/5/7/10 below; a score
  between two anchors is allowed). The axis score is the mean of the indicators that have
  evidence, rounded to an integer; an exact .5 is rounded towards 5 (no more extreme than the
  evidence). Fewer than two indicators with evidence = the axis is "unknown" (null).
- Evidence order: deeds (votes, laws, conduct in government) before platforms and statements.
  A law a party passed as a coalition price counts against it. The means are scored, not the
  goals (lower prices through competition is not socialism). Sectoral budgets (yeshiva stipends,
  the Arab-sector five-year plans) do not count on the economic axis. A joint list is scored by
  its dominant faction. Issues that belong to no axis (the judicial overhaul, the nation-state
  law) count only through their effect on an axis.
- No "newer evidence wins" rule (Yonatan declined it): deeds before words is the only tie-break.
- Every indicator score carries at least one source URL; the build fails otherwise.

File format (tools/data/axes_2026.txt), '|' separated, '#' starts a comment:
  U|key|url                         a source, referred to as @key
  N|list id|text                    a note on how the list was scored (shown on the page)
  I|list id|indicator|score|sources|text
      indicator  one of the keys in AXES below
      score      integer 0-10
      sources    space separated: @key or a full URL
      text       the evidence in one or two Hebrew sentences
An indicator without an I line has no evidence for that list.
"""
import os
from collections import OrderedDict

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

AXES = [
    dict(key="sec", he="ביטחוני", lo="יוני", hi="ניצי",
         scope="הסכסוך עם הפלסטינים, השטחים וההתנחלויות, שימוש בכוח (עזה, לבנון, איראן) ומשא ומתן.",
         indicators=[
             ("state", "מדינה פלסטינית", ["מדינה על קווי 67' עכשיו", "שתי מדינות כיעד, חילופי שטחים",
                                           "היפרדות, בלי מדינה בטווח הנראה", "אין מדינה לעולם, לכל היותר אוטונומיה",
                                           "סיפוח מלא בלי זכויות, או \"הגירה\""]),
             ("settle", "התנחלויות וריבונות", ["פינוי", "הקפאה מחוץ לגושים", "גושים ובקעת הירדן בלבד",
                                               "הרחבה וריבונות חלקית", "ריבונות מלאה והתיישבות בעזה"]),
             ("force", "שימוש בכוח", ["התנגדות לרוב המבצעים", "כוח כמוצא אחרון, עדיפות להסדרים",
                                      "כוח מלא כשמותקפים, לצד הסדרים", "מדיניות התקפית ומכות מנע",
                                      "כוח מרבי, הגירה כפתרון"]),
         ]),
    dict(key="soc", he="חברתי", lo="ליברלי", hi="שמרני",
         scope="יחסי דת ומדינה, נישואים, שבת, זכויות להט\"ב וגיוס חרדים (כשאלה של דת ומדינה).",
         indicators=[
             ("marriage", "נישואים ואישות", ["נישואים אזרחיים, גם חד-מיניים", "נישואים אזרחיים", "ברית זוגיות",
                                             "מונופול הרבנות", "הרחבת סמכויות בתי הדין הדתיים"]),
             ("shabbat", "שבת ומרחב ציבורי", ["תחבורה ומסחר בלי הגבלה", "החלטה של כל רשות מקומית", "סטטוס קוו",
                                              "החמרה ואכיפה", "אכיפה והפרדה מגדרית"]),
             ("lgbt", "להט\"ב", ["שוויון מלא, כולל פונדקאות ואימוץ", "תמיכה ברוב החקיקה", "עמדה מעורבת",
                                 "התנגדות לחקיקה", "התנגדות פעילה וביטול הישגים"]),
             ("draft", "גיוס חרדים", ["גיוס לכולם, עם סנקציות", "מסלולים ומכסה מוגבלת לפטור", "יעדים הדרגתיים",
                                      "פטור רחב בפועל", "פטור מלא בחוק"]),
         ]),
    dict(key="eco", he="כלכלי", lo="סוציאליסטי", hi="קפיטליסטי",
         scope="מסים, רווחה והוצאה ציבורית (לא מגזרית), הפרטה ורגולציה, איגודים ושוק העבודה.",
         indicators=[
             ("tax", "מסים", ["העלאה פרוגרסיבית חדה", "העלאה לעשירים", "שמירה על הקיים", "הורדה",
                              "מס אחיד וקיצוץ חד"]),
             ("welfare", "רווחה והוצאה (לא מגזרית)", ["הרחבה גדולה", "הרחבה", "רווחה ממוקדת", "צמצום", "קיצוץ עמוק"]),
             ("market", "שווקים ובעלות", ["הלאמה ופיקוח מחירים", "התנגדות להפרטה, פיקוח", "רפורמות תחרות",
                                          "הפרטה והסרת רגולציה", "הפרטה גורפת"]),
             ("labor", "עבודה ואיגודים", ["איגודים חזקים מאוד", "חיזוק האיגודים, העלאת שכר מינימום", "עמדה ניטרלית",
                                          "החלשת ההסתדרות, שוק עבודה גמיש", "פירוק האיגודים"]),
         ]),
]
ANCHOR_AT = [0, 3, 5, 7, 10]

# The political compass (compass.html): one question per indicator, five answers that sit on the
# indicator's anchors (same order as the anchors: 0, 3, 5, 7, 10). Written to be neutral:
# infinitives (no gender), the policy itself rather than a label for it, both names where the
# name is political ("יהודה ושומרון (הגדה המערבית)"), and no answer marked as the default.
# The order here is the order of the questions: the axes are interleaved.
COMPASS_INTRO = ("שאלה אחת לכל מדד במפת הצירים. בכל שאלה חמש תשובות, וכל תשובה היא אחד העוגנים שלפיהם דורגו "
                 "הרשימות. אפשר לדלג על שאלה ולחזור לשאלות קודמות.")
COMPASS = [
    ("state", "מה צריך להיות היחס לשאיפה למדינה פלסטינית?", [
        "להקים עכשיו מדינה פלסטינית בגבולות 1967",
        "לחתור להסכם של שתי מדינות, עם חילופי שטחים",
        "להיפרד מהפלסטינים, אבל בלי מדינה בעתיד הנראה לעין",
        "לא להקים מדינה פלסטינית אף פעם; לכל היותר אוטונומיה",
        "לספח את כל השטח בלי לתת לפלסטינים זכות הצבעה, או לעודד אותם להגר",
    ]),
    ("marriage", "איך צריך להתחתן בישראל?", [
        "נישואים אזרחיים לכל מי שרוצה, כולל זוגות חד-מיניים",
        "נישואים אזרחיים כאפשרות, לצד נישואים דתיים",
        "ברית זוגיות אזרחית למי שלא יכול או לא רוצה להתחתן דרך הרבנות",
        "נישואים ליהודים רק דרך הרבנות, כמו היום",
        "להרחיב את הסמכויות של בתי הדין הדתיים גם לתחומים נוספים",
    ]),
    ("tax", "מה לעשות עם המסים?", [
        "להעלות מסים באופן משמעותי, ויותר ככל שההכנסה גבוהה",
        "להעלות מסים רק על בעלי ההכנסות וההון הגבוהים",
        "להשאיר את המסים כמו שהם",
        "להוריד מסים",
        "מס אחיד לכולם והורדה חדה של המסים",
    ]),
    ("force", "מתי ישראל צריכה להשתמש בכוח צבאי (בעזה, בלבנון, מול איראן)?", [
        "כמעט אף פעם; להימנע מרוב המבצעים הצבאיים",
        "רק כמוצא אחרון; קודם לנסות להגיע להסדרים",
        "בכוח מלא כשתוקפים אותנו, ולצד זה לחתור להסדרים",
        "גם ביוזמה: מכות מנע ומדיניות התקפית",
        "בכוח מרבי, כולל עידוד הגירה של האוכלוסייה מאזורי הלחימה",
    ]),
    ("shabbat", "מה צריך להיות המצב בשבת במרחב הציבורי?", [
        "תחבורה ציבורית ומסחר בשבת בלי הגבלה",
        "כל רשות מקומית תחליט בעצמה",
        "להשאיר את ההסדרים הקיימים (הסטטוס קוו)",
        "להחמיר את ההגבלות בשבת ולאכוף אותן",
        "לאכוף את השבת, וגם הפרדה בין גברים לנשים במרחב הציבורי",
    ]),
    ("welfare", "כמה המדינה צריכה להוציא על רווחה ושירותים ציבוריים (לכלל האוכלוסייה)?", [
        "להגדיל מאוד את ההוצאה",
        "להגדיל את ההוצאה",
        "לשמור על ההוצאה, ולמקד את העזרה במי שהכי צריך",
        "לצמצם את ההוצאה",
        "לקצץ את ההוצאה באופן עמוק",
    ]),
    ("settle", "מה לעשות עם ההתנחלויות ביהודה ושומרון (הגדה המערבית)?", [
        "לפנות את ההתנחלויות",
        "להקפיא את הבנייה מחוץ לגושי ההתיישבות הגדולים",
        "להשאיר בידי ישראל רק את הגושים הגדולים ואת בקעת הירדן",
        "להרחיב את ההתיישבות ולהחיל ריבונות ישראלית על חלק מהשטח",
        "להחיל ריבונות על כל השטח ולחדש את ההתיישבות גם ברצועת עזה",
    ]),
    ("lgbt", "מה צריך להיות היחס בחוק לזוגות ולמשפחות של להט\"ב?", [
        "שוויון מלא, כולל פונדקאות ואימוץ",
        "לתמוך ברוב החוקים שמרחיבים את הזכויות",
        "תלוי בחוק: בחלק כן ובחלק לא",
        "להתנגד לחוקים חדשים בנושא",
        "לבטל גם זכויות שכבר ניתנו",
    ]),
    ("market", "מה צריך להיות התפקיד של המדינה בשווקים ובבעלות על חברות?", [
        "להלאים חברות מרכזיות ולפקח על המחירים",
        "להתנגד להפרטות ולהגביר את הפיקוח",
        "רפורמות שמגבירות את התחרות",
        "להפריט ולהסיר רגולציה",
        "להפריט כמעט כל מה שנמצא בידי המדינה",
    ]),
    ("draft", "מה לעשות עם גיוס חרדים לצבא?", [
        "גיוס לכולם, עם סנקציות על מי שלא מתגייס",
        "גיוס, עם מסלולים מותאמים ומכסה מוגבלת של פטורים",
        "יעדי גיוס שעולים בהדרגה",
        "פטור רחב בפועל לתלמידי ישיבות",
        "פטור מלא, מעוגן בחוק",
    ]),
    ("labor", "מה צריך להיות הכוח של האיגודים המקצועיים בשוק העבודה?", [
        "איגודים חזקים מאוד, עם השפעה רבה על השכר והתנאים",
        "לחזק את האיגודים ולהעלות את שכר המינימום",
        "להשאיר את המצב כמו שהוא",
        "להחליש את ההסתדרות ולהגמיש את שוק העבודה",
        "לפרק את האיגודים",
    ]),
]

RULES = [
    "לכל רשימה ציון לכל מדד: מספר שלם בין 0 ל-10, לפי העוגן הקרוב (מותר בין שני עוגנים).",
    "ציון הציר הוא ממוצע המדדים שיש עליהם ראיות, מעוגל למספר שלם; ממוצע שבדיוק באמצע (x.5) מעוגל לכיוון 5, כדי לא לטעון לעמדה קיצונית יותר ממה שהראיות מראות.",
    "פחות משני מדדים עם ראיות: הציר \"לא ידוע\". במפה הרשימה מוצגת כקו מקווקו לכל אורך הציר הזה.",
    "מעשים לפני הצהרות: הצבעות, חקיקה והתנהלות בממשלה קודמים למצעים ולהתבטאויות. חוק שמפלגה העבירה כמחיר קואליציוני נספר לחובתה.",
    "מעריכים את האמצעי ולא את המטרה: הורדת מחירים בעזרת תחרות היא לא סוציאליזם.",
    "תקציבים מגזריים (מלגות לבני ישיבות, תוכניות החומש לחברה הערבית) לא נספרים בציר הכלכלי.",
    "רשימה משותפת מקבלת ציון לפי הסיעה הדומיננטית בה, והפער בין הסיעות נכתב בהערה.",
    "נושאים שאינם שייכים לאף ציר (הרפורמה המשפטית, חוק הלאום) נספרים רק דרך ההשפעה שלהם על אחד הצירים.",
]


def die(msg):
    raise SystemExit("axes_2026.txt: " + msg)


def axis_score(values):
    """Mean of the indicators with evidence; .5 rounds towards 5; fewer than two = None."""
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None
    m = sum(vals) / float(len(vals))
    lo = int(m // 1)
    frac = m - lo
    if abs(frac - 0.5) < 1e-9:
        return lo if m > 5 else lo + 1
    return int(round(m))


def load(list_ids):
    """Read the file and return the data/axes.js object. list_ids = the ids of the 2026 lists."""
    ind_keys = OrderedDict()
    for ax in AXES:
        for k, _, anchors in ax["indicators"]:
            if len(anchors) != len(ANCHOR_AT):
                die("indicator %s needs %d anchors" % (k, len(ANCHOR_AT)))
            ind_keys[k] = ax["key"]
    urls, notes, ind = {}, {}, OrderedDict()
    for n, line in enumerate(open(os.path.join(DATA, "axes_2026.txt"), encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("|")
        where = "line %d" % n
        if f[0] == "U":
            if len(f) != 3 or not f[2].startswith("https://"):
                die("%s bad source line" % where)
            if f[1] in urls:
                die("%s duplicate source key %s" % (where, f[1]))
            urls[f[1]] = f[2]
        elif f[0] == "N":
            if len(f) != 3 or f[1] not in list_ids:
                die("%s bad note line" % where)
            notes[f[1]] = f[2]
        elif f[0] == "I":
            if len(f) != 6:
                die("%s has %d fields, expected 6" % (where, len(f)))
            _, lid, key, score, srcs, text = f
            if lid not in list_ids:
                die("%s unknown list %r" % (where, lid))
            if key not in ind_keys:
                die("%s unknown indicator %r" % (where, key))
            if not score.isdigit() or not 0 <= int(score) <= 10:
                die("%s score must be an integer 0-10" % where)
            links = []
            for s in srcs.split():
                if s.startswith("@"):
                    if s[1:] not in urls:
                        die("%s unknown source %s (U lines must come first)" % (where, s))
                    links.append(urls[s[1:]])
                elif s.startswith("https://"):
                    links.append(s)
                else:
                    die("%s bad source %r" % (where, s))
            if not links:
                die("%s indicator without a source" % where)
            if not text.strip():
                die("%s indicator without a text" % where)
            if (lid, key) in ind:
                die("%s duplicate %s/%s" % (where, lid, key))
            ind[(lid, key)] = dict(score=int(score), text=text.strip(), urls=links)
        else:
            die("%s unknown record type %r" % (where, f[0]))
    scored = sorted({lid for lid, _ in ind}, key=list_ids.index)
    lists = OrderedDict()
    for lid in scored:
        entry = OrderedDict(note=notes.get(lid, ""), axes=OrderedDict())
        for ax in AXES:
            items = OrderedDict()
            for k, _, _ in ax["indicators"]:
                items[k] = ind.get((lid, k))
            score = axis_score([v["score"] if v else None for v in items.values()])
            entry["axes"][ax["key"]] = OrderedDict(score=score, n=sum(1 for v in items.values() if v),
                                                   ind=items)
        lists[lid] = entry
    for lid in notes:
        if lid not in lists:
            die("note for %s, which has no indicators" % lid)
    seen = [k for k, _, _ in COMPASS]
    if sorted(seen) != sorted(ind_keys) or len(seen) != len(set(seen)):
        die("COMPASS needs exactly one question per indicator")
    for k, q, answers in COMPASS:
        if not q.strip() or len(answers) != len(ANCHOR_AT) or not all(a.strip() for a in answers):
            die("COMPASS question %s needs a text and %d answers" % (k, len(ANCHOR_AT)))
    out = OrderedDict(
        election="2026",
        anchorsAt=ANCHOR_AT,
        axes=[OrderedDict(key=a["key"], he=a["he"], lo=a["lo"], hi=a["hi"], scope=a["scope"],
                          indicators=[OrderedDict(key=k, he=he, anchors=anc) for k, he, anc in a["indicators"]])
              for a in AXES],
        rules=RULES,
        compass=OrderedDict(intro=COMPASS_INTRO, questions=[
            OrderedDict(ind=k, axis=ind_keys[k], q=q, answers=a) for k, q, a in COMPASS]),
        lists=lists,
    )
    return out


def self_check():
    assert axis_score([7, 7, 8]) == 7
    assert axis_score([6, 3, 6, 7]) == 5          # 5.5 -> towards 5
    assert axis_score([4, 7]) == 5                # 5.5 -> towards 5
    assert axis_score([8, 7, 8, 7]) == 7          # 7.5 -> towards 5
    assert axis_score([3, 4]) == 4                # 3.5 -> towards 5
    assert axis_score([0, 0, 1]) == 0
    assert axis_score([0, None, None, None]) is None

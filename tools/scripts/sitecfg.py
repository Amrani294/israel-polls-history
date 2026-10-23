"""Website configuration: how each final list maps to the collected sources.

Every value here is either copied from a verified extract in data/ (and the
builder re-checks it against that extract) or is a manual mapping whose
source is named next to it.
"""

KNESSET = {"2009": "18", "2013": "19", "2015": "20", "2019a": "21", "2019b": "22",
           "2020": "23", "2021": "24", "2022": "25"}

HE_ELECTION_ARTICLE = {
    "2009": "הבחירות לכנסת השמונה עשרה", "2013": "הבחירות לכנסת התשע עשרה",
    "2015": "הבחירות לכנסת העשרים", "2019a": "הבחירות לכנסת העשרים ואחת",
    "2019b": "הבחירות לכנסת העשרים ושתיים", "2020": "הבחירות לכנסת העשרים ושלוש",
    "2021": "הבחירות לכנסת העשרים וארבע", "2022": "הבחירות לכנסת העשרים וחמש",
}

# First government sworn in after each election (None = no government formed).
GOVERNMENT = {
    "2022": ("הממשלה ה-37", "2022-12-29", "בנימין נתניהו"),
    "2021": ("הממשלה ה-36", "2021-06-13", "נפתלי בנט (ברוטציה עם יאיר לפיד)"),
    "2020": ("הממשלה ה-35", "2020-05-17", "בנימין נתניהו (ברוטציה עם בני גנץ)"),
    "2019b": None,
    "2019a": None,
    "2015": ("הממשלה ה-34", "2015-05-14", "בנימין נתניהו"),
    "2013": ("הממשלה ה-33", "2013-03-18", "בנימין נתניהו"),
    "2009": ("הממשלה ה-32", "2009-03-31", "בנימין נתניהו"),
}

# Candidates recommended to the President after the election, and where it was read.
CANDIDATES = {"N": "בנימין נתניהו", "L": "ציפי לבני", "H": "יצחק הרצוג", "G": "בני גנץ",
              "Y": "יאיר לפיד", "B": "נפתלי בנט", "-": "לא המליץ על אף מועמד"}
REC_SRC = {
    "2022": "https://en.wikipedia.org/wiki/Thirty-seventh_government_of_Israel",
    "2021": "https://en.wikipedia.org/wiki/Thirty-sixth_government_of_Israel",
    "2020": "https://en.wikipedia.org/wiki/Thirty-fifth_government_of_Israel",
    "2019b": "https://en.wikipedia.org/wiki/Thirty-fifth_government_of_Israel",
    "2019a": "https://en.wikipedia.org/wiki/Thirty-fifth_government_of_Israel",
    "2015": "https://en.wikipedia.org/wiki/2015_Israeli_legislative_election",
    "2013": "https://en.wikipedia.org/wiki/2013_Israeli_legislative_election",
    "2009": "https://he.wikipedia.org/wiki/%D7%94%D7%91%D7%97%D7%99%D7%A8%D7%95%D7%AA_%D7%9C%D7%9B%D7%A0%D7%A1%D7%AA_%D7%94%D7%A9%D7%9E%D7%95%D7%A0%D7%94_%D7%A2%D7%A9%D7%A8%D7%94",
}
REC_NOTE = {
    "2021": "סבב ההמלצות הראשון (5.4.2021), אחרי הבחירות.",
    "2009": "המקור מציין 65 ממליצים על נתניהו ו-28 על לבני; השיוך לרשימות נגזר מהסכום (65 = הליכוד, ישראל ביתנו, ש\"ס, יהדות התורה, האיחוד הלאומי, הבית היהודי), ושאר 27 הח\"כים לא המליצו.",
}

# Political position on the English Wikipedia party infobox.
# en title -> (exact infobox text, Hebrew rendering, axis low, axis high, note)
# Axis: -3 far-left, -2 left-wing, -1 centre-left, 0 centre, 1 centre-right,
# 2 right-wing, 3 far-right. None = not given.
POSITION = {
    "Likud": ("Right-wing", "ימין", 2, 2, ""),
    "Israeli Labor Party": ("Centre-left", "מרכז-שמאל", -1, -1, ""),
    "Meretz": ("Left-wing", "שמאל", -2, -2, ""),
    "United Torah Judaism": ("Social: ; Right-wing; Economic:; Centre-left",
                             "חברתית: ימין; כלכלית: מרכז-שמאל", 2, 2,
                             "בציר מוצג המיקום החברתי (ימין); כלכלית המקור מגדיר מרכז-שמאל"),
    "Shas": ("Fiscal: Centre-left; Social: Right-wing", "כלכלית: מרכז-שמאל; חברתית: ימין", 2, 2,
             "בציר מוצג המיקום החברתי (ימין); כלכלית המקור מגדיר מרכז-שמאל"),
    "Ra'am": ("", "לא מצוין בתיבת המידע", None, None, ""),
    "Yisrael Beiteinu": ("Right-wing", "ימין", 2, 2, ""),
    "Otzma Yehudit": ("Far-right", "ימין קיצוני", 3, 3, ""),
    "Hadash–Ta'al": ("Left-wing", "שמאל", -2, -2, ""),
    "The Jewish Home": ("Far-right", "ימין קיצוני", 3, 3, ""),
    "Balad (political party)": ("Left-wing to far-left", "שמאל עד שמאל קיצוני", -3, -2, ""),
    "Yesh Atid": ("Centre", "מרכז", 0, 0, ""),
    "Joint List": ("Left-wing", "שמאל", -2, -2, ""),
    "Blue and White (political alliance)": ("Centre", "מרכז", 0, 0, ""),
    "Blue and White (political party)": ("Centre", "מרכז", 0, 0, ""),
    "Yamina": ("Right-wing to far-right", "ימין עד ימין קיצוני", 2, 3, ""),
    "Labor-Gesher": ("Centre-left", "מרכז-שמאל", -1, -1, ""),
    "Labor-Gesher-Meretz": ("Centre-left", "מרכז-שמאל", -1, -1, ""),
    "New Hope (Israel)": ("Centre-right to right-wing", "מרכז-ימין עד ימין", 1, 2, ""),
    "Religious Zionist Party": ("Far-right", "ימין קיצוני", 3, 3, ""),
    "National Unity (Israel)": ("Centre to centre-right", "מרכז עד מרכז-ימין", 0, 1, ""),
    "National Union (Israel)": ("Right-wing to far-right", "ימין עד ימין קיצוני", 2, 3, ""),
    "Hadash": ("Left-wing to far-left", "שמאל עד שמאל קיצוני", -3, -2, ""),
    "Kadima": ("Centre", "מרכז", 0, 0, ""),
    "Hatnua": ("Centre to centre-left", "מרכז עד מרכז-שמאל", -1, 0, ""),
    "Likud Yisrael Beiteinu": ("Right-wing", "ימין", 2, 2, ""),
    "Zionist Union": ("Centre-left", "מרכז-שמאל", -1, -1, ""),
    "Kulanu": ("Centre to centre-right", "מרכז עד מרכז-ימין", 0, 1, ""),
    "Yachad (political party)": ("Right-wing to far-right", "ימין עד ימין קיצוני", 2, 3, ""),
    "Zehut": ("Right-wing to far-right", "ימין עד ימין קיצוני", 2, 3, ""),
    "Gesher (2019 political party)": ("Centre", "מרכז", 0, 0, ""),
    "New Right (Israel)": ("Right-wing to far-right", "ימין עד ימין קיצוני", 2, 3, ""),
    "Union of Right-Wing Parties": ("Right-wing to far-right", "ימין עד ימין קיצוני", 2, 3, ""),
    "Democratic Union (Israel)": ("Centre-left to left-wing", "מרכז-שמאל עד שמאל", -2, -1, ""),
}
NO_EN = ("", "אין ערך בוויקיפדיה האנגלית", None, None, "")

# slug -> (Hebrew Wikipedia article, English Wikipedia article or None)
PARTY = {
    "likud": ("הליכוד", "Likud"),
    "yesh-atid": ("יש עתיד", "Yesh Atid"),
    "rzp": ("הציונות הדתית (רשימה)", "Religious Zionist Party"),
    "national-unity": ("המחנה הממלכתי", "National Unity (Israel)"),
    "shas": ("מפלגת ש\"ס", "Shas"),
    "utj": ("יהדות התורה", "United Torah Judaism"),
    "yb": ("ישראל ביתנו", "Yisrael Beiteinu"),
    "raam": ("הרשימה הערבית המאוחדת", "Ra'am"),
    "hadash-taal": ("חד\"ש-תע\"ל", "Hadash–Ta'al"),
    "labor": ("מפלגת העבודה הישראלית", "Israeli Labor Party"),
    "meretz": ("מרצ", "Meretz"),
    "balad": ("ברית לאומית דמוקרטית", "Balad (political party)"),
    "jewish-home": ("הבית היהודי", "The Jewish Home"),
    "blue-white": ("כחול לבן (רשימה)", "Blue and White (political alliance)"),
    "yamina": ("ימינה", "Yamina"),
    "joint-list": ("הרשימה המשותפת", "Joint List"),
    "new-hope": ("תקווה חדשה (מפלגה)", "New Hope (Israel)"),
    "labor-gesher-meretz": ("העבודה-גשר-מרצ", "Labor-Gesher-Meretz"),
    "otzma": ("עוצמה יהודית", "Otzma Yehudit"),
    "labor-gesher": ("העבודה-גשר", "Labor-Gesher"),
    "democratic-union": ("המחנה הדמוקרטי", "Democratic Union (Israel)"),
    "urwp": ("איחוד מפלגות הימין", "Union of Right-Wing Parties"),
    "kulanu": ("כולנו (מפלגה)", "Kulanu"),
    "raam-balad": ("רע\"מ-בל\"ד", None),
    "new-right": ("הימין החדש", "New Right (Israel)"),
    "zehut": ("זהות (מפלגה)", "Zehut"),
    "gesher": ("מפלגת גשר (2018)", "Gesher (2019 political party)"),
    "zionist-union": ("המחנה הציוני", "Zionist Union"),
    "yachad": ("יחד - העם איתנו", "Yachad (political party)"),
    "likud-beiteinu": ("הליכוד - ישראל ביתנו", "Likud Yisrael Beiteinu"),
    "hatnua": ("התנועה", "Hatnua"),
    "raam-taal": ("רע\"מ-תע\"ל", None),
    "hadash": ("החזית הדמוקרטית לשלום ולשוויון", "Hadash"),
    "kadima": ("קדימה (מפלגה)", "Kadima"),
    "otzma-leisrael": ("עוצמה לישראל", "Otzma Yehudit"),
    "am-shalem": ("עם שלם", None),
    "national-union": ("האיחוד הלאומי", "National Union (Israel)"),
}
EN_OVERRIDE = {("2021", "blue-white"): "Blue and White (political party)"}
EN_NOTE = {
    "otzma-leisrael": "בוויקיפדיה האנגלית 'עוצמה לישראל' מפנה לערך של עוצמה יהודית (אותה מפלגה, ששינתה את שמה).",
    "raam-taal": "אין ערך נפרד לרשימה בוויקיפדיה האנגלית; בערך של רע\"מ אין שדה מיקום פוליטי.",
    "raam-balad": "אין ערך נפרד לרשימה בוויקיפדיה האנגלית.",
    "am-shalem": "בוויקיפדיה האנגלית 'עם שלם' מפנה לרשימת מפלגות קטנות, בלי שדה מיקום פוליטי.",
}

# Per election: final list name (as in blocs.FINAL) -> (slug, ballot letters,
# recommendation code, recommendation note, faction rules).
# Faction rules: faction names from the Knesset article tables (data/mk_raw.txt)
# whose initial members were elected on this list. ("@name") = single member.
LISTS = {
    "2022": {
        "הליכוד": ("likud", "מחל", "N", "", ["הליכוד"]),
        "יש עתיד": ("yesh-atid", "פה", "Y", "", ["יש עתיד", "סיעת יחיד"]),
        "הציונות הדתית": ("rzp", "ט", "N", "", ["הציונות הדתית", "עוצמה יהודית", "נעםחבר אחד"]),
        "המחנה הממלכתי": ("national-unity", "כן", "-", "", ["כחול לבן - המחנה הממלכתי", "הימין הממלכתי"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "ישראל ביתנו": ("yb", "ל", "-", "", ["ישראל ביתנו"]),
        "רע\"מ": ("raam", "עם", "-", "", ["רע\"מ"]),
        "חד\"ש-תע\"ל": ("hadash-taal", "ום", "-", "", ["חד\"ש-תע\"ל"]),
        "העבודה": ("labor", "אמת", "Y", "", ["העבודה"]),
        "מרצ": ("meretz", "מרצ", None, "", []),
        "בל\"ד": ("balad", "ד", None, "", []),
        "הבית היהודי": ("jewish-home", "ב", None, "", []),
    },
    "2021": {
        "הליכוד": ("likud", "מחל", "N", "", ["הליכוד"]),
        "יש עתיד": ("yesh-atid", "פה", "Y", "", ["יש עתיד"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס"]),
        "כחול לבן": ("blue-white", "כן", "Y", "", ["כחול לבן"]),
        "ימינה": ("yamina", "ב", "B", "", ["ימינה", "המחנה הממלכתי", "ח\"כ יחיד", "חופש כלכלי"]),
        "העבודה": ("labor", "אמת", "Y", "", ["העבודה"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "ישראל ביתנו": ("yb", "ל", "Y", "", ["ישראל ביתנו"]),
        "הציונות הדתית": ("rzp", "ט", "N", "", ["הציונות הדתית"]),
        "הרשימה המשותפת": ("joint-list", "ודעם", "-", "", ["הרשימה המשותפת"]),
        "תקווה חדשה": ("new-hope", "ת", "-", "", ["תקווה חדשה"]),
        "מרצ": ("meretz", "מרצ", "Y", "", ["מרצ"]),
        "רע\"מ": ("raam", "עם", "-", "", ["רע\"מ"]),
    },
    "2020": {
        "הליכוד": ("likud", "מחל", "N", "", ["הליכוד"]),
        "כחול לבן": ("blue-white", "פה", "G", "", ["כחול לבן", "יש עתיד – תל\"ם", "דרך ארץ"]),
        "הרשימה המשותפת": ("joint-list", "ודעם", "G", "", ["הרשימה המשותפת", "רע\"מ"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "העבודה-גשר-מרצ": ("labor-gesher-meretz", "אמת", "G",
                            "העבודה (3) ומרצ (3) המליצו על גנץ; גשר (אורלי לוי-אבקסיס) לא המליצה",
                            ["העבודה", "מרצ", "גשר"]),
        "ישראל ביתנו": ("yb", "ל", "G", "", ["ישראל ביתנו"]),
        "ימינה": ("yamina", "טב", "N", "", ["ימינה", "האיחוד הלאומי", "הבית היהודי"]),
        "עוצמה יהודית": ("otzma", "נץ", None, "", []),
    },
    "2019b": {
        "כחול לבן": ("blue-white", "פה", "G", "", ["כחול לבן"]),
        "הליכוד": ("likud", "מחל", "N", "", ["הליכוד"]),
        "הרשימה המשותפת": ("joint-list", "ודעם", "G",
                           "10 מתוך 13 ח\"כים המליצו על גנץ; 3 ח\"כי בל\"ד לא המליצו",
                           ["הרשימה המשותפת"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס"]),
        "ישראל ביתנו": ("yb", "ל", "-", "", ["ישראל ביתנו"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "ימינה": ("yamina", "טב", "N", "", ["הבית היהודי-האיחוד הלאומי", "הימין החדש"]),
        "העבודה-גשר": ("labor-gesher", "אמת", "G", "", ["העבודה-גשר"]),
        "המחנה הדמוקרטי": ("democratic-union", "מרצ", "G", "", ["המחנה הדמוקרטי"]),
        "עוצמה יהודית": ("otzma", "כף", None, "", []),
    },
    "2019a": {
        "הליכוד": ("likud", "מחל", "N", "", ["הליכוד", "אח\"י"]),
        "כחול לבן": ("blue-white", "פה", "G", "", ["כחול לבן"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "חד\"ש-תע\"ל": ("hadash-taal", "ום", "-", "", ["חד\"ש-תע\"ל"]),
        "העבודה": ("labor", "אמת", "G", "", ["העבודה"]),
        "ישראל ביתנו": ("yb", "ל", "N", "", ["ישראל ביתנו"]),
        "איחוד מפלגות הימין": ("urwp", "טב", "N", "", ["איחוד מפלגות הימין"]),
        "מרצ": ("meretz", "מרצ", "G", "", ["מרצ"]),
        "כולנו": ("kulanu", "כ", "N", "", ["כולנו"]),
        "רע\"מ-בל\"ד": ("raam-balad", "דעם", "-", "", ["רע\"מ", "בל\"ד"]),
        "הימין החדש": ("new-right", "נ", None, "", []),
        "זהות": ("zehut", "ז", None, "", []),
        "גשר": ("gesher", "נר", None, "", []),
    },
    "2015": {
        "הליכוד": ("likud", "מחל", "N", "", ["הליכוד"]),
        "המחנה הציוני": ("zionist-union", "אמת", "H", "", ["העבודה", "התנועה"]),
        "הרשימה המשותפת": ("joint-list", "ודעם", "-", "", ["הרשימה המשותפת", "תע\"ל"]),
        "יש עתיד": ("yesh-atid", "פה", "-", "", ["יש עתיד"]),
        "כולנו": ("kulanu", "כ", "N", "", ["כולנו"]),
        "הבית היהודי": ("jewish-home", "טב", "N", "", ["הבית היהודי", "הימין החדש"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס"]),
        "ישראל ביתנו": ("yb", "ל", "N", "", ["ישראל ביתנו", "ח\"כ יחיד"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "מרצ": ("meretz", "מרצ", "H", "", ["מרצ"]),
        "יחד": ("yachad", "קץ", None, "", []),
    },
    "2013": {
        "הליכוד ביתנו": ("likud-beiteinu", "מחל", "N", "", ["הליכוד", "ישראל ביתנו"]),
        "יש עתיד": ("yesh-atid", "פה", "N", "", ["יש עתיד"]),
        "העבודה": ("labor", "אמת", "-", "", ["העבודה"]),
        "הבית היהודי": ("jewish-home", "טב", "N", "", ["הבית היהודי"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "התנועה": ("hatnua", "צפ", "-", "", ["התנועה"]),
        "מרצ": ("meretz", "מרצ", "-", "", ["מרצ"]),
        "רע\"מ-תע\"ל": ("raam-taal", "עם", "-", "", ["רע\"מ-תע\"ל-מד\"ע"]),
        "חד\"ש": ("hadash", "ו", "-", "", ["חד\"ש"]),
        "בל\"ד": ("balad", "ד", "-", "", ["בל\"ד"]),
        "קדימה": ("kadima", "כן", "N", "", ["קדימה"]),
        "עוצמה לישראל": ("otzma-leisrael", "נץ", None, "", []),
        "עם שלם": ("am-shalem", "ץ", None, "", []),
    },
    "2009": {
        "קדימה": ("kadima", "כן", "L", "", ["קדימה", "התנועה"]),
        "הליכוד": ("likud", "מחל", "N", "", ["הליכוד"]),
        "ישראל ביתנו": ("yb", "ל", "N", "", ["ישראל ביתנו", "??"]),
        "העבודה": ("labor", "אמת", "-", "", ["העצמאות", "העבודה"]),
        "ש\"ס": ("shas", "שס", "N", "", ["ש\"ס", "סיעת יחיד"]),
        "יהדות התורה": ("utj", "ג", "N", "", ["יהדות התורה"]),
        "רע\"מ-תע\"ל": ("raam-taal", "עם", "-", "", ["רע\"מ-תע\"ל-מד\"ע"]),
        "האיחוד הלאומי": ("national-union", "ט", "N", "", ["האיחוד הלאומי", "עוצמה לישראל"]),
        "חד\"ש": ("hadash", "ו", "-", "", ["חד\"ש"]),
        "מרצ": ("meretz", "מרצ", "-", "", ["מרצ"]),
        "הבית היהודי": ("jewish-home", "ב", "N", "", ["הבית היהודי"]),
        "בל\"ד": ("balad", "ד", "-", "", ["בל\"ד"]),
    },
}

# A member listed in one faction but elected on another list.
MEMBER_MOVES = {("2021", "אופיר סופר"): ("הציונות הדתית", "הליכוד")}
MOVE_NOTE = {("2021", "אופיר סופר"): "שוריין במקום ה-28 ברשימת הליכוד (איש האיחוד הלאומי, לפי הסכם עם סמוטריץ'), וביוני 2021 עבר לסיעת הציונות הדתית"}

# Leader names in the results tables that differ from the Hebrew Wikipedia title.
LEADER_TITLE = {
    "יעקב כץ": "יעקב כץ (כצל'ה)",
    "איתמר בן-גביר": "איתמר בן גביר",
}

# Official links missing from the Hebrew Wikipedia results section (read on gov.il,
# the landing page of the Central Elections Committee for the 23rd Knesset).
EXTRA_LINKS = {
    "2020": [
        {"label": "רשימות המועמדים לכנסת ה-23 (ועדת הבחירות המרכזית, gov.il)",
         "url": "https://www.gov.il/he/pages/candidates-lists-23", "orig": ""},
        {"label": "תוצאות הבחירות לכנסת ה-23 (ועדת הבחירות המרכזית)",
         "url": "https://votes23.bechirot.gov.il/", "orig": ""},
    ],
}


# ================================================================== 2026 (before the election)
# Built by build_site_data.upcoming(); no results yet. Sources:
#   lists, ballot letters, candidates  -> data/he26_candidates_raw.txt (he-wiki rev 44066081,
#                                          section per list, infobox list of candidates;
#                                          checked again against rev 44093533 on 20 Oct 2026:
#                                          same, except that rev 44093533 lists Sami Abu Shehadeh
#                                          3rd on the Joint List although its text says he withdrew
#                                          on 2 Oct - kept without him, user decision)
#   political positions (new articles)  -> data/en_positions_2026_check.txt
#   portraits of new candidates         -> data/img26_raw.txt (Wikidata P18 + Commons credits)
#   polls                               -> data/raw_2026.txt (made by make_raw_2026.py)
UPCOMING = {
    "2026": dict(
        knesset="26",
        he_article="הבחירות לכנסת העשרים ושש",
        en_article="2026 Israeli legislative election",
        as_of="2026-10-24",            # the day the sources were read (shown as "updated")
        outgoing=("הממשלה ה-37", "https://en.wikipedia.org/wiki/Thirty-seventh_government_of_Israel"),
        links=[
            {"label": "רשימות המועמדים לכנסת ה-26 (ועדת הבחירות המרכזית, gov.il)",
             "url": "https://www.gov.il/he/pages/candidates-lists-26", "orig": ""},
            {"label": "ועדת הבחירות המרכזית לכנסת ה-26 (gov.il)",
             "url": "https://www.gov.il/he/departments/units/elections-26/govil-landing-page", "orig": ""},
        ],
        # Lists that announced their withdrawal after submitting candidates (user decision: keep
        # them on the site, polls included, with a notice). poll list name -> date, source.
        withdrawn={
            "כחול לבן": dict(
                date="2026-10-19",
                src="https://www.timesofisrael.com/blue-and-whites-benny-gantz-pulls-out-of-race-sealing-precipitous-political-fall/",
                label="Times of Israel: גנץ מסיר את מועמדות כחול לבן"),
        },
        # poll list name -> (slug, he-wiki section, en article for the position, position note)
        lists=[
            ("הליכוד", "likud", "הליכוד", "Likud", ""),
            ("ביחד", "together", "ביחד", "Together (Israel)", ""),
            ("הציונות הדתית וזהות", "rzp", "הציונות הדתית וזהות", "Religious Zionist Party",
             "רשימה משותפת של הציונות הדתית וזהות; מוצג המיקום של הציונות הדתית, שבראש הרשימה (זהות: Right-wing to far-right)."),
            ("עוצמה יהודית", "otzma", "עוצמה יהודית", "Otzma Yehudit", ""),
            ("כחול לבן", "blue-white", "כחול לבן", "Blue and White (political party)", ""),
            ("ש\"ס", "shas", "מפלגת ש\"ס", "Shas", ""),
            ("יהדות התורה", "utj", "יהדות התורה", "United Torah Judaism", ""),
            ("ישראל ביתנו", "yb", "ישראל ביתנו", "Yisrael Beiteinu", ""),
            ("רע\"ם", "raam", "הרשימה הערבית המאוחדת", "Ra'am", ""),
            ("הרשימה המשותפת", "joint-list", "הרשימה המשותפת", "Joint List", ""),
            ("הדמוקרטים", "democrats", "הדמוקרטים", "The Democrats (Israel)", ""),
            ("ישר!", "yashar", "ישר!", "Yashar (political party)", ""),
            ("המילואימניקים-המפלגה הכלכלית", "reservists-nep", "המילואימניקים-המפלגה הכלכלית",
             "The Reservists (political party)",
             "רשימה משותפת של המילואימניקים והמפלגה הכלכלית החדשה; מוצג המיקום של המילואימניקים, שבראש הרשימה (המפלגה הכלכלית: גם Centre-right)."),
            ("עמך ישראל", "amcha-yisrael", "עמך ישראל", "Amcha Yisrael", ""),
            ("הציבור החרדי", "haredi-public", "הציבור החרדי", "Haredi Public", ""),
        ],
    ),
}
POSITION.update({
    "Together (Israel)": ("Centre to centre-right", "מרכז עד מרכז-ימין", 0, 1, ""),
    "The Democrats (Israel)": ("Centre-left to left-wing", "מרכז-שמאל עד שמאל", -2, -1, ""),
    "Yashar (political party)": ("Centre", "מרכז", 0, 0, ""),
    "The Reservists (political party)": ("Centre-right", "מרכז-ימין", 1, 1, ""),
    "Amcha Yisrael": ("Right-wing", "ימין", 2, 2, ""),
    "Haredi Public": ("", "לא מצוין בתיבת המידע", None, None, ""),
})

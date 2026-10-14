"""Per-election configuration: files, windows, publisher mapping, party lists."""
import re
from datetime import date


def has(*names):
    """Header predicate: True when any of the column names is present."""
    return lambda header: any(n in header for n in names)


def lacks(*names):
    return lambda header: not any(n in header for n in names)


# ----------------------------------------------------------------- outlets
# Each rule: (regex on the publisher text, outlet code, note or None).
# The first matching rule wins unless 'multi' lists several outlets.
def map_outlet(election, pub):
    """Return list of (outlet, note). Empty list = not a selected outlet."""
    p = pub.strip()
    if election in ("2026", "2022", "2021", "2020", "2019b"):
        table = [
            (r"^(HaHadashot 12|Channel 12)$", ["12"], None),
            (r"^Keshet$", ["12"], "published as 'Keshet' (counted as Channel 12 by user decision)"),
            (r"^Mako/Knesset Channel$", ["12"], "Mako (Keshet's website) with Knesset Channel - counted as Channel 12 by user decision"),
            (r"^Mako$", ["12"], "Mako (Keshet's website) - counted as Channel 12 by user decision"),
            (r"^Channel 13$", ["13"], None),
            (r"^Kan 11$", ["11"], None),
            (r"^Kan Radio$", ["11"], "Kan radio - counted as Kan 11 by user decision"),
            (r"^Reshet Bet$", ["11"], "Reshet Bet (Kan radio) - counted as Kan 11 by user decision"),
            (r"^Maariv$", ["MAARIV"], None),
            (r"^(The Jerusalem Post/Maariv|Maariv & The Jerusalem Post)$", ["MAARIV"], "joint Maariv/Jerusalem Post publication"),
            (r"^(103fm/Maariv|103fm & Maariv)$", ["MAARIV"], "joint 103FM/Maariv publication"),
            (r"^Haaretz$", ["HAARETZ"], None),
        ]
    elif election == "2019a":
        table = [
            (r"/Channel 12$", ["12"], None),
            (r"/Channel 13$", ["13"], None),
            (r"^Channel 13$", ["13"], None),
            (r"/Kan$", ["11"], None),
            (r"/Reshet Bet$", ["11"], "Reshet Bet (Kan radio) - counted as Kan 11 by user decision"),
            (r"/Maariv$", ["MAARIV"], None),
            (r"Radio 103FM & Maariv$", ["MAARIV"], "joint 103FM/Maariv publication"),
            (r"/Haaretz$", ["HAARETZ"], None),
        ]
    elif election == "2015":
        table = [
            (r"Galay Israel Radio", [], None),            # Galei Israel: private radio
            (r"Makor Rishon", [], None),
            (r"Nana 10", ["13"], "Nana 10 (Channel 10's website) - counted as Channel 10 by user decision; Channel 10 = predecessor of 13"),
            (r"Channel 2", ["12"], "Channel 2 (predecessor of 12)"),
            (r"Channel 10", ["13"], "Channel 10 (predecessor of 13)"),
            (r"Channel 1(?!\d)", ["11"], "Channel 1 / IBA (predecessor of Kan 11)"),
            (r"Reshet Bet|Israel Radio", ["11"], "IBA radio (Reshet Bet / Kol Israel) - counted as Kan 11 predecessor by user decision"),
            (r"Jerusalem Post", ["MAARIV"], "joint Maariv/Jerusalem Post publication"),
            (r"Walla-Maariv", ["MAARIV"], "joint Walla/Maariv publication"),
            (r"Maariv", ["MAARIV"], None),
            (r"Haaretz", ["HAARETZ"], None),
        ]
    elif election == "2013":
        table = [
            (r"Mako & Channel ?2", ["12"], "Channel 2 with Mako (predecessor of 12)"),
            (r"Mako|MAKO", ["12"], "Mako (Keshet's website) - counted as Channel 2 by user decision; Channel 2 = predecessor of 12"),
            (r"Channel ?2(?!\d)", ["12"], "Channel 2 (predecessor of 12)"),
            (r"Channel ?10", ["13"], "Channel 10 (predecessor of 13)"),
            (r"Channel ?1(?!\d)", ["11"], "Channel 1 / IBA (predecessor of Kan 11)"),
            (r"Reshet Bet|Israel Radio", ["11"], "IBA radio (Reshet Bet / Kol Israel) - counted as Kan 11 predecessor by user decision"),
            (r"Maariv", ["MAARIV"], None),
            (r"Haaretz", ["HAARETZ"], None),
        ]
    elif election == "2009":
        table = [
            (r"^Haaretz/Channel 10$", ["HAARETZ", "13"], "joint Haaretz/Channel 10 poll - counted for both by user decision; Channel 10 = predecessor of 13"),
            (r"^Channel 1('s Friday Diary)?$", ["11"], "Channel 1 / IBA (predecessor of Kan 11)"),
            (r"^Channel 2('s \"Mishal Cham\")?$", ["12"], "Channel 2 (predecessor of 12)"),
            (r"^Channel 10$", ["13"], "Channel 10 (predecessor of 13)"),
            (r"^Israel Radio's", ["11"], "IBA radio (Kol Israel) - counted as Kan 11 predecessor by user decision"),
            (r"^Haaretz$", ["HAARETZ"], None),
            (r"^Maariv$", ["MAARIV"], None),
        ]
    else:
        raise KeyError(election)
    for rx, outs, note in table:
        if re.search(rx, p):
            extra = ""
            if election == "2009" and "Friday Diary" in p:
                extra = " (programme 'Friday Diary')"
            if election == "2009" and "Mishal Cham" in p:
                extra = " (programme 'Mishal Cham')"
            return [(o, (note or "") + extra) for o in outs]
    return []


# ----------------------------------------------------------------- elections
ELECTIONS = {
    "2009": dict(
        label="פברואר 2009 (הכנסת ה-18)", date=date(2009, 2, 10), start=date(2008, 11, 10),
        files=["raw_2009.txt"], fmt="C",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_2009_Israeli_legislative_election",
        parties=[
            dict(name="קדימה", cols=["Kadima"]),
            dict(name="הליכוד", cols=["Likud"]),
            dict(name="העבודה", cols=["Labor"]),
            dict(name="ישראל ביתנו", cols=["Yisrael Beiteinu"]),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="מרצ", cols=["Meretz"]),
        ]),
    "2013": dict(
        label="ינואר 2013 (הכנסת ה-19)", date=date(2013, 1, 22), start=date(2012, 10, 22),
        files=["raw_2013.txt"], fmt="B",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_2013_Israeli_legislative_election",
        parties=[
            dict(name="הליכוד ביתנו", cols=["Likud", "YisraelBeiteinu"]),
            dict(name="העבודה", cols=["Labor"]),
            dict(name="הבית היהודי", cols=["JewishHome", "NationalUnion"]),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="יש עתיד", cols=["YeshAtid"]),
            dict(name="התנועה", cols=["Hatnuah"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="מרצ", cols=["Meretz"]),
        ]),
    "2015": dict(
        label="מרץ 2015 (הכנסת ה-20)", date=date(2015, 3, 17), start=date(2014, 12, 17),
        files=["raw_2015.txt"], fmt="B",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_2015_Israeli_legislative_election",
        parties=[
            dict(name="הליכוד", cols=["Likud"]),
            dict(name="המחנה הציוני", cols=["Labor", "Hatnuah"]),
            dict(name="הרשימה המשותפת", cols=["Hadash", "UAL-Ta'al", "Balad"]),
            dict(name="יש עתיד", cols=["YeshAtid"]),
            dict(name="הבית היהודי", cols=["JewishHome"]),
            dict(name="כולנו", cols=["Kulanu"]),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="ישראל ביתנו", cols=["YisraelBeiteinu"]),
        ]),
    "2019a": dict(
        label="אפריל 2019 (הכנסת ה-21)", date=date(2019, 4, 9), start=date(2019, 1, 9),
        files=["raw_2019a.txt"], fmt="B",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_April_2019_Israeli_legislative_election",
        parties=[
            dict(name="הליכוד", cols=["Likud"]),
            dict(name="כחול לבן", cols=["Blue &White", "YeshAtid", "Hosen-Telem"]),
            dict(name="העבודה", cols=["Labor"]),
            dict(name="חד\"ש-תע\"ל", cols=["Hadash–Ta'al"], presplit=has("JointList")),
            dict(name="הימין החדש", cols=["NewRight"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="איחוד מפלגות הימין", cols=["URWP", "JewishHome"]),
            dict(name="מרצ", cols=["Meretz"]),
            dict(name="כולנו", cols=["Kulanu"]),
            dict(name="ישראל ביתנו", cols=["YisraelBeiteinu"]),
            dict(name="זהות", cols=["Zehut"]),
        ]),
    "2019b": dict(
        label="ספטמבר 2019 (הכנסת ה-22)", date=date(2019, 9, 17), start=date(2019, 6, 17),
        files=["raw_2019b.txt"], fmt="A",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_September_2019_Israeli_legislative_election",
        parties=[
            dict(name="הליכוד", cols=["Likud", "Likud–Kulanu"],
                 col_notes={"Likud–Kulanu": "listed as Likud-Kulanu (Kulanu had already merged into Likud in May 2019)"}),
            dict(name="כחול לבן", cols=["Blue &White"]),
            dict(name="הרשימה המשותפת", cols=["JointList"]),
            dict(name="ימינה", cols=["Yamina", "URWP", "NewRight"]),
            dict(name="ישראל ביתנו", cols=["YisraelBeiteinu"]),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="העבודה-גשר", cols=["Labor-Gesher", "Labor", "Gesher"]),
            dict(name="המחנה הדמוקרטי", cols=["Dem.Union", "Meretz", "IDP"]),
        ]),
    "2020": dict(
        label="מרץ 2020 (הכנסת ה-23)", date=date(2020, 3, 2), start=date(2019, 12, 2),
        files=["raw_2020.txt"], fmt="A",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_2020_Israeli_legislative_election",
        parties=[
            dict(name="כחול לבן", cols=["Blue &White"]),
            dict(name="הליכוד", cols=["Likud"]),
            dict(name="הרשימה המשותפת", cols=["JointList"]),
            dict(name="העבודה-גשר-מרצ", cols=["Emet", "Labor-Gesher", "Dem.Union"]),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="ישראל ביתנו", cols=["YisraelBeiteinu"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="ימינה", cols=["Yamina", "NewRight", "NU", "JH–NU"]),
        ]),
    "2021": dict(
        label="מרץ 2021 (הכנסת ה-24)", date=date(2021, 3, 23), start=date(2020, 12, 23),
        files=["raw_2021.txt", "raw_2021_mako.txt"], fmt="A",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_2021_Israeli_legislative_election",
        parties=[
            dict(name="הליכוד", cols=["Likud"]),
            dict(name="יש עתיד", cols=["YeshAtid"], presplit=has("Yesh Atid-Telem")),
            dict(name="תקווה חדשה", cols=["NewHope"]),
            dict(name="ימינה", cols=["Yamina"], presplit=lacks("RZ", "ReligiousZionist")),
            dict(name="הרשימה המשותפת", cols=["JointList", "Ta'al"], presplit=lacks("Ra'am")),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="ישראל ביתנו", cols=["YisraelBeiteinu", "YB"]),
            dict(name="העבודה", cols=["Labor"]),
            dict(name="הציונות הדתית", cols=["ReligiousZionist", "RZ", "OtzmaYehudit-Noam"]),
            dict(name="כחול לבן", cols=["Blue &White", "B&W"]),
        ]),
    "2022": dict(
        label="נובמבר 2022 (הכנסת ה-25)", date=date(2022, 11, 1), start=date(2022, 8, 1),
        files=["raw_2022.txt", "raw_2022_mako.txt"], fmt="A",
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_2022_Israeli_legislative_election",
        parties=[
            dict(name="הליכוד", cols=["Likud"]),
            dict(name="יש עתיד", cols=["YeshAtid"]),
            dict(name="הציונות הדתית", cols=["RZP-OY", "ReligiousZionist", "OtzmaYehudit"],
                 col_notes={"ReligiousZionist": "Religious Zionist list incl. Otzma Yehudit, before Otzma's temporary separate run (15-26 Aug 2022)"}),
            dict(name="המחנה הממלכתי", cols=["NationalUnity", "NUP/B&W–NH"],
                 col_notes={"NUP/B&W–NH": "Blue and White-New Hope list, before Eisenkot joined and it was renamed National Unity (14 Aug 2022)"}),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="ישראל ביתנו", cols=["YisraelBeiteinu"]),
        ]),
    "2026": dict(
        label="אוקטובר 2026 (הכנסת ה-26)", date=date(2026, 10, 27), start=date(2026, 7, 27),
        files=["raw_2026.txt"], fmt="A", upcoming=True,
        source="https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Israeli_legislative_election",
        parties=[
            dict(name="הליכוד", cols=["Likud"]),
            dict(name="ביחד", cols=["Together"]),
            dict(name="הציונות הדתית וזהות", cols=["RZP", "Zehut"],
                 col_notes={"RZP": "Religious Zionist Party alone: Zehut was not a separate column in this table (before the 1 Sep 2026 union)"}),
            dict(name="עוצמה יהודית", cols=["Otzma"]),
            dict(name="כחול לבן", cols=["Blue & White"]),
            dict(name="ש\"ס", cols=["Shas"]),
            dict(name="יהדות התורה", cols=["UTJ"]),
            dict(name="ישראל ביתנו", cols=["Yisrael Beiteinu"]),
            dict(name="רע\"ם", cols=["Ra'am"]),
            dict(name="הרשימה המשותפת", cols=["Joint List", "Hadash–Ta'al", "Balad"]),
            dict(name="הדמוקרטים", cols=["Dems"]),
            dict(name="ישר!", cols=["Yashar"]),
            dict(name="המילואימניקים-המפלגה הכלכלית", cols=["Reserv.", "NEP", "Zionist Home"],
                 col_notes={"Zionist Home": "Zionist Home (Hendel and Tropper, until 6 Sep 2026) counted as the Reservists by user decision"}),
            dict(name="עמך ישראל", cols=["Amcha Yisrael", "Winter party"],
                 col_notes={"Winter party": "listed as 'Winter party' before the name Amcha Yisrael (25 Aug 2026)"}),
            dict(name="הציבור החרדי", cols=["Haredi Public"]),
        ]),
}

# Polls that print several scenario rows for the same publication.
# Key: (election, end date ISO, outlet) -> index (0-based, in file order) of the
# row to keep, plus the reason. Decision rule from the user: keep the scenario
# with the union that actually happened.
SCENARIO_CHOICE = {
    ("2026", "2026-07-27", "12"): (1, "2 scenario rows; kept the one with Hadash-Ta'al and Balad joint (the Joint List re-formed on 19 Aug 2026)"),
    ("2026", "2026-08-09", "11"): (1, "2 scenario rows; kept the one with Ofer Winter's party (it ran, as Amcha Yisrael)"),
    ("2026", "2026-08-17", "12"): (1, "2 scenario rows; kept the one with Ofer Winter's party (it ran, as Amcha Yisrael)"),
    ("2026", "2026-08-24", "12"): (1, "2 scenario rows; kept the one with Ofer Winter's party (it ran, as Amcha Yisrael)"),
    ("2026", "2026-08-30", "11"): (1, "2 scenario rows; kept the one with the Religious Zionist Party and Zehut joint (the union of 1 Sep 2026); most lists were not reported in it"),
    ("2020", "2020-01-13", "12"): (1, "3 scenario rows; kept the one with New Right + National Union + United Jewish Home joint (the Yamina union that formed on 14-15 Jan 2020; it still included Otzma, which ran alone)"),
    ("2020", "2020-01-02", "12"): (0, "2 scenario rows; neither shows a union that happened (the other joins National Union with United Jewish Home) - kept the base row"),
    ("2020", "2020-01-02", "13"): (1, "2 scenario rows; kept the one with Labor-Gesher + Democratic Union joint (the merger that formed on 13 Jan 2020)"),
}

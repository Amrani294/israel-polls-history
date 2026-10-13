"""Parse the verified Wikipedia extracts into one clean list of poll values.

Every value that ends up in the workbook comes from here, with a note that
says how it was derived (direct value, sum of components before a merger,
range midpoint, scenario choice, predecessor channel, joint publisher ...).
"""
import re
from datetime import date

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

OUTLETS = ["11", "12", "13", "MAARIV", "HAARETZ"]


# ---------------------------------------------------------------- dates
def parse_end_date(text, default_year):
    """Return the last day of a fieldwork range such as '29 Sep–1 Oct 22',
    '26-27 Oct 22', '17 Sep', 'Feb 6, 2009', '8–9 Dec 20'."""
    t = text.replace("–", "-").strip()
    m = re.fullmatch(r"([A-Za-z]{3})\w* (\d+), (\d{4})", t)          # Feb 6, 2009
    if m:
        return date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
    last = t.split("-")[-1].strip()                                   # after range dash
    m = re.fullmatch(r"(\d+) ([A-Za-z]{3})\w*(?: (\d{2,4}))?", last)
    if m:
        year = m.group(3)
        if year is None:
            # the month may sit only on the end part; year from default
            y = default_year
        else:
            y = int(year)
            if y < 100:
                y += 2000
        return date(y, MONTHS[m.group(2)], int(m.group(1)))
    m = re.fullmatch(r"(\d+)", last)                                  # '2-3 Apr' -> handled above
    raise ValueError("cannot parse date: %r" % text)


# ---------------------------------------------------------------- values
def parse_value(raw):
    """Return (seats, note) for one cell; seats is None when not reported."""
    v = raw.strip()
    if v in ("", "–", "—", "-", "~", "N/a", "—N/a", "–N/a"):
        return None, None
    m = re.fullmatch(r"(\d+)(\(\d+(\.\d+)?%\))?", v)                  # 4 or 4(3.9%)
    if m:
        return int(m.group(1)), None
    if re.fullmatch(r"\(\d+(\.\d+)?%+\)", v):                         # (2.8%) below threshold
        return 0, "below threshold %s = 0 seats" % v
    m = re.fullmatch(r"(\d+)-(\d+)", v)                               # 9-10 range
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return (a + b) / 2, "range %s -> midpoint" % v
    raise ValueError("cannot parse value: %r" % raw)


# ---------------------------------------------------------------- files
def read_extract(path):
    """Yield tables: (header list, list of row-lists). Rows keep raw cells."""
    tables = []
    current = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("H"):
            current = {"header": line.split("|")[1:], "rows": [], "events": []}
            tables.append(current)
        elif line.startswith("R"):
            current["rows"].append(line.split("|")[1:])
        elif line.startswith("E"):
            current["events"].append(line.split("|")[1:])
    return tables


def cells_of(row, header, first_party):
    """Turn a raw row into a list of (columns spanned, raw value)."""
    cells = []
    i = first_party
    while i < len(header):
        raw = row[i] if i < len(row) else ""
        span = 1
        m = re.search(r"\^c(\d+)$", raw)
        if m:
            span = int(m.group(1))
            raw = raw[:m.start()]
        cols = tuple(header[i:i + span])
        cells.append((cols, raw))
        i += span
    return cells


def party_value(cells, header, party):
    """Compute one party's seats from a row.

    party = dict(name, cols=[component column names], presplit=callable(header)->bool)
    Returns (value or None, note).
    """
    comps = set(party["cols"])
    if party.get("presplit") and party["presplit"](header):
        return None, "pre-split entity (different list) - not counted"
    hit = [(cols, raw) for cols, raw in cells if comps & set(cols)]
    if not hit:
        return None, None
    for cols, raw in hit:
        outside = set(cols) - comps
        if outside:
            return None, "joint cell with %s - not counted" % "+".join(sorted(outside))
    notes = []
    vals = []
    missing = []
    for cols, raw in hit:
        val, note = parse_value(raw)
        if note:
            notes.append(note)
        if val is None:
            missing.extend(cols)
        else:
            vals.append(val)
    if not vals:
        return None, None
    if len(hit) > 1:
        notes.append("pre-merger sum of " + " + ".join(
            "%s=%s" % ("+".join(cols), raw) for cols, raw in hit))
    elif len(hit[0][0]) == 1 and hit[0][0][0] in party.get("col_notes", {}):
        notes.append(party["col_notes"][hit[0][0][0]])
    if missing:
        notes.append("not reported: " + ", ".join(missing))
    return sum(vals), "; ".join(notes)

"""Turn the browser extract of the 2026 Wikipedia poll tables (data/wiki26_tables_raw.txt,
djb2 hash 242455336, checked in the browser; Wikipedia revision 1381577859, read 24 Oct 2026)
into the regular extract format (data/raw_2026.txt).

Extract format (one line per table row, cells separated by '|'):
  H<t>1 / H<t>2   the two header rows of table t ('^cN' = spans N columns, '^rN' = spans N rows)
  X<t>            a third header row (sub-headings of a spanning heading, e.g. the Joint List's
                  Hadash-Ta'al | Balad)
  R<t>            a poll row; a row whose first cells had '^rN' is followed by N-1 rows that
                  start directly with the party cells (scenario rows of the same poll)
  E<t>            an event row (copied as is)

Output, as in the other extracts:
- the columns are Date | Polling firm | Publisher | one column per list;
- 'Sample size', 'Others' and 'Gov.' are dropped ('Gov.' is a sum Wikipedia adds; 'Others'
  was never part of the 2026 extract, and every value in it is below the threshold or N/A);
- a cell spanning N columns is followed by N-1 '~' placeholders;
- the scenario rows of a poll repeat its date, firm and publisher.

Also writes data/poll_refs_2026.txt (citations, same format as poll_refs_raw.txt).
"""
import os
import re

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
TABLES_HASH = 242455336
REFS_HASH = 931941298
# Two-column headings, written out from the table as shown on Wikipedia.
SPLIT = {"RZP-Zehut": ["RZP", "Zehut"], "Reserv.-NEP": ["Reserv.", "NEP"]}
DROP = {"Samplesize", "Others", "Gov."}
# Citations corrected by hand (the reason is kept here and shown nowhere else):
# key = line in wiki26_refs_raw.txt, value = the citation used instead.
REF_FIX = {
    # In revision 1381105359 this row cites the Channel 13 article of 19 Aug (survey-905319423).
    # The earlier extract (revision of 14 Oct 2026) cited the 5 Aug article; kept that.
    "2026|5 Aug|MP+TM+SN+A|Channel 13|13tv.co.il/item/news/politics/politics/survey-905319423/?pid=106628":
    "2026|5 Aug|MP+TM+SN+A|Channel 13|13tv.co.il/item/news/politics/politics/r8iw1-905298096/?pid=106628/",
}


# Rows corrected by hand: key = line in wiki26_tables_raw.txt, value = the line used instead.
# (Empty since revision 1381577859: the Zman Yisrael row of 23-24 Sep has its colspan back.)
ROW_FIX = {}


def djb2(s):
    h = 5381
    for ch in s:
        h = (h * 33 + ord(ch)) % 1000000007
    return h


def span(cell, mark):
    m = re.search(r"\^%s(\d+)" % mark, cell)
    return int(m.group(1)) if m else 1


def bare(cell):
    return re.sub(r"\^[cr]\d+", "", cell)


def expand(cells):
    """Cells -> one value per column ('~' for the columns a spanning cell covers)."""
    out = []
    for c in cells:
        n = span(c, "c")
        out.append(re.sub(r"\^r\d+", "", c))   # '^cN' stays on the value, as in the other extracts
        out.extend(["~"] * (n - 1))
    return out


def header(h1, xrow):
    cols = []
    sub = list(xrow or [])
    for c in h1:
        name, n = bare(c), span(c, "c")
        if n == 1:
            cols.append(name)
        elif name in SPLIT:
            cols.extend(SPLIT[name])
        else:                                   # e.g. Joint List -> Hadash-Ta'al | Balad (X row)
            cols.extend(sub[:n])
            sub = sub[n:]
            if len(cols) and "" in cols:
                raise SystemExit("missing sub-heading for " + name)
    return cols


def main():
    src = open(os.path.join(DATA, "wiki26_tables_raw.txt"), encoding="utf-8").read()
    if djb2(src) != TABLES_HASH:
        raise SystemExit("wiki26_tables_raw.txt changed (hash %d)" % djb2(src))
    lines = src.split("\n")
    tables = {}                                 # t -> dict(h1, x, rows)
    order = []
    for line in lines:
        line = ROW_FIX.get(line, line)
        tag, _, rest = line.partition("|")
        if tag == "SOURCE":
            source = "SOURCE|" + rest.split("|")[0]
            continue
        t = tag[1]
        tb = tables.setdefault(t, dict(h1=None, x=None, rows=[]))
        if t not in order:
            order.append(t)
        f = rest.split("|")
        if tag[0] == "H" and tag.endswith("1"):
            tb["h1"] = f
        elif tag[0] == "X":
            tb["x"] = f
        elif tag[0] in "RE":
            tb["rows"].append((tag[0], f, line))
    out = [source]
    nrows = 0
    for t in order:
        tb = tables[t]
        cols = header(tb["h1"], tb["x"])
        keep = [i for i, c in enumerate(cols) if c not in DROP]
        hdr = [cols[i] for i in keep]
        hdr[0] = "Date"
        out.append("H%s|%s" % (t, "|".join(hdr)))
        lead, left = None, 0
        for kind, f, line in tb["rows"]:
            if kind == "E":
                out.append(line)
                continue
            if left:                            # scenario row: repeat date, firm, publisher, sample
                cells = lead + expand(f)
                left -= 1
            else:
                cells = expand(f)
                left = span(f[0], "r") - 1
                lead = cells[:4]
            if len(cells) != len(cols):
                raise SystemExit("row width %d != %d: %s" % (len(cells), len(cols), line))
            for i, c in enumerate(cells):
                if i not in keep and c == "~":
                    raise SystemExit("a spanning cell reaches a dropped column: " + line)
            out.append("R%s|%s" % (t, "|".join(cells[i] for i in keep)))
            nrows += 1
    open(os.path.join(DATA, "raw_2026.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

    refs = open(os.path.join(DATA, "wiki26_refs_raw.txt"), encoding="utf-8").read()
    if djb2(refs) != REFS_HASH:
        raise SystemExit("wiki26_refs_raw.txt changed (hash %d)" % djb2(refs))
    keep_refs = [REF_FIX.get(l, l) for l in refs.split("\n") if l]
    if len(keep_refs) != nrows:
        raise SystemExit("refs %d != rows %d" % (len(keep_refs), nrows))
    open(os.path.join(DATA, "poll_refs_2026.txt"), "w", encoding="utf-8").write("\n".join(keep_refs) + "\n")
    print("raw_2026.txt", nrows, "rows; refs", len(keep_refs))


if __name__ == "__main__":
    main()

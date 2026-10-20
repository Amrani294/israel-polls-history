"""Poll numbers read from the original publication (tools/data/primary_polls.txt).

The Wikipedia extracts give every poll's row. This layer records, for each poll of a
tracked outlet, what its own publication says (or, when it could not be reached, a
secondary report), and makes those numbers win over Wikipedia's (user decision,
20 Oct 2026). Every place where they differ is kept as a note.

File format: one record per line, fields separated by '|', '#' starts a comment.

  P|election|outlet|end|idx|kind|url|read|cells|note
      A poll that is in a Wikipedia extract. (election, outlet, end, idx) is the poll's key
      in build_data (idx = order of that outlet's rows with the same end date, 0-based).
  N|election|file|table|date text|firm|publisher|kind|url|read|cells|note
      A poll that is not (yet) in Wikipedia. It is added to the given extract file's table
      (0-based) as a new row; 'cells' must give every column the publication reports.

  kind   src   the outlet's own publication (article, broadcast graphic, official PDF)
         sec   another publication that reports the poll (Wikipedia's citation, a newspaper
               that reprinted it); used only when the outlet's own was not found
         none  nothing found besides Wikipedia; 'url' lists what was tried
  url    the publication (the page a reader should open)
  read   how the numbers were read: 'text' (the page text), 'img <url>' (a graphic on the
         page), 'infogram <url>' (the chart embedded in the page; its data table),
         'archive <url>' (a copy in the Internet Archive), 'pdf <url>'
  cells  the cells that differ from Wikipedia, in the extract's column names and cell syntax:
         Likud=22;RZP+Zehut=6;Blue & White=(0.9%). Empty = every number the publication
         shows is the same as in Wikipedia. Percentages below the threshold count as 0 seats;
         a different percentage is not a difference.
  note   a short note in Hebrew (optional), shown with the poll.
"""
import os
import re

from polls import parse_value

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
KINDS = ("src", "sec", "none")


def _cells(text, where):
    out = {}
    for part in [x for x in text.split(";") if x.strip()]:
        if "=" not in part:
            raise SystemExit("primary_polls.txt: bad cell %r (%s)" % (part, where))
        col, raw = part.split("=", 1)
        out[tuple(c.strip() for c in col.split("+"))] = raw.strip()
    return out


def load():
    checks, new = {}, []
    path = os.path.join(DATA, "primary_polls.txt")
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("|")
        where = "line %d" % n
        if f[0] == "P":
            if len(f) != 10:
                raise SystemExit("primary_polls.txt: %s has %d fields, expected 10" % (where, len(f)))
            _, e, outlet, end, idx, kind, url, read, cells, note = f
            if kind not in KINDS:
                raise SystemExit("primary_polls.txt: %s bad kind %r" % (where, kind))
            key = (e, outlet, end, int(idx))
            if key in checks:
                raise SystemExit("primary_polls.txt: %s duplicate %r" % (where, key))
            checks[key] = dict(kind=kind, url=url, read=read, cells=_cells(cells, where), note=note,
                               where=where, used=False)
        elif f[0] == "N":
            if len(f) != 12:
                raise SystemExit("primary_polls.txt: %s has %d fields, expected 12" % (where, len(f)))
            _, e, fname, table, dtext, firm, pub, kind, url, read, cells, note = f
            if kind != "src" and kind != "sec":
                raise SystemExit("primary_polls.txt: %s a new poll needs kind src or sec" % where)
            new.append(dict(election=e, file=fname, table=int(table), date_text=dtext, firm=firm,
                            publisher=pub, kind=kind, url=url, read=read,
                            cells=_cells(cells, where), note=note, where=where))
        else:
            raise SystemExit("primary_polls.txt: %s unknown record type %r" % (where, f[0]))
    return checks, new


def new_row(rec, header, first):
    """A row (raw cells, Wikipedia layout) for a poll that is only in the primary file."""
    row = [""] * len(header)
    row[0], row[1], row[2] = rec["date_text"], rec["firm"], rec["publisher"]
    for cols, raw in rec["cells"].items():
        if cols[0] not in header[first:]:
            raise SystemExit("primary_polls.txt: %s no column %s" % (rec["where"], cols[0]))
        i = header.index(cols[0], first)
        if tuple(header[i:i + len(cols)]) != cols:
            raise SystemExit("primary_polls.txt: %s columns %s are not adjacent" % (rec["where"], "+".join(cols)))
        row[i] = raw + ("^c%d" % len(cols) if len(cols) > 1 else "")
        for j in range(1, len(cols)):
            row[i + j] = "~"
    return row


def apply(rec, row, header, first, cells_of):
    """Return (new row, diffs) with the record's cells written over the Wikipedia row."""
    row = list(row)
    have = {cols: (i, raw) for cols, raw, i in _cells_at(row, header, first, cells_of)}
    diffs = []
    for cols, raw in rec["cells"].items():
        if cols not in have:
            raise SystemExit("primary_polls.txt: %s no cell %s in the Wikipedia row (cells: %s)" % (
                rec["where"], "+".join(cols), ", ".join("+".join(c) for c in have)))
        i, old = have[cols]
        span = re.search(r"\^c\d+$", row[i])
        row[i] = raw + (span.group(0) if span else "")
        a, b = parse_value(old)[0], parse_value(raw)[0]
        if a != b:
            diffs.append(("+".join(cols), old, raw))
    return row, diffs


def _cells_at(row, header, first, cells_of):
    """cells_of plus the row index of each cell."""
    out, i = [], first
    for cols, raw in cells_of(row, header, first):
        out.append((cols, raw, i))
        i += len(cols)
    return out

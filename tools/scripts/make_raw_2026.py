"""Turn the browser extract of the 2026 Wikipedia poll tables (data/wiki26_tables_raw.txt,
djb2 hash 960126135, checked in the browser) into the regular extract format (data/raw_2026.txt):

- the 'Sample size' column is dropped (the other extracts do not have it);
- a cell spanning N columns is followed by N-1 '~' placeholders (as in the other extracts);
- the repeated header row that the extract picked up as a data row is dropped;
- the newest table's header had two-column headings ('RZP- Zehut', 'Reserv.- NEP') that the
  extract mislabelled; they are written out from the table as shown on Wikipedia.

Also writes data/poll_refs_2026.txt (citations, same format as poll_refs_raw.txt).
"""
import os
import re

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
H0 = ["Fieldwork date", "Polling firm", "Publisher", "Sample size", "Likud", "Together", "RZP", "Zehut",
      "Otzma", "Blue & White", "Shas", "UTJ", "Yisrael Beiteinu", "Ra'am", "Joint List", "Dems", "Yashar",
      "Reserv.", "NEP", "Amcha Yisrael", "Haredi Public"]


def djb2(s):
    h = 5381
    for ch in s:
        h = (h * 33 + ord(ch)) % 1000000007
    return h


def main():
    src = open(os.path.join(DATA, "wiki26_tables_raw.txt"), encoding="utf-8").read()
    if djb2(src) != 960126135:
        raise SystemExit("wiki26_tables_raw.txt changed (hash %d)" % djb2(src))
    out = []
    for line in src.split("\n"):
        tag, _, rest = line.partition("|")
        f = rest.split("|")
        if tag == "SOURCE":
            out.append(line)
        elif tag.startswith("H"):
            hdr = H0 if tag == "H0" else f
            if tag == "H0" and len(f) != len(H0):
                raise SystemExit("H0 width changed")
            hdr = [h.replace("Fieldworkdate", "Date") for h in hdr]
            hdr[0] = "Date"
            out.append(tag + "|" + "|".join(hdr[:3] + hdr[4:]))
        elif tag.startswith("R"):
            if f[0] == "Fieldworkdate":
                continue
            cells = []
            for c in f[:3] + f[4:]:
                cells.append(c)
                m = re.search(r"\^c(\d+)$", c)
                if m:                                   # placeholders, as in the other extracts
                    cells.extend(["~"] * (int(m.group(1)) - 1))
            out.append(tag + "|" + "|".join(cells))
        elif tag.startswith("E"):
            out.append(line)
    open(os.path.join(DATA, "raw_2026.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    refs = open(os.path.join(DATA, "wiki26_refs_raw.txt"), encoding="utf-8").read()
    if djb2(refs) != 684729704:
        raise SystemExit("wiki26_refs_raw.txt changed")
    keep = [l for l in refs.split("\n") if l and "|Fieldworkdate|" not in l]
    open(os.path.join(DATA, "poll_refs_2026.txt"), "w", encoding="utf-8").write("\n".join(keep) + "\n")
    print("raw_2026.txt", sum(1 for l in out if l.startswith("R")), "rows; refs", len(keep))


if __name__ == "__main__":
    main()

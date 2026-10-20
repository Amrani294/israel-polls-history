"""Build the clean poll table (one row per poll x party) and print a summary."""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from polls import read_extract, cells_of, party_value, parse_end_date, OUTLETS  # noqa: E402
from config import ELECTIONS, map_outlet, SCENARIO_CHOICE  # noqa: E402
import primary  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def row_fields(fmt, row):
    """Return (date text, firm, publisher text, first party column index)."""
    if fmt == "A":
        return row[0], row[1], row[2], 3
    if fmt == "B":                       # 'firm/publisher' in one column
        return row[0], row[1], row[1], 2
    if fmt == "C":                       # date | media | pollster
        return row[0], row[2], row[1], 3
    raise ValueError(fmt)


def build():
    polls = []          # every selected poll (one entry per outlet it counts for)
    checks, new = primary.load()
    for key, cfg in ELECTIONS.items():
        seen = set()
        group_counter = defaultdict(int)
        for fname in cfg["files"]:
            for t_i, table in enumerate(read_extract(os.path.join(DATA, fname))):
                header = table["header"]
                rows = [(row, None) for row in table["rows"]]
                for rec in new:
                    if (rec["election"], rec["file"], rec["table"]) == (key, fname, t_i):
                        if cfg["fmt"] != "A":
                            raise SystemExit("primary_polls.txt: %s new polls only in format A" % rec["where"])
                        rec["used"] = True
                        rows.append((primary.new_row(rec, header, 3), rec))
                for row, newrec in rows:
                    dtext, firm, pub, first = row_fields(cfg["fmt"], row)
                    is_exit = "exit poll" in pub.lower() or "election result" in pub.lower()
                    if is_exit or pub.strip() in ("–", "Election Results", "Election results"):
                        continue
                    end = parse_end_date(dtext, cfg["date"].year)
                    if end >= cfg["date"]:
                        continue                         # exit polls / results rows
                    if not (cfg["start"] <= end < cfg["date"]):
                        continue
                    outlets = map_outlet(key, pub)
                    if not outlets:
                        continue
                    sig = (tuple(row), )
                    if sig in seen:                       # same row in two extracts
                        continue
                    seen.add(sig)
                    # the publication's own numbers (primary_polls.txt) win over Wikipedia's
                    idxs = []
                    for outlet, onote in outlets:
                        gkey = (key, end.isoformat(), outlet)
                        idxs.append(group_counter[gkey])
                        group_counter[gkey] += 1
                    check = None
                    if newrec:
                        check = dict(kind=newrec["kind"], url=newrec["url"], read=newrec["read"],
                                     note=newrec["note"], diffs=[], new=True)
                    else:
                        recs = [checks.get((key, outlet, end.isoformat(), i))
                                for (outlet, _), i in zip(outlets, idxs)]
                        recs = [r for r in recs if r]
                        if len(recs) > 1:
                            raise SystemExit("primary_polls.txt: two records for one row: %s, %s" % (
                                recs[0]["where"], recs[1]["where"]))
                        if recs:
                            rec = recs[0]
                            rec["used"] = True
                            row, diffs = primary.apply(rec, row, header, first, cells_of)
                            check = dict(kind=rec["kind"], url=rec["url"], read=rec["read"],
                                         note=rec["note"], diffs=diffs, new=False)
                    cells = cells_of(row, header, first)
                    for (outlet, onote), idx in zip(outlets, idxs):
                        values = {}
                        for party in cfg["parties"]:
                            val, note = party_value(cells, header, party)
                            values[party["name"]] = (val, note)
                        polls.append(dict(
                            election=key, date_text=dtext, end=end.isoformat(),
                            firm=firm, publisher=pub, outlet=outlet,
                            outlet_note=onote, values=values, header=header,
                            raw=row, group_index=idx, source=cfg["source"], check=check))
    stale = [r["where"] for r in list(checks.values()) + new if not r.get("used")]
    if stale:
        raise SystemExit("primary_polls.txt: records that match no poll: " + ", ".join(stale))
    # scenario choice: keep only the chosen row where a group has several rows
    groups = defaultdict(list)
    for p in polls:
        groups[(p["election"], p["end"], p["outlet"], p["firm"])].append(p)
    kept = []
    for gkey, items in groups.items():
        if len(items) == 1:
            kept.append(items[0])
            continue
        choice = SCENARIO_CHOICE.get(gkey[:3])
        if choice is None:
            raise SystemExit("unresolved duplicate poll group: %r" % (gkey,))
        idx, reason = choice
        for i, p in enumerate(items):
            p["scenario_note"] = reason
            if i == idx:
                kept.append(p)
    return kept


def summarize(polls):
    out = {}
    for key, cfg in ELECTIONS.items():
        ps = [p for p in polls if p["election"] == key]
        per = {}
        for party in cfg["parties"]:
            name = party["name"]
            by_outlet = {}
            for o in OUTLETS:
                vals = [p["values"][name][0] for p in ps
                        if p["outlet"] == o and p["values"][name][0] is not None]
                by_outlet[o] = (sum(vals) / len(vals), len(vals)) if vals else (None, 0)
            means = [v for v, n in by_outlet.values() if v is not None]
            per[name] = dict(by_outlet=by_outlet,
                             overall=sum(means) / len(means) if means else None)
        out[key] = per
    return out


if __name__ == "__main__":
    polls = build()
    summary = summarize(polls)
    for key, per in summary.items():
        print("==", key, ELECTIONS[key]["label"])
        counts = defaultdict(int)
        for p in polls:
            if p["election"] == key:
                counts[p["outlet"]] += 1
        print("   polls per outlet:", dict(counts))
        ranked = sorted(per.items(), key=lambda kv: -(kv[1]["overall"] or -1))
        for name, d in ranked:
            cells = "  ".join("%s=%s(%d)" % (o, "%.2f" % v if v is not None else "-", n)
                              for o, (v, n) in d["by_outlet"].items())
            print("   %-22s %6s   %s" % (name, "%.2f" % d["overall"] if d["overall"] else "-", cells))
    with open(os.path.join(DATA, "polls_clean.json"), "w", encoding="utf-8") as f:
        json.dump(polls, f, ensure_ascii=False, indent=1, default=str)


def poll_blocs(polls):
    """Per poll: seats per bloc (sum over every party column) and a note."""
    from blocs import BLOC_COLS, MIXED_CELLS
    from polls import cells_of, parse_value
    out = []
    for p in polls:
        key = p["election"]
        first = 2 if ELECTIONS[key]["fmt"] == "B" else 3
        cells = cells_of(p["raw"], p["header"], first)
        sums = {"C": 0, "O": 0, "N": 0, "X": 0}
        notes = []
        for cols, raw in cells:
            if all(c in ("Others",) for c in cols):
                continue
            val, note = parse_value(raw)
            if val is None:
                continue
            blocs = {BLOC_COLS[key][c] for c in cols}
            if len(blocs) > 1:
                b = MIXED_CELLS[(key, tuple(cols))]
                notes.append("תא משותף %s=%s שויך לפי הרוב" % ("+".join(cols), raw))
            else:
                b = blocs.pop()
            if note and note.startswith("range"):
                notes.append("טווח %s - אמצע הטווח" % raw)
            sums[b] += val
        total = sum(sums.values())
        out.append(dict(poll=p, sums=sums, total=total, notes=notes))
    return out

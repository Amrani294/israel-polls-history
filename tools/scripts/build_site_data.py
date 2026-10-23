"""Build the website data files (site/data/*.js) from the verified extracts.

Run:  python3 scripts/build_site_data.py <site dir>
Every figure comes from the same pipeline as the Excel workbook
(build_data / blocs) or from the hash-verified extracts in data/.
"""
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from build_data import build, summarize, poll_blocs  # noqa: E402
from blocs import FINAL, EXIT_FULL, KIND, GOV_SRC, RES_SRC, self_check  # noqa: E402
from config import ELECTIONS  # noqa: E402
from polls import OUTLETS  # noqa: E402
import build_xlsx as X  # noqa: E402  (labels and note translations, shared with the workbook)
import sitecfg as S  # noqa: E402
from localize_assets import local_image_name  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
ORDER = ["2022", "2021", "2020", "2019b", "2019a", "2015", "2013", "2009"]


def die(msg):
    raise SystemExit("ERROR: " + msg)


# ------------------------------------------------------------------ MKs
def split_members(text):
    """Split a comma list of titles; titles may themselves contain ', ' inside parentheses."""
    out, buf = [], ""
    for tok in text.split(","):
        buf = tok if not buf else buf + "," + tok
        if buf.count("(") == buf.count(")"):
            if buf:
                out.append(buf.strip() if not buf.startswith(" ") else buf.strip())
            buf = ""
    if buf:
        die("unbalanced title list")
    return [x for x in out if x]


def read_mk():
    knesset, images, cur = {}, {}, None
    for line in open(os.path.join(DATA, "mk_raw.txt"), encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("K|"):
            cur = line.split("|")[1]
            knesset[cur] = OrderedDict()
        elif line.startswith("F|"):
            _, fac, mem = line.split("|", 2)
            fac = re.sub(r"\[[^\]]*\]$", "", fac)
            knesset[cur][fac] = split_members(mem)
        elif line.startswith("I|"):
            _, title, f = line.split("|", 2)
            images[title] = f
    for k, facs in knesset.items():
        n = sum(len(v) for v in facs.values())
        if n != 120:
            die("Knesset %s has %d members" % (k, n))
    return knesset, images


def read_img_meta():
    meta = {}
    for line in open(os.path.join(DATA, "img_meta_raw.txt"), encoding="utf-8"):
        line = line.rstrip("\n")
        _, title, rest = line.split("|", 2)
        f, rest = rest.split("|", 1)
        artist, lic, _repo = rest.rsplit("|", 2)
        meta[(title, f)] = (artist, lic)
        meta.setdefault(("*", f), (artist, lic))
    return meta


# ------------------------------------------------------------------ results tables
def num(s):
    return int(s.replace(",", "")) if s else None


def read_results():
    raw = open(os.path.join(DATA, "results_raw.txt"), encoding="utf-8").read()
    by_title = {}
    for block in raw.split("==")[1:]:
        title, body = block.split("\n", 1)
        by_title[title] = body
    out = {}
    for key, title in S.HE_ELECTION_ARTICLE.items():
        body = by_title[title]
        rows, info, links, above = [], {}, [], True
        for line in body.split("\n"):
            cells = line.split("|")
            if line.startswith("אחוז החסימה"):
                info["threshold"] = line.split(":", 1)[1].strip()
                above = False
                continue
            if len(cells) == 11 and cells[0] not in ("כינוי הרשימה", "כינוי"):
                name = re.sub(r"\{.*\}", "", cells[0]).strip()
                m = re.search(r"\{(.*)\}", cells[0])
                rows.append(dict(name=name, article=(m.group(1).split(";")[0] if m else ""),
                                 letters=cells[2], leader=cells[3], seats=int(cells[4]),
                                 votes=num(cells[7]), pct=cells[8], passed=above))
            elif cells[0] == 'סה"כ':
                info["seats_total"], info["valid"] = int(cells[1]), num(cells[2])
            elif cells[0] == "בעלי זכות הצבעה":
                info["eligible"] = num(cells[1])
                info["valid_share"] = cells[3]
            elif line.startswith("רשימות המועמדים") or line.startswith("תוצאות הבחירות") \
                    or line.startswith("הודעה בדבר") or line.startswith("פרטי חישוב"):
                m = re.search(r"<([^>]*)>", line)
                label = re.sub(r"\{.*?\}|<.*?>", "", line).strip()
                label = re.sub(r"\s*\(אורכב [^)]*\)", "", label)
                urls = m.group(1).split(";") if m else []
                if urls:
                    links.append(dict(label=label, url=urls[-1] if urls else "",
                                      orig=urls[0]))
        if sum(r["seats"] for r in rows) != 120 or info["seats_total"] != 120:
            die("seat total in results " + key)
        if sum(r["votes"] for r in rows) != info["valid"]:
            die("votes do not add up in results %s: %d vs %d" % (
                key, sum(r["votes"] for r in rows), info["valid"]))
        out[key] = dict(rows=rows, info=info, links=links)
    return out


# ------------------------------------------------------------------ positions
def read_positions():
    pos = {}
    for line in open(os.path.join(DATA, "en_positions_raw.txt"), encoding="utf-8"):
        line = line.rstrip("\n")
        parts = line.split("|")
        if "ERROR" in line:
            continue
        query, title = parts[1], parts[2]
        p = parts[3][len("pos="):]
        pos[query] = (title, p)
    # read in the browser in a separate call (en infobox of the 2021 party)
    pos["Blue and White (political party)"] = ("Blue and White (political party)", "Centre")
    # 2026: articles read on 14 Oct 2026 (only those not read before are added)
    for line in open(os.path.join(DATA, "en_positions_2026_check.txt"), encoding="utf-8"):
        parts = line.rstrip("\n").split("|")
        if len(parts) > 3 and parts[1] not in pos:
            pos[parts[1]] = (parts[2], re.sub(r"\[[^\]]*\]$", "", parts[3][len("pos="):]))
    return pos


# ------------------------------------------------------------------ 2026 sources
def read_candidates_2026():
    """section -> (letters, [(name, he-wiki title or '')]) from the he-wiki infoboxes."""
    out = {}
    for line in open(os.path.join(DATA, "he26_candidates_raw.txt"), encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("SOURCE|"):
            continue
        sec, letters, _box, cands = line.split("|", 3)
        people = []
        for c in cands.split(";") if cands else []:
            bits = c.split("~")
            if len(bits) > 2:
                die("struck-out candidate at top level in %s" % sec)
            people.append((bits[0], bits[1]))
        out[sec] = (letters, people)
    return out


def read_img_2026():
    images, meta = {}, {}
    for line in open(os.path.join(DATA, "img26_raw.txt"), encoding="utf-8"):
        p = line.rstrip("\n").split("|")
        if p[0] == "I":
            images[p[1]] = p[2]
            meta[(p[1], p[2])] = (p[3], p[4])
    return images, meta


def en_url(title):
    return "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")


def he_url(title):
    return "https://he.wikipedia.org/wiki/" + title.replace(" ", "_")


def thumb(file):
    """Commons redirect to a 330px thumbnail (falls back to the original when smaller)."""
    from urllib.parse import quote
    return "https://commons.wikimedia.org/wiki/Special:FilePath/%s?width=330" % quote(file.replace(" ", "_"))


def commons_page(file):
    from urllib.parse import quote
    return "https://commons.wikimedia.org/wiki/File:" + quote(file.replace(" ", "_"))


def r1(x):
    return None if x is None else round(x, 2)


# ------------------------------------------------------------------ main
def main(site):
    self_check()
    knesset, images = read_mk()
    meta = read_img_meta()
    im26, meta26 = read_img_2026()
    for t, f in im26.items():
        images.setdefault(t, f)
    meta.update(meta26)
    results = read_results()
    positions = read_positions()
    polls = build()
    import poll_refs
    matched = poll_refs.match(polls, {k: c["fmt"] for k, c in ELECTIONS.items()})
    unsourced = [p for p in polls if not p["ref"] and not (p["check"] and p["check"]["url"])]
    if unsourced:
        die("polls without a citation: %d (matched %d of %d)" % (len(unsourced), matched, len(polls)))
    summary = summarize(polls)
    pblocs = poll_blocs(polls)

    people = {}

    def person(title, plain=False):
        if plain:   # a candidate without a Hebrew Wikipedia article
            people.setdefault(title, dict(img="", file="", page="", artist="", license="", wiki=""))
            return title
        if title not in people:
            f = images.get(title)
            if f is None:
                # leaders not in the MK extract: look them up in the wider metadata
                cands = [k for k in meta if k[0] == title]
                f = cands[0][1] if cands else ""
            m = meta.get((title, f)) or meta.get(("*", f)) if f else None
            if f and not m:
                die("no credit for image of %s" % title)
            img = thumb(f) if f else ""
            if f:   # after tools/scripts/localize_assets.py the portrait is a local file
                local = os.path.join("assets", "img", "people", local_image_name(f))
                if os.path.exists(os.path.join(site, local)):
                    img = local.replace(os.sep, "/")
            people[title] = dict(img=img, file=f, page=commons_page(f) if f else "",
                                 artist=m[0] if m else "", license=m[1] if m else "",
                                 wiki=he_url(title))
        return title

    elections = []
    all_polls = []
    used_members = defaultdict(set)
    for key in ORDER:
        cfg = ELECTIONS[key]
        kn = S.KNESSET[key]
        res = results[key]
        facs = knesset[kn]
        rows_by_letters = {r["letters"]: r for r in res["rows"]}
        lists = []
        claimed = set()
        for name, seats, bloc, bnote in FINAL[key]:
            if name not in S.LISTS[key]:
                die("no site config for %s %s" % (key, name))
            slug, letters, rec, rnote, rules = S.LISTS[key][name]
            row = rows_by_letters.get(letters)
            if not row:
                die("letters %s not in results %s" % (letters, key))
            if row["seats"] != seats:
                die("seat mismatch %s %s: %d vs %d" % (key, name, row["seats"], seats))
            he_art, en_art = S.PARTY[slug]
            en_art = S.EN_OVERRIDE.get((key, slug), en_art)
            # members
            members = []
            for fac in rules:
                if fac not in facs:
                    die("faction %r missing in Knesset %s" % (fac, kn))
                claimed.add(fac)
                for mname in facs[fac]:
                    mv = S.MEMBER_MOVES.get((key, mname))
                    if mv and mv[1] != name:
                        continue
                    members.append(mname)
            for (k2, mname), (frm, to) in S.MEMBER_MOVES.items():
                if k2 == key and to == name and mname not in members:
                    members.append(mname)
            leader = S.LEADER_TITLE.get(row["leader"], row["leader"])
            if seats:
                if leader not in members:
                    die("leader %s not among members of %s %s" % (leader, key, name))
                members.remove(leader)
                members.insert(0, leader)
            if len(members) != seats:
                die("member count %s %s: %d vs %d seats" % (key, name, len(members), seats))
            for mname in members:
                if mname in used_members[key]:
                    die("member twice: %s %s" % (key, mname))
                used_members[key].add(mname)
                person(mname)
            person(leader)
            # position
            if en_art:
                ptitle, ptext = positions[en_art]
                exp = S.POSITION[en_art]
                if exp[0] != ptext:
                    die("position text changed for %s: %r vs %r" % (en_art, ptext, exp[0]))
                pos = dict(en=ptext, he=exp[1], lo=exp[2], hi=exp[3], note=exp[4],
                           article=ptitle, url=en_url(ptitle))
            else:
                pos = dict(en="", he=S.NO_EN[1], lo=None, hi=None, note="", article="", url="")
            if S.EN_NOTE.get(slug):
                pos["note"] = (pos["note"] + " " if pos["note"] else "") + S.EN_NOTE[slug]
            # polls and exit polls
            tracked = name in [p["name"] for p in cfg["parties"]]
            pavg = None
            if tracked:
                d = summary[key][name]
                pavg = dict(overall=r1(d["overall"]),
                            outlets={o: dict(mean=r1(v), n=n) for o, (v, n) in d["by_outlet"].items()})
            exits = {e["channel"]: e["seats"][name] for e in EXIT_FULL[key]}
            lists.append(OrderedDict(
                id=slug, name=name, ballot=row["name"], letters=letters, leader=leader,
                seats=seats, votes=row["votes"], pct=row["pct"], passed=row["passed"],
                bloc=bloc, blocNote=bnote,
                rec=rec, recNote=rnote,
                members=members,
                memberNotes={m: S.MOVE_NOTE[(key, m)] for m in members if (key, m) in S.MOVE_NOTE},
                heWiki=he_url(he_art), position=pos,
                polls=pavg, exits=exits,
                exitAvg=r1(sum(exits.values()) / len(exits)),
            ))
        unclaimed = [f for f in facs if f not in claimed]
        if unclaimed:
            die("unclaimed factions in %s: %r" % (key, unclaimed))
        if sum(len(l["members"]) for l in lists) != 120:
            die("members total %s" % key)
        # small lists (below threshold and not in FINAL)
        final_letters = {S.LISTS[key][n][1] for n, *_ in FINAL[key]}
        small = [dict(name=r["name"], letters=r["letters"], leader=r["leader"], votes=r["votes"],
                      pct=r["pct"]) for r in res["rows"] if r["letters"] not in final_letters]
        # bloc summaries (same rule as the workbook)
        order = ["C", "O", "N", "X"] if KIND[key] == "rec" else ["C", "O", "X"]
        items = [x for x in pblocs if x["poll"]["election"] == key and x["total"] == 120]
        blocs_polls = {}
        per_outlet = {}
        for o in OUTLETS:
            its = [x for x in items if x["poll"]["outlet"] == o]
            if its:
                per_outlet[o] = {b: sum(x["sums"][b] for x in its) / len(its) for b in order}
                per_outlet[o]["n"] = len(its)
        for b in order:
            vals = [v[b] for v in per_outlet.values()]
            blocs_polls[b] = r1(sum(vals) / len(vals))
        blocs_exit = {}
        bloc_of = {n: b for n, _, b, _ in FINAL[key]}
        for b in order:
            vals = [sum(s for p, s in e["seats"].items() if bloc_of[p] == b) for e in EXIT_FULL[key]]
            blocs_exit[b] = r1(sum(vals) / len(vals))
        blocs_final = {b: sum(s for n, s, bb, _ in FINAL[key] if bb == b) for b in order}
        gov = S.GOVERNMENT[key]
        elections.append(OrderedDict(
            key=key, label=cfg["label"], date=cfg["date"].isoformat(), knesset=kn,
            windowStart=cfg["start"].isoformat(),
            kind=KIND[key], blocOrder=order,
            blocLabels={b: X.labels(key)[b] for b in order},
            government=dict(name=gov[0], date=gov[1], pm=gov[2]) if gov else None,
            info=res["info"], links=res["links"] + S.EXTRA_LINKS.get(key, []),
            heWiki=he_url(S.HE_ELECTION_ARTICLE[key]),
            resultsSrc=RES_SRC[key], govSrc=GOV_SRC[key], recSrc=S.REC_SRC[key],
            recNote=S.REC_NOTE.get(key, ""),
            pollSrc=cfg["source"], tracked=[p["name"] for p in cfg["parties"]],
            notes=X.election_notes(key),
            lists=lists, small=small,
            blocs=dict(polls=blocs_polls, pollsByOutlet={o: {k: r1(v) for k, v in d.items()}
                                                          for o, d in per_outlet.items()},
                       pollsUsed=len(items), exit=blocs_exit, final=blocs_final),
            exitPolls=[dict(channel=e["channel"], actual=e["actual"], version=e["version"],
                            time=e["time"], source=e["source"], note=e["note"], seats=e["seats"])
                       for e in EXIT_FULL[key]],
        ))
        # polls (one row per poll)
        all_polls.extend(poll_rows(key, polls, pblocs, KIND[key]))

    for key, up in S.UPCOMING.items():
        elections.insert(0, upcoming(key, up, polls, summary, pblocs, positions, person))
        all_polls[:0] = poll_rows(key, polls, pblocs, KIND[key])

    # credits for people actually shown
    for t, p in people.items():
        if p["file"] and not p["license"]:
            die("missing license for " + t)
    out = os.path.join(site, "data")
    os.makedirs(out, exist_ok=True)
    checks = OrderedDict()                      # per election: how the poll numbers were checked
    for p in all_polls:
        c = checks.setdefault(p["e"], OrderedDict(n=0, src=0, sec=0, none=0, wiki=0, diffs=0, added=0))
        c["n"] += 1
        k = p["check"]["k"] if p["check"] else "wiki"
        c[k] += 1
        if p["check"] and p["check"]["diffs"]:
            c["diffs"] += 1
        if p["check"] and p["check"]["added"]:
            c["added"] += 1
    meta_out = OrderedDict(
        pollChecks=checks,
        outlets=OrderedDict((o, X.OUTLET_LABEL[o]) for o in OUTLETS),
        predecessors=X.PRED, oldElections=sorted(X.OLD),
        candidates=S.CANDIDATES,
        built=__import__("datetime").date.today().isoformat(),
    )
    write_js(os.path.join(out, "elections.js"), "ELECTIONS", elections)
    write_js(os.path.join(out, "polls.js"), "POLLS", all_polls)
    write_js(os.path.join(out, "people.js"), "PEOPLE", people)
    write_js(os.path.join(out, "meta.js"), "META", meta_out)
    import axes
    axes.self_check()
    e26 = [e for e in elections if e["key"] == "2026"][0]
    write_js(os.path.join(out, "axes.js"), "AXES", axes.load([l["id"] for l in e26["lists"]]))
    print("elections", len(elections), "polls", len(all_polls), "people", len(people),
          "no photo", [t for t, p in people.items() if not p["file"]])


def poll_rows(key, polls, pblocs, kind):
    cfg = ELECTIONS[key]
    order = ["C", "O", "N", "X"] if kind == "rec" else (["C", "O"] if kind == "pre" else ["C", "O", "X"])
    ptotal = {id(x["poll"]): x for x in pblocs}
    out = []
    rows = sorted([p for p in polls if p["election"] == key], key=lambda p: (p["end"], p["outlet"]))
    for p in rows:
        onote = X.OUTLET_NOTE_HE[p["outlet_note"]] if p["outlet_note"] else ""
        if p.get("scenario_note"):
            onote = (onote + "; " if onote else "") + X.SCENARIO_HE[p["scenario_note"]]
        pb = ptotal[id(p)]
        vals, vnotes = {}, {}
        for party in [pp["name"] for pp in cfg["parties"]]:
            v, note = p["values"][party]
            vals[party] = v
            if note:
                vnotes[party] = X.value_note_he(note)
        out.append(OrderedDict(
            e=key, end=p["end"], dateText=p["date_text"], outlet=p["outlet"],
            publisher=p["publisher"], firm=p["firm"] if cfg["fmt"] != "B" else "",
            values=vals, valueNotes=vnotes, outletNote=onote,
            blocs={b: pb["sums"][b] for b in order}, total=pb["total"],
            blocNotes=pb["notes"], src=p["source"], ref=p["ref"], check=check_out(cfg, p["check"])))
    return out


def check_out(cfg, c):
    """What the site shows about the publication check (primary_polls.txt), or None."""
    if not c:
        return None
    from polls import parse_value
    diffs = []
    for cols, old, new in c["diffs"]:
        label = cols
        for party in cfg["parties"]:
            if set(cols.split("+")) & set(party["cols"]):
                label = party["name"]
        diffs.append([label, parse_value(old)[0], parse_value(new)[0]])
    url = c["url"] if re.match(r"https?://", c["url"] or "") else ""
    return OrderedDict(k=c["kind"], url=url, note=c["note"], diffs=diffs, added=c["new"])


def upcoming(key, up, polls, summary, pblocs, positions, person):
    """An election that has not happened yet: lists, candidates and polls, no results."""
    from blocs import BLOC_COLS, labels
    cfg = ELECTIONS[key]
    cands = read_candidates_2026()
    tracked = [p["name"] for p in cfg["parties"]]
    if [x[0] for x in up["lists"]] != tracked:
        die("2026: site lists differ from the tracked poll lists")
    for name in up.get("withdrawn", {}):
        if name not in tracked:
            die("2026: withdrawn list %s is not a tracked list" % name)
    bloc_of_col = BLOC_COLS[key]
    lists, used_sections = [], set()
    for name, slug, sec, en_art, pnote in up["lists"]:
        if sec not in cands:
            die("2026: no he-wiki section %s" % sec)
        used_sections.add(sec)
        letters, people_ = cands[sec]
        if not people_:
            die("2026: no candidates for %s" % sec)
        names = []
        for nm, title in people_:
            names.append(person(title) if title else person(nm, plain=True))
        party_cols = [pp for pp in cfg["parties"] if pp["name"] == name][0]["cols"]
        blocs_ = {bloc_of_col[c] for c in party_cols}
        if len(blocs_) != 1:
            die("2026: list %s spans blocs" % name)
        ptitle, ptext = positions[en_art]
        exp = S.POSITION[en_art]
        if exp[0] != ptext:
            die("position text changed for %s: %r vs %r" % (en_art, ptext, exp[0]))
        pos = dict(en=ptext, he=exp[1], lo=exp[2], hi=exp[3], note=" ".join(x for x in (exp[4], pnote) if x),
                   article=ptitle, url=en_url(ptitle))
        d = summary[key][name]
        lists.append(OrderedDict(
            id=slug, name=name, ballot=sec, letters=letters, leader=names[0],
            seats=None, votes=None, pct=None, passed=None,
            bloc=blocs_.pop(), blocNote="",
            rec=None, recNote="",
            members=[], memberNotes={}, candidates=names,
            heWiki=he_url(up["he_article"]) + "#" + sec.replace(" ", "_"), position=pos,
            polls=dict(overall=r1(d["overall"]),
                       outlets={o: dict(mean=r1(v), n=n) for o, (v, n) in d["by_outlet"].items()}),
            exits={}, exitAvg=None,
            withdrawn=up.get("withdrawn", {}).get(name),
        ))
    lists.sort(key=lambda l: -(l["polls"]["overall"] or 0))
    small = [dict(name=sec, letters=letters, leader=(ppl[0][0] if ppl else ""), votes=None, pct=None)
             for sec, (letters, ppl) in cands.items() if sec not in used_sections and letters]
    order = ["C", "O"]
    items = [x for x in pblocs if x["poll"]["election"] == key and x["total"] == 120]
    per_outlet = {}
    for o in OUTLETS:
        its = [x for x in items if x["poll"]["outlet"] == o]
        if its:
            per_outlet[o] = {b: sum(x["sums"][b] for x in its) / len(its) for b in order}
            per_outlet[o]["n"] = len(its)
    blocs_polls = {b: r1(sum(v[b] for v in per_outlet.values()) / len(per_outlet)) for b in order}
    last = max(p["end"] for p in polls if p["election"] == key)
    return OrderedDict(
        key=key, label=cfg["label"], date=cfg["date"].isoformat(), knesset=up["knesset"],
        windowStart=cfg["start"].isoformat(), upcoming=True, asOf=up["as_of"], lastPoll=last,
        kind="pre", blocOrder=order, blocLabels={b: labels(key)[b] for b in order},
        government=None, outgoing=dict(name=up["outgoing"][0], src=up["outgoing"][1]),
        info={}, links=up["links"],
        heWiki=he_url(up["he_article"]), enWiki=en_url(up["en_article"]),
        resultsSrc="", govSrc="", recSrc="", recNote="",
        pollSrc=cfg["source"], tracked=tracked,
        notes=X.election_notes(key),
        lists=lists, small=small,
        blocs=dict(polls=blocs_polls, pollsByOutlet={o: {k: r1(v) for k, v in d.items()}
                                                     for o, d in per_outlet.items()},
                   pollsUsed=len(items), exit=None, final=None),
        exitPolls=[],
    )


def write_js(path, var, obj):
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* generated by scripts/build_site_data.py - do not edit by hand */\n")
        f.write("window.%s = " % var)
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "site")

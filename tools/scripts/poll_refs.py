"""Attach to each poll the citation Wikipedia gives for it (data/poll_refs_raw.txt)."""
import os, re
from urllib.parse import urlsplit
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

# domains that belong to the outlet / pollster / election committee (the original publication)
ORIGINAL = ["mako.co.il", "13news.co.il", "13tv.co.il", "10.tv", "kan.org.il", "iba.org.il", "maariv.co.il",
            "nrg.co.il", "103fm.maariv.co.il", "haaretz.co.il", "haaretz.com", "walla.co.il", "jpost.com",
            "nana10.co.il", "bhirot2009.co.il", "bechirot", "gov.il", "geocartography.com", "makospecial.co.il",
            "ynet.co.il", "ynetnews.com", "news1.co.il"]

def norm(s):
    return re.sub(r"\s+", " ", s.replace("–", "-").replace("—", "-")).strip().lower()

def load():
    refs = {}
    for line in open(os.path.join(DATA, "poll_refs_raw.txt"), encoding="utf-8"):
        k, d, c1, c2, u = line.rstrip("\n").split("|", 4)
        if not u:
            continue
        key = (k, norm(d), norm(c1), norm(c2))
        refs.setdefault(key, u)
    return refs

def classify(url):
    full = "https://" + url if not url.startswith("http") else url
    host = urlsplit(full).netloc.lower()
    archived = host == "web.archive.org"
    if archived:
        m = re.search(r"/web/\d+/(https?://)?([^/]+)", full)
        host = m.group(2).lower() if m else host
    host = host[4:] if host.startswith("www.") else host
    original = any(host == d or host.endswith("." + d) or d in host for d in ORIGINAL)
    return dict(url=full, host=host, original=original, archived=archived)

def match(polls, fmt_of):
    refs = load()
    hit = 0
    for p in polls:
        k = p["election"]; fmt = fmt_of[k]
        raw = p["raw"]
        if fmt == "A":
            key = (k, norm(raw[0]), norm(raw[1]), norm(raw[2]))
            cands = [key]
        elif fmt == "B":
            cands = [(k, norm(raw[0]), norm(raw[1]), norm(raw[2]))]
        else:  # C: date | media | pollster
            cands = [(k, norm(raw[0]), norm(raw[1]), norm(raw[2]))]
        # 2013/2015/2019a tables give the year only in separator rows: also try without it
        cands += [(c[0], re.sub(r" (19|20)\d\d$", "", c[1])) + c[2:] for c in cands]
        u = next((refs[c] for c in cands if c in refs), None)
        p["ref"] = classify(u) if u else None
        hit += bool(u)
    return hit

"""Fill one day's Instagram slots (08:00-22:00 every two hours, Asia/Jerusalem).

usage: python3 refill.py SITE_DIR FONT_DIR YYYY-MM-DD

Run from the instagram-media worktree. Slots already in schedule.json are left alone,
so running it twice for the same day does nothing. Items never repeat. Renders the
new items into media/, commits and pushes the branch, then prints one JSON line per
new slot: {"date", "id", "info"} where info is the Metricool createScheduledPost payload.
Prints nothing (and says so on stderr) when the day is already full or nothing is left.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gen  # noqa: E402

HOURS = ["08", "10", "12", "14", "16", "18", "20", "22"]
REPO = "Amrani294/israel-polls-history"


def main():
    site, fd, day = sys.argv[1:4]
    sp = os.path.join(ROOT, "schedule.json")
    sched = json.load(open(sp, encoding="utf-8"))
    used = {i for _, i in sched["slots"]}
    taken = {w for w, _ in sched["slots"]}
    free = [day + "T" + h + ":00" for h in HOURS if day + "T" + h + ":00" not in taken]
    D = gen.Data(site)
    items = gen.catalog(D)
    left = [k for k in items if k not in used]
    reels = [k for k in left if items[k][0] == "reel"]
    posts = [k for k in left if items[k][0] == "post"]
    # one reel in every three slots while reels last; newest elections first (catalog order)
    pick = []
    for n in range(len(free)):
        src = reels if (n % 3 == 0 and reels) else (posts or reels)
        if not src:
            break
        pick.append(src.pop(0))
    if not pick:
        print("nothing to schedule for %s (free slots: %d, items left: %d)" % (day, len(free), len(left)), file=sys.stderr)
        return
    gen.render(items, pick, fd, os.path.join(ROOT, "media"))
    for w, i in zip(free, pick):
        sched["slots"].append([w, i])
    sched["slots"].sort()
    json.dump(sched, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    git = lambda *a: subprocess.run(["git", "-C", ROOT] + list(a), check=True, capture_output=True, text=True).stdout.strip()
    git("add", "-A")
    git("-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-q", "-m",
        "Instagram media for %s\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" % day)
    git("push", "-q", "origin", "instagram-media")
    sha = git("rev-parse", "HEAD")
    for w, i in zip(free, pick):
        kind = items[i][0]
        res = items[i][1](fd)
        url = "https://cdn.jsdelivr.net/gh/%s@%s/media/%s.%s" % (REPO, sha, i, "mp4" if kind == "reel" else "jpg")
        ig = {"type": "REEL", "showReelOnFeed": True} if kind == "reel" else {"type": "POST"}
        info = {"autoPublish": True, "draft": False, "descendants": [], "firstCommentText": "", "hasNotReadNotes": False,
                "media": [url], "mediaAltText": [], "providers": [{"network": "instagram"}],
                "publicationDate": {"dateTime": w + ":00", "timezone": "Asia/Jerusalem"},
                "shortener": False, "smartLinkData": {"ids": []}, "text": res[1], "instagramData": ig}
        if kind == "reel":
            info["videoCoverMilliseconds"] = res[3]
        print(json.dumps({"date": w + ":00", "id": i, "info": json.dumps(info, ensure_ascii=False)}, ensure_ascii=False))
    print("left after this day: %d" % (len(left) - len(pick)), file=sys.stderr)


if __name__ == "__main__":
    main()

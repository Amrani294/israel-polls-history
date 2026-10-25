# instagram-media

Media for the Instagram page of the site (not part of the site; Netlify publishes only `main`).

- `generator/gen.py` builds the posts (1080×1080 JPEG) and reels (1080×1920 MP4) from `data/*.js` on `main`.
- `media/` holds the rendered files. Metricool fetches them through jsDelivr, pinned to a commit:
  `https://cdn.jsdelivr.net/gh/Amrani294/israel-polls-history@<commit>/media/<file>`
- `schedule.json` lists what was scheduled and when (Asia/Jerusalem).

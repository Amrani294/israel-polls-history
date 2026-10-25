"""Sound effects for the reels: no music, only effects synced to the animation.

Every sound is synthesized here (sine, noise, filters); nothing is sampled.
Only ONE whoosh per reel (Yonatan, 25.10.2026: too many whooshes): the riser into the
reveal, or into the end card when the reel has no reveal.
Timeline (gen.py reel timings, passed in as T):
  0.2 + 0.07i  a soft pop as each ballot slip appears (T["rows"] slips)
  1.0 .. grow  counter ticks, rising in pitch, as the bars count up to the poll average
  morph - 0.8  a short alert "ding" as the label changes to "ובקלפי..."
  morph - 1    a riser whoosh into the reveal
  morph        a thump as the bars jump to the result, then ticks while they move
  morph + 3    a pop for each difference chip
  focus        a low "spotlight" hit as the biggest miss is highlighted
  end          a thump and a two-note chime on the end card
A reel without a reveal (the 2026 average) gets the title, slips, counter and end card.
The reel id seeds small variations (pitch, timing jitter), so reels don't sound identical.
"""
import hashlib
import wave

import numpy as np
from scipy.signal import butter, lfilter

SR = 44100


def _rng(seed_text):
    return np.random.default_rng(int(hashlib.sha256(seed_text.encode()).hexdigest()[:12], 16))


def _filt(x, kind, hz, order=2):
    w = np.clip(np.asarray(hz, dtype=float) / (SR / 2), 1e-4, 0.999)
    b, a = butter(order, w if w.ndim else float(w), kind)
    return lfilter(b, a, x)


def _whoosh(rng, dur, lo=300.0, hi=5000.0, up=True):
    """Noise whose band sweeps lo->hi (or back), with a smooth swell."""
    n = int(dur * SR)
    x = rng.standard_normal(n + 4000)
    out = np.zeros(n)
    blk = int(0.02 * SR)
    for s in range(0, n, blk):
        p = s / n if up else 1 - s / n
        c = lo * (hi / lo) ** p
        seg = _filt(x[s:s + blk + 4000], "band", [c * 0.6, min(c * 1.6, SR / 2 - 200)])
        out[s:s + blk] = seg[-min(blk, n - s):]
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return out * env * 2.0


def _pop(rng, f=700.0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    fr = f * (1 + 0.6 * np.exp(-t * 60))
    tone = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 45)
    click = _filt(rng.standard_normal(n), "high", 3000) * np.exp(-t * 400) * 0.3
    return tone + click


def _tick(f):
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 180)


def _thump(rng):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 45 + 80 * np.exp(-t * 25)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    air = _filt(rng.standard_normal(n), "low", 1200) * np.exp(-t * 20) * 0.25
    return body + air


def _chime(f1, f2, gap=0.14, dur=1.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, f in enumerate((f1, f2)):
        tt = np.maximum(t - k * gap, 0)
        on = (t >= k * gap).astype(float)
        out += on * (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2.01 * f * tt) + 0.12 * np.sin(2 * np.pi * 3.0 * f * tt)) * np.exp(-tt * 4.5)
    return out * 0.5


def _counter_ticks(start, end, n, f0, f1):
    """Tick times follow the same ease-in-out as the bars, so the ticks speed up then settle."""
    out = []
    for k in range(1, n + 1):
        p = k / (n + 1)
        # invert the cubic ease-in-out used in the page's draw()
        u = (p / 4) ** (1 / 3) if p < 0.5 else 1 - ((2 - 2 * p) ** (1 / 3)) / 2
        out.append((start + u * (end - start), f0 + (f1 - f0) * p))
    return out


def write_sfx(path, length, T, seed_text):
    rng = _rng(seed_text)
    n = int(length * SR)
    L = np.zeros(n)
    R = np.zeros(n)

    def put(x, at, g=1.0, pan=0.0):
        for buf, gg in ((L, g * (1 - max(pan, 0))), (R, g * (1 + min(pan, 0)))):
            i = int(at * SR)
            if i >= n:
                continue
            j = min(n, i + len(x))
            buf[max(i, 0):j] += gg * x[max(-i, 0):j - i]

    pitch = float(rng.choice([0.9, 1.0, 1.06, 1.12]))
    final = T["morph"] < length
    rows = int(T.get("rows", 9))

    for i in range(rows):
        put(_pop(rng, 620 * pitch * (1 + 0.04 * i)), 0.22 + 0.07 * i, 0.16, (i % 2 - 0.5) * 0.3)
    for tt, f in _counter_ticks(1.0, T["grow"], 22, 900 * pitch, 1700 * pitch):
        put(_tick(f), tt, 0.09)

    if final:
        put(_chime(988 * pitch, 1319 * pitch, 0.1, 0.9), T["morph"] - 0.8, 0.18)
        put(_whoosh(rng, 1.0, 200, 7000, True), T["morph"] - 1.0, 0.26)
        put(_thump(rng), T["morph"], 0.7)
        for tt, f in _counter_ticks(T["morph"], T["morph"] + 3, 16, 1500 * pitch, 800 * pitch):
            put(_tick(f), tt, 0.08)
        for i in range(rows):
            put(_pop(rng, 900 * pitch), T["morph"] + 3.05 + 0.04 * i, 0.10, (i % 2 - 0.5) * 0.4)
        put(_thump(rng), T["focus"], 0.45)

    if not final:                                  # the one whoosh of a reel without a reveal
        put(_whoosh(rng, 0.9, 300, 7000, True), T["end"] - 0.6, 0.24)
    put(_thump(rng), T["end"], 0.4)
    put(_chime(784 * pitch, 1175 * pitch, 0.16, 1.8), T["end"] + 0.15, 0.25)

    mix = np.stack([L, R], 1)
    fade = int(0.4 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix = np.tanh(mix * 1.2)
    mix *= 0.85 / max(1e-9, np.abs(mix).max())
    pcm = (mix * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

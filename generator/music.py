"""Original, synthesized "news / drama" score for the reels.

Nothing here is sampled or copied: every sound is generated from sine, saw and noise.
The score follows the reel's timeline (gen.py REEL timings): a ticking clock and a
pulsing bass while the bars grow, a riser into the reveal, an impact on the reveal,
a second hit when the biggest miss is highlighted, and a stinger on the end card.
A seed (the reel id) picks tempo, key, chord progression and bass pattern, so every
reel sounds different but the same reel always renders the same.

usage: write_score(path_wav, length_s, T, seed_text)
"""
import hashlib
import wave

import numpy as np
from scipy.signal import butter, lfilter

SR = 44100


def _rng(seed_text):
    return np.random.default_rng(int(hashlib.sha256(seed_text.encode()).hexdigest()[:12], 16))


def _lp(x, hz, order=2):
    b, a = butter(order, min(hz, SR / 2 - 100) / (SR / 2), "low")
    return lfilter(b, a, x)


def _hp(x, hz, order=2):
    b, a = butter(order, hz / (SR / 2), "high")
    return lfilter(b, a, x)


def _bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band")
    return lfilter(b, a, x)


def _saw(f, n, detune=0.0, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f * (1 + detune) + phase) % 1.0) - 1


def _env(n, a, d, sus=0.0):
    """Attack then exponential decay (seconds), floor at sus."""
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    dec = np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    return att * (sus + (1 - sus) * dec)


def _place(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    j = min(len(buf), i + len(x))
    buf[max(i, 0):j] += gain * x[max(-i, 0):j - i]


def _impact(rng, big=True):
    n = int((2.6 if big else 1.4) * SR)
    t = np.arange(n) / SR
    f = 38 + 90 * np.exp(-t * 14)                      # pitch drop
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (2.2 if big else 4))
    noise = _lp(rng.standard_normal(n), 2500) * np.exp(-t * 9)
    crack = _hp(rng.standard_normal(n), 3000) * np.exp(-t * 40) * 0.5
    return boom * 1.0 + noise * 0.35 + crack


def _riser(rng, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n)
    # sweep a band through rising centres, in blocks (cheap, sounds like a filter sweep)
    blk = int(0.05 * SR)
    for s in range(0, n, blk):
        c = 300 * (1 + 25 * (s / n) ** 2)
        seg = _bp(x[max(0, s - 2000):s + blk], c * 0.7, c * 1.4)
        out[s:s + blk] = seg[-min(blk, n - s):]
    tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (2.5 * t / dur)) / SR) * 0.25
    return (out * 3 + tone) * (t / dur) ** 2


def _reverse_swell(rng, dur):
    n = int(dur * SR)
    x = _hp(rng.standard_normal(n), 4000) * np.linspace(0, 1, n) ** 3
    return x * 0.6


def write_score(path, length, T, seed_text):
    rng = _rng(seed_text)
    n = int(length * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    bpm = rng.choice([84, 92, 100, 108, 116])
    beat = 60.0 / bpm
    root = rng.choice([55.0, 58.27, 61.74, 65.41, 69.30, 73.42])   # A1 .. D2
    minor = [0, 3, 7]
    progs = [[0, 8, 5, 7], [0, 5, 8, 7], [0, 10, 8, 7], [0, 8, 3, 10], [0, 1, 0, 7]]
    prog = progs[rng.integers(len(progs))]
    bass_pat = rng.choice([[1, 0, 1, 0, 1, 0, 1, 1], [1, 1, 0, 1, 1, 0, 1, 0], [1, 0, 0, 1, 1, 0, 1, 0]])
    final = T["morph"] < length
    reveal = T["morph"] if final else T["end"]

    # --- pad: minor chords, detuned saws, slow attack; brighter after the reveal
    bar = 4 * beat
    k = 0
    t0 = 0.0
    while t0 < length:
        semis = prog[k % len(prog)]
        tail = 0.8                                   # overlap the next chord: no gap at the bar line
        m = int(min(bar + tail, length - t0) * SR)
        chord = np.zeros(m)
        for iv in minor:
            f = root * 4 * 2 ** ((semis + iv) / 12)
            for d in (-0.004, 0.0, 0.005):
                chord += _saw(f, m, d, rng.random())
        cut = 900 if t0 < reveal else 1800
        chord = _lp(chord, cut) * _env(m, 0.35, 3.0, 0.6) * 0.05
        rel = min(m, int(tail * SR))
        chord[-rel:] *= np.linspace(1, 0, rel)
        _place(L, chord, t0)
        _place(R, chord * 0.9, t0)
        t0 += bar
        k += 1

    # --- bass pulse on eighths, from the start of the bars until the end card
    step = beat / 2
    i = 0
    t0 = 0.9
    while t0 < T["end"]:
        if bass_pat[i % 8]:
            semis = prog[int(t0 // bar) % len(prog)]
            f = root * 2 ** (semis / 12)
            m = int(0.28 * SR)
            x = (np.sin(2 * np.pi * f * np.arange(m) / SR) + 0.4 * _lp(_saw(f, m), 400)) * _env(m, 0.005, 0.12)
            g = 0.32 if t0 < reveal else 0.42
            _place(L, x, t0, g)
            _place(R, x, t0, g)
        t0 += step
        i += 1

    # --- the "news" clock: short filtered clicks on sixteenths, panned slightly
    t0 = 0.0
    i = 0
    while t0 < T["end"] - 0.2:
        m = int(0.012 * SR)
        clk = _hp(rng.standard_normal(m), 5000) * _env(m, 0.0005, 0.003)
        acc = 1.0 if i % 4 == 0 else 0.45
        _place(L, clk, t0, 0.10 * acc)
        _place(R, clk, t0, 0.06 * acc)
        t0 += beat / 4
        i += 1

    # --- timpani-like roll before the reveal
    for j in range(12):
        tt = reveal - 1.6 + j * 0.12
        m = int(0.3 * SR)
        tm = np.arange(m) / SR
        x = np.sin(2 * np.pi * (root * 2) * (1 + 0.15 * np.exp(-tm * 30)) * tm) * np.exp(-tm * 9)
        _place(L, x, tt, 0.08 + 0.025 * j)
        _place(R, x, tt, 0.08 + 0.025 * j)

    # --- riser + reverse swell into the reveal, impacts on the beats of the story
    rs = _riser(rng, 2.2)
    _place(L, rs, reveal - 2.2, 0.16)
    _place(R, rs, reveal - 2.2, 0.16)
    sw = _reverse_swell(rng, 1.2)
    _place(L, sw, reveal - 1.2, 0.5)
    _place(R, sw, reveal - 1.2, 0.5)
    hits = [(1.0, False), (reveal, True)]
    if final:
        hits.append((T["focus"], False))
    hits.append((T["end"], True))
    for at, big in hits:
        x = _impact(rng, big)
        _place(L, x, at, 0.6 if big else 0.35)
        _place(R, x, at, 0.6 if big else 0.35)

    # --- end card: a held low chord ringing out
    m = int((length - T["end"]) * SR)
    if m > 0:
        ring = np.zeros(m)
        for iv in (0, 7, 12, 15):
            ring += np.sin(2 * np.pi * root * 2 * 2 ** (iv / 12) * np.arange(m) / SR)
        ring *= _env(m, 0.02, 2.5) * 0.08
        _place(L, ring, T["end"])
        _place(R, ring, T["end"])

    mix = np.stack([L, R], 1)
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))[:, None]
    mix = np.tanh(mix * 1.4)
    mix *= 0.89 / max(1e-9, np.abs(mix).max())
    pcm = (mix * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return {"bpm": int(bpm), "root_hz": float(root), "prog": prog}

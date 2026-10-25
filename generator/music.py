"""Original, synthesized "news / drama" score for the reels.

Nothing here is sampled or copied: every sound is generated from sine, saw and noise.
The style is an election-night news theme, not a horror bed: consonant chord loops
(i-VI-III-VII and the like), a driving kick and bass, a bright string-like ostinato,
brass-like stabs, and a snare roll into the reveal. It follows the reel's timeline
(gen.py REEL timings): build while the bars grow, a roll into "ובקלפי...", a full hit
on the reveal, a lighter hit when the biggest miss is highlighted, and a major-chord
stinger on the end card.
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


def _kick(n=None):
    n = n or int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def _snare(rng, dec=0.12):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5
    nz = _bp(rng.standard_normal(n), 1200, 7000) * np.exp(-t / dec)
    return body + nz


def _hat(rng):
    n = int(0.05 * SR)
    return _hp(rng.standard_normal(n), 7000) * _env(n, 0.0005, 0.012)


def _crash(rng, dec=1.4):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    return _hp(rng.standard_normal(n), 5000) * np.exp(-t / dec) * 0.6


def _brass(freqs, dur, bright=3200):
    """Short brass-like stab: detuned saws, fast attack, filter closing."""
    n = int(dur * SR)
    x = np.zeros(n)
    for f in freqs:
        for d in (-0.006, 0.0, 0.006):
            x += _saw(f, n, d)
    a = _lp(x, bright) * 0.6 + _lp(x, bright * 0.35) * 0.4
    return a * _env(n, 0.012, dur * 0.5, 0.15) / max(1, len(freqs))


def _pluck(f, dur):
    n = int(dur * SR)
    x = _saw(f, n) * 0.6 + np.sign(np.sin(2 * np.pi * f * np.arange(n) / SR)) * 0.4
    return _lp(x, 2600) * _env(n, 0.003, 0.09)


def write_score(path, length, T, seed_text):
    rng = _rng(seed_text)
    n = int(length * SR)
    L = np.zeros(n)
    R = np.zeros(n)

    def put(x, at, g=1.0, pan=0.0):
        _place(L, x, at, g * (1 - max(pan, 0)))
        _place(R, x, at, g * (1 + min(pan, 0)))

    bpm = int(rng.choice([108, 112, 116, 120, 124, 128]))
    beat = 60.0 / bpm
    bar = 4 * beat
    root = float(rng.choice([55.0, 58.27, 61.74, 65.41, 69.30, 73.42]))   # A1 .. D2
    # consonant "news/epic" loops, in semitones from the tonic, with chord quality
    progs = [
        [(0, "m"), (8, "M"), (3, "M"), (10, "M")],    # i  VI  III VII
        [(0, "m"), (10, "M"), (8, "M"), (10, "M")],   # i  VII VI  VII
        [(0, "m"), (5, "m"), (8, "M"), (7, "M")],     # i  iv  VI  V
        [(8, "M"), (10, "M"), (0, "m"), (0, "m")],    # VI VII i   i
        [(0, "m"), (8, "M"), (10, "M"), (7, "M")],    # i  VI  VII V
    ]
    prog = progs[int(rng.integers(len(progs)))]
    arp = [[0, 1, 2, 1], [0, 2, 1, 2], [0, 1, 2, 3], [2, 1, 0, 1]][int(rng.integers(4))]
    final = T["morph"] < length
    reveal = T["morph"] if final else T["end"]
    start = 0.0                                    # music from the first frame

    def chord(semis, q, octave):
        third = 3 if q == "m" else 4
        return [root * octave * 2 ** ((semis + iv) / 12) for iv in (0, third, 7, 12)]

    t0 = start
    k = 0
    while t0 < T["end"]:
        semis, q = prog[k % len(prog)]
        after = t0 >= reveal - 1e-6
        ch = chord(semis, q, 4)
        # pad (soft strings), overlapping the next bar so there is no gap
        m = int(min(bar + 0.6, length - t0) * SR)
        pad = np.zeros(m)
        for f in ch[:3]:
            for d in (-0.004, 0.004):
                pad += _saw(f, m, d, rng.random())
        pad = _lp(pad, 2200 if after else 1400) * _env(m, 0.25, 4.0, 0.7) * 0.035
        rel = min(m, int(0.6 * SR))
        pad[-rel:] *= np.linspace(1, 0, rel)
        put(pad, t0)
        for b in range(4):
            tb = t0 + b * beat
            if tb >= T["end"]:
                break
            # kick: on 1 and 3 while building, every beat after the reveal
            if after or b in (0, 2):
                put(_kick(), tb, 0.55)
            # backbeat: from the reveal on
            if after and b in (1, 3):
                put(_snare(rng), tb, 0.32)
            # bass: root on eighths, pumping against the kick
            for h in (0, 1):
                f = root * 2 ** (semis / 12)
                m2 = int(beat / 2 * SR)
                x = _lp(_saw(f, m2), 320) * _env(m2, 0.004, 0.18) + 0.5 * np.sin(2 * np.pi * f * np.arange(m2) / SR) * _env(m2, 0.004, 0.2)
                put(x, tb + h * beat / 2, 0.30 if h == 0 else 0.22)
                put(_hat(rng), tb + h * beat / 2 + beat / 4, 0.08, 0.3)
            # string ostinato on sixteenths, one octave up
            hi = chord(semis, q, 8)
            for s16 in range(4):
                put(_pluck(hi[arp[s16]], beat / 4 + 0.05), tb + s16 * beat / 4, 0.07 if after else 0.05, -0.25)
        # brass stab on every chord change after the reveal
        if after:
            put(_brass(chord(semis, q, 4)[:3], 0.45), t0, 0.22)
        t0 += bar
        k += 1

    # snare roll into the reveal (eighths -> sixteenths -> thirty-seconds, crescendo)
    roll = []
    t = reveal - 2 * beat
    while t < reveal - 1e-6:
        frac = (t - (reveal - 2 * beat)) / (2 * beat)
        roll.append((t, frac))
        t += beat / 2 if frac < 0.25 else (beat / 4 if frac < 0.6 else beat / 8)
    for tt, frac in roll:
        put(_snare(rng, 0.07), tt, 0.10 + 0.25 * frac)
    sw = _hp(rng.standard_normal(int(1.0 * SR)), 3000) * np.linspace(0, 1, int(1.0 * SR)) ** 2
    put(sw, reveal - 1.0, 0.12)

    # hits
    semis0, q0 = prog[0]
    put(_kick(int(0.6 * SR)), reveal, 0.8)
    put(_crash(rng), reveal, 0.35)
    put(_brass(chord(semis0, q0, 4)[:3], 0.9), reveal, 0.28)
    if final:
        put(_crash(rng, 0.8), T["focus"], 0.2)
        put(_brass(chord(semis0, q0, 8)[:3], 0.4), T["focus"], 0.12)

    # end card: tonic MAJOR chord (a bright resolution), brass + crash, ringing out
    m = int((length - T["end"]) * SR)
    if m > 0:
        end = chord(0, "M", 4)
        put(_kick(int(0.6 * SR)), T["end"], 0.7)
        put(_crash(rng, 1.8), T["end"], 0.35)
        put(_brass(end[:3], length - T["end"], 2600), T["end"], 0.32)
        ring = np.zeros(m)
        for f in end:
            ring += np.sin(2 * np.pi * f / 2 * np.arange(m) / SR)
        put(ring * _env(m, 0.01, 2.0) * 0.05, T["end"])

    mix = np.stack([L, R], 1)
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix = np.tanh(mix * 1.3)
    mix *= 0.89 / max(1e-9, np.abs(mix).max())
    pcm = (mix * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return {"bpm": bpm, "root_hz": root, "prog": [p[0] for p in prog]}

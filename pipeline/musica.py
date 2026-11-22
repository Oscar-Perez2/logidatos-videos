#!/usr/bin/env python3
"""Música de fondo ORIGINAL para LogiDatos, sintetizada en código (numpy/scipy).
Al generarse aquí mismo no usa samples ni pistas de terceros: no hay copyright de nadie más.

Generar:  python3 musica.py gen --dur 42 --preset espacio --seed 2 --out musica.wav
Mezclar:  python3 musica.py mix silent.mp4 voz.mp3 musica.wav salida.mp4 --total 42

Presets (elige según el tema y varía la semilla en cada video):
  espacio   – ambiental, campanitas suaves (espacio, planetas, océano profundo)
  curioso   – alegre y ligero, pizzicato + percusión suave (animales, cuerpo, comida)
  misterio  – menor, pulso tipo reloj (historia, misterios, récords)
  energia   – más ritmo (tecnología, física, inventos, deportes)
"""
import argparse, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, lfilter

SR = 44100
PRESETS = {
    #           raíz MIDI, progresión (grados en semitonos + calidad), bpm, instrumentos
    "espacio":  dict(root=57, prog=[(0, "m"), (-4, "M"), (3, "M"), (-2, "M")], bpm=80, lead="bell", drums=False, sub=True, arp="slow"),
    "curioso":  dict(root=60, prog=[(0, "M"), (7, "M"), (9, "m"), (5, "M")], bpm=104, lead="pluck", drums=True, sub=False, arp="eighths"),
    "misterio": dict(root=62, prog=[(0, "m"), (-4, "M"), (5, "m"), (7, "M")], bpm=88, lead="pluck", drums="tick", sub=True, arp="eighths"),
    "energia":  dict(root=64, prog=[(0, "m"), (-4, "M"), (3, "M"), (-2, "M")], bpm=116, lead="pluck", drums=True, sub=True, arp="sixteenths"),
}

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def chord(root, q): return [root, root + (3 if q == "m" else 4), root + 7]

def env(n, a, r, sr=SR):
    e = np.ones(n); na = min(n, int(a * sr)); nr = min(n, int(r * sr))
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); return lfilter([1 - a], [1, -a], x)

def pad_note(f, dur, rng):
    t = np.arange(int(dur * SR)) / SR; s = np.zeros_like(t)
    for d in (-0.12, 0.0, 0.11):
        ff = f * 2 ** (d / 12); ph = rng.uniform(0, 2 * np.pi)
        s += np.sin(2 * np.pi * ff * t + ph) + 0.35 * np.sin(4 * np.pi * ff * t + ph) + 0.12 * np.sin(6 * np.pi * ff * t + ph)
    return lowpass(s, 1400) * env(len(t), 0.8, 1.0) / 3

def pluck(f, dur=0.9):
    t = np.arange(int(dur * SR)) / SR; s = np.zeros_like(t)
    for k in range(1, 7): s += np.sin(2 * np.pi * k * f * t) * np.exp(-t * (4 + 3.5 * k)) / k ** 1.4
    return s * env(len(t), 0.004, 0.05)

def bell(f, dur=2.2):
    t = np.arange(int(dur * SR)) / SR; idx = 2.2 * np.exp(-t * 2.5)
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 3.5 * f * t)) * np.exp(-t * 1.6)
    return s * env(len(t), 0.003, 0.3)

def kick():
    t = np.arange(int(0.35 * SR)) / SR; f = 45 + 75 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)

def hat(rng, dec=45, dur=0.12):
    n = int(dur * SR); x = np.diff(rng.standard_normal(n + 1)); t = np.arange(n) / SR
    return x * np.exp(-t * dec) * 0.25

def reverb(x, rng, secs=1.8, wet=0.28):
    n = int(secs * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.2); ir = lowpass(ir, 5000); ir /= np.sqrt(np.sum(ir ** 2))
    return (1 - wet) * x + wet * fftconvolve(x, ir)[: len(x)]

def add(buf, sig, start, gain=1.0):
    i = int(start * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig)); buf[i:j] += sig[: j - i] * gain

def generate(dur, preset, seed):
    P = PRESETS[preset]; rng = np.random.default_rng(seed)
    beat = 60 / P["bpm"]; bar = 4 * beat; n = int((dur + 3) * SR)
    L = np.zeros(n); R = np.zeros(n)
    prog = P["prog"][:]
    if seed % 2: prog = prog[2:] + prog[:2]          # variación por semilla
    root = P["root"] + int(rng.integers(-2, 3))       # tonalidad ligeramente distinta por video
    pattern = rng.permutation([0, 1, 2, 3, 2, 1, 0, 2])
    nbars = int(np.ceil(dur / bar)) + 1
    for b in range(nbars):
        deg, q = prog[b % len(prog)]; ch = chord(root + deg - 12, q); t0 = b * bar
        for m in ch:  # pad
            p = pad_note(hz(m), bar + 1.0, rng); add(L, p, t0, 0.16); add(R, p, t0, 0.16)
        if P["sub"]:
            sb = pad_note(hz(root + deg - 24), bar + 0.5, rng); add(L, sb, t0, 0.18); add(R, sb, t0, 0.18)
        tones = [m + 12 for m in ch] + [ch[0] + 24]
        if P["arp"] == "slow": steps, sub = 4, beat
        elif P["arp"] == "eighths": steps, sub = 8, beat / 2
        else: steps, sub = 16, beat / 4
        for s in range(steps):
            if P["arp"] == "sixteenths" and s % 4 == 3 and rng.random() < 0.5: continue
            m = tones[pattern[s % 8] % len(tones)]
            note = bell(hz(m + 12)) if P["lead"] == "bell" else pluck(hz(m))
            g = 0.10 if P["lead"] == "bell" else 0.13
            pan = 0.5 + 0.3 * (1 if s % 2 else -1)
            add(L, note, t0 + s * sub, g * (1 - pan) * 2); add(R, note, t0 + s * sub, g * pan * 2)
        if P["drums"] is True:
            for k in range(4):
                if k in (0, 2): add(L, kick(), t0 + k * beat, 0.32); add(R, kick(), t0 + k * beat, 0.32)
                for h in (0.5,) if P["bpm"] < 110 else (0.0, 0.5):
                    hh = hat(rng); add(L, hh, t0 + (k + h) * beat, 0.5); add(R, hh, t0 + (k + h) * beat, 0.4)
        elif P["drums"] == "tick":
            for k in range(8):
                hh = hat(rng, dec=90, dur=0.05); add(L, hh, t0 + k * beat / 2, 0.35 if k % 2 else 0.5); add(R, hh, t0 + k * beat / 2, 0.35)
    L = reverb(L, rng); R = reverb(R, np.random.default_rng(seed + 99))
    st = np.stack([L, R], 1)[: int(dur * SR)]
    fade_in, fade_out = int(1.0 * SR), int(2.5 * SR)
    st[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]; st[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
    rms = np.sqrt(np.mean(st ** 2)); st *= 10 ** (-20 / 20) / max(rms, 1e-9)     # RMS ≈ -20 dBFS
    st = np.tanh(st * 1.2) / 1.2                                                # techo suave
    return (np.clip(st, -1, 1) * 32767).astype(np.int16)

def mix(video, voice, music, out, total, music_db=-8.0):
    """Música bajo la voz con ducking suave (~4-5 dB cuando habla el narrador). Con -8 dB queda ~15 dB por debajo de la voz."""
    vol = 10 ** (music_db / 20)
    fc = (f"[1:a]aresample=44100,apad,asplit=2[v][sc];"
          f"[2:a]aresample=44100,volume={vol:.4f}[m];"
          f"[m][sc]sidechaincompress=threshold=0.08:ratio=2:attack=20:release=500[md];"
          f"[v][md]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", voice, "-i", music, "-filter_complex", fc,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(total), out], check=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("gen"); g.add_argument("--dur", type=float, required=True); g.add_argument("--preset", default="curioso", choices=PRESETS)
    g.add_argument("--seed", type=int, default=1); g.add_argument("--out", default="musica.wav")
    m = sp.add_parser("mix"); m.add_argument("video"); m.add_argument("voice"); m.add_argument("music"); m.add_argument("out")
    m.add_argument("--total", type=float, required=True); m.add_argument("--music_db", type=float, default=-8.0)
    a = ap.parse_args()
    if a.cmd == "gen":
        wavfile.write(a.out, SR, generate(a.dur, a.preset, a.seed)); print("OK", a.out)
    else:
        mix(a.video, a.voice, a.music, a.out, a.total, a.music_db); print("OK", a.out)

#!/usr/bin/env python3
"""Deterministic, original 16-wavetable curated design prototypes.

Offline-only. Four frames, nine band limits, 256 samples per row.
Does not modify legacy 108 table IDs or Move runtime.
"""
import math
from spectral_shape import _fft
from generate_shape_variants import BAND_LIMITS, N

NAMES = ("Sine", "Saw", "Square", "Triangle", "Odd", "Formant",
         "Hollow", "Metallic", "Glass", "Vocal", "Organic", "Resonant",
         "Inharmonic", "Spectral Sweep", "Fractal", "Noise-like")
FRAMES = 4

def harmonic_weight(table, h, frame):
    t = frame / (FRAMES - 1)
    if table == 0: return 1.0 if h == 1 else 0.0
    if table == 1: return h ** (-1.0 - 0.4 * t)
    if table == 2: return (h ** (-1.0 - 0.2 * t)) if h % 2 else 0.0
    if table == 3: return (h ** (-2.0 - 0.3 * t)) if h % 2 else 0.0
    if table == 4: return (h ** (-0.8 - 0.45*t)) if h % 2 else 0.0
    if table == 5: return math.exp(-((h - (4 + 11*t)) / 2.4)**2) / math.sqrt(h)
    if table == 6: return (h ** -1.0) if h % 3 == 1 else 0.02 / h
    if table == 7: return (0.2 + 0.8 * abs(math.sin(h * (0.83 + 0.13*t)))) / h**0.7
    if table == 8: return math.exp(-((h - (7 + 17*t)) / 3.5)**2) / h**0.4
    if table == 9: return sum(math.exp(-((h - c) / 1.6)**2) for c in (3+4*t, 9+6*t, 18+7*t)) / h**0.5
    if table == 10: return (0.35 + 0.65 * abs(math.sin(h * 0.37 + t * 2.0))) / h**1.1
    if table == 11: return math.exp(-((h - (3 + 18*t)) / 1.5)**2) / h**0.3
    if table == 12: return (0.9 if h in (2, 5, 9, 15, 23, 34) else 0.008) / h**0.35
    if table == 13: return math.exp(-((h - (2 + 26*t)) / 4.0)**2) / h**0.5
    if table == 14: return (0.5 + 0.5 * abs(math.sin(h*h*0.11+t))) / h**0.9
    return (0.2 + 0.8 * abs(math.sin(h*12.9898+78.233+t*7.0))) / h**0.75

def generate_row(table, frame, limit):
    if not 0 <= table < len(NAMES) or not 0 <= frame < FRAMES or limit not in BAND_LIMITS:
        raise ValueError("invalid table/frame/band")
    bins = [0j] * N
    for h in range(1, limit + 1):
        weight = harmonic_weight(table, h, frame)
        phase = (h * h * 0.037 + frame * h * 0.13) if table >= 7 else 0.0
        coefficient = 0.5j * weight * complex(math.cos(phase), math.sin(phase))
        bins[h] = -coefficient
        bins[N-h] = coefficient.conjugate() * -1
    row = [x.real for x in _fft(bins, inverse=True)]
    peak = max(abs(x) for x in row)
    if peak:
        row = [0.8 * x / peak for x in row]
    return row

def generate_bank():
    return [[ [generate_row(table, frame, limit) for limit in BAND_LIMITS]
              for frame in range(FRAMES)] for table in range(len(NAMES))]

def raw_float32_bytes():
    return len(NAMES) * FRAMES * len(BAND_LIMITS) * N * 4

if __name__ == "__main__":
    print("Curated tables:", len(NAMES))
    print("Float32 bytes:", raw_float32_bytes())

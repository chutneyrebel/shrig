#!/usr/bin/env python3
"""Phase 10B offline spectral shaping prototype.

Pure Python, standard library only. All transforms run offline, never in Move's
audio callback. This module intentionally does not modify existing wavetable IDs.
"""
import math

def spectral_shape(samples, tilt=0.0, cutoff=1.0, mix=1.0):
    """Shape a periodic real waveform using harmonic amplitudes.

    tilt: -1..1 (positive brightens upper harmonics)
    cutoff: 0..1 (soft harmonic lowpass; 1 is bypass)
    mix: 0..1 (0 is exact bypass)
    """
    n = len(samples)
    if n < 4 or n & (n - 1):
        raise ValueError("sample count must be a power of two >= 4")
    if not all(math.isfinite(x) for x in samples):
        raise ValueError("non-finite waveform sample")
    if not all(math.isfinite(x) for x in (tilt, cutoff, mix)):
        raise ValueError("non-finite shaping parameter")
    if not -1 <= tilt <= 1 or not 0 <= cutoff <= 1 or not 0 <= mix <= 1:
        raise ValueError("shaping parameter out of range")
    if mix == 0 or (tilt == 0 and cutoff == 1):
        return list(samples)
    nyquist = n // 2
    output = [sum(samples) / n] * n
    for harmonic in range(1, nyquist + 1):
        re = sum(samples[i] * math.cos(2 * math.pi * harmonic * i / n) for i in range(n))
        im = -sum(samples[i] * math.sin(2 * math.pi * harmonic * i / n) for i in range(n))
        # Log-frequency tilt. Harmonic one always remains at unity gain.
        gain = (harmonic ** tilt)
        if cutoff < 1:
            edge = max(1.0, cutoff * nyquist)
            gain *= 1.0 / (1.0 + (harmonic / edge) ** 8)
        gain = min(gain, 8.0)
        scale = (1.0 if harmonic == nyquist else 2.0) / n * gain
        for i in range(n):
            angle = 2 * math.pi * harmonic * i / n
            output[i] += scale * (re * math.cos(angle) - im * math.sin(angle))
    return [original + mix * (shaped - original)
            for original, shaped in zip(samples, output)]

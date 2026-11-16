#!/usr/bin/env python3
"""Phase 10B standalone offline spectral prototype regression tests."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from spectral_shape import spectral_shape

N = 64
def sine(h=1):
    return [0.5 * math.sin(2 * math.pi * h * i / N) for i in range(N)]
def magnitude(samples, h):
    re = sum(v * math.cos(2 * math.pi * h * i / N) for i, v in enumerate(samples))
    im = sum(v * math.sin(2 * math.pi * h * i / N) for i, v in enumerate(samples))
    return math.hypot(re, im)

class SpectralPrototypeTests(unittest.TestCase):
    def test_neutral_is_exact(self):
        original = [a + b for a, b in zip(sine(1), sine(9))]
        self.assertEqual(spectral_shape(original), original)
        self.assertEqual(spectral_shape(original, tilt=1, cutoff=0.2, mix=0), original)
    def test_brighten_and_darkening(self):
        original = [a + b for a, b in zip(sine(1), sine(8))]
        bright = spectral_shape(original, tilt=0.5)
        dark = spectral_shape(original, tilt=-0.5)
        self.assertGreater(magnitude(bright, 8), magnitude(original, 8) * 2)
        self.assertLess(magnitude(dark, 8), magnitude(original, 8) * 0.5)
    def test_filter_reduces_high_harmonics(self):
        original = [a + b for a, b in zip(sine(1), sine(20))]
        filtered = spectral_shape(original, cutoff=0.15)
        self.assertLess(magnitude(filtered, 20), magnitude(original, 20) * 0.01)
    def test_half_mix(self):
        original = [a + b for a, b in zip(sine(1), sine(8))]
        wet = spectral_shape(original, tilt=-0.5)
        half = spectral_shape(original, tilt=-0.5, mix=0.5)
        for a, b, c in zip(original, wet, half):
            self.assertAlmostEqual(c, (a + b) / 2, places=8)
    def test_invalid_inputs(self):
        for kwargs in ({"tilt": 2}, {"cutoff": -1}, {"mix": float("nan")}):
            with self.assertRaises(ValueError):
                spectral_shape(sine(), **kwargs)
        with self.assertRaises(ValueError):
            spectral_shape([1, 2, 3])
if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Curated wavetable design contracts, not a Move DSP integration test."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from curated_wavetables import NAMES, FRAMES, N, BAND_LIMITS, generate_row, raw_float32_bytes
from spectral_shape import _fft

class CuratedWavetableTests(unittest.TestCase):
    def test_library_size_and_footprint(self):
        self.assertEqual(len(NAMES), 16)
        self.assertEqual(len(set(NAMES)), 16)
        self.assertEqual(raw_float32_bytes(), 16 * 4 * 9 * 256 * 4)
    def test_all_tables_are_finite_and_bounded(self):
        for table in range(16):
            for frame in range(FRAMES):
                for band in BAND_LIMITS:
                    row = generate_row(table, frame, band)
                    self.assertEqual(len(row), N)
                    self.assertTrue(all(math.isfinite(x) and abs(x) <= 0.800001 for x in row))
    def test_bandlimiting(self):
        for table in range(16):
            for limit in (1, 8, 32, 96):
                bins = _fft(generate_row(table, 2, limit))
                self.assertLess(max(abs(x) for x in bins[limit+1:N-limit]), 1e-7)
    def test_frames_evolve(self):
        for table in range(1, 16):
            a = generate_row(table, 0, 48)
            b = generate_row(table, 3, 48)
            self.assertGreater(max(abs(x-y) for x,y in zip(a,b)), 1e-5)
    def test_sine_is_nearly_pure(self):
        bins = _fft(generate_row(0, 0, 96))
        self.assertLess(max(abs(x) for x in bins[2:96]), 1e-8)
if __name__ == "__main__":
    unittest.main()

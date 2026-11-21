"""Contract tests for the offline spectral reference; no live DSP changes."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from spectral_reference import SIZE, analyze, synthesize, transform


class SpectralReferenceTests(unittest.TestCase):
    def setUp(self):
        self.wave = [0.5 * math.sin(2 * math.pi * t / SIZE)
                     + 0.2 * math.sin(2 * math.pi * 7 * t / SIZE)
                     + 0.15 * math.sin(2 * math.pi * 91 * t / SIZE)
                     for t in range(SIZE)]

    def test_exact_zero_depth_bypass(self):
        self.assertEqual(transform(self.wave), self.wave)

    def test_dft_roundtrip(self):
        recovered = synthesize(analyze(self.wave))
        self.assertLess(max(abs(a - b) for a, b in zip(self.wave, recovered)), 1e-10)

    def test_each_operator_audible_and_distinct(self):
        variants = [transform(self.wave, **{key: 1.0})
                    for key in ("shift", "fold", "scramble")]
        for out in variants:
            self.assertGreater(sum((a-b)**2 for a, b in zip(self.wave, out)), 0.001)
            self.assertTrue(all(math.isfinite(x) for x in out))
        for i in range(len(variants)):
            for j in range(i):
                self.assertGreater(sum((a-b)**2 for a, b in zip(variants[i], variants[j])), 0.001)

    def test_composition_is_not_simple_original_blend(self):
        combined = transform(self.wave, 0.6, 0.7, 0.8)
        isolated = transform(self.wave, 0.6, 0, 0)
        self.assertGreater(sum((a-b)**2 for a, b in zip(combined, isolated)), 0.001)

    def test_scramble_seed_is_repeatable(self):
        self.assertEqual(transform(self.wave, scramble=1, seed=27),
                         transform(self.wave, scramble=1, seed=27))
        self.assertNotEqual(transform(self.wave, scramble=1, seed=27),
                            transform(self.wave, scramble=1, seed=28))

    def test_invalid_inputs_rejected(self):
        for bad in (-0.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                transform(self.wave, fold=bad)
        with self.assertRaises(ValueError):
            transform(self.wave[:-1], shift=0.5)


if __name__ == "__main__":
    unittest.main()

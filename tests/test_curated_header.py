#!/usr/bin/env python3
"""Ensure curated C bank is deterministic and doesn't disturb legacy runtime."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_curated_header import generate

class CuratedHeaderTests(unittest.TestCase):
    def test_deterministic_header(self):
        with tempfile.TemporaryDirectory() as directory:
            a = generate(Path(directory) / "a.h").read_bytes()
            b = generate(Path(directory) / "b.h").read_bytes()
            self.assertEqual(a, b)
            self.assertIn(b"static const float synth_esis_curated_tables[16][4][9][256]", a)
            self.assertEqual(a.count(b"/* "), 17)
    def test_legacy_runtime_not_modified(self):
        root = Path(__file__).resolve().parents[1]
        self.assertNotIn("curated_tables.h", (root / "src" / "dsp.c").read_text())
if __name__ == "__main__":
    unittest.main()

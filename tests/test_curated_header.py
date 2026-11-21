#!/usr/bin/env python3
"""Ensure curated C bank is deterministic and doesn't disturb legacy runtime."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_curated_header import generate
from curated_wavetables import NAMES
from aggressive_spectral import MODES

class CuratedHeaderTests(unittest.TestCase):
    def test_deterministic_header(self):
        with tempfile.TemporaryDirectory() as directory:
            a = generate(Path(directory) / "a.h").read_bytes()
            b = generate(Path(directory) / "b.h").read_bytes()
            self.assertEqual(a, b)
            self.assertIn(b"static const float synth_esis_curated_tables[16][4][9][256]", a)
            # One file header, one comment per curated table and spectral mode.
            self.assertEqual(a.count(b"/* "), 1 + len(NAMES) + len(MODES))
            for name in NAMES:
                self.assertIn(("/* " + name + " */").encode("ascii"), a)
            for mode in MODES:
                self.assertIn(("/* " + mode + " */").encode("ascii"), a)
    def test_curated_bank_is_opt_in(self):
        """Optional curated bank must not affect default legacy DSP builds."""
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "dsp.c").read_text()
        self.assertEqual(source.count('#include "curated_tables.h"'), 1)
        self.assertIn(
            '#ifdef SYNTH_ESIS_ENABLE_CURATED\n#include "curated_tables.h"',
            source,
        )
        self.assertIn(
            '#ifdef SYNTH_ESIS_ENABLE_CURATED\n    int t=clampi(table,0,123);\n'
            '#else\n    int t=clampi(table,0,107);\n#endif',
            source,
        )
        self.assertIn('#ifdef SYNTH_ESIS_ENABLE_CURATED\n    if(t>=108)', source)
if __name__ == "__main__":
    unittest.main()

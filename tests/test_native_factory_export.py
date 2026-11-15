"""Native factory export produces safe Schwung-shaped files offline."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from export_native_factory import export_factory

class NativeFactoryExportTests(unittest.TestCase):
    def test_all_presets_and_native_state(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "native"
            self.assertEqual(export_factory(out), 16)
            docs = [json.loads(p.read_text()) for p in sorted(out.glob("*.json"))]
            self.assertEqual(len(docs), 16)
            self.assertEqual(len({p["name"] for p in docs}), 16)
            for p in docs:
                self.assertEqual(set(p), {"name", "module", "version", "state"})
                self.assertEqual(p["module"], "synth_esis")
                self.assertEqual(p["version"], 1)
                self.assertIsInstance(p["state"], str)
                self.assertIn("cutoff=", p["state"])
                self.assertIn("mx0_0=", p["state"])
                self.assertIn("mx1_11=", p["state"])
            with self.assertRaises(ValueError):
                export_factory(out)

if __name__ == "__main__":
    unittest.main()

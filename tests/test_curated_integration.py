#!/usr/bin/env python3
"""Curated bank integration guard: IDs reserved, old presets unaffected."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class CuratedIntegrationTests(unittest.TestCase):
    def test_curated_lookup_is_compile_guarded(self):
        dsp=(ROOT/"src/dsp.c").read_text()
        build=(ROOT/"scripts/build.sh").read_text()
        self.assertIn("#ifdef SYNTH_ESIS_ENABLE_CURATED",dsp)
        self.assertIn("curated_table_at(t-108,p0,band,phase)",dsp)
        self.assertIn("curated_table_at(t-108,p1,band,phase)",dsp)
        self.assertIn("int t=clampi(table,0,107)",dsp)
        self.assertIn("int t=clampi(table,0,123)",dsp)
        self.assertIn("-DSYNTH_ESIS_ENABLE_CURATED -Ibuild",build)
    def test_existing_user_parameters_stay_legacy_bounded(self):
        params=json.loads((ROOT/"src/module.json").read_text())["capabilities"]["chain_params"]
        by_key={p["key"]:p for p in params}
        self.assertEqual(by_key["wavetable"]["max"],107)
        self.assertEqual(by_key["osc2_wavetable"]["max"],107)
        self.assertEqual(by_key["wt_bank"]["options"],["Legacy","Expanded"])
if __name__=="__main__":
    unittest.main()

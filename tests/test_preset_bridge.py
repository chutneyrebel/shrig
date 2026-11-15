"""Preset bridge must fail closed until hardware APIs are verified."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from preset_schema import default_patch
from preset_bridge import DryRunBridge, UnsafePresetApply, build_apply_plan

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.original = default_patch("Original")
        self.candidate = copy.deepcopy(self.original)
        self.candidate["name"] = "New Patch"
        self.candidate["parameters"]["cutoff"] = 41
        self.candidate["parameters"]["resonance"] = 23

    def test_changes_only_and_deterministic(self):
        plan = build_apply_plan(self.original, self.candidate)
        self.assertEqual({x["key"] for x in plan}, {"cutoff", "resonance"})
        self.assertEqual(plan, build_apply_plan(self.original, self.candidate))

    def test_identical_patch_is_noop(self):
        self.assertEqual(build_apply_plan(self.original, self.original), [])

    def test_no_snapshot_is_rejected(self):
        with self.assertRaises(UnsafePresetApply):
            DryRunBridge().plan(self.candidate)

    def test_snapshot_is_copied(self):
        bridge = DryRunBridge(self.original)
        self.original["parameters"]["cutoff"] = 100
        self.assertEqual(bridge.plan(self.candidate)[0]["from"], 78)

    def test_apply_never_writes(self):
        bridge = DryRunBridge(self.original)
        with self.assertRaises(UnsafePresetApply):
            bridge.apply(self.candidate)

    def test_invalid_candidate_is_rejected(self):
        self.candidate["parameters"]["cutoff"] = 999
        with self.assertRaises(ValueError):
            DryRunBridge(self.original).plan(self.candidate)

if __name__ == "__main__":
    unittest.main()

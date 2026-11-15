#!/usr/bin/env python3
"""Host-side Phase 10A patch interchange regression tests."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from preset_schema import default_patch, parse_patch, serialize_patch, validate_patch, parameter_specs

class PresetSchemaTests(unittest.TestCase):
    def setUp(self):
        self.patch = default_patch("Test texture")

    def test_roundtrip(self):
        self.assertEqual(parse_patch(serialize_patch(self.patch)), self.patch)

    def test_complete_writable_parameters(self):
        self.assertEqual(set(self.patch["parameters"]), set(parameter_specs()))
        self.assertNotIn("face_snapshot", self.patch["parameters"])
        self.assertNotIn("voice_activity", self.patch["parameters"])

    def test_missing_and_unknown_parameters(self):
        for operation in ("missing", "unknown"):
            patch = copy.deepcopy(self.patch)
            if operation == "missing":
                patch["parameters"].pop(next(iter(patch["parameters"])))
            else:
                patch["parameters"]["unknown"] = 10
            with self.assertRaises(ValueError):
                validate_patch(patch)

    def test_invalid_values(self):
        for key, spec in parameter_specs().items():
            for bad in (float("nan"), float("inf"), True, "50"):
                patch = copy.deepcopy(self.patch)
                patch["parameters"][key] = bad
                with self.assertRaises(ValueError):
                    validate_patch(patch)
            patch = copy.deepcopy(self.patch)
            patch["parameters"][key] = 1000000
            with self.assertRaises(ValueError):
                validate_patch(patch)

    def test_identity_and_schema(self):
        for field, value in (("module_id", "sprig-wt"), ("schema", 99), ("name", "")):
            patch = copy.deepcopy(self.patch)
            patch[field] = value
            with self.assertRaises(ValueError):
                validate_patch(patch)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            parse_patch('{"schema":1,"schema":1}')

    def test_json_size_limit(self):
        with self.assertRaises(ValueError):
            parse_patch(" " * 65537)

if __name__ == "__main__":
    unittest.main()

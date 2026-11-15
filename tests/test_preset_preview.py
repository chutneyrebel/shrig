"""Phase 10C reversible preset preview regression tests."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from preset_schema import default_patch
from preset_preview import PreviewSession

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.current = default_patch("Original")
        self.calls = []
        def apply(patch):
            self.calls.append(copy.deepcopy(patch))
            self.current = copy.deepcopy(patch)
        self.apply = apply
        self.session = PreviewSession(lambda: self.current, self.apply)
        self.a = default_patch("Glass Memory")
        self.b = default_patch("Copper Coil")

    def test_preview_then_cancel(self):
        self.session.begin()
        self.session.preview(self.a)
        self.session.preview(self.b)
        self.assertEqual(self.current, self.b)
        self.session.cancel()
        self.assertEqual(self.current["name"], "Original")
        self.assertFalse(self.session.active)

    def test_preview_then_confirm(self):
        self.session.begin()
        self.session.preview(self.a)
        self.assertEqual(self.session.confirm(), self.a)
        self.assertEqual(self.current, self.a)
        self.assertFalse(self.session.active)

    def test_close_restores(self):
        self.session.begin()
        self.session.preview(self.a)
        self.session.close()
        self.assertEqual(self.current["name"], "Original")

    def test_no_preview_without_begin(self):
        with self.assertRaises(RuntimeError):
            self.session.preview(self.a)

    def test_confirm_requires_candidate(self):
        self.session.begin()
        with self.assertRaises(RuntimeError):
            self.session.confirm()
        self.session.cancel()

    def test_invalid_patch_does_not_apply(self):
        self.session.begin()
        invalid = copy.deepcopy(self.a)
        invalid["parameters"]["cutoff"] = 1000
        with self.assertRaises(ValueError):
            self.session.preview(invalid)
        self.assertEqual(self.calls, [])
        self.session.cancel()

    def test_failed_apply_rolls_back(self):
        def failing_apply(patch):
            if patch["name"] == "Glass Memory":
                raise OSError("transport failed")
            self.current = copy.deepcopy(patch)
        session = PreviewSession(lambda: self.current, failing_apply)
        session.begin()
        with self.assertRaises(OSError):
            session.preview(self.a)
        self.assertEqual(self.current["name"], "Original")
        self.assertIsNone(session.candidate)
        session.cancel()

if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from tools.verify_sdk import find_conflict_markers

ROOT = Path(__file__).resolve().parents[1]


class VerifySdkTests(unittest.TestCase):
    def test_clean_tree(self):
        with tempfile.TemporaryDirectory() as td:
            tree = Path(td)
            (tree / "dlls").mkdir()
            (tree / "dlls" / "world.cpp").write_text("void Spawn() {}\n")
            self.assertEqual(find_conflict_markers(tree), [])

    def test_markers_detected(self):
        with tempfile.TemporaryDirectory() as td:
            tree = Path(td)
            (tree / "pm_shared").mkdir()
            (tree / "pm_shared" / "pm_shared.cpp").write_text("<<<<<<< ours\ncode\n>>>>>>> theirs\n")
            self.assertEqual(find_conflict_markers(tree), ["pm_shared/pm_shared.cpp"])

    def test_real_merged_tree_is_clean(self):
        tree = ROOT / "build" / "merged-real"
        if tree.is_dir():
            self.assertEqual(find_conflict_markers(tree), [])


if __name__ == "__main__":
    unittest.main()

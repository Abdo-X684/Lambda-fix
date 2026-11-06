import shutil
import tempfile
import unittest
from pathlib import Path

from merge.projects import (
    CLIENT_SOURCES,
    patch_makefile,
    patch_tree,
    patch_vcxproj,
    read_text,
)

ROOT = Path(__file__).resolve().parents[1]
VCX = '<?xml version="1.0" encoding="utf-8"?>\n<Project>\n  <ItemGroup>\n    <ClCompile Include="..\\..\\cl_dll\\hud.cpp" />\n  </ItemGroup>\n</Project>\n'
MK = "HL1_OBJS = \\\n\t$(HL1_OBJ_DIR)/hud.o \\\n\nall:\n\t@echo ok\n"


class ProjectPatchTests(unittest.TestCase):
    def test_vcxproj_is_idempotent_and_valid_xml(self):
        import xml.etree.ElementTree as ET
        new, added = patch_vcxproj(VCX, CLIENT_SOURCES)
        self.assertEqual(len(added), 2)
        self.assertIn("sr_hud_timer.cpp", new)
        ET.fromstring(new)
        again, added2 = patch_vcxproj(new, CLIENT_SOURCES)
        self.assertEqual(again, new)
        self.assertEqual(added2, [])

    def test_makefile_is_idempotent(self):
        new, added = patch_makefile(MK, "HL1_OBJS", CLIENT_SOURCES)
        self.assertEqual(len(added), 2)
        self.assertIn("$(GAME_SHARED_OBJ_DIR)/sr_core.o", new)
        self.assertIn("HL1_OBJS = \\\n\t$(HL1_OBJ_DIR)/sr_hud_timer.o", new)
        again, added2 = patch_makefile(new, "HL1_OBJS", CLIENT_SOURCES)
        self.assertEqual(again, new)
        self.assertEqual(added2, [])

    def test_missing_anchor_raises(self):
        from merge.projects import ProjectPatchError
        with self.assertRaises(ProjectPatchError):
            patch_makefile("nothing here\n", "HL1_OBJS", CLIENT_SOURCES)
        with self.assertRaises(ProjectPatchError):
            patch_vcxproj("<Project></Project>", CLIENT_SOURCES)

    def test_patch_tree_on_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            tree = Path(td) / "sdk"
            shutil.copytree(ROOT / "tests" / "fixtures" / "upstreams" / "op4", tree)
            changes = patch_tree(tree)
            self.assertEqual(len(changes), 4)
            self.assertTrue(all(c["changed"] for c in changes))
            self.assertIn("sr_hud_timer.cpp", read_text(tree / "projects" / "vs2019" / "hl_cdll.vcxproj"))
            again = patch_tree(tree)
            self.assertTrue(all(not c["changed"] for c in again))


if __name__ == "__main__":
    unittest.main()

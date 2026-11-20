"""Regression tests: BugfixedHL must be MERGED (compiled in), not referenced.

The user's correction: "I said merge BHL and add the compatibilities, but you
built a completely new system ... you removed BHL". These tests assert that
real BHL systems live in integration/bhl/, are copied into the OP4 tree by
merge/bhl.py, are wired into OP4's lifecycle, and are present in the shipped
ELF32 binaries.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BHL = ROOT / "integration" / "bhl"


class BhlMergeTests(unittest.TestCase):
    def test_bhl_sources_carry_gpl_provenance(self) -> None:
        for name in ("bhl_compat.cpp", "base.h", "speedometer.cpp",
                     "jumpspeed.cpp", "strafeguide.cpp", "bhlcfg.cpp",
                     "bhl_server.cpp"):
            text = (BHL / name).read_text(encoding="utf-8")
            self.assertIn("BugfixedHL", text, name)
            self.assertIn("GPL-3.0", text, name)

    def test_real_bhl_systems_are_present(self) -> None:
        checks = {
            "bhl_compat.h": ("class ConVar", "class ConCommand", "class CvarSystem",
                             "CON_COMMAND", "FCVAR_BHL_ARCHIVE"),
            "base.h": ("class CHudElem", "CHudElemBase", "DEFINE_HUD_ELEM"),
            "speedometer.cpp": ("CHudSpeedometer", "hud_speedometer"),
            "jumpspeed.cpp": ("CHudJumpspeed", "hud_jumpspeed"),
            "strafeguide.cpp": ("CHudStrafeGuide", "hud_strafeguide"),
            "bhlcfg.cpp": ("bugfixedhl.cfg", "FCVAR_BHL_ARCHIVE"),
            "bhl_server.cpp": ("sv_bhl_query_vars", "sv_bhl_defer_motd",
                               "CVAR_REGISTER"),
        }
        for name, needles in checks.items():
            text = (BHL / name).read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, f"{name}: {needle}")

    def test_merge_plan_lists_all_bhl_subsystems(self) -> None:
        from merge import bhl  # noqa: E402
        joined = " ".join(bhl.SYSTEMS)
        for needle in ("ConVar", "CHudElem", "CHudSpeedometer", "CHudJumpspeed",
                       "CHudStrafeGuide", "bhlcfg", "sv_bhl_query_vars"):
            self.assertIn(needle, joined, needle)
        self.assertEqual(len(bhl.CLIENT_SOURCES), 8)
        self.assertEqual(len(bhl.SERVER_SOURCES), 1)
        self.assertGreaterEqual(len(bhl.INJECTIONS), 10)

    def test_merge_bhl_applies_systems_and_compat_to_a_tree(self) -> None:
        from merge import bhl  # noqa: E402
        # Minimal OP4-shaped tree with the anchors merge/bhl.py expects.
        stubs = {
            "cl_dll/hud.h": ('#pragma once\nclass CHud\n{\npublic:\n'
                             '\tint m_iFontHeight;\n};\n'),
            "cl_dll/hud.cpp": ('#include "hud.h"\n'
                               'void CHud::Init()\n{\n}\n'
                               'void CHud::VidInit()\n{\n}\n'),
            "cl_dll/hud_redraw.cpp": ('#include "hud.h"\n'
                                      'bool CHud::Redraw(float flTime, bool intermission)\n{\n\treturn true;\n}\n'),
            "cl_dll/view.cpp": ('#include "Exports.h"\n'
                                'void DLLEXPORT V_CalcRefdef(struct ref_params_s* pparams)\n{\n}\n'),
            "cl_dll/input.cpp": ('#include "Exports.h"\n'
                                 'void DLLEXPORT HUD_Shutdown()\n{\n}\n'),
            "cl_dll/ammo.cpp": ('#include "hud.h"\n'
                                'bool CHudAmmo::MsgFunc_CurWeapon()\n{\n'
                                '\t\tm_pWeapon = nullptr;\n'
                                '\tm_pWeapon = pWeapon;\n}\n'),
            "cl_dll/vgui_ScorePanel.cpp": ('#include "hud.h"\n'
                                           'void CScorePanel::Update()\n{\n'
                                           '\t\t\t\t\tsprintf(sz, "%d", g_PlayerInfoList[m_iSortedRows[row]].ping);\n}\n'
                                           'SBColumnInfo g_ColumnInfo[NUM_COLUMNS] =\n\t{\n'
                                           '\t\t{"#VOICE", 40, Label::a_east},\n'
                                           '\t\t{NULL, 2, Label::a_east}, // blank column\n\t};\n'
                                           'void CScorePanel::Scores()\n{\n\t\t\t\tcase COLUMN_DEATHS:\n'
                                           '\t\t\t\t\tsprintf(sz, "%d", g_PlayerExtraInfo[m_iSortedRows[row]].deaths);\n\t\t\t\t\tbreak;\n}\n'),
            "cl_dll/vgui_ScorePanel.h": ('#define COLUMN_VOICE 6\n#define COLUMN_BLANK 7\n#define NUM_COLUMNS 8\n'),
            "cl_dll/death.cpp": ('#include "hud.h"\n'
                                 'void CHudDeathNotice::MsgFunc_DeathMsg()\n{\n'
                                 '\tint killer = READ_BYTE();\n\tint victim = READ_BYTE();\n}\n'),
            "cl_dll/ev_common.cpp": ('#include "hud.h"\n'
                                     'void EV_EjectBrass(float* origin, float* velocity, float rotation, int model, int soundtype)\n{\n}\n'),
            "cl_dll/StudioModelRenderer.cpp": ('#include "hud.h"\n'
                                               'bool CStudioModelRenderer::StudioDrawModel(int flags)\n{\n\treturn true;\n}\n'),
            "cl_dll/saytext.cpp": ('#include "hud.h"\n'
                                   'bool CHudSayText::MsgFunc_SayText()\n{\n'
                                   '\tint client_index = READ_BYTE(); // the client who spoke the message\n'
                                   '\tSayTextPrint(READ_STRING(), iSize - 1, client_index);\n}\n'),
            "dlls/world.cpp": ('#include "extdll.h"\n'
                               'void CWorld::Spawn()\n{\n}\n'),
            "linux/Makefile.hl_cdll": "HL1_OBJS = \\\n\t$(HL1_OBJ_DIR)/hud.o \\\n",
            "linux/Makefile.hldll": "HLDLL_OBJS = \\\n\t$(HLDLL_OBJ_DIR)/world.o \\\n",
            "projects/vs2019/hl_cdll.vcxproj": '<ClCompile Include="..\\..\\cl_dll\\hud.cpp" />\n',
            "projects/vs2019/hldll.vcxproj": '<ClCompile Include="..\\..\\dlls\\world.cpp" />\n',
        }
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            for rel, body in stubs.items():
                path = tree / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
            report = bhl.merge_into(tree)
            self.assertEqual(report["kind"], "bhl-into-op4-systems-merge")
            self.assertEqual(report["copied_files"], 20)
            self.assertEqual(report["injections_added"], len(bhl.INJECTIONS))
            self.assertEqual(report["injection_targets_missing"], [])
            for rel in ("cl_dll/speedometer.cpp", "cl_dll/base.h",
                        "cl_dll/bhl_compat.cpp", "dlls/bhl_server.cpp"):
                self.assertTrue((tree / rel).is_file(), rel)
            hud_h = (tree / "cl_dll/hud.h").read_text()
            self.assertIn("enum class HudPart { Common };", hud_h)
            # The enum must be at namespace scope, NOT inside class CHud.
            self.assertLess(hud_h.index("enum class HudPart"), hud_h.index("class CHud"))
            self.assertIn("DrawHudNumberCentered", hud_h)
            hud_cpp = (tree / "cl_dll/hud.cpp").read_text()
            self.assertIn("BHL_Init();", hud_cpp)
            self.assertIn("BHL_VidInit();", hud_cpp)
            self.assertIn("BHL_Draw(flTime);",
                          (tree / "cl_dll/hud_redraw.cpp").read_text())
            self.assertIn("BHL_OnRefdef(pparams);", (tree / "cl_dll/view.cpp").read_text())
            self.assertIn("BHL_Server_Init();", (tree / "dlls/world.cpp").read_text())
            mk = (tree / "linux/Makefile.hl_cdll").read_text()
            self.assertIn("$(HL1_OBJ_DIR)/speedometer.o", mk)
            self.assertIn("$(HL1_OBJ_DIR)/bhl_compat.o", mk)
            self.assertTrue((tree / "BHL_MERGE_REPORT.json").is_file())
            # Idempotent: a second pass adds nothing.
            again = bhl.merge_into(tree)
            self.assertEqual(again["copied_files"], 0)
            self.assertEqual(again["injections_added"], 0)

    def test_shipped_binaries_contain_the_bhl_systems(self) -> None:
        client = (ROOT / "dist/dlls/client.so").read_bytes()
        server = (ROOT / "dist/dlls/hl.so").read_bytes()
        self.assertEqual(client[:5], b"\x7fELF\x01")
        self.assertEqual(server[:5], b"\x7fELF\x01")
        for marker in (b"hud_speedometer", b"hud_jumpspeed", b"hud_strafeguide",
                       b"bhl_status", b"bhl_version", b"bugfixedhl.cfg",
                       b"BugfixedHL systems merged", b"CHudSpeedometer"):
            self.assertIn(marker, client, marker.decode())
        for marker in (b"sv_bhl_query_vars", b"sv_bhl_defer_motd",
                       b"sv_bhl_version", b"BugfixedHL server systems"):
            self.assertIn(marker, server, marker.decode())

    def test_speedrun_cfg_enables_the_bhl_systems_by_default(self) -> None:
        from merge.configgen import render_config  # noqa: E402
        cfg = render_config(ROOT)
        for name in ("hud_speedometer", "hud_jumpspeed", "hud_strafeguide"):
            self.assertIn(f'{name} "1"', cfg, name)

    def test_install_guide_explains_the_merge_not_the_addon(self) -> None:
        from tools.create_mod import install_text  # noqa: E402
        text = install_text("bhlop4")
        for needle in ("What is actually merged", "bhl_status", "bhl_version",
                       "bugfixedhl.cfg", "optional add-on", "not the merge"):
            self.assertIn(needle, text, needle)

    def test_bhl_merge_documents_the_correction(self) -> None:
        doc = (ROOT / "docs/BHL_MERGE.md").read_text(encoding="utf-8")
        for needle in ("Correction to an earlier path", "Compatibility layer", "GPL-3.0",
                       "sr_*", "bhl_status"):
            self.assertIn(needle, doc, needle)


if __name__ == "__main__":
    unittest.main()

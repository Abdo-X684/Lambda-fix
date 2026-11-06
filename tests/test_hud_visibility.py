"""Regression tests: the merged mod MUST be visibly different from stock OP4.

Bug report: "no BHL signs at all, it looks like a normal game". Root causes:
  * no sr_* cvar was registered on the client -> CVAR_GET_FLOAT() returned 0
    and SR_HUD_Redraw() bailed out;
  * the local RunTimer was never started, so `shown == 0` caused another early
    return until the first server split;
  * no cvars on the server either -> split broadcasts were suppressed.
The fix registers every cvar with a visible default, starts the timer at
CHud::Init(), draws a brand banner from frame one, and adds sr_status.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "overlay" / "cl_dll" / "sr_hud_timer.cpp"
SERVER = ROOT / "overlay" / "dlls" / "sr_server.cpp"


class HudVisibilityTests(unittest.TestCase):
    def test_client_registers_cvars_with_visible_defaults(self) -> None:
        src = CLIENT.read_text(encoding="utf-8")
        for decl in (
            'CVAR_CREATE("sr_timer_enable", "1"',
            'CVAR_CREATE("sr_timer_hud", "1"',
            'CVAR_CREATE("sr_hud_banner", "1"',
        ):
            self.assertIn(decl, src, decl)

    def test_client_timer_starts_at_init(self) -> None:
        src = CLIENT.read_text(encoding="utf-8")
        init = src[src.index("void SR_HUD_Init()"):src.index("void SR_HUD_Reset()")]
        self.assertIn("g_Timer.Start()", init)
        # No engine commands at CHud::Init() time (too early for `record`).
        self.assertNotIn("RestartDemo();", init)

    def test_client_draws_brand_banner_without_waiting_for_a_split(self) -> None:
        src = CLIENT.read_text(encoding="utf-8")
        redraw = src[src.index("void SR_HUD_Redraw("):]
        self.assertIn("[ BHL x OP4 SPEEDRUN ]", redraw)
        self.assertIn("pfnDrawSetTextColor", redraw)
        self.assertIn("SPLIT  waiting for first map change", redraw)
        self.assertNotIn("if (shown <= 0", redraw)

    def test_server_registers_cvars_and_status_command(self) -> None:
        src = SERVER.read_text(encoding="utf-8")
        for cvar, symbol in (("sr_net_splits", "sr_cv_net_splits"),
                             ("sr_splits_announce", "sr_cv_splits_announce"),
                             ("sr_practice_mode", "sr_cv_practice_mode"),
                             ("sr_version", "sr_cv_version")):
            self.assertIn(f"cvar_t {symbol}", src)
            self.assertIn(f'{{"{cvar}"', src)
            self.assertIn(f"CVAR_REGISTER(&{symbol})", src)
        self.assertIn('pfnAddServerCommand("sr_status", Command_Status)', src)
        self.assertIn("server DLL LOADED", src)

    def test_speedrun_cfg_ships_the_banner_cvar(self) -> None:
        cvars = json.loads((ROOT / "data" / "cvars.json").read_text(encoding="utf-8"))
        banner = [c for c in cvars["cvars"] if c["name"] == "sr_hud_banner"]
        self.assertEqual(len(banner), 1)
        self.assertEqual(banner[0]["value"], "1")

        sys_path = str(ROOT)
        import sys
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        from merge.configgen import render_config  # noqa: E402
        self.assertIn('sr_hud_banner "1"', render_config(ROOT))

    def test_shipped_binaries_contain_the_visible_markers(self) -> None:
        expected = {
            "client.so": [b"[ BHL x OP4 SPEEDRUN ]", b"client.so LOADED",
                          b"sr_hud_banner", b"SRSplit"],
            "hl.so": [b"server DLL LOADED", b"sr_status", b"sr_version",
                      b"SRSplit"],
        }
        for name, markers in expected.items():
            data = (ROOT / "dist" / "dlls" / name).read_bytes()
            self.assertEqual(data[:5], b"\x7fELF\x01", f"{name} is not ELF32")
            for marker in markers:
                self.assertIn(marker, data, f"{name}: missing {marker!r}")
        self.assertIn(b"vgui.so", (ROOT / "dist" / "dlls" / "client.so").read_bytes())

    def test_manifest_matches_the_rebuilt_binaries(self) -> None:
        manifest = json.loads((ROOT / "dist" / "dlls" / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["arch"], "ELF32 i386")
        for name, info in manifest["files"].items():
            data = (ROOT / "dist" / "dlls" / name).read_bytes()
            self.assertEqual(info["bytes"], len(data), name)
            self.assertEqual(info["sha256"], hashlib.sha256(data).hexdigest(), name)
            self.assertTrue(info["elf32"], name)

    def test_install_guide_explains_how_to_verify_the_dlls_are_loaded(self) -> None:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.create_mod import install_text  # noqa: E402
        text = install_text("bhlop4")
        for needle in ("sr_status", "sr_version", "client.so LOADED",
                       "not loading our two DLLs", "-game bhlop4"):
            self.assertIn(needle, text, needle)

    def test_mod_folder_zip_uses_the_new_binaries(self) -> None:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.create_mod import build  # noqa: E402
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bhlop4"
            zp = Path(tmp) / "mod.zip"
            build("bhlop4", out, zp)
            with zipfile.ZipFile(zp) as z:
                self.assertEqual(z.read("bhlop4/cl_dlls/client.so"),
                                 (ROOT / "dist" / "dlls" / "client.so").read_bytes())
                self.assertIn(b"sr_status", z.read("bhlop4/INSTALL.md"))
                self.assertIn(b'sr_hud_banner "1"', z.read("bhlop4/speedrun.cfg"))


if __name__ == "__main__":
    unittest.main()

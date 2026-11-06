import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.package_mod import FILES, build

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_package_contents_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            result = build(ROOT, out, tree=out / "no-report")
            self.assertTrue(result["ok"])
            zpath = out / "bhl-op4-speedrun-overlay.zip"
            self.assertTrue(zpath.is_file())
            with zipfile.ZipFile(zpath) as z:
                names = set(z.namelist())
                manifest = json.loads(z.read("MANIFEST.json"))
                self.assertIn("INSTALL.md", names)
                self.assertIn("gamedir/speedrun.cfg", names)
                self.assertIn("gamedir/splits/op4_route.json", names)
                self.assertIn("src/cl_dll/sr_hud_msg.cpp", names)
                self.assertIn("src/dlls/sr_server.cpp", names)
                self.assertIn("src/game_shared/sr_core.cpp", names)
                self.assertGreaterEqual(len(list((n for n in names if n.endswith(".snippet")))), 8)
                self.assertEqual(len(names), manifest["archive_entries"])
                self.assertFalse(manifest["includes_upstream_sources"])
                for name, meta in manifest["files"].items():
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), meta["sha256"], name)
                    self.assertEqual(len(z.read(name)), meta["bytes"], name)
                cfg = z.read("gamedir/speedrun.cfg").decode()
                self.assertIn('sv_cheats "0"', cfg)
                self.assertIn('sv_allowbunnyhopping "1"', cfg)
            with zipfile.ZipFile(zpath) as z2:
                self.assertEqual(z2.read("MANIFEST.json"), (out / "MANIFEST.json").read_bytes())

    def test_no_upstream_sdk_code_is_packaged(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            result = build(ROOT, out, tree=out / "no-report")
            with zipfile.ZipFile(result["zip"]) as z:
                for name in z.namelist():
                    self.assertNotIn("hud.cpp", name)  # OP4 hud.cpp must never be shipped
                    self.assertNotIn(".cache", name)
                    self.assertNotIn("merged-real", name)

    def test_package_is_deterministic_without_report(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            a = build(ROOT, out, tree=out / "no-report")["sha256"]
            b = build(ROOT, out, tree=out / "no-report")["sha256"]
            self.assertEqual(a, b)

    def test_report_timestamp_does_not_break_determinism(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            tree = out / "tree"
            tree.mkdir()
            (tree / "MERGE_REPORT.md").write_text("# Report\n- Generated: 2026-01-01T00:00:00+00:00\n- Mode: upstream\n")
            a = build(ROOT, out, tree=tree)["sha256"]
            (tree / "MERGE_REPORT.md").write_text("# Report\n- Generated: 2030-12-31T23:59:59+00:00\n- Mode: upstream\n")
            b = build(ROOT, out, tree=tree)["sha256"]
            self.assertEqual(a, b)
            with zipfile.ZipFile(out / "bhl-op4-speedrun-overlay.zip") as z:
                self.assertNotIn("Generated:", z.read("MERGE_REPORT.md").decode())

    def test_every_declared_input_exists(self):
        for src, _dest in FILES:
            self.assertTrue((ROOT / src).is_file(), src)


if __name__ == "__main__":
    unittest.main()

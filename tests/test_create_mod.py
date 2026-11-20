import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools import create_mod as cm

ROOT = Path(__file__).resolve().parents[1]


class ModNameTests(unittest.TestCase):
    def test_safe_names_accepted(self):
        for name in ("lambda", "op4sr", "speedrun_mod", "bhl-op4-v1"):
            with self.subTest(name=name):
                self.assertEqual(cm.validate_mod_name(name), name)

    def test_every_valve_prefix_is_rejected(self):
        for prefix in cm.VALVE_PREFIXES:
            with self.subTest(prefix=prefix):
                with self.assertRaisesRegex(ValueError, "Valve prefix"):
                    cm.validate_mod_name(prefix)
                with self.assertRaisesRegex(ValueError, "Valve prefix"):
                    cm.validate_mod_name(prefix + "_custom")

    def test_invalid_characters_rejected(self):
        for name in ("", "My Mod", "../evil", "mod!", "Valve"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    cm.validate_mod_name(name)

    def test_prefix_list_matches_the_sdk_source(self):
        source = ROOT / ".cache" / "upstreams" / "op4" / "game_shared" / "filesystem_utils.cpp"
        if not source.is_file():
            self.skipTest("run make fetch first")
        text = source.read_text(encoding="utf-8")
        block = text.split("ValveGameDirectoryPrefixes[] =", 1)[1].split("};", 1)[0]
        import re
        found = re.findall(r'"([a-z]+)"', block)
        self.assertEqual(tuple(found), cm.VALVE_PREFIXES)


class ModContentTests(unittest.TestCase):
    def test_liblist_points_at_gearbox_not_a_valve_dir(self):
        text = cm.liblist_text("lambda")
        self.assertIn('fallback_dir "gearbox"', text)
        self.assertIn('gamedll_linux "dlls/hl.so"', text)
        self.assertIn('startmap "of0a0"', text)
        self.assertNotIn("gamedll_linux \"dlls/opfor.so\"", text)

    def test_build_produces_folder_zip_and_valid_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "lambda"
            zpath = Path(td) / "mod.zip"
            result = cm.build("lambda", out, zpath, ROOT / "dist" / "dlls")
            self.assertTrue(result["valve_prefix_safe"])
            self.assertTrue((out / "liblist.gam").is_file())
            self.assertTrue((out / "steam_appid.txt").is_file())
            self.assertEqual((out / "steam_appid.txt").read_text(), "50\n")
            self.assertTrue((out / "delta.lst").is_file())
            self.assertTrue((out / "speedrun.cfg").is_file())
            self.assertTrue((out / "splits" / "op4_route.json").is_file())
            self.assertTrue((out / "INSTALL.md").is_file())
            self.assertIn("DO NOT put these files inside gearbox",
                          (out / "INSTALL.md").read_text())
            manifest = json.loads((out / "MANIFEST.json").read_text())
            self.assertEqual(manifest["mod_dir"], "lambda")
            self.assertEqual(manifest["fallback_dir"], "gearbox")
            self.assertEqual(manifest["steam_appid"], 50)
            for rel, info in manifest["files"].items():
                data = (out / rel).read_bytes()
                self.assertEqual(len(data), info["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), info["sha256"])
            self.assertTrue((out / "cl_dlls" / "client.so").read_bytes()[:5] == b"\x7fELF\x01")
            with zipfile.ZipFile(zpath) as z:
                names = z.namelist()
                self.assertIn("lambda/liblist.gam", names)
                self.assertIn("lambda/cl_dlls/client.so", names)
                self.assertIn("lambda/MANIFEST.json", names)
                self.assertFalse(any(n.startswith("gearbox/") for n in names))
                self.assertEqual(z.read("lambda/MANIFEST.json"),
                                 (out / "MANIFEST.json").read_bytes())

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            a = cm.build("lambda", Path(td) / "a", Path(td) / "a.zip", ROOT / "dist" / "dlls")
            b = cm.build("lambda", Path(td) / "b", Path(td) / "b.zip", ROOT / "dist" / "dlls")
            self.assertEqual(a["zip_sha256"], b["zip_sha256"])

    def test_valve_dir_name_is_refused_by_build(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "Valve prefix"):
                cm.build("gearbox", Path(td) / "x", Path(td) / "x.zip", ROOT / "dist" / "dlls")

    def test_non_elf32_binary_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            dlls = Path(td) / "dlls"
            dlls.mkdir()
            (dlls / "client.so").write_bytes(b"NOT AN ELF")
            (dlls / "hl.so").write_bytes(b"\x7fELF\x01" + b"\0" * 40)
            with self.assertRaisesRegex(ValueError, "not ELF32"):
                cm.collect_payload("lambda", dlls, ROOT / "data" / "delta.lst")


if __name__ == "__main__":
    unittest.main()

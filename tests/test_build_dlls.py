import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import build_dlls as bd

ROOT = Path(__file__).resolve().parents[1]


def fake_tree(root: Path, *, patched: bool = True) -> Path:
    linux = root / "linux"
    linux.mkdir(parents=True, exist_ok=True)
    (linux / "Makefile").write_text("all: build_dir targets\n")
    (linux / "Makefile.hl_cdll").write_text(
        "sr_hud_timer.o\nsr_hud_msg.o\nsr_core.o\n" if patched else "nothing here\n")
    (linux / "Makefile.hldll").write_text(
        "sr_server.o\nsr_core.o\n" if patched else "nothing here\n")
    for rel in bd.OUR_SOURCES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("// stub\n")
    return root


class PreflightTests(unittest.TestCase):
    def test_complete_tree_is_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree, vgui = fake_tree(root / "tree"), root / "vgui.so"
            vgui.write_bytes(b"fake")
            report = bd.preflight(tree, vgui=str(vgui))
            self.assertTrue(report["tree_ready"], report["missing"])
            self.assertEqual(report["missing"], [])
            self.assertTrue(report["vgui"]["found"])
            self.assertIsInstance(report["toolchain"]["m32_ok"], bool)

    def test_missing_build_file_is_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            tree = fake_tree(Path(td))
            (tree / "linux" / "Makefile.hldll").unlink()
            report = bd.preflight(tree)
            self.assertFalse(report["tree_ready"])
            self.assertTrue(any("linux/Makefile.hldll" in m for m in report["missing"]))

    def test_unpatched_build_file_is_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            tree = fake_tree(Path(td), patched=False)
            report = bd.preflight(tree)
            self.assertFalse(report["tree_ready"])
            self.assertTrue(any("unpatched" in m for m in report["missing"]))

    def test_missing_source_is_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            tree = fake_tree(Path(td))
            (tree / "cl_dll" / "sr_hud_msg.cpp").unlink()
            self.assertIn("cl_dll/sr_hud_msg.cpp", bd.preflight(tree)["missing"])

    def test_explicit_vgui_wins(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree, vgui = fake_tree(root / "tree"), root / "vgui.so"
            vgui.write_bytes(b"fake")
            (tree / "linux" / "release").mkdir(parents=True)
            (tree / "linux" / "release" / "vgui.so").write_bytes(b"other")
            self.assertEqual(bd.find_vgui(tree, str(vgui)), vgui)
            self.assertEqual(bd.find_vgui(tree), tree / "linux" / "release" / "vgui.so")

    def test_blockers_are_honest(self):
        with tempfile.TemporaryDirectory() as td:
            tree = fake_tree(Path(td))
            with patch.object(bd, "probe_m32", return_value={"ok": False, "detail": "no multilib"}):
                report = bd.preflight(tree, vgui=str(Path(td) / "vgui.so"))
            self.assertFalse(report["ready"])
            self.assertTrue(any("gcc-multilib" in b for b in report["blockers"]))
            self.assertTrue(any("vgui.so" in b for b in report["blockers"]))


class ArtifactTests(unittest.TestCase):
    def test_elf32_detection(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a.so", Path(td) / "b.so"
            a.write_bytes(b"\x7fELF\x01" + b"\0" * 32)
            b.write_bytes(b"\x7fELF\x02" + b"\0" * 32)
            self.assertTrue(bd.is_elf32(a))
            self.assertFalse(bd.is_elf32(b))

    def test_manifest_and_install(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src, out, mod = root / "src", root / "out", root / "bhlop4"
            src.mkdir(); out.mkdir()
            (mod / "cl_dlls").mkdir(parents=True)
            (mod / "cl_dlls" / "client.so").write_bytes(b"STOCK")
            artifacts = {}
            for name in ("client.so", "hl.so"):
                p = src / name
                p.write_bytes(b"\x7fELF\x01" + name.encode())
                artifacts[name] = p
            tree = fake_tree(root / "tree")
            (tree / "network").mkdir()
            (tree / "network" / "delta.lst").write_text("// delta\n")
            manifest = bd.write_manifest(out, artifacts, {
                "compiler": "g++", "cfg": "release", "tree": str(tree)})
            for name, p in artifacts.items():
                self.assertEqual(manifest["files"][name]["sha256"],
                                 hashlib.sha256(p.read_bytes()).hexdigest())
                self.assertTrue(manifest["files"][name]["elf32"])
                self.assertEqual((out / name).read_bytes(), p.read_bytes())
            self.assertTrue((out / "MANIFEST.json").is_file())
            written = bd.install_artifacts(out, mod, tree)
            self.assertIn(str(mod / "cl_dlls" / "client.so"), written)
            self.assertEqual((mod / "cl_dlls" / "client.so.orig").read_bytes(), b"STOCK")
            self.assertEqual((mod / "cl_dlls" / "client.so").read_bytes()[:5], b"\x7fELF\x01")
            self.assertTrue((mod / "delta.lst").is_file())

    def test_check_mode_is_json_and_does_not_build(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree, vgui = fake_tree(root / "tree"), root / "vgui.so"
            vgui.write_bytes(b"fake")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = bd.main(["--check", "--require-tree", "--tree", str(tree),
                                "--vgui", str(vgui)])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(buf.getvalue())["tree_ready"])

    def test_build_refuses_when_toolchain_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree, vgui = fake_tree(root / "tree"), root / "vgui.so"
            vgui.write_bytes(b"fake")
            with patch.object(bd, "probe_m32", return_value={"ok": False, "detail": "no multilib"}):
                with redirect_stderr(io.StringIO()):
                    code = bd.main(["--tree", str(tree), "--vgui", str(vgui)])
            self.assertEqual(code, 2)


class CommittedBinaryTests(unittest.TestCase):
    def test_downloadable_binaries_match_manifest(self):
        import hashlib
        dlls = ROOT / "dist" / "dlls"
        manifest_path = dlls / "MANIFEST.json"
        if not manifest_path.is_file():
            self.skipTest("run make build-dlls-zig first")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name, info in manifest["files"].items():
            path = dlls / name
            with self.subTest(name=name):
                self.assertTrue(path.is_file())
                data = path.read_bytes()
                self.assertEqual(len(data), info["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), info["sha256"])
                self.assertTrue(bd.is_elf32(path))


if __name__ == "__main__":
    unittest.main()

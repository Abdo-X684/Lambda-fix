"""Tests for the canonical BHL-based OP4 merge tree (bhl-op4/)."""

from __future__ import annotations

import hashlib
import json
import posixpath
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREE = ROOT / "bhl-op4"
PROV = TREE / "PROVENANCE.json"
STATUS = TREE / "PORT_STATUS.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BhlBaseTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROV.is_file():
            raise unittest.SkipTest("bhl-op4/ tree not generated (run: make bhl-base)")
        cls.prov = json.loads(PROV.read_text())
        cls.status = json.loads(STATUS.read_text()) if STATUS.is_file() else {}

    def test_01_architecture_is_bhl_first(self):
        self.assertEqual(
            self.prov["architecture"],
            "BASE=BugfixedHL-Rebased, ADD/MERGE=halflife-op4-updated")
        self.assertEqual(self.prov["base"]["repo"], "tmp64/BugfixedHL-Rebased")
        self.assertEqual(self.prov["base"]["license"], "GPL-3.0")
        self.assertEqual(self.prov["op4"]["repo"],
                         "twhl-community/halflife-op4-updated")
        self.assertGreaterEqual(self.prov["base"]["files"], 690)
        self.assertGreater(self.prov["op4"]["files"], 100)
        self.assertEqual(len(self.prov["glue_files"]), 11)
        self.assertIn("src/game/client/op4/op4_client_prediction.cpp",
                      self.prov["glue_files"])

    def test_02_every_provenance_entry_matches_disk(self):
        bad = []
        for rel, rec in self.prov["files"].items():
            f = TREE / rel
            if not f.is_file():
                bad.append(f"missing {rel}")
            elif sha256(f) != rec["sha256"]:
                bad.append(f"sha {rel}")
        self.assertEqual(bad, [], "provenance mismatch: " + ", ".join(bad[:5]))

    def test_03_no_conflict_markers_in_tree(self):
        bad = []
        for p in TREE.rglob("*"):
            if not p.is_file() or p.suffix not in (".cpp", ".h", ".txt", ".cmake", ".json"):
                continue
            try:
                t = p.read_text(errors="surrogateescape")
            except OSError:
                continue
            # Real conflict markers start a line; upstream BHL legitimately
            # contains ">>>>>>>>" banner strings in update_installer.cpp.
            if any(line.startswith(("<<<<<<< ", ">>>>>>> "))
                   for line in t.splitlines()):
                bad.append(str(p.relative_to(TREE)))
        self.assertEqual(bad, [])

    def test_04_driver_check_passes(self):
        r = subprocess.run(
            [sys.executable, "-m", "merge.bhl_base", "--check", "--out", "bhl-op4"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("BHL-BASE PROVENANCE OK", r.stdout)

    def test_05_every_cmake_wired_source_compiled_clean(self):
        self.assertEqual(self.status.get("status"), "compiled")
        errors = []
        for rel, srcs in self.prov["cmake"].items():
            side = "server" if "server" in rel else "client"
            cmake_text = (TREE / rel).read_text()
            for s in srcs:
                if s not in cmake_text:
                    errors.append(f"not in CMake: {s}")
                key = posixpath.normpath(f"src/game/{side}/{s}")
                rec = self.status["files"].get(key)
                if not rec or not rec["ok"]:
                    errors.append(f"did not compile: {key}")
        self.assertEqual(errors, [])

    def test_06_all_op4_weapons_compile_into_elf32_objects(self):
        weapons = [k for k in self.status["files"]
                   if k.startswith("src/game/server/op4/dlls/weapons/")]
        self.assertEqual(len(weapons), 15)
        failed = [k for k in weapons if not self.status["files"][k]["ok"]]
        self.assertEqual(failed, [])
        self.assertIn("x86-linux-gnu", self.status["target"])

    def test_07_verbatim_bhl_files_still_match_pinned_upstream(self):
        upstream = ROOT / ".cache/upstreams/bugfixhl"
        if not upstream.is_dir():
            self.skipTest("pinned BHL cache not present (run: make fetch)")
        verbatim = [(rel, rec) for rel, rec in self.prov["files"].items()
                    if rec["action"] == "verbatim" and rec["origin"] == "bugfixhl"]
        self.assertGreaterEqual(len(verbatim), 670)
        bad = []
        for rel, rec in verbatim:
            src = upstream / rel
            if not src.is_file() or sha256(src) != rec["sha256"]:
                bad.append(rel)
        self.assertEqual(bad, [], "BHL base files altered: " + ", ".join(bad[:5]))

    def test_08_merged_headers_carry_both_bhl_and_op4(self):
        checks = {
            "src/game/server/weapons.h": ("BULLET_PLAYER_EAGLE", "OP4-MERGE", "class CBasePlayerWeapon"),
            "src/game/server/cdll_dll.h": ("WEAPON_DISPLACER", "WEAPON_SUIT"),
            "src/common/const.h": ("WATERLEVEL_HEAD", "OP4-MERGE"),
            "src/game/server/skill.h": ("plrDmgSpore", "skilldata_t"),
            "src/game/server/player.h": ("ammo_762", "class CBasePlayer"),
            "src/game/server/gamerules.h": ("IsCTF", "class CGameRules"),
        }
        for rel, markers in checks.items():
            text = (TREE / rel).read_text()
            for marker in markers:
                self.assertIn(marker, text, f"{rel} missing {marker}")

    def test_09_glue_is_explicitly_labelled(self):
        h = (TREE / "src/game/server/op4/op4_compat.h").read_text()
        self.assertIn("NOT BugfixedHL", h)
        self.assertIn("does not reimplement", h)
        for rel in self.prov["glue_files"]:
            self.assertEqual(self.prov["files"][rel]["origin"], "this-repo")

    def test_11_base_tree_fingerprint_matches_disk(self):
        bhl_files = {r: v for r, v in self.prov["files"].items()
                     if v["origin"] == "bugfixhl"}
        digest = hashlib.sha256(
            "\n".join(f"{r}  {sha256(TREE / r)}" for r in sorted(bhl_files)).encode()
        ).hexdigest()
        self.assertEqual(digest, self.prov["base"]["tree_sha256"])
        # Every BHL file is either byte-identical or has a NAMED merge rule.
        # The exact split grows as weapon-scoped merges are added.
        self.assertEqual(self.prov["base"]["verbatim_files"]
                         + self.prov["base"]["merged_files"], 694)
        self.assertGreaterEqual(self.prov["base"]["merged_files"], 16)
        self.assertEqual(len(bhl_files), 694)

    def test_12_verbatim_bhl_server_sources_compile(self):
        bb = self.status["bhl_base"]
        self.assertGreaterEqual(bb["total"], 106)
        self.assertGreaterEqual(bb["clean"], 100)
        for rel in bb["files"]:
            rec = self.prov["files"][rel]
            self.assertEqual(rec["origin"], "bugfixhl", rel)
            self.assertEqual(rec["action"], "verbatim", rel)

    def test_13_op4_server_network_compat(self):
        checks = {
            "src/game/server/cdll_dll.h": ("MAX_WEAPONS 64", "MAX_WEAPON_SLOTS     7"),
            "src/game/server/weapons.h": ("MAX_WEAPONS 64",),
            "src/common/entity_state.h": ("weapondata[64]",),
            "src/game/client/entity.cpp": ("MAX_WEAPONS * sizeof(weapon_data_t)",),
            "src/game/client/hud.cpp": ('pfnHookUserMsg((char *)"Weapons"',),
            "src/game/client/hud_update.cpp": ("g_bOP4WeaponBits",),
            "src/game/client/op4/op4_client_prediction.cpp":
                ("OP4_MsgFunc_Weapons", "g_bOP4WeaponBits"),
        }
        for rel, markers in checks.items():
            text = (TREE / rel).read_text()
            for marker in markers:
                self.assertIn(marker, text, f"{rel} missing {marker}")

    def test_10_port_pending_matches_documented_count(self):
        wired = set()
        for rel, srcs in self.prov["cmake"].items():
            side = "server" if "server" in rel else "client"
            wired.update(posixpath.normpath(f"src/game/{side}/{s}")
                         for s in srcs)
        pending = sorted(
            str(p.relative_to(TREE)) for p in TREE.rglob("*.cpp")
            if "/op4/" in str(p.relative_to(TREE))
            and "reference" not in p.parts
            and str(p.relative_to(TREE)) not in wired)
        self.assertEqual(len(pending), self.prov["port_pending"]["count"])
        self.assertEqual(pending, self.prov["port_pending"]["files"])


if __name__ == "__main__":
    unittest.main()

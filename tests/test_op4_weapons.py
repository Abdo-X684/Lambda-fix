"""OP4 weapon integration tests (weapon scope ONLY).

TEST KIND: **build / link / source-level verification, NOT an in-game test.**
This module never claims a weapon works inside Half-Life. It proves that each
merged OP4 weapon is:

  * registered by the server's W_Precache() (ItemInfoArray / WeaponList),
  * hooked by the client's Game_HookEvents() to its playback-event script,
  * backed by the VERBATIM OP4 event body (compared byte-for-byte upstream),
  * present as a real, non-empty ELF32 symbol in client.so / hl.so,
  * covered by a declared, named BHL merge rule,
  * linked with zero unresolved own-build symbols.

In-game firing/reload/animation/sound proof requires the GoldSrc engine and
legal OP4 assets, which this sandbox does not have. That is recorded in
build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md and is NOT claimed here.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from merge import op4_weapon_events as wev

ROOT = Path(__file__).resolve().parent.parent
TREE = ROOT / "bhl-op4"
EVIDENCE = ROOT / "build-evidence" / "bhl-base"
CLIENT = EVIDENCE / "client.so"
SERVER = EVIDENCE / "hl.so"
PROV = TREE / "PROVENANCE.json"

TEST_KIND = "build+link+source (NOT in-game)"


def _brace_block(text: str, start: int) -> str:
    brace = text.index("{", start)
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise RuntimeError("unbalanced braces")


class Op4WeaponIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for p in (CLIENT, SERVER, PROV,
                  TREE / "src/game/server/weapons.cpp",
                  TREE / "src/game/client/hl/hl_events.cpp",
                  TREE / "src/game/client/op4/op4_weapon_events.cpp"):
            if not p.is_file():
                raise unittest.SkipTest(f"missing {p}")
        cls.prov = json.loads(PROV.read_text())
        cls.weapons_cpp = (TREE / "src/game/server/weapons.cpp").read_text()
        cls.hl_events = (TREE / "src/game/client/hl/hl_events.cpp").read_text()
        cls.ev_cpp = (TREE / "src/game/client/op4/op4_weapon_events.cpp").read_text()
        cls.ev_h = (TREE / "src/game/client/op4/op4_weapon_events.h").read_text()
        cls.upstream_ev = (wev.OP4 / "cl_dll" / "ev_hldm.cpp").read_text()
        cls.client_def = subprocess.run(
            ["nm", "--defined-only", str(CLIENT)], capture_output=True,
            text=True, check=True).stdout
        cls.server_def = subprocess.run(
            ["nm", "--defined-only", str(SERVER)], capture_output=True,
            text=True, check=True).stdout
        cls.manifest = json.loads((EVIDENCE / "MANIFEST.json").read_text())

    def test_01_server_registers_each_weapon(self):
        """W_Precache must precache every merged OP4 weapon (else no WeaponList)."""
        for w in wev.WEAPONS:
            with self.subTest(weapon=w["cls"]):
                needle = f'UTIL_PrecacheOtherWeapon("{w["cls"]}");'
                self.assertIn(needle, self.weapons_cpp,
                              f"{w['cls']} is compiled but NOT registered")
                if w["ammo"]:
                    self.assertIn(f'UTIL_PrecacheOther("{w["ammo"]}");',
                                  self.weapons_cpp)
        # No BHL weapon registration was removed.
        for bhl_w in ("weapon_crowbar", "weapon_9mmhandgun", "weapon_9mmAR",
                      "weapon_357", "weapon_gauss", "weapon_rpg",
                      "weapon_crossbow", "weapon_egon", "weapon_hornetgun"):
            with self.subTest(bhl_weapon=bhl_w):
                self.assertIn(f'UTIL_PrecacheOtherWeapon("{bhl_w}");',
                              self.weapons_cpp)

    def test_02_client_hooks_each_weapon_event(self):
        """Game_HookEvents must route each OP4 .sc script to its callback."""
        for w in wev.WEAPONS:
            with self.subTest(weapon=w["cls"]):
                self.assertIn(f'void {w["func"]}(struct event_args_s *args);',
                              self.hl_events, "missing extern \"C\" declaration")
                self.assertIn(
                    f'gEngfuncs.pfnHookEvent("{w["event"]}", {w["func"]});',
                    self.hl_events, "event script is never hooked")
        # No BHL event hook was removed.
        for bhl_ev in ("events/glock1.sc", "events/mp5.sc",
                       "events/gauss.sc", "events/snarkfire.sc",
                       "events/vehicle.sc"):
            with self.subTest(bhl_event=bhl_ev):
                self.assertIn(bhl_ev, self.hl_events)

    def test_03_event_bodies_are_verbatim_op4(self):
        """The shipped callback is byte-for-byte OP4's, not a rewrite/stub."""
        for w in wev.WEAPONS:
            with self.subTest(weapon=w["cls"]):
                m = re.search(r"^void " + re.escape(w["func"]) +
                              r"\(.*?\)\s*\{", self.upstream_ev, re.M | re.S)
                self.assertIsNotNone(m, "upstream body missing")
                upstream = _brace_block(self.upstream_ev, m.start()).strip()
                self.assertIn(upstream, self.ev_cpp,
                              "shipped body differs from pinned OP4 source")
                self.assertGreater(len(upstream), 400,
                                   "body suspiciously short (possible stub)")
        for w in wev.WEAPONS:
            for en in w["enums"]:
                with self.subTest(enum=en):
                    self.assertIn(f"enum {en}", self.ev_h)
        for name in wev.BULLET_TYPES:
            with self.subTest(bullet=name):
                self.assertIn(name, self.ev_h)

    def test_04_merges_are_declared_by_name(self):
        files = self.prov["files"]
        expected = {
            "src/game/server/weapons.cpp": ("op4-wprecache-op4-weapons",),
            "src/game/client/hl/hl_events.cpp": (
                "op4-client-weapon-event-decls",
                "op4-client-weapon-event-hooks"),
        }
        for rel, rules in expected.items():
            with self.subTest(file=rel):
                rec = files[rel]
                self.assertEqual(rec["origin"], "bugfixhl")
                self.assertEqual(rec["action"], "bhl+op4-merge")
                got = {r if isinstance(r, str) else r["rule"]
                       for r in rec.get("merge_rules", [])}
                for rule in rules:
                    self.assertIn(rule, got)
        glued = set(self.prov["glue_files"])
        for rel in ("src/game/client/op4/op4_weapon_events.h",
                    "src/game/client/op4/op4_weapon_events.cpp"):
            self.assertIn(rel, glued)
            self.assertEqual(files[rel]["origin"], "this-repo")
        wired = set(self.prov["cmake"]["src/game/client/CMakeLists.txt"])
        self.assertIn("op4/op4_weapon_events.cpp", wired)

    def test_05_elf32_symbols_are_real_and_non_empty(self):
        """client.so owns the event callback; hl.so owns the weapon class."""
        for w in wev.WEAPONS:
            with self.subTest(weapon=w["cls"]):
                self.assertIn(f" T {w['func']}\n", self.client_def,
                              f"{w['func']} not defined in client.so")
        for w in wev.WEAPONS:
            cname = w["cxx_class"]
            demangled = subprocess.run(
                ["c++filt"], input=self.server_def, capture_output=True,
                text=True, check=True).stdout
            self.assertIn(f"{cname}::Spawn()", demangled,
                          f"{cname}::Spawn missing from hl.so")
        if shutil.which("objdump"):
            for w in wev.WEAPONS:
                out = subprocess.run(
                    ["objdump", "-d", f"--disassemble={w['func']}", str(CLIENT)],
                    capture_output=True, text=True, check=True).stdout
                insns = [ln for ln in out.splitlines()
                         if "\t" in ln and ln.split("\t")[0].strip().endswith(":")]
                self.assertGreater(len(insns), 8,
                                   f"{w['func']} is an empty stub")

    def test_06_link_has_no_own_build_gaps(self):
        lib = self.manifest.get("libraries", self.manifest)
        for name in ("client.so", "hl.so"):
            with self.subTest(lib=name):
                self.assertTrue(lib[name]["elf32"])
                self.assertEqual(lib[name]["unresolved_own_build_symbols"], [])

    def test_07_this_is_not_an_in_game_test(self):
        """Guard against accidentally claiming runtime proof."""
        env = json.loads((EVIDENCE / "RUNTIME_ENVIRONMENT.json").read_text())
        self.assertIn(env.get("verdict"), ("NOT EXECUTABLE", "not executable"),
                      "runtime environment changed; re-evaluate in-game evidence")
        self.assertEqual(TEST_KIND, "build+link+source (NOT in-game)")


if __name__ == "__main__":
    unittest.main()

"""Verification of the 12 OP4 link gaps that the FINAL BOSS phase had to close.

This test inspects the DELIVERED ELF32 libraries, not the source tree alone:
  * every one of the 12 symbols must be DEFINED (not merely absent),
  * none of them may remain in the undefined-symbol table,
  * code symbols must disassemble to a real (non-empty) body, data symbols
    must have a non-zero size,
  * the provenance / declared-BHL-change evidence must be present.

It does NOT claim an in-game Opposing Force test. See
build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md for why that is impossible here.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "build-evidence" / "bhl-base"
CLIENT = EVIDENCE / "client.so"
SERVER = EVIDENCE / "hl.so"
MANIFEST = EVIDENCE / "MANIFEST.json"
PROV = ROOT / "bhl-op4" / "PROVENANCE.json"

# Exact demangled names from UNDEFINED_SYMBOLS.txt of the previous build.
CLIENT_GAPS = [
    "CBasePlayerWeapon::GetNextAttackDelay(float)",
    "typeinfo for CBasePlayerWeapon",
    "vtable for CBasePlayerWeapon",
]
SERVER_GAPS = [
    "CBaseMonster::AddShockEffect(float, float, float, float, float)",
    "CBasePlayerWeapon::GetNextAttackDelay(float)",
    "CRope::DetachObject()",
    "CTFGoalFlag::DropFlag(CBasePlayer*)",
    "CWorld::World",
    "oldgrapple",
    "oldweapons",
    "typeinfo for CBasePlayerWeapon",
    "vtable for CBasePlayerWeapon",
]
DATA_GAPS = {"CWorld::World", "oldgrapple", "oldweapons",
             "typeinfo for CBasePlayerWeapon", "vtable for CBasePlayerWeapon"}

# Two more real OP4 bodies added when 7 additional subsystem sources were
# wired into the BHL server target (see docs/BHL_BASE_MERGE.md). Neither may
# stay undefined, and neither may be an empty stub.
NEW_SERVER_FIXUPS = [
    "IsFacing(entvars_s*, Vector const&)",
    "CGib::SpawnRandomGibs(entvars_s*, int, GibData const&)",
]

NEW_WIRED_OP4 = (
    "op4/dlls/coopplay_gamerules.cpp",
    "op4/dlls/func_tank_of.cpp",
    "op4/dlls/hgrunt_medic.cpp",
    "op4/dlls/hgrunt_torch.cpp",
    "op4/dlls/pitworm_up.cpp",
    "op4/dlls/shocktrooper.cpp",
    "op4/dlls/voltigore.cpp",
)


def demangle(text: str) -> str:
    if not shutil.which("c++filt"):
        return text
    return subprocess.run(["c++filt"], input=text, capture_output=True,
                          text=True, check=True).stdout


def nm(lib: Path, defined: bool) -> str:
    flag = "--defined-only" if defined else "-u"
    return subprocess.run(["nm", flag, str(lib)], capture_output=True,
                          text=True, check=True).stdout


def demangled_map(lib: Path) -> dict[str, str]:
    """One c++filt call for the whole symbol table (thousands of symbols)."""
    out = nm(lib, True).splitlines()
    syms = [ln.split()[-1] for ln in out if len(ln.split()) >= 3]
    pretty = demangle("\n".join(syms) + "\n").splitlines()
    return dict(zip(syms, [p.strip() for p in pretty]))


_MAP: dict[str, dict[str, str]] = {}


def mangled(lib: Path, name: str) -> str | None:
    """Find the mangled symbol whose demangled form equals `name`."""
    if str(lib) not in _MAP:
        _MAP[str(lib)] = demangled_map(lib)
    for sym, pretty in _MAP[str(lib)].items():
        if pretty == name:
            return sym
    return None


class LinkGapClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for p in (CLIENT, SERVER, MANIFEST, PROV):
            if not p.is_file():
                raise unittest.SkipTest(f"missing {p}")
        data = json.loads(MANIFEST.read_text())
        cls.manifest = data.get("libraries", data)
        cls.prov = json.loads(PROV.read_text())
        cls.client_def = demangle(nm(CLIENT, True))
        cls.client_und = demangle(nm(CLIENT, False))
        cls.server_def = demangle(nm(SERVER, True))
        cls.server_und = demangle(nm(SERVER, False))

    def test_01_manifest_reports_zero_own_build_gaps(self):
        for lib in ("client.so", "hl.so"):
            with self.subTest(lib=lib):
                rec = self.manifest[lib]
                self.assertTrue(rec["elf32"], f"{lib} is not ELF32")
                self.assertEqual(rec["unresolved_own_build_symbols"], [],
                                 f"{lib} still reports link gaps")
        text = (EVIDENCE / "LINK_GAPS.md").read_text()
        self.assertNotIn("- `", text, "LINK_GAPS.md still lists gaps")

    def test_02_all_12_symbols_are_defined_and_no_longer_undefined(self):
        cases = [(CLIENT, self.client_def, self.client_und, CLIENT_GAPS),
                 (SERVER, self.server_def, self.server_und, SERVER_GAPS)]
        for lib, defined, undefined, gaps in cases:
            for name in gaps:
                with self.subTest(lib=lib.name, symbol=name):
                    self.assertIn(name, defined,
                                  f"{name} is NOT defined in {lib.name}")
                    self.assertNotIn(name, undefined,
                                     f"{name} is STILL UNDEFINED in {lib.name}")

    def test_03_code_bodies_are_real_not_empty_stubs(self):
        if not shutil.which("objdump"):
            self.skipTest("objdump not available")
        for lib, gaps in ((CLIENT, CLIENT_GAPS), (SERVER, SERVER_GAPS)):
            for name in gaps:
                if name in DATA_GAPS:
                    continue
                with self.subTest(lib=lib.name, symbol=name):
                    sym = mangled(lib, name)
                    self.assertIsNotNone(sym, f"no symbol for {name}")
                    out = subprocess.run(
                        ["objdump", "-d", f"--disassemble={sym}", str(lib)],
                        capture_output=True, text=True, check=True).stdout
                    insns = [ln for ln in out.splitlines()
                             if "\t" in ln and ln.split("\t")[0].strip().endswith(":")]
                    self.assertGreater(len(insns), 8,
                                       f"{name} disassembles to <=8 instructions "
                                       f"({len(insns)}): likely an empty stub")

    def test_04_data_symbols_have_nonzero_size(self):
        for lib, gaps in ((CLIENT, CLIENT_GAPS), (SERVER, SERVER_GAPS)):
            sized = subprocess.run(["nm", "-S", "--defined-only", str(lib)],
                                   capture_output=True, text=True,
                                   check=True).stdout
            sizes = {}
            for line in sized.splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    sizes[parts[-1]] = int(parts[1], 16)
            for name in gaps:
                if name not in DATA_GAPS:
                    continue
                sym = mangled(lib, name)
                self.assertIsNotNone(sym, f"no symbol for {name}")
                with self.subTest(lib=lib.name, symbol=name):
                    self.assertGreater(sizes.get(sym, 0), 0,
                                       f"{name} has zero size")

    def test_05_provenance_of_every_fixup_is_recorded(self):
        files = self.prov["files"]
        glue = set(self.prov["glue_files"])
        expected_glue = {
            "src/game/server/op4/op4_link_fixups.cpp",
            "src/game/server/op4/op4_ctf_player.cpp",
            "src/game/server/op4/op4_entity_enumerator.h",
            "src/game/shared/op4_weapon_timing.h",
            "src/game/shared/op4_weapon_timing.cpp",
        }
        self.assertTrue(expected_glue.issubset(glue))
        for rel in expected_glue:
            self.assertEqual(files[rel]["origin"], "this-repo", rel)
        # The CTF/rope bodies are real verbatim OP4 files, wired into CMake.
        wired = {s for s in self.prov["cmake"]["src/game/server/CMakeLists.txt"]}
        for rel in ("op4/dlls/ctf/CTFGoalFlag.cpp", "op4/dlls/rope/CRope.cpp",
                    "op4/dlls/ctf/CItemCTF.cpp"):
            self.assertIn(rel, wired, f"{rel} not wired into the BHL target")
            self.assertEqual(files["src/game/server/" + rel]["origin"], "op4")

    def test_06_bhl_changes_are_declared_and_reasoned(self):
        files = self.prov["files"]
        declared = {
            "src/game/server/game.cpp":
                ("op4-gamedllinit-decls", "op4-gamedllinit-call"),
            "src/game/shared/CMakeLists.txt":
                ("op4-shared-weapon-timing-cmake",),
              "src/game/server/weapons.h": ("op4-weapon-timing-state",),
              "src/game/server/cbase.h": ("op4-cworld-ctor-dtor",
                                         "op4-entity-eflags"),
              "src/game/server/gamerules.h": ("op4-gamerules-monster-hooks",
                                             "op4-gamerules-ctf-virtuals"),
              "src/game/server/gamerules.cpp": ("op4-install-gamerules-decls",
                                               "op4-install-gamerules-branch"),
              "src/game/server/monsters.h": ("op4-gibdata-spawn-overload",),
          }
        for rel, rules in declared.items():
            with self.subTest(file=rel):
                rec = files[rel]
                self.assertEqual(rec["origin"], "bugfixhl", rel)
                self.assertEqual(rec["action"], "bhl+op4-merge", rel)
                got = {r if isinstance(r, str) else r["rule"]
                       for r in rec.get("merge_rules", [])}
                for rule in rules:
                    self.assertIn(rule, got, f"{rel} missing declared rule {rule}")

    def test_07_real_upstream_bodies_back_the_fixups(self):
        """Key statements from the pinned OP4 sources must be present verbatim."""
        fixups = (ROOT / "bhl-op4/src/game/server/op4/op4_link_fixups.cpp").read_text()
        ctf = (ROOT / "bhl-op4/src/game/server/op4/dlls/ctf/ctfplay_gamerules.cpp").read_text()
        ctfh = (ROOT / "bhl-op4/src/game/server/op4/dlls/ctf/ctfplay_gamerules.h").read_text()
        ctfplayer = (ROOT / "bhl-op4/src/game/server/op4/op4_ctf_player.cpp").read_text()
        rules = (ROOT / "bhl-op4/src/game/server/gamerules.cpp").read_text()
        timing = (ROOT / "bhl-op4/src/game/shared/op4_weapon_timing.h").read_text()
        flag = (ROOT / "bhl-op4/src/game/server/op4/dlls/ctf/CTFGoalFlag.cpp").read_text()
        rope = (ROOT / "bhl-op4/src/game/server/op4/dlls/rope/CRope.cpp").read_text()
        probes = [
            (fixups, "m_flShockDuration += flShockDuration;",
             "OP4 monsters.cpp AddShockEffect"),
            (fixups, "World = this;", "OP4 world.cpp CWorld ctor"),
            (fixups, "CVAR_REGISTER(&oldgrapple);", "OP4 game.cpp registration"),
            (fixups, 'pfnRegUserMsg("FlagIcon", -1)',
             "OP4 UserMessages.cpp FlagIcon"),
            (ctf, "teamscores[teamIndex]", "real OP4 ctfplay_gamerules.cpp SendFlagIcon"),
            (ctf, "if (teamscores[1] < teamscores[0])",
             "real OP4 ctfplay_gamerules.cpp GetLosingTeam"),
            (ctfh, "bool IsCTF() override { return true; }", "OP4 CTF IsCTF override"),
            (ctfplayer, "bool CBasePlayer::Menu_Team_Input", "OP4 player.cpp menu"),
            (ctfplayer, "g_pGameRules->TeamsBalanced()", "OP4 menu team balancing"),
            (ctfplayer, "cvar_t ctf_capture", "OP4 game.cpp CTF cvars"),
            (ctfplayer, "void respawn(entvars_t* pev, bool fCopyCorpse)", "OP4 client.cpp respawn"),
            (rules, "return new CHalfLifeCTFplay();", "declared BHL InstallGameRules CTF"),
            (rules, "return new CHalfLifeCoopplay();", "declared BHL InstallGameRules coop"),
            (timing, "float flNextAttack = timeBase + delay - flCreep;",
             "OP4 weapons.cpp GetNextAttackDelay"),
            (timing, "state.prevPrimaryAttack = flNextAttack - timeBase;",
             "OP4 weapons.cpp GetNextAttackDelay"),
            (flag, "void CTFGoalFlag::DropFlag(CBasePlayer* pPlayer)",
             "real OP4 CTFGoalFlag.cpp"),
            (rope, "void CRope::DetachObject()", "real OP4 CRope.cpp"),
            (fixups, "if (DotProduct(forward, vecDir) > 0.96)",
             "OP4 h_ai.cpp IsFacing cone"),
            (fixups, "pGib->Spawn(gibData.ModelName);",
             "OP4 combat.cpp GibData gib spawning"),
            (fixups, "pLimitTracking[currentBody] >= gibData.Limits[currentBody].MaxGibs",
             "OP4 combat.cpp GibData submodel limits"),
        ]
        for text, needle, label in probes:
            with self.subTest(source=label):
                self.assertIn(needle, text, f"missing real OP4 statement: {needle}")

    def test_08_new_fixups_are_defined_with_real_bodies(self):
        """The two new gap closures must be real code, not undefined/stubs."""
        for name in NEW_SERVER_FIXUPS:
            with self.subTest(symbol=name):
                self.assertIn(name, self.server_def,
                              f"{name} is NOT defined in hl.so")
                self.assertNotIn(name, self.server_und,
                                 f"{name} is STILL UNDEFINED in hl.so")
        if shutil.which("objdump"):
            for name in NEW_SERVER_FIXUPS:
                sym = mangled(SERVER, name)
                self.assertIsNotNone(sym, f"no symbol for {name}")
                out = subprocess.run(
                    ["objdump", "-d", f"--disassemble={sym}", str(SERVER)],
                    capture_output=True, text=True, check=True).stdout
                insns = [ln for ln in out.splitlines()
                         if "\t" in ln and ln.split("\t")[0].strip().endswith(":")]
                with self.subTest(symbol=name):
                    self.assertGreater(len(insns), 8,
                                       f"{name} disassembles to <=8 instructions")

    def test_09_newly_wired_sources_are_real_op4_files(self):
        """The 7 additional wired files are verbatim OP4, not glue copies."""
        files = self.prov["files"]
        wired = set(self.prov["cmake"]["src/game/server/CMakeLists.txt"])
        for rel in NEW_WIRED_OP4:
            with self.subTest(source=rel):
                self.assertIn(rel, wired, f"{rel} not wired into the BHL target")
                rec = files["src/game/server/" + rel]
                self.assertEqual(rec["origin"], "op4", rel)
                self.assertIn(rec["action"],
                              ("verbatim", "op4+compat-patch"), rel)
                self.assertEqual(rec["upstream_path"],
                                 rel.removeprefix("op4/"), rel)


    def test_10_real_ctf_rules_are_wired_and_isctf_is_live(self):
        """The real OP4 CTF rules file must be wired, own its symbols once, and
        be reachable from InstallGameRules with a live IsCTF() override."""
        files = self.prov["files"]
        wired = set(self.prov["cmake"]["src/game/server/CMakeLists.txt"])
        rel = "op4/dlls/ctf/ctfplay_gamerules.cpp"
        self.assertIn(rel, wired, f"{rel} not wired into the server target")
        rec = files["src/game/server/" + rel]
        self.assertEqual(rec["origin"], "op4")
        self.assertIn(rec["action"], ("verbatim", "op4+compat-patch"))
        self.assertNotIn(rel, self.prov["port_pending"]["files"])

        ctf = (ROOT / "bhl-op4/src/game/server/op4/dlls/ctf/ctfplay_gamerules.cpp").read_text()
        ctf_h = (ROOT / "bhl-op4/src/game/server/op4/dlls/ctf/ctfplay_gamerules.h").read_text()
        rules = (ROOT / "bhl-op4/src/game/server/gamerules.cpp").read_text()
        head = (ROOT / "bhl-op4/src/game/server/gamerules.h").read_text()
        glue = (ROOT / "bhl-op4/src/game/server/op4/op4_link_fixups.cpp").read_text()
        player = (ROOT / "bhl-op4/src/game/server/op4/op4_ctf_player.cpp").read_text()

        self.assertIn("bool IsCTF() override { return true; }", ctf_h)
        self.assertIn("virtual bool IsCTF()", head)
        self.assertIn("return new CHalfLifeCTFplay();", rules)
        self.assertIn("return new CHalfLifeCoopplay();", rules)
        self.assertIn("SF_WORLD_CTF", rules)
        # Single ownership: these CTF bodies exist in the real file, not glue.
        for needle in ("void GetLosingTeam(int& iTeamNum, int& iScoreDiff)",
                       "void DisplayTeamFlags(CBasePlayer* pPlayer)"):
            self.assertIn(needle, ctf)
            self.assertNotIn(needle, glue)
        # Real OP4 CTF cvars/messages/menu bodies are present and registered.
        for needle in ("mp_ctfplay", "mp_coopplay", "mp_ctf_capture"):
            self.assertIn(needle, player)
        for needle in ("gmsgCTFScore", "gmsgSetMenuTeam", "gmsgTeamFull"):
            self.assertTrue(
                ("pfnRegUserMsg" in glue and needle in glue and needle in player),
                f"{needle} not defined AND registered")
        for needle in ("bool CBasePlayer::Menu_Team_Input(int inp)",
                       "void respawn(entvars_t* pev, bool fCopyCorpse)"):
            self.assertIn(needle, player)


if __name__ == "__main__":
    unittest.main()

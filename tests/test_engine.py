import json
import tempfile
import unittest
from pathlib import Path

from merge.engine import MergeEngine, MergeError
from merge.fetch import resolve_sources
from merge.manifest import Plan, Rule, load_plan, load_upstreams

ROOT = Path(__file__).resolve().parents[1]


def _rule(rid, action, path, **kwargs):
    raw = {"id": rid, "action": action, "path": path, **kwargs}
    return Rule(rid, action, path, raw)


class OfflineMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstreams = load_upstreams(ROOT)
        cls.plan = load_plan(ROOT)
        cls.sources = resolve_sources(ROOT, cls.upstreams, offline=True)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "merged"
        cls.report = MergeEngine(ROOT, cls.plan, cls.upstreams, cls.sources,
                                 "offline", cls.out, strict=True).run()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_summary_healthy(self):
        s = self.report["summary"]
        self.assertEqual(s["errors"], 0)
        self.assertEqual(s["missing"], 0)
        self.assertEqual(s["anchor_drift"], 0)
        self.assertGreater(s["injected"], 0)
        self.assertGreater(s["added"], 0)
        self.assertEqual(s["generated"], 2)
        self.assertEqual(s["patched"], 4)
        self.assertGreater(s["tree_files"], 25)
        self.assertEqual(len(self.report["files"]), s["rules"])

    def test_report_written_and_json_matches(self):
        on_disk = json.loads((self.out / "MERGE_REPORT.json").read_text())
        self.assertEqual(on_disk["tree_hash"], self.report["tree_hash"])
        self.assertTrue((self.out / "MERGE_REPORT.md").is_file())
        self.assertIn("Merge report", (self.out / "MERGE_REPORT.md").read_text())

    def test_tree_hash_is_deterministic(self):
        again = MergeEngine(ROOT, self.plan, self.upstreams, self.sources,
                            "offline", self.out, strict=True).run()
        self.assertEqual(again["tree_hash"], self.report["tree_hash"])

    def test_injects_are_on_their_own_lines(self):
        hud = (self.out / "cl_dll" / "hud.cpp").read_text()
        self.assertIn('#include "hud.h"\n#include "sr_hud_timer.h"\n', hud)
        self.assertNotIn('"hud.h"#include', hud)
        self.assertIn("void CHud::Init()\n{\n\t// BHL x OP4", hud)
        world = (self.out / "dlls" / "world.cpp").read_text()
        self.assertIn("SR_Server_OnMapSpawn(STRING(gpGlobals->mapname));", world)

    def test_op4_only_content_survives(self):
        self.assertTrue((self.out / "dlls" / "weapons" / "CDisplacer.cpp").is_file())
        self.assertIn("OP4: CTF flag icons", (self.out / "cl_dll" / "hud.cpp").read_text())

    def test_conflicts_quarantined_not_written_into_sources(self):
        self.assertEqual(len(self.report["conflicts"]), 1)
        conflict = self.report["conflicts"][0]
        self.assertEqual(conflict["path"], "pm_shared/pm_shared.cpp")
        quarantine = (self.out / conflict["quarantine"]).read_text()
        self.assertIn("<<<<<<<", quarantine)
        src = (self.out / "pm_shared" / "pm_shared.cpp").read_text()
        self.assertNotIn("<<<<<<<", src)
        self.assertIn("PM_Grapple_Update", src)

    def test_deferred_manual_ports_documented(self):
        self.assertEqual(len(self.report["manual_port"]), 2)
        for item in self.report["manual_port"]:
            self.assertTrue(item["reason"])
            self.assertGreater(item["blocks"], 0)

    def test_ported_gpl_files_are_quarantined_with_banner(self):
        ported = (self.out / "integration" / "ports" / "bhl_timer.cpp").read_text()
        self.assertIn("NOT", ported[:400])
        self.assertTrue((self.out / "integration" / "ports" / "README.md").is_file())

    def test_generated_config_and_route(self):
        self.assertIn('sv_cheats "0"', (self.out / "gamedir" / "speedrun.cfg").read_text())
        route = json.loads((self.out / "gamedir" / "splits" / "op4_route.json").read_text())
        self.assertEqual(len(route["chapters"]), 13)

    def test_build_files_patched(self):
        vcx = (self.out / "projects" / "vs2019" / "hl_cdll.vcxproj").read_text()
        self.assertIn("sr_hud_timer.cpp", vcx)
        self.assertIn("sr_core.cpp", vcx)
        mk = (self.out / "linux" / "Makefile.hldll").read_text()
        self.assertIn("sr_server.o", mk)


class ConflictPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        (base / "ours").mkdir()
        (base / "base").mkdir()
        (base / "donor").mkdir()
        (base / "ours" / "f.txt").write_text("line one\nCONFLICT OP4\nline three\n")
        (base / "base" / "f.txt").write_text("line one\nCONFLICT VANILLA\nline three\n")
        (base / "donor" / "f.txt").write_text("line one\nCONFLICT BUGFIXHL\nline three\n")
        self.sources = {"target": base / "ours", "base": base / "base",
                        "donor": base / "donor", "repo": ROOT, "overlay": ROOT / "overlay"}
        self.out = base / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, policy, quarantine=None):
        raw = {"id": "tw", "action": "three_way", "path": "f.txt",
               "base": "base:f.txt", "ours": "target:f.txt", "theirs": "donor:f.txt",
               "on_conflict": policy}
        if quarantine:
            raw["quarantine"] = quarantine
        plan = Plan("t", "target", "", (_rule("tw", "three_way", "f.txt", **{k: v for k, v in raw.items() if k not in ("id", "action", "path")}),), {})
        return MergeEngine(ROOT, plan, {}, self.sources, "offline", self.out).run()

    def test_marker_policy_quarantines(self):
        report = self._run("marker", "conflicts/f.txt.diff3")
        self.assertEqual(report["files"][0]["status"], "conflict")
        self.assertIn("<<<<<<<", (self.out / "conflicts" / "f.txt.diff3").read_text())
        self.assertNotIn("<<<<<<<", (self.out / "f.txt").read_text())

    def test_ours_policy_defers(self):
        report = self._run("ours")
        self.assertEqual(report["files"][0]["status"], "deferred")
        self.assertEqual(len(report["manual_port"]), 1)
        self.assertIn("CONFLICT OP4", (self.out / "f.txt").read_text())

    def test_theirs_policy(self):
        report = self._run("theirs")
        self.assertEqual(report["files"][0]["status"], "donor")
        self.assertIn("CONFLICT BUGFIXHL", (self.out / "f.txt").read_text())

    def test_fail_policy_records_error(self):
        report = self._run("fail")
        self.assertEqual(report["files"][0]["status"], "error")
        self.assertEqual(report["summary"]["errors"], 1)

    def test_strict_fails_on_anchor_drift(self):
        plan = Plan("t", "target", "", (
            _rule("inj", "inject", "f.txt", anchor="NOT THERE",
                  snippet="repo:integration/snippets/hud_include.snippet"),
        ), {})
        with self.assertRaises(MergeError):
            MergeEngine(ROOT, plan, {}, self.sources, "offline", self.out, strict=True).run()


if __name__ == "__main__":
    unittest.main()

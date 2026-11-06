import tempfile
import unittest
from pathlib import Path

from merge.engine import MergeEngine
from merge.manifest import Plan, Rule, validate_plan, load_upstreams, load_plan

ROOT = Path(__file__).resolve().parents[1]


def audit_plan(expect):
    raw = {"id": "a", "action": "audit", "path": "f.cpp", "expect": expect,
           "feature": "test", "evidence": "test evidence"}
    rule = Rule("a", "audit", "f.cpp", raw)
    return Plan("t", "target", "", (rule,), {})


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        (base / "sdk").mkdir()
        (base / "sdk" / "f.cpp").write_text(
            "#define FACTOR 2\nvoid Cap() { FACTOR; }\n// guard present\n"
        )
        self.sources = {"target": base / "sdk", "repo": ROOT, "overlay": ROOT / "overlay"}
        self.out = base / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def test_all_equivalences_found(self):
        plan = audit_plan([
            {"meaning": "factor", "pattern": "FACTOR", "min": 2},
            {"meaning": "cap fn", "pattern": "void Cap()"},
            {"meaning": "guard", "pattern": "guard present"},
        ])
        report = MergeEngine(ROOT, plan, {}, self.sources, "offline", self.out, strict=True).run()
        self.assertEqual(report["files"][0]["status"], "audited")
        self.assertEqual(report["summary"]["audited"], 1)
        self.assertEqual(report["audits"][0]["verdict"], "equivalent")
        self.assertEqual(report["warnings"], [])

    def test_regex_expectation(self):
        plan = audit_plan([{"meaning": "cap fn", "pattern": r"void\s+Cap\s*\(\)", "regex": True}])
        report = MergeEngine(ROOT, plan, {}, self.sources, "offline", self.out).run()
        self.assertEqual(report["audits"][0]["checks"][0]["found"], 1)

    def test_missing_equivalence_is_reported_not_hidden(self):
        plan = audit_plan([{"meaning": "missing", "pattern": "DOES_NOT_EXIST"}])
        report = MergeEngine(ROOT, plan, {}, self.sources, "offline", self.out).run()
        self.assertEqual(report["files"][0]["status"], "anchor_drift")
        self.assertEqual(report["audits"][0]["verdict"], "missing")
        self.assertTrue(any("missing equivalences" in w for w in report["warnings"]))

    def test_invalid_regex_rejected_by_manifest_validation(self):
        plan = audit_plan([{"meaning": "broken", "pattern": "[", "regex": True}])
        errors = validate_plan(plan, load_upstreams(ROOT))
        self.assertTrue(any("invalid regex" in e for e in errors))

    def test_shipped_plan_audits_are_three(self):
        plan = load_plan(ROOT)
        self.assertEqual(sum(1 for r in plan.rules if r.action == "audit"), 3)
        self.assertEqual(validate_plan(plan, load_upstreams(ROOT)), [])


if __name__ == "__main__":
    unittest.main()

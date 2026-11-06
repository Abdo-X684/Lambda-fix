import copy
import json
import unittest
from pathlib import Path

from merge.manifest import (
    ManifestError,
    Plan,
    Rule,
    load_plan,
    load_upstreams,
    split_spec,
    validate_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstreams = load_upstreams(ROOT)
        cls.plan = load_plan(ROOT)

    def test_pins_are_full_shas_with_checksums(self):
        self.assertEqual(set(self.upstreams), {"op4", "bugfixhl", "valve_hlsdk"})
        for u in self.upstreams.values():
            self.assertEqual(len(u.ref), 40)
            self.assertEqual(len(u.tarball["sha256"]), 64)
            self.assertTrue(u.tarball["url"].startswith("https://codeload.github.com/"))

    def test_shipped_plan_is_valid(self):
        self.assertEqual(validate_plan(self.plan, self.upstreams), [])
        self.assertEqual(self.plan.target, "op4")
        self.assertGreaterEqual(len(self.plan.rules), 20)

    def test_rule_ids_unique(self):
        ids = [r.id for r in self.plan.rules]
        self.assertEqual(len(ids), len(set(ids)))

    def test_validation_catches_bad_rules(self):
        raw = json.loads((ROOT / "merge" / "plan.json").read_text())
        raw["rules"].append({"id": "bad", "action": "explode", "path": "x.cpp"})
        raw["rules"].append({"id": "traversal", "action": "skip", "path": "../escape.cpp"})
        raw["rules"].append({"id": "unknown-source", "action": "copy",
                             "path": "x.cpp", "from": "nope:file.cpp"})
        plan = Plan(name="t", target="op4", description="",
                    rules=tuple(Rule(id=r["id"], action=r["action"], path=r["path"], raw=r)
                                for r in raw["rules"]), raw=raw)
        errors = validate_plan(plan, self.upstreams)
        self.assertGreaterEqual(len(errors), 3)
        self.assertTrue(any("unknown action" in e for e in errors))
        self.assertTrue(any("safe relative" in e for e in errors))
        self.assertTrue(any("not a known upstream" in e for e in errors))

    def test_three_way_requires_all_inputs_and_valid_policy(self):
        raw = {"id": "tw", "action": "three_way", "path": "a.cpp", "ours": "op4:a.cpp"}
        plan = Plan("t", "op4", "", (Rule("tw", "three_way", "a.cpp", raw),), {})
        errors = validate_plan(plan, self.upstreams)
        self.assertTrue(any("needs 'base'" in e for e in errors))
        self.assertTrue(any("needs 'theirs'" in e for e in errors))
        raw2 = dict(raw, base="valve_hlsdk:a.cpp", theirs="bugfixhl:a.cpp", on_conflict="magic")
        plan2 = Plan("t", "op4", "", (Rule("tw", "three_way", "a.cpp", raw2),), {})
        self.assertTrue(any("bad on_conflict" in e for e in validate_plan(plan2, self.upstreams)))

    def test_split_spec(self):
        self.assertEqual(split_spec("repo:data/x.json"), ("repo", "data/x.json"))
        with self.assertRaises(ManifestError):
            split_spec("noseparator")

    def test_missing_file_raises(self):
        with self.assertRaises(ManifestError):
            load_upstreams(ROOT / "does-not-exist")


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from merge.configgen import (
    load_route,
    render_config,
    route_maps,
    validate_route,
    write_config,
)

ROOT = Path(__file__).resolve().parents[1]


class ConfigGenTests(unittest.TestCase):
    def test_shipped_route_is_valid(self):
        self.assertEqual(validate_route(ROOT), [])
        route = load_route(ROOT)
        self.assertEqual(len(route["chapters"]), 13)
        self.assertEqual(len(route_maps(route)), 39)
        self.assertEqual(len(route_maps(route, include_boot_camp=True)), 44)

    def test_render_config_is_deterministic_and_legal(self):
        cfg = render_config(ROOT)
        self.assertEqual(cfg, render_config(ROOT))
        self.assertIn('sv_cheats "0"', cfg)
        self.assertNotIn('sv_cheats "1"', cfg)
        for cvar in json.loads((ROOT / "data" / "cvars.json").read_text())["cvars"]:
            self.assertIn(f'{cvar["name"]} "', cfg)
        for chapter in load_route(ROOT)["chapters"]:
            self.assertIn(chapter["name"], cfg)
            self.assertIn(chapter["maps"][0], cfg)
        self.assertIn('bind "F6" "sr_split_now"', cfg)

    def test_write_config(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "nested" / "speedrun.cfg"
            text = write_config(ROOT, out)
            self.assertEqual(out.read_text(), text)
            self.assertTrue(out.is_file())

    def test_duplicate_map_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "data").mkdir()
            route = load_route(ROOT)
            route["chapters"][2]["maps"].append("of1a1")
            (tmp / "data" / "op4_route.json").write_text(json.dumps(route))
            (tmp / "data" / "cvars.json").write_text((ROOT / "data" / "cvars.json").read_text())
            problems = validate_route(tmp)
            self.assertTrue(any("appears twice" in p for p in problems))


if __name__ == "__main__":
    unittest.main()

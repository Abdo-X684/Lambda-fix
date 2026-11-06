import unittest
from pathlib import Path

from merge.configgen import load_route, route_maps
from tools.gen_route_header import check_header, expected_header

ROOT = Path(__file__).resolve().parents[1]


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.route = load_route(ROOT)
        self.header = (ROOT / "src" / "speedrun" / "sr_route_data.h").read_text()

    def test_generated_header_in_sync(self):
        self.assertEqual(check_header(ROOT), [])
        self.assertEqual(self.header, expected_header(ROOT))

    def test_every_map_in_header(self):
        for name in route_maps(self.route, include_boot_camp=True):
            with self.subTest(name=name):
                self.assertIn(f'"{name}"', self.header)

    def test_counts_in_header(self):
        self.assertIn("kChapterCount = 13", self.header)
        self.assertIn("kBootCampMapCount = 5", self.header)

    def test_chapter_order_and_ids(self):
        ids = [c["id"] for c in self.route["chapters"]]
        self.assertEqual(ids, [f"ch{i:02d}" for i in range(13)])
        self.assertEqual(self.route["chapters"][0]["maps"], ["of0a0"])
        self.assertEqual(self.route["chapters"][-1]["maps"], ["of7a0"])

    def test_boot_camp_is_a_separate_category(self):
        boot = set(self.route["boot_camp"]["maps"])
        self.assertFalse(boot & set(route_maps(self.route)))
        self.assertIn("speedrun.com", self.route["boot_camp"]["note"])


if __name__ == "__main__":
    unittest.main()

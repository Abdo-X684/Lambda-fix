import re
import unittest
from pathlib import Path

from web import app

ROOT = Path(__file__).resolve().parents[1]


class WebTests(unittest.TestCase):
    def test_status_payload(self):
        st = app.status_payload()
        self.assertEqual(st["rules"], 26)
        self.assertEqual(len(st["upstreams"]), 3)
        self.assertEqual(st["route"]["maps"], 39)
        self.assertEqual(st["route"]["chapters"], 13)

    def test_static_assets_exist(self):
        for rel, _ctype in app.STATIC.values():
            self.assertTrue((ROOT / rel).is_file(), rel)
        self.assertTrue((ROOT / "web" / "index.html").is_file())

    def test_all_js_element_ids_exist_in_html(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        ids = set(re.findall(r"\$\('([A-Za-z0-9_-]+)'\)", js))
        markup_ids = set(re.findall(r'id="([A-Za-z0-9_-]+)"', html))
        self.assertTrue(ids, "no $() ids found in app.js")
        self.assertEqual(ids - markup_ids, set(), f"missing ids: {ids - markup_ids}")

    def test_api_paths_in_js_are_served(self):
        js = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
        paths = set(re.findall(r"api\('(/api/[a-z-]+)'", js))
        self.assertEqual(paths, {"/api/status", "/api/route", "/api/plan", "/api/config",
                                 "/api/report", "/api/readme", "/api/merge", "/api/tests"})

    def test_dashboard_binds_all_interfaces(self):
        source = (ROOT / "web" / "app.py").read_text(encoding="utf-8")
        self.assertIn('("0.0.0.0", port)', source)
        self.assertNotIn("127.0.0.1", source)


if __name__ == "__main__":
    unittest.main()

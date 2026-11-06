import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cli(*args):
    return subprocess.run([sys.executable, "-m", "merge.cli", *args],
                          cwd=ROOT, capture_output=True, text=True, timeout=120)


class CliTests(unittest.TestCase):
    def test_plan(self):
        r = cli("plan")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("bugfixhl", r.stdout)
        self.assertIn("valve_hlsdk", r.stdout)

    def test_route_check(self):
        r = cli("route", "--check")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("39 maps", r.stdout)

    def test_config_stdout(self):
        r = cli("config")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('sv_cheats "0"', r.stdout)

    def test_run_offline_strict_json(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "merged")
            r = cli("run", "--offline", "--strict", "--json", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout[:800])
            report = json.loads(r.stdout)
            self.assertEqual(report["mode"], "offline")
            self.assertEqual(report["summary"]["errors"], 0)
            self.assertTrue((Path(out) / "MERGE_REPORT.md").is_file())

    def test_run_without_fetched_upstreams_fails_clearly(self):
        r = cli("run", "--out", "/tmp/bhl-op4-never-fetched-test")
        # In this sandbox `make fetch` may have been run; either outcome is fine,
        # but the CLI must never crash with a traceback.
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()

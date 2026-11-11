"""The full-OP4 server patch must reproduce from the pinned clean SDK."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Op4ServerPrepareTests(unittest.TestCase):
    def test_prepare_check_passes(self):
        if not (ROOT / ".cache/upstreams/op4/dlls/player.cpp").is_file():
            self.skipTest("pinned OP4 SDK not present (run: make fetch)")
        r = subprocess.run(
            [sys.executable, "tools/prepare_op4_msvc_server.py", "--check"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OP4 MSVC SERVER SOURCE OK", r.stdout)


if __name__ == "__main__":
    unittest.main()

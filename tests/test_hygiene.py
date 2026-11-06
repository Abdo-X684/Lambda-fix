import unittest
from pathlib import Path

from tools.check_hygiene import check

ROOT = Path(__file__).resolve().parents[1]


class HygieneTests(unittest.TestCase):
    def test_repository_is_clean(self):
        self.assertEqual(check(ROOT), [])

    def test_broken_link_is_detected(self):
        # The checker must actually fail on a broken local markdown link.
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            for rel in ("upstreams.json", ".gitignore", "docs", "tests/fixtures/upstreams"):
                src, dst = ROOT / rel, tmp / rel
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            (tmp / "docs" / "BROKEN.md").write_text("[bad](nope.md)\n")
            issues = check(tmp)
            self.assertTrue(any("broken link" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from tools.check_hygiene import check

ROOT = Path(__file__).resolve().parents[1]


class HygieneTests(unittest.TestCase):
    def test_repository_is_clean(self):
        self.assertEqual(check(ROOT), [])

    def test_site_absolute_links_are_not_treated_as_files(self):
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            shutil.copy2(ROOT / "upstreams.json", tmp / "upstreams.json")
            shutil.copy2(ROOT / ".gitignore", tmp / ".gitignore")
            shutil.copytree(ROOT / "docs", tmp / "docs")
            (tmp / "docs" / "LINKS.md").write_text("[dl](/dist/dlls/client.so)\n")
            (tmp / "docs" / "README.md").write_text(
                (tmp / "docs" / "README.md").read_text(encoding="utf-8")
                + "\n[LINKS.md](LINKS.md)\n")
            issues = check(tmp)
            self.assertFalse(any("dist/dlls" in i for i in issues), issues)

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

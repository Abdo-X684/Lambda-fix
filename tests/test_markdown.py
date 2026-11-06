import unittest
from pathlib import Path

from web.markdown import DocumentStore, render_markdown

ROOT = Path(__file__).resolve().parents[1]


class MarkdownRendererTests(unittest.TestCase):
    def test_html_is_escaped(self):
        r = render_markdown("<script>alert(1)</script>\n\n**bold** and `code`")
        self.assertNotIn("<script>", r.html)
        self.assertIn("&lt;script&gt;", r.html)
        self.assertIn("<strong>bold</strong>", r.html)
        self.assertIn("<code>code</code>", r.html)

    def test_unsafe_url_never_becomes_a_link(self):
        r = render_markdown("[click](javascript:alert) [x](data:text/html,hi)")
        self.assertNotIn("<a ", r.html)
        self.assertIn("doc-missing", r.html)

    def test_external_and_internal_links(self):
        r = render_markdown(
            "[site](https://example.com) [doc](docs/RESOLUTION.md)",
            known_docs=frozenset({"docs/RESOLUTION.md"}),
        )
        self.assertIn('target="_blank"', r.html)
        self.assertIn('rel="noopener noreferrer"', r.html)
        self.assertIn('data-doc="docs/RESOLUTION.md"', r.html)

    def test_site_absolute_download_link_stays_clickable(self):
        r = render_markdown("[download](/dist/dlls/client.so)")
        self.assertIn('href="/dist/dlls/client.so"', r.html)
        self.assertNotIn("doc-missing", r.html)

    def test_code_span_inside_link_label_stays_intact(self):
        r = render_markdown("[`x`](docs/README.md)",
                            known_docs=frozenset({"docs/README.md"}))
        self.assertIn("<code>x</code>", r.html)
        self.assertIn('data-doc="docs/README.md"', r.html)

    def test_headings_toc_and_duplicate_slugs(self):
        r = render_markdown("# العنوان\n\n## بند\n\n## بند\n\n### تفصيل")
        self.assertEqual(len(r.toc), 4)
        self.assertIn('id="العنوان"', r.html)
        self.assertIn('id="بند"', r.html)
        self.assertIn('id="بند-2"', r.html)
        self.assertEqual(r.toc[0]["level"], 1)

    def test_tables_lists_quotes_and_fences(self):
        md = ("| أ | ب |\n| --- | ---: |\n| 1 | 2 |\n\n"
              "- أول\n- ثانٍ\n\n> ملاحظة\n\n```bash\nmake verify\n```")
        r = render_markdown(md)
        self.assertIn("<table>", r.html)
        self.assertIn("text-align: right", r.html)
        self.assertIn("<ul>", r.html)
        self.assertIn("<blockquote>", r.html)
        self.assertIn('class="language-bash"', r.html)
        self.assertIn("make verify", r.html)

    def test_relative_links_resolve_from_the_doc_directory(self):
        html = render_markdown("[r](../README.md)", current="docs/README.md",
                               known_docs=frozenset({"README.md"})).html
        self.assertIn('data-doc="README.md"', html)


class DocumentStoreTests(unittest.TestCase):
    def test_index_and_whitelist(self):
        store = DocumentStore(ROOT)
        names = [d["name"] for d in store.index()]
        self.assertIn("README.md", names)
        self.assertIn("CONTRIBUTING.md", names)
        self.assertIn("docs/RESOLUTION.md", names)
        self.assertTrue(all(d["title"] for d in store.index()))
        self.assertIsNone(store.get("../upstreams.json"))
        self.assertIsNone(store.get("missing.md"))

    def test_readme_is_fully_rendered(self):
        doc = DocumentStore(ROOT).get("README.md")
        self.assertTrue(doc["title"])
        self.assertIn("<table", doc["html"])
        self.assertGreaterEqual(len(doc["toc"]), 8)
        self.assertNotIn("<script", doc["html"])
        self.assertNotIn('href="javascript:', doc["html"])
        for item in doc["toc"]:
            self.assertIn(f'id="{item["id"]}"', doc["html"])

    def test_every_document_renders(self):
        store = DocumentStore(ROOT)
        for entry in store.index():
            with self.subTest(doc=entry["name"]):
                doc = store.get(entry["name"])
                self.assertIsNotNone(doc)
                self.assertTrue(doc["html"].strip())
                self.assertIn("<", doc["html"])


if __name__ == "__main__":
    unittest.main()

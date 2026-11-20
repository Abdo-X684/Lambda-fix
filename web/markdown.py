"""Tiny, dependency-free Markdown renderer for the dashboard's README page.

Only the subset used by this repository's docs is supported (headings, fenced
code, tables, lists, quotes, rules, bold/italic, inline code and links). All
text is HTML-escaped first; relative `.md` links become in-app doc links and
anything else (including `javascript:` URLs) is never emitted as a link.
"""

from __future__ import annotations

import html
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*```([\w+-]*)\s*$")
RULE_RE = re.compile(r"^\s*(?:-{3,}|\*{3,})\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$")
UL_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
OL_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
CODE_SPAN_RE = re.compile(r"(`[^`]+`)")


@dataclass
class Rendered:
    html: str
    toc: list[dict]


def _plain(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _slug(text: str, counts: dict) -> str:
    base = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE).strip()
    base = re.sub(r"\s+", "-", base) or "section"
    counts[base] = counts.get(base, 0) + 1
    return base if counts[base] == 1 else f"{base}-{counts[base]}"


def _link(match: re.Match, current: str, known: frozenset) -> str:
    label, raw_url = match.group(1), html.unescape(match.group(2))
    url = html.escape(raw_url, quote=True)
    if raw_url.startswith("#"):
        return f'<a href="{url}">{label}</a>'
    if raw_url.startswith("/"):
        return f'<a href="{url}">{label}</a>'
    if raw_url.startswith(("http://", "https://", "mailto:")):
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
    base, _, frag = raw_url.partition("#")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(current), base))
    if resolved in known:
        return (
            f'<a class="doc-link" href="#docs/{html.escape(resolved, quote=True)}" '
            f'data-doc="{html.escape(resolved, quote=True)}">{label}</a>'
        )
    return f'<span class="doc-missing" title="file is outside the docs folder">{label}</span>'


def _inline(text: str, current: str, known: frozenset) -> str:
    escaped = html.escape(text, quote=True)
    codes: list[str] = []

    def stash(match: re.Match) -> str:
        codes.append(f"<code>{match.group(1)[1:-1]}</code>")
        return f"\x00C{len(codes) - 1}\x00"

    # Stash code spans first so a link like [`code`](doc.md) stays intact and
    # nothing inside the code is ever reformatted.
    escaped = CODE_SPAN_RE.sub(stash, escaped)
    escaped = LINK_RE.sub(lambda m: _link(m, current, known), escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", escaped)
    for i, code in enumerate(codes):
        escaped = escaped.replace(f"\x00C{i}\x00", code)
    return escaped


def _cells(line: str) -> list[str]:
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return parts


def _aligns(line: str) -> list[str]:
    result = []
    for cell in _cells(line):
        left, right = cell.startswith(":"), cell.endswith(":")
        result.append("center" if left and right else "right" if right else "left" if left else "")
    return result


def _table(header, aligns, rows, current, known) -> str:
    def row(cells, tag="td"):
        rendered = []
        for i, cell in enumerate(cells):
            align = aligns[i] if i < len(aligns) else ""
            style = f' style="text-align: {align}"' if align else ""
            rendered.append(f"<{tag}{style}>{_inline(cell, current, known)}</{tag}>")
        return "<tr>" + "".join(rendered) + "</tr>"

    body = "".join(row(r) for r in rows)
    return (
        '<div class="table-wrap"><table><thead>'
        + row(header, "th")
        + "</thead><tbody>"
        + body
        + "</tbody></table></div>"
    )


def render_markdown(text: str, current: str = "README.md",
                    known_docs: frozenset = frozenset()) -> Rendered:
    """Return safe HTML plus a table of contents for the given Markdown."""
    known = frozenset(known_docs)
    lines = text.splitlines()
    out: list[str] = []
    toc: list[dict] = []
    counts: dict = {}
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append("<p>" + "<br>".join(_inline(line, current, known) for line in paragraph) + "</p>")
            paragraph.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush_paragraph()
            i += 1
            continue
        fence = FENCE_RE.match(line)
        if fence:
            flush_paragraph()
            lang = html.escape(fence.group(1), quote=True)
            i += 1
            code = []
            while i < len(lines) and not FENCE_RE.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence (or EOF)
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f'<pre class="md-code"><code{cls}>{html.escape(chr(10).join(code))}</code></pre>')
            continue
        heading = HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            level, raw = len(heading.group(1)), heading.group(2).strip()
            title = _plain(_inline(raw, current, known))
            slug = _slug(title, counts)
            out.append(f'<h{level} id="{html.escape(slug, quote=True)}">'
                       f'{_inline(raw, current, known)}</h{level}>')
            if level <= 3:
                toc.append({"level": level, "text": title, "id": slug})
            i += 1
            continue
        if RULE_RE.match(line):
            flush_paragraph()
            out.append("<hr>")
            i += 1
            continue
        if line.lstrip().startswith(">"):
            flush_paragraph()
            quote = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append("<blockquote>" + "<br>".join(
                _inline(q, current, known) for q in quote) + "</blockquote>")
            continue
        if "|" in line and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1]):
            flush_paragraph()
            header = _cells(line)
            aligns = _aligns(lines[i + 1])
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            out.append(_table(header, aligns, rows, current, known))
            continue
        ordered = bool(OL_RE.match(line))
        if ordered or UL_RE.match(line):
            flush_paragraph()
            items = []
            while i < len(lines):
                match = (OL_RE if ordered else UL_RE).match(lines[i])
                if not match:
                    break
                items.append(match.group(1))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(
                f"<li>{_inline(item, current, known)}</li>" for item in items) + f"</{tag}>")
            continue
        paragraph.append(line.strip())
        i += 1
    flush_paragraph()
    return Rendered("\n".join(out), toc)


def first_heading(text: str) -> str:
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return _plain(_inline(match.group(2).strip(), "README.md", frozenset()))
    return ""


class DocumentStore:
    """Whitelisted, read-only view of the repository docs for the UI."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.docs: dict[str, Path] = {}
        for name in ("README.md", "CONTRIBUTING.md"):
            path = self.root / name
            if path.is_file():
                self.docs[name] = path
        for path in sorted((self.root / "docs").glob("*.md")):
            self.docs[f"docs/{path.name}"] = path
        fixtures = self.root / "tests" / "fixtures" / "README.md"
        if fixtures.is_file():
            self.docs["tests/fixtures/README.md"] = fixtures

    def index(self) -> list[dict]:
        entries = []
        for name, path in self.docs.items():
            text = path.read_text(encoding="utf-8")
            group = "docs" if name.startswith("docs/") else (
                "fixtures" if name.startswith("tests/") else "root")
            entries.append({
                "name": name,
                "title": first_heading(text) or name,
                "group": group,
                "bytes": len(text.encode("utf-8")),
            })
        return entries

    def get(self, name: str) -> dict | None:
        path = self.docs.get(name)
        if path is None or not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
        rendered = render_markdown(text, name, frozenset(self.docs))
        return {
            "name": name,
            "title": first_heading(text) or name,
            "html": rendered.html,
            "toc": rendered.toc,
            "markdown": text,
            "bytes": len(text.encode("utf-8")),
        }

#!/usr/bin/env python3
"""Repository hygiene checker (stdlib only).

Keeps the tidy-up durable: whitespace, encodings, JSON, Python syntax, dead
imports, local markdown links, the docs index, fixture directories and
.gitignore coverage. `make hygiene` and `tests/test_hygiene.py` run this.
"""

from __future__ import annotations

import ast
import codecs
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# bhl-op4/ is the verbatim, checksum-tracked upstream tree. Its whitespace is
# upstream's own and must not be "tidied" (that would break PROVENANCE.json).
# Its integrity is checked by tests/test_bhl_base.py and merge.bhl_base --check.
SKIP_DIRS = {"build", ".cache", "dist", ".git", "__pycache__", "CMakeFiles",
             "bhl-op4"}
TEXT_SUFFIXES = {
    ".py", ".md", ".json", ".cpp", ".h", ".js", ".css", ".html",
    ".yml", ".yaml", ".snippet", ".txt", ".cfg",
}
TEXT_NAMES = {"Makefile", "CMakeLists.txt", ".gitignore", "LICENSE", "README"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES:
            # VGUI2 localisation files are UTF-16LE BOM by design; the LF/UTF-8
            # text checks below must not treat their null bytes as source text.
            with path.open("rb") as f:
                if f.read(2) == codecs.BOM_UTF16_LE:
                    continue
            yield path


def _unused_imports(path: Path, text: str) -> list[str]:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []  # reported by the syntax check
    imported: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported[alias.asname or alias.name.split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for alias in node.names:
                if alias.name != "*":
                    imported[alias.asname or alias.name] = node.lineno

    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            value = node.value
            while isinstance(value, ast.Attribute):
                value = value.value
            if isinstance(value, ast.Name):
                used.add(value.id)
    # Public re-exports in __init__.py are intentional.
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                for element in node.value.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        used.add(element.value)
    return [f"{name} (line {line})" for name, line in imported.items() if name not in used]


def check(root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    files = list(iter_text_files(root))

    for path in files:
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        if b"\r\n" in data:
            issues.append(f"{rel}: CRLF line endings (use LF)")
        if data and not data.endswith(b"\n"):
            issues.append(f"{rel}: missing final newline")
        for number, line in enumerate(data.splitlines(), 1):
            if line.rstrip(b" \t") != line:
                issues.append(f"{rel}: trailing whitespace on line {number}")
        if path.suffix == ".json":
            try:
                json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                issues.append(f"{rel}: invalid JSON: {exc}")
        if path.suffix == ".py":
            text = data.decode("utf-8")
            try:
                compile(text, rel, "exec")
            except SyntaxError as exc:
                issues.append(f"{rel}: syntax error: {exc}")
            for name in _unused_imports(path, text):
                issues.append(f"{rel}: unused import {name}")

    # Local markdown links must resolve.
    for path in files:
        if path.suffix != ".md":
            continue
        for match in LINK_RE.finditer(path.read_text(encoding="utf-8")):
            target = match.group(1).split("#")[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "/")):
                continue
            if not (path.parent / target).resolve().exists():
                issues.append(
                    f"{path.relative_to(root).as_posix()}: broken link -> {target}"
                )

    # Every doc must be listed in the docs index.
    docs = root / "docs"
    index = docs / "README.md"
    if not index.is_file():
        issues.append("docs/README.md: missing docs index")
    else:
        index_text = index.read_text(encoding="utf-8")
        for doc in sorted(docs.glob("*.md")):
            if doc.name != "README.md" and doc.name not in index_text:
                issues.append(f"docs/README.md: missing link to {doc.name}")

    # Offline fixtures must exist for every pinned upstream.
    upstreams = json.loads((root / "upstreams.json").read_text(encoding="utf-8"))
    for upstream in upstreams["upstreams"]:
        fixture = root / "tests" / "fixtures" / "upstreams" / upstream["name"]
        if not fixture.is_dir():
            issues.append(f"tests/fixtures/upstreams/{upstream['name']}: missing fixture dir")

    ignore = (root / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("/build/", "/dist/", "/.cache/", "__pycache__/"):
        if pattern not in ignore:
            issues.append(f".gitignore: missing {pattern}")
    return issues


def main() -> int:
    issues = check()
    if issues:
        for issue in issues:
            print(f"  ! {issue}", file=sys.stderr)
        print(f"hygiene: {len(issues)} issue(s)", file=sys.stderr)
        return 1
    print(f"hygiene: OK ({len(list(iter_text_files(ROOT)))} text files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

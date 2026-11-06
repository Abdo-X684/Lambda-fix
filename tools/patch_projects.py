#!/usr/bin/env python3
"""CLI wrapper around :mod:`merge.projects` for a merged SDK tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge.projects import (  # noqa: E402
    BUILD_FILES,
    patch_makefile,
    patch_tree,
    patch_vcxproj,
    read_text,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd(), help="merged SDK tree")
    p.add_argument("--check", action="store_true", help="report without writing")
    args = p.parse_args(argv)
    if args.check:
        changed = []
        for rel, kind, payload in BUILD_FILES:
            path = args.root / rel
            if not path.is_file():
                continue
            text = read_text(path)
            if kind == "vcxproj":
                new, added = patch_vcxproj(text, payload)
            else:
                obj_var, sources = payload
                new, added = patch_makefile(text, obj_var, sources)
            if new != text:
                changed.append((rel, added))
        for rel, added in changed:
            print(f"would patch {rel}: {', '.join(added)}")
        print(f"{len(changed)} build file(s) need patching")
        return 1 if changed else 0
    for change in patch_tree(args.root):
        print(f"{change['file']}: {', '.join(change['added']) or 'already up to date'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

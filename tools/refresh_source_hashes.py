#!/usr/bin/env python3
"""Refresh a build-evidence SOURCES.sha256 after regenerating bhl-op4/.

The Windows MSVC workflow publishes its DLLs from CI; its source list is the
same checked-in tree. This tool recomputes hashes for existing entries so
``tools/weapon_inventory.py --check`` does not mistake a source regeneration
for a stale build. Missing pinned ``.cache/`` dependencies are left alone:
``source_hashes()`` already skips them explicitly.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def refresh(path: Path) -> int:
    lines = path.read_text().splitlines()
    out: list[str] = []
    changed = 0
    for line in lines:
        if not line.strip():
            continue
        old, name = line.split("  ", 1)
        p = Path(name)
        if not p.is_absolute():
            p = ROOT / p
        if not p.is_file():
            if ".cache/" not in name:
                raise SystemExit(f"missing source for {name}")
            out.append(f"{old}  {name}")
            continue
        new = hashlib.sha256(p.read_bytes()).hexdigest()
        if new != old:
            changed += 1
        out.append(f"{new}  {name}")
    path.write_text("\n".join(out) + "\n")
    print(f"refreshed {changed}/{len(out)} hashes in {path.relative_to(ROOT)}")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    a = ap.parse_args()
    p = a.path if a.path.is_absolute() else ROOT / a.path
    refresh(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

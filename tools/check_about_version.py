#!/usr/bin/env python3
"""Fail if the About-page version does not match the newest package version.

The About page prints LF_VERSION from bhl-op4/src/common/appversion.h.in
verbatim (options_about.cpp: "%d.%d.%d" from APP_VERSION). That line is a
literal, not derived from git tags, so it silently goes stale whenever a
package is cut without bumping it. Releases 1.0.6 through 1.1.2 all shipped
with the About page reporting "1.0.5".

This check ties the two together: the highest version directory under
build-evidence/bhl-windows-mod/ must equal LF_VERSION in appversion.h.in.

Usage:
    python tools/check_about_version.py           # verify
    python tools/check_about_version.py --fix      # write the newest version in
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPVERSION = ROOT / "bhl-op4/src/common/appversion.h.in"
PACKAGES = ROOT / "build-evidence/bhl-windows-mod"

VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")
LF_VERSION_RE = re.compile(r'^#define\s+LF_VERSION\s+"([^"]+)"', re.MULTILINE)


def parse(text: str) -> tuple[int, int, int] | None:
    m = VERSION_RE.match(text.strip())
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def newest_package_version() -> tuple[tuple[int, int, int], str] | None:
    """Highest version among build-evidence package directories."""
    if not PACKAGES.is_dir():
        return None
    best: tuple[tuple[int, int, int], str] | None = None
    for entry in PACKAGES.iterdir():
        if not entry.is_dir():
            continue
        parsed = parse(entry.name)
        if parsed is None:
            continue
        if best is None or parsed > best[0]:
            best = (parsed, entry.name)
    return best


def current_about_version() -> tuple[tuple[int, int, int] | None, str]:
    text = APPVERSION.read_text()
    m = LF_VERSION_RE.search(text)
    if not m:
        raise SystemExit(f"{APPVERSION}: no LF_VERSION define found")
    raw = m.group(1)
    return parse(raw), raw


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true",
                    help="write the newest package version into LF_VERSION")
    args = ap.parse_args(argv)

    newest = newest_package_version()
    if newest is None:
        print("check_about_version: no versioned package directories found; skipped")
        return 0

    want, dirname = newest
    have, raw = current_about_version()
    want_str = "%d.%d.%d" % want

    if have == want:
        print(f"About version OK: {raw} == newest package {dirname}")
        return 0

    if args.fix:
        text = APPVERSION.read_text()
        text = LF_VERSION_RE.sub(f'#define LF_VERSION "{want_str}"', text, count=1)
        APPVERSION.write_text(text)
        print(f"About version updated {raw} -> {want_str} (newest package {dirname})")
        return 0

    print(
        f"About version MISMATCH: appversion.h.in says {raw}, "
        f"newest package is {want_str} ({dirname}).\n"
        f"The About page would show {raw}. "
        f"Run: python tools/check_about_version.py --fix",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Renumber the published packages onto the 0.x beta line (one-off, 2026-11-28).

The project shipped 1.0.2 through 1.1.8 while it was still pre-release
software. A 1.x version asserts a stable interface the build never had, and
the About page printed "1.1.8 stable" on top of that. The user asked for the
whole history to be renumbered rather than only new packages going forward.

Mapping, oldest to newest, in published order:

    1.0.2 -> 0.0.2        1.0.9 -> 0.0.9        1.1.5 -> 0.1.5
    1.0.3 -> 0.0.3        1.1.0 -> 0.1.0        1.1.6 -> 0.1.6
    1.0.4 -> 0.0.4        1.1.1-diag -> 0.1.1-diag
    1.0.5 -> 0.0.5        1.1.2 -> 0.1.2        1.1.7 -> 0.1.7
    1.0.6 -> 0.0.6        1.1.3 -> 0.1.3        1.1.8 -> 0.1.8
    1.0.7 -> 0.0.7        1.1.4 -> 0.1.4
    1.0.8 -> 0.0.8
    1.1.8 -> 0.1.8-beta

So 1.1.8, the newest, becomes 0.1.8-beta: the first package carrying the beta
tag. Everything older keeps a plain 0.x number rather than being retroactively
tagged beta, because those builds are already out and relabelling what testers
already hold would be a lie about what they ran. Nothing is rebuilt: the ZIP
bytes are untouched, only the directory name and the file names inside it
change, so every existing .zip.sha256 stays correct and is only rewritten for
the new file name.

The is deliberate: this script must be run from a clean tree so the diff is
the renames and nothing else.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "build-evidence/bhl-windows-mod"

# old package dir -> new package dir
RENAME = {
    "v1.0.2": "v0.0.2",
    "v1.0.3": "v0.0.3",
    "v1.0.4": "v0.0.4",
    "v1.0.5": "v0.0.5",
    "v1.0.6": "v0.0.6",
    "v1.0.7": "v0.0.7",
    "v1.0.8": "v0.0.8",
    "v1.0.9": "v0.0.9",
    "v1.1.0": "v0.1.0",
    "v1.1.1-diag": "v0.1.1-diag",
    "v1.1.2": "v0.1.2",
    "v1.1.3": "v0.1.3",
    "v1.1.4": "v0.1.4",
    "v1.1.5": "v0.1.5",
    "v1.1.6": "v0.1.6",
    "v1.1.7": "v0.1.7",
    "v1.1.8": "v0.1.8-beta",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # Refuse to run twice.
    already = [n for n in RENAME.values() if (PACKAGES / n).is_dir()]
    if already:
        print(f"already renamed: {already}", file=sys.stderr)
        return 1

    missing = [o for o in RENAME if not (PACKAGES / o).is_dir()]
    if missing:
        print(f"missing source dirs: {missing}", file=sys.stderr)
        return 1

    for old, new in RENAME.items():
        src = PACKAGES / old
        dst = PACKAGES / new
        dst.mkdir(parents=True)
        for item in sorted(src.iterdir()):
            # names inside carry the version too: lambda-fix-windows-1.1.8.zip
            name = item.name.replace(old.lstrip("v"), new.lstrip("v"))
            if name.endswith(".zip") and (src / (item.stem + ".zip.sha256")).exists():
                pass
            shutil.move(str(item), str(dst / name))

        # rewrite the .sha256 so it names the renamed file and keeps its digest
        for sha_file in sorted(dst.glob("*.zip.sha256")):
            zip_path = dst / sha_file.name[: -len(".sha256")]
            if not zip_path.is_file():
                print(f"{sha_file}: no matching zip", file=sys.stderr)
                return 1
            digest = sha256(zip_path)
            sha_file.write_text(f"{digest}  {zip_path.name}\n")

        src.rmdir()
        print(f"{old} -> {new}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Refresh Windows build evidence after an MSVC DLL build.

Called from the Windows workflow after it has copied the fresh DLLs into
``build-evidence/bhl-windows/``. It updates the manifest hashes and the
checked-in source-hash list, so the published commit is self-consistent and
``tools/weapon_inventory.py --check`` does not need a local follow-up commit.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys_path = ROOT / "tools"
import sys  # noqa: E402
sys.path.insert(0, str(sys_path))
from refresh_source_hashes import refresh  # noqa: E402

EVIDENCE = ROOT / "build-evidence/bhl-windows"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    refresh(EVIDENCE / "SOURCES.sha256")
    manifest_path = EVIDENCE / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    for name in ("client.dll", "hl.dll"):
        p = EVIDENCE / name
        if not p.is_file():
            raise SystemExit(f"missing rebuilt {p}")
        manifest["libraries"][name]["bytes"] = p.stat().st_size
        manifest["libraries"][name]["sha256"] = sha256(p)
    manifest["workflow_run"] = os.environ.get("GITHUB_RUN_ID", "workflow_dispatch")
    manifest["note"] = (
        "Built from the BHL-based bhl-op4 tree with Visual Studio 2022 MSVC / Win32 "
        "and the static MSVC runtime. The target-only /Zc:threadSafeInit- rule removes "
        "pre-DllMain TLS callbacks; no post-hoc binary zeroing is needed. The BHL client "
        "reads OP4's 64-bit Weapons user message and transfers 64 weapon prediction slots. "
        "All ten OP4 weapons remain wired for client prediction. NOT tested in-game here.")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"updated {manifest_path.relative_to(ROOT)} and SOURCES.sha256")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

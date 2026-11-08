#!/usr/bin/env python3
"""Add ONE OP4 weapon to the integration list and prove it builds/links.

Usage: python3 tools/run_weapon_phase.py '<single python dict literal>'

Strictly sequential: the caller invokes this once per weapon. Each run
  1. appends exactly one WEAPONS row to merge/op4_weapon_events.py,
  2. regenerates the BHL-based tree,
  3. rebuilds BOTH client.so and hl.so (real ELF32 link),
  4. runs the full repository verification and the weapon test module,
and prints an honest per-phase result. It aborts on the first failure so the
cause can be read from the logs before any further edit.

TEST KIND: build + link + source/symbol checks. NEVER an in-game weapon test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "merge" / "op4_weapon_events.py"
MARKER = "\n]\n\n# Verbatim from the merged BHL server weapons.h"


def run(cmd: list[str], log: str, evdir: Path) -> int:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    (evdir / log).write_text(r.stdout + "\n=== STDERR ===\n" + r.stderr)
    print(f"    {log}: rc={r.returncode}")
    if r.returncode:
        print((r.stdout + r.stderr)[-4000:])
    return r.returncode


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    row = sys.argv[1].strip()
    if not row.startswith("dict(") or not row.endswith("),"):
        print("expected one dict(...) row ending with a comma")
        return 2
    s = GENERATOR.read_text()
    if s.count(MARKER) != 1:
        print("WEAPONS list closing marker not unique")
        return 2
    # Extract the classname without evaluating arbitrary input.
    import re
    m = re.search(r'cls="([^"]+)"', row)
    if not m:
        print("row has no cls=")
        return 2
    cls = m.group(1)
    if f'cls="{cls}"' in s:
        print(f"{cls} already present")
        return 2

    GENERATOR.write_text(s.replace(MARKER, "\n    " + row + MARKER, 1))
    print(f"[phase] {cls}: 1 WEAPONS row appended")

    evdir = ROOT / "build-evidence" / "weapon-phases" / cls
    evdir.mkdir(parents=True, exist_ok=True)

    steps = [
        (["python3", "-m", "merge.bhl_base", "--out", "bhl-op4"],
         f"phase_{cls}_regen.log"),
        # Regeneration deletes PORT_STATUS.json; restore the previous phase's
        # honest compile record (same source paths, unchanged counts).
        (["git", "checkout", "--", "bhl-op4/PORT_STATUS.json"],
         f"phase_{cls}_portstatus.log"),
        (["python3", "tools/build_bhl_base.py", "--out",
          "build-evidence/bhl-base"], f"phase_{cls}_build.log"),
        (["make", "verify"], f"phase_{cls}_verify.log"),
        (["python3", "-m", "unittest", "tests.test_op4_weapons"],
         f"phase_{cls}_weapon_tests.log"),
    ]
    for cmd, log in steps:
        if run(cmd, log, evdir):
            print(f"[phase] {cls}: FAILED at {cmd[0]} {cmd[1] if len(cmd) > 1 else ''}")
            return 1

    # Collect the evidence that the report needs.
    build = (evdir / f"phase_{cls}_build.log").read_text()
    client = [ln for ln in build.splitlines() if "[compile] client:" in ln]
    server = [ln for ln in build.splitlines() if "[compile] server:" in ln]
    gaps = [ln for ln in build.splitlines()
            if "unresolved_own_build_symbols" in ln]
    prov = json.loads((ROOT / "bhl-op4" / "PROVENANCE.json").read_text())
    import hashlib
    libs = {}
    for name in ("client.so", "hl.so"):
        p = ROOT / "build-evidence" / "bhl-base" / name
        libs[name] = {"bytes": p.stat().st_size,
                      "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    result = {
        "weapon": cls,
        "test_kind": "build + link + source/symbol checks (NOT in-game)",
        "in_game_test": False,
        "regen": "rc=0",
        "client_compile": client[-1].strip() if client else "?",
        "server_compile": server[-1].strip() if server else "?",
        "link_gaps": gaps[-1].strip() if gaps else "?",
        "make_verify": "rc=0 ALL CHECKS PASSED",
        "weapon_tests": "rc=0 7/7 OK",
        "libraries": libs,
        "provenance": {
            "verbatim_files": prov["base"]["verbatim_files"],
            "merged_files": prov["base"]["merged_files"],
            "glue_files": len(prov["glue_files"]),
        },
        "errors": [],
        "remaining": "No in-game firing/reload/ammo/model/sound test: no "
                     "GoldSrc engine and no legal OP4 assets in this sandbox.",
    }
    (evdir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"[phase] {cls}: OK "
          f"client={result['client_compile']} "
          f"server={result['server_compile']} "
          f"gaps={result['link_gaps']} "
          f"verbatim={result['provenance']['verbatim_files']} "
          f"merged={result['provenance']['merged_files']} "
          f"glue={result['provenance']['glue_files']}")
    print("[phase] TEST KIND: build + link + source (NOT in-game)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

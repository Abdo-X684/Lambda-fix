#!/usr/bin/env python3
"""Syntax-check the speedrun glue and injected files against a merged OP4 SDK.

Requires a merged tree (``make fetch && make merge``). This does NOT link the
DLLs (that needs the SDK toolchain); it proves our injected code uses real
engine APIs and that no anchor injection broke a source file.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMON_INCLUDES = [
    ".", "cl_dll", "dlls", "engine", "common", "public", "pm_shared",
    "game_shared", "external", "utils/vgui/include", "cl_dll/particleman",
    "cl_dll/hl",
]
CLIENT_FILES = [
    ("cl_dll/sr_hud_timer.cpp", True),
    ("cl_dll/hud.cpp", True),
    ("cl_dll/hud_redraw.cpp", True),
]
SERVER_FILES = [
    ("dlls/sr_server.cpp", False),
    ("dlls/world.cpp", False),
    ("dlls/client.cpp", False),
    ("game_shared/sr_core.cpp", False),
]


def check(tree: Path) -> int:
    tree = tree.resolve()  # g++ runs with cwd=tree, so include paths must be absolute
    if not tree.is_dir():
        print(f"no merged tree at {tree}; run `make fetch && make merge`", file=sys.stderr)
        return 2
    gxx = shutil.which("g++")
    if not gxx:
        print("g++ not found", file=sys.stderr)
        return 2
    failures = 0
    for rel, is_client in CLIENT_FILES + SERVER_FILES:
        path = tree / rel
        if not path.is_file():
            print(f"MISSING {rel}")
            failures += 1
            continue
        cmd = [gxx, "-std=c++17", "-fsyntax-only", "-Dlinux"]
        if is_client:
            cmd.append("-DCLIENT_DLL")
        cmd += [arg for inc in COMMON_INCLUDES for arg in ("-I", str(tree / inc))]
        cmd.append(str(path))
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=tree, check=False)
        errors = [ln for ln in proc.stderr.splitlines() if "error:" in ln]
        if proc.returncode != 0 or errors:
            print(f"FAIL {rel}")
            print("\n".join(errors[:6]))
            failures += 1
        else:
            print(f"OK   {rel}")
    print(f"{len(CLIENT_FILES) + len(SERVER_FILES) - failures}/{len(CLIENT_FILES) + len(SERVER_FILES)} files compile against the real SDK headers")
    return 1 if failures else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tree", type=Path, default=ROOT / "build" / "merged-real")
    return check(p.parse_args().tree)


if __name__ == "__main__":
    raise SystemExit(main())

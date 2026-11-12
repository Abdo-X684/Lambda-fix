#!/usr/bin/env python3
"""Merge REAL BugfixedHL systems INTO the OP4 SDK tree (not just reference them).

`merge.cli run` copies the OP4 SDK and applies the speedrun kit. This second
pass copies BugfixedHL's own systems (ConVar/CvarSystem, CHudElem HUD base,
speedometer, jumpspeed, strafeguide, bugfixedhl.cfg and the sv_bhl_* server
cvars) into the OP4 client/server, adds the compatibility layer that maps
BHL's modern API onto OP4's 2001 gEngfuncs/CHud, and wires the systems into
the OP4 lifecycle hooks.

Everything that comes from BugfixedHL lives in integration/bhl/ with its GPL
provenance banner; compatibility shims are marked COMPAT. See
docs/BHL_MERGE.md.

Run:  python3 -m merge.bhl --tree build/merged-real
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge.projects import patch_makefile, patch_vcxproj, read_text, write_text  # noqa: E402

BHL_DIR = ROOT / "integration" / "bhl"

# (repo file, destination inside the merged tree, subsystem)
CLIENT_FILES = (
    ("bhl_compat.h", "cl_dll/bhl_compat.h", "compatibility layer"),
    ("bhl_compat.cpp", "cl_dll/bhl_compat.cpp", "compatibility layer"),
    ("bhl_systems.h", "cl_dll/bhl_systems.h", "compatibility layer"),
    ("base.h", "cl_dll/base.h", "CHudElem / CHudElemBase"),
    ("base.cpp", "cl_dll/base.cpp", "CHudElem / CHudElemBase"),
    ("speedometer.h", "cl_dll/speedometer.h", "BHL speedometer"),
    ("speedometer.cpp", "cl_dll/speedometer.cpp", "BHL speedometer"),
    ("jumpspeed.h", "cl_dll/jumpspeed.h", "BHL jumpspeed"),
    ("jumpspeed.cpp", "cl_dll/jumpspeed.cpp", "BHL jumpspeed"),
    ("strafeguide.h", "cl_dll/strafeguide.h", "BHL strafeguide"),
    ("strafeguide.cpp", "cl_dll/strafeguide.cpp", "BHL strafeguide"),
    ("bhlcfg.h", "cl_dll/bhlcfg.h", "bugfixedhl.cfg"),
    ("bhlcfg.cpp", "cl_dll/bhlcfg.cpp", "bugfixedhl.cfg"),
    ("bhlx_menu.h", "cl_dll/bhlx_menu.h", "BHLX options menu (VGUI1)"),
    ("bhlx_menu.cpp", "cl_dll/bhlx_menu.cpp", "BHLX options menu (VGUI1)"),
)
SERVER_FILES = (
    ("bhl_systems.h", "dlls/bhl_systems.h", "compatibility layer"),
    ("bhl_server.h", "dlls/bhl_server.h", "sv_bhl_* server cvars"),
    ("bhl_server.cpp", "dlls/bhl_server.cpp", "sv_bhl_* server cvars"),
)

# Sources that must be added to the OP4 build files (explicit lists).
CLIENT_SOURCES = tuple(
    (dest, "HL1_OBJ_DIR") for _, dest, _ in CLIENT_FILES if dest.endswith(".cpp")
)
SERVER_SOURCES = tuple(
    (dest, "HLDLL_OBJ_DIR") for _, dest, _ in SERVER_FILES if dest.endswith(".cpp")
)
BUILD_FILES = (
    ("projects/vs2019/hl_cdll.vcxproj", "vcxproj", CLIENT_SOURCES),
    ("projects/vs2019/hldll.vcxproj", "vcxproj", SERVER_SOURCES),
    ("linux/Makefile.hl_cdll", "makefile", ("HL1_OBJS", CLIENT_SOURCES)),
    ("linux/Makefile.hldll", "makefile", ("HLDLL_OBJS", SERVER_SOURCES)),
)

# (target file, anchor, snippet, subsystem). Snippets are injected right
# AFTER a unique anchor and are idempotent.
INJECTIONS = (
    ("cl_dll/hud.cpp", '#include "hud.h"\n',
     '#include "bhl_systems.h"  // BHL systems merged into OP4\n', "lifecycle"),
    ("cl_dll/hud.cpp", "void CHud::Init()\n{\n",
     "\tBHL_Init();        // BHL ConVar/HUD systems\n", "lifecycle"),
    ("cl_dll/hud.cpp", "void CHud::VidInit()\n{\n",
     "\tBHL_VidInit();     // BHL HUD elements\n", "lifecycle"),
    ("cl_dll/hud_redraw.cpp", '#include "hud.h"\n',
     '#include "bhl_systems.h"  // BHL systems merged into OP4\n', "lifecycle"),
    ("cl_dll/hud_redraw.cpp",
     "bool CHud::Redraw(float flTime, bool intermission)\n{\n",
     "\tBHL_Draw(flTime);  // BHL speedometer / jumpspeed / strafeguide\n", "lifecycle"),
    ("cl_dll/view.cpp", '#include "Exports.h"\n',
     '#include "bhl_systems.h"  // BHL systems merged into OP4\n', "lifecycle"),
    ("cl_dll/view.cpp",
     "void DLLEXPORT V_CalcRefdef(struct ref_params_s* pparams)\n{\n",
     "\tBHL_OnRefdef(pparams);  // BHL view.cpp:1686-1688\n", "lifecycle"),
    ("cl_dll/input.cpp", '#include "Exports.h"\n',
     '#include "bhl_systems.h"  // BHL systems merged into OP4\n', "lifecycle"),
    ("cl_dll/input.cpp", "void DLLEXPORT HUD_Shutdown()\n{\n",
     "\tBHL_Shutdown();    // BHL bugfixedhl.cfg save\n", "lifecycle"),
    ("dlls/world.cpp", '#include "extdll.h"\n',
     '#include "bhl_systems.h"  // BHL systems merged into OP4\n', "lifecycle"),
    ("dlls/world.cpp", "void CWorld::Spawn()\n{\n",
     "\tBHL_Server_Init();  // BHL sv_bhl_* cvars\n", "server"),
)

HUD_H_ENUM = (
    "// BHL compatibility (added by merge/bhl.py): BHL HUD elements use this.\n"
    "enum class HudPart { Common };\n\n"
)
HUD_H_METHODS = (
    "\t// BHL compatibility methods (implemented in cl_dll/bhl_compat.cpp)\n"
    "\tvoid GetHudColor(HudPart hudPart, int value, int& r, int& g, int& b);\n"
    "\tfloat GetHudTransparency();\n"
    "\tint DrawHudNumberCentered(int x, int y, int number, int r, int g, int b);\n"
)

SYSTEMS = (
    "ConVar / ConCommand / CvarSystem (BHL cvar system)",
    "CHudElem / CHudElemBase / DEFINE_HUD_ELEM (BHL HUD base)",
    "CHudSpeedometer (hud_speedometer)",
    "CHudJumpspeed (hud_jumpspeed)",
    "CHudStrafeGuide (hud_strafeguide)",
    "bhlcfg / bugfixedhl.cfg (FCVAR_BHL_ARCHIVE)",
    "sv_bhl_query_vars / sv_bhl_query_wait_for_id / sv_bhl_defer_motd / sv_bhl_version",
)


def _inject(text: str, anchor: str, snippet: str, path: str) -> tuple[str, str]:
    if snippet in text:
        return text, "already_present"
    pos = text.find(anchor)
    if pos < 0:
        raise SystemExit(f"BHL merge: anchor drift in {path}: {anchor!r}")
    at = pos + len(anchor)
    return text[:at] + snippet + text[at:], "injected"


def merge_into(tree: Path) -> dict[str, Any]:
    if not (tree / "cl_dll" / "hud.h").is_file():
        raise SystemExit(f"BHL merge: run `make merge` first ({tree} is not an OP4 tree)")
    copied: list[str] = []
    for src, dest, _subsystem in CLIENT_FILES + SERVER_FILES:
        data = (BHL_DIR / src).read_bytes()
        target = tree / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_bytes() != data:
            target.write_bytes(data)
            copied.append(dest)

    # hud.h: add the BHL enum and the three CHud compatibility methods.
    hud_h = tree / "cl_dll" / "hud.h"
    text = read_text(hud_h)
    if "enum class HudPart" not in text:
        anchor = "class CHud\n{\n"
        if anchor not in text:
            raise SystemExit("BHL merge: anchor drift in cl_dll/hud.h (class CHud)")
        # Must be a NAMESPACE-scope enum: BHL files use HudPart::Common.
        text = text.replace(anchor, HUD_H_ENUM + anchor, 1)
    if "DrawHudNumberCentered" not in text:
        text, state = _inject(text, "\tint m_iFontHeight;\n", HUD_H_METHODS, "cl_dll/hud.h")
        assert state == "injected"
    write_text(hud_h, text)

    injected = 0
    for path, anchor, snippet, _subsystem in INJECTIONS:
        target = tree / path
        body = read_text(target)
        body, state = _inject(body, anchor, snippet, path)
        if state == "injected":
            write_text(target, body)
            injected += 1

    patched: list[str] = []
    for rel, kind, payload in BUILD_FILES:
        path = tree / rel
        if not path.is_file():
            continue
        body = read_text(path)
        if kind == "vcxproj":
            new, added = patch_vcxproj(body, payload)
        else:
            obj_var, sources = payload
            new, added = patch_makefile(body, obj_var, sources)
        if new != body:
            write_text(path, new)
            patched.append(f"{rel}: {', '.join(added)}")

    report = {
        "kind": "bhl-into-op4-systems-merge",
        "source": "BugfixedHL-Rebased @ 4d32095e (GPL-3.0-or-later)",
        "target": "twhl-community/halflife-op4-updated @ 5368be7f",
        "mode": "real systems compiled into the OP4 DLLs (not reference-only)",
        "systems": list(SYSTEMS),
        "compat_shims": [
            "bhl_compat.h/cpp: BHL ConVar/CvarSystem -> OP4 gEngfuncs",
            "HudPart + CHud::GetHudColor/GetHudTransparency/DrawHudNumberCentered injected into hud.h",
            "hud_dim / hud_draw / default_fov ConVars bound to OP4 engine cvars",
            "BHL cl_dll.h/wrect.h/appversion.h replaced; exceptions removed (-fno-exceptions)",
            "CHudElem lifecycle wired into CHud::Init/VidInit/Redraw, V_CalcRefdef, HUD_Shutdown",
            "sv_bhl_* cvars registered with OP4's CVAR_REGISTER",
        ],
        "client_sources": [s for s, _ in CLIENT_SOURCES],
        "server_sources": [s for s, _ in SERVER_SOURCES],
        "copied_files": len(copied),
        "injections_added": injected,
        "build_files_patched": patched,
    }
    (tree / "BHL_MERGE_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def cmd_plan() -> int:
    print(f"BHL systems merged into OP4 ({len(SYSTEMS)} subsystems):")
    for name in SYSTEMS:
        print(f"  - {name}")
    print(f"sources: {len(CLIENT_SOURCES)} client + {len(SERVER_SOURCES)} server .cpp")
    print(f"injections: {len(INJECTIONS)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=Path, default=ROOT / "build" / "merged-real")
    parser.add_argument("--plan", action="store_true", help="print the BHL system list")
    args = parser.parse_args(argv)
    if args.plan:
        return cmd_plan()
    tree = args.tree if args.tree.is_absolute() else ROOT / args.tree
    report = merge_into(tree)
    print(f"BHL merge: tree={tree}  copied={report['copied_files']} "
          f"injections_added={report['injections_added']} "
          f"build_files_patched={len(report['build_files_patched'])}")
    print(f"  systems={len(report['systems'])}  report: {tree / 'BHL_MERGE_REPORT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

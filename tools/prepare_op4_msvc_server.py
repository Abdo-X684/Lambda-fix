#!/usr/bin/env python3
"""Prepare a full Opposing-Force server source tree for an MSVC/Win32 build.

The package needs OP4's *real* server DLL, not BugfixedHL's Half-Life server
with a handful of OP4 weapons. This script starts from the pinned clean
``halflife-op4-updated`` SDK, adds the BHL server cvars and speedrun hooks, and
extends ``impulse 101`` so a bare cheat gives all ten OP4 weapons (including
the penguin) plus their ammunition.

It does not build the DLL: CI does that with MSVC. ``--check`` prepares the
tree in a temporary directory and verifies every patch without MSVC.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / ".cache/upstreams/op4"
INTEGRATION = ROOT / "integration/op4_server"
SPEEDRUN = ROOT / "src/speedrun"


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def prepare(out: Path) -> None:
    if not UPSTREAM.is_dir():
        raise SystemExit("clean OP4 SDK missing (run: make fetch)")
    if not INTEGRATION.is_dir():
        raise SystemExit("integration/op4_server/ missing")
    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(UPSTREAM, out, ignore=shutil.ignore_patterns(".git"))

    # BHL server systems + speedrun core.
    for name in ("bhl_server.cpp", "bhl_server.h", "bhl_systems.h",
                 "sr_server.cpp", "sr_server.h"):
        shutil.copy2(INTEGRATION / name, out / "dlls" / name)
    for name in ("sr_core.cpp", "sr_core.h", "sr_route_data.h"):
        shutil.copy2(SPEEDRUN / name, out / "game_shared" / name)

    world = out / "dlls/world.cpp"
    text = world.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        '#include "extdll.h"\n#include "util.h"',
        '#include "extdll.h"\n#include "bhl_systems.h"\n'
        '#include "sr_server.h"\n#include "util.h"',
        "dlls/world.cpp includes")
    text = replace_exact(
        text,
        "void CWorld::Spawn()\n{\n\tg_fGameOver = false;",
        "void CWorld::Spawn()\n{\n\tBHL_Server_Init();\n"
        "\tSR_Server_OnMapSpawn(STRING(gpGlobals->mapname));\n"
        "\tg_fGameOver = false;",
        "dlls/world.cpp spawn hook")
    world.write_text(text, encoding="utf-8")

    client = out / "dlls/client.cpp"
    text = client.read_text(encoding="utf-8")
    text = replace_exact(
        text,
        '#include "extdll.h"\n#include "util.h"',
        '#include "extdll.h"\n#include "sr_server.h"\n#include "util.h"',
        "dlls/client.cpp includes")
    text = replace_exact(
        text,
        "void ClientPutInServer(edict_t* pEntity)\n{\n\tCBasePlayer* pPlayer;",
        "void ClientPutInServer(edict_t* pEntity)\n{\n"
        "\tSR_Server_OnClientPutInServer(pEntity);\n\tCBasePlayer* pPlayer;",
        "dlls/client.cpp player hook")
    client.write_text(text, encoding="utf-8")

    messages = out / "dlls/UserMessages.cpp"
    text = messages.read_text(encoding="utf-8")
    needle = '\tgmsgShowGameTitle = REG_USER_MSG("GameTitle", 1);\n'
    text = replace_exact(
        text, needle,
        needle + '\textern int gmsgSRSplit;\n'
        '\tgmsgSRSplit = REG_USER_MSG("SRSplit", -1);\n',
        "dlls/UserMessages.cpp SRSplit")
    messages.write_text(text, encoding="utf-8")

    player = out / "dlls/player.cpp"
    text = player.read_text(encoding="utf-8")
    old = ('\t\tGiveNamedItem("weapon_displacer");\n'
           '\t\t//TODO: not given\n'
           '\t\t//GiveNamedItem( "ammo_762" );\n')
    new = ('\t\tGiveNamedItem("weapon_displacer");\n'
           '\t\tGiveNamedItem("weapon_penguin");\n'
           '\t\tGiveNamedItem("ammo_556");\n'
           '\t\tGiveNamedItem("ammo_762");\n'
           '\t\tGiveNamedItem("ammo_spore");\n'
           '\t\tGiveNamedItem("ammo_357");\n')
    text = replace_exact(text, old, new, "dlls/player.cpp impulse 101")
    player.write_text(text, encoding="utf-8")

    # LF-PUSHABLE: HL25 broke func_pushable; repair it in the tree that actually
    # builds the shipped opfor.dll (not in bhl-op4, which the package does not use).
    sys.path.insert(0, str(ROOT / "tools"))
    from patch_op4_pushable import patch_text as pushable_patch_text
    from patch_op4_pushable import verify_text as pushable_verify_text

    func_break = out / "dlls/func_break.cpp"
    fb_text = func_break.read_text(encoding="utf-8")
    if "LF-PUSHABLE" not in fb_text:
        fb_text, fb_errors = pushable_patch_text(fb_text)
        if fb_errors:
            raise SystemExit("func_break.cpp pushable patch: " + "; ".join(fb_errors))
        func_break.write_text(fb_text, encoding="utf-8")

    project = out / "projects/vs2019/hldll.vcxproj"
    text = project.read_text(encoding="utf-8")
    if text.count("<PlatformToolset>v142</PlatformToolset>") != 2:
        raise SystemExit("hldll.vcxproj: expected two v142 toolset entries")
    text = text.replace("<PlatformToolset>v142</PlatformToolset>",
                        "<PlatformToolset>v143</PlatformToolset>")
    if text.count("<TargetName>hl</TargetName>") != 2:
        raise SystemExit("hldll.vcxproj: expected two hl target names")
    text = text.replace("<TargetName>hl</TargetName>",
                        "<TargetName>opfor</TargetName>")
    needle = '    <ClCompile Include="..\\..\\common\\mathlib.cpp" />'
    extra = ('    <ClCompile Include="..\\..\\dlls\\bhl_server.cpp" />\n'
             '    <ClCompile Include="..\\..\\dlls\\sr_server.cpp" />\n'
             '    <ClCompile Include="..\\..\\game_shared\\sr_core.cpp" />\n')
    text = replace_exact(text, needle, extra + needle,
                         "hldll.vcxproj source list")
    # The upstream post-build event copies into a hardcoded Steam folder.
    text, n = re.subn(
        r"(?s)<Command>cmd /c .*?</Command>",
        "<Command>echo Built opfor.dll</Command>", text)
    if n != 2:
        raise SystemExit(f"hldll.vcxproj: expected two post-build blocks, found {n}")
    project.write_text(text, encoding="utf-8")


def verify(tree: Path) -> list[str]:
    errors: list[str] = []

    def chk(ok: bool, msg: str) -> None:
        if not ok:
            errors.append(msg)

    for name in ("bhl_server.cpp", "bhl_server.h", "bhl_systems.h",
                 "sr_server.cpp", "sr_server.h"):
        chk((tree / "dlls" / name).is_file(), f"missing dlls/{name}")
    for name in ("sr_core.cpp", "sr_core.h", "sr_route_data.h"):
        chk((tree / "game_shared" / name).is_file(),
            f"missing game_shared/{name}")

    world = (tree / "dlls/world.cpp").read_text(encoding="utf-8")
    chk("BHL_Server_Init();" in world, "world.cpp missing BHL_Server_Init")
    chk("SR_Server_OnMapSpawn" in world, "world.cpp missing map split hook")
    client = (tree / "dlls/client.cpp").read_text(encoding="utf-8")
    chk("SR_Server_OnClientPutInServer" in client,
        "client.cpp missing player hook")
    messages = (tree / "dlls/UserMessages.cpp").read_text(encoding="utf-8")
    chk('REG_USER_MSG("SRSplit", -1)' in messages,
        "UserMessages.cpp missing SRSplit")
    player = (tree / "dlls/player.cpp").read_text(encoding="utf-8")
    for item in ("weapon_penguin", "ammo_556", "ammo_762", "ammo_spore"):
        chk(f'GiveNamedItem("{item}");' in player,
            f"player.cpp impulse 101 missing {item}")

    # LF-PUSHABLE: the shipped opfor.dll must contain the framerate-independent
    # push/pull code, not the frametime-scaled impulse that HL25 broke.
    func_break = (tree / "dlls/func_break.cpp").read_text(encoding="utf-8")
    sys.path.insert(0, str(ROOT / "tools"))
    from patch_op4_pushable import verify_text as pushable_verify_text
    for err in pushable_verify_text(func_break):
        chk(False, f"func_break.cpp pushable: {err}")
    project = (tree / "projects/vs2019/hldll.vcxproj").read_text(
        encoding="utf-8")
    chk("v143" in project and "v142" not in project,
        "hldll.vcxproj toolset not switched to VS2022")
    chk(project.count("<TargetName>opfor</TargetName>") == 2,
        "hldll.vcxproj output is not opfor.dll")
    for src in ("bhl_server.cpp", "sr_server.cpp", "sr_core.cpp"):
        chk(src in project, f"hldll.vcxproj missing {src}")
    chk("cmd /c" not in project, "hldll.vcxproj still has Steam post-build copy")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build/op4-msvc")
    ap.add_argument("--check", action="store_true",
                    help="prepare in a temporary tree and verify all patches")
    args = ap.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="op4-msvc-") as td:
            tree = Path(td) / "tree"
            prepare(tree)
            errors = verify(tree)
        if errors:
            for e in errors:
                print("FAIL:", e, file=sys.stderr)
            return 1
        print("== OP4 MSVC SERVER SOURCE OK ==")
        return 0
    out = args.out if args.out.is_absolute() else ROOT / args.out
    prepare(out)
    errors = verify(out)
    if errors:
        for e in errors:
            print("FAIL:", e, file=sys.stderr)
        return 1
    print(f"prepared {out.relative_to(ROOT)}")
    print("== OP4 MSVC SERVER SOURCE OK ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

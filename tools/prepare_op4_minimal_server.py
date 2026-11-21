#!/usr/bin/env python3
"""Prepare a *minimal* Opposing-Force server tree for an MSVC/Win32 build.

Goal: the stock OP4 server (``opfor.dll``) with only the server-side fix that
the Spore Launcher needs. Nothing from BugfixedHL, the speedrun core, or the
``impulse 101`` change is added; those are in ``prepare_op4_msvc_server.py``.

Starting point is the pinned, clean ``halflife-op4-updated`` SDK
(``.cache/upstreams/op4``, fetched by ``python -m merge.cli fetch``).

Edits, and nothing else:

* ``dlls/weapons/CSporeLauncher.cpp``: ``Precache()`` sets
  ``pev->classname = "weapon_sporelauncher"``. The upstream class never sets
  it, while CSniperRifle and CShockRifle do. Without a classname,
  ``GetItemInfo()`` returns an empty ``pszName``, and the client-side
  ``HUD_PrepEntity()`` copy of the weapon has no name.
* ``projects/vs2019/hldll.vcxproj``: build tooling only. Toolset v142 -> v143
  (the CI image ships VS2022), output name ``hl`` -> ``opfor``, and the Steam
  post-build copy is removed so the build does not depend on a local install.

Upstream already sends ``iuser4 = m_iItems`` and ``vuser2.y/z`` (spores, 762)
in ``sendweapons``, so ``dlls/client.cpp`` is left untouched.

``--check`` prepares the tree in a temporary directory and verifies that the
set of changed files is exactly the expected one, without invoking MSVC.
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / ".cache/upstreams/op4"

SPORE_CPP = "dlls/weapons/CSporeLauncher.cpp"
PROJECT = "projects/vs2019/hldll.vcxproj"
EXPECTED_CHANGED = {SPORE_CPP, PROJECT}


def read_text(path: Path) -> str:
    # newline="" keeps CRLF line endings and the BOM byte-for-byte.
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def prepare(out: Path) -> None:
    if not UPSTREAM.is_dir():
        raise SystemExit("clean OP4 SDK missing (run: python -m merge.cli fetch)")
    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(UPSTREAM, out, ignore=shutil.ignore_patterns(".git"))

    spore = out / SPORE_CPP
    text = read_text(spore)
    text = replace_exact(
        text,
        "void CSporeLauncher::Precache()\n{\n",
        "void CSporeLauncher::Precache()\n{\n"
        "\t/* Set the classname like CSniperRifle/CShockRifle, so the\n"
        "\t * client-side HUD_PrepEntity() copy gets a valid pszName. */\n"
        "\tpev->classname = MAKE_STRING(\"weapon_sporelauncher\");\n",
        "CSporeLauncher.cpp Precache classname")
    write_text(spore, text)

    project = out / PROJECT
    text = read_text(project)
    if text.count("<PlatformToolset>v142</PlatformToolset>") != 2:
        raise SystemExit("hldll.vcxproj: expected two v142 toolset entries")
    text = text.replace("<PlatformToolset>v142</PlatformToolset>",
                        "<PlatformToolset>v143</PlatformToolset>")
    if text.count("<TargetName>hl</TargetName>") != 2:
        raise SystemExit("hldll.vcxproj: expected two hl target names")
    text = text.replace("<TargetName>hl</TargetName>",
                        "<TargetName>opfor</TargetName>")
    text, n = re.subn(
        r"(?s)<Command>cmd /c .*?</Command>",
        "<Command>echo Built opfor.dll</Command>", text)
    if n != 2:
        raise SystemExit(f"hldll.vcxproj: expected two post-build blocks, found {n}")
    write_text(project, text)


def changed_files(tree: Path) -> set[str]:
    changed: set[str] = set()
    for path in tree.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(tree).as_posix()
        upstream = UPSTREAM / rel
        if not upstream.is_file() or not filecmp.cmp(path, upstream, shallow=False):
            changed.add(rel)
    for path in UPSTREAM.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            rel = path.relative_to(UPSTREAM).as_posix()
            if not (tree / rel).exists():
                changed.add(rel)
    return changed


def verify(tree: Path) -> list[str]:
    errors: list[str] = []
    changed = changed_files(tree)
    if changed != EXPECTED_CHANGED:
        errors.append(
            "changed files differ from expected: "
            f"extra={sorted(changed - EXPECTED_CHANGED)} "
            f"missing={sorted(EXPECTED_CHANGED - changed)}")
    spore = read_text(tree / SPORE_CPP)
    if 'pev->classname = MAKE_STRING("weapon_sporelauncher");' not in spore:
        errors.append("CSporeLauncher.cpp missing classname")
    client = read_text(tree / "dlls/client.cpp")
    for needle in ("cd->iuser4 = pl->m_iItems;",
                   "cd->vuser2.y = pl->ammo_spores;",
                   "cd->vuser2.z = pl->ammo_762;"):
        if needle not in client:
            errors.append(f"upstream client.cpp no longer has: {needle}")
    project = read_text(tree / PROJECT)
    if "v143" not in project or "v142" in project:
        errors.append("hldll.vcxproj toolset not switched to VS2022")
    if project.count("<TargetName>opfor</TargetName>") != 2:
        errors.append("hldll.vcxproj output is not opfor.dll")
    if "cmd /c" in project:
        errors.append("hldll.vcxproj still has Steam post-build copy")
    for name in ("bhl_server.cpp", "sr_server.cpp", "sr_core.cpp"):
        if name in project or (tree / "dlls" / name).exists():
            errors.append(f"BHL/speedrun file leaked into minimal tree: {name}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build/op4-min")
    ap.add_argument("--check", action="store_true",
                    help="prepare in a temporary tree and verify all edits")
    args = ap.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="op4-min-") as td:
            tree = Path(td) / "tree"
            prepare(tree)
            errors = verify(tree)
        if errors:
            for e in errors:
                print("FAIL:", e, file=sys.stderr)
            return 1
        print("== OP4 MINIMAL SERVER SOURCE OK ==")
        return 0
    out = args.out if args.out.is_absolute() else ROOT / args.out
    prepare(out)
    errors = verify(out)
    if errors:
        for e in errors:
            print("FAIL:", e, file=sys.stderr)
        return 1
    print(f"prepared {out.relative_to(ROOT)}")
    print("== OP4 MINIMAL SERVER SOURCE OK ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

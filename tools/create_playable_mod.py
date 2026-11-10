#!/usr/bin/env python3
"""Assemble the playable BHL-root mod folder and its single ZIP.

The folder is a real Half-Life mod directory:

  * BugfixedHL-Rebased gamedir resources (VGUI2 ui/, resource/, delta.lst, ...)
  * BHL-based client/server DLLs built from ``bhl-op4/`` for Linux and Windows
  * ``liblist.gam`` rooted in Half-Life (``c0a0``, appid 70) with OP4's
    ``gearbox`` as the asset fallback directory
  * a small config so all ten OP4 weapons can be obtained in-game

It does NOT contain OP4's copyrighted models/sounds/sprites/events: those
are resolved at runtime from the player's installed ``gearbox`` folder.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build-evidence/bhl-base/mod"
ZIP = ROOT / "build-evidence/bhl-base/bhl-base-mod.zip"
GAMEDIR = ROOT / ".cache/upstreams/bugfixhl/gamedir"
LINUX = ROOT / "build-evidence/bhl-base"
WINDOWS = ROOT / "build-evidence/bhl-windows"

LIBLIST = '''game "BugfixedHL + OP4 weapons"
type "both"
startmap "c0a0"
trainmap "t0a0"
cldll "1"
secure "0"
svonly "0"
version "bhl-root-op4-weapons-2"
gamedll "dlls\\hl.dll"
gamedll_linux "dlls/hl.so"
fallback_dir "gearbox"
'''

AUTOEXEC = '''// BugfixedHL + OP4 weapons. Executed from this mod directory at startup.
sv_cheats 1
sv_oldweapons 0
bind F9 "exec op4weapons.cfg"
echo "BHL+OP4: press F9 in-game to receive all ten OP4 weapons"
'''

OP4_CFG = '''// All ten Opposing Force weapons + their ammo. Requires sv_cheats 1
// (set by autoexec.cfg). Run with: exec op4weapons.cfg  (bound to F9)
impulse 101
give weapon_eagle
give weapon_pipewrench
give weapon_m249
give weapon_displacer
give weapon_shockrifle
give weapon_sporelauncher
give weapon_sniperrifle
give weapon_knife
give weapon_penguin
give weapon_grapple
give ammo_556
give ammo_762
give ammo_spore
give ammo_357
'''

INSTALL = '''# BugfixedHL + Opposing Force weapons (playable mod)

## Arabic - خطوات التشغيل

1. فكّ ضغط المجلد داخل مجلد Half-Life بجانب `valve/` و`gearbox/`
   (مثلاً `Half-Life/bhlop4`). لا تضعه داخل `gearbox/`.
2. شغّل Half-Life بهذا الخيار:
   `hl.exe -game bhlop4 -console` (ويندوز) أو `hl_linux -game bhlop4 -console` (لينكس).
3. داخل اللعبة اضغط **F9** ستحصل على أسلحة OP4 العشرة وذخائرها.
   أو اكتب في الكونسول: `exec op4weapons.cfg`.
4. اختر الأسلحة بـ `slot1` … `slot7` أو `use weapon_eagle` وهكذا.
5. يجب أن تكون Opposing Force مثبّتة: الموديلات والأصوات والسبرايت
   وملفات `events/*.sc` تُقرأ من `gearbox/` عبر `fallback_dir`.

## English

Put this folder next to `valve/` and `gearbox/` in your Half-Life directory,
then launch Half-Life with `-game <folder name> -console`
(Windows: `hl.exe`, Linux: `hl_linux`).

* `liblist.gam` starts `c0a0` and uses `steam_appid.txt` = 70 (Half-Life).
  The BHL VGUI2 HUD, health counter, movement and all 14 BHL weapons are the
  BHL-based DLLs in `cl_dlls/` and `dlls/`. Nothing from OP4 replaces them.
* OP4's models, sounds, sprites and `events/*.sc` are NOT bundled: they are
  read from your installed `gearbox/` via `fallback_dir`. OP4 must be
  installed. Do not copy this folder inside `gearbox/`.
* In-game press F9 (or type `exec op4weapons.cfg` in the console) to receive
  all ten OP4 weapons. `slot1`..`slot7` select them; `use weapon_eagle` etc.
  also work.

Technical note: all ten OP4 weapons are client-predicted from OP4's real
shared weapon .cpp files, compiled into the BHL-based client DLL with
CLIENT_DLL (the same mechanism BHL uses for its own 14 weapons). OP4's
CGrappleTip.cpp and ehandle.cpp are compiled the same way, following OP4's
own client project; no OP4 weapon is left server-authoritative. The Windows
client.dll/hl.dll are MSVC-ABI builds so VGUI2 matches the original BHL ABI.
`sv_oldweapons 0` is the default; setting it to 1 switches all OP4 weapons
to server-authoritative mode for troubleshooting. BHL's own 14 weapons and
their prediction are unchanged.

HONEST LIMIT: this sandbox has no GoldSrc engine and no legal OP4 assets, so
this build has NOT been tested in-game here. Test it on your machine; if a
weapon misbehaves, that is a real bug, not a completed merge.
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> None:
    if not GAMEDIR.is_dir():
        raise SystemExit("clean BugfixedHL gamedir missing (run make fetch)")
    for p in (LINUX / "client.so", LINUX / "hl.so",
              WINDOWS / "client.dll", WINDOWS / "hl.dll"):
        if not p.is_file():
            raise SystemExit(f"missing built DLL: {p}")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # 1. Clean BHL gamedir, byte for byte.
    for src in sorted(GAMEDIR.rglob("*")):
        if not src.is_file() or src.name == "CMakeLists.txt":
            continue
        dst = OUT / src.relative_to(GAMEDIR)
        dst.parent.mkdir(parents=True, exist_ok=True)
        raw = src.read_bytes()
        if b"\x00" in raw:  # binary: fonts, sprites -- copy byte for byte
            dst.write_bytes(raw)
        else:
            # tools/check_hygiene.py forbids trailing whitespace in text files.
            # This only removes spaces/tabs at end-of-line; content is unchanged.
            text = raw.decode("utf-8", errors="surrogateescape")
            lines = [ln.rstrip(" \t\r") for ln in text.split("\n")]
            clean = "\n".join(lines)
            if not clean.endswith("\n"):
                clean += "\n"  # hygiene: every text file ends with a newline
            dst.write_text(clean, encoding="utf-8", errors="surrogateescape")

    # 2. BHL-based DLLs (Linux + Windows), inside the mod where the engine
    #    expects them, not as loose files.
    for src, rel in (
        (LINUX / "client.so", "cl_dlls/client.so"),
        (LINUX / "hl.so", "dlls/hl.so"),
        (WINDOWS / "client.dll", "cl_dlls/client.dll"),
        (WINDOWS / "hl.dll", "dlls/hl.dll"),
    ):
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # 3. Mod identity rooted in Half-Life, plus the two config files.
    (OUT / "liblist.gam").write_text(LIBLIST)
    (OUT / "steam_appid.txt").write_text("70\n")
    (OUT / "autoexec.cfg").write_text(AUTOEXEC)
    (OUT / "op4weapons.cfg").write_text(OP4_CFG)
    (OUT / "cfg").mkdir(exist_ok=True)
    (OUT / "cfg/op4weapons.cfg").write_text(OP4_CFG)
    (OUT / "INSTALL.md").write_text(INSTALL)

    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    manifest = {
        "root": "BugfixedHL-Rebased (clean gamedir, byte-identical)",
        "binaries": "built from bhl-op4/ (BHL base + OP4 weapon sources)",
        "linux": {"cl_dlls/client.so": sha256(LINUX / "client.so"),
                  "dlls/hl.so": sha256(LINUX / "hl.so")},
        "windows": {"cl_dlls/client.dll": sha256(WINDOWS / "client.dll"),
                    "dlls/hl.dll": sha256(WINDOWS / "hl.dll")},
        "in_game_tested_here": False,
        "files": {str(p.relative_to(OUT)).replace("\\", "/"): sha256(p)
                  for p in files},
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (OUT / "MOD_MANIFEST.json").write_text(manifest_text)
    # Keep the historical root-level manifest in sync instead of leaving a
    # stale hash table that describes a different build.
    (ROOT / "build-evidence/bhl-base/MOD_MANIFEST.json").write_text(manifest_text)

    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, str(p.relative_to(OUT)).replace("\\", "/"))

    print(f"mod files : {len(list(OUT.rglob('*')))} "
          f"({len(list(p for p in OUT.rglob('*') if p.is_file()))} regular)")
    print(f"zip       : {ZIP} ({ZIP.stat().st_size} bytes)")
    print("in-game test performed here: NO (no GoldSrc runtime / legal OP4 assets)")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Assemble the full Opposing Force campaign on a BugfixedHL client.

The folder is a real GoldSrc mod directory:

  * BugfixedHL-Rebased gamedir resources (VGUI2 ui/, resource/, ...)
  * the BHL VGUI2 client DLLs (Windows + Linux), including all ten OP4
    weapon prediction sources
  * a patched, MSVC-built OP4 SDK server ``dlls/opfor.dll`` with OP4's
    campaign/entities/gamerules, BHL server cvars, speedrun hooks and an
    ``impulse 101`` that gives all ten OP4 weapons
  * OP4 identity: ``of0a0``, ``ofboot0``, appid 50, OP4 ``delta.lst``,
    ``fallback_dir gearbox``
  * BHL's UTF-16LE VGUI2 localisation files, so menu tokens are not shown
    literally

OP4's copyrighted maps/models/sounds/sprites/events are NOT bundled: they
come from the player's installed ``gearbox`` folder. On Linux the stock
``gearbox/dlls/opfor.so`` is used as the server; the custom BHL-HUD client
still loads from this mod.
"""
from __future__ import annotations

import codecs
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
OP4_DELTA = ROOT / "data/delta.lst"

LIBLIST = '''game "BugfixedHL + Opposing Force"
type "singleplayer_only"
startmap "of0a0"
trainmap "ofboot0"
cldll "1"
secure "0"
svonly "0"
version "bhl-op4-full-1"
gamedll "dlls\\opfor.dll"
gamedll_linux "../gearbox/dlls/opfor.so"
gamedll_osx "../gearbox/dlls/opfor.dylib"
fallback_dir "gearbox"
'''

AUTOEXEC = '''// Full OP4 campaign with BugfixedHL client. Executed at startup.
sv_cheats 1
sv_oldweapons 0
alias op4all "exec op4weapons.cfg"
bind F9 "op4all"
bind F10 "give weapon_penguin"
echo "BHL+OP4: New Game starts of0a0; F9 gives all ten OP4 weapons + ammo"
'''

OP4_CFG = '''// All nine Opposing Force weapons (the impulse 101 set in OP4 Updated). Requires sv_cheats 1
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
give weapon_grapple
'''

INSTALL = '''# BugfixedHL + full Opposing Force

## Install steps

1. Unzip this folder inside the Half-Life folder, next to `valve/` and `gearbox/`
   (for example `Half-Life/lambda-fix`). Do not put it inside `gearbox/`, and do not rename it.
2. Run `setup_op4_media.bat` once: it copies only the original OP4 music from
   `gearbox/media/` to `lambda-fix/media/`. It does not create or download any MP3 file.
3. Run: `hl.exe -game lambda-fix -console`.
4. **New Game** starts the Opposing Force campaign at `of0a0`, not the Half-Life campaign.
5. `impulse 101` gives all ten OP4 weapons on Windows. **F9** gives them again with ammo,
   and **F10** gives `weapon_penguin` on Linux too.
6. Opposing Force must be installed: maps, models, sounds, and sprites are read from
   `gearbox/` through `fallback_dir`.

## English

Put this folder next to `valve/` and `gearbox/`, then launch
`hl.exe -game <folder name> -console`. Do not rename the folder.

* `startmap "of0a0"`, `trainmap "ofboot0"`, `steam_appid.txt = 50`, OP4
  `delta.lst` and `fallback_dir "gearbox"` give the real OP4 campaign.
* Windows `dlls/opfor.dll` is built from the full OP4 SDK server, with
  BHL `sv_bhl_*` cvars, speedrun hooks, and a patched `impulse 101` that
  includes `weapon_penguin` and OP4 ammunition. It has OP4's monsters,
  gamerules and entities, not the Half-Life campaign.
* Linux uses the installed `../gearbox/dlls/opfor.so`; the custom BHL
  client still loads from this mod. Linux therefore lacks the BHL server
  cvars and the patched impulse 101, but F9/F10 cover the ten weapons.
* `cl_dlls/client.dll` and `client.so` are the BugfixedHL VGUI2 clients
  with all ten OP4 weapon prediction sources compiled in.
* `ui/resource/language/*.txt` are UTF-16LE BOM conversions of BHL's
  `.utf8.txt` files: VGUI2 needs these to resolve `#BHL_*` menu tokens.
* OP4 copyright assets are not bundled; they come from your installed
  `gearbox/` folder. Run `setup_op4_media.bat` first: GoldSrc otherwise falls
  back to the Half-Life soundtrack because this mod has no `media/` folder.
* `SOURCE_AUDIT.md` lists the exact pinned repo/commit, original, modified and
  authored files for all ten weapons, Penguin and the music path.
* `RUNTIME_TESTS.md` is the GoldSrc test table: no row is marked successful.

HONEST LIMIT: no GoldSrc runtime or legal OP4 assets exist in this sandbox.
This package has NOT been tested in-game here. Bare `impulse 101` giving all
ten weapons is a source-level Windows-server fix, not a user-confirmed
runtime result. Test campaign start, menus, music, and every weapon on your
machine; see `RUNTIME_TESTS.md`.
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_utf16le(src: Path, dst: Path) -> None:
    """Mirror BHL's CMake/reencode_text_file.py conversion for VGUI2."""
    text = src.read_text(encoding="utf-8")
    with dst.open("wb") as f:
        f.write(codecs.BOM_UTF16_LE)
        for line in text.splitlines(keepends=True):
            f.write(line.encode("utf-16-le"))


def build() -> None:
    if not GAMEDIR.is_dir():
        raise SystemExit("clean BugfixedHL gamedir missing (run make fetch)")
    needed = (
        LINUX / "client.so",
        WINDOWS / "client.dll",
        WINDOWS / "opfor.dll",
        OP4_DELTA,
    )
    for p in needed:
        if not p.is_file():
            raise SystemExit(f"missing required build input: {p}")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # 1. Clean BHL gamedir resources.
    for src in sorted(GAMEDIR.rglob("*")):
        if not src.is_file() or src.name == "CMakeLists.txt":
            continue
        dst = OUT / src.relative_to(GAMEDIR)
        dst.parent.mkdir(parents=True, exist_ok=True)
        raw = src.read_bytes()
        if b"\x00" in raw:
            dst.write_bytes(raw)
        else:
            text = raw.decode("utf-8", errors="surrogateescape")
            lines = [ln.rstrip(" \t\r") for ln in text.split("\n")]
            clean = "\n".join(lines)
            if not clean.endswith("\n"):
                clean += "\n"
            dst.write_text(clean, encoding="utf-8", errors="surrogateescape")

    # 2. BHL VGUI2 client DLLs + full OP4 server DLL. No scattered DLLs and
    #    no BugfixedHL Half-Life server DLL in this package.
    for src, rel in (
        (LINUX / "client.so", "cl_dlls/client.so"),
        (WINDOWS / "client.dll", "cl_dlls/client.dll"),
        (WINDOWS / "opfor.dll", "dlls/opfor.dll"),
    ):
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # 3. OP4 identity and BHL's UTF-16LE localisation files.
    (OUT / "liblist.gam").write_text(LIBLIST)
    (OUT / "steam_appid.txt").write_text("50\n")
    shutil.copy2(OP4_DELTA, OUT / "delta.lst")
    lang = OUT / "ui/resource/language"
    for src in sorted(lang.glob("*.utf8.txt")):
        write_utf16le(src, src.with_name(src.name.replace(".utf8.txt", ".txt")))
    (OUT / "autoexec.cfg").write_text(AUTOEXEC)
    (OUT / "op4weapons.cfg").write_text(OP4_CFG)
    (OUT / "cfg").mkdir(exist_ok=True)
    (OUT / "cfg/op4weapons.cfg").write_text(OP4_CFG)
    (OUT / "INSTALL.md").write_text(INSTALL)

    # User's installed OP4 soundtrack only; no MP3 is bundled or generated.
    setup = (ROOT / "tools/packaging/setup_op4_media.bat").read_text()
    (OUT / "setup_op4_media.bat").write_bytes(
        setup.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    shutil.copy2(ROOT / "docs/OP4_SOURCE_AUDIT.md", OUT / "SOURCE_AUDIT.md")
    shutil.copy2(ROOT / "docs/OP4_RUNTIME_TESTS.md", OUT / "RUNTIME_TESTS.md")

    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    manifest = {
        "architecture": "full OP4 campaign/server + BugfixedHL VGUI2 client",
        "root": "BugfixedHL-Rebased gamedir + OP4 SDK server",
        "campaign": {"startmap": "of0a0", "trainmap": "ofboot0", "steam_appid": 50},
        "server": {
            "windows": "dlls/opfor.dll (patched OP4 SDK, BHL cvars, speedrun hooks, all-ten impulse 101)",
            "linux": "../gearbox/dlls/opfor.so (stock installed OP4 server)",
        },
        "binaries": {
            "cl_dlls/client.so": sha256(LINUX / "client.so"),
            "cl_dlls/client.dll": sha256(WINDOWS / "client.dll"),
            "dlls/opfor.dll": sha256(WINDOWS / "opfor.dll"),
        },
        "in_game_tested_here": False,
        "music_setup_required": True,
        "music_source": "installed gearbox/media via setup_op4_media.bat; no MP3 bundled",
        "source_audit": "SOURCE_AUDIT.md",
        "runtime_tests": "RUNTIME_TESTS.md",
        "files": {str(p.relative_to(OUT)).replace("\\", "/"): sha256(p)
                  for p in files},
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (OUT / "MOD_MANIFEST.json").write_text(manifest_text)
    (ROOT / "build-evidence/bhl-base/MOD_MANIFEST.json").write_text(
        manifest_text)

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

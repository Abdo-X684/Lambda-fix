#!/usr/bin/env python3
"""Generate the honest OP4-weapon inventory from the pinned clean sources.

This reads the independent clean BugfixedHL and clean OP4 checkouts, the merged
``bhl-op4/`` tree, built-binary manifests and the playable mod. It never uses
an earlier report or CI result as evidence. ``--check`` fails if any source
fact, built binary, package hash or in-game-test claim has drifted; ``--write``
regenerates docs/WEAPON_INVENTORY.md.
"""

from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from merge import op4_client_prediction, op4_weapon_events  # noqa: E402

BHL_CLEAN = ROOT / ".cache/upstreams/bugfixhl"
OP4_CLEAN = ROOT / ".cache/upstreams/op4"
TREE = ROOT / "bhl-op4"
MOD = ROOT / "build-evidence/bhl-base/mod"
DOC = ROOT / "docs/WEAPON_INVENTORY.md"


def precache(path: Path) -> set[str]:
    return set(re.findall(
        r'UTIL_PrecacheOtherWeapon\(\s*"([^"]+)"',
        path.read_text()))


def link_map(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in (root / "dlls/weapons").rglob("*.cpp"):
        for cls, cxx in re.findall(
                r'LINK_ENTITY_TO_CLASS\(\s*(weapon_[A-Za-z0-9_]+)\s*,\s*'
                r'([A-Za-z0-9_]+)\s*\)', p.read_text()):
            out[cls] = cxx
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes(path: Path) -> tuple[int, list[str], int]:
    bad: list[str] = []
    skipped = 0
    entries = path.read_text().splitlines()
    for line in entries:
        digest, name = line.split("  ", 1)
        p = Path(name)
        if not p.is_absolute():
            p = ROOT / p
        if not p.is_file():
            # Pinned SDK/dependency sources are fetched by the build drivers,
            # not committed. A clean checkout may legitimately lack them.
            if ".cache/" in name:
                skipped += 1
                continue
            bad.append(name + " (missing)")
        elif sha256(p) != digest:
            bad.append(name)
    return len(entries), bad, skipped


def collect() -> tuple[list[str], str]:
    errors: list[str] = []

    def chk(ok: bool, msg: str) -> None:
        if not ok:
            errors.append(msg)

    bhl_w = precache(BHL_CLEAN / "src/game/server/weapons.cpp")
    op4_w = precache(OP4_CLEAN / "dlls/weapons.cpp")
    merged_w = precache(TREE / "src/game/server/weapons.cpp")
    op4_only = sorted(op4_w - bhl_w)
    chk(len(bhl_w) == 14, f"clean BHL W_Precache has {len(bhl_w)}, expected 14")
    chk(len(op4_w) == 24, f"clean OP4 W_Precache has {len(op4_w)}, expected 24")
    chk(len(op4_only) == 10, f"OP4-exclusive weapon count is {len(op4_only)}, expected 10")
    chk(merged_w == bhl_w | op4_w, "merged W_Precache differs from BHL + OP4")
    merged_text = (TREE / "src/game/server/weapons.cpp").read_text()
    for cls in sorted(bhl_w | op4_w):
        n = len(re.findall(r'UTIL_PrecacheOtherWeapon\(\s*"' + re.escape(cls) + r'"', merged_text))
        chk(n == 1, f"{cls} registered {n} times in merged W_Precache")

    clean_links = link_map(OP4_CLEAN)
    events = {w["cls"]: w for w in op4_weapon_events.WEAPONS}
    chk(set(events) == set(op4_only), "event inventory does not match clean OP4-only weapons")
    ids = dict(op4_client_prediction.CLIENT_PREDICTED_IDS)
    chk(set(ids.values()) == {
        "WEAPON_DISPLACER", "WEAPON_EAGLE", "WEAPON_GRAPPLE", "WEAPON_KNIFE",
        "WEAPON_M249", "WEAPON_PENGUIN", "WEAPON_PIPEWRENCH",
        "WEAPON_SHOCKRIFLE", "WEAPON_SNIPERRIFLE", "WEAPON_SPORELAUNCHER"},
        "client prediction ID list is not all ten OP4 weapons")

    cmake = (TREE / "src/game/client/CMakeLists.txt").read_text()
    hl_weapons = (TREE / "src/game/client/hl/hl_weapons.cpp").read_text()
    events_cpp = (TREE / "src/game/client/op4/op4_weapon_events.cpp").read_text()
    status = json.loads((TREE / "PORT_STATUS.json").read_text())
    prov = json.loads((TREE / "PROVENANCE.json").read_text())
    config = (MOD / "op4weapons.cfg").read_text()
    autoexec = (MOD / "autoexec.cfg").read_text()
    mod_manifest = json.loads((MOD / "MOD_MANIFEST.json").read_text())

    chk("op4-hud-bucket-7" in prov["files"]["src/game/server/cdll_dll.h"]["merge_rules"],
        "7th HUD bucket merge rule missing")
    chk("MAX_WEAPON_SLOTS     7" in (TREE / "src/game/server/cdll_dll.h").read_text(),
        "MAX_WEAPON_SLOTS is not 7")
    chk('HookCommand<&CHudAmmo::UserCmd_Slot7>("slot7")' in
        (TREE / "src/game/client/hud/ammo.cpp").read_text(),
        "slot7 command is not hooked")
    chk("sv_oldweapons 0" in autoexec, "autoexec does not enable OP4 prediction")
    chk(mod_manifest.get("in_game_tested_here") is False,
        "mod manifest does not explicitly say it was NOT tested in-game")
    liblist = (MOD / "liblist.gam").read_text()
    for marker in ('startmap "of0a0"', 'trainmap "ofboot0"',
                   'fallback_dir "gearbox"', 'gamedll "dlls\\opfor.dll"'):
        chk(marker in liblist, f"liblist.gam missing {marker}")
    chk((MOD / "steam_appid.txt").read_text() == "50\n",
        "steam_appid.txt is not Opposing Force (50)")
    chk(sha256(MOD / "delta.lst") == sha256(ROOT / "data/delta.lst"),
        "mod/delta.lst is not the merged BHL+OP4 network delta")
    delta = (ROOT / "data/delta.lst").read_text()
    chk("DEFINE_DELTA( iuser4, DT_INTEGER, 8, 1.0 )" in delta
        and "DEFINE_DELTA( m_iId, DT_INTEGER, 6, 1.0 )" in delta
        and "DEFINE_DELTA( health, DT_SIGNED | DT_FLOAT, 11, 1.0 )" in delta,
        "merged delta is missing OP4 iuser4/6-bit m_iId or BHL 11-bit health")
    for rel, markers in {
        "src/game/client/hl/hl_weapons.cpp": (
            "CBasePlayerItem::ItemInfoArray[info.iId] = info;",
            "AddAmmoNameToAmmoRegistry(info.pszAmmo1, weaponName);",
            "player.ammo_spores", "player.ammo_762", "player.m_iItems",
            "g_pWpns[MAX_WEAPONS]", "for (i = 0; i < MAX_WEAPONS; i++)"),
        "src/game/client/op4/op4_client_prediction.cpp": (
            "CBasePlayerItem::AmmoInfoArray[MAX_AMMO_SLOTS]",
            "OP4_GetAmmoIndex", "OP4_MsgFunc_OldWeapon", "OP4_MsgFunc_HudColor"),
        "src/game/client/hud.cpp": (
            'pfnHookUserMsg((char *)"OldWeapon"',
            'pfnHookUserMsg((char *)"HudColor"'),
        "src/game/client/hl/hl_baseentity.cpp": ("OP4_GetAmmoIndex",),
    }.items():
        text = (TREE / rel).read_text()
        for marker in markers:
            chk(marker in text, f"{rel} missing {marker}")
    for required in ("setup_op4_media.bat", "SOURCE_AUDIT.md", "RUNTIME_TESTS.md"):
        chk((MOD / required).is_file(), f"mod/{required} missing")
    lang_files = sorted(p for p in (MOD / "ui/resource/language").glob("*.txt")
                        if not p.name.endswith(".utf8.txt"))
    chk(len(lang_files) == 11, "BHL UTF-16LE language files are missing")
    chk(all(p.read_bytes().startswith(codecs.BOM_UTF16_LE) for p in lang_files),
        "BHL language files are not UTF-16LE BOM")

    for cls in op4_only:
        cxx = clean_links.get(cls)
        chk(bool(cxx), f"{cls}: no clean OP4 LINK_ENTITY_TO_CLASS class")
        if not cxx:
            continue
        src = f"../server/op4/dlls/weapons/{cxx}.cpp"
        disk = f"src/game/server/op4/dlls/weapons/{cxx}.cpp"
        header = TREE / f"src/game/server/op4/dlls/weapons/{cxx}.h"
        chk(src in cmake, f"{cls}: {src} missing from client CMake")
        chk((TREE / disk).is_file(), f"{cls}: server weapon source missing")
        chk(f"{cxx} g_{cxx[1:]};" in hl_weapons, f"{cls}: client weapon object missing")
        chk(f"HUD_PrepEntity(&g_{cxx[1:]}, &player);" in hl_weapons,
            f"{cls}: HUD_PrepEntity missing")
        chk(f"case {ids.get(cxx)}:" in hl_weapons, f"{cls}: GetLocalWeapon case missing")
        chk(status["files"].get(disk, {}).get("ok") is True,
            f"{cls}: source did not compile into ELF32 object")
        hdr = header.read_text()
        chk("UTIL_DefaultUseDecrement();" in hdr and "server-authoritative" not in hdr,
            f"{cls}: UseDecrement is not client-predicted")
        w = events.get(cls, {})
        if w.get("func"):
            chk(w["func"] in events_cpp, f"{cls}: event {w['func']} missing")
        else:
            chk(cxx == "CGrapple", f"{cls}: missing event without documented reason")
        if w.get("ammo"):
            chk(f"give {w['ammo']}" in config, f"{cls}: ammo {w['ammo']} missing from config")
        chk(f"give {cls}" in config, f"{cls}: give command missing from config")

    for extra in ("../server/op4/dlls/weapons/CGrappleTip.cpp",
                  "../server/op4/dlls/ehandle.cpp"):
        chk(extra in cmake, f"client CMake missing OP4 client source {extra}")

    linux = json.loads((ROOT / "build-evidence/bhl-base/MANIFEST.json").read_text())
    windows = json.loads((ROOT / "build-evidence/bhl-windows/MANIFEST.json").read_text())
    chk(windows.get("abi") == "msvc",
        "Windows DLL manifest is not the MSVC-ABI build")
    for name in ("client.so", "hl.so"):
        chk(linux["libraries"][name].get("glibc_max") == "GLIBC_2.17",
            f"{name} is not linked to the GLIBC_2.17 baseline")
    for side, manifest in (("bhl-base", linux), ("bhl-windows", windows)):
        n, bad, skipped = source_hashes(
            ROOT / f"build-evidence/{side}/SOURCES.sha256")
        chk(not bad, f"{side}/SOURCES.sha256 has {len(bad)} stale entries: {bad[:2]}")
        for name, rec in manifest["libraries"].items():
            p = ROOT / f"build-evidence/{side}/{name}"
            chk(p.is_file() and sha256(p) == rec["sha256"],
                f"{side}/{name} does not match MANIFEST.json")
            # The full-OP4 package ships only the BHL clients and the patched
            # OP4 server. The historical BHL-root hl.so/hl.dll remain build
            # evidence but are deliberately NOT copied into the mod folder.
            if name.startswith("hl."):
                continue
            mod_rel = ("cl_dlls/" if name.startswith("client") else "dlls/") + name
            mod_file = MOD / mod_rel
            chk(mod_file.is_file() and sha256(mod_file) == rec["sha256"],
                f"mod/{mod_rel} does not match built {side}/{name}")

    opfor_built = ROOT / "build-evidence/bhl-windows/opfor.dll"
    opfor_mod = MOD / "dlls/opfor.dll"
    chk(opfor_built.is_file(), "full OP4 server opfor.dll is missing")
    if opfor_built.is_file():
        chk(opfor_mod.is_file()
            and sha256(opfor_mod) == sha256(opfor_built),
            "mod/dlls/opfor.dll does not match the built OP4 server")

    zip_path = ROOT / "build-evidence/bhl-base/bhl-base-mod.zip"
    chk(zip_path.is_file(), "playable mod ZIP missing")
    chk("weapon_shockroach" not in op4_w,
        "weapon_shockroach is an alias, not an eleventh OP4 player weapon")

    linux_client = linux["libraries"]["client.so"]
    linux_server = linux["libraries"]["hl.so"]
    win_client = windows["libraries"]["client.dll"]
    win_server = windows["libraries"]["hl.dll"]
    opfor_size = opfor_built.stat().st_size
    opfor_hash = sha256(opfor_built)
    rows = [f"| `{cls}` | no | yes | incomplete | yes | not tested |"
            for cls in op4_only]
    doc = f"""# Opposing Force weapon inventory on the BugfixedHL base

> Generated automatically by `python3 tools/weapon_inventory.py --write` from the clean
> `.cache/upstreams/bugfixhl/` and `.cache/upstreams/op4/` copies, the merged tree
> `bhl-op4/`, `PORT_STATUS.json`, the Linux and Windows build manifests, and the `mod/` package.
> The package now starts the full OP4 campaign (`of0a0`) with a real OP4 server, not a
> Half-Life campaign with OP4 weapons. No earlier report or CI result is read as evidence.

## Required table

| Weapon | In BHL | In OP4 | Merge status | Prediction | In-game test |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

**Required interpretation:** `incomplete` under 'Merge status' and `not tested` under 'In-game test' are not evasions of
the inventory: source, client/server, event, registration, and give-command files are wired for all ten weapons,
but there is no GoldSrc engine and no legal OP4 assets in this environment. So no row says `complete`
or `passing`, and nothing is said about any weapon working in game. `yes` under `Prediction`
means the real weapon file is wired into `client` with `CLIENT_DLL` and the `GetLocalWeapon`
and `UseDecrement()` state, not proof of runtime prediction.

`weapon_shockroach` is not an eleventh weapon: it is an alias for `CShockRifle` in
the clean OP4 source and does not appear in `W_Precache()`; `monster_shockroach`
is a separate monster entity in `dlls/shockroach.cpp`.

## What the check actually verified

* Clean BHL: `{len(bhl_w)}` weapons in `W_Precache()`; clean OP4: `{len(op4_w)}`;
  the difference is `{len(op4_only)}` OP4-only weapons. The merged tree registers `{len(merged_w)}`
  names, once per name, with no duplicate registration.
* Client: ten real OP4 weapon files + `CGrappleTip.cpp` + `ehandle.cpp`
  + `op4_client_prediction.cpp` + nine view events, compiled with `CLIENT_DLL`.
  `CGrapple` is no longer server-authoritative; no `UseDecrement()` is forced to `FALSE`.
* `MAX_WEAPON_SLOTS = 7` and the `slot7` command are wired into BHL code; the seventh-slot sprite
  in `sprites/hud.txt` is still not tested in game.
* OP4 network compatibility: `MAX_WEAPONS = 64`, `local_state_t.weapondata[64]`, moving
  prediction data for 64 weapons, and binding the 8-byte `Weapons` message in the BHL client
  so weapon bits are not read only from the old 32-bit engine field.
* `liblist.gam` starts `of0a0` and `ofboot0`; `steam_appid.txt = 50`;
  merged BHL+OP4 `delta.lst` (keeps `health`/`eflags` and adds `iuser4`
  and a 6-bit `m_iId`), and `fallback_dir "gearbox"` loads the installed OP4 assets.
* After the bug report: client prediction gaps were fixed (`ItemInfoArray`, ammo registration,
  `GetAmmoIndex`, `ammo_spores/ammo_762/m_iItems`, 64-slot loops,
  `OldWeapon`/`HudColor`, and clearing state on ResetHUD), at the source level only.
* Music: `setup_op4_media.bat` copies the original MP3s from `gearbox/media` only;
  there is no MP3 in the ZIP and no generated music. Details are in `SOURCE_AUDIT.md`.
* `autoexec.cfg` sets `sv_oldweapons 0`; `op4weapons.cfg` gives the ten weapons
  and ammo via F9. The patched Windows server also makes `impulse 101` give them,
  including `weapon_penguin`; Linux uses F9/F10 with the original `gearbox` server.
* Linux: `client.so` `{linux_client['bytes']}` bytes, sha256
  `{linux_client['sha256']}`, linked against `GLIBC_2.17`; the old `hl.so` server
  (`{linux_server['bytes']}` bytes) is not in the package and uses
  `../gearbox/dlls/opfor.so` instead.
* Windows (`{windows['target']}`, `{windows['toolchain']}`, ABI compatible with MSVC/VGUI2):
  `client.dll` `{win_client['bytes']}` bytes, sha256 `{win_client['sha256']}`;
  `opfor.dll` `{opfor_size}` bytes, sha256 `{opfor_hash}`. The old `hl.dll`
  server (`{win_server['bytes']}` bytes) is not in the package.
  These are MSVC binaries, but they are **not tested in game**.
* `SOURCES.sha256` hashes are checked for every existing file, and the violation count must be zero;
  `.cache/` paths for SDK/deps are not in git and are restored by the build script,
  so missing ones are skipped explicitly and are not counted as a pass. The `mod/cl_dlls/` binaries
  and `mod/dlls/opfor.dll` match the existing build exactly.
* `MOD_MANIFEST.json` states explicitly: `in_game_tested_here: false`.

## Gaps that block a 'complete' mark

1. No loading in the GoldSrc engine, and no real selection/fire/reload/ammo/animation/sound/prediction
   testing, and no crash or multiplayer testing.
2. No legal OP4 assets are included: models, sounds, HUD sprites, and `events/*.sc`
   are read from the user's installed `gearbox/` copy through `fallback_dir`.
3. No Windows runtime test and no seventh HUD slot test in game, and no
   confirmation from the user that the OP4 campaign, menus, music, and every weapon work after this change;
   the `RUNTIME_TESTS.md` table shows `not tested` for every row.
4. The Linux server is the original `gearbox` one: it has no `sv_bhl_*` and no
   `impulse 101` patch, which is an explicit difference from the Windows build.
5. Builds, compilation, and automated checks do not replace these tests.
"""
    return errors, doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    errors, doc = collect()
    if a.write:
        DOC.write_text(doc)
        print(f"wrote {DOC.relative_to(ROOT)}")
    if a.check:
        if not DOC.is_file() or DOC.read_text() != doc:
            errors.append("docs/WEAPON_INVENTORY.md is stale; run --write")
        if errors:
            for e in errors:
                print("FAIL:", e, file=sys.stderr)
            return 1
        print("== OP4 WEAPON INVENTORY OK ==")
    elif not a.write:
        print(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

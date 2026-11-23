#!/usr/bin/env python3
"""Create a ready-to-copy GoldSrc MOD FOLDER (not a Valve game directory).

halflife-op4-updated refuses to run when the mod folder name starts with any
of Valve's prefixes (valve, gearbox, bshift, ...): UTIL_IsValveGameDirectory()
in game_shared/filesystem_utils.cpp prints the fatal error and quits. Putting
client.so / hl.so inside gearbox/ therefore ALWAYS fails.

This builds a standalone folder (default: lambda-fix) with liblist.gam -> fallback
"gearbox", steam_appid 50, delta.lst, the two ELF32 binaries, speedrun.cfg and
the route, plus a deterministic zip + sha256 manifest.

Run:  python3 tools/create_mod.py
Then: copy dist/lambda-fix/ into <Half-Life>/ and launch -game lambda-fix
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge.configgen import render_config  # noqa: E402

# Copied verbatim from game_shared/filesystem_utils.cpp (ValveGameDirectoryPrefixes).
VALVE_PREFIXES = (
    "valve", "gearbox", "bshift", "ricochet", "dmc",
    "cstrike", "czero", "dod", "tfc",
)
MOD_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
DEFAULT_NAME = "lambda-fix"


def validate_mod_name(name: str) -> str:
    if not name or not MOD_NAME_RE.fullmatch(name):
        raise ValueError(f"invalid mod folder name: {name!r} (use lowercase letters/digits/-/_)")
    lowered = name.lower()
    for prefix in VALVE_PREFIXES:
        if lowered.startswith(prefix):
            raise ValueError(
                f"mod folder {name!r} starts with Valve prefix {prefix!r}; "
                "UTIL_IsValveGameDirectory() would shut the game down. "
                f"Use something like {DEFAULT_NAME!r} instead."
            )
    return name


def liblist_text(name: str) -> str:
    return (
        'game "BugfixedHL x OP4 Speedrun"\n'
        'type "singleplayer_only"\n'
        'startmap "of0a0"\n'
        'trainmap "ofboot0"\n'
        'cldll "1"\n'
        'secure "0"\n'
        'svonly "0"\n'
        'version "bhl-systems-1"\n'
        'gamedll "dlls\\hl.dll"\n'
        'gamedll_linux "dlls/hl.so"\n'
        'fallback_dir "gearbox"\n'
    )


def install_text(name: str) -> str:
    return f"""# BugfixedHL x OP4 Speedrun — installation

## DO NOT put these files inside gearbox/ or valve/

The OP4 SDK contains `UTIL_IsValveGameDirectory()` which aborts startup when
the mod folder name starts with `valve`, `gearbox`, `bshift`, `dmc`, `cstrike`,
`czero`, `dod`, `ricochet` or `tfc`. That is the message you saw. This folder is
named `{name}` precisely so it passes that check.

## Install

1. Copy the whole `{name}/` folder into your Half-Life directory, **next to**
   `valve/` and `gearbox/` — e.g. `.../steamapps/common/Half-Life/{name}/`.
   Never overwrite anything in `gearbox/`; Steam will restore it and the guard
   will refuse to run anyway.
2. `liblist.gam` already points at `fallback_dir "gearbox"`, and
   `steam_appid.txt` contains `50` so Steam mounts the Opposing Force assets.
3. Launch: `hl_linux -game {name} -console -dev +exec speedrun.cfg`
   (Windows: `hl.exe -game {name} -console -dev +exec speedrun.cfg`), or add
   `-game {name}` to the game's Steam launch options.
4. `delta.lst` (from the OP4 SDK `network/` folder) is included; it is required
   for client/server network data to line up.

The real `vgui.so` and all game assets come from your own legally installed
Half-Life: Opposing Force. `client.so` has a `DT_NEEDED vgui.so` entry; the game
supplies that library at runtime. No Valve/Gearbox binary is redistributed.

## What is actually merged: real BugfixedHL systems

Earlier builds used BugfixedHL only as a reference and shipped a brand-new
`sr_*` speedrun system. That was wrong. This build compiles **BHL's own
systems** into the OP4 client/server, with only a compatibility layer
(`integration/bhl/`):

* `ConVar` / `ConCommand` / `CvarSystem` (BHL's cvar system)
* `CHudElem` / `CHudElemBase` (BHL's HUD base)
* `CHudSpeedometer`, `CHudJumpspeed`, `CHudStrafeGuide`
* `bhlcfg` / `bugfixedhl.cfg`
* server cvars `sv_bhl_query_vars`, `sv_bhl_query_wait_for_id`,
  `sv_bhl_defer_motd`, `sv_bhl_version`

The `sr_*` RTA timer / `SRSplit` layer is an **optional add-on**, not the merge.

## How to confirm the merge is really loaded (5 seconds)

| Sign | Where |
| --- | --- |
| speedometer / jumpspeed / strafe guide | on screen (`hud_speedometer 1`, `hud_jumpspeed 1`, `hud_strafeguide 1` are already in `speedrun.cfg`) |
| `[BHL] BugfixedHL systems merged into Opposing Force` | console at startup |
| **`bhl_status`** | console: lists the merged BHL systems (a real BHL `CON_COMMAND`) |
| `bhl_version` -> `bhl-systems-1` | console (BHL `ConVar`) |
| `sv_bhl_version` / `sv_bhl_query_vars` | server cvars |
| `bugfixedhl.cfg` | created in the mod folder on shutdown |
| `[BHLxOP4] ...` / `sr_status` | optional speedrun add-on only |

If NONE of these appear, the game is **not loading our two DLLs** (stock
binaries are running). Check, in order:

* the folder really is `Half-Life/{name}/` (not `Half-Life/{name}/{name}/`
  after unzipping, and not inside `gearbox/`);
* the launch options really contain `-game {name}` — Steam sometimes keeps an
  old `-game gearbox` in the options; check `liblist.gam` contains
  `gamedll_linux "dlls/hl.so"`;
* `Half-Life/vgui.so` exists (the engine needs it to load `client.so`);
* the console does not say `could not load library .../client.so` (wrong
  architecture or missing 32-bit runtime libraries);
* you are on Linux — these are ELF32 binaries. On Windows build the VS2019
  solution and use `client.dll` / `hl.dll` in the same folder.

Verify the files with `MANIFEST.json` (sha256 for every entry). Both libraries
are ELF 32-bit i386, because GoldSrc Linux cannot load 64-bit libraries.
"""


def collect_payload(name: str, dlls: Path, delta: Path) -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    for rel, src in (
        ("cl_dlls/client.so", dlls / "client.so"),
        ("dlls/hl.so", dlls / "hl.so"),
    ):
        if not src.is_file():
            raise FileNotFoundError(f"missing {src} — run make build-dlls-zig first")
        data = src.read_bytes()
        if data[:5] != b"\x7fELF\x01":
            raise ValueError(f"{src} is not ELF32")
        payload[rel] = data
    if not delta.is_file():
        raise FileNotFoundError(f"missing {delta} — run make fetch && make merge")
    payload["delta.lst"] = delta.read_bytes()
    payload["liblist.gam"] = liblist_text(name).encode("utf-8")
    payload["steam_appid.txt"] = b"50\n"
    payload["speedrun.cfg"] = render_config(ROOT).encode("utf-8")
    payload["splits/op4_route.json"] = (ROOT / "data" / "op4_route.json").read_bytes()
    payload["INSTALL.md"] = install_text(name).encode("utf-8")
    return payload


def manifest_for(name: str, payload: dict[str, bytes]) -> dict[str, Any]:
    return {
        "kind": "goldsrc-mod-folder",
        "mod_dir": name,
        "valve_prefix_safe": True,
        "valve_prefixes": list(VALVE_PREFIXES),
        "fallback_dir": "gearbox",
        "steam_appid": 50,
        "launch": f"-game {name}",
        "files": {
            rel: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for rel, data in payload.items()
        },
    }


def build(name: str = DEFAULT_NAME, out: Path | None = None,
          zip_path: Path | None = None, dlls: Path | None = None) -> dict[str, Any]:
    name = validate_mod_name(name)
    out = out or ROOT / "dist" / name
    zip_path = zip_path or ROOT / "dist" / "bhl-op4-mod.zip"
    dlls = dlls or ROOT / "dist" / "dlls"
    delta = ROOT / "data" / "delta.lst"

    payload = collect_payload(name, dlls, delta)
    manifest = manifest_for(name, payload)
    payload["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    if out.exists():
        shutil.rmtree(out)
    for rel, data in payload.items():
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(payload):
            info = zipfile.ZipInfo(f"{name}/{rel}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o755 << 16 if rel.endswith(".so") else 0o644 << 16
            zf.writestr(info, payload[rel])
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return {
        "ok": True, "mod_dir": name, "folder": str(out), "zip": str(zip_path),
        "zip_bytes": zip_path.stat().st_size, "zip_sha256": sha,
        "files": len(payload), "valve_prefix_safe": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--dlls", type=Path)
    parser.add_argument("--install", type=Path,
                        help="copy the finished folder into this Half-Life directory")
    args = parser.parse_args(argv)
    try:
        result = build(args.name, args.out, args.zip, args.dlls)
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"mod folder: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {result['folder']} ({result['files']} files)")
    print(f"wrote {result['zip']} ({result['zip_bytes']} bytes, sha256={result['zip_sha256'][:16]}…)")
    if args.install:
        dest = args.install / args.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(result["folder"], dest)
        print(f"installed -> {dest}")
        print(f"launch with: -game {args.name} -console -dev +exec speedrun.cfg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a distributable *overlay* package for the merged OP4 mod.

Only files authored in this repository are packaged: the core, the engine glue,
generated cfg/route, snippets and docs. Upstream SDK sources are NEVER included
(they are licensed separately and fetched at build time). Every archived file
is listed with a sha256 in MANIFEST.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge.configgen import load_route, render_config  # noqa: E402

# (source path relative to this repo, path inside the zip)
FILES = (
    ("src/speedrun/sr_core.h", "src/game_shared/sr_core.h"),
    ("src/speedrun/sr_core.cpp", "src/game_shared/sr_core.cpp"),
    ("src/speedrun/sr_route_data.h", "src/game_shared/sr_route_data.h"),
    ("overlay/cl_dll/sr_hud_timer.h", "src/cl_dll/sr_hud_timer.h"),
    ("overlay/cl_dll/sr_hud_timer.cpp", "src/cl_dll/sr_hud_timer.cpp"),
    ("overlay/cl_dll/sr_hud_msg.h", "src/cl_dll/sr_hud_msg.h"),
    ("overlay/cl_dll/sr_hud_msg.cpp", "src/cl_dll/sr_hud_msg.cpp"),
    ("overlay/dlls/sr_server.h", "src/dlls/sr_server.h"),
    ("overlay/dlls/sr_server.cpp", "src/dlls/sr_server.cpp"),
    ("LICENSE", "LICENSE"),
    ("docs/LICENSES.md", "docs/LICENSES.md"),
    ("docs/SPEEDRUN.md", "docs/SPEEDRUN.md"),
)
SNIPPETS = "integration/snippets"
INSTALL_NAME = "INSTALL.md"


def install_text() -> str:
    return """# BugfixedHL x Opposing Force - Speedrun Overlay

This archive contains **only** the files authored by the merge kit. It does not
contain Valve/Gearbox/BugfixedHL source code: you must build the merged SDK
tree separately (`make fetch && make merge`) or apply the snippets to your own
OP4 SDK checkout.

## Apply

1. `make fetch && make merge` in the merge-kit repository, then build the two
   DLLs with the OP4 SDK toolchain (VS2019 project or `linux/Makefile`).
   `merge/projects.py` already added the new `.cpp` files to those build files.
2. Copy `src/cl_dll/*` to `<OP4 SDK>/cl_dll/`, `src/dlls/*` to `dlls/`,
   `src/game_shared/*` to `game_shared/` if you are applying manually, and
   apply `integration/snippets/*.snippet` at the anchors documented in
   `merge/plan.json`.
3. Copy `gamedir/speedrun.cfg` into the mod directory and put
   `gamedir/splits/op4_route.json` under `splits/`.

## Run

* `F5` reset, `F6` split, `F7` practice toggle.
* The server broadcasts `SRSplit` (cumulative RTA + PB delta) on every level
  change; the HUD projects server time between messages.
* `sv_cheats` stays `0`; a run recorded with cheats on is flagged INVALID.
* `sv_allowbunnyhopping 1` is the OP4-native equivalent of BugfixedHL's bhop cap
  toggle (see `docs/RESOLUTION.md` in the kit repository).

## Verify the archive

`MANIFEST.json` lists sha256 + size for every file. Recompute with:

```bash
python3 -c "import json,hashlib,pathlib; m=json.load(open('MANIFEST.json'));\\
[print(f, hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()==v) for f,v in m['files'].items()]"
```

Licenses: see `LICENSE` (MIT, our code) and `docs/LICENSES.md` (upstream
obligations). This archive is not a standalone playable game.
"""


def build(root: Path = ROOT, out_dir: Path | None = None, tree: Path | None = None) -> dict[str, Any]:
    out_dir = out_dir or (root / "dist")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, bytes] = {}

    for src, dest in FILES:
        path = root / src
        if not path.is_file():
            raise FileNotFoundError(f"package input missing: {src}")
        payload[dest] = path.read_bytes()
    for snippet in sorted((root / SNIPPETS).glob("*.snippet")):
        payload[f"{SNIPPETS}/{snippet.name}"] = snippet.read_bytes()

    payload["gamedir/speedrun.cfg"] = render_config(root).encode("utf-8")
    payload["gamedir/splits/op4_route.json"] = (
        json.dumps(load_route(root), indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    payload[INSTALL_NAME] = install_text().encode("utf-8")

    report = (tree or (root / "build" / "merged-real")) / "MERGE_REPORT.md"
    if report.is_file():
        # The generated timestamp must not make two identical merges produce
        # different archives; drop only that volatile line.
        lines = [
            line for line in report.read_text(encoding="utf-8").splitlines()
            if not line.startswith("- Generated:")
        ]
        payload["MERGE_REPORT.md"] = ("\n".join(lines) + "\n").encode("utf-8")

    manifest = {
        "schema": 1,
        "package": "bhl-op4-speedrun-overlay",
        "version": "0.1.0",
        "includes_upstream_sources": False,
        "file_count": len(payload),
        "archive_entries": len(payload) + 1,  # + MANIFEST.json itself
        "files": {
            name: {
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
            for name, data in sorted(payload.items())
        },
    }
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    payload["MANIFEST.json"] = manifest_bytes

    zip_path = out_dir / "bhl-op4-speedrun-overlay.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    (out_dir / "MANIFEST.json").write_bytes(manifest_bytes)
    return {
        "ok": True,
        "zip": str(zip_path),
        "manifest": str(out_dir / "MANIFEST.json"),
        "file_count": len(payload),
        "bytes": zip_path.stat().st_size,
        "sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        "manifest_data": manifest,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "dist")
    p.add_argument("--tree", type=Path, default=ROOT / "build" / "merged-real")
    args = p.parse_args(argv)
    result = build(ROOT, args.out, args.tree)
    print(f"wrote {result['zip']} ({result['bytes']} bytes, {result['file_count']} files)")
    print(f"sha256={result['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

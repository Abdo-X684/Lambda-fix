# Architecture (current)

## Problem

| | BugfixedHL-Rebased | halflife-op4-updated |
|---|---|---|
| Layout | `src/game/{client,server,shared}`, `src/common` | `cl_dll`, `dlls`, `game_shared`, `common` |
| UI | VGUI2, split HUD, `ConVar` class | VGUI1, one `cl_dll/hud.cpp`, macros |
| Build | CMake | VS2019 vcxproj + Linux Makefiles |
| License | GPL-3.0 | Valve HLSDK (non-commercial) + TWHL |

Copying OP4's `cl_dll/hud.cpp` over BHL's `src/game/client/hud.cpp` would break both. So the project
does not merge the two trees as one block. It takes BHL as the base and applies OP4 content through
named, recorded rules.

## Layers

1. **Base tree**: `bhl-op4/`, a verbatim copy of BugfixedHL-Rebased with named merge rules applied.
   Every file has a provenance record in `bhl-op4/PROVENANCE.json`.
2. **Sources**: `merge/fetch.py` downloads the pinned upstreams (commit + sha256 checked, safe
   extraction) into `.cache/upstreams/`.
3. **Merge tooling**: `merge/bhl_base.py` produces `bhl-op4/` from the base and the OP4 tree
   (deterministic, rebuilt from scratch). `--check` verifies the provenance fingerprint and that every
   CMake-wired source is present and clean.
4. **Compilation evidence**: `tools/build_bhl_base.py` builds 32-bit `client.so` and `hl.so` with
   Zig's clang. `tools/verify_bhl_base.py --compile` compiles each source to an ELF32 object and writes
   `bhl-op4/PORT_STATUS.json`.
5. **Speedrun add-on** (optional): `src/speedrun/sr_core.{h,cpp}` is a C++17 core with no engine
   dependency. It contains the run timer, the route, splits, personal bests, and the server mirror. See
   [`SPEEDRUN.md`](SPEEDRUN.md).
6. **Packaging**: `tools/create_playable_mod.py` creates the standalone `lambda-fix/` mod folder and the zip
   with `MOD_MANIFEST.json` (sha256 for every file). The package never contains Valve assets.
7. **Web dashboard**: `web/app.py` (standard library `http.server`) and `web/markdown.py` (a safe Markdown
   renderer with no dependencies). The dashboard shows the merge status and the README/docs with a side
   index.

## Key decisions

* **Base is BugfixedHL**: OP4 systems and weapons are merged into BHL headers and sources, not the other
  way round. Earlier releases did the opposite and were corrected; see
  [`BHL_MERGE.md`](BHL_MERGE.md) and [`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md).
* **Named, mechanical transformations only**: each change to a source file is a named rule with a count
  in `PROVENANCE.json`. Function bodies come from OP4 unchanged.
* **Server authority**: the server owns the speedrun timer. The client HUD only displays the mirrored time.
* **Determinism**: `compute_tree_hash()` hashes `(path, content)` in a fixed order and excludes the report,
  so repeated runs give the same hash. Package zips use fixed timestamps.

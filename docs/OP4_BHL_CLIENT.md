# OP4-based BugfixedHL client (VGUI1) — status

**Direction (user decision, final attempt):** the base is the pinned
Opposing Force SDK `twhl-community/halflife-op4-updated @ 5368be7f`. BugfixedHL-Rebased
features are layered on top; no new mod is created. The VGUI2 conflict is
resolved by keeping OP4's VGUI1 menus and porting the gameplay features.

## What the generator does (`tools/build_op4_bhl.py`)

1. Copies the OP4 tree (`.cache/upstreams/op4`) unchanged.
2. Merges BHL systems via `merge.bhl` (speedometer, jumpspeed, strafeguide,
   `bhlcfg`/`bugfixedhl.cfg`, `sv_bhl_*` server cvars).
3. Adds BHL **autojump** (`cl_autojump`, `cl_autojump_priority`) and
   **ducktap** (`+ducktap`/`-ducktap`) to OP4's `cl_dll/input.cpp`, copied from
   BHL `src/game/client/input.cpp`. The PM accessors (`PM_GetOnGround`,
   `PM_GetWaterLevel`, `PM_GetMoveType`) are added to OP4 `pm_shared.cpp`.
4. Makes the OP4 VS projects build on `windows-2022` (toolset v143, no Steam
   post-build copy) and fetches the two pinned binary libs (`vgui.lib`,
   `SDL2.lib`) by SHA-256.
5. Writes `OP4_BHL_PROVENANCE.json` classifying every file as
   `op4-verbatim`, `op4-patched`, `bhl-copied`, or `generated-or-binary`.

Each feature edit is an anchored, count-checked replacement (the anchor must
match exactly once), so an upstream change fails loudly instead of silently
mis-merging.

## Static evidence (this sandbox)

* `python3 tools/build_op4_bhl.py --check` → OK: 828 files, 11 edits.
* Host `g++ -std=c++17 -fsyntax-only` over all client (`cl_dll`, `pm_shared`,
  particleman) and server (`dlls`, `dlls/weapons`) sources: **zero new errors
  against the unmodified OP4 base** (the two pre-existing errors in
  `GameStudioModelRenderer_Sample.cpp` and `overview.cpp` are identical in the base).

These are syntax checks only. They are NOT an MSVC build, not a link, and not
a runtime test.

## Build status — BLOCKED

* `.github/workflows/windows-op4-bhl-client.yml` pushed. Its run
  (`43266147753`, and dispatch `43266447256`) **did not start**: GitHub reports
  "recent account payments have failed or your spending limit needs to be
  increased". This is an account billing issue, not a code failure. All
  workflows on this account are blocked the same way (`CI` run `43266147487`).
* Until billing is fixed, no `client.dll` for this tree exists.

## Not yet verified

* MSVC compile/link of the OP4+BHL client (`hl_cdll.vcxproj`).
* Any in-game behaviour: weapons, music, autojump/ducktap, HUD. Nothing in
  this document is runtime-tested. The weapon/music table stays
  `غير مُختبَر`.

# integration/ports - reference only, NOT compiled

These files are copied from the pinned **BugfixedHL-Rebased** commit by
`merge/plan.json`. They document the upstream fixes we are porting
(auto demo recording, the `ConVar` class, the timer HUD) and are kept for
side-by-side review.

* They are **GPL-3.0** code (see `LICENSES.md` at the repository root).
* They are deliberately placed outside `cl_dll/`, `dlls/`, `game_shared/`,
  `common/` and `pm_shared/` so no build system picks them up.
* The shipped implementation is a clean-room core in
  `game_shared/sr_core.*` plus the thin engine glue in
  `cl_dll/sr_hud_timer.*` and `dlls/sr_server.*`.

Never `#include` these files into the mod. If you distribute the generated
merged tree, comply with the upstream licenses first.

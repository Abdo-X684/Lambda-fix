# BugfixedHL systems merged INTO Opposing Force — bhl-systems-1

> **Correction of the whole approach.** Earlier builds treated BugfixedHL as a
> *reference*: three "equivalence audits" said OP4 already had bunnyhop and
> client fixes, and a brand-new `sr_*` speedrun system was written from
> scratch. That is not what was asked. Asked: **merge the BHL systems, add
> compatibility shims, don't remove BHL**. This release does that.

## Real BHL systems now compiled inside the OP4 DLLs

| BHL system | Source (BugfixedHL-Rebased) | In OP4 tree |
| --- | --- | --- |
| `ConVar` / `ConCommand` / `CvarSystem` | `src/common/convar.{h,cpp}` | `cl_dll/bhl_compat.*` |
| `CHudElem` / `CHudElemBase` / `DEFINE_HUD_ELEM` | `src/game/client/hud/base.{h,cpp}` | `cl_dll/base.*` |
| `CHudSpeedometer` | `hud/speedometer.{h,cpp}` | `cl_dll/speedometer.*` |
| `CHudJumpspeed` | `hud/jumpspeed.{h,cpp}` | `cl_dll/jumpspeed.*` |
| `CHudStrafeGuide` | `hud/strafeguide.{h,cpp}` | `cl_dll/strafeguide.*` |
| `bhlcfg` / `bugfixedhl.cfg` | `bhlcfg.{h,cpp}` | `cl_dll/bhlcfg.*` |
| `sv_bhl_query_vars`, `sv_bhl_query_wait_for_id`, `sv_bhl_defer_motd`, `sv_bhl_version` | `CBugfixedServer.cpp` | `dlls/bhl_server.cpp` |

`integration/bhl/` carries the GPL-3.0 provenance banners. **Only** the
`bhl_compat` layer is new code: it maps BHL's modern `ConVar`/`CHudElem`/
`HudPart`/`CHud::GetHudColor` API onto OP4's 2001 `gEngfuncs`/`CHud`, and
`merge/bhl.py` injects the lifecycle hooks and patches the build files.
Full list of shims: `docs/BHL_MERGE.md`.

The `sr_*` RTA timer / `SRSplit` layer remains as an **optional add-on**; it is
no longer presented as the merge.

## Verify in 5 seconds

| Sign | Where |
| --- | --- |
| speedometer / jumpspeed / strafe guide | on screen (`hud_speedometer 1`, `hud_jumpspeed 1`, `hud_strafeguide 1` are in `speedrun.cfg`) |
| `[BHL] BugfixedHL systems merged into Opposing Force` | console at startup |
| **`bhl_status`** | console: lists the merged BHL systems (real BHL `CON_COMMAND`) |
| `bhl_version` -> `bhl-systems-1` | console (BHL `ConVar`) |
| `sv_bhl_version`, `sv_bhl_query_vars` | server cvars |
| `bugfixedhl.cfg` | written to the mod folder on shutdown |

## Install

Extract **`bhl-op4-mod.zip` next to** `valve/` and `gearbox/`
(`Half-Life/bhlop4/`) and launch
`hl_linux -game bhlop4 -console -dev +exec speedrun.cfg`.

**DO NOT copy `client.so`/`hl.so` into `gearbox/` or `valve/`.** The OP4 SDK's
`UTIL_IsValveGameDirectory()` aborts startup for any mod folder starting with
`valve`, `gearbox`, `bshift`, `dmc`, `cstrike`, `czero`, `dod`, `ricochet` or
`tfc`. `bhlop4/` + `fallback_dir "gearbox"` reads the OP4 assets without
modifying them. See `INSTALL.md` inside the zip for the full checklist.

| Asset | Size | Purpose |
| --- | --- | --- |
| `bhl-op4-mod.zip` | ~9.4 MB | complete, ready-to-copy mod folder |
| `client.so` | ELF32 | client binary with BHL systems (`cl_dlls/`) |
| `hl.so` | ELF32 | server binary with BHL cvars (`dlls/`) |
| `MANIFEST.json` | sha256 + ELF32 | verification |

Both are **ELF 32-bit i386**. `client.so` has `DT_NEEDED vgui.so`; the real
`vgui.so` and game assets come from your own legally installed Half-Life:
Opposing Force. No Valve/Gearbox binary is redistributed.

Reproduce: `make merge && make build-dlls-zig && make mod`.

**Licensing changed:** GPL-3.0 BHL code is now *compiled into* the binaries
(it used to be reference-only). Distribution of these binaries must comply with
GPL-3.0-or-later (`docs/LICENSES.md`). Kit code (`merge/`, `tools/`,
`src/speedrun/`, `web/`) stays MIT.

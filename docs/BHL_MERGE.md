# BugfixedHL actually merged into OP4 — not just a reference

> **Correction to an earlier path:** in releases `0.1.x`, BugfixedHL was used only as a *reference*.
> Three "parity audits" said OP4 already had bunnyhop and client fixes, and then a new `sr_*`
> system was built for speedrunning from scratch. That was a mistake in understanding the goal.
> The goal was: **merge the BHL systems themselves into OP4, and add only a compatibility layer**.
> Starting with `bhl-systems-1`, the real BHL systems are compiled into `client.so` and `hl.so`.

## What does "merging the systems" mean here?

OP4 (`twhl-community/halflife-op4-updated` @ `5368be7f`) is the base tree, unchanged.
On top of it, the BugfixedHL-Rebased systems (@ `4d32095e`, GPL-3.0) are moved over as they are,
plus a **compatibility layer** (`integration/bhl/`) that bridges the gap between modern BHL
(ConVar, CHudElem, VGUI) and the older OP4 code (`gEngfuncs`, `CHud`, `CVAR_CREATE`).
The system is not re-invented or replaced.

The merge is run by `python3 -m merge.bhl --tree build/merged-real`. `make merge` calls it
automatically after `merge.cli run`. Report:

## Systems moved over (compiled into the binaries)

| # | BHL system | Source | Where it lives in OP4 |
| --- | --- | --- | --- |
| 1 | `ConVar` / `ConCommand` / `CvarSystem` | `src/common/convar.h`, `convar.cpp` | `cl_dll/bhl_compat.{h,cpp}` |
| 2 | `CHudElem` / `CHudElemBase` / `DEFINE_HUD_ELEM` | `src/game/client/hud/base.{h,cpp}` | `cl_dll/base.{h,cpp}` |
| 3 | `CHudSpeedometer` (`hud_speedometer`) | `hud/speedometer.{h,cpp}` | `cl_dll/speedometer.*` |
| 4 | `CHudJumpspeed` (`hud_jumpspeed`) | `hud/jumpspeed.{h,cpp}` | `cl_dll/jumpspeed.*` |
| 5 | `CHudStrafeGuide` (`hud_strafeguide`) | `hud/strafeguide.{h,cpp}` | `cl_dll/strafeguide.*` |
| 6 | `bhlcfg` / `bugfixedhl.cfg` | `bhlcfg.{h,cpp}` | `cl_dll/bhlcfg.*` |
| 7 | `sv_bhl_query_vars`, `sv_bhl_query_wait_for_id`, `sv_bhl_defer_motd`, `sv_bhl_version` | `CBugfixedServer.cpp` | `dlls/bhl_server.cpp` |

Every file in `integration/bhl/` carries the source banner and the GPL-3.0 license. Edits marked
`COMPAT` are the only changes to BHL code.

## Compatibility layer (the only layer we wrote)

| Gap | Compatibility fix |
|---|---|
| BHL registers cvars in one batch via `CvarSystem::RegisterCvars()`, while OP4 uses `CVAR_CREATE` | `ConVar::GetCvar()` registers lazily and prefers an existing engine cvar (`pfnGetCvarPointer`) before creating a new one |
| `FCVAR_BHL_ARCHIVE`, `ALPHA_AMMO_*`, `HUD_DRAW_ALWAYS`, `FADE_TIME`, `M_PI` do not exist in OP4 | Constants in `bhl_compat.h` |
| BHL calls `gHUD.GetHudColor(HudPart::Common, …)`, `GetHudTransparency()`, `DrawHudNumberCentered()` | `merge/bhl.py` injects `enum class HudPart` and the declarations of the three functions into `cl_dll/hud.h`. The implementation is in `bhl_compat.cpp` (reads `giR/giG/giB` from OP4) |
| Modern `cl_dll.h` / `wrect.h` / `appversion.h` do not exist | Replaced by `bhl_compat.h` and `BHL_MERGE_VERSION` |
| OP4 builds with `-fno-exceptions` | The `try/catch` in `bhlcfg.cpp` was removed (the only one) |
| BHL creates HUD elements with `CHud::RegisterHudElem<T>()` | `BHL_Init()` creates `new CHudSpeedometer()` / `CHudJumpspeed()` / `CHudStrafeGuide()` and calls `Init/VidInit/Draw` |
| BHL updates speed from `V_CalcRefdef` | `BHL_OnRefdef(pparams)` is injected into `cl_dll/view.cpp`, making the same three calls as `BHL view.cpp:1686-1688` |
| BHL saves `bugfixedhl.cfg` on exit | `BHL_Shutdown()` is injected into `HUD_Shutdown()` |
| BHL server cvars need `IBugfixedServer` / Metamod | The original OP4 `cvar_t` + `CVAR_REGISTER`, with a load banner |
| OP4 requires explicit source lists | `merge/bhl.py` adds 6 client `.cpp` files and 1 server `.cpp` to `Makefile.hl_cdll`, `Makefile.hldll`, and `*.vcxproj` |

## Where did `sr_*` go?

The `sr_*` layer (RTA timer, `SRSplit`, `sr_status`) was an **optional add-on** built in
earlier releases. It is not "the merge". It stays because it works and does no harm, but:

* the merge title and UI are now about **BHL systems**;
* `bhl_status` (the real BHL command, via `CON_COMMAND`) is the verification reference;
* `hud_speedometer` / `hud_jumpspeed` / `hud_strafeguide` are enabled by default in
  `speedrun.cfg`;
* you can hide the add-on banner with `sr_hud_banner 0`; BHL stays visible.

## How do you check?

| Sign | Source |
|---|---|
| Speed meter / jumpspeed / strafe guide on screen | BHL systems, enabled with `hud_speedometer 1` … |
| `[BHL] BugfixedHL systems merged into Opposing Force` in the console | `BHL_Init()` |
| `bhl_status` | `CON_COMMAND` from BHL |
| `bhl_version` → `bhl-systems-1` | `ConVar` from BHL |
| `sv_bhl_version`, `sv_bhl_query_vars` on the server | `BHL_Server_Init()` |
| `bugfixedhl.cfg` is created in the mod folder | `bhlcfg::Shutdown()` |

`python3 -m merge.bhl --plan` lists the systems, and `make verify` checks that they exist in the
sources and binaries.

## Licenses

BugfixedHL-Rebased is under **GPL-3.0-or-later**. Its code is now compiled into the binaries, not
just kept as a reference file. So the resulting binaries are derived from GPL code and must be
handled accordingly (`docs/LICENSES.md`). The kit code (`src/speedrun`, `merge/`, `tools/`) stays
MIT. Valve/Gearbox assets and `vgui.so` are not distributed.

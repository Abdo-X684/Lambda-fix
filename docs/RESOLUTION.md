# How the earlier conflicts were resolved (historical)

> **Historical note.** This describes the earlier phase, when OP4 was the base tree and
> BugfixedHL was only a reference. That approach was replaced by the BHL-base merge
> described in [`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md). The numbers below are from
> that phase and do not describe the current tree.

## 1. Discovery

A three-way merge (vanilla HLSDK as the base, OP4 as "ours", BugfixedHL-Rebased as "theirs")
produced **127 conflicting hunks** in `pm_shared.cpp`, about 92 in `hud.cpp`, and about 127 in
`client.cpp`. The cause was not a semantic disagreement. BugfixedHL had rewritten these files
(modern C++, VGUI2, `ConVar`), so the shared base was too far away to produce a meaningful merge.

A code check showed that `halflife-op4-updated` (based on HLSDK Updated) **already contains** the
required fixes:

| BugfixedHL fix | Equivalent in OP4-updated | Evidence |
|---|---|---|
| `s_bBHopCap` + `PM_SetBHopCapEnabled` control `PM_PreventMegaBunnyJumping()` | `physinfo "bj"` is read in `PM_PreventMegaBunnyJumping()` and set from `sv_allowbunnyhopping` | `pm_shared/pm_shared.cpp:2551`, `dlls/client.cpp:985-1000`, `dlls/player.cpp:3131` |
| `BUNNYJUMP_MAX_SPEED_FACTOR` and the cap call from `PM_Jump` | Same constant and call | `pm_shared/pm_shared.cpp:2541,2565,2669` |
| Command-length guard in `ClientCommand` (crash prevention) | Same comment and `strncpy(...,127)` + `command[127]='\0'` | `dlls/client.cpp:670-686` |
| HUD state reset in `Init` (`m_pSpriteList=NULL`, `m_flTime=1.0`) | `m_iLogo=0`, `m_flTime=1.0`, constructor `m_pHudList(NULL)` | `cl_dll/hud.cpp:384,415`, `cl_dll/hud.h:719` |

Re-merging the files would have duplicated code or dropped OP4 code (CTF, `FlagIcons`, gamerules).
So the decision was: **no merge, but an equivalence audit plus wiring of the settings.**

## 2. Implementation

1. The three `three_way` rules in `merge/plan.json` were replaced with `audit` rules. Each one
   checks for specific patterns in an OP4 file and records `verdict`, `meaning`, `found`, `min`,
   and `evidence` with line references. A missing pattern produces an `anchor_drift` status, a
   warning, and a failure under `--strict`.
2. `bhl_bunnyhop` (not an OP4 cvar) was replaced by the real **`sv_allowbunnyhopping 1`** in
   `data/cvars.json`, `speedrun.cfg`, and `sr::RenderConfig`. `bhl_disable_selfgauss` was removed,
   because OP4 has no equivalent.
3. Features missing from OP4 were added as clean, tested code: `sr_core.*` (timer, splits, PB,
   server mirror), `sr_hud_timer.*`, `sr_hud_msg.*`, `sr_server.*`, and the `SRSplit` message
   registered in `dlls/UserMessages.cpp`.
4. `integration/ports/` remains a GPL-only review archive, outside the build paths.

## 3. Checks at that time

| Check | Result |
|---|---|
| Equivalence audits (offline and real) | 3/3 `equivalent`, 11 matching patterns |
| Conflict markers in `cl_dll/dlls/game_shared/pm_shared/common` | 0 |
| `g++ -fsyntax-only` on injected files and glue against the real SDK headers | 9/9 |
| Python / C++ tests | 131 / 77 |
| Tree fingerprint | Deterministic across two consecutive runs |

## 4. What stayed outside this repository

Linking `hl.dll` / `client.dll` with an HLSDK build tool and running the mod inside the game with the
Opposing Force assets needed an external build tool and the game files. Those cannot run inside the
repository. Current status: see [`ROADMAP.md`](ROADMAP.md).

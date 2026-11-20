# Speedrun layer design (optional add-on)

This is an **optional add-on** on top of BugfixedHL. It is not the merge itself (see
[`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md)).

## Timing

* `sr::IClock` can be injected: `SystemClock` (steady_clock) in the game, `FakeClock` in tests.
* `RunTimer` computes `now - start - paused_total`. Pausing does not add load time. Freezing at
  `of7a0` stops the run timer.
* `ServerMirror` on the client: `OnServerSplit(at, now)`, then
  `ProjectedMs(now2) = at + max(0, now2 - now)`. On `Freeze`, it stops for good.
* `FormatTime` outputs `M:SS.mmm` or `H:MM:SS.mmm`.

## Network: `SRSplit`

| Side | Behavior |
|---|---|
| Server | `gmsgSRSplit = REG_USER_MSG("SRSplit", -1)` in `LinkUserMessages()`. On each split: `MESSAGE_BEGIN(MSG_ALL, ...)`, then `WRITE_LONG(at)`, `WRITE_LONG(delta)`, `WRITE_BYTE(hasPb)`, `WRITE_STRING(map)`, `MESSAGE_END()` |
| Client | `HOOK_MESSAGE(SRSplit)` in `CHud::Init`. `__MsgFunc_SRSplit` reads with `BEGIN_READ/READ_*`, checks `READ_OK()`, then calls `SR_HUD_OnSplit(...)` |
| HUD | Shows `ServerMirror`, and the last split with the PB difference via `DrawConsoleString` |

`sr_net_splits 0` disables the broadcast for local tests.

## Route and splits

`data/op4_route.json` is the single source: 13 chapters and 39 maps. The Boot Camp
`ofboot0..ofboot4` is a separate category. `SplitAt(map)` rejects a stopped timer, an unknown map,
and going backwards. Skipping forward is allowed. `ParsePersonalBest` ignores damaged lines so that
one bad line cannot corrupt a whole PB file.

## Legitimacy

| Item | Mechanism |
|---|---|
| `sv_cheats` | `0` in the cfg. The server marks the run INVALID if it is enabled |
| `sr_practice_mode 1` | Prevents the run from counting as valid |
| Authority | The timer runs on the server and broadcasts `SRSplit`. The HUD is a mirror only |
| bunnyhop | `sv_allowbunnyhopping 1` (the OP4 equivalent of the BugfixedHL fix) |
| demo | `sr_autodemo 1` runs `record sr_run_<epoch>` at start or reset, and `stop` at the end |
| binds | `F5` reset, `F6` split, `F7` practice. Do not bind `Space` or `E` |

## Console commands

`sr_split`, `sr_reset`, and `sr_practice_toggle` are registered once, on the first `CWorld::Spawn`.
PB file: `map=ms` lines in `splits/op4_pb.txt`.

## Checks

`tools/verify_sdk.py`: 9 files compiled with `g++ -fsyntax-only` against the real OP4 headers, plus a
check that no conflict markers exist in any buildable source.

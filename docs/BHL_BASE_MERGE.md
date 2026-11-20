# The correct merge: **BugfixedHL is the base**, and OP4 is merged on top

> This is the **only architecture reference** after the course correction. Older documents
> (`BHL_MERGE.md`, `RESOLUTION.md`) describe the earlier approach, where **OP4 was the base**.

## 1. Why it was rebuilt

An explicit audit showed that the earlier output was not built on BHL:

* `client.so` contained only 4 BHL files out of 110 objects in the BHL client.
* `hl.so` contained **no** BHL code. `bhl_server.cpp` was written in this repository.
* `ConVar / CvarSystem` was a separate reimplementation (similarity `0.030` to `src/common/convar.cpp`).
* `MERGE_REPORT.json` said `merged=0`, and `plan.json` had zero `three_way` rules. No real merge
  happened between the two trees.

The goal was, and still is: **a project built on BHL that uses its files**, with the OP4 systems
and weapons merged into it. That is what `bhl-op4/` does now.

## 2. Structure (from `bhl-op4/PROVENANCE.json`)

| Layer | Source | Files | Status |
|---|---|---|---|
| **BASE** | `tmp64/BugfixedHL-Rebased @ 4d32095e3c33` (GPL-3.0) | **694** | **671 verbatim** (byte-identical to the commit; 6 of them carry recorded edits, see below) + **23** with declared merges |
| **ADD / MERGE** | `twhl-community/halflife-op4-updated @ 5368be7f8eba` | **154** | Weapons, CTF, rope, OP4 entities, client events |
| **GLUE** | this repository | **11** | `server/op4/`: `op4_compat.{h,cpp}`, `op4_compat_late.h`, `op4_link_fixups.cpp`, `op4_ctf_player.cpp`, `op4_entity_enumerator.h`; `client/op4/`: `op4_weapon_events.{h,cpp}`, `op4_client_prediction.cpp`; `shared/`: `op4_weapon_timing.{h,cpp}` |
| Source records | — | **859** entries | For each file: origin, `commit`, `sha256`, `action`, rule names |

The whole tree is **tracked in Git** inside `bhl-op4/` (not in the ignored `.cache/`), together
with `PROVENANCE.json`. `action` is one of `verbatim`, `verbatim+edit`, `bhl+op4-merge`,
`op4+compat-patch`, `compat-glue`, or `reference-only`.

`base.tree_sha256` is one fingerprint of all BHL files on disk (sorted `path  sha256` lines).
`--check` recomputes it from disk, so it does not depend on `.cache/` being present.

Driver: `python3 -m merge.bhl_base --out bhl-op4` (deterministic, rebuilds from scratch).
Checker: `python3 -m merge.bhl_base --check --out bhl-op4`.

**Recorded edits to BHL files** (the `verbatim+edit` entries): the auto-update entry is removed
from Advanced > About, and the default `hud_color` is set to OP4 green (`0 160 0`). These are
intentional, and they are the only BHL-origin files that differ from upstream.

## 3. Real merge rules inside BHL files

These are not a layer that imitates BHL. They are OP4 additions **inside the BHL headers
themselves** (named rules, 14 BHL files):

| # | BHL file | What was merged from OP4 |
|---|---|---|
| 1 | `src/game/server/weapons.h` | Extra OP4 constants from `dlls/weapons.h` |
| 2 | `src/game/server/weapons.h` | 3 bullet types: `BULLET_PLAYER_556/762/EAGLE` in `enum Bullet` |
| 3 | `src/game/server/weapons.h` | `#include "weaponinfo.h"` for `weapon_data_t` |
| 4 | `src/game/server/weapons.h` | `GetWeaponData/SetWeaponData/DecrementTimers/IncrementAmmo/GetNextAttackDelay` on `CBasePlayerWeapon` |
| 5 | `src/game/server/weapons.h` | `FindHullIntersection` declaration |
| 6 | `src/game/server/weapons.h` | `CLaserSpot::Spawn` made `public` (OP4 `CEagleLaser` inherits it) |
| 7 | `src/game/server/cdll_dll.h` | Full `enum WeaponId` (26 OP4 weapon IDs) |
| 8 | `src/common/const.h` | `enum WaterLevel` |
| 9 | `src/game/server/skill.h` | **All** missing `skilldata_t` fields (OP4 monster and CTF tuning) |
| 10 | `src/game/server/player.h` | OP4 state: `ammo_762`, `m_iTeamNum`, `m_WeaponBits`, CTF fields, `HasSuit()`, rope/autoaim |
| 11 | `src/game/server/basemonster.h` | Shock effect state (`AddShockEffect`, `UpdateShockEffect`, `ClearShockEffect`) |
| 12 | `src/game/server/cbase.h` | `CWorld::World`, `EHANDLE::Entity<T>()`, `MySquadTalkMonsterPointer()`, `PlaySentenceCore()` |
| 13 | `src/game/server/monsters.h` | OP4 `struct GibLimit` / `struct GibData` |
| 14 | `src/game/server/gamerules.h` | `IsCTF()` |
| 15 | `src/game/{server,client}/CMakeLists.txt` | OP4 sources whose compilation is proven are added to the BHL targets |
| 16 | `src/game/server/gamerules.h` | `IPointsForMonsterKill` / `MonsterKilled` (OP4 `dlls/gamerules.h:113,116`) |
| 17 | `src/game/server/monsters.h` | `CGib::SpawnRandomGibs(..., const GibData&)` declaration (OP4 `dlls/monsters.h:184`) |
| 18 | `src/game/server/cbase.h` | `byte m_EFlags` (OP4 `dlls/cbase.h:169`) |
| 19 | `src/game/server/game.cpp` + `src/game/shared/CMakeLists.txt` | cvar registration and the `FlagIcon` message; shared weapon-timing translation unit |

The core OP4 files (`dlls/{util,player,weapons,gamerules,skill,decals,...}`) are kept in
`src/game/server/op4/reference/` for reference only. They are not compiled and do not shadow BHL
headers. Their additions are the ones merged into BHL headers in the table above.

## 4. Compatibility layer (allowed, and named)

OP4 uses an updated HLSDK (`bool`, `override`, `Vector` as event arguments, `enum class`), while
BHL uses the original HLSDK interface (`int/BOOL`, `float *`). So **named, mechanical
transformations** are applied to OP4 sources. Each rule and its count is in `PROVENANCE.json`
(839 applications across 103 OP4 files):

* Rules derived from BHL's own headers: each function that BHL declares as `BOOL`/`int` and OP4
  declares as `bool` is converted to **the declared BHL type** (not a guessed type).
* `KeyValue` returns `void` in BHL. Its declarations are converted, and `return true/false` is
  removed only inside those function bodies (bracket-matched).
* `bool → BOOL` in the parameters of `CanPlaySentence`, `StopFollowing`, and
  `PlayScriptedSentence`, so they match the BHL virtual functions.
* `enum class CTFTeam → enum CTFTeam`. `CTFTeam::Name` stays valid and is accepted together with
  the `int` that BHL's player state uses.
* `Holster() → Holster(int skiplocal)`, `Vector::Normalize() → Normalized()`,
  `GET_PRIVATE<T>() → (T*)GET_PRIVATE()`, and a `CTFTeam` cast.
* "Late include" for `PLAYBACK_EVENT_FULL` and `FindHullIntersection`, so they do not break BHL's
  declarations (a macro defined after all the `#include`s).

**Function bodies are still OP4.** The `op4_compat.*` layer does not reimplement any BHL system.
It only provides OP4 functions that lived in `dlls/weapons.cpp` / `util.cpp` (which cannot be
compiled alongside BHL's copies), argument conversions, and missing OP4 constants.
`UTIL_IsCTF()` calls `g_pGameRules->IsCTF()`. The real CTF rules are created by
`InstallGameRules` and return `true`. CTF menu, `respawn`, cvar, and OP4 message bodies were added
in the glue file `op4_ctf_player.cpp` (text from `player.cpp` / `client.cpp` / `game.cpp`), and
`IsFacing` comes from `h_ai.cpp:196-210`. `ctfplay_gamerules.cpp` itself is wired in and is no
longer copied into glue.

## 5. Proof of compilation (not just file presence)

`python3 tools/verify_bhl_base.py --compile` compiles **every** OP4 source, and **every** BHL
server source copied verbatim, to a **real ELF32 object** (`zig c++ -target x86-linux-gnu -c`)
against the merged tree's headers. It records the result for each file in
`bhl-op4/PORT_STATUS.json` (the `files` and `bhl_base` sections).

Current result:

* **15 / 15 OP4 weapons compile** to ELF32 objects: `CDisplacer`, `CDisplacerBall`, `CEagle`,
  `CEagleLaser`, `CGrapple`, `CGrappleTip`, `CKnife`, `CM249`, `CPenguin`, `CPipewrench`,
  `CShockBeam`, `CShockRifle`, `CSniperRifle`, `CSpore`, `CSporeLauncher`.
  `readelf -h` on `CEagle.o`: `ELF32 / REL / Intel 80386`.
* **101 / 106 BHL server sources** (copied verbatim, not only headers) compile to ELF32 objects in
  the merged tree. The five that fail are listed in `PORT_STATUS.json` with reasons (`appversion.h`
  is generated by CMake, a Windows path in `stats.cpp`, `Make2D` from a different SDK, …). All real
  BHL sources compile in the actual build (`server: 179/179 clean`).
* **68 / 71** OP4 sources compile to ELF32 objects, including 15/15 weapons, CTF, rope, and
  entities (`CTFGoal`, `CTFSpawn`, `CRope`, `CRopeSegment`, `CDrillSergeant`, `hgrunt_medic`,
  `shocktrooper`, `voltigore`, …).
* **66 sources** are wired into `src/game/server/CMakeLists.txt`. The build target does not include
  a broken file or a file with a declared link gap. `--check` verifies that every wired file is
  clean (0 failures). The real build produced 179 server objects and zero link gaps.
* **25 `port_pending` files** (21 client, 4 server). The four that do not compile yet
  (`Wxdebug.cpp`, `squeakgrenade.cpp`, `world.cpp`, `ctf/ctfplay_gamerules.cpp`) and two clean
  sources that are excluded because they duplicate BHL systems (`UserMessages.cpp`) are explained
  in `PORT_STATUS.json`.

> `--check` fails if any CMake-wired source does not compile. A file that does not compile cannot
> be claimed as "merged".

## 6. Current state, stated plainly

1. **Real `client.so` / `client.dll` are built from `bhl-op4/`**: a BugfixedHL VGUI2 client with
   the ten OP4 weapons and their prediction, the OP4 server's `Weapons` message, and Linux linking
   against a `GLIBC_2.17` baseline. The `hl.so` / `hl.dll` built from the BHL root still exist as
   build evidence, but they are **not** the full OP4 campaign package: the HL server has no OP4
   entities or rules.
2. **The full campaign server** is `opfor.dll`, built from the OP4 SDK by
   `.github/workflows/windows-op4-server.yml` and `tools/prepare_op4_msvc_server.py`. It includes
   `sv_bhl_*`, the speedrun hooks, and `impulse 101` for all ten weapons. On Linux the package uses
   `../gearbox/dlls/opfor.so` from the user's own copy, so there is no Linux server build that
   carries the BHL systems yet.
3. The old OP4 client HUD sources (`hl_events`, `ev_hldm`, particleman) stay as reference because
   of the VGUI1 / VGUI2 differences. The real client is BHL VGUI2, not the stock OP4 client with
   patches. The critical OP4 messages are wired into the BHL client instead of importing the whole
   OP4 client.
4. `dist/dlls/*.so`, `dist/bhlop4/`, and `v0.1.0-linux32` come from the earlier **OP4-based** tree.
   They are **legacy** and are not evidence for the current package.
5. We do not claim that the mod is fully playable. Game assets and the real `vgui.so` are not
   included, and the user has not yet confirmed a run inside GoldSrc.

## 7. Licenses

BHL: **GPL-3.0**. OP4 / Valve HLSDK: the Valve license (free distribution only, no commercial use).
[`LICENSES.md`](LICENSES.md) explains the obligations. This repository **does not claim legal
compliance** for distributing any binary. Do not distribute binaries without reviewing both
licenses.

## 8. Commands

```bash
make fetch                                  # pinned trees + sha256
make bhl-base                               # rebuild bhl-op4/ from scratch
python3 tools/verify_bhl_base.py --compile  # ELF32 objects + PORT_STATUS.json
python3 tools/prepare_op4_msvc_server.py --check  # verify the OP4 server patches
make verify-bhl-base                        # PROVENANCE check + wired sources
python3 tools/create_playable_mod.py        # full OP4 campaign package
make verify                                 # all repository checks
```

## 9. Network compatibility: OP4 server and BHL client

The real OP4 server is not like the HL server. It has `MAX_WEAPONS = 64` and
`local_state_t.weapondata[64]`, and it sends the weapon bits in the user message `Weapons`
(8 bytes) instead of the 32-bit `client_data_t::iWeaponBits` field. So named rules in
`merge/bhl_base.py` are applied to the BHL client:

* `op4-max-weapons-64`, `op4-max-weapons-64-server`, and `op4-local-state-64` expand the shared
  prediction structures.
* `op4-prediction-transfer-64` in `entity.cpp` makes `HUD_TxferPredictionData` transfer data for
  64 weapons.
* `op4-weapons-message-hook` in `hud.cpp` registers `OP4_MsgFunc_Weapons` from
  `op4_client_prediction.cpp`. The message reads both halves and stores the low 32 bits in
  `gHUD.m_iWeaponBits` (all ten OP4 weapon IDs are below 32).
* `op4-weapons-message-flag-decl` and `op4-weapons-message-flag-use` in `hud_update.cpp` stop
  `UpdateClientData` from overwriting OP4 bits in the old field after the message arrives.

`liblist.gam` in the package uses `startmap "of0a0"`, `trainmap "ofboot0"`, `steam_appid.txt = 50`,
and `fallback_dir "gearbox"`. `data/delta.lst` is no longer a raw OP4 copy or a raw BHL copy. It is
generated by `tools/make_merged_delta.py` from the two installed files. It keeps BHL's 11-bit
`health` and 2-bit `eflags`, and adds OP4's 6-bit `m_iId` and 8-bit `iuser4`. The
`ui/resource/language/*.txt` files are written as UTF-16LE with BOM, because VGUI2 requests `.txt`
rather than `.utf8.txt`.

After the user reported that the weapons did not work, named rules were added as well:
`op4-client-iteminfo-ammo-registry` fills `ItemInfoArray` and registers ammo with OP4's
two-argument form; `op4-client-getammoindex-real` replaces the `-1` stub;
`op4-client-prediction-state-in/out` transfers `ammo_spores`, `ammo_762`, and `m_iItems`;
`op4-client-weapon-array-64` and `op4-client-weapon-loops-64` expand prediction; and the
`OldWeapon` / `HudColor` messages are wired and cleared on `InitHUD` / `ResetHUD`.
These are source and package changes. They are **not** a claim of an in-game test.

## 10. Music and test limits

OP4 `dlls/triggers.cpp::PlayCDTrack()` sends `cd play <track>` to the engine. There is no MP3
path in the game code and no `cd/mp3/media` command in the cfg files. Because the mod folder has
no `media/`, the engine looks for music in `valve`, and `fallback_dir` is not enough to force
`gearbox/media`. So `setup_op4_media.bat` copies the original MP3 files only, from the installed
`gearbox` copy into `bhlop4/media/`. Nothing is generated or downloaded.

Full details and the original, edited, and self-written file list are in
[`docs/OP4_SOURCE_AUDIT.md`](OP4_SOURCE_AUDIT.md). The table in
[`docs/OP4_RUNTIME_TESTS.md`](OP4_RUNTIME_TESTS.md) has no passing mark: **GoldSrc was not run in
this environment**.

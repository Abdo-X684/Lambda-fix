# Opposing Force source and asset audit

> **File and source audit only.** The GoldSrc engine was not run in this environment,
> and compilation, CI, file presence, or event logging is not proof that any weapon works.
> User report: the game runs, the music is OP4 music, and the weapons work. This was not re-tested here,
> so no untested row is marked as passing.

## 1. Pinned repositories and commits

| Role | Repository | Commit | Tarball hash |
|---|---|---|---|
| OP4 weapons/server source | [twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated) | [`5368be7f8eba14b05236c7c52ad5f6b11fd95e55`](https://github.com/twhl-community/halflife-op4-updated/commit/5368be7f8eba14b05236c7c52ad5f6b11fd95e55) | `c65e53713b5ef2d3a8a65dfea4010ccb87afb096944e310ce094f9fbdef43753` |
| BHL base / VGUI2 / movement | [tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased) | [`4d32095e3c33d5ca60809d9c51f8aafe51c0a521`](https://github.com/tmp64/BugfixedHL-Rebased/commit/4d32095e3c33d5ca60809d9c51f8aafe51c0a521) | `a70ab961de1c40f6d4df025fbd37f14c81951afef9b6175023518ed4f81228dc` |
| HLSDK origin | [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife) | [`b1b5cf5892918535619b2937bb927e46cb097ba1`](https://github.com/ValveSoftware/halflife/commit/b1b5cf5892918535619b2937bb927e46cb097ba1) | `f5e7793f974bc02d1e1c4e29a9733df23c2f8dfbaa97c888bb738c2d9b2b5726` |

All ten weapons come from **one OP4 repository** at the commit above; there are no models
or entities from any other repository. Models, sounds, maps, and MP3s are not in this
repository or in the ZIP: they are read from the user's own legally installed `gearbox/` copy.

## 2. Weapon table: origin, files, edits, self-written code

| Weapon | Code name | Original OP4 files | Declared edit | Client event | Files we wrote for the weapon | In game |
|---|---|---|---|---|---|---|
| Desert Eagle | `weapon_eagle` / `CEagle` | `CEagle.cpp`<br>`CEagle.h`<br>`CEagleLaser.cpp`<br>`CEagleLaser.h` | `op4+compat-patch, verbatim` | `events/eagle.sc` → `EV_FireEagle` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Pipe Wrench | `weapon_pipewrench` / `CPipewrench` | `CPipewrench.cpp`<br>`CPipewrench.h` | `op4+compat-patch` | `events/pipewrench.sc` → `EV_Pipewrench` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| M249 | `weapon_m249` / `CM249` | `CM249.cpp`<br>`CM249.h` | `op4+compat-patch` | `events/m249.sc` → `EV_FireM249` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Displacer | `weapon_displacer` / `CDisplacer` | `CDisplacer.cpp`<br>`CDisplacer.h`<br>`CDisplacerBall.cpp`<br>`CDisplacerBall.h` | `op4+compat-patch, verbatim` | `events/displacer.sc` → `EV_FireDisplacer` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Shock Rifle / weapon_shockroach alias | `weapon_shockrifle` / `CShockRifle` | `CShockRifle.cpp`<br>`CShockRifle.h`<br>`CShockBeam.cpp`<br>`CShockBeam.h`<br>`shockroach.cpp` | `op4+compat-patch` | `events/shock.sc` → `EV_FireShockRifle` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Spore Launcher | `weapon_sporelauncher` / `CSporeLauncher` | `CSporeLauncher.cpp`<br>`CSporeLauncher.h`<br>`CSpore.cpp`<br>`CSpore.h` | `op4+compat-patch` | `events/spore.sc` → `EV_FireSpore` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Sniper Rifle | `weapon_sniperrifle` / `CSniperRifle` | `CSniperRifle.cpp`<br>`CSniperRifle.h` | `op4+compat-patch` | `events/sniper.sc` → `EV_SniperRifle` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Knife | `weapon_knife` / `CKnife` | `CKnife.cpp`<br>`CKnife.h` | `op4+compat-patch` | `events/knife.sc` → `EV_Knife` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Penguin | `weapon_penguin` / `CPenguin` | `CPenguin.cpp`<br>`CPenguin.h`<br>`penguin_grenade.cpp` | `op4+compat-patch` | `events/penguinfire.sc` → `EV_PenguinFire` | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |
| Grapple | `weapon_grapple` / `CGrapple` | `CGrapple.cpp`<br>`CGrapple.h`<br>`CGrappleTip.cpp`<br>`CGrappleTip.h` | `op4+compat-patch, verbatim` | not in OP4 source | none; weapon bodies are original | **not tested inside GoldSrc in this environment** |

**Shock Roach note:** weapon_shockroach is an alternate classname for CShockRifle, not a separate player weapon. monster_shockroach / COFShockRoach in dlls/shockroach.cpp is a separate OP4 creature entity. W_Precache registers weapon_shockrifle only.

**Every `op4+compat-patch` file above**: the weapon body is from OP4, and the edits are named in
`bhl-op4/PROVENANCE.json` (`bool/int` compatibility, headers, `Vector::Normalize`).
No replacement fire or reload logic was written. The OP4 files `dlls/weapons.cpp` and `dlls/player.cpp`
are kept as reference only; the package server is built from the full OP4 source via
`tools/prepare_op4_msvc_server.py`.

### BHL files edited by named rules

* `src/game/client/hud.cpp` — `bhl+op4-merge`
* `src/game/client/hud_msg.cpp` — `bhl+op4-merge`
* `src/game/client/hud_update.cpp` — `bhl+op4-merge`
* `src/game/client/entity.cpp` — `bhl+op4-merge`
* `src/game/client/hl/hl_events.cpp` — `bhl+op4-merge`
* `src/game/client/hl/hl_weapons.cpp` — `bhl+op4-merge`
* `src/game/client/hl/hl_baseentity.cpp` — `bhl+op4-merge`
* `src/game/client/CMakeLists.txt` — `bhl+op4-merge`
* `src/game/server/weapons.cpp` — `bhl+op4-merge`
* `src/game/server/weapons.h` — `bhl+op4-merge`
* `src/game/server/cdll_dll.h` — `bhl+op4-merge`
* `src/game/server/player.h` — `bhl+op4-merge`
* `src/common/entity_state.h` — `bhl+op4-merge`
* `src/game/server/CMakeLists.txt` — `bhl+op4-merge`

### Files written by this project (not from OP4 or BHL)

* `src/game/client/op4/op4_client_prediction.cpp`
* `src/game/client/op4/op4_weapon_events.cpp`
* `src/game/client/op4/op4_weapon_events.h`
* `src/game/server/op4/op4_compat.cpp`
* `src/game/server/op4/op4_compat.h`
* `src/game/server/op4/op4_compat_late.h`
* `src/game/server/op4/op4_link_fixups.cpp`
* `src/game/server/op4/op4_ctf_player.cpp`
* `src/game/server/op4/op4_entity_enumerator.h`
* `src/game/shared/op4_weapon_timing.cpp`
* `src/game/shared/op4_weapon_timing.h`
* `tools/packaging/setup_op4_media.bat`

This is only a wiring, prediction, event-hook, and music-setup layer; it does not replace BHL systems
(VGUI2, movement, bhop, monsters, the fourteen BHL weapons).

## 3. Penguin: source code

* Weapon: `CPenguin` / `weapon_penguin`; FGD: `Killer Penguin`.
* Live entity: `CPenguinGrenade` / `monster_penguin`.
* Files: `dlls/weapons/CPenguin.cpp`, `dlls/weapons/CPenguin.h`, `dlls/penguin_grenade.cpp` from OP4 at the commit above.
* Function: CPenguin::PrimaryAttack() plays events/penguinfire.sc and, server-side, creates monster_penguin at the trace endpoint with forward velocity. CPenguinGrenade::Spawn() sets models/w_penguin.mdl and HuntThink() makes it seek a target before exploding.
* Models: Only from the user's installed gearbox/models/*.mdl via fallback_dir; the repository and ZIP contain no .mdl file.
* No `.mdl` is inside the ZIP; any model path seen in the installed game files comes from `gearbox/`, not a second repository.

## 4. Source gaps fixed after the bug report

> These are source checks only; they were not tested in game.

| Check | Present in the generated tree |
|---|---|
| `all_ten_prediction_objects` | `True` |
| `all_ten_prediction_cases` | `True` |
| `g_pWpns_max_weapons` | `True` |
| `prediction_loops_max_weapons` | `True` |
| `op4_ammo_state_transfer` | `True` |
| `iteminfoarray_populated` | `True` |
| `two_arg_ammo_registry` | `True` |
| `client_ammoinfoarray_definition` | `True` |
| `client_getammoindex_real` | `True` |
| `hud_weaponlist` | `True` |
| `hud_curweapon_ammox` | `True` |
| `slot7` | `True` |
| `max_weapon_slots_7` | `True` |
| `oldweapon_hook` | `True` |
| `hudcolor_hook` | `True` |
| `weapons_hook` | `True` |
| `reset_on_init_and_reset_hud` | `True` |
| `oldweapon_message_glue` | `True` |
| `hudcolor_message_glue` | `True` |
| `event_hooks` | `9/9 events wired` |

Main source fixes: moving `iuser4 → m_iItems` and `vuser2.y/z → ammo_spores/ammo_762`
into BHL client prediction; expanding the prediction arrays/loops to `MAX_WEAPONS=64`; filling
`ItemInfoArray` and registering ammo with OP4's two-argument form; defining `AmmoInfoArray`
and a real `GetAmmoIndex` in the client; linking `OldWeapon`/`HudColor` with `Weapons`;
clearing network state on `InitHUD`/`ResetHUD`; generating a merged `delta.lst` that keeps
BHL's health/eflags and adds a 6-bit `m_iId` and OP4's `iuser4`.
These were the candidate causes for the earlier weapon bug. A later user report says the weapons work; this was not re-tested here.

## 5. Music: cause, path, and fix

* Code path: OP4 dlls/triggers.cpp PlayCDTrack() sends engine 'cd play <track>' (and 'cd stop' for -1). The engine, not the game DLL, maps the track ID to media/*.mp3. Shipped autoexec.cfg/op4weapons.cfg contain no cd/mp3/media command.
* Diagnosis: The ZIP contains no media/*.mp3 and no gamestartup.mp3. GoldSrc looks in the active mod's media/ folder and then valve/media; fallback_dir gearbox supplies maps/models/sounds but is not a reliable media/ lookup for CD/MP3 tracks. An earlier report said the intro played Half-Life music. A later user report says the music works and is the OP4 soundtrack.
* Fix: setup_op4_media.bat copies only the user's original gearbox/media/*.mp3 (plus gearbox_downloads/media/*.mp3 when present) into lambda-fix/media/. No track is invented, renamed, or downloaded.
* Startup music: gamestartup.mp3 is copied only if the installed OP4 copy provides it; it is never fabricated.
* In-game result: **user reports OP4 music plays in game; not run or tested in this environment**.

Engine behavior sources (for review, not as runtime proof):
* https://developer.valvesoftware.com/wiki/List_of_HL1_soundtracks
* https://twhl.info/wiki/page/Tutorial:_Making_Music_Play_in_Maps_[GoldSource]/5984
* https://github.com/UCyborg/hl-mp3-fix

## 6. Package limits

* The ZIP does not include `.mdl`, `.wav`, `.sc`, `.mp3`, or `.bsp`. The only third-party sprites are `sprites/ag_*.spr` (Adrenaline Gamer, license unconfirmed).
* `SOURCE_AUDIT.md`, `RUNTIME_TESTS.md`, and `INSTALL.md` are included in the ZIP. `setup_op4_media.bat` is a Windows helper in `tools/packaging/` and is **not** in the Linux ZIP, so the Linux package has no `media/` folder.
* `MOD_MANIFEST.json` states `in_game_tested_here: false`.

**Summary:** every original, edited, and self-written file is documented above, but there is no GoldSrc test here;
the `RUNTIME_TESTS.md` table in the package has no passing mark.

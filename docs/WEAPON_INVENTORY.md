# Opposing Force weapon inventory on the BugfixedHL base

> Generated automatically by `python3 tools/weapon_inventory.py --write` from the clean
> `.cache/upstreams/bugfixhl/` and `.cache/upstreams/op4/` copies, the merged tree
> `bhl-op4/`, `PORT_STATUS.json`, the Linux and Windows build manifests, and the `mod/` package.
> The package now starts the full OP4 campaign (`of0a0`) with a real OP4 server, not a
> Half-Life campaign with OP4 weapons. No earlier report or CI result is read as evidence.

## Required table

| Weapon | In BHL | In OP4 | Merge status | Prediction | In-game test |
| --- | --- | --- | --- | --- | --- |
| `weapon_displacer` | no | yes | incomplete | yes | not tested |
| `weapon_eagle` | no | yes | incomplete | yes | not tested |
| `weapon_grapple` | no | yes | incomplete | yes | not tested |
| `weapon_knife` | no | yes | incomplete | yes | not tested |
| `weapon_m249` | no | yes | incomplete | yes | not tested |
| `weapon_penguin` | no | yes | incomplete | yes | not tested |
| `weapon_pipewrench` | no | yes | incomplete | yes | not tested |
| `weapon_shockrifle` | no | yes | incomplete | yes | not tested |
| `weapon_sniperrifle` | no | yes | incomplete | yes | not tested |
| `weapon_sporelauncher` | no | yes | incomplete | yes | not tested |

**Required interpretation:** `incomplete` under 'Merge status' and `not tested` under 'In-game test' are not evasions of
the inventory: source, client/server, event, registration, and give-command files are wired for all ten weapons,
but there is no GoldSrc engine and no legal OP4 assets in this environment. So no row says `complete`
or `passing`, and nothing is said about any weapon working in game. `yes` under `Prediction`
means the real weapon file is wired into `client` with `CLIENT_DLL` and the `GetLocalWeapon`
and `UseDecrement()` state, not proof of runtime prediction.

`weapon_shockroach` is not an eleventh weapon: it is an alias for `CShockRifle` in
the clean OP4 source and does not appear in `W_Precache()`; `monster_shockroach`
is a separate monster entity in `dlls/shockroach.cpp`.

## What the check actually verified

* Clean BHL: `14` weapons in `W_Precache()`; clean OP4: `24`;
  the difference is `10` OP4-only weapons. The merged tree registers `24`
  names, once per name, with no duplicate registration.
* Client: ten real OP4 weapon files + `CGrappleTip.cpp` + `ehandle.cpp`
  + `op4_client_prediction.cpp` + nine view events, compiled with `CLIENT_DLL`.
  `CGrapple` is no longer server-authoritative; no `UseDecrement()` is forced to `FALSE`.
* `MAX_WEAPON_SLOTS = 7` and the `slot7` command are wired into BHL code; the seventh-slot sprite
  in `sprites/hud.txt` is still not tested in game.
* OP4 network compatibility: `MAX_WEAPONS = 64`, `local_state_t.weapondata[64]`, moving
  prediction data for 64 weapons, and binding the 8-byte `Weapons` message in the BHL client
  so weapon bits are not read only from the old 32-bit engine field.
* `liblist.gam` starts `of0a0` and `ofboot0`; `steam_appid.txt = 50`;
  merged BHL+OP4 `delta.lst` (keeps `health`/`eflags` and adds `iuser4`
  and a 6-bit `m_iId`), and `fallback_dir "gearbox"` loads the installed OP4 assets.
* After the bug report: client prediction gaps were fixed (`ItemInfoArray`, ammo registration,
  `GetAmmoIndex`, `ammo_spores/ammo_762/m_iItems`, 64-slot loops,
  `OldWeapon`/`HudColor`, and clearing state on ResetHUD), at the source level only.
* Music: `setup_op4_media.bat` copies the original MP3s from `gearbox/media` only;
  there is no MP3 in the ZIP and no generated music. Details are in `SOURCE_AUDIT.md`.
* `autoexec.cfg` sets `sv_oldweapons 0`; `op4weapons.cfg` gives the ten weapons
  and ammo via F9. The patched Windows server also makes `impulse 101` give them,
  including `weapon_penguin`; Linux uses F9/F10 with the original `gearbox` server.
* Linux: `client.so` `28303100` bytes, sha256
  `57c26765f9a9219ba388fb8349b3f56fe3b3e6a1ce920fbdb2c023584eba3b95`, linked against `GLIBC_2.17`; the old `hl.so` server
  (`21252408` bytes) is not in the package and uses
  `../gearbox/dlls/opfor.so` instead.
* Windows (`x86-windows-msvc / PE32 i386`, `MSVC 19.44 / Visual Studio 2022 / CMake 3.30.9 / vcpkg x86-windows-static`, ABI compatible with MSVC/VGUI2):
  `client.dll` `2071552` bytes, sha256 `02acbadbd4aa8aeb209209911550be996c426f961b72e06f19d10a41d0612887`;
  `opfor.dll` `1860608` bytes, sha256 `866d4dd3392b7cf906141f0520d032f89fc166fab3095cbec3b87e951996143a`. The old `hl.dll`
  server (`1661952` bytes) is not in the package.
  These are MSVC binaries, but they are **not tested in game**.
* `SOURCES.sha256` hashes are checked for every existing file, and the violation count must be zero;
  `.cache/` paths for SDK/deps are not in git and are restored by the build script,
  so missing ones are skipped explicitly and are not counted as a pass. The `mod/cl_dlls/` binaries
  and `mod/dlls/opfor.dll` match the existing build exactly.
* `MOD_MANIFEST.json` states explicitly: `in_game_tested_here: false`.

## Gaps that block a 'complete' mark

1. No loading in the GoldSrc engine, and no real selection/fire/reload/ammo/animation/sound/prediction
   testing, and no crash or multiplayer testing.
2. No legal OP4 assets are included: models, sounds, HUD sprites, and `events/*.sc`
   are read from the user's installed `gearbox/` copy through `fallback_dir`.
3. No Windows runtime test and no seventh HUD slot test in game, and no
   confirmation from the user that the OP4 campaign, menus, music, and every weapon work after this change;
   the `RUNTIME_TESTS.md` table shows `not tested` for every row.
4. The Linux server is the original `gearbox` one: it has no `sv_bhl_*` and no
   `impulse 101` patch, which is an explicit difference from the Windows build.
5. Builds, compilation, and automated checks do not replace these tests.

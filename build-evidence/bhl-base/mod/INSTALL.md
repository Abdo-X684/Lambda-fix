# bhlop4 — BugfixedHL + Opposing Force (Linux)

## Install

1. Install Half-Life: Opposing Force. The `gearbox/` folder must sit next to `valve/`.
2. Delete any old `bhlop4` folder.
3. Unzip this package into the main game folder, next to `valve/` and `gearbox/`
   (example: `game/bhlop4/`). Do not put it inside `gearbox/`. Do not rename it.
4. Launch with `-game bhlop4` (depends on your `hl.sh`).

## Requirements

- SDL2 installed on the system (`libSDL2-2.0.so.0`).
- Half-Life: Opposing Force installed. Maps, models, and sounds are read from `gearbox/`.

## What is inside

- `cl_dlls/client.so`: BugfixedHL client with the Opposing Force weapons, built with `-O2`.
  It links its own tier0/vstdlib replacements (see `LINUX_SHIMS_README.txt`).
- Server: the stock `gearbox/dlls/opfor.so` from your installed game is used.
- `ui/resource/`: BHL menus. The Advanced > About page has no auto-update option.
  The default HUD color is green.
- `resource/bhlop4_english.txt`: English localization for menu text.
- `LICENSES/`: GPL-3.0 (BugfixedHL), Valve Half-Life 1 SDK License, and MIT (build tools).
  `NOTICE.txt` explains the source of each part.

## Notes

- This package contains no Valve assets. Maps, models, and sounds come from `gearbox/`.
- Music on Linux is not tested.
- Test results are listed in `RUNTIME_TESTS.md`. Only what was reported as working is marked as working.
- If you get an error, send the last lines of the console output.

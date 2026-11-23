# BugfixedHL + full Opposing Force

## Install steps

1. Unzip this folder inside the Half-Life folder, next to `valve/` and `gearbox/`
   (for example `Half-Life/lambda-fix`). Do not put it inside `gearbox/`, and do not rename it.
2. Run `setup_op4_media.bat` once: it copies only the original OP4 music from
   `gearbox/media/` to `lambda-fix/media/`. It does not create or download any MP3 file.
3. Run: `hl.exe -game lambda-fix -console`.
4. **New Game** starts the Opposing Force campaign at `of0a0`, not the Half-Life campaign.
5. `impulse 101` gives the nine OP4 weapons on Windows.
6. Opposing Force must be installed: maps, models, sounds, and sprites are read from
   `gearbox/` through `fallback_dir`.

## English

Put this folder next to `valve/` and `gearbox/`, then launch
`hl.exe -game <folder name> -console`. Do not rename the folder.

* `startmap "of0a0"`, `trainmap "ofboot0"`, `steam_appid.txt = 50`, OP4
  `delta.lst` and `fallback_dir "gearbox"` give the real OP4 campaign.
* Windows `dlls/opfor.dll` is built from the full OP4 SDK server, with
  BHL `sv_bhl_*` cvars, speedrun hooks, and a patched `impulse 101` that
  gives the nine OP4 weapons (no penguin, no extra ammo). It has OP4's monsters,
  gamerules and entities, not the Half-Life campaign.
* Linux uses the installed `../gearbox/dlls/opfor.so`; the custom BHL
  client still loads from this mod. Linux therefore lacks the BHL server
  cvars and the patched impulse 101, but the console command covers the nine weapons.
* `cl_dlls/client.dll` and `client.so` are the BugfixedHL VGUI2 clients
  with all ten OP4 weapon prediction sources compiled in.
* `ui/resource/language/*.txt` are UTF-16LE BOM conversions of BHL's
  `.utf8.txt` files: VGUI2 needs these to resolve `#BHL_*` menu tokens.
* OP4 copyright assets are not bundled; they come from your installed
  `gearbox/` folder. Run `setup_op4_media.bat` first: GoldSrc otherwise falls
  back to the Half-Life soundtrack because this mod has no `media/` folder.
* `SOURCE_AUDIT.md` lists the exact pinned repo/commit, original, modified and
  authored files for all ten weapons, Penguin and the music path.
* `RUNTIME_TESTS.md` is the GoldSrc test table: no row is marked successful.

HONEST LIMIT: no GoldSrc runtime or legal OP4 assets exist in this sandbox.
This package has NOT been tested in-game here. Bare `impulse 101` giving all
ten weapons is a source-level Windows-server fix, not a user-confirmed
runtime result. Test campaign start, menus, music, and every weapon on your
machine; see `RUNTIME_TESTS.md`.

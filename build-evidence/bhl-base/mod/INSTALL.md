# BugfixedHL + Opposing Force weapons (playable mod)

Put this folder next to `valve/` and `gearbox/` in your Half-Life directory,
then launch Half-Life with `-game <folder name> -console`
(Windows: `hl.exe`, Linux: `hl_linux`).

* `liblist.gam` starts `c0a0` and uses `steam_appid.txt` = 70 (Half-Life).
  The BHL VGUI2 HUD, health counter, movement and all 14 BHL weapons are the
  BHL-based DLLs in `cl_dlls/` and `dlls/`. Nothing from OP4 replaces them.
* OP4's models, sounds, sprites and `events/*.sc` are NOT bundled: they are
  read from your installed `gearbox/` via `fallback_dir`. OP4 must be
  installed. Do not copy this folder inside `gearbox/`.
* In-game press F9 (or type `exec op4weapons.cfg` in the console) to receive
  all ten OP4 weapons. `slot1`..`slot7` select them; `use weapon_eagle` etc.
  also work.

Technical note: OP4 weapons run server-authoritatively (`sv_oldweapons 1`),
so their firing, reload, animations, sounds, effects, ammo and HUD updates
are delivered by the BHL-based server DLL. BHL's own 14 weapons keep their
original client prediction. There is no OP4 client-side prediction here.

HONEST LIMIT: this sandbox has no GoldSrc engine and no legal OP4 assets, so
this build has NOT been tested in-game here. Test it on your machine; if a
weapon misbehaves, that is a real bug, not a completed merge.

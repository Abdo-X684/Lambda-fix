# BHL-root playable package

This folder is built from the BHL-root binaries in `build-evidence/bhl-base/`
(and the PE32 twins in `build-evidence/bhl-windows/`), NOT from the old
`dist/bhlop4` OP4-root kit (`bhl-systems-1`).

* `liblist.gam` identifies the mod as BugfixedHL, starts `c0a0`, falls back to
  `valve` (implicit) + `gearbox` (for OP4 weapon assets).
* `steam_appid.txt` = 70 (Half-Life), not 50 (Opposing Force).
* BHL `gamedir/` VGUI2 resources are included.

Launch: `hl.exe -game <this folder> -console` (copy folder next to valve/ and
gearbox/, do not put it inside gearbox/).

HONEST LIMIT: this corrects the PACKAGE IDENTITY only. The OP4 weapons still
have no client prediction / HUD selection / verified in-game behaviour, and I
have no GoldSrc runtime here to test it. Do not treat this as a working merge.

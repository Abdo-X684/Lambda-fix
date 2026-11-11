# BugfixedHL + full Opposing Force

## Arabic - خطوات التشغيل

1. فكّ ضغط المجلد داخل مجلد Half-Life بجانب `valve/` و`gearbox/`
   (مثلاً `Half-Life/bhlop4`). لا تضعه داخل `gearbox/` ولا تغيّر اسم المجلد.
2. شغّل: `hl.exe -game bhlop4 -console`.
3. **New Game** يبدأ حملة Opposing Force من `of0a0`، لا حملة Half-Life.
4. `impulse 101` يعطي كل أسلحة OP4 العشرة في ويندوز؛ **F9** يعيد إعطاءها
   مع الذخيرة، و**F10** يعطي `weapon_penguin` على لينكس أيضاً.
5. يجب أن تكون Opposing Force مثبّتة: الخرائط والموديلات والأصوات
   والسبرايت تُقرأ من `gearbox/` عبر `fallback_dir`.

## English

Put this folder next to `valve/` and `gearbox/`, then launch
`hl.exe -game <folder name> -console`. Do not rename the folder.

* `startmap "of0a0"`, `trainmap "ofboot0"`, `steam_appid.txt = 50`, OP4
  `delta.lst` and `fallback_dir "gearbox"` give the real OP4 campaign.
* Windows `dlls/opfor.dll` is built from the full OP4 SDK server, with
  BHL `sv_bhl_*` cvars, speedrun hooks, and a patched `impulse 101` that
  includes `weapon_penguin` and OP4 ammunition. It has OP4's monsters,
  gamerules and entities, not the Half-Life campaign.
* Linux uses the installed `../gearbox/dlls/opfor.so`; the custom BHL
  client still loads from this mod. Linux therefore lacks the BHL server
  cvars and the patched impulse 101, but F9/F10 cover the ten weapons.
* `cl_dlls/client.dll` and `client.so` are the BugfixedHL VGUI2 clients
  with all ten OP4 weapon prediction sources compiled in.
* `ui/resource/language/*.txt` are UTF-16LE BOM conversions of BHL's
  `.utf8.txt` files: VGUI2 needs these to resolve `#BHL_*` menu tokens.
* OP4 copyright assets are not bundled; they come from your installed
  `gearbox/` folder.

HONEST LIMIT: no GoldSrc runtime or legal OP4 assets exist in this sandbox.
This package has NOT been tested in-game here. Bare `impulse 101` giving all
ten weapons is a source-level Windows-server fix, not a user-confirmed
runtime result. Test campaign start, menus, and every weapon on your machine.

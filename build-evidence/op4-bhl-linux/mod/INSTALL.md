# BugfixedHL + full Opposing Force

## Arabic - خطوات التشغيل

1. فكّ ضغط المجلد داخل مجلد Half-Life بجانب `valve/` و`gearbox/`
   (مثلاً `Half-Life/bhlop4`). لا تضعه داخل `gearbox/` ولا تغيّر اسم المجلد.
2. شغّل `setup_op4_media.bat` مرة واحدة: ينسخ موسيقى OP4 الأصلية فقط من
   `gearbox/media/` إلى `bhlop4/media/`؛ لا يُنشئ ولا يحمّل أي ملف MP3.
3. شغّل: `hl.exe -game bhlop4 -console`.
4. **New Game** يبدأ حملة Opposing Force من `of0a0`، لا حملة Half-Life.
5. `impulse 101` يعطي كل أسلحة OP4 العشرة في ويندوز؛ **F9** يعيد إعطاءها
   مع الذخيرة، و**F10** يعطي `weapon_penguin` على لينكس أيضاً.
6. يجب أن تكون Opposing Force مثبّتة: الخرائط والموديلات والأصوات
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

## Settings menu
- **F8** opens the BHLS Settings menu (same as typing `bhls_settings`).
- The main menu button is not available from client code (engine GameUI). See LINUX_OP4_CLIENT_NOTE.txt.
- Speedometer: type `hud_speedometer 1`. Plain-text HP/AMMO: `bhl_hud_text 1` (default).

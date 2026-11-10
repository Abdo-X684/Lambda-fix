# BugfixedHL + Opposing Force weapons (playable mod)

## Arabic - خطوات التشغيل

1. فكّ ضغط المجلد داخل مجلد Half-Life بجانب `valve/` و`gearbox/`
   (مثلاً `Half-Life/bhlop4`). لا تضعه داخل `gearbox/`.
2. شغّل Half-Life بهذا الخيار:
   `hl.exe -game bhlop4 -console` (ويندوز) أو `hl_linux -game bhlop4 -console` (لينكس).
3. داخل اللعبة اضغط **F9** ستحصل على أسلحة OP4 العشرة وذخائرها.
   أو اكتب في الكونسول: `exec op4weapons.cfg`.
4. اختر الأسلحة بـ `slot1` … `slot7` أو `use weapon_eagle` وهكذا.
5. يجب أن تكون Opposing Force مثبّتة: الموديلات والأصوات والسبرايت
   وملفات `events/*.sc` تُقرأ من `gearbox/` عبر `fallback_dir`.

## English

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

Technical note: all ten OP4 weapons are client-predicted from OP4's real
shared weapon .cpp files, compiled into the BHL-based client DLL with
CLIENT_DLL (the same mechanism BHL uses for its own 14 weapons). OP4's
CGrappleTip.cpp and ehandle.cpp are compiled the same way, following OP4's
own client project; no OP4 weapon is left server-authoritative. The Windows
client.dll/hl.dll are MSVC-ABI builds so VGUI2 matches the original BHL ABI.
`sv_oldweapons 0` is the default; setting it to 1 switches all OP4 weapons
to server-authoritative mode for troubleshooting. BHL's own 14 weapons and
their prediction are unchanged.

HONEST LIMIT: this sandbox has no GoldSrc engine and no legal OP4 assets, so
this build has NOT been tested in-game here. Test it on your machine; if a
weapon misbehaves, that is a real bug, not a completed merge.

# تدقيق مصادر وأصول Opposing Force

> **تدقيق ملفات ومصادر فقط.** لم يُشغَّل محرك GoldSrc في هذه البيئة،
> ولا تُعدّ الترجمة أو CI أو وجود ملفات أو تسجيل حدث دليلاً على عمل أي سلاح.
> بلاغ المستخدم: اللعبة تعمل، لكن موسيقى المقدمة ليست OP4 والأسلحة لا تعمل بشكل صحيح؛
> لذلك لا توجد علامة نجاح لأي صف غير مُختبَر.

## 1. المستودعات والالتزامات المثبّتة

| الدور | المستودع | الالتزام | بصمة الحزمة |
|---|---|---|---|
| مصدر أسلحة/خادم OP4 | [twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated) | [`5368be7f8eba14b05236c7c52ad5f6b11fd95e55`](https://github.com/twhl-community/halflife-op4-updated/commit/5368be7f8eba14b05236c7c52ad5f6b11fd95e55) | `c65e53713b5ef2d3a8a65dfea4010ccb87afb096944e310ce094f9fbdef43753` |
| أساس BHL / VGUI2 / الحركة | [tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased) | [`4d32095e3c33d5ca60809d9c51f8aafe51c0a521`](https://github.com/tmp64/BugfixedHL-Rebased/commit/4d32095e3c33d5ca60809d9c51f8aafe51c0a521) | `a70ab961de1c40f6d4df025fbd37f14c81951afef9b6175023518ed4f81228dc` |
| أصل HLSDK | [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife) | [`b1b5cf5892918535619b2937bb927e46cb097ba1`](https://github.com/ValveSoftware/halflife/commit/b1b5cf5892918535619b2937bb927e46cb097ba1) | `f5e7793f974bc02d1e1c4e29a9733df23c2f8dfbaa97c888bb738c2d9b2b5726` |

الأسلحة العشرة كلها من **مستودع OP4 واحد** وبنفس الالتزام أعلاه؛ لا توجد نماذج
أو كيانات بديلة من مستودع آخر. الموديلات/الأصوات/الخرائط/الـMP3 ليست في هذا
المستودع ولا في ZIP: تُقرأ من نسخة `gearbox/` المثبّتة قانونياً لدى المستخدم.

## 2. جدول الأسلحة: الأصل، الملفات، التعديل، الكتابة الذاتية

| السلاح | الاسم البرمجي | ملفات OP4 الأصلية | تعديل معلن | حدث العميل | ملفات كتبناها للسلاح | داخل اللعبة |
|---|---|---|---|---|---|---|
| Desert Eagle | `weapon_eagle` / `CEagle` | `CEagle.cpp`<br>`CEagle.h`<br>`CEagleLaser.cpp`<br>`CEagleLaser.h` | `op4+compat-patch, verbatim` | `events/eagle.sc` → `EV_FireEagle` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Pipe Wrench | `weapon_pipewrench` / `CPipewrench` | `CPipewrench.cpp`<br>`CPipewrench.h` | `op4+compat-patch` | `events/pipewrench.sc` → `EV_Pipewrench` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| M249 | `weapon_m249` / `CM249` | `CM249.cpp`<br>`CM249.h` | `op4+compat-patch` | `events/m249.sc` → `EV_FireM249` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Displacer | `weapon_displacer` / `CDisplacer` | `CDisplacer.cpp`<br>`CDisplacer.h`<br>`CDisplacerBall.cpp`<br>`CDisplacerBall.h` | `op4+compat-patch, verbatim` | `events/displacer.sc` → `EV_FireDisplacer` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Shock Rifle / weapon_shockroach alias | `weapon_shockrifle` / `CShockRifle` | `CShockRifle.cpp`<br>`CShockRifle.h`<br>`CShockBeam.cpp`<br>`CShockBeam.h`<br>`shockroach.cpp` | `op4+compat-patch` | `events/shock.sc` → `EV_FireShockRifle` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Spore Launcher | `weapon_sporelauncher` / `CSporeLauncher` | `CSporeLauncher.cpp`<br>`CSporeLauncher.h`<br>`CSpore.cpp`<br>`CSpore.h` | `op4+compat-patch` | `events/spore.sc` → `EV_FireSpore` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Sniper Rifle | `weapon_sniperrifle` / `CSniperRifle` | `CSniperRifle.cpp`<br>`CSniperRifle.h` | `op4+compat-patch` | `events/sniper.sc` → `EV_SniperRifle` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Knife | `weapon_knife` / `CKnife` | `CKnife.cpp`<br>`CKnife.h` | `op4+compat-patch` | `events/knife.sc` → `EV_Knife` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Penguin | `weapon_penguin` / `CPenguin` | `CPenguin.cpp`<br>`CPenguin.h`<br>`penguin_grenade.cpp` | `op4+compat-patch` | `events/penguinfire.sc` → `EV_PenguinFire` | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |
| Grapple | `weapon_grapple` / `CGrapple` | `CGrapple.cpp`<br>`CGrapple.h`<br>`CGrappleTip.cpp`<br>`CGrappleTip.h` | `op4+compat-patch, verbatim` | لا يوجد في مصدر OP4 | لا شيء؛ أجسام الأسلحة أصلية | **غير مُختبَر داخل GoldSrc في هذه البيئة** |

**توضيح Shock Roach:** weapon_shockroach is an alternate classname for CShockRifle, not a separate player weapon. monster_shockroach / COFShockRoach in dlls/shockroach.cpp is a separate OP4 creature entity. W_Precache registers weapon_shockrifle only.

**كل ملف `op4+compat-patch` أعلاه**: جسم السلاح من OP4، والتعديلات مسماة في
`bhl-op4/PROVENANCE.json` (توافق `bool/int`، ترويسات، `Vector::Normalize`).
لم يُكتب منطق إطلاق أو إعادة تعبئة بديل. ملفات `dlls/weapons.cpp` و`dlls/player.cpp`
في OP4 محفوظة كمرجع فقط؛ خادم الحزمة يُبنى من مصدر OP4 الكامل عبر
`tools/prepare_op4_msvc_server.py`.

### ملفات BHL المعدّلة بقواعد مسماة

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

### ملفات كتبها هذا المشروع (ليست من OP4 ولا BHL)

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

هذه طبقة توصيل/تنبؤ/تثبيت أحداث/إعداد موسيقى فقط؛ لا تحل محل أنظمة BHL
(VGUI2، الحركة، Bhop، الوحوش، أسلحة BHL الأربعة عشر).

## 3. Penguin: المصدر البرمجي

* السلاح: `CPenguin` / `weapon_penguin`؛ FGD: `Killer Penguin`.
* الكيان الحي: `CPenguinGrenade` / `monster_penguin`.
* الملفات: `dlls/weapons/CPenguin.cpp`, `dlls/weapons/CPenguin.h`, `dlls/penguin_grenade.cpp` من OP4 بالالتزام أعلاه.
* الوظيفة: CPenguin::PrimaryAttack() plays events/penguinfire.sc and, server-side, creates monster_penguin at the trace endpoint with forward velocity. CPenguinGrenade::Spawn() sets models/w_penguin.mdl and HuntThink() makes it seek a target before exploding.
* الموديلات: Only from the user's installed gearbox/models/*.mdl via fallback_dir; the repository and ZIP contain no .mdl file.
* لا يوجد `.mdl` داخل ZIP؛ أي موديل بطريق شوهد في ملفات اللعبة المثبّتة مصدره `gearbox/`، لا مستودع ثانٍ.

## 4. فجوات المصدر التي عُولجت بعد بلاغ الخلل

> هذه فحوصات مصدرية فقط؛ لم تُختبر داخل اللعبة.

| الفحص | موجود في الشجرة المولّدة |
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
| `event_hooks` | `9/9 أحداث موصولة` |

أهم الإصلاحات المصدرية: نقل `iuser4 → m_iItems` و`vuser2.y/z → ammo_spores/ammo_762`
إلى تنبؤ عميل BHL؛ توسيع مصفوفة/حلقات التنبؤ إلى `MAX_WEAPONS=64`؛ ملء
`ItemInfoArray` وتسجيل الذخيرة بصيغة OP4 ذات المعاملين؛ تعريف `AmmoInfoArray`
و`GetAmmoIndex` الحقيقي في العميل؛ ربط `OldWeapon`/`HudColor` مع `Weapons`؛
تفريغ حالة الشبكة عند `InitHUD`/`ResetHUD`؛ توليد `delta.lst` مدمج يحافظ
على صحة/eflags الخاصة بـBHL ويضيف `m_iId` بـ6 بتات و`iuser4` الخاص بـOP4.
هذه مرشحات سببية قوية لخلل الأسلحة، وليست إثبات تشغيل.

## 5. الموسيقى: السبب والمسار والإصلاح

* مسار الكود: OP4 dlls/triggers.cpp PlayCDTrack() sends engine 'cd play <track>' (and 'cd stop' for -1). The engine, not the game DLL, maps the track ID to media/*.mp3. Shipped autoexec.cfg/op4weapons.cfg contain no cd/mp3/media command.
* التشخيص: The ZIP contains no media/*.mp3 and no gamestartup.mp3. GoldSrc looks in the active mod's media/ folder and then valve/media; fallback_dir gearbox supplies maps/models/sounds but is not a reliable media/ lookup for CD/MP3 tracks. Therefore an unmodified bhlop4 folder plays the Half-Life soundtrack.
* الإصلاح: setup_op4_media.bat copies only the user's original gearbox/media/*.mp3 (plus gearbox_downloads/media/*.mp3 when present) into bhlop4/media/. No track is invented, renamed, or downloaded.
* موسيقى البداية: gamestartup.mp3 is copied only if the installed OP4 copy provides it; it is never fabricated.
* النتيجة داخل اللعبة: **غير مُختبَر داخل GoldSrc في هذه البيئة**.

مصادر سلوك المحرك (للفحص، لا كدليل تشغيل):
* https://developer.valvesoftware.com/wiki/List_of_HL1_soundtracks
* https://twhl.info/wiki/page/Tutorial:_Making_Music_Play_in_Maps_[GoldSource]/5984
* https://github.com/UCyborg/hl-mp3-fix

## 6. حدود الحزمة

* ZIP لا يضم `.mdl`, `.wav`, `.sc`, `.mp3`, `.bsp`؛ سبرايت `sprites/ag_*.spr` فقط من BHL.
* `setup_op4_media.bat`, `SOURCE_AUDIT.md`, `RUNTIME_TESTS.md`, `INSTALL.md` مرفقة داخل ZIP.
* `MOD_MANIFEST.json` ينص صراحة على `in_game_tested_here: false`.

**الخلاصة:** كل ملف أصلي/معدّل/مكتوب ذاتياً موثّق أعلاه، لكن لا اختبار GoldSrc هنا؛
جدول `RUNTIME_TESTS.md` المرفق لا يحوي علامة نجاح واحدة.

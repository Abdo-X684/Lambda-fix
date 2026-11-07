# إثبات البناء الحقيقي من شجرة `bhl-op4/`

> **الحالة:** تم بناء `client.so` و `hl.so` فعلياً من ملفات `bhl-op4/`، وكلتاهما ELF32
> وتصدّر نقاط دخول BugfixedHL الحقيقية. **لكن المكتبتين لم تُحمّلا بعد داخل المحرك،
> ولم تُختبرا داخل Opposing Force.** يوجد 12 رمزاً غير مُحلول (3 في العميل و9 في الخادم)
> مصدرها أنظمة OP4 التي ما زالت `port-pending`. هذه الرموز موثّقة بالاسم أدناه ولا
> تُخفى ولا تُجاوز. لا يُعلَن اكتمال المشروع.
>
> لا علاقة لهذا البناء بـ `dist/dlls/*.so` أو `dist/bhl-op4-mod.zip` أو Release
> `v0.1.0-linux32`؛ تلك ملفات OP4-root قديمة ولم تُلمس ولم تُقدَّم كنتيجة جديدة.

---

## 1. البيئة المطابقة لمتطلبات BugfixedHL

الشجرة `bhl-op4/` هي شجرة BugfixedHL-Rebased الأصلية (694 ملف BHL)، وتتطلب
`bhl-op4/CMakeLists.txt` الآتي: CMake ≥ 3.25، `nlohmann_json CONFIG`،
`unofficial-pcre CONFIG` (PCRE1)، Python 3.8..<4، Threads، SDL2،
`source_sdk` (الـ submodule المثبّت)، واختيارياً libzip/CURL للتحديث.
محرك Half-Life هنا 32-bit، والـ sandbox لا يحتوي `g++ -m32` ولا
`/usr/lib/i386-linux-gnu/libstdc++.so`، لذلك استُخدم clang المرفق مع Zig موجهاً
إلى `i386-unknown-linux-gnu` (يُربط libc++ داخل الملف بدلاً من الاعتماد على
libstdc++ خارجية 32-bit).

```bash
# أدوات البناء (ليست جزءاً من المستودع؛ /tmp لا يُحفظ في اللقطة)
python3 -m venv /tmp/zenv
/tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
/tmp/zenv/bin/cmake --version        # cmake version 3.30.9
/tmp/zenv/lib/python3.11/site-packages/ziglang/zig version   # 0.17.1
g++ --version | head -1             # g++ 12.2.0 (استُخدم للتشخيص فقط)

# المصادر المثبّتة (مطلوبة قبل البناء)
cd /home/user/Bugfixhl-speedrun-op4
make fetch
#   .cache/upstreams/bugfixhl         = tmp64/BugfixedHL-Rebased @ 4d32095e3c33
#   .cache/upstreams/op4              = twhl-community/halflife-op4-updated @ 5368be7f8eba
#   .cache/upstreams/hl1_source_sdk   = tmp64/hl1_source_sdk @ 11f26656677c881c7c630d03957900e7701da62e
#   .cache/upstreams/valve_hlsdk
```

التبعيات الثالثة تُحمّل تلقائياً بواسطة سكربت البناء مع التحقق من `sha256`:

| الحزمة | المصدر | sha256 |
|---|---|---|
| nlohmann/json v3.11.3 | `https://codeload.github.com/nlohmann/json/tar.gz/v3.11.3` | `0d8ef5af7f9794e3263480193c491549b2ba6cc74bb018906202ada498a79406` |
| PCRE1 (luvit/pcre mirror) | `https://codeload.github.com/luvit/pcre/tar.gz/master` | `5aa545145f0c5a584b54a34f04c2d61c01d31724d3fbae2ee20cd8e3c422594d` |

مكتبات الربط 32-bit تأتي من الشجرة/الـ SDK المثبّت نفسها:
`bhl-op4/lib/public/libSDL2-2.0.so.0`،
`.cache/upstreams/hl1_source_sdk/lib/public/{libtier0,libvstdlib,libsteam_api}.so`
(كلها `ELF32 / Intel 80386`).

---

## 2. أمر البناء الكامل

```bash
cd /home/user/Bugfixhl-speedrun-op4
export PYTHONDONTWRITEBYTECODE=1
python3 tools/build_bhl_base.py \
    --out build-evidence/bhl-base \
    --work /tmp/bhlbuild \
    --sdk .cache/upstreams/hl1_source_sdk \
    --deps .cache/bhl-build/deps \
    --jobs 8
```

السكربت **لا** يخترع نظام بناء بديلاً، بل يعيد إنتاج ما تفعله ملفات CMake الحقيقية:

* قوائم المصادر تُقرأ من `set( SOURCE_FILES ... )` و`list( APPEND SOURCE_FILES ... )`
  و`add_sources(...)` داخل `bhl-op4/` نفسها، **بما فيها فروع `elseif( PLATFORM_LINUX )`**
  (التي تضيف `net_linux.cpp` و`engine_patches_linux.cpp`)، وفروع
  `USE_UPDATER` و`PLATFORM_WINDOWS` تُستبعد لأن البناء بلا updater وعلى Linux.
* التعريفات مأخوذة من `COMMON_DEFINES` + `GAME_COMMON_DEFINES` +
  `SOURCE_SDK_DEFINES` + `target_compile_definitions(client/server ...)`:
  `CLIENT_DLL` للعميل، `SERVER_DLL` للخادم، `VERSION_SAFE_STEAM_API_INTERFACES`،
  `SOURCE_SDK_GFX_PATH="ui/gfx/vgui"`، `SOURCE_SDK_VGUI_NS_ALIAS`،
  `NO_STEAM`، `USE_UPDATER=0`، و`SOURCE_SDK_MIN_STEAM_API` **غير** مُعرَّف
  (لأن `hl1_source_sdk/CMakeLists.txt` يفرضه `FALSE` على غير Windows).
* `target_precompile_headers(client PRIVATE pch.h)` يُعاد إنتاجه بـ
  `-include bhl-op4/src/game/client/pch.h`.
* `appversion.h` يُولَّد من قالب BHL نفسه `bhl-op4/src/common/appversion.h.in`
  بالنسخة `1.14.0-dev+no-git`.
* المكتبات الثابتة `tier1`, `tier2`, `vgui_controls`, `glad`, `semver`, `pcre`
  تُبنى من قوائم CMake الخاصة بها ثم تُربط كـ archives (`ar rcs`)، تماماً كما في
  `add_library(... STATIC ...)`. هذا مهم: في `public/bitvec.h` توجد تخصصات
  صريحة غير `inline`، ولو رُبطت كل الـ objects مباشرة لظهرت رموز مكررة بين
  `bitbuf.o` و`newbitbuf.o`.

**الأوامر الكاملة لكل وحدة ترجمة (401 أمر) محفوظة في:**
`build-evidence/bhl-base/BUILD_COMMANDS.txt`.
**بصمات كل ملف مصدر مترجم (393 ملفاً):** `build-evidence/bhl-base/SOURCES.sha256`.
**السجل الكامل:** `build-evidence/bhl-base/build.log`.
**قائمة كل الرموز غير المحلولة كاملة:** `build-evidence/bhl-base/UNDEFINED_SYMBOLS.txt`.

---

## 3. سجل البناء (كامل)

```
=== bhl-op4 real 32-bit build ===
tree   : /home/user/Bugfixhl-speedrun-op4/bhl-op4
sdk    : /home/user/Bugfixhl-speedrun-op4/.cache/upstreams/hl1_source_sdk
out    : /home/user/Bugfixhl-speedrun-op4/build-evidence/bhl-base
zig    : /tmp/zenv/lib/python3.11/site-packages/ziglang/zig (clang for i386-unknown-linux-gnu)
[deps] nlohmann: nlohmann-json-3.11.3.tar.gz sha256=0d8ef5af7f9794e3263480193c491549b2ba6cc74bb018906202ada498a79406
[deps] pcre: pcre-master.tar.gz sha256=5aa545145f0c5a584b54a34f04c2d61c01d31724d3fbae2ee20cd8e3c422594d
[gen] appversion.h from bhl-op4/src/common/appversion.h.in
[gen] PCRE1 config.h / pcre.h from pcre.h.generic, config.h.generic
[compat] 3 build fixes written to build-evidence/bhl-base/patches
[cmake] client=137 server=128 common=7
[compile] client: 137/137 clean
[compile] server: 128/128 clean
[cmake] tier1=35 tier2=3 vgui_controls=68
[compile] tier1: 35/35 clean
[compile] tier2: 3/3 clean
[compile] vgui_controls: 68/68 clean
[compile] glad: 1/1 clean
[compile] semver: 1/1 clean
[compile] pcre: 20/20 clean
[ar] libvgui_controls.a: 68 objects
[ar] libtier2.a: 3 objects
[ar] libtier1.a: 35 objects
[ar] libglad.a: 1 objects
[ar] libsemver.a: 1 objects
[ar] libpcre.a: 20 objects
[link] client.so: 137 objects, 6 archives, 4 shared libs
[link] client.so: OK (27740848 bytes)
[link] hl.so: 128 objects, 1 archives, 0 shared libs
[link] hl.so: OK (16795192 bytes)
[audit] client.so: 3 unresolved symbols from our own build
[audit] hl.so: 9 unresolved symbols from our own build
```

---

## 4. الأخطاء التي ظهرت وكيف عولجت (بلا تجاوز شكلي ولا إخفاء)

| # | الخطأ الحقيقي | السبب | المعالجة |
|---|---|---|---|
| 1 | `hl1_source_sdk/public/tier1/utlblockmemory.h:142-143` — `std::swap` على `m_nIndexMask` / `m_nIndexShift` في 55 وحدة ترجمة | bit-field لا يمكن ربطه بمرجع غير ثابت؛ يرفضه g++ وclang معاً (تحققنا بملف تجريبي مستقل `/tmp/bitfield_probe.cpp`) | نسخة من شجرة include للـ SDK مع **تبديل يدوي** داخل `CUtlBlockMemory::Swap`؛ الفرق في `patches/utlblockmemory.h.patch`. لا يوجد إصلاح لاحق في تاريخ الـ submodule (آخر تعديل 2020-07-10 "Add Linux support"). |
| 2 | `src/game/client/results.cpp:400` — ربط مرجع غير ثابت بالقيمة المؤقتة التي يعيدها مُكرِّر `std::filesystem::path` | MSVC و`g++ -fpermissive` يتساهلان؛ clang يرفضه في C++17 | وحدة ترجمة واحدة تُرجمت من نسخة overlay موثّقة: `auto &i` → `const auto &i`. الفرق في `patches/results.cpp.patch`. **الوحدات الـ136 الأخرى للعميل تُرجمت مباشرة من `bhl-op4/`.** |
| 3 | `hud_ammo.cpp`, `hud_ammo_secondary.cpp` — `member access into incomplete type 'ConVar'` | BHL يعتمد على `target_precompile_headers(client PRIVATE pch.h)` | استُخدم `-include` لملف `pch.h` الخاص بـ BHL نفسه؛ لا تعديل على المصادر. |
| 4 | `controls.cpp` — `incomplete type vgui2::ISurface` | `vgui_controls` يعتمد على قائمة PCH الخاصة بالـ SDK | أُعيد إنتاج قائمة `target_precompile_headers(vgui_controls ...)` في `patches/vgui_pch.h`. |
| 5 | 54 خطأ `use of undeclared identifier 'SOURCE_SDK_GFX_PATH'`، و`expected class name` لـ `CSteamAPIContext`، و`appversion.h` مفقود، و`PM_*` غير معرّفة | تعريفات/مسارات كانت ناقصة في مسبار الترجمة المباشر | أُضيفت تعريفات CMake الحقيقية و`appversion.h` المولّد و`CLIENT_DLL`/`SERVER_DLL`/`VERSION_SAFE_STEAM_API_INTERFACES`. |
| 6 | `glad/glad.h` و`pcre.h` و`nlohmann/json.hpp` مفقودة | تبعيات غير مثبّتة في النظام | بُني PCRE1 من مصدره (20 ملف C)، واستُخدمت ترويسات nlohmann وglad وSDL2 من الشجرة/الحزم المثبّتة. |
| 7 | 16 ملف OP4 سقطت بـ `'op4_compat.h' file not found` و`'ctf/CTFDefs.h' file not found` | مسارات include لـ `src/game/server/op4/*` كانت ناقصة، و`list( APPEND SOURCE_FILES )` لم يكن يُقرأ | أُضيفت المسارات بعد مسارات BHL (حتى لا تحجبها)، وعُدِّل محلّل CMake ليقرأ `list(APPEND ...)` والفروع الشرطية. |
| 8 | `duplicate symbol: qsort_s`، `pathmatch`, `processor_detect_linux`, ثم `CBitVecT<...>::And` من `bitbuf.o` + `newbitbuf.o` | ربط كل الـ objects مباشرة بدل المكتبات الثابتة | بُنيت archives عبر `ar rcs` ورُبطت بـ `--start-group`، مطابقةً لـ `add_library(STATIC)`. |
| 9 | `gEngfuncs` غير مُحلول في `hl.so` | `src/common/convar.cpp` يختار الفرع بـ `#ifdef SERVER_DLL` | أُضيف `-DSERVER_DLL` للخادم كما في `src/game/server/CMakeLists.txt`. |
| 10 | 5 رموز `NetSendUdp` / `NetReceiveUdp` / `NetClearSocket` / `NetCloseSocket` / `NetGetRuleValueFromBuffer` غير محلولة | `net_linux.cpp` داخل `elseif( PLATFORM_LINUX )` كان يُسقطه المحلّل | محلّل CMake يقيّم الشروط الآن؛ client من 135 إلى 137 وحدة ترجمة، والرموز اختفت. |

---

## 5. النتيجة

| الملف | الحجم | sha256 | ELF | رموز مُصدَّرة | نقاط دخول BHL | `DT_NEEDED` |
|---|---|---|---|---|---|---|
| `build-evidence/bhl-base/client.so` | 27,740,848 | `6b8bcaa7d0d60ed2b6b29e90023552da972ef6b0fd2440b7fb7ab8d9946f9c42` | ELF32 / Intel 80386 | 4,930 | `Initialize`, `HUD_Init`, `HUD_VidInit`, `HUD_Redraw`, `HUD_UpdateClientData`, `HUD_Reset`, `HUD_Frame`, `HUD_Shutdown`, `HUD_Key_Event`, `V_CalcRefdef`, … | `libSDL2-2.0.so.0`, `libtier0.so`, `libvstdlib.so`, `libm`, `libc`, `ld-linux.so.2` |
| `build-evidence/bhl-base/hl.so` | 16,795,192 | `1801ba9c41b968285a57aa8a1136d61eb663f7f32dc378197f4ec52f5c28ea99` | ELF32 / Intel 80386 | 3,331 | `GetEntityAPI`, `GetEntityAPI2`, `GetNewDLLFunctions`, `GiveFnptrsToDll` | `libm`, `libc`, `ld-linux.so.2` |

البيانات الوصفية الكاملة: `build-evidence/bhl-base/MANIFEST.json`.

---

## 6. الرموز غير المحلولة المتبقية — السبب الدقيق وما ينقص

هذه **ليست** رموز المحرك (tier0/vstdlib/SDL2/Steam/libc/libm مُستبعدة من القائمة؛
القائمة الكاملة في `UNDEFINED_SYMBOLS.txt`). هذه رموز يجب أن يوفّرها بناءنا،
وهي نتيجة أن دمج أنظمة OP4 لم يكتمل بعد. الملف `LINK_GAPS.md` يولَّد آلياً بها.

### `client.so` (3)
* `CBasePlayerWeapon::GetNextAttackDelay(float)`
* `typeinfo for CBasePlayerWeapon`
* `vtable for CBasePlayerWeapon`

**السبب:** قاعدة الدمج `op4-weapon-prediction-api` في `merge/bhl_base.py` أضافت
`virtual float GetNextAttackDelay(float delay);` إلى `bhl-op4/src/game/server/weapons.h`
دون إضافة التنفيذ ولا الحقلين `m_flPrevPrimaryAttack` / `m_flLastFireTime`.
بما أنها أول دالة افتراضية غير inline فهي «key function»، فيبقى الـ vtable
و`typeinfo` بلا تعريف في العميل والخادم.

**ما ينقص:** نقل التنفيذ الحقيقي من
`bhl-op4/src/game/server/op4/reference/dlls/weapons.cpp:1071` (خادم) و
`bhl-op4/src/game/client/op4/hl/hl_baseentity.cpp:309` (عميل)، مع إضافة الحقلين
إلى `CBasePlayerWeapon` كقاعدة دمج معلنة، أو تعريف الدالة inline لكلا الطرفين.

### `hl.so` (9)
* نفس الرموز الثلاثة أعلاه.
* `CBaseMonster::AddShockEffect(float, float, float, float, float)` — مُعلَن في
  `basemonster.h` مع حقول الحالة، لكن جسمه في OP4 `dlls/monsters.cpp` الذي لا يمكن
  أن يتعايش مع `monsters.cpp` الخاص بـ BHL. **ينقص:** نقل `AddShockEffect` /
  `UpdateShockEffect` / `ClearShockEffect` (حوالي 50 سطراً من OP4) إلى glue معلن.
* `CRope::DetachObject()` — من نظام الحبال OP4. `CRope.cpp` يترجم نظيفاً بالفعل،
  لكنه غير موصول بـ CMake. **ينقص:** وصل `CRope.cpp` (وتبعياته) بعد التأكد من عدم
  تكرار الرموز مع BHL.
* `CTFGoalFlag::DropFlag(CBasePlayer*)` — من نظام CTF، و`CTFGoalFlag.cpp` لا يزال
  `port-pending` بـ 7 أخطاء في `ctf/ctfplay_gamerules.h` (`override` على دوال غير
  افتراضية في `CGameRules` الخاص بـ BHL). `UTIL_IsCTF()` حالياً `false` لكن الرابط
  يحتاج الرمز. **ينقص:** إصلاح ذاك الهيدر ووصل ملفات CTF أو تعريف معلن للدالة.
* `CWorld::World` — أضيف `static CWorld *World` إلى `cbase.h` كدمج OP4، لكن
  التعريف والتهيئة في `CWorld::Spawn` موجودان فقط في OP4 `dlls/world.cpp` الذي
  يتعارض مع `world.cpp` الخاص بـ BHL. **ينقص:** تعريف وتهيئة معلنان، أو تكييف
  `CGrappleTip.cpp` لاستخدام كيان العالم عبر `INDEXENT(0)`.
* `oldgrapple`, `oldweapons` — متغيرا `cvar_t` مُعلنان `extern` في مصادر OP4 ولم
  يُعرَّفا. **ينقص:** تعريفهما وتسجيلهما في glue أو في `game.cpp` المدمج.

> هذه هي نفس الفجوات المسجلة سابقاً في `bhl-op4/PORT_STATUS.json` (CTF، gamerules،
> world، hgrunt، `GibData`، …) و`docs/BHL_BASE_MERGE.md` «Remaining work»؛
> البناء الحقيقي كشف أنها فجوات **ربط** أيضاً وليست فجوات ترجمة فقط.

---

## 7. الاختبار داخل Opposing Force — لم يُنفَّذ

لا يوجد في بيئة البناء محرك Half-Life، ولا `vgui.so` حقيقي، ولا أصول Opposing Force
من نسخة المستخدم الشرعية. لذلك:

* لم تُحمَّل أي من المكتبتين داخل `hl_linux`، ولم تُشغَّل خريطة، ولم يُختبر سلاح OP4.
* لا يمكن ادعاء «قابلية اللعب» أو «نجاح الدمج» قبل إغلاق رموز القسم 6 ثم التحميل الفعلي.
* المطلوب للاختبار: نسخة GPL/Steam شرعية من Half-Life + Opposing Force، تثبيت
  المكتبتين في مجلد **مستقل غير Valve** (`bhlop4/cl_dlls` و`bhlop4/dlls`) مع
  `liblist.gam` يحتوي `fallback_dir "gearbox"` و`steam_appid.txt` بالقيمة `50`
  و`delta.lst`، و`vgui.so` والأصول من نسخة المستخدم، ثم:
  `hl_linux -game bhlop4 -console -dev +exec speedrun.cfg`.
* لا تُشحن `vgui.so` ولا أصول اللعبة من هذا المستودع.

---

## 8. ما لم يُلمس

`dist/dlls/client.so`، `dist/dlls/hl.so`، `dist/bhl-op4-mod.zip`،
Release `v0.1.0-linux32`، و`build/merged*/` كلها بقيت كما هي (OP4-root قديمة).
لا يوجد PR نحو `main` ولا تحديث Release بناءً على هذا البناء.
`bhl-op4/` نفسها بقيت كما هي: 683 ملفاً BHL مطابقاً بايتاً ببايت + 11 ملفاً
معلَنة الدمج + 154 ملف OP4 + 3 glue، `base.tree_sha256` لم يتغير.
التعديلات الوحيدة على المستودع في هذه المرحلة هي `tools/build_bhl_base.py`،
هذا المستند، ومجلد `build-evidence/bhl-base/`.

# الدمج الصحيح: **BugfixedHL هو الأساس**، وOP4 يُدمج فوقه

> هذا الملف هو **المرجع المعماري الوحيد** بعد تصحيح المسار. الوثائق الأقدم
> (`BHL_MERGE.md`, `RESOLUTION.md`, `MERGE_PLAN.md`) تصف النهج السابق الذي كان
> **OP4 هو الأساس**؛ اقرأ [`LEGACY.md`](LEGACY.md) أولاً.

## 1. لماذا أُعيد البناء

التدقيق الصريح أثبت أن الناتج السابق لم يكن مبنياً على BHL:

* `client.so` كان يحوي 4 ملفات BHL فقط من أصل 110 كائنات في عميل BHL.
* `hl.so` لم يحوِ **أي** كود BHL، بل `bhl_server.cpp` مكتوباً هنا.
* `ConVar / CvarSystem` كان إعادة تنفيذ مستقلة (نسبة تشابه `0.030` مع
  `src/common/convar.cpp`).
* `MERGE_REPORT.json` كان يقول `merged=0`، و`plan.json` فيه صفر قواعد
  `three_way`. لم يحدث دمج فعلي بين الشجرتين.

المطلوب كان ولا يزال: **مشروع مبني على BHL ويستعمل ملفاته**، مع دمج أنظمة
وأسلحة OP4 داخله. هذا ما يفعله `bhl-op4/` الآن.

## 2. البنية (من `bhl-op4/PROVENANCE.json`)

| الطبقة | المصدر | عدد الملفات | الحالة |
| --- | --- | --- | --- |
| **BASE** | `tmp64/BugfixedHL-Rebased @ 4d32095e3c33` (GPL-3.0) | **694** | **677 ملفاً حرفياً** (مطابقة بايت-ببايت للـ commit) + 17 ملفاً عليها دمج معلن |
| **ADD / MERGE** | `twhl-community/halflife-op4-updated @ 5368be7f8eba` | **154** | أسلحة، CTF، rope، كيانات OP4، أحداث العميل |
| **GLUE** | هذا المستودع | **10** | `op4_compat.h`, `op4_compat_late.h`, `op4_compat.cpp`, `op4_link_fixups.cpp`, `op4_entity_enumerator.h`, `op4_ctf_player.cpp`, `op4_weapon_timing.{h,cpp}`, `op4/op4_weapon_events.{h,cpp}` |
| بيان المصدر | — | **858** مدخلاً | لكل ملف: الأصل، `commit`، `sha256`، `action`، أسماء القواعد |

الشجرة كاملة **متتبَّعة في Git** داخل `bhl-op4/` (وليست في `.cache/` المستثنى)،
ومعها `PROVENANCE.json`: `action` يكون `verbatim` / `bhl+op4-merge` /
`op4+compat-patch` / `compat-glue` / `reference-only`.

الحقل `base.tree_sha256` هو بصمة واحدة لكل ملفات BHL على القرص
(`sha256` فوق سطور `المسار` + فراغين + `sha256 الملف` مرتّبة)، و`--check` يعيد
حسابها من القرص ويقارنها — لا تعتمد على وجود `.cache/`.

السائق: `python3 -m merge.bhl_base --out bhl-op4` (حتمي، يعيد البناء من الصفر)،
والمدقق: `python3 -m merge.bhl_base --check --out bhl-op4`.

## 3. قواعد الدمج الحقيقية في ملفات BHL

هذه ليست طبقة تحاكي BHL؛ هذه إضافات OP4 **داخل هيدرات BHL نفسها**
(29 قاعدة مسماة على 14 ملفاً من BHL؛ أحدثها في `BHL_FINAL_AUDIT.md` §2):

| رقم | ملف BHL | ما أُدمج من OP4 |
| --- | --- | --- |
| 1 | `src/game/server/weapons.h` | ثوابت OP4 الإضافية من `dlls/weapons.h` |
| 2 | `src/game/server/weapons.h` | 3 أنواع رصاص: `BULLET_PLAYER_556/762/EAGLE` داخل `enum Bullet` |
| 3 | `src/game/server/weapons.h` | `#include "weaponinfo.h"` لـ `weapon_data_t` |
| 4 | `src/game/server/weapons.h` | `GetWeaponData/SetWeaponData/DecrementTimers/IncrementAmmo/GetNextAttackDelay` على `CBasePlayerWeapon` |
| 5 | `src/game/server/weapons.h` | إعلان `FindHullIntersection` |
| 6 | `src/game/server/weapons.h` | `CLaserSpot::Spawn` يصبح `public` (OP4 `CEagleLaser` يرثه) |
| 7 | `src/game/server/cdll_dll.h` | `enum WeaponId` كاملاً (26 معرّف سلاح OP4) |
| 8 | `src/common/const.h` | `enum WaterLevel` |
| 9 | `src/game/server/skill.h` | **كل** حقول `skilldata_t` الناقصة (OP4 monsters/CTF tuning) |
| 10 | `src/game/server/player.h` | حالة OP4: `ammo_762`, `m_iTeamNum`, `m_WeaponBits`, حقول CTF، `HasSuit()`, rope/autoaim |
| 11 | `src/game/server/basemonster.h` | حالة تأثير الشوك (`AddShockEffect`, `UpdateShockEffect`, `ClearShockEffect`) |
| 12 | `src/game/server/cbase.h` | `CWorld::World`، `EHANDLE::Entity<T>()`، `MySquadTalkMonsterPointer()`، `PlaySentenceCore()` |
| 13 | `src/game/server/monsters.h` | `struct GibLimit` / `struct GibData` من OP4 |
| 14 | `src/game/server/gamerules.h` | `IsCTF()` |
| 15 | `src/game/{server,client}/CMakeLists.txt` | مصادر OP4 المُثبَت ترجمتها تُضاف إلى أهداف BHL |
| 16 | `src/game/server/gamerules.h` | `IPointsForMonsterKill` / `MonsterKilled` (OP4 `dlls/gamerules.h:113,116`) |
| 17 | `src/game/server/monsters.h` | إعلان `CGib::SpawnRandomGibs(..., const GibData&)` (OP4 `dlls/monsters.h:184`) |
| 18 | `src/game/server/cbase.h` | `byte m_EFlags` (OP4 `dlls/cbase.h:169`) |
| 19 | `src/game/server/game.cpp` + `src/game/shared/CMakeLists.txt` | تسجيل cvars/رسالة `FlagIcon`، وTU توقيت السلاح المشترك |

ملفات OP4 الأساسية (`dlls/{util,player,weapons,gamerules,skill,decals,...}`)
موضوعة في `src/game/server/op4/reference/` كمرجع فقط: لا تُترجم ولا تظلّل
هيدرات BHL. إضافاتها هي ما نُقل إلى هيدرات BHL في الجدول أعلاه.

## 4. التوافقيات (مسموح بها، ومعلنة بالاسم)

OP4 يستخدم HLSDK مُحدَّثاً (`bool`, `override`, `Vector` كوسائط أحداث،
`enum class`)، وBHL يستخدم واجهة HLSDK الأصلية (`int/BOOL`, `float *`). لذلك
طُبّقت تحويلات **ميكانيكية مسماة** على مصادر OP4 (كل قاعدة وعدد تطبيقاتها في
`PROVENANCE.json`، 839 تطبيقاً على 103 ملفات OP4):

* قواعد مُشتقّة من هيدرات BHL نفسها: كل دالة يُعلنها BHL بـ `BOOL`/`int`
  ويُعلنها OP4 بـ `bool` تُحوَّل إلى **نوع BHL المُعلَن** (لا إلى نوع مُخمَّن).
* `KeyValue` في BHL يُعيد `void`؛ تُحوَّل الإعلانات وتُجرَّد `return true/false`
  داخل أجسام تلك الدوال فقط (مطابقة الأقواس).
* `bool → BOOL` في معاملات `CanPlaySentence`, `StopFollowing`,
  `PlayScriptedSentence` حتى تطابق الدوال الافتراضية في BHL فعلياً.
* `enum class CTFTeam → enum CTFTeam` (يبقى `CTFTeam::Name` صالحاً ويُقبل مع
  `int` الذي تستخدمه حالة اللاعب في BHL).
* `Holster() → Holster(int skiplocal)`، `Vector::Normalize() → Normalized()`،
  `GET_PRIVATE<T>() → (T*)GET_PRIVATE()`، صبّ `CTFTeam`.
* «تضمين متأخر» لـ `PLAYBACK_EVENT_FULL` و`FindHullIntersection` حتى لا تفسد
  إعلانات BHL (ماكرو مُعرَّف بعد كل الـ `#include`).

**أجسام الدوال بقيت من OP4.** طبقة `op4_compat.*` لا تعيد تنفيذ أي نظام BHL؛
هي فقط توفّر دوال OP4 التي كانت تعيش في `dlls/weapons.cpp` / `util.cpp`
(وهذان لا يمكن ترجمتهما بجانب نسختي BHL)، وتحويلات وسيطات، وثوابت OP4
الناقصة. `UTIL_IsCTF()` تستدعي `g_pGameRules->IsCTF()`؛ قواعد CTF الحقيقية
صارت تُنشأ من `InstallGameRules` وتعيد `true`. أجسام القوائم و`respawn` و
cvars ورسائل OP4 أُضيفت في glue مُوسوم `op4_ctf_player.cpp` (نصّاً من
`player.cpp` / `client.cpp` / `game.cpp`)، و`IsFacing` من `h_ai.cpp:196-210`.
`ctfplay_gamerules.cpp` نفسه موصول، لم يبقَ منقولاً إلى glue.

## 5. إثبات الترجمة (وليس مجرد وجود ملفات)

`python3 tools/verify_bhl_base.py --compile` يترجم **كل** مصدر OP4، و**كل**
مصدر خادم BHL المنسوخ حرفياً، إلى **كائن ELF32 حقيقي**
(`zig c++ -target x86-linux-gnu -c`) مقابل هيدرات الشجرة المدمجة، ويسجّل
النتيجة لكل ملف في `bhl-op4/PORT_STATUS.json` (قسم `files` وقسم `bhl_base`).

النتيجة الحالية:

* **15 / 15 من أسلحة OP4 تُترجم بنجاح** إلى كائنات ELF32:
  `CDisplacer`, `CDisplacerBall`, `CEagle`, `CEagleLaser`, `CGrapple`,
  `CGrappleTip`, `CKnife`, `CM249`, `CPenguin`, `CPipewrench`, `CShockBeam`,
  `CShockRifle`, `CSniperRifle`, `CSpore`, `CSporeLauncher`.
  `readelf -h` على `CEagle.o`: `ELF32 / REL / Intel 80386`.
* **101 / 106 من مصادر خادم BHL نفسها** (المنسوخة حرفياً، لا هيدرات فقط)
  تُترجم إلى كائنات ELF32 داخل الشجرة المدمجة. الخمسة المتعثرة مفصّلة في
  `PORT_STATUS.json` (`appversion.h` يُولّده CMake، مسار Windows في
  `stats.cpp`، `Make2D` من نسخة SDK أخرى، …). مصادر BHL الحقيقية كلها تُترجم
  داخل البناء الفعلي (`server: 179/179 clean`).
* **68 / 71** من مصادر OP4 تُترجم بنجاح إلى كائنات ELF32، منها 15/15 سلاحاً
  وCTF وrope وكيانات (`CTFGoal`, `CTFSpawn`, `CRope`, `CRopeSegment`,
  `CDrillSergeant`, `hgrunt_medic`, `shocktrooper`, `voltigore`, …).
* **66 مصدراً** موصولة بـ `src/game/server/CMakeLists.txt` — هدف البناء لا
  يضمّ ملفاً معطوباً ولا ملفاً فيه فجوة ربط معلنة؛ `--check` يتحقق من أن كل
  ملف موصول نظيف (0 فشل). البناء الفعلي أنتج 179 كائن خادم وصفر فجوة ربط.
* **26 ملف `port_pending`** (21 عميل + 5 خادم). الأربعة التي لا تُترجم بعد
  (`Wxdebug.cpp`، `squeakgrenade.cpp`، `world.cpp`،
  `ctf/ctfplay_gamerules.cpp`) ومصدران نظيفان مستبعدان لتكرار أنظمة BHL
  (`ehandle.cpp`, `UserMessages.cpp`) مفصّلة بأسبابها في `BHL_FINAL_AUDIT.md` §7.

> `--check` يفشل إذا أي مصدر موصول بـ CMake لم يُترجم بنجاح. لا يمكن إدعاء
> «مدموج» لملف لا يُترجم.

## 6. ما لم يُنجز بعد (بصراحة)

1. **لا يوجد `client.so` / `hl.so` جديد من هذه الشجرة.** البناء الكامل يحتاج
   أداة BHL الرسمية: CMake ≥ 3.30، حزم vcpkg (`nlohmann-json`, `pcre`,
   `libzip`, `curl`)، و`tmp64/hl1_source_sdk @ 11f26656677c…` (submodule).
   هذه الأدوات غير متاحة في بيئة البناء الحالية؛ لم أُنتج ثنائيات وهمية.
2. **الثنائيات والـ Release الحالية قديمة**: `dist/dlls/*.so`،
   `dist/bhlop4/`، و`v0.1.0-linux32` مبنية من شجرة **OP4-أساس** السابقة.
   هي **legacy** وليست ناتج `bhl-op4/`؛ لا تستخدمها كدليل على هذا الدمج.
3. مصادر عميل OP4 (`hl_events`, `ev_hldm`, HUD, particleman) منسوخة لكنها
   غير موصولة ببناء العميل بعد (فروق VGUI2/GameUI بين الشجرتين).
4. CTF كـ gamerules **موصول وحقيقي** الآن (`ctfplay_gamerules.cpp`،
   `InstallGameRules`، `IsCTF()`، القوائم، 13 رسالة، 9 cvars،
   `unresolved_own_build_symbols: []`). ما لم يُكمل بعد: HUD عميل OP4
   (تعارض VGUI1/VGUI2) وأي اختبار داخل اللعبة.
5. لا يُدعى أن المود قابل للعب كاملاً، ولا تُضمَّن أصول اللعبة أو
   `vgui.so` الحقيقي.

## 7. الرخص

BHL: **GPL-3.0**. OP4 / Valve HLSDK: رخصة Valve غير التجارية.
[`LICENSES.md`](LICENSES.md) يوضّح الالتزامات؛ هذا المستودع **لا يدّعي
امتثالاً قانونياً** لأي توزيع ثنائي. لا توزّع binaries دون مراجعة الرخصتين.

## 8. الأوامر

```bash
make fetch                                  # الشجرتان المثبّتتان + sha256
make bhl-base                               # إعادة بناء bhl-op4/ من الصفر
python3 tools/verify_bhl_base.py --compile  # كائنات ELF32 + PORT_STATUS.json
make verify-bhl-base                        # فحص PROVENANCE + المصادر الموصولة
make verify                                 # كل فحوصات المستودع
```

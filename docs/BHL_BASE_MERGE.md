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
| **BASE** | `tmp64/BugfixedHL-Rebased @ 4d32095e3c33` (GPL-3.0) | **694** | **683 ملفاً حرفياً** (مطابقة بايت-ببايت للـ commit) + 11 ملفاً عليها دمج معلن |
| **ADD / MERGE** | `twhl-community/halflife-op4-updated @ 5368be7f8eba` | **154** | أسلحة، CTF، rope، كيانات OP4، أحداث العميل |
| **GLUE** | هذا المستودع | **3** | `op4_compat.h`, `op4_compat_late.h`, `op4_compat.cpp` |
| بيان المصدر | — | **851** مدخلاً | لكل ملف: الأصل، `commit`، `sha256`، `action`، أسماء القواعد |

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
(20 قاعدة على 11 ملفاً من BHL):

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

ملفات OP4 الأساسية (`dlls/{util,player,weapons,gamerules,skill,decals,...}`)
موضوعة في `src/game/server/op4/reference/` كمرجع فقط: لا تُترجم ولا تظلّل
هيدرات BHL. إضافاتها هي ما نُقل إلى هيدرات BHL في الجدول أعلاه.

## 4. التوافقيات (مسموح بها، ومعلنة بالاسم)

OP4 يستخدم HLSDK مُحدَّثاً (`bool`, `override`, `Vector` كوسائط أحداث،
`enum class`)، وBHL يستخدم واجهة HLSDK الأصلية (`int/BOOL`, `float *`). لذلك
طُبّقت تحويلات **ميكانيكية مسماة** على مصادر OP4 (كل قاعدة وعدد تطبيقاتها في
`PROVENANCE.json`، 470 تطبيقاً):

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
الناقصة. `UTIL_IsCTF()` تُعيد `false` صراحةً لأن قواعد CTF ليست القواعد
النشطة بعد — مُوثّق، غير مخفي. بعض الإعلانات (`UpdateShockEffect`,
`IsFacing`, `Player_Menu`, …) أجسامها في ملفات OP4 الأساسية غير المدمجة؛
هذه **فجوة ربط** معلنة، لا تُخفى خلف stub وهمي.

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
* **103 / 109 من مصادر خادم BHL نفسها** (المنسوخة حرفياً، لا هيدرات فقط)
  تُترجم إلى كائنات ELF32 داخل الشجرة المدمجة. الستة المتعثرة مفصّلة في
  `PORT_STATUS.json` (`appversion.h` يُولّده CMake، مسار Windows في
  `stats.cpp`، `Make2D` من نسخة SDK أخرى، …).
* **48 / 69** من مصادر خادم OP4 تُترجم بنجاح، منها CTF وrope وكيانات
  (`CTFGoal`, `CTFSpawn`, `CRope`, `CRopeSegment`, `CDrillSergeant`, …).
* **16 مصدراً** موصولة بـ `src/game/server/CMakeLists.txt` (الـ15 +
  `op4_compat.cpp`) — هدف البناء لا يضمّ ملفاً معطوباً ولا ملفاً فيه فجوة ربط
  معلنة. المصادر الـ32 الأخرى الناجحة موجودة في الشجرة وموثّقة في
  `PORT_STATUS.json` لكنها غير موصولة بعد.
* **21 مصدر خادم** ما زال `port_pending`، و**74 مصدر OP4** إجمالاً
  (خادم + عميل) غير موصول؛ لكل واحد قائمة أخطائه الدقيقة في `PORT_STATUS.json`.

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
4. CTF كـ gamerules نشط، وبعض كيانات OP4، لم تُكمل توافقياتها بعد؛
   `UTIL_IsCTF() == false` حتى إتمامها. فجوات الربط المذكورة في القسم 4
   تحتاج نقل الأجسام من ملفات OP4 الأساسية أو كتابة معادلاتها داخل BHL.
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

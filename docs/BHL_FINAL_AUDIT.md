# التقرير النهائي — FINAL BOSS

> **الخلاصة الصريحة:** أُغلقت فجوات الربط الإثني عشر بتطبيقات Opposing Force
> حقيقية، ثم في مرحلة المتابعة وُصل 36 مصدر OP4 إضافي حقيقي بهدف خادم BHL،
> وأُضيف جسمان حقيقيان آخران (`IsFacing` و`CGib::SpawnRandomGibs(GibData)`)
> بعد أن كشف الوصل الجديد عنهما، وأُعيد بناء `client.so` و`hl.so` من الشجرة
> النهائية بصفر فجوة ربط مع اختبارات تنفيذية للأجسام الحقيقية.
> **لكن المشروع لم يُكتمل**: لم يُختبر داخل Opposing Force لأن البيئة لا تحتوي
> محركاً ولا `vgui.so` ولا أصولاً شرعية ولا محمّل ELF32 ديناميكياً. لا اختبار
> مخبّر، ولا نجاح مُستنتَج من الترجمة أو CI. لا PR إلى `main`، ولا Release.

---

## 0. الهوية والـ commit

| البند | القيمة |
|---|---|
| الفرع | `arena/dd30bd22-bugfixhl-speedrun-op4` |
| commit البناء/الأدلة | هذا الالتزام (`git log -1`)؛ سبقه `425a30f5250d…` |
| أساس BHL | `tmp64/BugfixedHL-Rebased @ 4d32095e3c33` |
| مصدر OP4 | `twhl-community/halflife-op4-updated @ 5368be7f8eba` |
| SDK | `tmp64/hl1_source_sdk @ 11f26656677c881c7c630d03957900e7701da62e` |

---

## 1. إغلاق فجوات الربط

الجدول الكامل (المصدر الأصلي، سبب الغياب، التغيير، دليل اختفاء الرمز،
الاختبار الوظيفي) في
[`../build-evidence/bhl-base/LINK_GAP_CLOSURE.md`](../build-evidence/bhl-base/LINK_GAP_CLOSURE.md).

| المكتبة | قبل | بعد |
|---|---|---|
| `client.so` | 3 فجوات | **0** |
| `hl.so` | 9 فجوات | **0** |

- لا دالة فارغة، ولا stub لإسكات الرابط، ولا تعطيل نظام، ولا نسخ عشوائي.
- stub عميل OP4 `hl_baseentity.cpp:309` (`return flTime;`) **رُفض صراحةً**
  واستُخدمت خوارزمية `dlls/weapons.cpp:1069-1099`.
- الأجسام التي لا يمكن أن تتواجد ملفاتها الأصلية بجانب ملفات BHL بنفس الاسم
  نُقلت نصّاً إلى glue مُوسوم باسم الملف والسطور العلوية:
  `dlls/monsters.cpp:3448-3503`، `dlls/world.cpp:483-501`،
  `dlls/game.cpp:588-592,1189-1193`،
  `dlls/ctf/ctfplay_gamerules.cpp:48-67,92-138,141-263`،
  `dlls/cdll_dll.h:200-213`، `dlls/h_ai.cpp:196-210`،
  `dlls/combat.cpp:179-265`.
- ظهرت فجوة جديدة أثناء العمل (`GetLosingTeam`) بعد وصل `CItemCTF.cpp`
  وأُغلقت بجسم OP4 الحقيقي؛ لم تُخفَ.

### 1.1 مرحلة المتابعة: 36 ملف OP4 حقيقي إضافي + فجوة جديدة أُغلقت

وُصل 29 مصدر OP4 نظيفاً (كيانات/CTF/NPC)، ثم 7 مصادر أخرى بعد إصلاح توافق
مُعلَن. الآن **66 مصدر OP4/glue موصول بهدف خادم BHL** (كانت 29).

وصل الـ29 كشف فجوة ربط حقيقية واحدة في `hl.so`:
`IsFacing(entvars_s*, Vector const&)` — يستدعيها `otis.cpp` و`CDrillSergeant.cpp`
و`CRecruit.cpp` و`hgrunt_ally.cpp` وغيرها. الجسم الحقيقي موجود في
`.cache/upstreams/op4/dlls/h_ai.cpp:196-212` ولا يوجد له نظير في BHL
`src/game/server/h_ai.cpp`. أُضيف نصّاً إلى glue موسوم، **لا stub**، مع تحويلين
ميكانيكيين فقط (`Vector::Normalize()` ← `Normalized()`،
`UTIL_MakeVectorsPrivate` يستقبل `float*`).

وصل 7 مصادر أخرى تطلّب خمسة توافقات معلَنة، كلها إضافية ولا تحذف نظام BHL:

| العنصر | المصدر العلوي | الشكل |
|---|---|---|
| `IsFacing` | `dlls/h_ai.cpp:196-210` | جسم حقيقي في glue |
| `CGib::SpawnRandomGibs(pev, n, GibData)` | `dlls/combat.cpp:179-265` | جسم حقيقي في glue + إعلان مُدمج في `monsters.h` |
| `IPointsForMonsterKill` / `MonsterKilled` | `dlls/gamerules.h:113,116` | virtuals مُضافة إلى `CGameRules` |
| `byte CBaseEntity::m_EFlags` | `dlls/cbase.h:169` | حقل مُضاف إلى القاعدة (وأُزيل التكرار من `CBasePlayer`) |
| `CLASS_ALIEN_RACE_X`، `stackalloc`/`stackfree`، `ExplosionCreate` 5-وسيط، `Make2D()` | `dlls/cbase.h:112`، `common/Platform.h:87`، `dlls/explode.h:25`، `dlls/vector.h:115` | ثوابت/ماكروهات/مهايئات في `op4_compat.h` و`op4_compat_late.h` |

`dlls/ehandle.cpp` **استُبعد صراحةً** بعد أن فشل الربط بتكرار
`EHANDLE::Get/Set/operator->` مع `cbase.cpp` في BHL؛ لم يُخفَ الفشل.

**الدليل:** `nm --defined-only` يعرض الرموز الـ12 + الـ2 الجديدين، `nm -u` لا
يعرضها، `nm -S` يثبت أحجام البيانات، `objdump` يثبت أن الأجسام ليست `ret`
فارغة، `LINK_GAPS.md` بلا بنود، `MANIFEST.json` بـ`[]` للمكتبتين.

---

## 2. حماية الهوية

`bhl-op4/PROVENANCE.json` (855 ملفاً):

| الأصل | العدد | الحالة |
|---|---|---|
| BugfixedHL-Rebased | 694 | **680 مطابقة بايت-ببايت** للمصدر المثبّت + **13 دمجاً مُعلَناً** |
| halflife-op4-updated | 154 | ملفات OP4 بـ`upstream_path` |
| glue (هذا المستودع) | 8 | `action: compat-glue`، كل واحد موسوم بمصدره العلوي |
| `base.tree_sha256` | `48f2511ebd7a2e830daf59e99f2f3c48caaaf6c9f70509e9d115aba23e606e2d` | يُعاد حسابه ويتحقق منه `--check` |

**كل تغيير على ملفات BHL مُعلَن بالاسم والسبب** (14 ملفاً). القواعد الجديدة في
هذه المرحلة:

| ملف BHL | القاعدة | السبب |
|---|---|---|
| `src/game/server/gamerules.h` | `op4-gamerules-cbasemonster-fwd` + `op4-gamerules-monster-hooks` | `CHalfLifeCoopplay` يعلّم دالتين `override` غائبتين عن قاعدة BHL |
| `src/game/server/monsters.h` | `op4-gibdata-spawn-overload` | إعلان التحميل الزائد لـ `GibData` (الجسم في glue) |
| `src/game/server/cbase.h` | `op4-entity-eflags` | `pitworm_up.cpp` يضبط `EFLAG_SLERP` عبر `m_EFlags` |
| `src/game/server/player.h` | `op4-player-state` (عُدّل) | أُزيل `m_EFlags` المكرر ونُقل إلى `CBaseEntity` كما في OP4 |
| `src/game/server/CMakeLists.txt` | `op4-cmake-sources` | 66 مصدر OP4/glue موصول بالهدف |

`python3 -m merge.bhl_base --check --out bhl-op4` يتحقق من كل بصمة،
و`tests/test_bhl_base.py::test_07` يقارن الـ680 ملفاً بايت-ببايت بالمصدر المثبّت،
و`test_op4_link_fixups.py::test_06` يثبت أن القواعد معلَنة بأسماء،
و`test_09` يثبت أن المصادر السبعة الجديدة أصلها `op4` لا glue.

**ما لم يحدث:** لم تُحذف ميزة BHL، ولم يُستبدل نظام BHL بمحاكاة، ولم تُغيَّر
واجهة BHL لإخفاء تعارض (فقط حقول/إعلانات مضافة وتسجيل)، وكل إضافة OP4 لها
`upstream_path` أو تعليق باسم الملف والسطور.

---

## 3. إعادة البناء القابلة للتكرار

```bash
python3 -m merge.bhl_base --out bhl-op4
python3 tools/build_bhl_base.py
```

| البند | القيمة |
|---|---|
| وحدات ترجمة | **445** (كلها `ok`) — عميل 138، خادم 179، tier1 35، tier2 3، vgui 68، glad/semver 2، PCRE 20 |
| أوامر موثّقة | 453 في `BUILD_COMMANDS.txt` |
| بصمات مصادر الإدخال | 445 في `SOURCES.sha256` |
| مكتبات ثابتة | 6 أرشيفات، ربط بلا `--allow-shlib-undefined` |
| `client.so` | 27,753,724 B — `37a09c5202c1db3021d0f6c88b6137b24330e040cc4844b8aaf25a8bdaa84f57` |
| `hl.so` | 21,231,808 B — `3eabfa02bf75799ff422c949874ce376a9e4fca64b48d9e38b3520302a594744` |
| رموز مُصدَّرة / undefined | عميل 4,931 / 311، خادم 4,467 / 156 (كلها يوفّرها المحرك/النظام) |
| المعمارية | ELF32 / Intel 80386 (مُثبت بـ`readelf -h`) |
| فجوات البناء | 0 / 0 |

- البناء من `bhl-op4/` فقط؛ لا ثنائيات قديمة، لا شجرة OP4-root، لا `dist`،
  ولا استبدال بعد البناء. بصمات `MANIFEST.json` تُطابق الملفات على القرص.
- سجل الترجمة/الربط الكامل: `../build-evidence/bhl-base/build.log`،
  وقائمة `nm -u` الكاملة: `UNDEFINED_SYMBOLS.txt`.
- الملفات القديمة unchanged: `dist/dlls/client.so`
  `1aa6d65927e9afaeb39660e82f91c961719aa356dd8e263a63d25ad99004a3a9`،
  `dist/dlls/hl.so`
  `302b8ebd6e15c1180338d74cc526af258dac2ebd1911c04b0a31ffd247dbe4e4`،
  `dist/bhl-op4-mod.zip`
  `87b5f5b12fc0710af46bb3482fed768e74578536c11ab92c77a57a5a140bbab3`.
- **قيد مُعلَن:** لم يُنفَّذ `cmake` كاملاً؛ استُخدم استنساخ أمين لقوائم/تعريفات
  CMake مع Zig-clang (مفصّل في `BHL_BASE_BUILD.md`).

---

## 4. التثبيت والاختبار داخل اللعبة: **لم يُنفَّذ**

`python3 tools/probe_runtime_environment.py` →
[`../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md`](../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md)
يسجّل `NOT EXECUTABLE`:

| الفحص | النتيجة الفعلية |
|---|---|
| محرك `hl_linux` / `hw.so` / `vgui.so` | غير موجود |
| أصول OP4 (`.bsp`، `.mdl`، `pak0.pak`) | غير موجودة |
| `/lib/ld-linux.so.2` | غير موجود |
| `libSDL2-2.0.so.0` / `libtier0.so` / `libvstdlib.so` 32-bit | غير موجودة |
| تنفيذ ELF32 ديناميكي بسيط | `FileNotFoundError: ... required file not found` |
| تنفيذ ELF32 **static musl** | `ELF32-RUN-OK`، `rc=0` (يثبت أن العائق هو المحمّل/المكتبات، ليس المعالج) |
| `dist/bhlop4/` | مجرد هيكل تغليف قديم بلا محرك ولا أصول، وثنائياته قديمة ولا تُستخدم كدليل |

**النتيجة:** لا يمكن تحميل المكتبتين، ولا تشغيل خريطة، ولا HUD/UI، ولا أسلحة BHL
أو OP4، ولا تبديل/ذخيرة/إعادة تعبئة، ولا Monster/Rope/Grapple/CTF، ولا مراقبة
أعطال، ولا إعادة اختبار بعد آخر تعديل داخل جلسة لعب. هذه القائمة **ناقصة صراحةً**
وليست مُستنتَجة كنجاح. لا يكفي ظهور قائمة أو تحميل مكتبة، ولم يُدعَّ أي منهما.

---

## 5. كل الاختبارات ونتائجها (بعد آخر تعديل)

| الاختبار | الأمر | النتيجة |
|---|---|---|
| سلامة الشجرة / المطابقة بايت-ببايت | `python3 -m merge.bhl_base --check --out bhl-op4` | `BHL-BASE PROVENANCE OK` |
| ترجمة مصادر OP4 + مصادر BHL إلى ELF32 | `python3 tools/verify_bhl_base.py --compile` | OP4 `68/71` نظيفة، BHL `102/107`، **كل ملف موصول بـ CMake نظيف (0 فشل)** |
| الرموز الـ12 + الرمزان الجديدان / الأجسام / البيانات / القواعد / المصادر الموصولة | `python3 -m unittest tests.test_bhl_base tests.test_op4_link_fixups -v` | **22/22 OK** (منها `test_10` يثبت وصل قواعد CTF و`IsCTF()`) |
| خوارزمية `GetNextAttackDelay` + مُعدّد كيانات OP4 | `make test-op4` | **14 تحقّق PASS** |
| أجسام الإصلاحات الحقيقية مُستخرجة نصّاً من الشجرة (بما فيها `IsFacing`) | `make test-op4-fixups` | **55 تحقّق PASS** |
| نظافة الملفات النصية | `python3 tools/check_hygiene.py` | `hygiene: OK` |
| الاختبارات الكاملة | `make verify` | `== ALL CHECKS PASSED ==` |

`tools/gen_op4_fixup_harness.py` يستخرج أجسام الدوال **نصّاً** من `bhl-op4/`
(لا يعيد كتابتها) ثم يترجمها وينفّذها مع محاكاة لحالة المحرك فقط؛ المنطق
المُختبر هو نفسه الذي في الثنائيات. أُضيفت 8 تحقّقات تنفيذية لـ `IsFacing`
(مخروط `0.96`، إهمال المحور Z، الاتجاه الخلفي، دوران 90°).

---

## 6. CI

- معرّف تشغيل CI ونتائجه مذكوران في الإجابة النهائية للجلسة.
- **CI أخضر ليس إثبات نجاح** ولم يُستخدم كذلك في أي استنتاج أعلاه.

---

## 7. قائمة النواقص الصريحة

1. لا اختبار داخل Opposing Force (السبب الكامل في القسم 4)؛ ولا إعادة اختبار
   داخل اللعبة بعد آخر تعديل.
2. **26 ملف `port_pending`** إجمالاً (21 عميل + 5 خادم). أسباب الخمسة الخادم
   معلَنة، لا مُخفاة:
   - `dlls/ehandle.cpp`: يكرّر `EHANDLE` مع `cbase.cpp` في BHL.
   - `dlls/UserMessages.cpp`: يكرّر `LinkUserMessages()` في BHL (رسائل OP4
     سُجّلت من `GameDLLInit` بديلاً عنه).
   - `dlls/squeakgrenade.cpp`: يكرّر `CSqueak`/`CSqueakGrenade` في BHL.
   - `dlls/world.cpp`: يكرّر `CWorld` في BHL (الـ singleton منقول إلى glue).
   - `dlls/Wxdebug.cpp`: Windows-only داخل `_DEBUG`؛ `tchar.h` غائب ولا كود يُنتَج على Linux.
   - أما `dlls/ctf/ctfplay_gamerules.cpp` **فقد وُصل في هذه الجولة**: نُقلت
     ملكية الـ15 رمزاً CTF من glue إلى الملف الحقيقي، وأضيفت القوائم/cvars/
     الرسائل/الـ virtuals المطلوبة، وصار `IsCTF()` يُفعَّل فعلاً. يبقى أن
     **عميل OP4 (HUD الأعلام/scoreboard/spectator) غير موصول** لتعارض
     VGUI1/VGUI2 مثبت في `COMPLETION_INVENTORY.md` §4، وأن مباراة CTF
     **غير مُختبَرة داخل اللعبة**.
3. ملفات OP4 الأساسية (`weapons.cpp`، `monsters.cpp`، `world.cpp`، `game.cpp`،
   `util.cpp`، `gamerules.cpp`) تبقى `reference-only`؛ لم تُدمج ككتلة.
4. لم يُنفَّذ configure/build بـ CMake كاملاً بمولّد CMake فعلي.
5. لا PR إلى `main`، ولا تحديث Release، ولا توزيع ثنائيات، ولا ادعاء امتثال
   ترخيصي (GPL-3.0 مقابل ترخيص Valve غير التجاري).
6. اختبار تعدد الأشكال لـ `vtable`/`typeinfo` وقت التشغيل غير ممكن بلا محرك؛
   اكتُفي بإثبات الحجم والتعريف وعدم كون الجسم stub.

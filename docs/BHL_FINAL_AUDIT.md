# التقرير النهائي — FINAL BOSS

> **الخلاصة الصريحة:** أُغلقت فجوات الربط الإثني عشر بتطبيقات Opposing Force
> حقيقية، وأُعيد بناء `client.so` و`hl.so` من الشجرة النهائية بصفر فجوة،
> مع اختبارات تنفيذية للأجسام الحقيقية. **لكن المشروع لم يُكتمل**: لم يُختبر
> داخل Opposing Force لأن البيئة لا تحتوي محركاً ولا `vgui.so` ولا أصولاً شرعية
> ولا محمّل ELF32 ديناميكياً. لا اختبار مخبّر، ولا نجاح مُستنتَج من الترجمة أو CI.
> لا PR إلى `main`، ولا Release.

---

## 0. الهوية والcommit

| البند | القيمة |
|---|---|
| الفرع | `arena/dd30bd22-bugfixhl-speedrun-op4` |
| commit البناء/الأدلة | `a5f24e0eebc6365001c20041fd65a88a082a3257` |
| commit تحديث هذا التقرير | التزام لاحق لتحديث هذا التقرير فقط (`git log -1`) |
| أساس BHL | `tmp64/BugfixedHL-Rebased @ 4d32095e3c33` |
| مصدر OP4 | `twhl-community/halflife-op4-updated @ 5368be7f8eba` |
| SDK | `tmp64/hl1_source_sdk @ 11f26656677c881c7c630d03957900e7701da62e` |

---

## 1. المرحلة الأولى — إغلاق الرموز الإثني عشر

الجدول الكامل (المصدر الأصلي، سبب الغياب، التغيير المطلوب، دليل اختفاء الرمز،
الاختبار الوظيفي) في
[`../build-evidence/bhl-base/LINK_GAP_CLOSURE.md`](../build-evidence/bhl-base/LINK_GAP_CLOSURE.md).

| المكتبة | قبل | بعد |
|---|---|---|
| `client.so` | 3 فجوات | **0** |
| `hl.so` | 9 فجوات | **0** |

- لا دالة فارغة، ولا stub لإسكات الرابط، ولا تعطيل نظام، ولا تغيير واجهة BHL
  لإخفاء تعارض، ولا نسخ عشوائي.
- stub عميل OP4 `hl_baseentity.cpp:309` (`return flTime;`) **رُفض صراحةً**
  واستُخدمت خوارزمية `dlls/weapons.cpp:1069-1099`.
- وُصلت ملفات OP4 حقيقية إلى هدف BHL: 8 من `dlls/ctf/` و4 من `dlls/rope/`
  (منها `CTFGoalFlag.cpp` و`CRope.cpp` اللذان يحملان الجسمين المطلوبين).
- الأجسام التي لا يمكن أن تتواجد ملفاتها الأصلية بجانب ملفات BHL بنفس الاسم
  نُقلت نصّاً إلى glue مُوسوم باسم الملف والسطور العلوية:
  `dlls/monsters.cpp:3448-3503`، `dlls/world.cpp:483-501`،
  `dlls/game.cpp:588-592,1189-1193`،
  `dlls/ctf/ctfplay_gamerules.cpp:48-67,92-138,141-263`،
  `dlls/cdll_dll.h:200-213`.
- ظهرت فجوة جديدة واحدة أثناء العمل (`GetLosingTeam`) بعد وصل `CItemCTF.cpp`
  وأُغلقت بجسم OP4 الحقيقي؛ لم تُخفَ.

**الدليل:** `nm --defined-only` يعرض الـ12، `nm -u` لا يعرضها،
`nm -S` يثبت أحجام البيانات، `objdump` يثبت أن الأجسام ليست `ret` فارغة،
`LINK_GAPS.md` بلا بنود، `MANIFEST.json` بـ`[]`.

---

## 2. المرحلة الثانية — حماية الهوية

`bhl-op4/PROVENANCE.json` (855 ملفاً):

| الأصل | العدد | الحالة |
|---|---|---|
| BugfixedHL-Rebased | 694 | **681 مطابقة بايت-ببايت** للمصدر المثبّت + **13 دمجاً مُعلَناً** |
| halflife-op4-updated | 154 | ملفات OP4 بـ`upstream_path` |
| glue (هذا المستودع) | 7 | `action: compat-glue`، كل واحد موسوم بمصدره العلوي |
| `base.tree_sha256` | `48f2511ebd7a2e830daf59e99f2f3c48caaaf6c9f70509e9d115aba23e606e2d` | يُعاد حسابه ويتحقق منه `--check` |

**كل تغيير على ملفات BHL مُعلَن بالاسم والسبب** (13 ملفاً، ومنها 4 جديدة في هذه المرحلة):

| ملف BHL | القاعدة | السبب |
|---|---|---|
| `src/game/server/weapons.h` | `op4-weapon-timing-state` | حقلا `m_flPrevPrimaryAttack` / `m_flLastFireTime` المطلوبان للخوارزمية الحقيقية |
| `src/game/server/cbase.h` | `op4-cworld-ctor-dtor` | إعلان باني/هادم `CWorld` ل singleton OP4 |
| `src/game/server/game.cpp` | `op4-gamedllinit-decls` + `op4-gamedllinit-call` | تسجيل cvars OP4 الحقيقية ورسالة `FlagIcon` من `GameDLLInit` في BHL (وإلا لكانت بيانات ميتة) |
| `src/game/shared/CMakeLists.txt` | `op4-shared-weapon-timing-cmake` | ترجمة TU التوقيت في المكتبتين عبر قائمة BHL المشتركة نفسها |

الـ9 الأخرى كانت موجودة من قبل وموثّقة في `BHL_BASE_MERGE.md`.
`python3 -m merge.bhl_base --check --out bhl-op4` يتحقق من كل بصمة،
و`tests/test_bhl_base.py::test_07` يقارن الـ681 ملفاً بايت-ببايت بالمصدر المثبّت،
و`test_op4_link_fixups.py::test_06` يثبت أن التغييرات الأربعة معلَنة بقواعد مسماة.

**ما لم يحدث:** لم تُحذف ميزة BHL، ولم يُستبدل نظام BHL بمحاكاة، ولم تُغيَّر
واجهة BHL لإخفاء تعارض (فقط حقول/إعلانات مضافة وتسجيل)، وكل إضافة OP4 لها
`upstream_path` أو تعليق باسم الملف والسطور.

---

## 3. المرحلة الثالثة — إعادة البناء القابلة للتكرار

```bash
python3 -m merge.bhl_base --out bhl-op4
python3 tools/build_bhl_base.py
```

| البند | القيمة |
|---|---|
| وحدات ترجمة | **408** (كلها `ok`) — عميل 138، خادم 142، tier1 35، tier2 3، vgui 68، glad/semver 2، PCRE 20 |
| أوامر موثّقة | 416 في `BUILD_COMMANDS.txt` |
| بصمات مصادر الإدخال | 408 في `SOURCES.sha256` |
| مكتبات ثابتة | 6 أرشيفات، ربط بلا `--allow-shlib-undefined` |
| `client.so` | 27,753,660 B — `3230033ffaf2634b7c485ec9a19611aa541a7c6c20078eb4f47fda058018b9a8` |
| `hl.so` | 17,415,276 B — `791e853b664366a37b9adb4948537c80c8f43a1a22f36db81f44ca917f54fdeb` |
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

## 4. المرحلة الرابعة — التثبيت والاختبار داخل اللعبة: **لم يُنفَّذ**

`python3 tools/probe_runtime_environment.py` →
[`../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md`](../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md)
يسجّل:

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

## 5. المرحلة الخامسة — كل الاختبارات ونتائجها

| الاختبار | الأمر | النتيجة |
|---|---|---|
| سلامة الشجرة / المطابقة بايت-ببايت | `python3 -m merge.bhl_base --check --out bhl-op4` | `BHL-BASE PROVENANCE OK` |
| ترجمة مصادر OP4 + مصادر BHL إلى ELF32 | `python3 tools/verify_bhl_base.py --compile` | OP4 `59/70` نظيفة، BHL `103/108`، **كل ملف موصول بـ CMake نظيف (0 فشل)** |
| الرموز الإثني عشر / الأجسام غير الفارغة / البيانات / القواعد المعلَنة | `python3 -m unittest tests.test_op4_link_fixups -v` | **7/7 OK** |
| خوارزمية `GetNextAttackDelay` + مُعدّد كيانات OP4 | `make test-op4` | **14 تحقّق PASS** |
| أجسام الإصلاحات الحقيقية مُستخرجة نصّاً من الشجرة | `make test-op4-fixups` | **39 تحقّق PASS** |
| الاختبارات الكاملة | `make verify` | `== ALL CHECKS PASSED ==` |
| CI | `gh run list` | معرّف التشغيل في الإجابة النهائية للجلسة |

`tools/gen_op4_fixup_harness.py` يستخرج أجسام الدوال **نصّاً** من
`bhl-op4/` (لا يعيد كتابتها) ثم يترجمها وينفّذها مع محاكاة لحالة المحرك فقط؛
المنطق المُختبر هو نفسه الذي في الثنائيات.

---

## 6. CI

- معرّف تشغيل CI ونتائجه مذكوران في الإجابة النهائية للجلسة.
- لا يضيف هذا الالتزام أي تغيير على الشجرة أو الثنائيات؛ البناء موثّق في الالتزام أعلاه.
- **CI أخضر ليس إثبات نجاح** ولم يُستخدم كذلك في أي استنتاج أعلاه.

---

## 7. قائمة النواقص الصريحة

1. لا اختبار داخل Opposing Force (السبب الكامل في القسم 4).
2. `dlls/ctf/ctfplay_gamerules.cpp` **غير موصول**: يحتاج حقول `CBasePlayer`
   الخاصة بـ OP4 (`m_szTeamModel`، `m_szTeamName`، `m_iSnipeKills`...) وثوابت
   قوائم OP4 و`UTIL_FindPlayers` و`SecondsToTime`. إضافتها تعني استبدال أنظمة
   BHL — ممنوع. **النتيجة العملية:** `CGameRules::IsCTF()` يبقى `false`، فقواعد
   CTF لا تُفعَّل ومباراة CTF كاملة غير قابلة للعب؛ كيانات CTF ورسائل HUD
   موجودة ومُختبرة كودياً فقط.
3. 62 ملف OP4 ما زالت `port-pending`، منها `CItemBackpackCTF`،
   `CItemLongJumpCTF`، `CItemPortableHEVCTF`، `CItemRegenerationCTF`،
   `CTFDetect`، `ctfplay_gamerules.cpp`.
4. ملفات OP4 الأساسية (`weapons.cpp`، `monsters.cpp`، `world.cpp`، `game.cpp`،
   `util.cpp`، `gamerules.cpp`) تبقى `reference-only`؛ لم تُدمج ككتلة.
5. لم يُنفَّذ configure/build بـ CMake كاملاً.
6. لا PR إلى `main`، ولا تحديث Release، ولا توزيع ثنائيات، ولا ادعاء امتثال
   ترخيصي (GPL-3.0 مقابل ترخيص Valve غير التجاري).
7. اختبار تعدد الأشكال لـ `vtable`/`typeinfo` وقت التشغيل غير ممكن بلا محرك؛
   اكتُفي بإثبات الحجم والتعريف وعدم كون الجسم stub.

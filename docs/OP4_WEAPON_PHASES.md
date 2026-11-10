# دمج أسلحة Opposing Force في BHL — سجل المراحل

**الهدف:** الحفاظ على BHL كما يعمل الآن، وإضافة أسلحة OP4 الناقصة **سلاحاً واحداً
في كل مرة**، بتغييرات صغيرة قابلة للمراجعة وبأدلة لكل مرحلة.

**الأساس:** `BugfixedHL-Rebased @ 4d32095e3c33` +
`halflife-op4-updated @ 5368be7f8eba`. الشجرة المولّدة: `bhl-op4/`.

**ما لا يمسّه هذا العمل:** حركة اللاعب/bhop، الوحوش، VGUI2، أي نظام BHL يعمل،
ونقل ملفات OP4 بالجملة. التعديلات محصورة في تسجيل الأسلحة، الذخيرة، الأصوات،
أحداث العرض من جهة العميل، واعتمادية واحدة لازمة لتشغيل حدث M249.

> ⚠️ **نوع الاختبار في كل المراحل أدناه: بناء + ربط + فحص مصدر ورموز ELF32.
> ليس اختباراً داخل اللعبة.** لا محرك GoldSrc، ولا `hw.so` / `vgui.so`، ولا أصول
> OP4 شرعية، ولا محمّل ELF32 ديناميكي في هذه البيئة
> ([`RUNTIME_ENVIRONMENT.md`](../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md)).
> لذلك **لا يُعلَن أي سلاح «يعمل داخل اللعبة»** قبل تجربة فعلية خارجة عن هذه البيئة.

---

## 1. الملفات المغيّرة (كل المراحل)

| ملف | التعديل |
| --- | --- |
| `merge/op4_weapon_events.py` | مولّد يستخرج **نص OP4 الأصلي حرفياً** لدوال `EV_*` وتعدادات الأنيميشن ومعرّفات الرصاص؛ كل مرحلة تضيف **صفّ بيانات واحد** فقط |
| `merge/bhl_base.py` | قواعد دمج معلَنة بأسماء: `op4-wprecache-op4-weapons`، `op4-client-weapon-event-decls`، `op4-client-weapon-event-hooks`، `op4-client-setlocalbody`؛ وصل `op4/op4_weapon_events.cpp` بـ `client/CMakeLists.txt` |
| `bhl-op4/src/game/server/weapons.cpp` | داخل `W_Precache()`: 10 أسطر `UTIL_PrecacheOtherWeapon` + 3 ذخائر + 3 أصوات `spore_hit` — إضافة فقط، لم يُحذف أي سطر BHL |
| `bhl-op4/src/game/client/hl/hl_events.cpp` | 9 تصريحات `extern "C"` + 9 `pfnHookEvent` لأحداث OP4 — إضافة فقط داخل `Game_HookEvents()` |
| `bhl-op4/src/game/client/hl/hl_weapons.cpp` | دمج معلَن واحد: `SetLocalBody()` (اعتمادية حدث M249) مطبَّق على مصفوفة BHL `g_pWpns[]` بدلاً من قائمة كائنات OP4 |
| `bhl-op4/src/game/client/op4/op4_weapon_events.h` | **جديد**: تعدادات أنيميشن OP4 حرفياً + معرّفات الرصاص `556/762/EAGLE` |
| `bhl-op4/src/game/client/op4/op4_weapon_events.cpp` | **جديد**: 9 أجسام `EV_*` الأصلية حرفياً + حالة العميل اللازمة (`g_iClub` معرَّف، `g_iSwing` مستعار من BHL)؛ هيدرات BHL بـ `../` حتى لا تحجبها هيدرات OP4 |
| `tools/verify_bhl_base.py` | فحص ترجمة حقيقي لوحدات glue للعميل (PCH + defs العميل) وتسجيلها في `PORT_STATUS.json` |
| `tools/run_weapon_phase.py` | مشغّل يفرض «سلاح واحد في كل مرة» ويحفظ سجلات كل مرحلة في `build-evidence/weapon-phases/<cls>/` |
| `tests/test_op4_weapons.py` | **جديد**: 7 اختبارات تُطبَّق على كل سلاح (تسجيل خادم، ربط حدث، مطابقة الجسم مع OP4، قواعد الدمج، رموز ELF32 غير فارغة، صفر فجوة ربط، تأكيد أن الاختبار ليس داخل اللعبة) |
| `tests/test_bhl_base.py`، `.github/workflows/ci.yml` | فحص الأعداد صار مجموعياً (`verbatim + merged == 694`) بدلاً من تثبيت رقم يتغيّر مع كل مرحلة |
| `tests/fixtures/op4_weapon_events.json` | **جديد**: بصمات sha256 لأجسام `EV_*` التسعة من الـ commit المثبّت، ليُثبت CI تطابقها بدون وجود `.cache/upstreams` |

### الفرق (diff)

```sh
git diff c067b51~1 -- merge/op4_weapon_events.py merge/bhl_base.py \
  bhl-op4/src/game/server/weapons.cpp \
  bhl-op4/src/game/client/hl/hl_events.cpp \
  bhl-op4/src/game/client/hl/hl_weapons.cpp \
  bhl-op4/src/game/client/op4/op4_weapon_events.h \
  bhl-op4/src/game/client/op4/op4_weapon_events.cpp \
  bhl-op4/src/game/client/CMakeLists.txt \
  tools/verify_bhl_base.py tools/run_weapon_phase.py tests/test_op4_weapons.py
```

---

## 2. المراحل (كل مرحلة = صف بيانات واحد + بناء كامل + اختبار)

| # | السلاح | التسجيل / الذخيرة / الأصوات | حدث العميل | البناء والاختبار | دليل المرحلة |
| --- | --- | --- | --- | --- | --- |
| 1 | `weapon_eagle` | `weapon_eagle` | `events/eagle.sc` → `EV_FireEagle` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_eagle/RESULT.json) |
| 2 | `weapon_pipewrench` | `weapon_pipewrench` (+ `g_iClub`) | `events/pipewrench.sc` → `EV_Pipewrench` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_pipewrench/RESULT.json) |
| 3 | `weapon_m249` | `weapon_m249` + `ammo_556` | `events/m249.sc` → `EV_FireM249` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_m249/RESULT.json) |
| 4 | `weapon_displacer` | `weapon_displacer` | `events/displacer.sc` → `EV_FireDisplacer` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_displacer/RESULT.json) |
| 5 | `weapon_shockrifle` | `weapon_shockrifle` | `events/shock.sc` → `EV_FireShockRifle` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_shockrifle/RESULT.json) |
| 6 | `weapon_sporelauncher` | `weapon_sporelauncher` + `ammo_spore` + 3 أصوات `spore_hit` | `events/spore.sc` → `EV_FireSpore` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_sporelauncher/RESULT.json) |
| 7 | `weapon_sniperrifle` | `weapon_sniperrifle` + `ammo_762` | `events/sniper.sc` → `EV_SniperRifle` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_sniperrifle/RESULT.json) |
| 8 | `weapon_knife` | `weapon_knife` (+ `g_iSwing` من BHL) | `events/knife.sc` → `EV_Knife` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_knife/RESULT.json) |
| 9 | `weapon_penguin` | `weapon_penguin` | `events/penguinfire.sc` → `EV_PenguinFire` | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_penguin/RESULT.json) |
| 10 | `weapon_grapple` | `weapon_grapple` | **لا يوجد حدث عميل في OP4** (`hl_events.cpp` يربط 9 فقط) | عميل 139/139، خادم 179/179، 7/7 | [`RESULT.json`](../build-evidence/weapon-phases/weapon_grapple/RESULT.json) |

كل مجلد مرحلة يحتوي أيضاً على `regen` / `build` / `verify` / `weapon_tests`
(سجلات كاملة) و`RESULT.json` فيه بصمات `client.so` و`hl.so` لتلك المرحلة.

`make verify` و`unittest` أُعيدا بعد **كل** مرحلة على حدة: `ALL CHECKS PASSED`
و`7/7 OK` في المراحل العشر. بعد إصلاح خطأ CI أُضيف اختبار انحدار ثامن
(`test_08`)، فأصبحت المجموعة النهائية `8/8 OK` والمجموع الكلي `30/30 OK`.

---

## 3. البناء النهائي (بعد المرحلة 10)

| البند | النتيجة |
| --- | --- |
| `python3 -m merge.bhl_base --out bhl-op4` | rc=0، 858 إدخال provenance |
| `python3 tools/build_bhl_base.py --out build-evidence/bhl-base` | rc=0 — عميل `139/139`، خادم `179/179`، `446` وحدة ترجمة، `454` أمراً، **فجوات الربط `[]`** |
| `client.so` | `27,802,960` B — `3cae1d779c5a2a2d47e138baa43a45bb06d870037dd6da995f581532d32d9100` |
| `hl.so` | `21,232,512` B — `09550d9b2acc2f0fca05857d8d6eaf3112f1fcf32d0fd40a6404884463f46cf1` |
| `python3 tools/verify_bhl_base.py --compile` | rc=0 — OP4 `68/71`، BHL `101/106`، **glue العميل `1/1`** |
| `python3 tools/verify_bhl_base.py --check` | rc=0 — `BHL-BASE TREE OK`، 67 مصدراً موصولاً بـ CMake |
| `make verify` | rc=0 — `ALL CHECKS PASSED` |
| `unittest tests.test_bhl_base tests.test_op4_link_fixups tests.test_op4_weapons` | rc=0 — `30/30 OK` |
| `PROVENANCE.json` | BHL `677` مطابق بايت-ببايت + `17` دمجاً معلَناً، OP4 `154`، glue `10` |

### إثبات الرموز (بناء/ربط، **ليس داخل اللعبة**)

* `nm --defined-only client.so` → الرموز التسعة `EV_FireEagle`, `EV_Pipewrench`,
  `EV_FireM249`, `EV_FireDisplacer`, `EV_FireShockRifle`, `EV_FireSpore`,
  `EV_SniperRifle`, `EV_Knife`, `EV_PenguinFire` كلها `T` (غير فارغة،
  `objdump` يثبت أنها ليست stubs)، مع `g_iClub` و`SetLocalBody(int,int)`.
* `nm --defined-only hl.so | c++filt` → `CEagle::Spawn()`, `CPipewrench::Spawn()`,
  `CM249::Spawn()`, `CDisplacer::Spawn()`, `CShockRifle::Spawn()`,
  `CSporeLauncher::Spawn()`, `CSniperRifle::Spawn()`, `CKnife::Spawn()`,
  `CPenguin::Spawn()`, `CGrapple::Spawn()` وكل `Precache()` المقابلة.
* `strings hl.so` → أصناف الأسلحة والذخائر العشرة/الثلاثة مسجَّلة.
* اختبار آلي يقارن كل جسم `EV_*` مع `cl_dll/ev_hldm.cpp` للـ commit المثبّت
  **حرفياً**، ويثبت بقاء تسجيلات وأحداث BHL الأصلية دون حذف.
* **ما لم يُختبر:** إطلاق، إعادة تعبئة، ضرر، ذخيرة، أنيميشن، صوت، ظهور النموذج
  داخل اللعبة. لا توجد بيئة لعبة ولا أصول شرعية.

---

## 4. الأخطاء التي ظهرت وحُلّت (من الكود وسجلات البناء)

1. **تعارض رابط C/C++ (المرحلة 1):** تضمين `ev_hldm.h` وصل إلى هيدر OP4 أولاً،
   فظهر `declaration of 'EV_FireEagle' has a different language linkage`.
   الحل: تضمين هيدرات BHL صراحة بصيغة `../hud.h` و`../cl_util.h` و
   `../eventscripts.h` و`../ev_hldm.h` و`../cl_dll.h`.
2. **فجوة إثبات (المرحلة 1):** `verify_bhl_base.py` لم يكن يترجم glue العميل،
   فكان `make verify` يفشل بـ `wired source did not compile`. أُضيف فحص ترجمة
   حقيقي لوحدات العميل الموصولة (`client_glue: 1/1`).
3. **`SetLocalBody` (المرحلة 3):** جسم `EV_FireM249` الأصلي يستدعي دالة من
   `cl_dll/hl/hl_weapons.cpp` الخاص بـ OP4، ولا يمكن وصل ذلك الملف لأنه يكرّر
   نظام تنبؤ BHL. الحل: دمج معلَن باسم `op4-client-setlocalbody` يطبّق **نفس
   العملية** على مصفوفة BHL `g_pWpns[]`. لا إعادة كتابة لنظام BHL، ولا stub.
4. **`g_iSwing` (المرحلة 8):** BHL يعرّف هذا المتغير بالفعل في
   `src/game/client/ev_hldm.cpp:1183`؛ glue يصرّحه `extern` بدلاً من تعريفه مرة
   ثانية. `g_iClub` خاص بـ OP4 فعرِّف داخل glue.
5. **`enum class DisplacerMode` و`DISPLACER_NUM_BEAMS` (المرحلة 4):** المولّد
   وُسّع لاستخراج `enum class` وتصريحات خارج التعداد حرفياً؛ لم تُكتب ثوابت
   يدوياً.
6. **خطأ في اختبار (المرحلة 1):** تعبير نمطي بلا `re.M`؛ صُحّح إلى تطابق سطر
   `nm` الصريح.
7. **فشل CI بعد الدفع (`make verify-bhl-base`):** `merge/op4_weapon_events.py`
   كان يبني glue عند **الاستيراد** فيقرأ `.cache/upstreams/op4/cl_dll/ev_hldm.cpp`،
   وهذا المسار مستثنى من Git وغير موجود في نسخة CI النظيفة → `FileNotFoundError`
   في مهمّتَي `verify` و`bhl-base-compile`. السبب من سجل CI وليس تخميناً.
   الحل: (أ) `_build()` صار كسولاً عبر `weapon_events()` لا يُستدعى إلا عند توليد
   الشجرة فعلاً؛ (ب) قراءة تعداد `Bullet` من **مصدر OP4 المثبّت** بدل الشجرة
   المولّدة (التي تُنسخ أولاً بنسخة BHL قبل الدمج، فكانت تُنتج تعداداً فارغاً)؛
   (ج) إضافة `tests/fixtures/op4_weapon_events.json` ببصمات الأجسام التسعة
   حتى يبقى إثبات «حرفياً» قائماً على CI؛ (د) اختبار انحدار `test_08` يحاكي غياب
   الكاش. أُعيد التوليد فطابقت الملفات المولّدة الحالة السابقة بايت-ببايت،
   وأُعيد `make verify` محلياً **مع إخفاء `.cache/upstreams` كاملاً** فنجح.

**لا توجد أخطاء بناء أو ربط متبقية.** `unresolved_own_build_symbols: []`
للمكتبتين.

---

## 5. النواقص الصريحة (تمنع ادّعاء الاكتمال)

1. **لا اختبار داخل اللعبة إطلاقاً** — بيئي: لا محرك، لا `vgui.so`، لا أصول OP4
   شرعية، لا محمّل ELF32 ديناميكي. كل ما سبق إثبات بناء/ربط/مصدر.
2. **تنبؤ العميل (client-side prediction):** BHL يمتلك كائنات تنبؤ للأسلحة الأصلية
   فقط (`g_pWpns[]`)؛ كائنات تنبؤ OP4 (`g_Eagle`, `g_M249`, …) غير مضافة لأن
   إضافتها تعني وصل `cl_dll/hl/hl_weapons.cpp` كاملاً وهو يكرّر نظام BHL — وهذا
   خارج النطاق المسموح. لذلك `SetLocalBody()` لا يجد كائن تنبؤ لأسلحة OP4 حالياً،
   مع أن `EV_WeaponAnimation(anim, body)` في الحدث الأصلي يمرّر الـ body للمحرك.
   هذا فرق **غير مُختبَر داخل اللعبة** ولا يُعلَن أنه مكافئ تماماً.
3. **أصول HUD/النماذج/الأصوات:** ملفات `sprites/*.spr` و`models/v_*.mdl` وملفات
   `weapon_*.txt` وأصوات OP4 غير مضمّنة قانونياً في المستودع؛ `Precache()` الأصلي
   والحدث الأصلي يشيران إليها، لكن تشغيلها الفعلي غير مُثبت.
4. **25 ملف OP4 ما زالت `port_pending`** — ليست أخطاء في هذه المرحلة؛ أسبابها معلَنة
   في [`COMPLETION_INVENTORY.md`](COMPLETION_INVENTORY.md) ولا تُنقل بالجملة.
5. `weapon_shockroach` صنف خادم مرتبط لكن OP4 نفسه لا يسجّله في `W_Precache()`
   (سلاح وحش)؛ لم يُضف تسجيلاً غير موجود في المصدر.

---

## 6. الحكم

الأسلحة العشرة `weapon_eagle`, `weapon_pipewrench`, `weapon_m249`,
`weapon_displacer`, `weapon_shockrifle`, `weapon_sporelauncher`,
`weapon_sniperrifle`, `weapon_knife`, `weapon_penguin`, `weapon_grapple`
**مُسجَّلة وموصولة ومترجمة ومربوطة** بإثبات بناء/ربط/مصدر، مع ذخائرها وأصواتها
وأحداث عرضها الأصلية حرفياً، وبصفر فجوة ربط، ودون المساس بحركة اللاعب أو الوحوش
أو VGUI2 أو أنظمة BHL العاملة.

**غير مُثبتة داخل اللعبة، ولا يُعلَن أي منها مكتملاً.** النواقص في §5 تحتاج بيئة
GoldSrc وأصولاً شرعية واختباراً فعلياً قبل أي حكم بالتشغيل.

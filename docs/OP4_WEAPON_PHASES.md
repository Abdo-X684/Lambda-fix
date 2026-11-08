# دمج أسلحة Opposing Force في BHL — سجل المراحل

**الهدف:** الحفاظ على BHL كما يعمل الآن، وإضافة أسلحة OP4 الناقصة **سلاحاً واحداً
في كل مرة**، بتغييرات صغيرة قابلة للمراجعة وبأدلة لكل مرحلة.

**الأساس:** `BugfixedHL-Rebased @ 4d32095e3c33` +
`halflife-op4-updated @ 5368be7f8eba`. الشجرة المولّدة: `bhl-op4/`.

**ما لا يمسّه هذا العمل:** حركة اللاعب/bhop، الوحوش، VGUI2، أي نظام BHL يعمل،
ونقل ملفات OP4 بالجملة. التعديلات محصورة في ملفات الأسلحة، التسجيل، الذخيرة،
أحداث العرض من جهة العميل، والاعتماديات اللازمة لتشغيل السلاح فقط.

> ⚠️ **نوع الاختبار في كل المراحل أدناه: بناء + ربط + فحص مصدر ورموز ELF32.
> ليس اختباراً داخل اللعبة.** لا محرك GoldSrc، ولا `hw.so` / `vgui.so`، ولا أصول
> OP4 شرعية، ولا محمّل ELF32 ديناميكي في هذه البيئة
> ([`RUNTIME_ENVIRONMENT.md`](../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md)).
> لذلك **لا يُعلَن أي سلاح «يعمل داخل اللعبة»** قبل تجربة فعلية خارجة عن هذه البيئة.

---

## المرحلة 1 — `weapon_eagle` (Desert Eagle)

### الملفات المغيّرة

| ملف | التعديل |
| --- | --- |
| `merge/op4_weapon_events.py` | مولّد جديد يستخرج **نص OP4 الأصلي حرفياً** لدوال `EV_*` وتعدادات الأنيميشن ومعرّفات الرصاص، ويولّد glue للعميل فقط |
| `merge/bhl_base.py` | استيراد المولّد، إصدار ملفي glue، وصل `op4/op4_weapon_events.cpp` بـ `client/CMakeLists.txt`، وإضافة قواعد دمج معلَنة بأسماء: `op4-wprecache-op4-weapons`، `op4-client-weapon-event-decls`، `op4-client-weapon-event-hooks` |
| `bhl-op4/src/game/server/weapons.cpp` | سطر واحد داخل `W_Precache()`: `UTIL_PrecacheOtherWeapon("weapon_eagle");` — بدون هذا لا يُسجَّل الصنف في `WeaponList` |
| `bhl-op4/src/game/client/hl/hl_events.cpp` | تصريح `extern "C" void EV_FireEagle(event_args_s*);` + `pfnHookEvent("events/eagle.sc", EV_FireEagle);` داخل `Game_HookEvents()` |
| `bhl-op4/src/game/client/op4/op4_weapon_events.h` | **جديد**: `enum DesertEagleAnim` و`BULLET_PLAYER_556/762/EAGLE` بقيم OP4، مأخوذة نصّاً |
| `bhl-op4/src/game/client/op4/op4_weapon_events.cpp` | **جديد**: جسم `EV_FireEagle` الأصلي (صوت، وميض فوهة، قذيفة فارغة، `V_PunchAxis`، `EV_HLDM_FireBullets`)؛ يشمل هيدرات BHL بـ `../` حتى لا تحجبها هيدرات OP4 |
| `tools/verify_bhl_base.py` | فحص ترجمة حقيقي لوحدات glue الخاصة بالعميل (مع PCH وdefs الخاصة بالعميل) وتسجيلها في `PORT_STATUS.json` |
| `tests/test_op4_weapons.py` | **جديد**: 7 اختبارات لكل سلاح (تسجيل خادم، ربط حدث عميل، مطابقة الجسم مع OP4 بايت-ببايت، قواعد الدمج المعلَنة، رموز ELF32 غير فارغة، صفر فجوة ربط، وتأكيد أن الاختبار ليس داخل اللعبة) |
| `tests/test_bhl_base.py`، `.github/workflows/ci.yml` | تحديث الأعداد الثابتة بعد الدمج الجديد (678/16، glue=10، BHL `>=106`) |

### الفرق (diff)

```sh
git diff 6353375 -- merge/op4_weapon_events.py merge/bhl_base.py \
  bhl-op4/src/game/server/weapons.cpp \
  bhl-op4/src/game/client/hl/hl_events.cpp \
  bhl-op4/src/game/client/op4/op4_weapon_events.h \
  bhl-op4/src/game/client/op4/op4_weapon_events.cpp \
  bhl-op4/src/game/client/CMakeLists.txt \
  tools/verify_bhl_base.py tests/test_op4_weapons.py
```

### نتائج البناء

| البند | النتيجة |
| --- | --- |
| `python3 -m merge.bhl_base --out bhl-op4` | rc=0، 858 إدخال provenance |
| `python3 tools/build_bhl_base.py --out build-evidence/bhl-base` | rc=0 — عميل `139/139`، خادم `179/179`، `446` وحدة ترجمة، `454` أمراً، **فجوات الربط `[]`** |
| `client.so` | `27,761,892` B — `113981e51dee0943d6ef803e4fc92c2b6c7a9531c44d3d22b5688ee8423b6b45` |
| `hl.so` | `21,231,824` B — `44ed987023adcccf0d7f8e6f81b84339dbea393d27acfe66781010638bc41e7a` |
| `python3 tools/verify_bhl_base.py --compile` | rc=0 — OP4 `68/71`، BHL `101/106`، **glue العميل `1/1`** |
| `make verify` | rc=0 — `ALL CHECKS PASSED` |
| `unittest tests.test_bhl_base tests.test_op4_link_fixups tests.test_op4_weapons` | rc=0 — `29/29 OK` |

### نتائج اختبار السلاح (بناء/ربط، **ليس داخل اللعبة**)

* `tests/test_op4_weapons.py`: **7/7 OK**.
* `nm --defined-only client.so` → `00806920 T EV_FireEagle` (رمز حقيقي، و`objdump` يثبت أنه ليس stub).
* `nm --defined-only hl.so | c++filt` → `CEagle::Spawn()` و`CEagle::Precache()`.
* `strings hl.so` → صنف `weapon_eagle` مسجَّل.
* تطابق جسم `EV_FireEagle` مع `cl_dll/ev_hldm.cpp` للـ commit المثبّت، حرفياً.
* **ما لم يُختبر:** إطلاق، إعادة تعبئة، ضرر، ذخيرة، أنيميشن، صوت، ظهور النموذج داخل
  اللعبة. لا توجد بيئة لعبة ولا أصول شرعية.

### الأخطاء المتبقية وأسبابها

1. **خطأ ترجمة وُجِد وحُلّ:** في المحاولة الأولى كان `#include "../ev_hldm.h"` يصل إلى
   هيدر OP4 أولاً، فظهر `declaration of 'EV_FireEagle' has a different language
   linkage`. السبب: OP4 يعرّف الدالة برابط C++ بينما `hl_events.cpp` يصرّحها `extern "C"`.
   الحل: تضمين هيدرات BHL صراحة بصيغة `../hud.h` و`../cl_util.h` و
   `../eventscripts.h` و`../ev_hldm.h`. أُعيد الترجمة rc=0.
2. **خطأ في الاختبارات وُجِد وحُلّ:** `test_05` كان يستخدم تعبيراً نمطياً بلا `re.M`؛
   صُحّح إلى تطابق سطر `nm` الصريح.
3. **فجوة إثبات وُجِدت وحُلّت:** `tools/verify_bhl_base.py` لم يكن يترجم وحدات glue
   للعميل، فكان `make verify` يفشل بـ `wired source did not compile`. أُضيف فحص ترجمة
   حقيقي لوحدات العميل الموصولة بـ CMake (`client_glue: 1/1`).
4. **26 ملف OP4 ما زالت `port_pending`** — ليست أخطاء في هذه المرحلة؛ أسبابها معلَنة
   في [`COMPLETION_INVENTORY.md`](COMPLETION_INVENTORY.md) ولا تُنقل بالجملة.
5. **لا اختبار داخل اللعبة** — بيئي، ليس خطأً في الكود.

### الحكم

`weapon_eagle` **مُسجَّل وموصول ومترجم ومربوط** بإثبات بناء/ربط/مصدر.
**غير مُثبت داخل اللعبة، ولا يُعلَن مكتملاً.**

---

## الأسلحة التالية (لم تُنفَّذ بعد)

`weapon_pipewrench` · `weapon_m249` · `weapon_displacer` · `weapon_shockrifle` ·
`weapon_sporelauncher` · `weapon_sniperrifle` · `weapon_knife` · `weapon_penguin` ·
`weapon_grapple`

لكل سلاح: فحص مصدر OP4 → تحديد الاعتماديات اللازمة فقط → دمج → بناء العميل
والخادم → اختبار → تقرير بنفس البنود أعلاه.

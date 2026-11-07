# ما هو قديم (Legacy) — اقرأ قبل استخدام أي ثنائي

> **الشجرة المعتمدة الآن هي [`bhl-op4/`](../bhl-op4/PROVENANCE.json)**،
> ومعماريتها موثّقة في [`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md):
> BugfixedHL-Rebased هو الأساس، وOP4 يُدمج فوقه.

بعد تدقيق صريح تبيّن أن النهج السابق كان خاطئاً: كان **OP4 هو الأساس**
وفوقه 4 ملفات من BHL وطبقة توافقية كُتبت هنا. لذلك صُنّف ما يلي كـ **legacy**:

| المسار / الأصل | الحالة | لماذا |
| --- | --- | --- |
| `integration/bhl/*` | legacy | 15 ملفاً: 4 نسخ حرفية من BHL + إعادة تنفيذ لـ `ConVar/CvarSystem` (تشابه `0.030` مع `convar.cpp`) |
| `merge/bhl.py`, `merge/plan.json`, `merge/engine.py` | legacy | `MERGE_REPORT.json` كان `merged=0` و`three_way rules = 0`؛ لم يحدث دمج بين الشجرتين |
| `src/speedrun/sr_*`, `overlay/cl_dll/sr_*`, `overlay/dlls/sr_*` | legacy | «نظام جديد كلياً» للمؤقّت/التقسيمات/الديمو، وليس أنظمة BHL |
| `build/merged-real/`, `build/merged/` | legacy | شجرة OP4-أساس، غير متتبَّعة في Git |
| `dist/dlls/client.so`, `dist/dlls/hl.so`, `MANIFEST.json` | **legacy binaries** | مبنية من شجرة OP4-أساس؛ `hl.so` لا يحوي أي كود BHL |
| `dist/bhlop4/`, `dist/bhl-op4-mod.zip` | legacy | حزمة التثبيت لتلك الثنائيات |
| Release `v0.1.0-linux32` | legacy | أصوله من البناء القديم، لم تُحدَّث ولم تُحذف |
| `docs/BHL_MERGE.md`, `docs/RESOLUTION.md`, `docs/MERGE_PLAN.md`, `docs/BUILDING.md` | توثيق قديم | يصف نهج OP4-أساس وادعاءات `bhl_status` / `bhl-systems-1` |
| `.github/workflows/release.yml` (خطوة فحص السلاسل النصية) | legacy | كانت تتحقق من وجود `bhl_status` داخل الثنائي، لا من مصدر الكود |

## ماذا يعني هذا عملياً

* **لا تستخدم** الثنائيات أو الـ Release كدليل على أن المشروع مبني على BHL.
* **لا تُحدَّث** هذه المسارات لإخفاء المشكلة؛ تُترك كما هي كسجلّ تدقيق،
  والعمل الجديد يسير في `bhl-op4/` + `merge/bhl_base.py` +
  `tools/verify_bhl_base.py`.
* حلّ تثبيت مجلد `bhlop4/` المستقل (`fallback_dir "gearbox"`,
  `steam_appid.txt` = 50، `delta.lst`) يبقى صحيحاً تقنياً، لكنه يخصّ
  الثنائيات القديمة فقط.
* لم يُبنَ بديل ثنائي بعد: بناء BHL الكامل يحتاج CMake ≥ 3.30 وvcpkg
  و`hl1_source_sdk`. لم أُنتج ثنائيات وهمية ولم ألمس الـ Release.

## حقائق التدقيق (للرجوع إليها)

* `client.so` القديم: 6 كائنات من 110 مرتبطة بـ BHL، منها 4 فقط كود BHL حرفي.
* `hl.so` القديم: صفر رموز لأصناف BHL؛ الموجود `_Z15BHL_Server_Initv` فقط.
* كل الـ 15 commit السابقة كُتبت داخل المستودع، صفر merge commits، صفر تاريخ مستورد.
* `bhl_compat.cpp` مقابل `src/common/convar.cpp`: نسبة تشابه `0.030`.
* بانرات `Source: BugfixedHL-Rebased / GPL-3.0` على ملفات مكتوبة هنا كانت
  نسبة مصدر خاطئة.

التصحيح الكامل موثّق في [`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md) وبيان
المصدر لكل ملف في [`bhl-op4/PROVENANCE.json`](../bhl-op4/PROVENANCE.json).

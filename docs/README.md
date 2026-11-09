# فهرس الوثائق

| ملف | المحتوى |
| --- | --- |
| [OP4_WEAPON_PHASES.md](OP4_WEAPON_PHASES.md) | 🔫 **سجل مراحل دمج الأسلحة**: سلاحاً بسلاح، الملفات/الفرق/البناء/الاختبارات، مع تمييز صريح بين إثبات البناء والتشغيل داخل اللعبة |
| [COMPLETION_INVENTORY.md](COMPLETION_INVENTORY.md) | 📋 **جرد الاكتمال**: تصنيف كل مصادر OP4، الـ26 `port_pending`، تعارض VGUI1/VGUI2، جذور CTF/IsCTF، وحالة مراحل التنفيذ |
| [BHL_BASE_MERGE.md](BHL_BASE_MERGE.md) | ✅ **المرجع المعماري الحالي**: BHL أساساً + دمج أنظمة/أسلحة OP4، قواعد الدمج، إثبات الترجمة، ما لم يُنجز |
| [BHL_FINAL_AUDIT.md](BHL_FINAL_AUDIT.md) | 🛑 **التقرير النهائي**: إغلاق الـ12 رمزاً، البناء النهائي، كل اختبار ونتيجته، وقائمة النواقص صراحةً |
| [BHL_BASE_BUILD.md](BHL_BASE_BUILD.md) | 🔧 **إثبات البناء الحقيقي**: أوامر/سجلات/بصمات بناء `client.so` و`hl.so` من `bhl-op4/`، صفر فجوة ربط، الإصلاحات المعلنة |
| [BHL_WINDOWS_BUILD.md](BHL_WINDOWS_BUILD.md) | 🪟 **نسخة ويندوز**: `client.dll` / `hl.dll` PE32 من نفس الشجرة، مع إثبات البناء/الربط وحدوده الصريحة |
| [LEGACY.md](LEGACY.md) | ⚠️ ما صُنّف قديماً (الثنائيات، الـ Release، `sr_*`، وثائق المرحلة السابقة) |
| [BUILDING.md](BUILDING.md) | *(legacy)* بناء `client.so` / `hl.so` من شجرة OP4-أساس |
| [ARCHITECTURE.md](ARCHITECTURE.md) | *(legacy)* طبقات المرحلة السابقة |
| [BHL_MERGE.md](BHL_MERGE.md) | *(legacy)* وصف `bhl-systems-1` على شجرة OP4-أساس |
| [MERGE_PLAN.md](MERGE_PLAN.md) | أنواع القواعد الـ30، سياسات التعارض، نقاط الحقن، ملفات البناء |
| [RESOLUTION.md](RESOLUTION.md) | كيف حُلّت التعارضات الـ127 والمنقولات المؤجلة، بأدلة السطور |
| [SPEEDRUN.md](SPEEDRUN.md) | المؤقّت، `SRSplit`، التقسيمات، PB، الشرعية، demo |
| [UPSTREAMS.md](UPSTREAMS.md) | المصادر المثبّتة، sha256، الرخص، ولماذا لا تُضمّن |
| [LICENSES.md](LICENSES.md) | التزامات الرخص قبل أي توزيع |
| [ROADMAP.md](ROADMAP.md) | ما اكتمل، ما يحتاج بيئة اللعبة، التحسينات الاختيارية |

من الجذر: [`README.md`](../README.md) للبدء السريع،
[`CONTRIBUTING.md`](../CONTRIBUTING.md) لإضافة قاعدة أو تحديث pin،
و[`tests/fixtures/README.md`](../tests/fixtures/README.md) للـ fixtures.

> كل رابط محلي في هذه الوثائق مُختبَر آلياً عبر `make hygiene`.
>
> 💡 تُقرأ هذه الوثائق أيضاً **داخل واجهة المشروع**: شغّل `make serve` ثم افتح
> تبويب «📖 README والوثائق» أو الرابط `/#docs`. إضافة ملف `.md` جديد إلى
> `docs/` تظهر تلقائياً في قائمة الوثائق (بشرط إضافته إلى هذا الفهرس).

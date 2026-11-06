# فهرس الوثائق

| ملف | المحتوى |
| --- | --- |
| [BUILDING.md](BUILDING.md) | بناء `client.so` / `hl.so`: ماذا أحمّل، 32-bit، `vgui.so`، التثبيت والتشغيل |
| [ARCHITECTURE.md](ARCHITECTURE.md) | الطبقات، تدفق البيانات، والقرارات المعمارية |
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

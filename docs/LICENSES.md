# الرخص والالتزامات

> **تنبيه بعد تصحيح المسار:** الشجرة المعتمدة [`bhl-op4/`](../bhl-op4/PROVENANCE.json)
> تحتوي **694 ملفاً كاملاً من BugfixedHL-Rebased (GPL-3.0)** متتبَّعة في Git،
> إضافةً إلى 154 ملفاً من OP4/Valve SDK. هذا ليس «منقولات للمراجعة فقط» كما في
> المرحلة السابقة. أي توزيع لهذه الشجرة أو لأي ثنائي يُبنى منها يخضع لـ
> **GPL-3.0** بالكامل، مع رخصة Valve غير التجارية لكود OP4. لا يُدعى امتثال
> قانوني هنا؛ راجع [`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md) و
> [`LEGACY.md`](LEGACY.md).

* **كود هذا المستودع** (المحرّك، النواة C++، glue، اللوحة، الاختبارات، التوثيق): MIT.
  يُسمح بالاستخدام التجاري ضمن حدود رخص المصادر أدناه.
* **BugfixedHL-Rebased** — GPL-3.0. المنقولات في `integration/ports/` للمراجعة
  فقط، ولا تُترجم ولا تُربط. إذا وزّعت شجرة مدموجة تحتوي كوداً مشتقاً منه،
  التزم بـ GPL-3.0 (المصدر، الإسناد، نفس الرخصة).
* **Valve HALF-LIFE SDK** و**halflife-op4-updated** — رخصة Valve للاستخدام
  غير التجاري في تحسينات منتجات Valve، مع إصلاحات مجتمع TWHL. راجع
  `LICENSE` في كل مستودع قبل أي توزيع.
* **بيانات المسار** — أسماء الخرائط والفصول من SourceRuns Wiki؛ حقوق الأسماء
  والعلامات لـ Valve/Gearbox.

حزمة `dist/*.zip` تحتوي كودنا فقط وتتضمن `MANIFEST.json` بـ sha256 لكل ملف. الشجرة المولّدة في `build/` ليست قطعة قابلة للتوزيع بشكل مستقل: هي تجميع
لمصادر مرخّصة separately، ويجب مراجعة الالتزامات قبل نشر أي حزمة مود.

هذا المستند ليس استشارة قانونية.

`data/delta.lst` (in the mod folder) is copied from the OP4 SDK `network/`
folder because GoldSrc mods require it for client/server network data; it is
SDK data, not kit code, and remains under the SDK's terms.

## تحديث bhl-systems-1: كود GPL يُترجم الآن داخل الثنائيات

حتى `0.1.x` كانت ملفات `integration/ports/` نسخاً مرجعية **غير مترجمة**.
ابتداءً من `bhl-systems-1` تُنقل أنظمة BugfixedHL الحقيقية إلى
`integration/bhl/` وتُترجم داخل `client.so` / `hl.so` (`docs/BHL_MERGE.md`).
أي توزيع لهذه الثنائيات هو توزيع لعمل مشتق من كود تحت **GPL-3.0-or-later**،
فيجب أن يلتزم بشروطها (المصدر المقابل، الإشعارات، نفس الرخصة). كود الـ kit
 (`merge/`, `tools/`, `src/speedrun/`, `web/`) يبقى MIT ولا يغيّر هذا الالتزام.

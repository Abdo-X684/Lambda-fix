# المصادر المثبّتة

| الاسم | الدور | المستودع | commit | sha256 (أول 16) | الرخصة |
| --- | --- | --- | --- | --- | --- |
| `op4` | target | `twhl-community/halflife-op4-updated` | `5368be7f8eba` | `c65e53713b5ef2d3a` | Valve HLSDK + TWHL |
| `bugfixhl` | donor | `tmp64/BugfixedHL-Rebased` | `4d32095e3c33` | `a70ab961de1c40f6` | GPL-3.0 |
| `valve_hlsdk` | base | `ValveSoftware/halflife` | `b1b5cf589291` | `f5e7793f974bc02d` | Valve HLSDK |

القيم الكاملة في `upstreams.json`. `fetch.py` يتحقق من **sha256 + الحجم** قبل
فك الضغط، ويرفض أي archive path traversal أو symlink أو ملف ثنائي، ويكتب
`.cache/upstreams/<name>/.FETCHED.json` ليكون التنزيل قابلاً للتخزين المؤقت.

## لماذا لا نُضمّن الكود؟

1. رخص Valve SDK تقيّد إعادة التوزيع؛ GPL-3.0 يفرض التزامات على العمل المشتق.
2. 21MB من الأرشيفات و~2600 ملف لا لزوم لها في git.
3. التثبيت بـ SHA + checksum يعطي نتيجة قابلة لإعادة التوليد أفضل من نسخة عالقة.

## offline fixtures

`tests/fixtures/upstreams/` يحتوي نسخاً مصغّرة بنفس المسارات ونفس الـ anchors
للملفات التي تستخدمها خطة الدمج (schema 2) والتدقيقات، وتُستخدم في CI والاختبارات
بلا شبكة. `valve_hlsdk` الآن مجلد عنصر نائب فقط لأن `three_way` غير مستخدم في
الخطة الحالية (ما زال مثبّتاً كأصل مشترك لقواعد مستقبلية، ومُختبراً عبر
`ConflictPolicyTests`). التفاصيل في [`tests/fixtures/README.md`](../tests/fixtures/README.md).

أي تغيير في تخطيط المصدر الحقيقي يجب أن ينعكس هنا، وإلا كشف `anchor_drift`
ذلك فوراً، و`make hygiene` يتحقق من وجود مجلد لكل مصدر مثبّت.

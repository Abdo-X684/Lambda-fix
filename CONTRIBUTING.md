# المساهمة / Adding to the kit

القاعدة الذهبية: **لا تضف تعديلاً ضمنياً**. كل تغيير على شجرة OP4 يُعلن كقاعدة في
`merge/plan.json`، وكل مصدر خارجي يُثبّت في `upstreams.json`.

## قبل أي commit

```bash
make hygiene     # نصوص، JSON، استيرادات، روابط markdown، فهرس الوثائق
make verify      # 111 اختبار Python + 77 فحص C++ + التوليد + الدمج + الحزمة
make fetch && make merge && make verify-sdk   # إن غيّرت pins أو نقاط حقن
```

`make tidy` ينظّف `__pycache__` ومجلدات `.stage-*` اليتيمة ثم يعيد فحص النظافة.

## أين أضع كل شيء؟

| أريد… | المكان |
| --- | --- |
| قاعدة دمج/حقن/تدقيق جديدة | `merge/plan.json` (+ مقطع في `integration/snippets/` إن لزم) |
| سلوك محرك الدمج | `merge/engine.py` + اختبار في `tests/` |
| كود C++ مشترك بين test واللعبة | `src/speedrun/` ثم قاعدة `copy` إلى `game_shared/` |
| glue يعتمد على محرك Half-Life | `overlay/cl_dll/` أو `overlay/dlls/` + تحديث `merge/projects.py` |
| خريطة/فصل/cvar | `data/` ثم `python3 tools/gen_route_header.py --write` |
| وثيقة جديدة | `docs/` **وأضفها إلى `docs/README.md`** (وإلا يفشل `make hygiene`)؛ تظهر تلقائياً في تبويب الوثائق بالواجهة |
| اختبار | `tests/test_*.py` أو `tests/cpp/test_speedrun.cpp` |
| تعديل عارض الوثائق | `web/markdown.py` + `tests/test_markdown.py` (افحص التهريب والروابط) |
| بناء الـ DLL | `tools/build_dlls.py` + `docs/BUILDING.md`؛ `make build-dlls-check` لا يحتاج أداة 32-bit |

## إضافة قاعدة `inject`

1. تأكد أن الـ anchor يظهر **مرة واحدة فقط** في الملف الحقيقي:
   `grep -c "<anchor>" .cache/upstreams/op4/<path>`.
2. اكتب المقطع في `integration/snippets/`، وأضف القاعدة، ثم حدّث الـ fixture
   المناسب في `tests/fixtures/upstreams/op4/` بنفس الـ anchor.
3. شغّل `python3 -m merge.cli run --offline --strict` ثم الدمج الحقيقي.

## تحديث pin

غيّر `ref` و`tarball.sha256` و`tarball.bytes` في `upstreams.json`
(راجع الـ commit أولاً)، ثم `python3 -m merge.cli fetch --force`،
`make merge`، وافحص `build/merged-real/MERGE_REPORT.md`.
أي `anchor_drift` يعني أن upstream تغيّر — لا تُخفِه، بل حدّث القاعدة ووثّقها.

## التنسيق

Python 3.9+ بلا اعتماديات، C++17، نصوص UTF-8 بـ LF وسطر أخير newline،
لا مسافات زائدة في نهاية الأسطر. `tools/check_hygiene.py` يفرض ذلك.

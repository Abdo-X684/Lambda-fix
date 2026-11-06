# المعمارية

## المشكلة

| | BugfixedHL-Rebased | halflife-op4-updated |
| --- | --- | --- |
| التخطيط | `src/game/{client,server,shared}`, `src/common`, `src/pm_shared` | `cl_dll`, `dlls`, `game_shared`, `common`, `pm_shared` |
| الواجهة | VGUI2، HUD مقسّم إلى `client/hud/*`، `ConVar` class | VGUI1، `cl_dll/hud.cpp` واحد، macros |
| الأساس | HLSDK 2.3-p3 محدّث + إصلاحات Metamod | HLSDK Updated + كود Gearbox المُعاد بناؤه |
| البناء | CMake | VS2019 vcxproj + Linux Makefiles |
| الرخصة | GPL-3.0 | Valve HLSDK (non-commercial) + TWHL |

أخذ ملف `src/game/client/hud.cpp` من BugfixedHL ووضعه مكان `cl_dll/hud.cpp` يدمر
كل كود OP4 (CTF، flag icons، gamerules). لهذا المشروع **لا يدمج المستودعين كتلةً واحدة**،
بل يطبّق طبقة انتقائية قابلة للمراجعة.

## الطبقات

1. **البيانات** — `upstreams.json` (3 مصادر بـ SHA + sha256 + رخصة + دور)
   و`merge/plan.json` (26 قاعدة صريحة). لا يحدث أي تعديل ضمني.
2. **المصادر** — `merge/fetch.py` ينزّل أرشيفات codeload، يتحقق من sha256 والحجم،
   يفك الضغط بأمان (يمنع traversal والروابط الرمزية والملفات الثنائية)، ويضعها في
   `.cache/upstreams/` (مستثنى من git). `--offline` يبدّلها بـ fixtures مصغّرة.
3. **المحرّك** — `merge/engine.py`:
   - ينسخ شجرة OP4 إلى مجلد مرحلي،
   - `three_way`: `git merge-file -p --diff3` مع vanilla كأصل، OP4 كـ ours،
     BugfixedHL كـ theirs،
   - `copy`: نقل مع ترجمة مسارات (`merge/layout.py`) وإعادة كتابة `#include`
     وبانر مصدر للملفات المرجعية،
   - `inject`: إدراج بعد anchor فريد، مع كشف «انحراف الـ anchor»،
   - `generate`: `speedrun.cfg` و`op4_route.json`،
   - `merge/projects.py`: إضافة الملفات الجديدة إلى قوائم بناء VS وLinux،
   - تقرير + بصمة شجرة + تبديل ذري للمجلد الناتج.
4. **النواة** — `src/speedrun/sr_core.{h,cpp}`: C++17 بلا أي اعتماد على المحرك،
   تُبنى وتُختبر على المضيف وتُنسخ كما هي إلى `game_shared/` في الشجرة المدموجة.
5. **ال glue** — `overlay/cl_dll/sr_hud_timer.*` و`overlay/dlls/sr_server.*`
   ومقاطع `integration/snippets/`: الكود الوحيد الذي يتكلم مع محرك Half-Life.
6. **العرض** — `web/app.py` (stdlib http.server) + واجهة RTL، تقرأ نفس ملفات
   البيانات وتشغّل الدمج والاختبارات عبر JSON API نسبي.

## قراران مهمان

* **التعارضات تُحجر ولا تُكتب في ملفات قابلة للترجمة.** `on_conflict: marker`
  يكتب نتيجة `git merge-file` في `integration/conflicts/` ويترك ملف OP4 نظيفاً،
  بينما `on_conflict: ours` يسجّل «نقل يدوي مؤجّل» بسبب واضح.
* **المنفولات GPL للمراجعة فقط.** الكود المنقول من BugfixedHL يوضع في
  `integration/ports/` خارج كل مسارات البناء، والمنفذة فعلياً نواة نظيفة
  مكتوبة هنا. هذا يمنع تلوث الشجرة بتبعيات VGUI2 ويوضح الالتزام الرخصي.

## حتمية النتيجة

`compute_tree_hash()` يهضم `(المسار النسبي، المحتوى)` لكل ملف بترتيب مفروض،
ويستثني ملفات التقرير نفسها. إعادة تشغيل الدمج على نفس المدخلات تعطي نفس
البصمة (يختبره `tests/test_engine.py`).

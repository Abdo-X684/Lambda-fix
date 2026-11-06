# المعمارية (النسخة المكتملة)

## المشكلة

| | BugfixedHL-Rebased | halflife-op4-updated |
| --- | --- | --- |
| التخطيط | `src/game/{client,server,shared}`, `src/common` | `cl_dll`, `dlls`, `game_shared`, `common` |
| الواجهة | VGUI2، HUD مقسّم، `ConVar` class | VGUI1، `cl_dll/hud.cpp` واحد، macros |
| البناء | CMake | VS2019 vcxproj + Linux Makefiles |
| الرخصة | GPL-3.0 | Valve HLSDK (non-commercial) + TWHL |

وضع `src/game/client/hud.cpp` مكان `cl_dll/hud.cpp` يدمر كود OP4. لذا المشروع
لا يدمج المستودعين كتلةً واحدة، بل يطبّق طبقة انتقائية مُثبتة بالأدلة.

## الطبقات

1. **البيانات** — `upstreams.json` (3 مصادر بـ SHA + sha256 + رخصة + دور)
   و`merge/plan.json` (30 قاعدة صريحة، schema 2).
2. **المصادر** — `merge/fetch.py`: تنزيل + تحقق sha256/حجم + فك آمن
   (يمنع traversal والروابط الرمزية والثنائيات) إلى `.cache/upstreams/`.
   `--offline` يبدّلها بـ fixtures بنفس المسارات والـ anchors.
3. **المحرّك** — `merge/engine.py`: نسخ شجرة OP4 إلى مرحلة مؤقتة،
   `audit` (تدقيق تكافؤ)، `copy` (ترجمة مسارات/`#include`/بانر)،
   `inject` (anchor فريد)، `generate`، `patch_projects`،
   ثم تقرير + بصمة شجرة + تبديل ذري.
4. **النواة** — `src/speedrun/sr_core.{h,cpp}`: C++17 بلا اعتماد على المحرك،
   تُبنى وتُختبر على المضيف وتُنسخ كما هي إلى `game_shared/`.
   تحوي `RunTimer` و`Route` و`Split`/PB و`ServerMirror`.
5. **الـ glue** — `overlay/cl_dll/sr_hud_timer.*` و`sr_hud_msg.*`،
   `overlay/dlls/sr_server.*`، ومقاطع `integration/snippets/`.
6. **الشبكة** — السيرفر يسجّل `SRSplit` في `LinkUserMessages()` ويبثّ
   `(at, delta, hasPb, map)` عند كل changelevel؛ العميل يربطها في
   `CHud::Init` ويعرض `ServerMirror` (زمن سلطوي + إسقاط رتيب محلي).
7. **العرض والتوزيع** — `web/app.py` (stdlib http.server + RTL)،
   `web/markdown.py` (عارض Markdown آمن بلا اعتماديات: عناوين بفهرس، جداول،
   كتل أوامر، روابط وثائق داخلية؛ يُهرَّب كل النص خادمياً)،
   `tools/package_mod.py` (zip + `MANIFEST.json` بـ sha256، بلا كود SDK).
   اللوحة تبويبان: لوحة التحكم، وصفحة README/الوثائق بفهرس جانبي.

## القرارات المهمة

* **التكافؤ بدل الدمج الأعمى**: OP4-updated يوفّر bunnyhop وحماية الأوامر
  وتهيئة HUD أصلاً. التدقيق الآلي يثبت ذلك بمراجع سطور؛ التفاصيل في
  [`RESOLUTION.md`](RESOLUTION.md). لا تعارضات مخفية ولا cvars وهمية.
* **المنقولات GPL للمراجعة فقط** في `integration/ports/` خارج مسارات البناء،
  والتنفيذ نواة نظيفة مكتوبة هنا.
* **الزمن سلطوي**: HUD لا يخمن الزمن، بل يستقبل الرسائل ويعرض إسقاطاً رتيباً.
* **الحتمية**: `compute_tree_hash()` يهضم `(المسار، المحتوى)` بترتيب مفروض
  ويستثني التقرير؛ إعادة التشغيل تعطي نفس البصمة. الحزمة كذلك بتواريخ zip ثابتة.

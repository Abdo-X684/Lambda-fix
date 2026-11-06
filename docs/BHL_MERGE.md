# BugfixedHL مدموج فعلياً داخل OP4 — لا مجرد مرجع

> **تصحيح لمسار سابق:** في الإصدارات `0.1.x` كان BugfixedHL يُستخدم كـ *مرجع*
> فقط: ثلاث «تدقيقات تكافؤ» تقول إن OP4 يملك أصلاً bunnyhop وإصلاحات العميل،
> ثم بُنِي نظام `sr_*` جديد للسبيدرن من الصفر. هذا كان خطأً في فهم المطلوب.
> المطلوب كان: **ادمج أنظمة BHL نفسها داخل OP4، وضع طبقة توافقية فقط**.
> اعتباراً من `bhl-systems-1` صارت أنظمة BHL الحقيقية تُترجم داخل `client.so`
> و`hl.so`.

## ماذا يعني «دمج الأنظمة» هنا؟

OP4 (`twhl-community/halflife-op4-updated` @ `5368be7f`) هو الشجرة الأساس،
كما هي. فوقها تُنقل أنظمة BugfixedHL-Rebased (@ `4d32095e`، GPL-3.0) كما هي،
مع **طبقة توافقيات** (`integration/bhl/`) تسد الفجوة بين BHL الحديث (ConVar،
CHudElem، VGUI) وOP4 القديم (`gEngfuncs`, `CHud`, `CVAR_CREATE`). لا يُعاد
اختراع النظام، ولا يُستبدل بآخر.

الدمج ينفّذه `python3 -m merge.bhl --tree build/merged-real`، ويستدعيه
`make merge` تلقائياً بعد `merge.cli run`. التقرير:
`build/merged-real/BHL_MERGE_REPORT.json`.

## الأنظمة المنقولة (مترجمة فعلياً داخل الثنائيات)

| # | نظام BHL | المصدر | مكانه في OP4 |
| --- | --- | --- | --- |
| 1 | `ConVar` / `ConCommand` / `CvarSystem` | `src/common/convar.h`, `convar.cpp` | `cl_dll/bhl_compat.{h,cpp}` |
| 2 | `CHudElem` / `CHudElemBase` / `DEFINE_HUD_ELEM` | `src/game/client/hud/base.{h,cpp}` | `cl_dll/base.{h,cpp}` |
| 3 | `CHudSpeedometer` (`hud_speedometer`) | `hud/speedometer.{h,cpp}` | `cl_dll/speedometer.*` |
| 4 | `CHudJumpspeed` (`hud_jumpspeed`) | `hud/jumpspeed.{h,cpp}` | `cl_dll/jumpspeed.*` |
| 5 | `CHudStrafeGuide` (`hud_strafeguide`) | `hud/strafeguide.{h,cpp}` | `cl_dll/strafeguide.*` |
| 6 | `bhlcfg` / `bugfixedhl.cfg` | `bhlcfg.{h,cpp}` | `cl_dll/bhlcfg.*` |
| 7 | `sv_bhl_query_vars`, `sv_bhl_query_wait_for_id`, `sv_bhl_defer_motd`, `sv_bhl_version` | `CBugfixedServer.cpp` | `dlls/bhl_server.cpp` |

كل ملف في `integration/bhl/` يحمل بانر المصدر والرخصة GPL-3.0؛ التعديلات
المسمّاة `COMPAT` هي التعديلات الوحيدة على كود BHL.

## التوافقيات (الطبقة الوحيدة التي كتبناها)

| فجوة | التوافقية |
| --- | --- |
| BHL يسجّل cvars دفعة واحدة عبر `CvarSystem::RegisterCvars()` بينما OP4 يستخدم `CVAR_CREATE` | `ConVar::GetCvar()` تسجيل كسول، ويفضّل cvar موجود في المحرك (`pfnGetCvarPointer`) قبل إنشاء واحد جديد |
| `FCVAR_BHL_ARCHIVE`, `ALPHA_AMMO_*`, `HUD_DRAW_ALWAYS`, `FADE_TIME`, `M_PI` غير موجودة في OP4 | ثوابت في `bhl_compat.h` |
| BHL يستدعي `gHUD.GetHudColor(HudPart::Common, …)`, `GetHudTransparency()`, `DrawHudNumberCentered()` | `merge/bhl.py` يحقن `enum class HudPart` وإعلانات الدوال الثلاث في `cl_dll/hud.h`، والتنفيذ في `bhl_compat.cpp` (يقرأ `giR/giG/giB` من OP4) |
| `cl_dll.h` / `wrect.h` / `appversion.h` الحديثة غير موجودة | استُبدلت بـ `bhl_compat.h` و`BHL_MERGE_VERSION` |
| OP4 يُبنى بـ `-fno-exceptions` | `try/catch` في `bhlcfg.cpp` أُزيل (الوحيد) |
| BHL ينشئ عناصر HUD بـ `CHud::RegisterHudElem<T>()` | `BHL_Init()` ينشئ `new CHudSpeedometer()` / `CHudJumpspeed()` / `CHudStrafeGuide()` ويستدعي `Init/VidInit/Draw` |
| BHL يحدّث السرعة من `V_CalcRefdef` | حقن `BHL_OnRefdef(pparams)` في `cl_dll/view.cpp` → نفس الاستدعاءات الثلاثة في `BHL view.cpp:1686-1688` |
| BHL يحفظ `bugfixedhl.cfg` عند الإغلاق | حقن `BHL_Shutdown()` في `HUD_Shutdown()` |
| BHL ConVar على السيرفر يحتاج `IBugfixedServer`/Metamod | `cvar_t` + `CVAR_REGISTER` الأصليان في OP4، مع بانر تحميل |
| OP4 يجبر قوائم مصادر صريحة | `merge/bhl.py` يضيف 6 `.cpp` للعميل و1 للسيرفر إلى `Makefile.hl_cdll`/`Makefile.hldll`/`*.vcxproj` |

## أين صار `sr_*`؟

طبقة `sr_*` (مؤقت RTA، `SRSplit`, `sr_status`) **إضافة اختيارية** بُنيت في
الإصدارات السابقة؛ ليست «الدمج». بقيت لأنها تعمل ولا تؤذي أحداً، لكن:

* عنوان الدمج والواجهة صارا عن **أنظمة BHL**؛
* `bhl_status` (أمر BHL الحقيقي عبر `CON_COMMAND`) هو مرجع التحقق؛
* `hud_speedometer` / `hud_jumpspeed` / `hud_strafeguide` مفعّلة افتراضياً في
  `speedrun.cfg`؛
* يمكنك تعطيلbanner الإضافة بـ `sr_hud_banner 0` وسيبقى BHL ظاهراً.

## كيف تتأكد؟

| العلامة | المصدر |
| --- | --- |
|مؤشر السرعة / jumpspeed / strafe guide على الشاشة | أنظمة BHL، مفعّلة بـ `hud_speedometer 1` … |
| `[BHL] BugfixedHL systems merged into Opposing Force` في الكونسول | `BHL_Init()` |
| `bhl_status` | `CON_COMMAND` من BHL |
| `bhl_version` → `bhl-systems-1` | `ConVar` من BHL |
| `sv_bhl_version`, `sv_bhl_query_vars` على السيرفر | `BHL_Server_Init()` |
| `bugfixedhl.cfg` يُنشأ في مجلد المود | `bhlcfg::Shutdown()` |

`python3 -m merge.bhl --plan` يسرد الأنظمة، و
`make verify` يفحص أنها موجودة في المصادر والثنائيات.

## الرخص

BugfixedHL-Rebased تحت **GPL-3.0-or-later**؛ الآن كوده يُترجم داخل الثنائيات،
وليس مجرد ملف مرجعي. لذلك الثنائيات الناتجة مشتقة من GPL ويجب التعامل معها
وفقها (`docs/LICENSES.md`). كود الـ kit (`src/speedrun`, `merge/`, `tools/`) يبقى
MIT. لا تُوزّع أصول Valve/Gearbox ولا `vgui.so`.

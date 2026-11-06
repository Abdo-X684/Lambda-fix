# كيف حُلّت التعارضات الـ127 والمنقولات المؤجلة

> النتيجة: `0 conflicts · 0 deferred · 0 errors` في الدمج الحقيقي، مثبتة بتدقيق
> آلي داخل `MERGE_REPORT.json` لا بادعاء يدوي.

## 1. الاكتشاف

الدمج ثلاثي الأطراف الأول (`vanilla HLSDK` كأصل، `OP4` كـ ours،
`BugfixedHL-Rebased` كـ theirs) أعطى **127 hunk متعارضاً** في `pm_shared.cpp`
و~92 في `hud.cpp` و~127 في `client.cpp`. سبب التعارض ليس خلافاً دلالياً، بل أن
BugfixedHL **أعاد كتابة** هذه الملفات بالكامل (C++ حديث، VGUI2، `ConVar`)،
فصار «الأصل المشترك» أبعد من أن يُنتج دمجاً ذا معنى.

فحص الكود الفعلي كشف أن `halflife-op4-updated` (المبني على HLSDK Updated)
يحتوي **أصلاً** على الإصلاحات المطلوبة:

| إصلاح BugfixedHL | مكافئه الأصلي في OP4-updated | الدليل |
| --- | --- | --- |
| `s_bBHopCap` + `PM_SetBHopCapEnabled` يتحكم بـ `PM_PreventMegaBunnyJumping()` | `physinfo "bj"` يُقرأ في `PM_PreventMegaBunnyJumping()` ويُضبط من `sv_allowbunnyhopping` | `pm_shared/pm_shared.cpp:2551` و`dlls/client.cpp:985-1000` و`dlls/player.cpp:3131` |
| `BUNNYJUMP_MAX_SPEED_FACTOR` واستدعاء الـ cap من `PM_Jump` | نفس الثابت ونفس الاستدعاء | `pm_shared/pm_shared.cpp:2541,2565,2669` |
| حماية طول الأمر في `ClientCommand` (منع crash) | نفس التعليق ونفس `strncpy(...,127)` + `command[127]='\0'` | `dlls/client.cpp:670-686` (BHL: `src/game/server/client.cpp:648-686`) |
| تصفير حالة HUD في `Init` (`m_pSpriteList=NULL`, `m_flTime=1.0`) | `m_iLogo=0`, `m_flTime=1.0`, constructor `m_pHudList(NULL)` | `cl_dll/hud.cpp:384,415` و`cl_dll/hud.h:719` (BHL: `src/game/client/hud.cpp:343-350`) |

النتيجة: إعادة دمج الملفات كانت ستُدخل كوداً مكرراً أو تُسقط كود OP4 (CTF،
`FlagIcons`، gamerules). القرار الصحيح: **لا دمج، بل تدقيق تكافؤ + توصيل إعداد**.

## 2. التنفيذ

1. استُبدلت قواعد `three_way` الثلاث بقواعد `audit` في `merge/plan.json`.
   كل قاعدة تتحقق من وجود أنماط محددة في ملف OP4 وتسجّل في التقرير:
   `verdict`, `meaning`, `found`, `min`, و`evidence` بمراجع السطور.
   أي نمط ناقص → حالة `anchor_drift` + تحذير + فشل `--strict`.
2. `bhl_bunnyhop` (cvar غير موجود في OP4) استُبدل بـ **`sv_allowbunnyhopping 1`**
   الحقيقي في `data/cvars.json` و`speedrun.cfg` و`sr::RenderConfig`.
   `bhl_disable_selfgauss` حُذف لأنه لا يوجد مكافئ له في OP4 (لم نخترع cvar وهمياً).
3. ما لم يكن موجوداً في OP4 أُضيف ككود نظيف ومُختبَر:
   `sr_core.*` (مؤقّت/تقسيمات/PB/`ServerMirror`)، `sr_hud_timer.*`،
   `sr_hud_msg.*`، `sr_server.*`، ورسالة `SRSplit` المسجّلة في
   `dlls/UserMessages.cpp` قبل أن يربطها العميل.
4. `integration/ports/` بقي أرشيف مراجعة GPL فقط، خارج مسارات البناء.

## 3. التحقق

| فحص | النتيجة |
| --- | --- |
| تدقيقات التكافؤ (offline + حقيقي) | 3/3 `equivalent`، 11 نمطاً مطابقاً |
| علامات تعارض في `cl_dll/dlls/game_shared/pm_shared/common` | 0 |
| `g++ -fsyntax-only` للملفات المحقونة وglue مقابل هيدرات SDK الحقيقية | 9/9 |
| اختبارات Python / C++ | 64 / 77 |
| بصمة الشجرة | حتمية عبر تشغيلين متتاليين |

## 4. ما تبقّى خارج نطاق المستودع

ربط `hl.dll`/`client.dll` بأداة بناء HLSDK وتشغيل المود داخل اللعبة مع أصول
Opposing Force. هذا يحتاج أداة بناء خارجية وملفات اللعبة، لا يمكن إجراؤها داخل
المستودع؛ لكن كل المدخلات (المشاريع، Makefiles، المصادر، cfg، الحزمة) جاهزة
ومُتحقَّق منها نحوياً. راجع `dist/INSTALL.md` بعد `make package`.

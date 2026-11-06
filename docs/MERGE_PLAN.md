# خطة الدمج والقواعد

كل تعديل معلن في `merge/plan.json`؛ `python3 -m merge.cli plan` يعرضها،
و`validate_plan()` يرفض أي قاعدة مجهولة الإجراء أو مسار traversal أو مصدر غير معروف.

## الأنواع

| action | الوظيفة | حقول أساسية |
| --- | --- | --- |
| `three_way` | دمج `ours`(OP4) مع `theirs`(BugfixedHL) على `base`(vanilla) | `base`, `ours`, `theirs`, `on_conflict`, اختياري `quarantine`, `manual_port` |
| `copy` | نسخ ملف مع ترجمة مسار/تضمين وبانر مصدر | `from`, `path`, اختياري `include_rewrites`, `banner` |
| `inject` | إدراج مقطع عند anchor فريد | `anchor`, `where`, `snippet` |
| `generate` | توليد ملف من `data/` | `generator` = `speedrun_cfg` \| `route_json` |
| `skip` | توثيق قرار عدم النقل | `note` |

## سياسات التعارض

| `on_conflict` | السلوك | الحالة في التقرير |
| --- | --- | --- |
| `marker` | كتابة نتيجة الدمج بعلامات التعارض في `quarantine` وترك الملف الأصلي | `conflict` |
| `ours` | الإبقاء على كود OP4 وتسجيل سبب النقل اليدوي | `deferred` |
| `theirs` | اعتماد نسخة BugfixedHL (للحالات المراجَعة فقط) | `donor` |
| `fail` | إيقاف القاعدة وتسجيل خطأ | `error` |

`--strict` يفشل فقط عند قواعد لم تُطبَّق (`error`, `anchor_drift`, `missing`)؛
التعارضات المحجورة نتيجة متوقعة وموثّقة لا تُفسد الشجرة.

## نقاط الحقن (مؤكدة مقابل الكود الفعلي)

| ملف OP4 | الـ anchor | المقطع |
| --- | --- | --- |
| `cl_dll/hud.cpp` | `#include "hud.h"` | تضمين `sr_hud_timer.h` |
| `cl_dll/hud.cpp` | `void CHud::Init()\n{\n` | `SR_HUD_Init()` |
| `cl_dll/hud_redraw.cpp` | `#include "hud.h"` | تضمين HUD |
| `cl_dll/hud_redraw.cpp` | `bool CHud::Redraw(float flTime, bool intermission)\n{\n` | `SR_HUD_Redraw(flTime)` |
| `dlls/world.cpp` | `#include "extdll.h"` | تضمين `sr_server.h` |
| `dlls/world.cpp` | `void CWorld::Spawn()\n{\n` | `SR_Server_OnMapSpawn(STRING(gpGlobals->mapname))` |
| `dlls/client.cpp` | `#include "extdll.h"` | تضمين `sr_server.h` |
| `dlls/client.cpp` | `void ClientPutInServer(edict_t* pEntity)\n{\n` | `SR_Server_OnClientPutInServer(pEntity)` |

إذا تغيّر upstream وصار الـ anchor مكرراً أو مفقوداً، تُسجَّل `anchor_drift`
ويُترك الملف دون تعديل — لا حقن أعمى.

## ملفات البناء

`merge/projects.py` يضيف بشكل idempotent:
`cl_dll/sr_hud_timer.cpp` و`game_shared/sr_core.cpp` إلى `hl_cdll`،
و`dlls/sr_server.cpp` و`game_shared/sr_core.cpp` إلى `hldll`،
في كل من `projects/vs2019/*.vcxproj` و`linux/Makefile.hl_*`.
قواعد `%.o` العامة في Makefiles تتكفل بالباقي.

## كيف أُحدّث pins أو أحلّ تعارضاً؟

1. غيّر `ref` و`sha256` و`bytes` في `upstreams.json` بعد مراجعة الcommit الجديد
   (`curl .../codeload ... | sha256sum`).
2. `python3 -m merge.cli fetch --force` إن لزم، ثم `make merge` وافحص `MERGE_REPORT.md`.
3. التعارضات المحجورة في `integration/conflicts/*.diff3`: انقل الـ hunks المطلوبة
   يدوياً إلى الملف الهدف، ثم حوّل القاعدة إلى `on_conflict: ours` مع `manual_port`
   يوثّق ما نُقل.
4. `make verify && make verify-sdk` قبل أي commit.

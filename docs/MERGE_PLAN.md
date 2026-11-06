# خطة الدمج والقواعد (schema 2)

كل تعديل معلن في `merge/plan.json`؛ `python3 -m merge.cli plan` يعرض القواعد الـ30،
و`validate_plan()` يرفض أي إجراء مجهول، مسار traversal، مصدر غير معروف،
أو تعبير نمطي خاطئ في قواعد التدقيق.

## الأنواع

| action | الوظيفة | حقول أساسية |
| --- | --- | --- |
| `audit` | إثبات أن OP4 يوفّر إصلاح BugfixedHL أصلاً | `expect: [{meaning, pattern, min?, regex?}]`, `evidence`, `feature` |
| `three_way` | دمج `ours`(OP4) مع `theirs`(BugfixedHL) على `base`(vanilla) — متاح لقواعد مستقبلية | `base`, `ours`, `theirs`, `on_conflict`, `quarantine?` |
| `copy` | نسخ مع ترجمة مسار/تضمين وبانر مصدر | `from`, `path`, `include_rewrites?`, `banner?` |
| `inject` | إدراج مقطع عند anchor فريد | `anchor`, `where`, `snippet` |
| `generate` | توليد ملف من `data/` | `generator` = `speedrun_cfg` \| `route_json` |
| `skip` | توثيق قرار عدم النقل | `note` |

`audit` يعطي `audited` عند اكتمال كل الأنماط، و`anchor_drift` + تحذير عند غيابها.
ثلاثي الأطراف ما زال مدعوماً ومُختبراً (`ConflictPolicyTests`) لكنه غير مستخدم
في الخطة الحالية: راجع [`RESOLUTION.md`](RESOLUTION.md) للسبب.

## سياسات التعارض (إن استُخدم three_way)

| `on_conflict` | السلوك | الحالة |
| --- | --- | --- |
| `marker` | كتابة نتيجة الدمج بعلامات في `quarantine` وترك الملف الأصلي | `conflict` |
| `ours` | الإبقاء على OP4 وتسجيل سبب النقل اليدوي | `deferred` |
| `theirs` | اعتماد نسخة BugfixedHL | `donor` |
| `fail` | إيقاف القاعدة | `error` |

`--strict` يفشل عند `error`, `anchor_drift`, `missing` فقط.

## نقاط الحقن (10/10 مؤكدة مقابل الكود الفعلي)

| ملف OP4 | الـ anchor | المقطع |
| --- | --- | --- |
| `cl_dll/hud.cpp` | `#include "hud.h"` | `#include "sr_hud_timer.h"` + `"sr_hud_msg.h"` |
| `cl_dll/hud.cpp` | `void CHud::Init()\n{\n` | `HOOK_MESSAGE(SRSplit);` و`SR_HUD_Init();` |
| `cl_dll/hud_redraw.cpp` | `#include "hud.h"` | تضمين HUD |
| `cl_dll/hud_redraw.cpp` | `bool CHud::Redraw(float flTime, bool intermission)\n{\n` | `SR_HUD_Redraw(flTime)` |
| `dlls/world.cpp` | `#include "extdll.h"` | تضمين `sr_server.h` |
| `dlls/world.cpp` | `void CWorld::Spawn()\n{\n` | `SR_Server_OnMapSpawn(STRING(gpGlobals->mapname))` |
| `dlls/client.cpp` | `#include "extdll.h"` | تضمين `sr_server.h` |
| `dlls/client.cpp` | `void ClientPutInServer(edict_t* pEntity)\n{\n` | `SR_Server_OnClientPutInServer(pEntity)` |
| `dlls/UserMessages.cpp` | `gmsgShowGameTitle = REG_USER_MSG("GameTitle", 1);` | `gmsgSRSplit = REG_USER_MSG("SRSplit", -1);` |

تسجيل الرسالة قبل `CHud::Init` ضروري كي ينجح `pfnHookUserMsg` على العميل؛
ويوجد تسجيل احتياطي في `SR_Server_OnMapSpawn` إن لم يُطبّق الحقن.

## ملفات البناء

`merge/projects.py` يضيف idempotent:
`cl_dll/sr_hud_timer.cpp`, `cl_dll/sr_hud_msg.cpp`, `game_shared/sr_core.cpp`
إلى `hl_cdll`؛ و`dlls/sr_server.cpp`, `game_shared/sr_core.cpp` إلى `hldll`،
في `projects/vs2019/*.vcxproj` و`linux/Makefile.hl_*`.

## تحديث المصدر / حلّ تعارض جديد

1. غيّر `ref` + `sha256` + `bytes` في `upstreams.json` بعد مراجعة الـ commit.
2. `python3 -m merge.cli fetch --force` ثم `make merge` وافحص `MERGE_REPORT.md`.
3. إن ظهر `anchor_drift` في `audit`، حدّث `evidence`/الأنماط أو انقل الإصلاح
   يدوياً كقاعدة `copy`/`inject` جديدة — لا تُخفِ الفحص.
4. `make verify && make verify-sdk && make package` قبل أي commit.

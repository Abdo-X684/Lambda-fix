# تصميم طبقة السبيدرن (مكتمل)

## الزمن

* `sr::IClock` قابل للحقن: `SystemClock` (steady_clock) في اللعبة، `FakeClock` في الاختبارات.
* `RunTimer` يحسب `now - start - paused_total`؛ الإيقاف لا يضيف زمن التحميل،
  والتجميد عند `of7a0` يمنع تضخم الرن.
* `ServerMirror` على العميل: `OnServerSplit(at, now)` ثم
  `ProjectedMs(now2) = at + max(0, now2 - now)`؛ عند `Freeze` يتوقف نهائياً.
* `FormatTime` → `M:SS.mmm` أو `H:MM:SS.mmm`.

## الشبكة: `SRSplit`

| جهة | السلوك |
| --- | --- |
| السيرفر | `gmsgSRSplit = REG_USER_MSG("SRSplit", -1)` في `LinkUserMessages()`؛ عند كل تقسيم `MESSAGE_BEGIN(MSG_ALL, ...)` ثم `WRITE_LONG(at)`, `WRITE_LONG(delta)`, `WRITE_BYTE(hasPb)`, `WRITE_STRING(map)`, `MESSAGE_END()` |
| العميل | `HOOK_MESSAGE(SRSplit)` في `CHud::Init`؛ `__MsgFunc_SRSplit` يقرأ بـ `BEGIN_READ/READ_*` ويتحقق `READ_OK()` ثم `SR_HUD_OnSplit(...)` |
| HUD | يعرض `ServerMirror`، وآخر تقسيم مع فرق PB عبر `DrawConsoleString` |

`sr_net_splits 0` يعطّل البثّ للاختبار المحلي.

## المسار والتقسيمات

`data/op4_route.json` هو المصدر الوحيد: 13 فصلاً و39 خريطة، ومعسكر التدريب
`ofboot0..ofboot4` فئة منفصلة. `SplitAt(map)` يرفض المؤقّت المتوقف، الخريطة
المجهولة، والعودة للخلف؛ القفز للأمام مسموح (skips). `ParsePersonalBest`
يتجاهل الأسطر التالفة كي لا يُفسد ملف PB رنّاً كاملاً.

## الشرعية

| البند | الآلية |
| --- | --- |
| `sv_cheats` | `0` في cfg؛ السيرفر يعلم الرن INVALID إن كان مفعّلاً |
| `sr_practice_mode 1` | يمنع اعتبار الرن صالحاً |
| السلطة | المؤقّت على السيرفر + بثّ `SRSplit`؛ HUD مرآة فقط |
| bunnyhop | `sv_allowbunnyhopping 1` (مكافئ OP4 الأصلي لإصلاح BugfixedHL) |
| demo | `sr_autodemo 1` → `record sr_run_<epoch>` عند البدء/الإعادة، `stop` عند الخاتمة |
| binds | `F5` إعادة، `F6` تقسيم، `F7` تدريب — لا تلمس `Space` أو `E` |

## أوامر اللعبة

`sr_split`, `sr_reset`, `sr_practice_toggle` تُسجَّل مرة واحدة عند أول
`CWorld::Spawn`. ملف PB: أسطر `map=ms` في `splits/op4_pb.txt`.

## التحقق

`tools/verify_sdk.py`: 9 ملفات `g++ -fsyntax-only` أمام هيدرات OP4 الحقيقية
+ فحص عدم وجود علامات تعارض في أي مصدر قابل للبناء.

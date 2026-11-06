# تصميم طبقة السبيدرن

## الزمن

* `sr::IClock` قابل للحقن: `SystemClock` (steady_clock) في اللعبة، `FakeClock` في الاختبارات.
* `RunTimer` يحسب `now - start - paused_total`؛ الإيقاف المؤقت لا يضيف زمن التحميل،
  والتجميد عند `Finish()` يمنع تضخم الرن بعد `of7a0`.
* `FormatTime` → `M:SS.mmm` أو `H:MM:SS.mmm` للأزمنة الطويلة.

## المسار والتقسيمات

`data/op4_route.json` هو المصدر الوحيد: 13 فصلاً و39 خريطة (من
[SourceRuns Wiki](https://wiki.sourceruns.org/Opposing-Force-Maps.html))،
ومعسكر التدريب `ofboot0..ofboot4` فئة منفصلة على speedrun.com ولا يُخلط بالـ any%.

`SplitAt(map)` يرفض: مؤقّت متوقف، خريطة مجهولة، أو العودة للخلف في الترتيب.
القفز للأمام مسموح (skips شائعة في سبيدرن HL). آخر خريطة `of7a0` تُنهي الرن تلقائياً.
`ParsePersonalBest` يتجاهل التعليقات والأسطر التالفة والقيم السالبة كي لا يُفسد
ملف PB رنّاً كاملاً.

## الشرعية

| البند | الآلية |
| --- | --- |
| `sv_cheats` | يبقى `0` في cfg؛ السيرفر يعلم الرن INVALID إذا كان مفعّلاً |
| وضع التدريب | `sr_practice_mode 1` يمنع اعتبار الرن صالحاً |
| السلطة | المؤقّت على السيرفر، HUD العميل مرآة عرض فقط |
| demo | `sr_autodemo 1` مستوحى من BugfixedHL auto demo |
| الروابط | `F5` إعادة، `F6` تقسيم، `F7` تدريب — لا تلمس `Space` (bhop) ولا `E` |

## أوامر اللعبة

`sr_split`, `sr_reset`, `sr_practice_toggle` تُسجَّل مرة واحدة عند أول
`CWorld::Spawn` عبر `g_engfuncs.pfnAddServerCommand`.

## ملف PB

```
# BHLxOP4 personal best - map=ms
of0a0=1500
of1a1=2500
...
```

## HUD

`SR_HUD_Redraw` يرسم RTA وآخر تقسيم مع فرق PB باستخدام
`DrawConsoleString` و`gHUD.m_scrinfo` الحقيقيين من OP4 SDK.
التحقق: `tools/verify_sdk.py` يترجم كل ملفات glue والملفات المحقونة مقابل
هيدرات SDK الفعلية بـ `-fsyntax-only`.

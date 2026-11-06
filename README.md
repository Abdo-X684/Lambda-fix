# BugfixedHL × Opposing Force — Speedrun Merge Kit

دمج **BugfixedHL-Rebased** (إصلاحات Half-Life و bunnyhop و ConVar و HUD مؤقّت وتسجيل demo)
فوق **Half-Life: Opposing Force SDK** (الأسلحة، الوحوش، CTF، gamerules)، مع طبقة
**سبيدرن** كاملة: مؤقّت RTA سلطوي على السيرفر، تقسيمات لكل فصل، أفضل زمن شخصي،
HUD، و`speedrun.cfg` مولّد آلياً.

> المشروع ليس «نسخ ملفات ولصقها». تخطيط BugfixedHL هو `src/game/{client,server,shared}`
> بينما OP4 يحتفظ بتخطيط HLSDK الكلاسيكي `cl_dll/`, `dlls/`, `game_shared/`.
> لذلك الدمج هنا **مؤتمت، مثبّت على commit + sha256، ثلاثي الأطراف، وواعٍ بالتعارضات**.

---

## البدء السريع

```bash
make verify        # 51 اختبار Python + 63 فحص C++ + فحص التوليد + دمج offline
make fetch         # تنزيل SDKات الثلاثة المثبّتة مع التحقق من sha256
make merge         # الدمج الحقيقي → build/merged-real
make verify-sdk    # g++ -fsyntax-only للملفات المحقونة أمام هيدرات SDK الحقيقية
make serve         # لوحة التحكم على http://localhost:8000
```

لا توجد اعتماديات خارجية: Python 3.9+ (stdlib فقط)، g++ مع C++17، و`git`.
`cmake` اختياري عبر `make build-cmake`.

| أمر | الوصف |
| --- | --- |
| `python3 -m merge.cli plan` | عرض المصادر المثبّتة وقواعد الدمج الـ26 |
| `python3 -m merge.cli run --offline --strict` | دمج الـ fixtures بلا إنترنت، يفشل عند أي انحراف |
| `python3 -m merge.cli run --out build/merged-real` | دمج SDK الفعلي |
| `python3 -m merge.cli route --check` | سلامة المسار وتزامن هيدر C++ المولّد |
| `python3 -m merge.cli config --out speedrun.cfg` | توليد الإعدادات |
| `python3 tools/patch_projects.py --root build/merged --check` | هل ملفات البناء محدّثة؟ |

---

## ماذا أُنجز فعلاً (الحالة الحالية)

| جزء | الحالة |
| --- | --- |
| 3 مصادر مثبّتة بـ SHA كامل + sha256 للأرشيف | ✅ |
| محرّك دمج ثلاثي الأطراف (`git merge-file`) مع سياسات تعارض | ✅ |
| ترجمة مسارات `src/game/*` ↔ `cl_dll|dlls|game_shared` + إعادة كتابة `#include` | ✅ |
| 8 نقاط حقن بـ anchor وحيد (فحص انحراف تلقائي) في كود OP4 الحقيقي | ✅ 8/8 |
| تعديل `hl_cdll.vcxproj`, `hldll.vcxproj`, `Makefile.hl_cdll`, `Makefile.hldll` | ✅ 4/4 |
| نواة C++ نظيفة: مؤقّت، إيقاف/استئناف، تقسيمات، PB، تنسيق زمن، config | ✅ 63 فحص |
| HUD عميل + مؤقّت سيرفر + أوامر `sr_split` / `sr_reset` / `sr_practice_toggle` | ✅ |
| مسار OP4 الحقيقي: 13 فصلاً / 39 خريطة + معسكر تدريب منفصل (5) | ✅ |
| تقرير `MERGE_REPORT.json/md` مع بصمة شجرة حتمية | ✅ |
| لوحة تحكم RTL حية (مؤقّت، تقسيمات، تشغيل الدمج والاختبارات، cfg) | ✅ |
| CI على GitHub Actions | ✅ |
| تعارضات `pm_shared.cpp` (127 hunk) | ⚠️ محجورة في `integration/conflicts/` |
| ملفات `dlls/client.cpp` و`cl_dll/hud.cpp` المكتوبة بالكامل في BugfixedHL | ⚠️ مؤجلة لنقل يدوي موثّق |
| ربط DLL النهائي وتوزيع المود مع أصول اللعبة | ⏳ يتطلب أداة بناء HLSDK كاملة + أصول OP4 |

**نتيجة الدمج الحقيقي:** 811 ملف من OP4 → 827 ملف في الشجرة الناتجة، صفر أخطاء،
صفر انحراف anchors، و**7/7 من ملفات glue والملفات المحقونة تجتاز فحص الترجمة**
أمام هيدرات SDK الفعلية (`tools/verify_sdk.py`).

هذه صراحةً طبقة أساس ليوم العمل الأول: التعارضات لا تُخفى، بل تُحجر ويُوثّق
سبب التأجيل في التقرير. لا يوجد ادّعاء بأن المود قابل للعب بالكامل بعد.

---

## المعمارية

```
upstreams.json ──(pin + sha256)──> make fetch ──> .cache/upstreams/{op4,bugfixhl,valve_hlsdk}
                                                     │
merge/plan.json ──(26 قاعدة)──> merge/engine.py <──────┘
   │                              │  copy target tree
   │                              ├─ three_way(op4 ← vanilla → bugfixhl)
   │                              ├─ copy  (reference ports + sr_core + overlay)
   │                              ├─ inject(anchor-checked hooks)
   │                              ├─ generate(speedrun.cfg, op4_route.json)
   │                              └─ patch_projects(vcxproj + Makefiles)
   │                              ↓
   │                     build/merged + MERGE_REPORT.{json,md} + tree sha256
   ↓
data/op4_route.json ──> tools/gen_route_header.py ──> src/speedrun/sr_route_data.h
        │                                            ├─> C++ tests (63 checks)
        ├──> web/app.py (dashboard + JSON API)       └─> game_shared/sr_core.cpp
        └──> merge/configgen.py ──> gamedir/speedrun.cfg
```

التفاصيل في [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)،
وقواعد الدمج في [`docs/MERGE_PLAN.md`](docs/MERGE_PLAN.md)،
ومنطق السبيدرن في [`docs/SPEEDRUN.md`](docs/SPEEDRUN.md).

---

## السبيدرن

* المؤقّت على **السيرفر** ويقرأ ساعة `std::chrono::steady_clock`، لا معدّل الإطارات.
* كل `changelevel` = تقسيم؛ الخرائط تُنفّذ بترتيب المسار فقط، والخرائط غير المعروفة لا تُنهي الرن.
* `sv_cheats` يجب أن يبقى `0`؛ أي رن مع Cheats يُعلَم INVALID ولا يُكتب PB.
* `sr_practice_mode 1` يعطّل كتابة PB. الروابط: `F5` إعادة، `F6` تقسيم، `F7` وضع التدريب
  (تُترك `Space` للقفز و`E` للاستخدام).
* PB يُخزَّن كأسطر `map=ms` في `splits/op4_pb.txt`، ويُقرأ بتسامح مع الأسطر التالفة.

---

## الرخص

كود هذا المستودع MIT. **لكن** الـ SDKات ليست مُضمّنة في git: تُنزّل عند البناء فقط،
والشجرة الناتجة تخضع لرخصها (Valve HLSDK non-commercial، وGPL-3.0 لـ BugfixedHL،
ورخصة TWHL). ملفات `integration/ports/` منقولة للمراجعة فقط ولا تُترجم.
اقرأ [`docs/LICENSES.md`](docs/LICENSES.md) قبل أي توزيع.

---

## 🎯 وماذا نشتري بـ 100,000$؟

محطة بناء 18K، شاشات 240Hz وقياس الإدخال 6K، مختبر توافق Steam/WON/Linux 12K،
CI runners 8K، قهوة 3K… و53K للإصدار 1.0. أما BugfixedHL فمفتوح المصدر،
لذا لا يمكن شراؤه — وهذا أفضل 😄. (الجائزة تُصرف بعد `make verify` طبعاً.)

---

## English TL;DR

A reproducible, conflict-aware merge kit that ports BugfixedHL fixes and
speedrun tooling onto the Opposing Force SDK. Upstreams are pinned by commit
and tarball checksum; a 3-way merge (vanilla HLSDK as base) plus anchor-checked
injections produce a merged SDK tree, a deterministic tree hash and a JSON/MD
report. A clean-room C++17 core implements the RTA timer, splits, PB and config
generation; a live RTL dashboard drives the pipeline. `make verify` runs all
checks; `make fetch && make merge && make verify-sdk` exercises the real SDKs.
Conflicts are quarantined and manual ports are documented, never hidden.

### المصادر

* [tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased)
* [twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated)
* [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife)
* [SourceRuns: Opposing Force Maps](https://wiki.sourceruns.org/Opposing-Force-Maps.html)

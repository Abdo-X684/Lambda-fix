# BugfixedHL × Opposing Force — Speedrun Merge Kit ✅

دمج **BugfixedHL-Rebased** (إصلاحات Half-Life و bunnyhop و ConVar و HUD مؤقّت وتسجيل demo)
فوق **Half-Life: Opposing Force SDK** (الأسلحة، الوحوش، CTF، gamerules)، مع طبقة
**سبيدرن** كاملة: مؤقّت RTA سلطوي على السيرفر، بثّ التقسيمات للعميل عبر رسالة
`SRSplit`، أفضل زمن شخصي، HUD، تسجيل demo تلقائي، و`speedrun.cfg` مولّد آلياً.

> المشروع ليس «نسخ ملفات ولصقها». تخطيط BugfixedHL هو `src/game/{client,server,shared}`
> بينما OP4 يحتفظ بتخطيط HLSDK الكلاسيكي `cl_dll/`, `dlls/`, `game_shared/`.
> لذلك الدمج هنا **مؤتمت، مثبّت على commit + sha256، مدقَّق التكافؤ، وخالٍ من التعارضات**.

**الحالة: مكتمل.** `0 تعارضات · 0 منقولات مؤجلة · 0 أخطاء · 0 انحراف anchors`.

---

## البدء السريع

```bash
make verify        # النظافة + 111 اختبار Python + 77 فحص C++ + التوليد + الدمج + الحزمة
make hygiene       # فحص المسافات/JSON/الاستيرادات/روابط الوثائق
make tidy          # تنظيف __pycache__ والمجلدات المرحلية ثم إعادة الفحص
make fetch         # تنزيل SDKات الثلاثة المثبّتة مع التحقق من sha256
make merge         # الدمج الحقيقي → build/merged-real
make verify-sdk    # g++ -fsyntax-only لـ9 ملفات + فحص خلوّ المصادر من علامات التعارض
make package       # dist/bhl-op4-speedrun-overlay.zip + MANIFEST.json
make build-dlls    # client.so + hl.so (يحتاج gcc-multilib + vgui.so من اللعبة)
make serve         # لوحة التحكم + صفحة README على http://localhost:8000
```

لا توجد اعتماديات خارجية: Python 3.9+ (stdlib فقط)، g++ مع C++17، و`git`.
`cmake` اختياري عبر `make build-cmake`.

### ⬇ تحميل المود الجاهز

**حمّل [`bhl-op4-mod.zip`](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/bhl-op4-mod.zip)**،
فكّه داخل مجلد Half-Life بجوار `valve/` و`gearbox/`، وشغّل `-game bhlop4`.
يحتوي `client.so` + `hl.so` (ELF32) مع `liblist.gam`, `steam_appid.txt`,
`delta.lst`, `speedrun.cfg` و`splits/`.

> ⚠️ **لا تضع الملفات داخل `gearbox/`**: SDK يرفض أي مجلد يبدأ بـ `gearbox`
> أو `valve` ويغلق اللعبة برسالة *“run from its intended location”*.
> المجلد المستقل `bhlop4` + `fallback_dir "gearbox"` هو الحل؛ التفاصيل في
> [`docs/BUILDING.md`](docs/BUILDING.md).

الملفان منشوران أيضاً كأصول منفردة في [**GitHub Release**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.1.0-linux32):
[client.so](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/client.so) ·
[hl.so](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/hl.so) ·
[`MANIFEST.json`](dist/dlls/MANIFEST.json)، ومن لوحة التحكم زر «⬇ المود الجاهز».
`make mod` يعيد توليد المجلد والأرشيف.

### 🔎 كيف تتأكد أن الدمج شغّال؟

النسخة `v0.1.1` تُظهر سطراً أخضر `[ BHL x OP4 SPEEDRUN ] v0.1.1` أعلى يسار
الشاشة مع مؤقت `RTA`، وتطبع `[BHLxOP4] client.so LOADED` في الكونسول،
والأمر **`sr_status`** يعرض الإصدار والخريطة وحالة المؤقت. إن لم يظهر شيء من
هذا فالمكتبات لم تُحمّل: تأكد من `Half-Life/bhlop4/` ومن `-game bhlop4` في
خيارات التشغيل. التفاصيل في [`docs/BUILDING.md`](docs/BUILDING.md).

### 🖥 واجهة المشروع

`make serve` يفتح لوحة RTL بتبويبين: **لوحة التحكم** (مؤقّت، الدمج، التدقيقات،
cfg، الحزمة، شريط انتقال سريع) و**README والوثائق** — عارض Markdown محلي آمن
يعرض `README.md` وكل `docs/*.md` بفهرس جانبي، جداول، كتل أوامر، وروابط تنتقل
بين الوثائق. الرابط المباشر للصفحة: `/#docs` (أو `/#docs/docs/RESOLUTION.md`).
لا CDN ولا مكتبات JavaScript؛ المحتوى يُقرأ من المستودع عبر `/api/docs`
و`/api/doc`، والـ HTML يُهرَّب خادمياً قبل إرساله.

| أمر | الوصف |
| --- | --- |
| `python3 -m merge.cli plan` | عرض المصادر المثبّتة وقواعد الدمج الـ30 |
| `python3 -m merge.cli run --offline --strict` | دمج الـ fixtures بلا إنترنت، يفشل عند أي انحراف |
| `python3 -m merge.cli route --check` | سلامة المسار وتزامن هيدر C++ المولّد |
| `python3 -m merge.cli config --out speedrun.cfg` | توليد الإعدادات |
| `python3 tools/patch_projects.py --root build/merged-real --check` | هل ملفات البناء محدّثة؟ |

---

## ماذا أُنجز فعلاً

| جزء | الحالة |
| --- | --- |
| 3 مصادر مثبّتة بـ SHA كامل + sha256 للأرشيف | ✅ |
| محرّك دمج: 30 قاعدة (تدقيق تكافؤ، نسخ، حقن، توليد) | ✅ |
| **حلّ الـ127 تعارضاً** بتدقيق تكافؤ آلي: OP4 يوفّر bunnyhop أصلاً عبر `physinfo "bj"` + `sv_allowbunnyhopping` | ✅ 3/3 تدقيقات |
| **إغلاق المنقولات المؤجلة** (`client.cpp`, `hud.cpp`) بإثبات أن إصلاحات BugfixedHL موجودة في OP4-updated | ✅ |
| 10 نقاط حقن بـ anchor وحيد في كود OP4 الحقيقي (منها تسجيل `SRSplit`) | ✅ 10/10 |
| تعديل 4 ملفات بناء (`vcxproj` + Linux Makefiles) | ✅ 4/4 |
| نواة C++17: مؤقّت، إيقاف/استئناف، تقسيمات، PB، `ServerMirror`، config | ✅ 77 فحص |
| رسالة شبكة `SRSplit` سيرفر → عميل + HUD يعرض زمن السيرفر | ✅ |
| تسجيل demo تلقائي (`sr_autodemo`) وأوامر `sr_split` / `sr_reset` / `sr_practice_toggle` | ✅ |
| مسار OP4 الحقيقي: 13 فصلاً / 39 خريطة + معسكر تدريب منفصل (5) | ✅ |
| تقرير `MERGE_REPORT.json/md` ببصمة شجرة حتمية | ✅ |
| لوحة تحكم RTL حية (مؤقّت، تقسيمات، الدمج، الاختبارات، الحزمة، cfg) | ✅ |
| **حزمة توزيع** قابلة للتحقق بـ sha256، بلا أي كود SDK مرخّص خارجياً | ✅ |
| CI على GitHub Actions (verify + دمج حقيقي + فحص ترجمة + حزمة) | ✅ |

**نتيجة الدمج الحقيقي:** 811 ملف من OP4 → **828 ملف**، صفر أخطاء، صفر تعارضات،
صفر مؤجّلات، صفر انحراف، **9/9 ملفات glue/mحقونة تجتاز فحص الترجمة** أمام هيدرات
SDK الفعلية، ولا علامات تعارض في أي ملف قابل للبناء.

القرار الهندسي موثّق بالسطور والأدلة في [`docs/RESOLUTION.md`](docs/RESOLUTION.md):
إعادة دمج ملفات أُعيد كتابتها بالكامل كان سيدمّر كود OP4، بينما OP4-updated يوفّر
السلوك نفسه أصلاً — فاستُبدل الدمج الأعمى بتدقيق تكافؤ آلي + توصيل الـ cvar الصحيح.

الخطوة الوحيدة التي تحتاج بيئة خارجية هي **ربط الـ DLL النهائي**: نفّذ
`make build-dlls` بعد `make fetch && make merge` على جهاز فيه `gcc-multilib`
ونسخة من اللعبة (للحصول على `vgui.so` والأصول). الدليل الكامل — بما فيه «من أين
أحمّل كل شيء» — في [`docs/BUILDING.md`](docs/BUILDING.md). الملفات والمشاريع
جاهزة ومُختبرة نحوياً، والسكربت يفحص البيئة ويقول لك بصراحة ما ينقصها.

---

## المعمارية

```
upstreams.json ──(pin + sha256)──> make fetch ──> .cache/upstreams/{op4,bugfixhl,valve_hlsdk}
                                                     │
merge/plan.json ──(30 قاعدة)──> merge/engine.py <─────┘
   │                              │  copy target tree
   │                              ├─ audit   (BugfixedHL fix == OP4-native code, 3/3)
   │                              ├─ copy    (reference ports + sr_core + overlay)
   │                              ├─ inject  (anchor-checked hooks, 10/10)
   │                              ├─ generate(speedrun.cfg, op4_route.json)
   │                              └─ patch_projects(vcxproj + Makefiles)
   │                              ↓
   │                     build/merged-real + MERGE_REPORT.{json,md} + tree sha256
   ↓
data/op4_route.json ──> gen_route_header.py ──> src/speedrun/sr_route_data.h
        │                                       ├─> 77 C++ checks
        ├──> web/app.py (dashboard + JSON API)  └─> game_shared/sr_core.cpp
        ├──> merge/configgen.py ──> gamedir/speedrun.cfg
        └──> tools/package_mod.py ──> dist/*.zip + MANIFEST.json
```

**فهرس الوثائق:** [`docs/README.md`](docs/README.md) · [`BUILDING`](docs/BUILDING.md) · [`ARCHITECTURE`](docs/ARCHITECTURE.md) ·
[`MERGE_PLAN`](docs/MERGE_PLAN.md) · [`RESOLUTION`](docs/RESOLUTION.md) ·
[`SPEEDRUN`](docs/SPEEDRUN.md) · [`ROADMAP`](docs/ROADMAP.md) ·
ودليل المساهمة [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## السبيدرن

* المؤقّت على **السيرفر** يقرأ `std::chrono::steady_clock`، لا معدّل الإطارات.
* كل `changelevel` = تقسيم، ويُبثّ للعميل: `WRITE_LONG(at) + WRITE_LONG(delta) + WRITE_BYTE(hasPb) + WRITE_STRING(map)`.
  العميل يعرض `sr::ServerMirror` (زمن السيرفر + إسقاط محلي رتيب بين الرسائل).
* `sv_cheats` يبقى `0`؛ أي رن مع Cheats يُعلَم INVALID. `sr_practice_mode 1` يعطّل PB.
* `sv_allowbunnyhopping 1` هو المكافئ الأصلي في OP4 لـ bhop cap في BugfixedHL.
* الروابط: `F5` إعادة، `F6` تقسيم، `F7` تدريب (تُترك `Space` للقفز و`E` للاستخدام).
* `sr_autodemo 1` يسجّل demo لكل رن ويوقفه عند `of7a0`.

---

## الرخص

كود هذا المستودع MIT. **لكن** الـ SDKات ليست مُضمّنة في git، والحزمة لا تحتوي
أيّاً من مصادرها: تُنزّل عند البناء فقط والشجرة الناتجة تخضع لرخصها.
ملفات `integration/ports/` منقولة للمراجعة فقط ولا تُترجم.
اقرأ [`docs/LICENSES.md`](docs/LICENSES.md) قبل أي توزيع.

---

## 🎯 وماذا نشتري بـ 100,000$؟

محطة بناء 18K، شاشات 240Hz وقياس الإدخال 6K، مختبر توافق Steam/WON/Linux 12K،
CI runners 8K، قهوة 3K… و53K للإصدار 1.0. أما BugfixedHL فمفتوح المصدر،
لذا لا يمكن شراؤه — وهذا أفضل 😄. (الجائزة صُرفت بعد `make verify`.)

---

## English TL;DR

A reproducible merge kit that ports BugfixedHL fixes and speedrun tooling onto
the Opposing Force SDK. Upstreams are pinned by commit and tarball checksum;
machine-verified equivalence audits (OP4 already implements the donor fixes),
anchor-checked injections, and build-file patching produce a merged SDK tree
with **zero conflicts, zero deferred ports, zero errors** and a deterministic
tree hash. A clean-room C++17 core implements the RTA timer, splits, PB,
server-time projection and config generation; a server→client `SRSplit` user
message keeps the HUD authoritative. A distributable, sha256-manifested overlay
package and an RTL live dashboard are included. `make verify` runs everything;
`make fetch && make merge && make verify-sdk && make package` exercises the
real SDKs. Only the final DLL link needs the external HLSDK toolchain.

### المصادر

* [tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased)
* [twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated)
* [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife)
* [SourceRuns: Opposing Force Maps](https://wiki.sourceruns.org/Opposing-Force-Maps.html)

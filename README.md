# BugfixedHL × Opposing Force — الأساس هو BugfixedHL

> **الحزمة الحالية:** [`build-evidence/bhl-base/bhl-base-mod.zip`](build-evidence/bhl-base/bhl-base-mod.zip)
> · [**Release مباشر**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/bhl-op4-full-20261111/bhl-base-mod.zip)
> · [**تدقيق المصادر والأصول**](docs/OP4_SOURCE_AUDIT.md)
> · [**جدول اختبارات GoldSrc**](docs/OP4_RUNTIME_TESTS.md)
> · [**جرد الأسلحة**](docs/WEAPON_INVENTORY.md)
> · [**INSTALL**](build-evidence/bhl-base/mod/INSTALL.md)

## الحالة بصراحة

| البند | الوضع |
| --- | --- |
| البنية | عميل BHL/VGUI2/الحركة/Bhop + خادم OP4 كامل وحملة `of0a0`؛ `bhlop4` بجانب `valve/` و`gearbox/` |
| المصادر | [`bhl-op4/PROVENANCE.json`](bhl-op4/PROVENANCE.json): 694 ملف BHL (671 مطابق + 23 مدمج)، 154 ملف OP4، 11 ملف glue، بالالتزامات المثبّتة في [`upstreams.json`](upstreams.json) |
| بعد بلاغ «الأسلحة لا تعمل» | إصلاحات مصدرية موثّقة: `ItemInfoArray`/تسجيل الذخيرة/`GetAmmoIndex`، نقل `iuser4`/`ammo_spores`/`ammo_762`، حلقات 64، `OldWeapon`/`HudColor`، `delta.lst` مدمج BHL+OP4 |
| الموسيقى | `setup_op4_media.bat` ينسخ MP3 الأصلية من `gearbox/media` فقط؛ لا MP3 داخل ZIP ولا ملف مُولّد |
| البناء | Linux ELF32 `152/152` عميل و`179/179` خادم؛ Windows `client.dll`/`opfor.dll` عبر CI/MSVC؛ التفاصيل في [`MANIFEST`](build-evidence/bhl-base/MANIFEST.json) |
| اختبار داخل GoldSrc | ❌ **لم يُنفَّذ هنا** — لا محرك ولا أصول OP4 شرعية؛ كل صف في [`RUNTIME_TESTS.md`](docs/OP4_RUNTIME_TESTS.md) يحمل `غير مُختبَر` |
| إعلان الاكتمال | ❌ **لا** — المستخدم بلّغ أن اللعبة تبدأ لكن الموسيقى والأسلحة ليست صحيحة؛ الإصلاحات الجديدة تحتاج تحققاً داخل اللعبة |

## التشغيل

1. فكّ ZIP إلى `Half-Life/bhlop4/` (ليس `gearbox_addon`، ولا تغيير اسم `gearbox`).
2. شغّل `setup_op4_media.bat` مرة واحدة قبل اللعبة.
3. شغّل `hl.exe -game bhlop4 -console`.
4. اختبر الحملة، الموسيقى، وكل سلاح بحسب [`RUNTIME_TESTS.md`](docs/OP4_RUNTIME_TESTS.md).

**حد ملزم:** لا توجد علامة نجاح لأي سلاح أو للموسيقى حتى يختبرها المستخدم داخل GoldSrc.
التجميع وCI ووجود الملفات ليست دليل تشغيل. لا تستخدم حزم `dist/` القديمة.

## الدليل والبرهان

* [`docs/OP4_WEAPON_PHASES.md`](docs/OP4_WEAPON_PHASES.md) — سجل دمج أسلحة OP4 مرحلة بمرحلة: الملفات، الفرق، بناء العميل/الخادم، الاختبارات، الأخطاء، والنواقص.
* [`docs/BHL_FINAL_AUDIT.md`](docs/BHL_FINAL_AUDIT.md) — التقرير الجامع: كل رمز، كل تغيير على BHL، كل اختبار ونتيجته، النواقص صراحةً.
* [`docs/BHL_BASE_BUILD.md`](docs/BHL_BASE_BUILD.md) و
  [`build-evidence/bhl-base/MANIFEST.json`](build-evidence/bhl-base/MANIFEST.json)
  — 459 بصمة مصدر لينكس و462 بصمة ويندوز، سجل كامل، بصمات مطابقة للملفات المترجمة فعلياً على القرص.
* [`build-evidence/bhl-base/LINK_GAP_CLOSURE.md`](build-evidence/bhl-base/LINK_GAP_CLOSURE.md)
  — جدول الـ12 رمزاً: التنفيذ الأصلي، سبب الغياب، التغيير، دليل الاختفاء، الاختبار؛ ومعها `IsFacing` و`CGib::SpawnRandomGibs(GibData)` في التقرير النهائي.
* [`bhl-op4/PORT_STATUS.json`](bhl-op4/PORT_STATUS.json) — نتيجة ترجمة كل مصدر OP4
  إلى كائن ELF32 حقيقي مقابل هيدرات BHL المدمجة.
* [`build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md`](build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md)
  — أدلة قابلة لإعادة التشغيل على استحالة الاختبار داخل اللعبة.
* `python3 -m merge.bhl_base --check --out bhl-op4` يتحقق من كل بصمة،
  و`tests/test_bhl_base.py::test_07` يقارن الـ677 ملفاً بالمصدر المثبّت.

```bash
make fetch                                  # الشجرتان المثبّتتان + sha256
make bhl-base                               # إعادة بناء bhl-op4/ من الصفر
python3 tools/verify_bhl_base.py --compile  # كائنات ELF32 + PORT_STATUS.json
python3 tools/build_bhl_base.py             # بناء client.so و hl.so من bhl-op4/
make test-op4                               # خوارزمية OP4 الحقيقية + مُعدّد الكيانات
make test-op4-fixups                        # أجسام الإصلاحات الحقيقية مُستخرجة نصّاً
python3 -m unittest tests.test_op4_link_fixups -v
python3 tools/probe_runtime_environment.py  # فحص بيئة التشغيل
make verify                                 # كل فحوصات المستودع
```

## ما لم يُنجز بعد — بصراحة

1. **لا اختبار داخل Opposing Force**: لا تحميل في محرك، لا خريطة، لا HUD/UI،
   لا أسلحة BHL/OP4، لا تبديل ولا ذخيرة ولا إعادة تعبئة، لا Monster/Rope/Grapple/CTF
   وقت تشغيل، ولا مراقبة أعطال. الأسباب بأدلة في `RUNTIME_ENVIRONMENT.md`.
2. **قواعد CTF صارت موصولة وفعلية**: `ctf/ctfplay_gamerules.cpp` مترجم وموصول،
   و`InstallGameRules` ينشئ `CHalfLifeCTFplay`/`CHalfLifeCoopplay`، و`IsCTF()`
   تعيد `true` في قواعد CTF، و13 رسالة و9 cvars مسجّلة، والقوائم و`respawn`
   بأجسام OP4 الحقيقية. **لكن مباراة CTF داخل اللعبة غير مُختبَرة**، وHUD عميل
   OP4 غير موصول (تعارض VGUI1/VGUI2). التفاصيل في
   [`docs/COMPLETION_INVENTORY.md`](docs/COMPLETION_INVENTORY.md).
   **25 ملف OP4 ما زالت `port-pending`** (21 عميل + 4 خادم مستبعدة بأسباب معلَنة).
3. لم يُنفَّذ configure/build بـ CMake كاملاً (استُخدم استنساخ أمين لقوائمه مع Zig-clang).
4. **الثنائيات والـ Release أدناه قديمة**: `dist/dlls/*.so`, `dist/bhlop4/`,
   `v0.1.0-linux32` مبنية من شجرة **OP4-أساس** السابقة، لم تُلمس، ولا تُستخدم كدليل.
5. لا PR إلى `main`، ولا تحديث Release، ولا توزيع ثنائيات، ولا ادعاء امتثال ترخيصي.

## الرخص

BHL: GPL-3.0. OP4/Valve HLSDK: رخصة Valve غير التجارية.
[`docs/LICENSES.md`](docs/LICENSES.md) — لا يدّعي المستودع امتثالاً لتوزيع ثنائي.

---

## ⚠️ ما يلي توثيق المرحلة السابقة (legacy)

الأقسام التالية تصف نهج «OP4 هو الأساس + `sr_*`» الذي رُفض بعد التدقيق.
تُترك كسجلّ تاريخي فقط؛ **لا تعتمد عليها** كحالة المشروع الحالية.

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

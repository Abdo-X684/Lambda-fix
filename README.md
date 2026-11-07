# BugfixedHL × Opposing Force — **BHL هو الأساس** ✅

> **الشجرة المعتمدة:** [`bhl-op4/`](bhl-op4/PROVENANCE.json).
> **BugfixedHL-Rebased هو الأساس الكامل** (694 ملفاً منسوخة حرفياً)، وفوقه
> تُدمج أنظمة وأسلحة **Opposing Force**. هذا عكس النهج السابق الذي كان OP4
> هو الأساس — راجع [`docs/LEGACY.md`](docs/LEGACY.md) و
> [`docs/BHL_BASE_MERGE.md`](docs/BHL_BASE_MERGE.md).

## ما تغيّر فعلاً

| بند | السابق (legacy) | الآن |
| --- | --- | --- |
| الأساس | OP4 (828 ملف) | **BHL @ `4d32095e3c33` — 694 ملف** |
| كود BHL في `client.so` | 4 ملفات فقط | الشجرة كلها + 15 سلاح OP4 مُترجمة فوقها |
| كود BHL في `hl.so` | **صفر** | لم يُبنَ بعد (انظر «ما لم يُنجز») |
| `ConVar/CvarSystem` | إعادة تنفيذ مستقلة (تشابه `0.030`) | نظام BHL الأصلي في الشجرة |
| دمج ثلاثي الأطراف | `merged=0` | 20 قاعدة دمج معلنة داخل هيدرات BHL |
| إثبات المصدر | بانرات و`strings` | `PROVENANCE.json` بـ sha256 لكل ملف |

## الدليل المعماري والبرهان

* [`bhl-op4/PROVENANCE.json`](bhl-op4/PROVENANCE.json) — أصل كل ملف، و`commit`،
  و`sha256`، واسم كل قاعدة عدّلته (851 مدخلاً).
* [`bhl-op4/PORT_STATUS.json`](bhl-op4/PORT_STATUS.json) — نتيجة ترجمة كل
  مصدر OP4 إلى **كائن ELF32 حقيقي** مقابل هيدرات BHL المدمجة.
* **683 / 683 ملف BHL منسوخ حرفياً** يطابق الـ commit المثبّت بايتاً ببايت
  (و11 ملف BHL آخر عليها دمج معلن)، وبصمة الشجرة `base.tree_sha256` محسوبة
  ومُعاد التحقق منها في كل `--check`.
* **103 / 109 من مصادر خادم BHL نفسها** تُترجم إلى كائنات ELF32 مقابل الشجرة
  المدمجة — أي أن الأساس كود BHL قابل للترجمة فعلاً، لا هيدرات فقط.
* **15 / 15 أسلحة OP4 تُترجم بنجاح** (CDisplacer, Eagle, Grapple, Knife, M249,
  Penguin, Pipewrench, ShockRifle, SniperRifle, Spore, …) و**48 / 69** من مصادر
  خادم OP4. 16 مصدراً فقط موصولة بـ `src/game/server/CMakeLists.txt` — لا يُوصل
  أي ملف لم تُثبت ترجمته.
* 20 قاعدة دمج حقيقية: `WeaponId`، `Bullet`، `WaterLevel`، حقول `skilldata_t`،
  حالة `CBasePlayer`/`CBaseMonster`، `CWorld::World`، `IsCTF()`… كلها داخل
  **ملفات BHL نفسها**، لا في طبقة بديلة.

```bash
make fetch                                  # الشجرتان المثبّتتان + sha256
make bhl-base                               # إعادة بناء bhl-op4/ من الصفر
python3 tools/verify_bhl_base.py --compile  # كائنات ELF32 + PORT_STATUS.json
make verify-bhl-base                        # فحص المصدر + المصادر الموصولة
make verify                                 # كل فحوصات المستودع
```

## ما لم يُنجز بعد — بصراحة

1. **لا يوجد `client.so` / `hl.so` من الشجرة الجديدة.** البناء الكامل يحتاج
   CMake ≥ 3.30، حزم vcpkg، و`tmp64/hl1_source_sdk @ 11f26656677c…`.
   لم أُنتج ثنائيات وهمية.
2. **الثنائيات والـ Release أدناه قديمة**: `dist/dlls/*.so`, `dist/bhlop4/`,
   `v0.1.0-linux32` مبنية من شجرة **OP4-أساس** السابقة. لا تستخدمها كدليل
   على هذا الدمج. لم ألمسها ولم أُحدّث الـ Release.
3. مصادر عميل OP4 وCTF/كيانات/rope منسوخة لكنها `port_pending`؛ أخطاء كل
   ملف مدرجة في `PORT_STATUS.json`. `UTIL_IsCTF()` تُعيد `false` صراحةً.
4. لا يُدعى أن المود قابل للعب كاملاً؛ `vgui.so` وأصول اللعبة من نسختك الشرعية.

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

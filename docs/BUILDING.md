# كيف أبني `client.so` — ومن أين أحمّل الأشياء؟

## ✅ جاهز للتحميل الآن (الطريقة الأسرع)

بنيتُ الاثنين فعلاً داخل المشروع بـ Zig كمُصرّف i386 عابر (بلا `gcc-multilib`
وبلا `vgui.so` من اللعبة وقت الربط):

| الملف | الحجم | التحميل |
| --- | --- | --- |
| `client.so` | 9.0 MB | [**⬇ مباشر**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/client.so) · [صفحة Release](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.1.0-linux32) · [من اللوحة](/dist/dlls/client.so) |
| `hl.so` | 15.9 MB | [**⬇ مباشر**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/hl.so) · [صفحة Release](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.1.0-linux32) · [من اللوحة](/dist/dlls/hl.so) |
| `MANIFEST.json` | sha256 + ELF32 | [**⬇ مباشر**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/MANIFEST.json) |

اضغط الزر، ضع `client.so` في `gearbox/cl_dlls/` و`hl.so` في `gearbox/dlls/`،
وشغّل `-game gearbox`. لإعادة إنتاجهما: `make build-dlls-zig` (يحتاج
`pip install ziglang` فقط). **`vgui.so` الحقيقية وأصول اللعبة تبقى من نسختك
المشروعة**؛ المكتبة الوهمية استُخدمت للربط فقط لإنشاء `DT_NEEDED`، ولا تُوزّع.

---

## الجواب المختصر

**`client.so` لا يُحمّل من موقع: يُبنى من الشجرة المدموجة.** لا يوجد رابط «شرعي»
لتحميله جاهزاً، ومستودعنا لا يوزّع ثنائيات Valve/Gearbox. النسخة الأصلية أصلاً
موجودة داخل لعبتك عند:

```
.../steamapps/common/Half-Life/gearbox/cl_dlls/client.so   # العميل
.../steamapps/common/Half-Life/gearbox/dlls/hl.so          # السيرفر
```

ومهمتنا أن نستبدلها بنسخة مبنية من `build/merged-real/` (التي تحتوي HUD
السبيدرن و`SRSplit` و`sr_core`). المخرجان دائماً `client.so` و`hl.so`،
أولهما لـ `cl_dlls/` والثاني لـ `dlls/` [1](https://deepwiki.com/twhl-community/halflife-op4-updated).

```bash
make fetch && make merge          # ① الشجرة المدموجة (828 ملف، 0 تعارضات)
make build-dlls                   # ② الفحص ثم البناء ثم dist/dlls/
```

أو يدوياً، وهو نفس الشيء الذي يفعله السكربت:

```bash
cd build/merged-real/linux
make CFG=release                  # → release/client.so و release/hl.so
```

---

## إذن ماذا أحمّل فعلاً؟

| تحتاجه | من أين | هل أحمّله يدوياً؟ |
| --- | --- | --- |
| مصادر OP4 / BugfixedHL / HLSDK | `make fetch` ينزّلها تلقائياً بـ commit + sha256 مثبّتين في `upstreams.json` | ❌ لا — مؤتمت بالكامل |
| **أداة البناء 32-bit** | مدير حزم توزيعتك: `sudo apt install build-essential gcc-multilib g++-multilib libgl1-mesa-dev` (GCC 9+ / C++17) | ✅ نعم، من الـ repos |
| **أصول اللعبة** (`gearbox/`, الخرائط، الأصوات) | Steam: Half-Life (app 70) + Opposing Force (app 50) [2](https://steamcommunity.com/app/50/discussions/0/3103512736615438885/)؛ أو سيرفر عبر SteamCMD: `+app_set_config 90 mod gearbox +app_update 90 validate` [1](https://steamcommunity.com/discussions/forum/13/810938082280349586/) | ✅ نعم — للتشغيل فقط، لا للت compiling |
| **`vgui.so`** (مكتبة Valve الخاصة) | جذر تثبيت اللعبة: `Half-Life/vgui.so` — **لا تُوزّع ولا تُبنى هنا** [4](https://github.com/ranting-soberly/half-life-decay-linux-installer) | ✅ انسخها من لعبتك |
| `delta.lst`, `speedrun.cfg`, `splits/` | `network/delta.lst` من الـ SDK + حزمة `make package` | ❌ السكربت ينسخها مع `--install` |

> ⚠️ `vgui.so` هي الملف الوحيد الذي لا يستطيع المستودع توفيره: رابط العميل
> (`-L$(CFG) vgui.so`) يبحث عنها في `linux/release/`. انسخها إلى هناك، أو مرّر
> `--vgui /path/to/Half-Life/vgui.so`، أو اضبط `HL_ROOT` على مجلد اللعبة.

---

## لماذا 32 بالتحديد؟ 🔧

محرك GoldSrc على Linux عبارة عن **ELF 32-bit**، لذا `linux/Makefile` يستخدم
`CPLUS="g++ -m32"` و`ARCH=i386`. أي `client.so` بـ 64-bit سيرفضه المحرك
برسالة `could not load library client.so`. لذلك `-m32` + مكتبات i386 شرط،
وليست خياراً [4](https://github.com/ranting-soberly/half-life-decay-linux-installer).

في هذه الـ sandbox تحديداً `g++ -m32` يفشل بـ `cannot find Scrt1.o` لأن
`gcc-multilib` غير مثبّت ولا توجد أصول لعبة — لذلك **لا أستطيع تسليمك
`client.so` جاهزاً من هنا**، لكن `tools/build_dlls.py` يكتشف ذلك بصراحة بدل
أن يعطيك ملفاً مكسوراً. على جهازك بعد تثبيت الحزم أعلاه، يكتمل البناء.

---

## خطوات البناء الكاملة

```bash
# 0) مرة واحدة: الأدوات + اللعبة
sudo apt install build-essential gcc-multilib g++-multilib libgl1-mesa-dev

# 1) مصادر مثبّتة + دمج حقيقي
make fetch
make merge
make verify-sdk            # 9/9 ملفات تُترجم أمام هيدرات SDK الحقيقية

# 2) فحص جاهزية البيئة (لا يبني شيئاً)
make build-dlls-check
python3 tools/build_dlls.py --check | python3 -m json.tool

# 3) البناء (يعطيك تعليمات واضحة إن نقص شيء)
python3 tools/build_dlls.py \
    --vgui "/path/to/Half-Life/vgui.so" \
    --cfg release --jobs 8
```

`merge/projects.py` كان أضاف مسبقاً إلى `linux/Makefile.hl_cdll` و
`Makefile.hldll`: `sr_hud_timer.o`, `sr_hud_msg.o`, `sr_server.o`, `sr_core.o`،
وسكربت البناء يتحقق من وجودها قبل تشغيل `make`. كما يصلح إذن `gendbg.sh`
(أرشيف codeload لا يحفظ الـ exec bit) ويضع `vgui.so` في `linux/release/`.

### الناتج

```
dist/dlls/client.so       ← ELF 32-bit i386
dist/dlls/hl.so
dist/dlls/MANIFEST.json   ← sha256 + الحجم + تأكيد ELF32 لكل ملف
```

---

## التثبيت والتشغيل

```bash
python3 tools/build_dlls.py --vgui "/path/Half-Life/vgui.so" \
    --install "/path/Half-Life/gearbox"
```

السكربت ينسخ `client.so` إلى `gearbox/cl_dlls/` و`hl.so` إلى `gearbox/dlls/`
**ويحتفظ بنسخة `.orig` من ملفات اللعبة الأصلية** قبل الاستبدال، ثم ينسخ
`delta.lst`, `speedrun.cfg`, `splits/op4_route.json`.

تأكد أن `gearbox/liblist.gam` يحتوي (حسب دليل TWHL [2](https://twhl.info/wiki/page/Half-Life_Programming_-_Getting_Started)):

```text
game "BugfixedHL x OP4 Speedrun"
gamedll "dlls/hl.dll"
gamedll_linux "dlls/hl.so"
```

وشغّل:

```bash
hl_linux -game gearbox -console -dev +exec speedrun.cfg
```

ثم `F5` إعادة، `F6` تقسيم، `F7` تدريب. `sv_cheats` يبقى `0`.

### على Windows بدلاً من ذلك

افتح `build/merged-real/projects/vs2019/projects.sln` بـ VS2019+ وابنِ
`hl_cdll` و`hldll`؛ الناتج `client.dll` و`hl.dll` يوضعان في نفس المجلدين
[2](https://twhl.info/wiki/page/Half-Life_Programming_-_Getting_Started).

---

## استكشاف الأخطاء

| الرسالة | السبب / الحل |
| --- | --- |
| `cannot find Scrt1.o` / `skipping incompatible libstdc++.so` | ناقص `gcc-multilib g++-multilib` — ثبّت الحزم ثم أعد `--check` |
| `fatal error: bits/c++config.h: No such file or directory` | نفس السبب: هيدرات C++ الخاصة بـ i386 غير مثبّتة (`g++-multilib`) |
| `cannot find vgui.so` | انسخ `vgui.so` من جذر اللعبة إلى `linux/release/` أو مرّر `--vgui` |
| `./gendbg.sh: Permission denied` | السكربت يصلحها تلقائياً؛ أو `chmod +x linux/gendbg.sh` |
| `could not load library client.so` | غالباً بنيت 64-bit أو ينقصك `libstdc++6-i386`؛ افحص `ldd client.so` |
| `Host_InitError ... vgui.so: cannot open` | ضع `vgui.so` حيث يجدها المحرك (جذر Half-Life) وليس فقط وقت الربط |
| تعارضات في الشجرة | `make merge` يعطي 0 تعارضات؛ إن ظهر غير ذلك راجع [`RESOLUTION.md`](RESOLUTION.md) |

للتوزيع العام يُفضّل البناء داخل **Steam Runtime "scout"** حتى تعمل المكتبات
على أجهزة أخرى [2](https://twhl.info/wiki/page/Half-Life_Programming_-_Getting_Started).

---

## الرخص

`client.so` و`hl.so` مشتقان من كود OP4/Valve، فيخضعان لرخصها — لا تُرفع إلى
هذا المستودع ولا إلى حزمة `make package` (التي تحتوي كودنا فقط). راجع
[`LICENSES.md`](LICENSES.md) قبل أي توزيع. `vgui.so` وأصول اللعبة تبقى ملك
Valve/Gearbox وتُنسخ محلياً من نسختك المشروعة فقط.

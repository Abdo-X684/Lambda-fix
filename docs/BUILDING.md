# كيف أبني `client.so` — ومن أين أحمّل الأشياء؟

## ⛔ أولاً: لا تضع الملفات داخل `gearbox/`

إذا ظهرت لك الرسالة:

> *This mod has detected that it is being run from a Valve game directory which
> is not supported. Run this mod from its intended location. The game will now
> shut down.*

فالسبب أنك نسخت `client.so`/`hl.so` إلى **`gearbox/cl_dlls/`** و**`gearbox/dlls/`**
(كما قلتُ لك خطأً في إرشادات سابقة — هذا كان خطأي). SDK يحوي حاجزاً صريحاً
`UTIL_IsValveGameDirectory()` في `game_shared/filesystem_utils.cpp` يرفض أي
مجلد مود يبدأ بأحد البادئات:
`valve`, `gearbox`, `bshift`, `ricochet`, `dmc`, `cstrike`, `czero`, `dod`, `tfc`
(مطابقة بادئة، أي `gearbox_hd` مرفوض أيضاً). العميل يوقف اللعبة برسالة SDL
والسيرفر يطبعها في الكونسول.

**الحل:** مجلد مود مستقل اسمه `bhlop4` بجوار `valve/` و`gearbox/`، مع
`fallback_dir "gearbox"` كي تُقرأ أصول OP4 من مجلدها الرسمي دون تعديله.

```bash
python3 tools/create_mod.py --install "/path/to/Half-Life"
# ينشئ /path/to/Half-Life/bhlop4/{liblist.gam,steam_appid.txt,delta.lst,
#        cl_dlls/client.so,dlls/hl.so,speedrun.cfg,splits/,INSTALL.md}
hl_linux -game bhlop4 -console -dev +exec speedrun.cfg
```

أو حمّل الأرشيف الجاهز `bhl-op4-mod.zip`، فكّه داخل مجلد Half-Life، وشغّل
`-game bhlop4`. لا تلمس `gearbox/` أبداً: Steam يعيد ملفاته، والحاجز يرفضه أصلاً.

---

## ✅ جاهز للتحميل الآن

| الملف | الحجم | التحميل |
| --- | --- | --- |
| **`bhl-op4-mod.zip`** ⭐ | 9.3 MB | [**⬇ المود كامل**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/bhl-op4-mod.zip) · [من اللوحة](/dist/bhl-op4-mod.zip) |
| `client.so` | 9.0 MB | [**⬇ مباشر**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/client.so) · [من اللوحة](/dist/dlls/client.so) |
| `hl.so` | 15.9 MB | [**⬇ مباشر**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/hl.so) · [من اللوحة](/dist/dlls/hl.so) |
| `MANIFEST.json` | sha256 + ELF32 | [**⬇ مباشر**](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/download/v0.1.0-linux32/MANIFEST.json) |

صفحة الإصدار: [v0.1.0-linux32](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.1.0-linux32).
الثنائيات ELF 32-bit حقيقية، مبنية بـ Zig كمُصرّف i386 عابر (بلا `gcc-multilib`
وبلا `vgui.so` من اللعبة وقت الربط). **`vgui.so` الحقيقية وأصول اللعبة تبقى من
نسختك المشروعة**؛ المكتبة الوهمية استُخدمت للربط فقط لإنشاء `DT_NEEDED`، ولا تُوزّع.

---

## الجواب المختصر عن «من أين أحمّل client.so؟»

لا يوجد رابط «شرعي» لتحميله منفرداً: النسخة الأصلية تأتي مع لعبتك عند
`.../Half-Life/gearbox/cl_dlls/client.so`، ومهمتنا بناء نسخة بديلة من الشجرة
المدموجة (HUD السبيدرن + `SRSplit` + `sr_core`) داخل **مجلد المود**، لا فوقها
[1](https://deepwiki.com/twhl-community/halflife-op4-updated).

```bash
make fetch && make merge          # ① الشجرة المدموجة (828 ملف، 0 تعارضات)
make build-dlls-zig               # ② dist/dlls/{client.so,hl.so}
make mod                          # ③ dist/bhlop4/ + bhl-op4-mod.zip
```

---

## إذن ماذا أحمّل فعلاً؟

| تحتاجه | من أين | هل أحمّله يدوياً؟ |
| --- | --- | --- |
| مصادر OP4 / BugfixedHL / HLSDK | `make fetch` ينزّلها تلقائياً بـ commit + sha256 مثبّتين في `upstreams.json` | ❌ لا — مؤتمت بالكامل |
| **أداة البناء 32-bit** | `pip install ziglang` للطريقة السريعة، أو `sudo apt install build-essential gcc-multilib g++-multilib libgl1-mesa-dev` (GCC 9+) | ✅ نعم، من الـ repos |
| **أصول اللعبة** (`gearbox/`, الخرائط، الأصوات) | Steam: Half-Life (app 70) + Opposing Force (app 50) [2](https://steamcommunity.com/app/50/discussions/0/3103512736615438885/)؛ أو SteamCMD `+app_set_config 90 mod gearbox +app_update 90 validate` [1](https://steamcommunity.com/discussions/forum/13/810938082280349586/) | ✅ نعم — للتشغيل فقط |
| **`vgui.so`** | جذر تثبيت اللعبة `Half-Life/vgui.so` — **لا تُوزّع** [4](https://github.com/ranting-soberly/half-life-decay-linux-installer) | ✅ من لعبتك |
| `delta.lst`, `liblist.gam`, `steam_appid.txt`, `speedrun.cfg`, `splits/` | `make mod` يولّدها كلها (`data/delta.lst` من شبكة OP4 SDK) | ❌ مؤتمت |

> `fallback_dir "gearbox"` هو المفتاح: المود يقرأ أصول OP4 من مجلد Valve الرسمي
> دون أن يُشغَّل منه. لا يمكن سلسلة أكثر من fallback واحد، لكن `valve` يبقى
> الأساس الضمني للمحرك [1](https://twhl.info/wiki/page/liblist.gam).
> `steam_appid.txt = 50` يجعل Steam يركّب أصول Opposing Force للمود [2](https://steamcommunity.com/app/50/discussions/0/3103512736615438885/).

---

## لماذا 32 بالتحديد؟ 🔧

محرك GoldSrc على Linux **ELF 32-bit**، لذا `linux/Makefile` يستخدم
`g++ -m32` و`ARCH=i386`. أي `client.so` بـ 64-bit يُرفض بـ
`could not load library client.so` [4](https://github.com/ranting-soberly/half-life-decay-linux-installer).
في هذه الـ sandbox لا يوجد `gcc-multilib`، لذلك بنيتُ الملفين بـ Zig
(`x86-linux-gnu`) مع هيدر `GL/gl.h` مصغّر و`vgui.so` وهمي للربط فقط.

---

## خطوات البناء الكاملة (إن أردت إعادة الإنتاج)

```bash
python3 -m pip install ziglang
make fetch && make merge
make verify-sdk                  # 9/9 ملفات تُترجم أمام هيدرات SDK الحقيقية
make build-dlls-zig              # client.so + hl.so + MANIFEST.json
make mod                         # مجلد bhlop4 + الأرشيف
```

`merge/projects.py` أضاف مسبقاً `sr_hud_timer.o`, `sr_hud_msg.o`,
`sr_server.o`, `sr_core.o` إلى `Makefile.hl_cdll`/`Makefile.hldll`، وسكربت
البناء يتحقق من وجودها ويصلح إذن `gendbg.sh`. النواة تُبنى أيضاً بـ
`-fno-exceptions` (فحص دائم في `make verify`).

### التثبيت والتشغيل

```text
Half-Life/
├── valve/          ← لا تلمسه
├── gearbox/        ← لا تلمسه (الأصول تُقرأ منه عبر fallback_dir)
└── bhlop4/         ← هنا فقط
    ├── liblist.gam
    ├── steam_appid.txt   (50)
    ├── delta.lst
    ├── cl_dlls/client.so
    ├── dlls/hl.so
    ├── speedrun.cfg
    └── splits/op4_route.json
```

`liblist.gam` الجاهز:

```text
game "BugfixedHL x OP4 Speedrun"
type "singleplayer_only"
startmap "of0a0"
trainmap "ofboot0"
cldll "1"
gamedll "dlls\hl.dll"
gamedll_linux "dlls/hl.so"
fallback_dir "gearbox"
```

وشغّل `hl_linux -game bhlop4 -console -dev +exec speedrun.cfg`
(أو أضف `-game bhlop4` لخيارات التشغيل في Steam). `F5` إعادة، `F6` تقسيم،
`F7` تدريب. `sv_cheats` يبقى `0`. للمود على Windows: ابنِ
`projects/vs2019/projects.sln` بـ VS2019+ وضع `client.dll`/`hl.dll` في نفس
مجلد المود [2](https://twhl.info/wiki/page/Half-Life_Programming_-_Getting_Started).

---

## استكشاف الأخطاء

| الرسالة | السبب / الحل |
| --- | --- |
| **This mod has detected that it is being run from a Valve game directory…** | نسخت الملفات إلى `gearbox/` أو `valve/`؛ استخدم `bhlop4/` مع `fallback_dir "gearbox"` |
| `cannot find Scrt1.o` / `bits/c++config.h` | ناقص `gcc-multilib g++-multilib` — أو استخدم `make build-dlls-zig` |
| `cannot find vgui.so` | انسخ `vgui.so` من جذر اللعبة أو مرّر `--vgui` لـ `build_dlls.py` |
| `./gendbg.sh: Permission denied` | السكربت يصلحها تلقائياً؛ أو `chmod +x linux/gendbg.sh` |
| `could not load library client.so` | بنيت 64-bit أو ينقصك `libstdc++6-i386`؛ افحص `ldd client.so` |
| `Host_InitError ... vgui.so: cannot open` | ضع `vgui.so` في جذر Half-Life حيث يجدها المحرك |
| خرائط/موديلات OP4 مفقودة | تأكد من `fallback_dir "gearbox"` و`steam_appid.txt = 50` |

للتوزيع العام يُفضّل البناء داخل **Steam Runtime "scout"** [2](https://twhl.info/wiki/page/Half-Life_Programming_-_Getting_Started).

---

## الرخص

`client.so` و`hl.so` مشتقان من كود OP4/Valve، فيخضعان لرخصها؛ `data/delta.lst`
منقول من مجلد `network/` في SDK لأن كل مود يحتاجه. لا تُرفع ثنائيات Valve إلى
حزمة `make package` (كودنا فقط). راجع [`LICENSES.md`](LICENSES.md) قبل أي توزيع.

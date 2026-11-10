# إثبات البناء الحقيقي من شجرة `bhl-op4/` — الحالة النهائية

> **الحالة:** بُنِي `client.so` و`hl.so` فعلياً من الشجرة النهائية `bhl-op4/`،
> وكلتاهما `ELF32 / Intel 80386`، و**صفر** رمز غير مُحلول من بنائنا
> (`unresolved_own_build_symbols: []`). رموز الربط الإثني عشر أُغلقت بتطبيقات
> OP4 حقيقية موثّقة رمزاً برمز في
> [`../build-evidence/bhl-base/LINK_GAP_CLOSURE.md`](../build-evidence/bhl-base/LINK_GAP_CLOSURE.md).
>
> **لكن المكتبتين لم تُحمّلا داخل محرك Half-Life، ولم تُختبرا داخل Opposing Force.**
> السبب موثّق بأدلة قابلة لإعادة التشغيل في
> [`../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md`](../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md).
> **لا يُعلَن اكتمال المشروع.** التقرير الجامع:
> [`BHL_FINAL_AUDIT.md`](BHL_FINAL_AUDIT.md).
>
> لا علاقة لهذا البناء بـ `dist/dlls/*.so` أو `dist/bhl-op4-mod.zip` أو Release
> `v0.1.0-linux32`؛ تلك ملفات OP4-root قديمة لم تُلمس ولم تُقدَّم كنتيجة.

---

## 1. البيئة المطابقة لمتطلبات BugfixedHL

الشجرة `bhl-op4/` هي BugfixedHL-Rebased الأصلية (694 ملف BHL) وتتطلب
CMake ≥ 3.25، `nlohmann_json CONFIG`، `unofficial-pcre CONFIG` (PCRE1)،
Python 3.8..<4، Threads، SDL2، و`source_sdk`. المحرك 32-bit، والـ sandbox لا
يحتوي `g++ -m32` ولا libstdc++ 32-bit، فاستُخدم clang المرفق مع Zig موجهاً إلى
`i386-unknown-linux-gnu`.

```bash
python3 -m venv /tmp/zenv
/tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
/tmp/zenv/bin/cmake --version                                  # 3.30.9
/tmp/zenv/lib/python3.11/site-packages/ziglang/zig version   # 0.17.1
g++ --version | head -1                                       # 12.2.0 (تشخيص فقط)
cd /home/user/Bugfixhl-speedrun-op4
make fetch
#   .cache/upstreams/bugfixhl       = tmp64/BugfixedHL-Rebased @ 4d32095e3c33
#   .cache/upstreams/op4            = twhl-community/halflife-op4-updated @ 5368be7f8eba
#   .cache/upstreams/hl1_source_sdk = tmp64/hl1_source_sdk @ 11f26656677c881c7c630d03957900e7701da62e
```

| الحزمة | المصدر | sha256 |
|---|---|---|
| nlohmann/json v3.11.3 | `https://codeload.github.com/nlohmann/json/tar.gz/v3.11.3` | `0d8ef5af7f9794e3263480193c491549b2ba6cc74bb018906202ada498a79406` |
| PCRE1 (luvit/pcre mirror) | `https://codeload.github.com/luvit/pcre/tar.gz/master` | `5aa545145f0c5a584b54a34f04c2d61c01d31724d3fbae2ee20cd8e3c422594d` |

مكتبات الربط 32-bit من الشجرة/الـ SDK المثبّت:
`bhl-op4/lib/public/libSDL2-2.0.so.0`،
`.cache/upstreams/hl1_source_sdk/lib/public/{libtier0,libvstdlib,libsteam_api}.so`.

**لم يُنفَّذ `cmake` كاملاً**: `tools/build_bhl_base.py` يستنسخ قوائم
`SOURCE_FILES` (بما فيها الفروع الشرطية `if/elseif/else` و`list(APPEND)`)،
والتعريفات، والـ PCH، والمكتبات الثابتة من CMake الحقيقي، ثم يترجم بـ Zig-clang.
هذا قيد مُعلَن، وليس ادعاء configure كامل.

---

## 2. أوامر البناء الكاملة (كما نُفِّذت)

```bash
cd /home/user/Bugfixhl-speedrun-op4
export PYTHONDONTWRITEBYTECODE=1
python3 -m merge.bhl_base --out bhl-op4
python3 tools/build_bhl_base.py
python3 tools/verify_bhl_base.py --compile
python3 -m unittest tests.test_op4_link_fixups -v
make test-op4
make test-op4-fixups
python3 tools/probe_runtime_environment.py
make verify
```

الأدلة المولّدة في `build-evidence/bhl-base/`:

| ملف | المحتوى |
|---|---|
| `BUILD_COMMANDS.txt` | 454 أمر ترجمة/ربط فعلي |
| `SOURCES.sha256` | بصمة 459 ملف مصدر مُدخل |
| `compile-units.json` | 446 وحدة ترجمة، كلها `ok` |
| `build.log` | سجل الترجمة والربط الكامل |
| `UNDEFINED_SYMBOLS.txt` | `nm -u` الكامل للمكتبتين |
| `LINK_GAPS.md` | **فارغ من الرموز** (0 فجوة) |
| `LINK_GAP_CLOSURE.md` | جدول الرموز الإثني عشر: المصدر، سبب الغياب، التغيير، الدليل، الاختبار |
| `MANIFEST.json` | البصمات، ELF، التصديرات، `DT_NEEDED`، الفجوات |
| `patches/` | إصلاحات التوافق الثلاثة المعلَنة للبناء |
| `RUNTIME_ENVIRONMENT.{json,md}` | أدلة استحالة الاختبار داخل اللعبة |

لا توجد ملفات قديمة أو `failed/` أو ثنائيات من `dist/` داخل هذا الدليل،
ولا استبدال بعد البناء: بصمة كل ملف في `MANIFEST.json` تُطابق الملف على القرص
(مُختبَر آلياً).

---

## 3. سجل البناء (مقتطف كامل للمراحل)

```
=== bhl-op4 real 32-bit build ===
[deps] nlohmann: nlohmann-json-3.11.3.tar.gz sha256=0d8ef5af...a79406
[deps] pcre: pcre-master.tar.gz sha256=5aa54514...594d
[gen] appversion.h from bhl-op4/src/common/appversion.h.in
[gen] PCRE1 config.h / pcre.h from pcre.h.generic, config.h.generic
[compat] 3 build fixes written to build-evidence/bhl-base/patches
[cmake] client=139 server=179 common=8
[compile] client: 139/139 clean
[compile] server: 179/179 clean
[cmake] tier1=35 tier2=3 vgui_controls=68
[compile] tier1: 35/35 clean
[compile] tier2: 3/3 clean
[compile] vgui_controls: 68/68 clean
[compile] glad: 1/1 clean
[compile] semver: 1/1 clean
[compile] pcre: 20/20 clean
[ar] libvgui_controls.a: 68 objects
[ar] libtier2.a: 3 objects
[ar] libtier1.a: 35 objects
[ar] libglad.a / libsemver.a / libpcre.a
[link] client.so: 139 objects, 6 archives, 4 shared libs
[link] client.so: OK (27802960 bytes)
[link] hl.so: 179 objects, 1 archives, 0 shared libs
[link] hl.so: OK (21232512 bytes)
[audit] client.so: 0 unresolved symbols from our own build
[audit] hl.so: 0 unresolved symbols from our own build
[done] 26.7s
```

السجل الكامل: `../build-evidence/bhl-base/build.log`.

---

## 4. النتيجة النهائية

| الملف | الحجم (بايت) | sha256 | ELF | رموز مُصدَّرة | رموز undefined | نقاط دخول BHL | `DT_NEEDED` |
|---|---|---|---|---|---|---|---|
| `build-evidence/bhl-base/client.so` | 27,802,960 | `3cae1d779c5a2a2d47e138baa43a45bb06d870037dd6da995f581532d32d9100` | ELF32 / Intel 80386 | 4,941 | 311 | `Initialize`, `HUD_Init`, `HUD_VidInit`, `HUD_Redraw`, `HUD_UpdateClientData`, `HUD_Reset`, `HUD_Frame`, `HUD_Shutdown`, `HUD_Key_Event`, `V_CalcRefdef` | `libSDL2-2.0.so.0`, `libtier0.so`, `libvstdlib.so`, `libm.so.6`, `libc.so.6`, `ld-linux.so.2` |
| `build-evidence/bhl-base/hl.so` | 21,232,512 | `09550d9b2acc2f0fca05857d8d6eaf3112f1fcf32d0fd40a6404884463f46cf1` | ELF32 / Intel 80386 | 4,467 | 156 | `GetEntityAPI`, `GetEntityAPI2`, `GetNewDLLFunctions`, `GiveFnptrsToDll` | `libm.so.6`, `libc.so.6`, `ld-linux.so.2` |

الـ 311/157 undefined هي رموز يوفّرها المحرك/النظام (tier0/vstdlib، SDL2،
libc/libm، C++ ABI) ويوفّرها المحرك عند التحميل؛ ليست فجوات من بنائنا.
القائمة الكاملة في `UNDEFINED_SYMBOLS.txt`، والتصنيف في
`tools/build_bhl_base.py::is_engine_or_libc_symbol`.

---

## 5. الأخطاء التي ظهرت وكيف عولجت (بلا تجاوز شكلي ولا إخفاء)

| # | الخطأ | السبب | الإصلاح الحقيقي |
|---|---|---|---|
| 1 | `ctfplay_gamerules.h:102,106,108,110` — `override` لا يقابل virtual في BHL، و`bool` بدل `BOOL` | OP4-updated حدّث واجهة `CGameRules` | رقع مُعلَنة `bhl-ctf-nonvirtual-overrides` و`bhl-ctf-changeplayerteam-bools`؛ أُزيلت كلمة `override` فقط وعدّل نوع المعامل، الأجسام بقيت OP4 |
| 2 | `UTIL_FindEntitiesByClassname` غير موجود في BHL | BHL يعرض `UTIL_FindEntityByClassname` المفرد فقط | `op4_entity_enumerator.h` = `dlls/util.h:597-735` نصّاً، يستدعي primitive الخاص بـ BHL نفسه؛ لم تُغيَّر واجهة BHL |
| 3 | `CItemCTF.cpp:220` — `'CBasePlayer' does not refer to a value` | OP4 لديه `Instance<T>()` قالبي | رقعة `bhl-instance-template` تحوّلها إلى `static_cast<T*>(CBaseEntity::Instance(...))` |
| 4 | `gmsg*` غير مُعرّفة | `UserMessages.h` يعرّفها `inline` (COMDAT) مقابل تعريفات BHL القوية | رقعة `bhl-ctf-usermsg-extern` حوّلتها إلى `extern`؛ 13 رسالة OP4-only معرّفة في glue ومسجّلة من `GameDLLInit` |
| 5 | `GetLosingTeam(int&,int&)` فجوة ظهرت بعد وصل `CItemCTF.cpp` | الدالة كانت في `ctfplay_gamerules.cpp` غير الموصول | سابقاً جسم OP4 الحقيقي في glue؛ **الآن** `ctfplay_gamerules.cpp` نفسه موصول ويملك التعريف الوحيد |
| 6 | `op4_compat.h` يحوي تضمينات BHL، فلا يمكن تضمينه في اختبار مضيف | بنية الملف الأصلية | فُصل مُعدّد الكيانات إلى `op4_entity_enumerator.h` مستقل كي يُختبر تنفيذياً |
| 7 | `hl_baseentity.cpp:309` في عميل OP4 هو `return flTime;` | stub | **رُفض صراحةً**؛ استُخدمت خوارزمية `dlls/weapons.cpp:1069-1099` الحقيقية |

---

## 6. ما لم يُلمس / ما لم يُنجز

- `dist/dlls/client.so`، `dist/dlls/hl.so`، `dist/bhl-op4-mod.zip`،
  Release `v0.1.0-linux32`: لم تُلمس، بصماتها unchanged.
- لا PR إلى `main`، ولا تحديث Release، ولا ادعاء امتثال ترخيصي لتوزيع الثنائيات
  (GPL-3.0 مقابل ترخيص Valve غير التجاري).
- **لا اختبار داخل Opposing Force**، ولا تحميل داخل المحرك، ولا خريطة، ولا HUD،
  ولا أسلحة، ولا Monster/Rope/Grapple/CTF وقت تشغيل، ولا مراقبة أعطال.
  الأسباب والأدلة: `../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md`.
  - `dlls/ctf/ctfplay_gamerules.cpp` (قواعد CTF الفعلية) غير موصول؛
    و**25 ملف OP4** ما زالت `port-pending` (21 عميل + 4 خادم مستبعدة بأسباب
    معلَنة). التفاصيل في `BHL_FINAL_AUDIT.md` §7 و`LINK_GAP_CLOSURE.md`.

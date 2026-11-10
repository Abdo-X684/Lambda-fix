# نسخة ويندوز (DLL) — نفس شجرة `bhl-op4`

> ⚠️ **الجداول والبصمات أدناه تاريخية وتصف بناء MinGW/Zig السابق الذي انهار في `vgui2.dll`.**
> البنائيات الحالية في [`MANIFEST.json`](../build-evidence/bhl-windows/MANIFEST.json) مبنية بـ **MSVC 19.44 / Win32**، بنفس شجرة `bhl-op4` وبكل أسلحة OP4 العشرة و Client Prediction، لكنها **غير مُختبَرة داخل اللعبة هنا**.

أُضيفت نسخة **ويندوز 32‑بت** إلى جانب نسخة لينكس بدون حذف أو استبدال أي ملف من لينكس.
كل ما يخص لينكس (`build-evidence/bhl-base/`, `tools/build_bhl_base.py`, CI) باقٍ كما هو وبنفس البصمات.

## الناتج

| الملف | النوع | الحجم | sha256 |
| --- | --- | --- | --- |
| `build-evidence/bhl-windows/client.dll` | PE32 i386 | 14,618,112 B | `cd3e192283d011511c0deb77566cd4fb6bfc3336066a1bc4090bbecaaa3d5509` |
| `build-evidence/bhl-windows/hl.dll` | PE32 i386 | 13,909,504 B | `4e635472b6a11f90cbd6561d44cabcaf3be95542aaa8d74d17aa13db81157af7` |

- المُشغّل: `tools/build_bhl_windows.py` (Zig clang، `-target x86-windows-gnu`).
- قوائم مصادر BHL انتقائية **Windows** حسب `CMakeLists.txt`: عميل `139/139`، خادم `179/179`، كل وحدات SDK/التبعيات نظيفة، **صفر فجوة ربط**.
- `client.dll` يصدّر `101` رمزاً (منها `ClientFactory`, `CreateInterface`, `HUD_*`, `CL_CreateMove`…)، و`hl.dll` يصدّر `715` رمزاً؛ القوائم في `EXPORTS_client.txt` / `EXPORTS_hl.txt`.
- رموز أسلحة OP4 موجودة في كائنات العميل: 9 `EV_*` + `SetLocalBody` + `g_iClub` — [`OP4_SYMBOLS.txt`](../build-evidence/bhl-windows/OP4_SYMBOLS.txt).
- الاستيرادات: `tier0.dll`, `vstdlib.dll`, `dbghelp.dll`, `DINPUT8.dll`, `WS2_32.dll` و CRT/`KERNEL32`/`USER32` — [`IMPORTS.txt`](../build-evidence/bhl-windows/IMPORTS.txt).
- الأدلة الكاملة: [`MANIFEST.json`](../build-evidence/bhl-windows/MANIFEST.json), `BUILD_COMMANDS.txt`, `SOURCES.sha256`, `build.log`, `patches/` (فروق توافقية على نسخ **مؤقتة** من هيدرات SDK + مصادر ويندوز الخارجية، لا على الشجرة الأصلية).

## حدود الإثبات — بصراحة

- ✅ **إثبات:** ترجمة + ربط PE32 + مصادر + رموز + بصمات + تصدير/استيراد.
- ❌ **لا يوجد:** تشغيل على ويندوز، محرك GoldSrc، اختبار داخل اللعبة، إطلاق نار/إعادة تعبئة/ذخيرة/موديل/أنيميشن/صوت، أصول OP4 شرعية.
- ❌ **لا يُقال:** أي سلاح OP4 «كامل»، ولا اكتمال المشروع.
- نسخة ويندوز مبنية **cross-compile**؛ محمّل DLL والتبعيات (`SDL2.dll`, `tier0.dll`, `vstdlib.dll`, `steam_api.dll`) يوفّرها المحرك عند التشغيل فقط.

## لينكس لم يتغيّر

`client.so` = `3cae1d779c5a2a2d47e138baa43a45bb06d870037dd6da995f581532d32d9100`
`hl.so` = `09550d9b2acc2f0fca05857d8d6eaf3112f1fcf32d0fd40a6404884463f46cf1`
`make verify` + `30/30` اختبار + `verify_bhl_base.py --compile` ما زالت خضراء.

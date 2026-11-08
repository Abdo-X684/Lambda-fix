# جرد الاكتمال الشامل — COMPLETION INVENTORY

> الغرض من هذا الملف هو المرحلة الأولى من طلب الاكتمال: **جرد كامل لكل الوظائف
> والمصادر والاعتماديات**، بلا ادّعاء اكتمال. كل بند مصنّف: (أ) موصول ومُختبَر،
> (ب) منجز في هذه الجولة، (ج) مستبعد بسبب مثبت قانونياً، (د) غير قابل للإثبات
> في هذه البيئة. الأساس `BugfixedHL-Rebased`، والإضافات
> `halflife-op4-updated @ 5368be7f8eba`، والفرع
> `arena/dd30bd22-bugfixhl-speedrun-op4`.

**حكم صريح:** لم يُعلَن اكتمال BHL. قواعد CTF و`IsCTF()` صارت حقيقية وموصولة،
لكن عميل OP4 لا يزال غير مكتمل معمارياً ولا يوجد أي إثبات داخل اللعبة.
قائمة النواقص في §8 **ليست فارغة**، وهذا وحده يمنع ادّعاء الاكتمال.

---

## 1. الأساس BHL (ليس «نصف نقل»)

| البند | العدد | الدليل |
|---|---|---|
| ملفات BHL في `bhl-op4/` | 694 | `PROVENANCE.json` |
| مطابقة بايت-ببايت للـ commit المثبّت | 677 | `tests/test_bhl_base.py::test_07` |
| ملفات BHL عليها دمج مُعلَن بالاسم والسبب | 17 | `merge_rules` في `PROVENANCE.json` |
| مصادر خادم BHL تُترجم في البناء الفعلي | 179/179 | `build.log` (مع مصادر OP4) |
| مصادر عميل BHL تُترجم في البناء الفعلي | 139/139 | `build.log` |

**النتيجة:** كل وظائف BHL الأصلية موجودة كأساس، لا تُحذف ولا تُستبدل.
كل تغيير إضافة حقل/إعلان/تسجيل مُعلَن بالاسم في `PROVENANCE.json`.

**بند خارج الشجرة (مُسجَّل):** نواة السرعة `src/speedrun/` وتقرير
`tests/cpp/test_speedrun.cpp` تعود لمرحلة OP4-root المرفوضة، وليست داخل
`bhl-op4/`. عميل BHL يحوي `src/game/client/hud/timer.cpp` الخاص به.

---

## 2. ما أُنجز فعلاً في هذه الجولة (الخادم + CTF)

| البند | قبل | بعد | الدليل |
|---|---|---|---|
| `ctf/ctfplay_gamerules.cpp` | `port_pending`، 50 خطأ ترجمة | **موصول بـ CMake**، يُترجم نظيفاً | `src/game/server/CMakeLists.txt:195` |
| `CGameRules::IsCTF()` | `false` دائماً (لا قواعد CTF تُنشأ) | `CHalfLifeCTFplay::IsCTF()` الحقيقية تعيد `true`، والقواعد تُنشأ فعلاً | `ctfplay_gamerules.h:60` + `gamerules.cpp:325-360` |
| `InstallGameRules` | فروع BHL فقط | فرعا coop/CTF مُعلَنان (`op4-install-gamerules-decls/branch`) مع بقاء كل فروع BHL | `gamerules.cpp` |
| CTF globals / `SendFlagIcon*` / `DisplayTeamFlags` / `GetTeamName` / `GetLosingTeam` | منسوخة إلى glue | **التعريف الوحيد في الملف الحقيقي**؛ حذفت نسخ glue | `op4_link_fixups.cpp` + harness |
| قوائم CTF (`Player_Menu`, `ResetMenu`, `Menu_Team_Input`, `Menu_Char_Input`) | رموز ناقصة | أجسام OP4 الحقيقية من `player.cpp` في glue مُوسوم `op4_ctf_player.cpp` | `nm` + `test_07` |
| `respawn()` | رمز ناقص | جسم `client.cpp:152-166` الحقيقي | `op4_ctf_player.cpp` |
| cvars OP4 | 3 فقط | 9: أضيفت `mp_ctfplay`, `mp_ctf_autoteam`, `mp_ctf_capture`, `mp_coopplay`, `mp_defaultcoop`, `mp_coopweprespawn` | `OP4_RegisterGameDLLHooks()` |
| رسائل OP4 للمستخدم | `FlagIcon` فقط | 13 رسالة مسجّلة بأسماء/أحجام OP4 | `OP4_RegisterGameDLLHooks()` + harness |
| `gmsg*` في `UserMessages.h` | `inline` (COMDAT) | `extern` برقعة مُعلَنة، تعريف واحد قوي لكل رمز | `bhl-ctf-usermsg-extern` |
| واجهة `CGameRules` | لا `TeamsBalanced` / `GetNumTeams` / … | 5 virtuals مضافة **في نهاية** قائمة `CGameRules` حتى لا يتحرك أي slot قديم | `op4-gamerules-ctf-virtuals` |
| `apply_merges()` | فحص أول 40 حرفاً كان يُسقط القواعد المتأخرة صمتاً | فحص النص الكامل؛ القواعد 19–22 صارت تُطبَّق فعلاً | `merge/bhl_base.py` |

**لم تُستخدم أي دالة فارغة / stub / محاكاة.** الأجسام من الـ upstream المثبّت،
والتكيّف الوحيد ميكانيكي (`int` بدل `CTFTeam` في حقول الفريق،
`OP4_Normalized` بدل `Vector::Normalize`).

---

## 3. الخادم: مصادر OP4 (71 مصدر `.cpp`)

| الحالة | العدد | التفصيل |
|---|---|---|
| موصولة بـ `src/game/server/CMakeLists.txt` | 66 | 15 سلاحاً + CTF كاملاً + rope + NPC/كيانات + coop + glue |
| `port_pending` بسبب مثبت | 5 | انظر §3.1 |

### 3.1 المستبعدات الخمس — أسباب جذرية مثبتة

| الملف | الخطأ الجذري | التصنيف |
|---|---|---|
| `dlls/Wxdebug.cpp` | `#include <tchar.h>` غير موجود؛ الجسم كله داخل `#ifdef _DEBUG` ويستخدم Win32 registry | (ج) Windows-only، لا كود يُنتَج على Linux |
| `dlls/squeakgrenade.cpp` | `SQUEAK_UP/DOWN/IDLE1/...` غير معرّفة؛ يعرّف `CSqueak`/`CSqueakGrenade` الموجودين في BHL | (ج) تكرار نظام BHL |
| `dlls/world.cpp` | `g_pBodyQueueHead`, `CSave`/`CRestore` حديثة، `InstallGameRules(pWorld)`؛ يعرّف `CWorld` الموجود في BHL | (ج) تكرار؛ الـ singleton منقول نصّاً إلى glue |
| `dlls/ehandle.cpp` | يعيد تعريف `EHANDLE` الخاص بـ BHL | (ج) تكرار ABI |
| `dlls/UserMessages.cpp` | يعيد تعريف `LinkUserMessages()` الخاص بـ BHL | (ج) تكرار؛ رسائل OP4 سُجّلت من `GameDLLInit` بديلاً عنه |

**ليست «ملفات معلّقة بلا توثيق»**: كل واحد مذكور هنا بالاسم والسبب، وموجود
في الشجرة كمرجع، ومصنّف `port_pending` في `PROVENANCE.json`/`PORT_STATUS.json`.

### 3.2 تعارضات الربط التي حُلّت

وصل `ctfplay_gamerules.cpp` كما هو كان سيولّد 15 رمزاً مكرّراً قوياً
(`teamscores`, `team_names`, `g_szScoreIconNameBM/OF`,
`g_flFlagReturnTime`, `g_flBaseDefendDist`, `g_flDefendCarrierTime`,
`g_flCaptureAssistTime`, `g_flPowerupRespawnTime`, `g_iMapScoreMax`,
`GetTeamName`, `GetLosingTeam`, `SendFlagIcon`, `SendFlagIcons`,
`DisplayTeamFlags`). الحل كان **نقل ملكية التعريف** إلى الملف الحقيقي،
لا حذف الوظيفة ولا كتمان الرابط. `RGB_*`/`UnpackRGB` نُقلا إلى
`op4_compat.h` برقعة مُعلَنة، و`gmsgFlagIcon` بقي في glue لأنه الوحيد
المسجّل من `GameDLLInit`.

---

## 4. العميل: مصادر OP4 (21 مصدر `.cpp`) — العائق المعماري

مسبار ترجمة حقيقي بأعلام بناء العميل (`-DCLIENT_DLL` + `-include pch.h`):
**4 نظيفة / 17 متعثرة** — أُعيد تشغيله بعد آخر تعديل
(`/tmp/probe_client.py`، نتائج `/tmp/probe_client2.out`).

| الملف | السبب الجذري المُقاس | التصنيف |
|---|---|---|
| `com_weapons.cpp` | نظيف، لكن 19/26 رمزاً عاماً يطابق `client.so` (`HUD_GetWeaponAnim`, `UTIL_WeaponTimeBase`, `stub_PrecacheEvent` …) | (ج) تكرار نظام BHL |
| `events.cpp` | نظيف، 5/5 رموز عامة مكرّرة (`EV_HookEvents()`, `FloatBits`, `IsFinite` …) | (ج) تكرار |
| `util.cpp` | نظيف، 5/5 رموز مكرّرة (`LoadSprite`, `Vector2D::Vector2D` …) | (ج) تكرار |
| `particleman/IParticleMan_Active.cpp` | نظيف، لكن `IParticleMan_Active::*` و`CBaseParticle::*` موجودة أصلاً في `client.so` | (ج) تكرار |
| `death.cpp`, `hud_spectator.cpp`, `saytext.cpp`, `scoreboard.cpp`, `overview.cpp` | `fatal error: 'vgui_TeamFortressViewport.h' file not found` (VGUI1) | (ج) تعارض VGUI1/VGUI2 |
| `hud_flagicons.cpp` | `unknown type 'm_FlagIcons'`, `'FlagIcon'`, `'FlagTimer'`؛ `CHudFlagIcons : CHudBase` غير موجود | (ج) إطار HUD مختلف |
| `hud_playerbrowse.cpp` | `fatal error: 'ctf/CTFDefs.h' file not found` | (ج) مسار + إطار HUD |
| `ev_common.cpp` | `no member named 'm_Spectator' in 'CHud'`, `INSET_IN_EYE`, `VEC_VIEW` | (ج) `CHud` أُعيد كتابته في BHL |
| `ev_hldm.cpp` | `weapons/CEagle.h` غير موجود | (ج) تكرار `ev_hldm.cpp` في BHL |
| `hl/hl_events.cpp`, `hl/hl_objects.cpp` | `#include "../hud.h"` مسار نسبي خاطئ | (ج) بديل BHL `hl/hl_events.cpp` |
| `hl/hl_weapons.cpp` | `weapons/CGrapple.h` غير موجود | (ج) بديل BHL |
| `hl/hl_baseentity.cpp` | 51 خطأً: يعيد تعريف `CBaseEntity::*` العميل؛ ويحوي stub `return flTime;` **مرفوض صراحةً** | (ج) تكرار + stub مرفوض |
| `particleman/CBaseParticle.cpp` | `g_vecZero`, `Vector::Normalize`, `Vector`→`float*` | (ج) تكرار + توافق |
| `particleman/CFrustum.cpp` | `PlatformHeaders.h` غير موجود | (ج) تكرار + مسار |
| `particleman/CMiniMem.cpp` | `LengthSquared`, `Normalize`, `g_vecZero` | (ج) تكرار + توافق |
| `tri.cpp` | `DLLEXPORT` + `gHUD.m_Spectator` غير موجودين في BHL | (ج) بديل BHL `tri.cpp` |

**الدليل الحاسم على استحالة الوصل دون محاكاة:** BHL `src/game/client/hud.h:112`
يعرّف `CHud` من دون `CHudBase`، ومن دون `AddHudElem()`، ومن دون
`DECLARE_MESSAGE`/`HOOK_MESSAGE`، ويستخدم `vgui2::IScheme`
و`CRainbow`. OP4 `cl_dll/hud.cpp:737` يعرّف `CHud::AddHudElem(CHudBase*)`
و`cl_dll/hud.h:500` يعرّف `CHudFlagIcons : CHudBase`. هذه ليست هيدرات ناقصة؛
إنها **إطارا HUD مختلفان**. وصل ملفات OP4 يستلزم إعادة كتابتها على إطار BHL،
وهو بالضبط «استبدال دوال حقيقية بمحاكاة» الممنوع صراحةً، أو حذف نظام BHL،
وهو ممنوع صراحةً أيضاً. لذلك صُنّفت (ج) بالدليل، لا (أ).

**ما لم يحدث:** لم تُحذف أي ميزة BHL، ولم يُكتب مهايئ VGUI1 مزيّف، ولم
يُوصل أي ملف عميل OP4 ادّعاءً بالاكتمال. الملفات الـ21 موجودة في الشجرة
كمرجع ومصنّفة `port_pending`.

---

## 5. الأنظمة الوظيفية المطلوبة

| النظام | الحالة | المتبقي |
|---|---|---|
| أسلحة OP4 (15) | موصولة، ELF32، 0 فجوة ربط | إثبات داخل اللعبة (د) |
| وحوش/ذكاء اصطناعي OP4 | 22+ ملف موصول، `IsFacing` و`GibData` حقيقيان | إثبات داخل اللعبة (د) |
| Rope / Grapple | `CRope*`, `CElectrifiedWire`, `CGrapple*`, `CGrappleTip` موصولة | إثبات داخل اللعبة (د) |
| CTF | **القواعد موصولة وحقيقية**، `IsCTF()` فعّالة، 13 رسالة و9 cvars مسجّلة، 0 فجوة | HUD عميل OP4 (ج) + إثبات داخل اللعبة (د) |
| Coop | `coopplay_gamerules.cpp` موصول ويُنشأ من `InstallGameRules` | إثبات داخل اللعبة (د) |
| قائمة الفريق / اختيار الشخصية | أجسام OP4 الحقيقية موصولة ومسجّلة | عرضها يعتمد على رسائل `VGUIMenu` في عميل BHL (د) |
| عميل OP4 | 0 موصول | معمارياً متعذر دون استبدال BHL (ج) |
| خادم OP4 | 66 موصول + 10 glue، 0 فجوة | إثبات داخل اللعبة (د) |

---

## 6. الاعتماديات / ABI / بيئة التشغيل

| البند | الحالة |
|---|---|
| المحرك `hl_linux` / `hw.so` / `vgui.so` | غير موجود |
| أصول OP4 الشرعية (`.bsp`, `.mdl`, `pak0.pak`) | غير موجودة |
| محمّل ELF32 ديناميكي `/lib/ld-linux.so.2` | غير موجود |
| `libSDL2-2.0.so.0`, `libtier0.so`, `libvstdlib.so` 32-bit | غير موجودة |
| تنفيذ static musl ELF32 | `ELF32-RUN-OK` (يُثبت أن العائق المحمّل لا المعالج) |
| `cmake` كامل | لم يُنفَّذ؛ استنساخ أمين لقوائم/تعريفات CMake مع Zig-clang i386 |
| امتثال ترخيصي للتوزيع | غير مدّعى (GPL-3.0 مقابل ترخيص Valve غير التجاري) |

**الحكم:** المرحلة السابعة (اختبار داخل محرك Opposing Force) والمرحلة الثامنة
(اختبار الأنظمة داخل اللعبة) **غير قابلتين للتنفيذ في هذا الـ sandbox**. كل
ميزة تُسجَّل «غير مثبتة وقت التشغيل» ولا يُعلَن اكتمالها. الاختبارات التنفيذية
المتاحة هي اختبارات كود على الأجسام الحقيقية المستخرجة نصّاً من الشجرة،
وهي **بديل غير كافٍ** ولا تُقدَّم كإثبات لعبة.

---

## 7. خطة التنفيذ بالمراحل (بعد هذه الجولة)

1. ✅ الجرد الشامل (هذا الملف).
2. ❌ **وصل مصادر العميل** — متعذر معمارياً؛ مُوثَّق بالدليل في §4، لم يُكتمل.
3. ✅ وصل `ctfplay_gamerules.cpp` + تفعيل coop/CTF في `InstallGameRules`.
4. ✅ تسجيل رسائل/cvars OP4، قوائم CTF، `respawn`، `IsFacing`، `GibData`.
5. ✅ حل تعارضات الربط: `unresolved_own_build_symbols: []` للثنائيتين.
6. ✅ بناء كامل نظيف من الشجرة النهائية + إعادة كل الاختبارات بعد آخر تعديل.
7. ❌ اختبار داخل المحرك — مستحيل، يُسجَّل كغير مثبت.
8. ❌ اختبار الأنظمة داخل اللعبة — مستحيل، يُسجَّل كغير مثبت.

---

## 8. قائمة النواقص (يجب أن تكون فارغة قبل إعلان الاكتمال)

| # | الناقص | التصنيف |
|---|---|---|
| 1 | 21 مصدر عميل OP4 غير موصولة (تعارض VGUI1/VGUI2 + تكرار `CHud`/رموز) | (ج) |
| 2 | 5 مصادر خادم OP4 غير موصولة (تكرار أنظمة BHL / Windows-only) | (ج) |
| 3 | لا `client.so`/`hl.so` مُختبران داخل محرك GoldSrc حقيقي | (د) |
| 4 | لا اختبار أسلحة/وحوش/AI/Rope/Grapple/CTF داخل اللعبة | (د) |
| 5 | لا إثبات vtables/typeinfo وقت التشغيل ولا تحميل `vgui.so` | (د) |
| 6 | لا أصول OP4 شرعية ولا محمّل ELF32 ديناميكي في البيئة | (د) |
| 7 | `cmake` كامل غير مُنفَّذ (استُنسخت قوائمه بأمانة) | (د) |
| 8 | لا ادّعاء امتثال ترخيصي لتوزيع الثنائيات | (د) |

**القائمة غير فارغة ⇒ لا يُعلَن اكتمال BHL.**

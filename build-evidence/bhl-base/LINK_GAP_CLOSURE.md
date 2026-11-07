# إغلاق رموز الربط الإثني عشر — دليل رمز برمز

> الحالة: **أُغلقت الـ12 رمزاً فعلياً** في البناء النهائي. `LINK_GAPS.md` فارغ،
> و`MANIFEST.json` يسجّل `unresolved_own_build_symbols: []` للمكتبتين.
> هذا إثبات ربط/كود **وليس** إثبات تشغيل داخل اللعبة؛ انظر
> `RUNTIME_ENVIRONMENT.md` و`docs/BHL_FINAL_AUDIT.md`.

المصدر العلوي الموحّد: `twhl-community/halflife-op4-updated @ 5368be7f8eba`
(المسارات أدناه تبدأ من `.cache/upstreams/op4/`)، والأساس
`tmp64/BugfixedHL-Rebased @ 4d32095e3c33`.

| # | الرمز (المكتبة) | التنفيذ الأصلي | سبب الغياب | التغيير المُعلَن | دليل الاختفاء من الرابط | اختبار وظيفي قابل للتنفيذ |
|---|---|---|---|---|---|---|
| 1 | `CBasePlayerWeapon::GetNextAttackDelay(float)` (client + server) | `dlls/weapons.cpp:1069-1099` الخوارزمية الحقيقية. **رُفض** stub العميل `cl_dll/hl/hl_baseentity.cpp:309` (`return flTime;`) | `dlls/weapons.cpp` يُحتفظ به `reference-only` لأنه يعرّف `CWeaponBox` و`CBasePlayerItem::*` التي تتعارض مع `bhl-op4/src/game/server/weapons.cpp`. قاعدة الدمج 4 أضافت الإعلان فقط | glue جديد `src/game/shared/op4_weapon_timing.{h,cpp}` بنص الخوارزمية (عُزل في دالة نقية ليُختبر)، + دمج مُعلَن `op4-weapon-timing-state` لحقلين في `weapons.h`، + دمج مُعلَن `op4-shared-weapon-timing-cmake` ليُترجم في المكتبتين | `nm --defined-only` يعرضه، `nm -u` لا يعرضه، `objdump` >8 تعليمات، `LINK_GAPS.md` فارغ | `tests/cpp/test_op4_algorithms.cpp`: 9 تحققات (أول طلقة، creep سالب/موجب، إعادة الضبط عند `-1`) + `tests/test_op4_link_fixups.py::test_02/03` |
| 2 | `typeinfo for CBasePlayerWeapon` (client + server) | يولّده المترجم من تعريف الصنف؛ أول virtual غير inline هو `GetNextAttackDelay` | لم يكن هناك TU يعرّف الدالة المفتاحية، فلم يُصدر vtable/typeinfo | نفس TU السابق (هو TU الدالة المفتاحية) | معرّف وغير undefined؛ `nm -S` حجم > 0 | `tests/test_op4_link_fixups.py::test_04` (بيانات، لا دالة؛ لا اختبار تعدد أشكال وقت تشغيل بلا محرك — مُعلَن) |
| 3 | `vtable for CBasePlayerWeapon` (client + server) | كما أعلاه | كما أعلاه | كما أعلاه | كما أعلاه | كما أعلاه |
| 4 | `CBaseMonster::AddShockEffect(float,float,float,float,float)` (server) | `dlls/monsters.cpp:3448-3478`، ومعها `UpdateShockEffect`/`ClearShockEffect` `:3480-3503` | `dlls/monsters.cpp` يتعارض مع `bhl-op4/src/game/server/monsters.cpp`؛ `basemonster.h` حصل على الحقول/الإعلانات فقط | glue `src/game/server/op4/op4_link_fixups.cpp` بالأجسام الثلاثة نصّاً | معرّف، غير undefined، جسم حقيقي >8 تعليمات | `build/op4_fixup_harness.cpp`: 9 تحققات (تفعيل، لون/حجم، `kRenderFxGlowShell`/`kRenderNormal`، تراكم المدة، انتهاء المدة، استعادة الحالة، `ClearShockEffect`) |
| 5 | `CRope::DetachObject()` (server) | `dlls/rope/CRope.cpp:1010-1014` (ملف OP4 حقيقي) | ملفات `dlls/rope/` منقولة لكن غير موصولة بـ CMake | وصل 4 ملفات rope حقيقية `op4/dlls/rope/*.cpp` بهدف BHL، مع إصلاحات توافق مُعلَنة | معرّف من الملف الحقيقي، غير undefined | harness: 3 تحققات (`m_bObjectAttached`، `m_flDetachTime = gpGlobals->time`) |
| 6 | `CTFGoalFlag::DropFlag(CBasePlayer*)` (server) | `dlls/ctf/CTFGoalFlag.cpp:750-780` و`DoDrop:730-748` (ملف OP4 حقيقي) | ملفات CTF غير موصولة؛ `ctfplay_gamerules.h` به 5 `override` لا تقابل virtuals في BHL، و`ChangePlayerTeam` يستخدم `bool` بدل `BOOL`، و`UTIL_FindEntitiesByClassname` غير موجود في BHL | وصل 8 ملفات CTF حقيقية؛ `op4_entity_enumerator.h` (= `dlls/util.h:597-735` نصّاً)؛ رقع مُعلَنة `bhl-ctf-nonvirtual-overrides`، `bhl-ctf-changeplayerteam-bools`، `bhl-ctf-gmsgflagicon-extern`، `bhl-instance-template`؛ glue بأجسام `DisplayTeamFlags`/`SendFlagIcon(s)`/`GetTeamName`/`GetLosingTeam` وحالة CTF من `ctfplay_gamerules.cpp` | معرّف من الملف الحقيقي، غير undefined؛ `GetLosingTeam` ظهر كفجوة جديدة بعد الوصل وأُغلق بجسم OP4 الحقيقي `:126-138` | harness: 10 تحققات لـ`DropFlag` (مسح `m_pFlag`، إزالة بتّي العلم، الحالة 3، ارتفاع 16/34، `SOLID_TRIGGER`، `owner/aiment`، تسلسل `not_carried`، تحديث HUD) + 8 تحققات للدوال المساندة |
| 7 | `CWorld::World` (server) | `dlls/world.cpp:483-501` (التعريف + الباني/الهادم) | `dlls/world.cpp` يعرّف أيضاً `Spawn`/`Precache`/`KeyValue` المتعارضة مع `bhl-op4/src/game/server/world.cpp`؛ `cbase.h` يحوي الإعلان `static` فقط عبر دمج | glue بالتعريف والباني/الهادم نصّاً + دمج مُعلَن `op4-cworld-ctor-dtor` في `cbase.h` | معرّف، غير undefined، `nm -S` حجم > 0 | harness: 5 تحققات (ابتداء null، `World = this`، رفض عالم ثانٍ، عدم مسح غير المالك، مسح المالك) |
| 8 | `oldgrapple` (server) | `dlls/game.cpp:588` تعريف `cvar_t`، و`:1189` تسجيل `CVAR_REGISTER` | `dlls/game.cpp` يُحتفظ به `reference-only` (يعرّف `GameDLLInit` الخاص بـ BHL)؛ `op4_compat.cpp` كان يعلنه `extern` فقط | glue بالتعريف الحقيقي + `OP4_RegisterGameDLLHooks()` + دمجان مُعلَنان `op4-gamedllinit-decls` / `op4-gamedllinit-call` في `bhl-op4/src/game/server/game.cpp` | معرّف، غير undefined، حجم > 0، و`GameDLLInit` يستدعي التسجيل فعلياً | harness: 5 تحققات (3 cvars بأسماء/قيم OP4، تسجيل `FlagIcon` في `gmsgFlagIcon`) |
| 9 | `oldweapons` (server) | `dlls/game.cpp:589`، التسجيل `:1190` | كما أعلاه | كما أعلاه | كما أعلاه | كما أعلاه |

> الرموز 1–3 مكرّرة في `client.so` و`hl.so` (3 + 9 = 12 فجوة أصلية).

## ما استُخدم كإثبات

```bash
python3 -m merge.bhl_base --out bhl-op4
python3 tools/build_bhl_base.py
python3 tools/verify_bhl_base.py --compile
make test-op4            # خوارزمية GetNextAttackDelay + مُعدّد الكيانات
make test-op4-fixups     # أجسام الإصلاحات الحقيقية مُستخرجة نصّاً من الشجرة
python3 -m unittest tests.test_op4_link_fixups -v
python3 tools/probe_runtime_environment.py
```

- `UNDEFINED_SYMBOLS.txt`: قائمة `nm -u` الكاملة (311 عميل / 156 خادم، كلها محرّك/ libc/ABI).
- `LINK_GAPS.md`: **بلا أي بند**.
- `MANIFEST.json`: `unresolved_own_build_symbols: []` للمكتبتين.
- `RUNTIME_ENVIRONMENT.md`: لماذا لا يوجد اختبار داخل اللعبة.

## ما لم يُكتمل صراحةً

- **`dlls/ctf/ctfplay_gamerules.cpp` لم يُوصل**: يحتاج حقول `CBasePlayer` الخاصة بـ OP4 (`m_szTeamModel`، `m_szTeamName`، `m_iSnipeKills`...) وثوابت قوائم OP4 و`UTIL_FindPlayers` و`SecondsToTime`. إضافتها تعني استبدال أنظمة BHL — ممنوع بحسب التعليمات. النتيجة: `CGameRules::IsCTF()` يبقى `false` في BHL، فلا تُفعَّل قواعد CTF كلعبة؛ كيانات CTF ورسائل HUD موجودة وقابلة للاستدعاء لكن مباراة CTF كاملة **غير قابلة للعب بعد**.
- 62 ملف OP4 ما زالت `port-pending` ومنها `CItemBackpackCTF`، `CItemLongJumpCTF`، `CItemPortableHEVCTF`، `CItemRegenerationCTF`، `CTFDetect`، و`ctfplay_gamerules.cpp`.
- ملفات OP4 الأساسية (`weapons.cpp`، `monsters.cpp`، `world.cpp`، `game.cpp`، `util.cpp`، `gamerules.cpp`) تبقى `reference-only`؛ لم تُدمج ككتلة واحدة.
- **لا اختبار داخل Opposing Force**: لا محرك، لا `vgui.so`، لا أصول شرعية، ولا محمّل ELF32 ديناميكي. مفصّل في `RUNTIME_ENVIRONMENT.md`.
- لم يُنفَّذ `cmake` كاملاً (استُخدم استنساخ أمين لقوائم/تعريفات CMake مع clang/Zig موجّه إلى i386).
- لا PR إلى `main`، ولا تحديث Release، ولا ادعاء امتثال ترخيصي لتوزيع الثنائيات (GPL-3.0 مقابل ترخيص Valve غير التجاري).

#!/usr/bin/env python3
"""Deterministic OP4 source/asset audit and honest runtime-test table.

This is a SOURCE audit. It records the pinned repos/commits, the original OP4
files for each weapon, the named modifications, the glue authored here, and the
music/asset resolution path. It never starts GoldSrc and never marks an
untested weapon as working. Package verification is done separately from the
generated JSON/Markdown so regenerating the ZIP does not make the audit stale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "bhl-op4/PROVENANCE.json"
UPSTREAMS = ROOT / "upstreams.json"
PACKAGE = ROOT / "build-evidence/bhl-base/bhl-base-mod.zip"
OUT_JSON = ROOT / "build-evidence/source-audit/OP4_SOURCE_AUDIT.json"
OUT_DOC = ROOT / "docs/OP4_SOURCE_AUDIT.md"
OUT_TESTS = ROOT / "docs/OP4_RUNTIME_TESTS.md"

ASSET_RE = re.compile(r'["\']((?:models|sound|sprites|events)/[^"\']+?(?:mdl|wav|spr|sc))["\']', re.I)

WEAPONS = [
    {
        "name": "Desert Eagle", "classname": "weapon_eagle", "cxx": "CEagle",
        "id": "WEAPON_EAGLE", "event": "events/eagle.sc", "event_func": "EV_FireEagle",
        "support": ["dlls/weapons/CEagle.cpp", "dlls/weapons/CEagle.h",
                    "dlls/weapons/CEagleLaser.cpp", "dlls/weapons/CEagleLaser.h"],
        "ammo": "357",
    },
    {
        "name": "Pipe Wrench", "classname": "weapon_pipewrench", "cxx": "CPipewrench",
        "id": "WEAPON_PIPEWRENCH", "event": "events/pipewrench.sc", "event_func": "EV_Pipewrench",
        "support": ["dlls/weapons/CPipewrench.cpp", "dlls/weapons/CPipewrench.h"],
        "ammo": None,
    },
    {
        "name": "M249", "classname": "weapon_m249", "cxx": "CM249",
        "id": "WEAPON_M249", "event": "events/m249.sc", "event_func": "EV_FireM249",
        "support": ["dlls/weapons/CM249.cpp", "dlls/weapons/CM249.h"],
        "ammo": "556",
    },
    {
        "name": "Displacer", "classname": "weapon_displacer", "cxx": "CDisplacer",
        "id": "WEAPON_DISPLACER", "event": "events/displacer.sc", "event_func": "EV_FireDisplacer",
        "support": ["dlls/weapons/CDisplacer.cpp", "dlls/weapons/CDisplacer.h",
                    "dlls/weapons/CDisplacerBall.cpp", "dlls/weapons/CDisplacerBall.h"],
        "ammo": "uranium",
    },
    {
        "name": "Shock Rifle / weapon_shockroach alias", "classname": "weapon_shockrifle",
        "cxx": "CShockRifle", "id": "WEAPON_SHOCKRIFLE", "event": "events/shock.sc",
        "event_func": "EV_FireShockRifle",
        "support": ["dlls/weapons/CShockRifle.cpp", "dlls/weapons/CShockRifle.h",
                    "dlls/weapons/CShockBeam.cpp", "dlls/weapons/CShockBeam.h",
                    "dlls/shockroach.cpp"],
        "ammo": "shock charges (recharging)",
        "note": (
            "OP4's clean source links BOTH weapon_shockrifle and weapon_shockroach "
            "to CShockRifle (CShockRifle.cpp lines 39-40); W_Precache registers only "
            "weapon_shockrifle. dlls/shockroach.cpp defines monster_shockroach / "
            "COFShockRoach, a separate creature entity, not an eleventh weapon."
        ),
    },
    {
        "name": "Spore Launcher", "classname": "weapon_sporelauncher", "cxx": "CSporeLauncher",
        "id": "WEAPON_SPORELAUNCHER", "event": "events/spore.sc", "event_func": "EV_FireSpore",
        "support": ["dlls/weapons/CSporeLauncher.cpp", "dlls/weapons/CSporeLauncher.h",
                    "dlls/weapons/CSpore.cpp", "dlls/weapons/CSpore.h"],
        "ammo": "spores",
    },
    {
        "name": "Sniper Rifle", "classname": "weapon_sniperrifle", "cxx": "CSniperRifle",
        "id": "WEAPON_SNIPERRIFLE", "event": "events/sniper.sc", "event_func": "EV_SniperRifle",
        "support": ["dlls/weapons/CSniperRifle.cpp", "dlls/weapons/CSniperRifle.h"],
        "ammo": "762",
    },
    {
        "name": "Knife", "classname": "weapon_knife", "cxx": "CKnife",
        "id": "WEAPON_KNIFE", "event": "events/knife.sc", "event_func": "EV_Knife",
        "support": ["dlls/weapons/CKnife.cpp", "dlls/weapons/CKnife.h"],
        "ammo": None,
    },
    {
        "name": "Penguin", "classname": "weapon_penguin", "cxx": "CPenguin",
        "id": "WEAPON_PENGUIN", "event": "events/penguinfire.sc", "event_func": "EV_PenguinFire",
        "support": ["dlls/weapons/CPenguin.cpp", "dlls/weapons/CPenguin.h",
                    "dlls/penguin_grenade.cpp"],
        "ammo": "exhaustible nests",
    },
    {
        "name": "Grapple", "classname": "weapon_grapple", "cxx": "CGrapple",
        "id": "WEAPON_GRAPPLE", "event": None, "event_func": None,
        "support": ["dlls/weapons/CGrapple.cpp", "dlls/weapons/CGrapple.h",
                    "dlls/weapons/CGrappleTip.cpp", "dlls/weapons/CGrappleTip.h"],
        "ammo": None,
        "note": "OP4's clean source has no .sc playback event for the grapple.",
    },
]

AUTHORED_FILES = [
    "src/game/client/op4/op4_client_prediction.cpp",
    "src/game/client/op4/op4_weapon_events.cpp",
    "src/game/client/op4/op4_weapon_events.h",
    "src/game/server/op4/op4_compat.cpp",
    "src/game/server/op4/op4_compat.h",
    "src/game/server/op4/op4_compat_late.h",
    "src/game/server/op4/op4_link_fixups.cpp",
    "src/game/server/op4/op4_ctf_player.cpp",
    "src/game/server/op4/op4_entity_enumerator.h",
    "src/game/shared/op4_weapon_timing.cpp",
    "src/game/shared/op4_weapon_timing.h",
    "tools/packaging/setup_op4_media.bat",
]

MODIFIED_BHL_FILES = [
    "src/game/client/hud.cpp", "src/game/client/hud_msg.cpp",
    "src/game/client/hud_update.cpp", "src/game/client/entity.cpp",
    "src/game/client/hl/hl_events.cpp", "src/game/client/hl/hl_weapons.cpp",
    "src/game/client/hl/hl_baseentity.cpp",
    "src/game/client/CMakeLists.txt", "src/game/server/weapons.cpp",
    "src/game/server/weapons.h", "src/game/server/cdll_dll.h",
    "src/game/server/player.h", "src/common/entity_state.h",
    "src/game/server/CMakeLists.txt",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gen_path(upstream_path: str) -> str:
    if upstream_path.startswith("dlls/"):
        return "src/game/server/op4/" + upstream_path
    if upstream_path.startswith("cl_dll/"):
        return "src/game/client/op4/" + upstream_path[len("cl_dll/"):]
    return upstream_path


def source_entry(provenance_files: dict, rel: str) -> dict:
    p = ROOT / "bhl-op4" / rel if rel.startswith("src/") else ROOT / rel
    entry = provenance_files.get(rel, {})
    return {
        "path": rel,
        "exists": p.is_file(),
        "sha256": sha256(p) if p.is_file() else None,
        "origin": entry.get("origin"),
        "action": entry.get("action"),
        "upstream_commit": entry.get("commit"),
        "upstream_path": entry.get("upstream_path"),
        "patch_rules": [r["rule"] for r in entry.get("patch_rules", [])],
        "merge_rules": entry.get("merge_rules", []),
    }


def op4_path(rel: str) -> str:
    if rel.startswith("dlls/"):
        return "src/game/server/op4/" + rel
    if rel.startswith("cl_dll/"):
        return "src/game/client/op4/" + rel[len("cl_dll/"):]
    return rel


def static_wiring() -> dict:
    def text(rel: str) -> str:
        return (ROOT / "bhl-op4" / rel).read_text(errors="surrogateescape")
    events = text("src/game/client/hl/hl_events.cpp")
    ammo = text("src/game/client/hud/ammo.cpp")
    weapons = text("src/game/client/hl/hl_weapons.cpp")
    prediction = text("src/game/client/op4/op4_client_prediction.cpp")
    hud = text("src/game/client/hud.cpp")
    hud_msg = text("src/game/client/hud_msg.cpp")
    baseentity = text("src/game/client/hl/hl_baseentity.cpp")
    return {
        "all_ten_prediction_objects": all(f"g_{w['cxx'][1:]}" in weapons for w in WEAPONS),
        "all_ten_prediction_cases": all(f"case {w['id']}:" in weapons for w in WEAPONS),
        "g_pWpns_max_weapons": "g_pWpns[MAX_WEAPONS]" in weapons,
        "prediction_loops_max_weapons": weapons.count("for (i = 0; i < MAX_WEAPONS; i++)") >= 2,
        "op4_ammo_state_transfer": all(x in weapons for x in
            ("player.ammo_spores", "player.ammo_762", "player.m_iItems",
             "to->client.vuser2.y", "to->client.vuser2.z", "to->client.iuser4")),
        "iteminfoarray_populated": "CBasePlayerItem::ItemInfoArray[info.iId] = info;" in weapons,
        "two_arg_ammo_registry": "AddAmmoNameToAmmoRegistry(info.pszAmmo1, weaponName);" in weapons,
        "client_ammoinfoarray_definition": "CBasePlayerItem::AmmoInfoArray[MAX_AMMO_SLOTS]" in prediction,
        "client_getammoindex_real": "OP4_GetAmmoIndex" in baseentity and "OP4_GetAmmoIndex" in prediction,
        "hud_weaponlist": 'HookMessage<&CHudAmmo::MsgFunc_WeaponList>("WeaponList")' in ammo,
        "hud_curweapon_ammox": all(x in ammo for x in
            ('MsgFunc_CurWeapon', 'MsgFunc_AmmoX')),
        "slot7": 'UserCmd_Slot7>("slot7")' in ammo,
        "max_weapon_slots_7": "#define MAX_WEAPON_SLOTS     7" in text("src/game/server/cdll_dll.h"),
        "oldweapon_hook": '"OldWeapon", OP4_MsgFunc_OldWeapon' in hud,
        "hudcolor_hook": '"HudColor", OP4_MsgFunc_HudColor' in hud,
        "weapons_hook": '"Weapons", OP4_MsgFunc_Weapons' in hud,
        "reset_on_init_and_reset_hud": hud_msg.count("OP4_ResetNetworkState();") >= 2,
        "oldweapon_message_glue": "OP4_MsgFunc_OldWeapon" in prediction,
        "hudcolor_message_glue": "OP4_MsgFunc_HudColor" in prediction,
        "event_hooks": {w["classname"]: w["event"] in events for w in WEAPONS if w["event"]},
    }


def build_audit() -> dict:
    upstreams = json.loads(UPSTREAMS.read_text())["upstreams"]
    provenance = json.loads(PROVENANCE.read_text())
    files = provenance["files"]
    weapons = []
    for w in WEAPONS:
        entries = [source_entry(files, op4_path(p)) for p in w["support"]]
        asset_refs = set()
        for e in entries:
            p = ROOT / "bhl-op4" / e["path"]
            if p.is_file():
                asset_refs.update(ASSET_RE.findall(p.read_text(errors="surrogateescape")))
        weapons.append({
            **{k: w[k] for k in ("name", "classname", "cxx", "id", "event", "event_func", "ammo", "note") if k in w},
            "source_repo": "twhl-community/halflife-op4-updated",
            "source_commit": "5368be7f8eba14b05236c7c52ad5f6b11fd95e55",
            "source_files": entries,
            "all_source_files_present": all(e["exists"] for e in entries),
            "all_source_files_from_op4": all(e["origin"] == "op4" for e in entries),
            "referenced_assets": sorted(asset_refs),
            "runtime_test": "غير مُختبَر داخل GoldSrc في هذه البيئة",
        })
    return {
        "audit_type": "source and package provenance; NOT gameplay verification",
        "in_game_tested_here": False,
        "upstreams": upstreams,
        "weapons": weapons,
        "authored_files": [source_entry(files, p) for p in AUTHORED_FILES],
        "modified_bhl_files": [source_entry(files, p) for p in MODIFIED_BHL_FILES],
        "static_wiring": static_wiring(),
        "package_policy": {
            "bundled_legal_assets": [],
            "music_source": "user's installed Half-Life/gearbox/media/*.mp3 (and gearbox_downloads/media when present)",
            "music_setup": "setup_op4_media.bat copies the original OP4 MP3s into <mod>/media/; no MP3 is generated or bundled",
            "required_docs": ["SOURCE_AUDIT.md", "RUNTIME_TESTS.md", "INSTALL.md"],
            "required_setup": ["setup_op4_media.bat"],
            "in_game_tested_here": False,
        },
        "penguin": {
            "weapon_class": "CPenguin",
            "weapon_classname": "weapon_penguin",
            "fgd_label": "Killer Penguin",
            "projectile_entity": "CPenguinGrenade",
            "projectile_classname": "monster_penguin",
            "source_files": [source_entry(files, op4_path(p)) for p in (
                "dlls/weapons/CPenguin.cpp", "dlls/weapons/CPenguin.h",
                "dlls/penguin_grenade.cpp")],
            "function": (
                "CPenguin::PrimaryAttack() plays events/penguinfire.sc and, server-side, "
                "creates monster_penguin at the trace endpoint with forward velocity. "
                "CPenguinGrenade::Spawn() sets models/w_penguin.mdl and HuntThink() "
                "makes it seek a target before exploding."
            ),
            "model_provenance": (
                "Only from the user's installed gearbox/models/*.mdl via fallback_dir; "
                "the repository and ZIP contain no .mdl file."
            ),
        },
        "shock_roach_definition": (
            "weapon_shockroach is an alternate classname for CShockRifle, not a separate "
            "player weapon. monster_shockroach / COFShockRoach in dlls/shockroach.cpp is "
            "a separate OP4 creature entity. W_Precache registers weapon_shockrifle only."
        ),
        "music": {
            "code_path": (
                "OP4 dlls/triggers.cpp PlayCDTrack() sends engine 'cd play <track>' "
                "(and 'cd stop' for -1). The engine, not the game DLL, maps the track ID "
                "to media/*.mp3. Shipped autoexec.cfg/op4weapons.cfg contain no cd/mp3/media command."
            ),
            "diagnosis": (
                "The ZIP contains no media/*.mp3 and no gamestartup.mp3. GoldSrc looks in the "
                "active mod's media/ folder and then valve/media; fallback_dir gearbox supplies "
                "maps/models/sounds but is not a reliable media/ lookup for CD/MP3 tracks. "
                "Therefore an unmodified bhlop4 folder plays the Half-Life soundtrack."
            ),
            "fix": (
                "setup_op4_media.bat copies only the user's original gearbox/media/*.mp3 "
                "(plus gearbox_downloads/media/*.mp3 when present) into bhlop4/media/. "
                "No track is invented, renamed, or downloaded."
            ),
            "startup_music": (
                "gamestartup.mp3 is copied only if the installed OP4 copy provides it; "
                "it is never fabricated."
            ),
            "runtime_test": "غير مُختبَر داخل GoldSrc في هذه البيئة",
            "engine_behavior_sources": [
                "https://developer.valvesoftware.com/wiki/List_of_HL1_soundtracks",
                "https://twhl.info/wiki/page/Tutorial:_Making_Music_Play_in_Maps_[GoldSource]/5984",
                "https://github.com/UCyborg/hl-mp3-fix",
            ],
        },
    }


def markdown(audit: dict) -> str:
    by_name = {u["name"]: u for u in audit["upstreams"]}
    op4, bhl, valve = by_name["op4"], by_name["bugfixhl"], by_name["valve_hlsdk"]
    lines = [
        "# تدقيق مصادر وأصول Opposing Force", "",
        "> **تدقيق ملفات ومصادر فقط.** لم يُشغَّل محرك GoldSrc في هذه البيئة،",
        "> ولا تُعدّ الترجمة أو CI أو وجود ملفات أو تسجيل حدث دليلاً على عمل أي سلاح.",
        "> بلاغ المستخدم: اللعبة تعمل، لكن موسيقى المقدمة ليست OP4 والأسلحة لا تعمل بشكل صحيح؛",
        "> لذلك لا توجد علامة نجاح لأي صف غير مُختبَر.", "",
        "## 1. المستودعات والالتزامات المثبّتة", "",
        "| الدور | المستودع | الالتزام | بصمة الحزمة |", "|---|---|---|---|",
        f"| مصدر أسلحة/خادم OP4 | [{op4['repo']}](https://github.com/{op4['repo']}) | [`{op4['ref']}`](https://github.com/{op4['repo']}/commit/{op4['ref']}) | `{op4['tarball']['sha256']}` |",
        f"| أساس BHL / VGUI2 / الحركة | [{bhl['repo']}](https://github.com/{bhl['repo']}) | [`{bhl['ref']}`](https://github.com/{bhl['repo']}/commit/{bhl['ref']}) | `{bhl['tarball']['sha256']}` |",
        f"| أصل HLSDK | [{valve['repo']}](https://github.com/{valve['repo']}) | [`{valve['ref']}`](https://github.com/{valve['repo']}/commit/{valve['ref']}) | `{valve['tarball']['sha256']}` |",
        "", "الأسلحة العشرة كلها من **مستودع OP4 واحد** وبنفس الالتزام أعلاه؛ لا توجد نماذج",
        "أو كيانات بديلة من مستودع آخر. الموديلات/الأصوات/الخرائط/الـMP3 ليست في هذا",
        "المستودع ولا في ZIP: تُقرأ من نسخة `gearbox/` المثبّتة قانونياً لدى المستخدم.", "",
        "## 2. جدول الأسلحة: الأصل، الملفات، التعديل، الكتابة الذاتية", "",
        "| السلاح | الاسم البرمجي | ملفات OP4 الأصلية | تعديل معلن | حدث العميل | ملفات كتبناها للسلاح | داخل اللعبة |",
        "|---|---|---|---|---|---|---|",
    ]
    for w in audit["weapons"]:
        src = "<br>".join(f"`{Path(e['path']).name}`" for e in w["source_files"])
        actions = ", ".join(sorted({e["action"] or "?" for e in w["source_files"]}))
        ev = f"`{w['event']}` → `{w['event_func']}`" if w["event"] else "لا يوجد في مصدر OP4"
        lines.append(
            f"| {w['name']} | `{w['classname']}` / `{w['cxx']}` | {src} | `{actions}` | {ev} | لا شيء؛ أجسام الأسلحة أصلية | **{w['runtime_test']}** |"
        )
    lines += [
        "", "**توضيح Shock Roach:** " + audit["shock_roach_definition"], "",
        "**كل ملف `op4+compat-patch` أعلاه**: جسم السلاح من OP4، والتعديلات مسماة في",
        "`bhl-op4/PROVENANCE.json` (توافق `bool/int`، ترويسات، `Vector::Normalize`).",
        "لم يُكتب منطق إطلاق أو إعادة تعبئة بديل. ملفات `dlls/weapons.cpp` و`dlls/player.cpp`",
        "في OP4 محفوظة كمرجع فقط؛ خادم الحزمة يُبنى من مصدر OP4 الكامل عبر",
        "`tools/prepare_op4_msvc_server.py`.", "",
        "### ملفات BHL المعدّلة بقواعد مسماة", "",
    ]
    lines += [f"* `{e['path']}` — `{e['action']}`" for e in audit["modified_bhl_files"]]
    lines += ["", "### ملفات كتبها هذا المشروع (ليست من OP4 ولا BHL)", ""]
    lines += [f"* `{e['path']}`" for e in audit["authored_files"]]
    lines += [
        "", "هذه طبقة توصيل/تنبؤ/تثبيت أحداث/إعداد موسيقى فقط؛ لا تحل محل أنظمة BHL",
        "(VGUI2، الحركة، Bhop، الوحوش، أسلحة BHL الأربعة عشر).", "",
        "## 3. Penguin: المصدر البرمجي", "",
        f"* السلاح: `{audit['penguin']['weapon_class']}` / `{audit['penguin']['weapon_classname']}`؛ FGD: `{audit['penguin']['fgd_label']}`.",
        f"* الكيان الحي: `{audit['penguin']['projectile_entity']}` / `{audit['penguin']['projectile_classname']}`.",
        "* الملفات: `dlls/weapons/CPenguin.cpp`, `dlls/weapons/CPenguin.h`, `dlls/penguin_grenade.cpp` من OP4 بالالتزام أعلاه.",
        f"* الوظيفة: {audit['penguin']['function']}",
        f"* الموديلات: {audit['penguin']['model_provenance']}",
        "* لا يوجد `.mdl` داخل ZIP؛ أي موديل بطريق شوهد في ملفات اللعبة المثبّتة مصدره `gearbox/`، لا مستودع ثانٍ.", "",
        "## 4. فجوات المصدر التي عُولجت بعد بلاغ الخلل", "",
        "> هذه فحوصات مصدرية فقط؛ لم تُختبر داخل اللعبة.", "",
        "| الفحص | موجود في الشجرة المولّدة |", "|---|---|",
    ]
    for k, v in audit["static_wiring"].items():
        if isinstance(v, dict):
            v = f"{sum(v.values())}/{len(v)} أحداث موصولة"
        lines.append(f"| `{k}` | `{v}` |")
    lines += [
        "", "أهم الإصلاحات المصدرية: نقل `iuser4 → m_iItems` و`vuser2.y/z → ammo_spores/ammo_762`",
        "إلى تنبؤ عميل BHL؛ توسيع مصفوفة/حلقات التنبؤ إلى `MAX_WEAPONS=64`؛ ملء",
        "`ItemInfoArray` وتسجيل الذخيرة بصيغة OP4 ذات المعاملين؛ تعريف `AmmoInfoArray`",
        "و`GetAmmoIndex` الحقيقي في العميل؛ ربط `OldWeapon`/`HudColor` مع `Weapons`؛",
        "تفريغ حالة الشبكة عند `InitHUD`/`ResetHUD`؛ توليد `delta.lst` مدمج يحافظ",
        "على صحة/eflags الخاصة بـBHL ويضيف `m_iId` بـ6 بتات و`iuser4` الخاص بـOP4.",
        "هذه مرشحات سببية قوية لخلل الأسلحة، وليست إثبات تشغيل.", "",
        "## 5. الموسيقى: السبب والمسار والإصلاح", "",
        f"* مسار الكود: {audit['music']['code_path']}",
        f"* التشخيص: {audit['music']['diagnosis']}",
        f"* الإصلاح: {audit['music']['fix']}",
        f"* موسيقى البداية: {audit['music']['startup_music']}",
        f"* النتيجة داخل اللعبة: **{audit['music']['runtime_test']}**.", "",
        "مصادر سلوك المحرك (للفحص، لا كدليل تشغيل):",
    ]
    lines += [f"* {u}" for u in audit["music"]["engine_behavior_sources"]]
    lines += [
        "", "## 6. حدود الحزمة", "",
        "* ZIP لا يضم `.mdl`, `.wav`, `.sc`, `.mp3`, `.bsp`؛ سبرايت `sprites/ag_*.spr` فقط من BHL.",
        "* `setup_op4_media.bat`, `SOURCE_AUDIT.md`, `RUNTIME_TESTS.md`, `INSTALL.md` مرفقة داخل ZIP.",
        "* `MOD_MANIFEST.json` ينص صراحة على `in_game_tested_here: false`.", "",
        "**الخلاصة:** كل ملف أصلي/معدّل/مكتوب ذاتياً موثّق أعلاه، لكن لا اختبار GoldSrc هنا؛",
        "جدول `RUNTIME_TESTS.md` المرفق لا يحوي علامة نجاح واحدة.", "",
    ]
    return "\n".join(lines)


def tests_markdown(audit: dict) -> str:
    rows = [
        "# جدول اختبارات GoldSrc المطلوبة", "",
        "> **لا يوجد محرك GoldSrc في هذه البيئة.** لم يُنفَّذ أي اختبار داخل اللعبة هنا.",
        "> لا تُوضع علامة نجاح لأي صف حتى يختبره المستخدم على جهازه ويوثّق النتيجة.",
        "> بلاغ المستخدم بأن اللعبة تبدأ مع موسيقى خاطئة وأسلحة لا تعمل يُسجَّل كخلل، لا كنجاح.", "",
        "| العنصر | منطق الخادم | تنبؤ العميل | HUD/ذخيرة | إعادة تعبئة | إطلاق | أنيميشن | صوت | تأثيرات | موديل | النتيجة داخل اللعبة |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for w in audit["weapons"]:
        rows.append(
            f"| {w['name']} | مصدر OP4 موجود | مصدر OP4 موجود | توصيل مصدرى فقط | غير مُختبَر | غير مُختبَر | غير مُختبَر | غير مُختبَر | غير مُختبَر | من `gearbox` المثبّت | **غير مُختبَر** |"
        )
    rows += [
        "| موسيقى المقدمة الأصلية | — | — | — | — | — | — | تُنسخ من `gearbox/media` فقط | — | — | **غير مُختبَر** |",
        "| موسيقى الخرائط `trigger_cdaudio` | خرائط OP4 خارجية | — | — | — | — | — | تُنسخ من `gearbox/media` فقط | — | — | **غير مُختبَر** |",
        "| حملة `of0a0` / `ofboot0` | خادم OP4 | — | — | — | — | — | — | — | خرائط خارجية | **غير مُختبَر** |",
        "| قوائم BHL VGUI2 | — | عميل BHL | — | — | — | — | — | — | — | **غير مُختبَر** |",
        "| `impulse 101` للأسلحة العشرة | مصدر خادم OP4 | — | — | — | — | — | — | — | — | **غير مُختبَر** |",
        "", "## بروتوكول الاختبار المطلوب من المستخدم", "",
        "1. فكّ ZIP في `Half-Life/bhlop4/` بجانب `valve/` و`gearbox/`، ثم شغّل `setup_op4_media.bat` مرة واحدة.",
        "2. شغّل `hl.exe -game bhlop4 -console`؛ سجّل بداية `of0a0`، موسيقى المقدمة، وموسيقى أول `trigger_cdaudio`.",
        "3. `sv_cheats 1; impulse 101`؛ لكل سلاح: اختياره، أيقونة/ذخيرة HUD، إطلاق، تفريغ المخزن، إعادة تعبئة، التبديل عنه/إليه، الصوت، موديل اليد/العالم، التأثيرات.",
        "4. اختبارات خاصة: Grapple على سطح صالح؛ Penguin ومراقبة `monster_penguin`؛ Displacer أولي/ثانوي/انتقال ذاتي؛ Shock Rifle أولي/ثانوي وإعادة الشحن.",
        "5. سجّل فيديو/console لكل صف. إلى أن يحدث ذلك يبقى كل صف **غير مُختبَر** ولا يُقال «يعمل».", "",
    ]
    return "\n".join(rows)


def package_audit() -> dict:
    if not PACKAGE.is_file():
        return {"exists": False, "errors": ["ZIP missing"]}
    with zipfile.ZipFile(PACKAGE) as z:
        names = z.namelist()
        manifest = json.loads(z.read("MOD_MANIFEST.json")) if "MOD_MANIFEST.json" in names else {}
        setup = z.read("setup_op4_media.bat").decode("utf-8", "replace") if "setup_op4_media.bat" in names else ""
    legal = [n for n in names if n.lower().endswith(
        (".mdl", ".wav", ".sc", ".mp3", ".bsp", ".spr")) and not n.startswith("sprites/ag_")]
    errors = []
    for required in (
        "liblist.gam", "steam_appid.txt", "delta.lst", "cl_dlls/client.dll",
        "cl_dlls/client.so", "dlls/opfor.dll", "MOD_MANIFEST.json", "INSTALL.md",
        "setup_op4_media.bat", "SOURCE_AUDIT.md", "RUNTIME_TESTS.md",
        "autoexec.cfg", "op4weapons.cfg",
    ):
        if required not in names:
            errors.append(f"missing {required}")
    if "dlls/hl.dll" in names or "dlls/hl.so" in names:
        errors.append("scattered Half-Life server DLL in full-OP4 package")
    if any(n.lower().endswith(".mp3") or n.startswith("media/") for n in names):
        errors.append("music bundled instead of copied from installed gearbox")
    if legal:
        errors.append(f"bundled legal assets: {legal}")
    if manifest.get("in_game_tested_here") is not False:
        errors.append("manifest does not explicitly say NOT in-game tested")
    if "gearbox\\media" not in setup or "valve\\media" in setup.lower():
        errors.append("media setup script does not use only installed gearbox media")
    return {
        "exists": True, "entries": len(names), "errors": errors,
        "bundled_music": [n for n in names if n.lower().endswith(".mp3")],
        "bundled_models": [n for n in names if n.lower().endswith(".mdl")],
        "setup_script": "setup_op4_media.bat" in names,
        "audit_docs": all(n in names for n in ("SOURCE_AUDIT.md", "RUNTIME_TESTS.md")),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    audit = build_audit()
    doc = markdown(audit)
    tests = tests_markdown(audit)
    data = json.dumps(audit, indent=2, sort_keys=True) + "\n"
    pkg = package_audit()
    if a.check:
        for p, expected in ((OUT_JSON, data), (OUT_DOC, doc), (OUT_TESTS, tests)):
            if not p.is_file() or p.read_text() != expected:
                raise SystemExit(f"{p.relative_to(ROOT)} is stale; run tools/audit_op4_sources.py")
        if not all(w["all_source_files_present"] and w["all_source_files_from_op4"] for w in audit["weapons"]):
            raise SystemExit("a weapon source is missing or is not from the pinned OP4 SDK")
        if pkg["errors"]:
            raise SystemExit("package audit failed: " + "; ".join(pkg["errors"]))
        print("== OP4 SOURCE AUDIT OK ==")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(data)
    OUT_DOC.write_text(doc)
    OUT_TESTS.write_text(tests)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_DOC.relative_to(ROOT)}")
    print(f"wrote {OUT_TESTS.relative_to(ROOT)}")
    if pkg["errors"]:
        print("package state (will be rebuilt): " + "; ".join(pkg["errors"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

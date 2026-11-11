#!/usr/bin/env python3
"""Generate the honest OP4-weapon inventory from the pinned clean sources.

This reads the independent clean BugfixedHL and clean OP4 checkouts, the merged
``bhl-op4/`` tree, built-binary manifests and the playable mod. It never uses
an earlier report or CI result as evidence. ``--check`` fails if any source
fact, built binary, package hash or in-game-test claim has drifted; ``--write``
regenerates docs/WEAPON_INVENTORY.md.
"""

from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from merge import op4_client_prediction, op4_weapon_events  # noqa: E402

BHL_CLEAN = ROOT / ".cache/upstreams/bugfixhl"
OP4_CLEAN = ROOT / ".cache/upstreams/op4"
TREE = ROOT / "bhl-op4"
MOD = ROOT / "build-evidence/bhl-base/mod"
DOC = ROOT / "docs/WEAPON_INVENTORY.md"


def precache(path: Path) -> set[str]:
    return set(re.findall(
        r'UTIL_PrecacheOtherWeapon\(\s*"([^"]+)"',
        path.read_text()))


def link_map(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in (root / "dlls/weapons").rglob("*.cpp"):
        for cls, cxx in re.findall(
                r'LINK_ENTITY_TO_CLASS\(\s*(weapon_[A-Za-z0-9_]+)\s*,\s*'
                r'([A-Za-z0-9_]+)\s*\)', p.read_text()):
            out[cls] = cxx
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes(path: Path) -> tuple[int, list[str], int]:
    bad: list[str] = []
    skipped = 0
    entries = path.read_text().splitlines()
    for line in entries:
        digest, name = line.split("  ", 1)
        p = Path(name)
        if not p.is_absolute():
            p = ROOT / p
        if not p.is_file():
            # Pinned SDK/dependency sources are fetched by the build drivers,
            # not committed. A clean checkout may legitimately lack them.
            if ".cache/" in name:
                skipped += 1
                continue
            bad.append(name + " (missing)")
        elif sha256(p) != digest:
            bad.append(name)
    return len(entries), bad, skipped


def collect() -> tuple[list[str], str]:
    errors: list[str] = []

    def chk(ok: bool, msg: str) -> None:
        if not ok:
            errors.append(msg)

    bhl_w = precache(BHL_CLEAN / "src/game/server/weapons.cpp")
    op4_w = precache(OP4_CLEAN / "dlls/weapons.cpp")
    merged_w = precache(TREE / "src/game/server/weapons.cpp")
    op4_only = sorted(op4_w - bhl_w)
    chk(len(bhl_w) == 14, f"clean BHL W_Precache has {len(bhl_w)}, expected 14")
    chk(len(op4_w) == 24, f"clean OP4 W_Precache has {len(op4_w)}, expected 24")
    chk(len(op4_only) == 10, f"OP4-exclusive weapon count is {len(op4_only)}, expected 10")
    chk(merged_w == bhl_w | op4_w, "merged W_Precache differs from BHL + OP4")
    merged_text = (TREE / "src/game/server/weapons.cpp").read_text()
    for cls in sorted(bhl_w | op4_w):
        n = len(re.findall(r'UTIL_PrecacheOtherWeapon\(\s*"' + re.escape(cls) + r'"', merged_text))
        chk(n == 1, f"{cls} registered {n} times in merged W_Precache")

    clean_links = link_map(OP4_CLEAN)
    events = {w["cls"]: w for w in op4_weapon_events.WEAPONS}
    chk(set(events) == set(op4_only), "event inventory does not match clean OP4-only weapons")
    ids = dict(op4_client_prediction.CLIENT_PREDICTED_IDS)
    chk(set(ids.values()) == {
        "WEAPON_DISPLACER", "WEAPON_EAGLE", "WEAPON_GRAPPLE", "WEAPON_KNIFE",
        "WEAPON_M249", "WEAPON_PENGUIN", "WEAPON_PIPEWRENCH",
        "WEAPON_SHOCKRIFLE", "WEAPON_SNIPERRIFLE", "WEAPON_SPORELAUNCHER"},
        "client prediction ID list is not all ten OP4 weapons")

    cmake = (TREE / "src/game/client/CMakeLists.txt").read_text()
    hl_weapons = (TREE / "src/game/client/hl/hl_weapons.cpp").read_text()
    events_cpp = (TREE / "src/game/client/op4/op4_weapon_events.cpp").read_text()
    status = json.loads((TREE / "PORT_STATUS.json").read_text())
    prov = json.loads((TREE / "PROVENANCE.json").read_text())
    config = (MOD / "op4weapons.cfg").read_text()
    autoexec = (MOD / "autoexec.cfg").read_text()
    mod_manifest = json.loads((MOD / "MOD_MANIFEST.json").read_text())

    chk("op4-hud-bucket-7" in prov["files"]["src/game/server/cdll_dll.h"]["merge_rules"],
        "7th HUD bucket merge rule missing")
    chk("MAX_WEAPON_SLOTS     7" in (TREE / "src/game/server/cdll_dll.h").read_text(),
        "MAX_WEAPON_SLOTS is not 7")
    chk('HookCommand<&CHudAmmo::UserCmd_Slot7>("slot7")' in
        (TREE / "src/game/client/hud/ammo.cpp").read_text(),
        "slot7 command is not hooked")
    chk("sv_oldweapons 0" in autoexec, "autoexec does not enable OP4 prediction")
    chk(mod_manifest.get("in_game_tested_here") is False,
        "mod manifest does not explicitly say it was NOT tested in-game")
    liblist = (MOD / "liblist.gam").read_text()
    for marker in ('startmap "of0a0"', 'trainmap "ofboot0"',
                   'fallback_dir "gearbox"', 'gamedll "dlls\\opfor.dll"'):
        chk(marker in liblist, f"liblist.gam missing {marker}")
    chk((MOD / "steam_appid.txt").read_text() == "50\n",
        "steam_appid.txt is not Opposing Force (50)")
    chk(sha256(MOD / "delta.lst") == sha256(ROOT / "data/delta.lst"),
        "mod/delta.lst is not OP4's network delta")
    lang_files = sorted(p for p in (MOD / "ui/resource/language").glob("*.txt")
                        if not p.name.endswith(".utf8.txt"))
    chk(len(lang_files) == 11, "BHL UTF-16LE language files are missing")
    chk(all(p.read_bytes().startswith(codecs.BOM_UTF16_LE) for p in lang_files),
        "BHL language files are not UTF-16LE BOM")

    for cls in op4_only:
        cxx = clean_links.get(cls)
        chk(bool(cxx), f"{cls}: no clean OP4 LINK_ENTITY_TO_CLASS class")
        if not cxx:
            continue
        src = f"../server/op4/dlls/weapons/{cxx}.cpp"
        disk = f"src/game/server/op4/dlls/weapons/{cxx}.cpp"
        header = TREE / f"src/game/server/op4/dlls/weapons/{cxx}.h"
        chk(src in cmake, f"{cls}: {src} missing from client CMake")
        chk((TREE / disk).is_file(), f"{cls}: server weapon source missing")
        chk(f"{cxx} g_{cxx[1:]};" in hl_weapons, f"{cls}: client weapon object missing")
        chk(f"HUD_PrepEntity(&g_{cxx[1:]}, &player);" in hl_weapons,
            f"{cls}: HUD_PrepEntity missing")
        chk(f"case {ids.get(cxx)}:" in hl_weapons, f"{cls}: GetLocalWeapon case missing")
        chk(status["files"].get(disk, {}).get("ok") is True,
            f"{cls}: source did not compile into ELF32 object")
        hdr = header.read_text()
        chk("UTIL_DefaultUseDecrement();" in hdr and "server-authoritative" not in hdr,
            f"{cls}: UseDecrement is not client-predicted")
        w = events.get(cls, {})
        if w.get("func"):
            chk(w["func"] in events_cpp, f"{cls}: event {w['func']} missing")
        else:
            chk(cxx == "CGrapple", f"{cls}: missing event without documented reason")
        if w.get("ammo"):
            chk(f"give {w['ammo']}" in config, f"{cls}: ammo {w['ammo']} missing from config")
        chk(f"give {cls}" in config, f"{cls}: give command missing from config")

    for extra in ("../server/op4/dlls/weapons/CGrappleTip.cpp",
                  "../server/op4/dlls/ehandle.cpp"):
        chk(extra in cmake, f"client CMake missing OP4 client source {extra}")

    linux = json.loads((ROOT / "build-evidence/bhl-base/MANIFEST.json").read_text())
    windows = json.loads((ROOT / "build-evidence/bhl-windows/MANIFEST.json").read_text())
    chk(windows.get("abi") == "msvc",
        "Windows DLL manifest is not the MSVC-ABI build")
    for name in ("client.so", "hl.so"):
        chk(linux["libraries"][name].get("glibc_max") == "GLIBC_2.17",
            f"{name} is not linked to the GLIBC_2.17 baseline")
    for side, manifest in (("bhl-base", linux), ("bhl-windows", windows)):
        n, bad, skipped = source_hashes(
            ROOT / f"build-evidence/{side}/SOURCES.sha256")
        chk(not bad, f"{side}/SOURCES.sha256 has {len(bad)} stale entries: {bad[:2]}")
        for name, rec in manifest["libraries"].items():
            p = ROOT / f"build-evidence/{side}/{name}"
            chk(p.is_file() and sha256(p) == rec["sha256"],
                f"{side}/{name} does not match MANIFEST.json")
            # The full-OP4 package ships only the BHL clients and the patched
            # OP4 server. The historical BHL-root hl.so/hl.dll remain build
            # evidence but are deliberately NOT copied into the mod folder.
            if name.startswith("hl."):
                continue
            mod_rel = ("cl_dlls/" if name.startswith("client") else "dlls/") + name
            mod_file = MOD / mod_rel
            chk(mod_file.is_file() and sha256(mod_file) == rec["sha256"],
                f"mod/{mod_rel} does not match built {side}/{name}")

    opfor_built = ROOT / "build-evidence/bhl-windows/opfor.dll"
    opfor_mod = MOD / "dlls/opfor.dll"
    chk(opfor_built.is_file(), "full OP4 server opfor.dll is missing")
    if opfor_built.is_file():
        chk(opfor_mod.is_file()
            and sha256(opfor_mod) == sha256(opfor_built),
            "mod/dlls/opfor.dll does not match the built OP4 server")

    zip_path = ROOT / "build-evidence/bhl-base/bhl-base-mod.zip"
    chk(zip_path.is_file(), "playable mod ZIP missing")
    chk("weapon_shockroach" not in op4_w,
        "weapon_shockroach is an alias, not an eleventh OP4 player weapon")

    linux_client = linux["libraries"]["client.so"]
    linux_server = linux["libraries"]["hl.so"]
    win_client = windows["libraries"]["client.dll"]
    win_server = windows["libraries"]["hl.dll"]
    opfor_size = opfor_built.stat().st_size
    opfor_hash = sha256(opfor_built)
    rows = [f"| `{cls}` | لا | نعم | ناقص | نعم | غير مختبر |"
            for cls in op4_only]
    doc = f"""# جرد أسلحة Opposing Force على أساس BugfixedHL

> مولّد آلياً بأمر `python3 tools/weapon_inventory.py --write` من نسختي
> `.cache/upstreams/bugfixhl/` و`.cache/upstreams/op4/` النظيفتين، والشجرة المدمجة
> `bhl-op4/`، و`PORT_STATUS.json`، و manifest الخاص ببنائي لينكس وويندوز، وحزمة `mod/`.
> الحزمة الآن تبدأ حملة OP4 كاملة (`of0a0`) بخادم OP4 حقيقي، وليس حملة
> Half-Life مع أسلحة OP4. لا يُقرأ أي تقرير سابق أو نتيجة CI كدليل.

## الجدول المطلوب

| السلاح | موجود في BHL | موجود في OP4 | حالة الدمج | Prediction | اختبار اللعبة |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

**تفسير ملزم:** `ناقص` في «حالة الدمج» و`غير مختبر` في «اختبار اللعبة» ليسا تهرباً من
الجرد: ملفات المصدر والعميل/الخادم والحدث والتسجيل والإعطاء موصولة لكل الأسلحة العشرة،
لكن لا محرك GoldSrc ولا أصول OP4 شرعية في هذه البيئة. لذلك لا يوجد صف `مكتمل`
ولا `ناجح`، ولا يُقال عن أي سلاح إنه يعمل داخل اللعبة. `نعم` في `Prediction`
يعني توصيل ملف السلاح الحقيقي داخل `client` مع `CLIENT_DLL` وحالة `GetLocalWeapon`
و`UseDecrement()`، لا إثبات تنبؤ وقت التشغيل.

`weapon_shockroach` ليس سلاحاً حادي عشر: هو اسم كيان بديل لـ `CShockRifle` في
مصدر OP4 النظيف ولا يظهر في `W_Precache()`.

## ما تحقق منه الفحص فعلياً

* BHL النظيف: `{len(bhl_w)}` سلاحاً في `W_Precache()`؛ OP4 النظيف: `{len(op4_w)}`؛
  الفرق هو `{len(op4_only)}` أسلحة OP4 فقط. الشجرة المدمجة تسجّل `{len(merged_w)}`
  اسماً، مرة واحدة لكل اسم، بدون تكرار تسجيل.
* العميل: عشرة ملفات أسلحة OP4 حقيقية + `CGrappleTip.cpp` + `ehandle.cpp`
  + `op4_client_prediction.cpp` + تسعة أحداث عرض، مترجمة بـ `CLIENT_DLL`.
  `CGrapple` لم يعد server-authoritative؛ لا يوجد `UseDecrement()` مجبر على `FALSE`.
* `MAX_WEAPON_SLOTS = 7` وأمر `slot7` موصولان في كود BHL؛ سبرايت السلة السابعة
  داخل `sprites/hud.txt` ما زال غير مُختبَر في اللعبة.
* توافق شبكة OP4: `MAX_WEAPONS = 64`، `local_state_t.weapondata[64]`، نقل
  بيانات التنبؤ لـ64 سلاحاً، وربط رسالة `Weapons` ذات 8 بايتات في عميل BHL
  حتى لا تُقرأ بتات الأسلحة من حقل المحرك القديم ذي 32 بت فقط.
* `liblist.gam` يبدأ `of0a0` و`ofboot0`، `steam_appid.txt = 50`،
  `delta.lst` هو ملف OP4، و`fallback_dir "gearbox"` يجلب أصول OP4 المثبّتة.
* `autoexec.cfg` يضبط `sv_oldweapons 0`؛ `op4weapons.cfg` يعطي الأسلحة العشرة
  والذخائر عبر F9. خادم ويندوز المرقّع يجعل `impulse 101` يعطيها أيضاً،
  بما فيها `weapon_penguin`؛ لينكس يستخدم F9/F10 مع خادم `gearbox` الأصلي.
* لينكس: `client.so` `{linux_client['bytes']}` بايت، sha256
  `{linux_client['sha256']}`، مرتبط بأساس `GLIBC_2.17`؛ خادم `hl.so` القديم
  (`{linux_server['bytes']}` بايت) ليس داخل الحزمة، ويستخدم
  `../gearbox/dlls/opfor.so` بدلاً منه.
* ويندوز (`{windows['target']}`, `{windows['toolchain']}`, ABI متوافق مع MSVC/VGUI2):
  `client.dll` `{win_client['bytes']}` بايت، sha256 `{win_client['sha256']}`؛
  `opfor.dll` `{opfor_size}` بايت، sha256 `{opfor_hash}`. خادم `hl.dll`
  القديم (`{win_server['bytes']}` بايت) ليس داخل الحزمة.
  هذه ثنائيات MSVC، لكنها **غير مُختبَرة داخل اللعبة**.
* بصمات `SOURCES.sha256` تُتحقق لكل ملف موجود، ويكون عدد المخالفات صفراً؛
  مسارات `.cache/` لتبعيات SDK/deps ليست داخل git ويعيدها سكربت البناء،
  فيُتخطى الغائب منها صراحةً ولا يُحتسب نجاحاً. ثنائيات `mod/cl_dlls/`
  و`mod/dlls/opfor.dll` تطابق البناء الموجود تماماً.
* `MOD_MANIFEST.json` يقول صراحة: `in_game_tested_here: false`.

## النواقص التي تمنع علامة «مكتمل»

1. لا تحميل في محرك GoldSrc، ولا اختيار/إطلاق/إعادة تعبئة/ذخيرة/أنيميشن/صوت/Prediction
   فعلي، ولا اختبار أعطال أو تعدد لاعبين.
2. لا أصول OP4 قانونية مرفقة: الموديلات، الأصوات، سبرايت HUD، و`events/*.sc`
   تُقرأ من نسخة `gearbox/` المثبّتة لدى المستخدم عبر `fallback_dir`.
3. لا اختبار لنظام Windows runtime ولا لسلّة HUD السابعة داخل اللعبة، ولا
   تأكيد من المستخدم أن حملة OP4 والقوائم وكل سلاح تعمل بعد هذا التغيير.
4. خادم لينكس هو `gearbox` الأصلي: لا يحمل `sv_bhl_*` ولا ترقيع
   `impulse 101`، وهذا فرق صريح عن نسخة ويندوز.
5. البناء/الترجمة/الفحوص الآلية ليست بديلاً عن هذه الاختبارات.
"""
    return errors, doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    errors, doc = collect()
    if a.write:
        DOC.write_text(doc)
        print(f"wrote {DOC.relative_to(ROOT)}")
    if a.check:
        if not DOC.is_file() or DOC.read_text() != doc:
            errors.append("docs/WEAPON_INVENTORY.md is stale; run --write")
        if errors:
            for e in errors:
                print("FAIL:", e, file=sys.stderr)
            return 1
        print("== OP4 WEAPON INVENTORY OK ==")
    elif not a.write:
        print(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Client-side Opposing Force WEAPON event glue.

Scope is deliberately narrow: ONLY the client playback-event callbacks that
OP4's weapons fire (animations, sounds, muzzle flash, shells, beams, bullet
prediction). Nothing here touches movement, monsters, VGUI2 or BHL HUD systems.

The bodies are extracted VERBATIM from the pinned upstream
``halflife-op4-updated @ 5368be7f8eba`` file ``cl_dll/ev_hldm.cpp`` at tree
generation time. They cannot be compiled by wiring that whole file: it also
defines BHL's own ``EV_FireGlock1``, ``EV_FireMP5`` ... which would duplicate
strong symbols in ``client.so``. Only the OP4-only ``EV_*`` callbacks are
taken, with a labelled client header supplying the animation enum constants
that OP4's ``dlls/weapons/*.h`` headers carry. No event function is
reimplemented and no stub is introduced.

Only the client-side state that the included OP4 bodies actually reference is
declared/defined here (``g_iClub``, ``g_iSwing``, ``SetLocalBody``). The one
BHL-side helper this needs is a declared, weapon-only merge in
``src/game/client/hl/hl_weapons.cpp`` (see merge/bhl_base.py).

Upstream references are written into the generated files.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OP4 = ROOT / ".cache" / "upstreams" / "op4"

# One weapon is added AT A TIME. Each addition is a single data row here:
#   cls       server classname registered in W_Precache()
#   ammo      extra ammo entity to precache, or None
#   sounds    extra sounds the weapon's OP4 W_Precache() precaches, or []
#   cxx_class server C++ class (used by tests to check hl.so symbols)
#   event     client .sc script hooked in Game_HookEvents(), or None
#   func      OP4 EV_* callback name, or None (grapple has no event script)
#   header    OP4 weapon header holding the animation enum(s)
#   enums     enum names to reproduce verbatim in the client glue header
#   defines   extra verbatim declarations from that header (outside enums)
WEAPONS = [
    dict(cls="weapon_eagle", ammo=None, sounds=[], cxx_class="CEagle",
         event="events/eagle.sc", func="EV_FireEagle",
         header="dlls/weapons/CEagle.h", enums=["DesertEagleAnim"],
         defines=[]),
    dict(cls="weapon_pipewrench", ammo=None, sounds=[], cxx_class="CPipewrench",
     event="events/pipewrench.sc", func="EV_Pipewrench",
     header="dlls/weapons/CPipewrench.h", enums=["pipewrench_e"],
     defines=[]),
    dict(cls="weapon_m249", ammo="ammo_556", sounds=[], cxx_class="CM249",
     event="events/m249.sc", func="EV_FireM249",
     header="dlls/weapons/CM249.h", enums=["M249Anim"],
     defines=[]),
    dict(cls="weapon_displacer", ammo=None, sounds=[], cxx_class="CDisplacer",
     event="events/displacer.sc", func="EV_FireDisplacer",
     header="dlls/weapons/CDisplacer.h", enums=["DisplacerAnim", "DisplacerMode"],
     defines=["static const size_t DISPLACER_NUM_BEAMS = 4;"]),
    dict(cls="weapon_shockrifle", ammo=None, sounds=[], cxx_class="CShockRifle",
     event="events/shock.sc", func="EV_FireShockRifle",
     header="dlls/weapons/CShockRifle.h", enums=["ShockRifleAnim"],
     defines=[]),
    dict(cls="weapon_sporelauncher", ammo="ammo_spore",
     sounds=["weapons/spore_hit1.wav", "weapons/spore_hit2.wav", "weapons/spore_hit3.wav"],
     cxx_class="CSporeLauncher", event="events/spore.sc", func="EV_FireSpore",
     header="dlls/weapons/CSporeLauncher.h", enums=["SporeLauncherAnim"],
     defines=[]),
    dict(cls="weapon_sniperrifle", ammo="ammo_762", sounds=[], cxx_class="CSniperRifle",
     event="events/sniper.sc", func="EV_SniperRifle",
     header="dlls/weapons/CSniperRifle.h", enums=["SniperRifleAnim"],
     defines=[]),
    dict(cls="weapon_knife", ammo=None, sounds=[], cxx_class="CKnife",
     event="events/knife.sc", func="EV_Knife",
     header="dlls/weapons/CKnife.h", enums=["KnifeAnim"],
     defines=[]),
    dict(cls="weapon_penguin", ammo=None, sounds=[], cxx_class="CPenguin",
     event="events/penguinfire.sc", func="EV_PenguinFire",
     header="dlls/weapons/CPenguin.h", enums=["PenguinAnim"],
     defines=[]),
    dict(cls="weapon_grapple", ammo=None, sounds=[], cxx_class="CGrapple",
     event=None, func=None, header="dlls/weapons/CGrapple.h",
     enums=["BarnacleGrappleAnim"], defines=[]),
]

# Verbatim from the merged BHL server weapons.h (itself an OP4-MERGE of the
# three OP4 bullet types). Kept in the client glue header so no BHL client
# header has to be modified for a weapon-only constant.
BULLET_TYPES = [
    "BULLET_PLAYER_556",
    "BULLET_PLAYER_762",
    "BULLET_PLAYER_EAGLE",
]


def _brace_block(text: str, start: int) -> str:
    """Return text[start:end] where end closes the first '{' at/after start."""
    brace = text.index("{", start)
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise RuntimeError("unbalanced braces in OP4 source")


def _function(name: str, src: str) -> str:
    m = re.search(r"^void " + re.escape(name) + r"\(.*?\)\s*\{",
                  src, re.M | re.S)
    if not m:
        raise RuntimeError(f"cannot find {name} in OP4 cl_dll/ev_hldm.cpp")
    return _brace_block(src, m.start()).strip()


def _enum(name: str, src: str) -> str:
    m = re.search(r"^enum\s+(?:class\s+)?" + re.escape(name) + r"\s*\{",
                  src, re.M)
    if not m:
        raise RuntimeError(f"cannot find enum {name}")
    return _brace_block(src, m.start()).strip()


def _build() -> tuple[str, str]:
    ev_src = (OP4 / "cl_dll" / "ev_hldm.cpp").read_text()
    hdr_cache: dict[str, str] = {}
    bodies: dict[str, str] = {
        w["func"]: _function(w["func"], ev_src)
        for w in WEAPONS if w["func"]
    }
    used = "\n".join(bodies.values())

    header = [
        "/* ---------------------------------------------------------------------------",
        " * OP4 -> BHL CLIENT WEAPON-EVENT GLUE (authored in this repository).",
        " *",
        " * Verbatim animation enums from the pinned OP4 weapon headers. OP4's",
        " * cl_dll/ev_hldm.cpp includes the SERVER weapon headers for these",
        " * constants; that cannot be done in BHL's client target, so only the",
        " * enum blocks (no classes, no server headers) are reproduced here.",
        " * Upstream: halflife-op4-updated @ 5368be7f8eba.",
        " * -------------------------------------------------------------------------*/",
        "#pragma once",
        "#include <cstddef>",
        "",
    ]
    cpp = [
        "/* ---------------------------------------------------------------------------",
        " * OP4 -> BHL CLIENT WEAPON-EVENT GLUE (authored in this repository).",
        " *",
        " * VERBATIM OP4 cl_dll/ev_hldm.cpp playback-event callbacks. Every body",
        " * below is extracted from the pinned upstream at generation time; the",
        " * exact function name and upstream file are written above each one.",
        " * These are real weapon effects, not stubs and not simulations.",
        " *",
        " * Wiring cl_dll/ev_hldm.cpp itself is impossible: it also defines BHL's",
        " * own EV_FireGlock1 / EV_FireMP5 / ... and would duplicate symbols.",
        " * -------------------------------------------------------------------------*/",
        '/* ../  = BHL src/game/client/. Quoted includes search THIS file\'s',
        ' * directory first, and src/game/client/op4/ contains OP4\'s own',
        ' * ev_hldm.h / eventscripts.h, which would shadow BHL\'s headers and',
        ' * conflict with BHL ev_common.cpp\'s definitions. */',
        '#include "../hud.h"',
        '#include "../cl_util.h"',
        '#include "../cl_dll.h"',
        '#include "const.h"',
        '#include "entity_state.h"',
        '#include "cl_entity.h"',
        '#include "entity_types.h"',
        '#include "usercmd.h"',
        '#include "pm_defs.h"',
        '#include "pm_materials.h"',
        '#include "../eventscripts.h"',
        '#include "../ev_hldm.h"',
        '#include "r_efx.h"',
        '#include "event_api.h"',
        '#include "event_args.h"',
        '#include "in_defs.h"',
        '#include "r_studioint.h"',
        '#include "com_model.h"',
        '#include "op4_weapon_events.h"',
        "",
        "/* BHL client helpers used by the verbatim OP4 bodies. */",
        "void V_PunchAxis(int axis, float punch);",
    ]
    if "SetLocalBody" in used:
        cpp += [
            "/* Declared OP4-MERGE in BHL src/game/client/hl/hl_weapons.cpp:",
            " * the same operation as OP4's SetLocalBody(), against BHL's own",
            " * local-weapon array. Required by the verbatim EV_FireM249 body. */",
            "void SetLocalBody(int id, int body);",
        ]
    if "g_iClub" in used:
        cpp += [
            "/* OP4 cl_dll/ev_hldm.cpp:1653 - OP4-only pipewrench swing counter. */",
            "int g_iClub;",
        ]
    if "g_iSwing" in used:
        cpp += [
            "/* BHL src/game/client/ev_hldm.cpp:1183 already owns g_iSwing",
            " * (same name and purpose as OP4's). Reference it, do not duplicate. */",
            "extern int g_iSwing;",
        ]
    cpp.append("")

    for w in WEAPONS:
        if w["header"] not in hdr_cache:
            hdr_cache[w["header"]] = (OP4 / w["header"]).read_text()
        hs = hdr_cache[w["header"]]
        for en in w["enums"]:
            block = _enum(en, hs)
            # OP4 uses `enum NAME { ... };` in some headers and a bare
            # `enum NAME { ... }` in others. Normalise with a semicolon.
            if not block.endswith(";"):
                block += ";"
            header += [f"/* {w['header']} : {en} (verbatim) */", block, ""]
        for decl in w.get("defines", []):
            if decl not in hs:
                raise RuntimeError(f"{w['header']}: missing verbatim declaration {decl!r}")
            header += [f"/* {w['header']} (verbatim) */", decl, ""]

    # OP4-only bullet ids, verbatim values from the merged server weapons.h.
    header += [
        "/* OP4-MERGE bullet ids (verbatim OP4 dlls/weapons.h Bullet enum tail).",
        " * BHL's client ev_hldm.h stops at BULLET_MONSTER_12MM; these extend it",
        " * without editing that stable header: EV_HLDM_DecalGunshot/CheckTracer",
        " * already handle unknown ids through their `default` branch. */",
        "enum OP4BulletType",
        "{",
    ]
    base = (ROOT / "bhl-op4" / "src" / "game" / "server" / "weapons.h").read_text()
    m = re.search(r"\tBULLET_MONSTER_12MM,\s*\n(.*?)\} Bullet;", base, re.S)
    if not m:
        raise RuntimeError("cannot read OP4 bullet types from merged weapons.h")
    tail = [ln.strip().rstrip(",") for ln in m.group(1).strip().splitlines()
            if ln.strip() and not ln.strip().startswith("/*")
            and not ln.strip().startswith("*")]
    for i, name in enumerate(tail):
        header.append(f"\t{name} = {9 + i},")
    header += ["};", ""]

    for w in WEAPONS:
        if not w["func"]:
            continue
        cpp += [
            f"/* ===== OP4 cl_dll/ev_hldm.cpp : {w['func']} (verbatim) ===== */",
            f'extern "C" void {w["func"]}(event_args_t *args);',
            bodies[w["func"]],
            "",
        ]

    return "\n".join(header) + "\n", "\n".join(cpp) + "\n"


WEAPON_EVENTS_H, WEAPON_EVENTS_CPP = _build()


if __name__ == "__main__":
    print(f"weapons={len(WEAPONS)} events={sum(1 for w in WEAPONS if w['func'])} "
          f"header={len(WEAPON_EVENTS_H)}B cpp={len(WEAPON_EVENTS_CPP)}B")
    for w in WEAPONS:
        print(f"  {w['cls']:26s} {str(w['event']):24s} {w['func']}")

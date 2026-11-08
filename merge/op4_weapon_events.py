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
that OP4's ``dlls/weapons/*.h`` headers carry. No function is reimplemented
and no stub is introduced.

Upstream references are written into the generated files.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OP4 = ROOT / ".cache" / "upstreams" / "op4"

# (server classname, client event fn, event script, OP4 weapon header,
#  animation enum name(s), extra ammo classname to precache or None)
#
# One weapon is added at a time. Each addition is a small, reviewable change:
# server W_Precache registration + client pfnHookEvent + the real EV_* body.
WEAPONS = [
    dict(cls="weapon_eagle", ammo=None, cxx_class="CEagle",
         event="events/eagle.sc", func="EV_FireEagle",
         header="dlls/weapons/CEagle.h", enums=["DesertEagleAnim"]),
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
    m = re.search(r"^enum\s+" + re.escape(name) + r"\s*\{", src, re.M)
    if not m:
        raise RuntimeError(f"cannot find enum {name}")
    return _brace_block(src, m.start()).strip()


def _build() -> tuple[str, str]:
    ev_src = (OP4 / "cl_dll" / "ev_hldm.cpp").read_text()
    hdr_cache: dict[str, str] = {}

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
        "void V_PunchAxis(int axis, float punch);",
        "",
        "/* Third-party/BHL client helpers used by the verbatim bodies. */",
        "",
    ]

    for w in WEAPONS:
        if w["header"] not in hdr_cache:
            hdr_cache[w["header"]] = (OP4 / w["header"]).read_text()
        hs = hdr_cache[w["header"]]
        for en in w["enums"]:
            block = _enum(en, hs)
            # OP4 uses `enum NAME { ... };` in some headers and bare `enum
            # NAME { ... }` in others. Normalise with a trailing semicolon.
            if not block.endswith(";"):
                block += ";"
            header += [f"/* {w['header']} : {en} (verbatim) */", block, ""]

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
        body = _function(w["func"], ev_src)
        cpp += [
            f"/* ===== OP4 cl_dll/ev_hldm.cpp : {w['func']} (verbatim) ===== */",
            f'extern "C" void {w["func"]}(event_args_t *args);',
            body,
            "",
        ]

    return "\n".join(header) + "\n", "\n".join(cpp) + "\n"


WEAPON_EVENTS_H, WEAPON_EVENTS_CPP = _build()


if __name__ == "__main__":
    print(f"weapons={len(WEAPONS)} header={len(WEAPON_EVENTS_H)}B "
          f"cpp={len(WEAPON_EVENTS_CPP)}B")
    for w in WEAPONS:
        print(f"  {w['cls']:26s} {w['event']:24s} {w['func']}")

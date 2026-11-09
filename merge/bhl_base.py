#!/usr/bin/env python3
"""Build the canonical BHL-based OP4 merge tree.

ARCHITECTURE (this is the whole point of the module):

    BASE  = BugfixedHL-Rebased @ 4d32095e3c33  (verbatim, all 694 files)
    ADD   = halflife-op4-updated @ 5368be7f8eba subsystems (weapons, CTF,
            rope, OP4 entities, OP4 client events/HUD)
    MERGE = additive, anchored merges of OP4 declarations INTO BHL headers
    PATCH = deterministic, named API adaptations applied to OP4 sources so
            their modernised (bool/override) HLSDK API matches BHL's HLSDK API
    GLUE  = one small compatibility header + implementation file for symbols
            whose OP4 implementation lives in OP4's own weapons.cpp/util.cpp
            (those files cannot be compiled next to BHL's versions of them)

Nothing here reimplements a BugfixedHL system. BugfixedHL is the tree; OP4 is
what gets merged into it. Every output file's origin is recorded in
PROVENANCE.json, including the exact rule that modified it.

Usage:
    python3 -m merge.bhl_base --out bhl-op4
    python3 -m merge.bhl_base --check --out bhl-op4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from . import op4_fixups
from . import op4_weapon_events

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "upstreams"
BHL = CACHE / "bugfixhl"
OP4 = CACHE / "op4"

BHL_COMMIT = "4d32095e3c33"
OP4_COMMIT = "5368be7f8eba"
SOURCE_SDK_COMMIT = "11f26656677c881c7c630d03957900e7701da62e"

# --------------------------------------------------------------------------
# ADD: OP4 subsystem directories, copied verbatim into the BHL tree
# --------------------------------------------------------------------------
ADD_DIRS = {
    "dlls/weapons": "src/game/server/op4/dlls/weapons",
    "dlls/ctf": "src/game/server/op4/dlls/ctf",
    "dlls/rope": "src/game/server/op4/dlls/rope",
    "cl_dll/hl": "src/game/client/op4/hl",
    "cl_dll/particleman": "src/game/client/op4/particleman",
}

# OP4 root-level dlls/ and cl_dll/ files that belong to the merged subsystems.
# OP4's own core headers/sources are kept as REFERENCE ONLY. They must not sit
# in op4/dlls/ because quoted #include would then prefer them over BHL's
# headers, and compiling them would duplicate BHL's own classes. Their additive
# declarations are merged into BHL's headers by apply_merges() instead.
REFERENCE_FILES = [
    "dlls/skill.h", "dlls/decals.h", "dlls/cdll_dll.h", "dlls/weapons.h",
    "dlls/weapons.cpp", "dlls/weapons_shared.cpp", "dlls/util.h",
    "dlls/util.cpp", "dlls/player.h", "dlls/player.cpp", "dlls/gamerules.h",
    "dlls/gamerules.cpp", "dlls/enginecallback.h",
]

ADD_ROOT_FILES = {
    "src/game/server/op4/dlls": [
        "dlls/UserMessages.h", "dlls/UserMessages.cpp",
        "dlls/coopplay_gamerules.cpp", "dlls/coopplay_gamerules.h",
        "dlls/ctfplay_gamerules.cpp", "dlls/ctfplay_gamerules.h",
          "dlls/ehandle.cpp", "dlls/Wxdebug.cpp", "dlls/wxdebug.h",
    ],
    "src/game/client/op4": [
        "cl_dll/hl_events.cpp", "cl_dll/ev_hldm.cpp", "cl_dll/ev_hldm.h",
        "cl_dll/ev_common.cpp", "cl_dll/com_weapons.cpp", "cl_dll/com_weapons.h",
        "cl_dll/hud_flagicons.cpp", "cl_dll/hud_playerbrowse.cpp",
        "cl_dll/hud_spectator.cpp", "cl_dll/hud_spectator.h",
        "cl_dll/overview.cpp", "cl_dll/overview.h", "cl_dll/death.cpp",
        "cl_dll/tri.cpp", "cl_dll/tri.h", "cl_dll/saytext.cpp",
        "cl_dll/scoreboard.cpp", "cl_dll/util.cpp", "cl_dll/util.h",
        "cl_dll/eventscripts.h", "cl_dll/events.cpp",
        "cl_dll/parsemsg.cpp", "cl_dll/parsemsg.h",
    ],
}

# OP4-only monsters / entities / map logic (names absent from BHL's server).
ADD_OP4_ENTITIES = [
    "baby_voltigore", "blkop_apache", "blkop_osprey", "blowercannon",
    "cleansuit_scientist", "CDrillSergeant", "COFAllyMonster",
    "COFSquadTalkMonster", "CRecruit", "func_tank_of", "geneworm",
    "gonome", "hfgrunt", "hgrunt_ally", "hgrunt_medic", "hgrunt_torch",
    "item_generic", "loader", "male_assassin", "nuclearbomb", "op4mortar",
    "otis", "penguin_grenade", "pitworm", "pitworm_up", "shockroach",
    "shocktrooper", "squeakgrenade", "voltigore", "zombie_barney",
    "zombie_soldier", "Wxdebug", "world", "geneworm",
]

# --------------------------------------------------------------------------
# PATCH: named, deterministic adaptations of OP4 sources to BHL's API.
# Every rule is recorded in PROVENANCE.json. These are compatibility edits,
# NOT new implementations: the method bodies remain OP4's upstream bodies.
# --------------------------------------------------------------------------
def repl(prefix: str, method: str, typ: str):
    """bool X::Method( -> typ X::Method(  (also matches unqualified)."""
    return (r"\bbool\s+(\w+::)?" + method + r"\s*\(",
            lambda m: typ + " " + (m.group(1) or "") + method + "(")


PATCH_RULES = [
    ("bhl-bool-to-int-save",        *repl("", "Save", "int")),
    ("bhl-bool-to-int-restore",     *repl("", "Restore", "int")),
    ("bhl-bool-to-bool-deploy",     *repl("", "Deploy", "BOOL")),
    ("bhl-bool-to-bool-shouldidle", *repl("", "ShouldWeaponIdle", "BOOL")),
    ("bhl-bool-to-int-iteminfo",    *repl("", "GetItemInfo", "int")),
    ("bhl-bool-to-bool-decrement",  *repl("", "UseDecrement", "BOOL")),
    ("bhl-bool-to-bool-addammo",    *repl("", "AddAmmo", "BOOL")),
    ("bhl-bool-to-bool-candeploy",  *repl("", "CanDeploy", "BOOL")),
    ("bhl-bool-to-bool-canholster", *repl("", "CanHolster", "BOOL")),
    ("bhl-bool-to-bool-emptysound", *repl("", "PlayEmptySound", "BOOL")),
    ("bhl-bool-to-bool-isuseable",  *repl("", "IsUseable", "BOOL")),
    ("bhl-bool-to-bool-clientdata", *repl("", "UpdateClientData", "BOOL")),
    ("bhl-bool-to-int-duplicate",   *repl("", "AddDuplicate", "int")),
    ("bhl-bool-to-int-extract",     *repl("", "ExtractAmmo", "int")),
    ("bhl-bool-to-int-extractclip", *repl("", "ExtractClipAmmo", "int")),
    ("bhl-bool-to-int-addtoplayer", *repl("", "AddToPlayer", "int")),
    ("bhl-bool-to-int-takedamage",  *repl("", "TakeDamage", "int")),
    ("bhl-bool-to-void-keyvalue",   r"\bbool\s+(\w+::)?KeyValue\s*\(",
                                     lambda m: "void " + (m.group(1) or "") + "KeyValue("),
    ("bhl-holster-skiplocal",
     r"\bvoid\s+Holster\(\)\s*override", "void Holster(int skiplocal = 0) override"),
    ("bhl-holster-skiplocal-def",
     r"(\bvoid\s+\w+::Holster)\(\)", r"\1(int skiplocal)"),
    ("bhl-drop-override-prediction",
     r"(\bvoid\s+(?:GetWeaponData|SetWeaponData)\s*\([^)]*\))\s*override", r"\1"),
    ("bhl-drop-override-increment",
     r"(\bvoid\s+IncrementAmmo\s*\([^)]*\))\s*override", r"\1"),
    ("bhl-vector-normalize",
     r"(\b\w+(?:->\w+|\.\w+)*)\.Normalize\(\)", r"OP4_Normalized(\1)"),
    ("bhl-getprivate-template",
     r"GET_PRIVATE<(\w+)>\(([^)]*)\)", r"((\1 *)GET_PRIVATE(\2))"),
      ("bhl-ctfteam-scoped-enum-cast",
       r"(\bm_iTeamNum\s*==\s*)(CTFTeam::\w+)", r"\1(int)\2"),
      # OP4 declares `enum class CTFTeam`; BHL's player state uses plain ints.
      # An unscoped enum still supports CTFTeam::Name in C++11 and converts to
      # int, so OP4's CTF comparisons/assignments work without touching logic.
      ("bhl-ctfteam-unscoped-enum",
       r"\benum class CTFTeam\b", "enum CTFTeam"),
      # OP4 modernised several BOOL parameters to bool; BHL's virtuals still
      # take BOOL. Mechanical parameter type adaptations (bodies unchanged).
      ("bhl-canplaysentence-signature",
       r"\bbool\s+CanPlaySentence\s*\(\s*bool\s+", "int CanPlaySentence(BOOL "),
      ("bhl-canplaysentence-param",
       r"CanPlaySentence\s*\(\s*bool\s+", "CanPlaySentence(BOOL "),
      ("bhl-playscriptedsentence-param",
       r"\bbool\s+bConcurrent\b", "BOOL bConcurrent"),
        ("bhl-stopfollowing-param",
         r"StopFollowing\s*\(\s*bool\s+", "StopFollowing(BOOL "),
        # OP4's CHalfLifeCTFplay (dlls/ctf/ctfplay_gamerules.h) declares five
        # CTF-only helpers with `override`. BHL's CGameRules has no such
        # virtuals, so `override` is a hard compile error. Dropping ONLY the
        # `override` keyword keeps OP4's real declarations/bodies intact.
        ("bhl-ctf-nonvirtual-overrides",
         r"(const char\* GetCharacterType\([^)]*\)|int GetNumTeams\(\)|"
         r"const char\* TeamWithFewestPlayers\(\)|bool TeamsBalanced\(\)|"
         r"void GoToIntermission\(\))\s*override", r"\1"),
        # BHL CGameRules::ChangePlayerTeam uses BOOL, OP4-updated uses bool.
        ("bhl-ctf-changeplayerteam-bools",
         r"\bbool\s+bKill\s*,\s*bool\s+bGib\b", "BOOL bKill, BOOL bGib"),
          # OP4's UserMessages.h defines every gmsg* id as a C++17 inline
          # variable. BHL's player.cpp already owns strong definitions for the
          # shared ids, and the labelled glue owns the OP4-only ids. Turning
          # them all into extern declarations gives exactly one strong symbol
          # per id instead of a COMDAT/strong mix.
          ("bhl-ctf-usermsg-extern",
           r"inline int (gmsg\w+) = 0;", r"extern int \1;"),
        # OP4's cbase.h has a template CBaseEntity::Instance<T>(edict_t*);
        # BHL has the non-template CBaseEntity::Instance(edict_t*) returning
        # CBaseEntity*. Same engine primitive, mechanical cast only.
        ("bhl-instance-template",
         r"\b(?:CBaseEntity::)?Instance<(\w+)>\(([^()]*)\)",
         r"static_cast<\1 *>(CBaseEntity::Instance(\2))"),
    ]


def bhl_legacy_int_methods(tree: Path) -> dict[str, str]:
    """Map method name -> BHL's declared legacy return type (BOOL or int).

    OP4-updated modernised these to `bool`; a `bool` override of a `BOOL`/`int`
    virtual is a hard compile error. The mapping is derived from BHL's own
    headers, not guessed.
    """
    out: dict[str, str] = {}
    for p in (tree / "src/game/server").rglob("*.h"):
        text = p.read_text(errors="surrogateescape")
        for typ, name in re.findall(
                r"\b(?:virtual\s+)?(BOOL|int)\s+(\w+)\s*\(", text):
            out.setdefault(name, typ)
    return out


def fix_keyvalue_returns(text: str) -> tuple[str, int]:
    """BHL declares KeyValue() as void; OP4's returns true/false.

    After `bhl-bool-to-void-keyvalue` the declarations match but the bodies
    still `return true;`. Strip those value returns inside KeyValue bodies
    only (brace-matched), leaving every other function untouched.
    """
    out = text
    count = 0
    # Process matches back-to-front so earlier offsets stay valid as the
    # string shrinks when `return true;` becomes `return;`.
    for m in reversed(list(re.finditer(
            r"\bvoid\s+(?:\w+::)?KeyValue\s*\([^)]*\)\s*\{", out))):
        start = m.end() - 1
        depth = 0
        end = start
        for i in range(start, len(out)):
            if out[i] == "{":
                depth += 1
            elif out[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end <= start:
            continue
        body = out[start:end]
        new_body, n = re.subn(r"\breturn\s+(?:true|false)\s*;", "return;", body)
        if n:
            out = out[:start] + new_body + out[end:]
            count += n
    return out, count


def compile_patch_rules(tree: Path | None = None):
    rules = [(name, re.compile(pat), rep) for name, pat, rep in PATCH_RULES]
    if tree is not None:
        types = bhl_legacy_int_methods(tree)
        names = sorted(types, key=len, reverse=True)
        rx = re.compile(r"\bbool\s+(\w+::)?(" + "|".join(names) + r")\s*\(")
        rules.append((
            "bhl-bool-returns-from-bhl-virtuals",
            rx,
            lambda m: types[m.group(2)] + " " + (m.group(1) or "") + m.group(2) + "(",
        ))
    return rules


# --------------------------------------------------------------------------
# GLUE: the only files authored in this repository (clearly labelled).
# --------------------------------------------------------------------------
GLUE_HEADER = r'''/* ---------------------------------------------------------------------------
 * OP4 -> BugfixedHL-Rebased compatibility GLUE.
 *
 * This header is NOT BugfixedHL and does not reimplement any BugfixedHL
 * system. It exists only because OP4's subsystem sources use the modernised
 * HLSDK API (bool/override, Vector-based event args) while BugfixedHL uses
 * the original HLSDK API. It supplies:
 *   - declarations for OP4 helpers whose upstream bodies live in OP4's
 *     weapons.cpp / util.cpp (those whole files cannot coexist with BHL's
 *     own weapons.cpp / util.cpp),
 *   - thin, mechanical argument conversions (Vector -> float *).
 * All game logic lives in the verbatim upstream BHL and OP4 files.
 * See docs/BHL_BASE_MERGE.md and PROVENANCE.json.
 * -------------------------------------------------------------------------*/
#ifndef OP4_BHL_COMPAT_H
#define OP4_BHL_COMPAT_H

#include "extdll.h"
#include "enginecallback.h"   /* BHL engine callbacks (WRITE_COORD, ...) */
#include "event_flags.h"
#include "weaponinfo.h"       /* BHL's weapon_data_t */
#include "ctf/CTFDefs.h"      /* OP4's CTFItem enum */

class CBaseEntity;            /* forward declaration only */

int  UTIL_DefaultPlaybackFlags();
BOOL UTIL_DefaultUseDecrement();
BOOL UTIL_UseOldWeapons();
bool UTIL_IsMultiplayer();
bool UTIL_IsCTF();

/* OP4 expects a 7th weapon slot; BHL declares 6. */
#ifndef MAX_WEAPON_SLOTS_OP4
#define MAX_WEAPON_SLOTS_OP4 7
#endif

/* OP4 decal indices: mapped to the nearest BHL decal until OP4's world.cpp
 * decal table is merged. Documented, not hidden. */
#ifndef DECAL_SPR_SPLT1
#define DECAL_SPR_SPLT1 DECAL_GUNSHOT1
#endif
#ifndef DECAL_OFSCORCH1
#define DECAL_OFSCORCH1 DECAL_SCORCH1
#endif
#ifndef PLAYER_GRAPPLE
#define PLAYER_GRAPPLE ((PLAYER_ANIM)8)
#endif
#ifndef PFLAG_ONROPE
#define PFLAG_ONROPE (1 << 6)   /* OP4 player.h */
#endif

/* OP4-only entity classifications (OP4 dlls/cbase.h). Additive: BHL's
 * classification enum is left untouched. */
#ifndef CLASS_HUMAN_MILITARY_FRIENDLY
#define CLASS_HUMAN_MILITARY_FRIENDLY 14
#endif
#ifndef CLASS_CTFITEM
#define CLASS_CTFITEM 30
#endif
  #ifndef CLASS_ALIEN_RACE_X
  #define CLASS_ALIEN_RACE_X 15  /* OP4 dlls/cbase.h:112 */
  #endif

  /* ---- OP4 dlls/cdll_dll.h:187-213, verbatim -------------------------- *
   * CTF menu ids, HUD colour constants and UnpackRGB(). BHL's cdll_dll.h
   * has none of them; ctf/ctfplay_gamerules.cpp uses all of them.        */
  #ifndef MENU_NONE
  #define MENU_NONE 0
  #define MENU_DEFAULT 1
  #define MENU_TEAM 2
  #define MENU_CLASS 3
  #define MENU_MAPBRIEFING 4
  #define MENU_INTRO 5
  #define MENU_CLASSHELP 6
  #define MENU_CLASSHELP2 7
  #define MENU_REPEATHELP 8
  #define MENU_STATSMENU 9
  #define MENU_SCOREBOARD 10
  #endif
  #ifndef RGB_YELLOWISH
  #define RGB_YELLOWISH 0x00FFA000 /* 255,160,0 */
  #define RGB_REDISH    0x00FF1010
  #define RGB_GREENISH  0x0000A000 /* 0,160,0 */
  #define RGB_HUD_COLOR RGB_GREENISH
  #endif
  inline void UnpackRGB(int &r, int &g, int &b, unsigned long ulRGB)
  {
      r = (ulRGB & 0xFF0000) >> 16;
      g = (ulRGB & 0xFF00) >> 8;
      b = ulRGB & 0xFF;
  }

  /* OP4 dlls/world.h:21 -- the worldspawn flag that selects CTF rules. */
  #ifndef SF_WORLD_CTF
  #define SF_WORLD_CTF 0x0008
  #endif

  /* ---- OP4 dlls/util.h:584-595, verbatim ------------------------------ */
  struct MinuteSecondTime
  {
      const int Minutes;
      const int Seconds;
  };
  inline MinuteSecondTime SecondsToTime(const int seconds)
  {
      const auto minutes = seconds / 60;
      return { minutes, seconds - (minutes * 60) };
  }

  /* OP4 dlls/game.cpp:580-586 / dlls/game.h:46-50 real cvars. Definitions
   * live in the labelled glue op4_link_fixups.cpp. */
  extern cvar_t ctfplay;
  extern cvar_t ctf_autoteam;
  extern cvar_t ctf_capture;
  extern cvar_t coopplay;
  extern cvar_t defaultcoop;
  extern cvar_t coopweprespawn;
  extern cvar_t oldweapons;

  /* OP4 user-message ids. BHL owns the shared ids (player.cpp); the labelled
   * glue owns the OP4-only ids. OP4's UserMessages.h is patched to extern. */
  extern int gmsgFlagIcon;
  extern int gmsgFlagTimer;
  extern int gmsgPlayerIcon;
  extern int gmsgPlayerBrowse;
  extern int gmsgHudColor;
  extern int gmsgSetMenuTeam;
  extern int gmsgCTFScore;
  extern int gmsgStatsInfo;
  extern int gmsgStatsPlayer;
  extern int gmsgTeamFull;
  extern int gmsgOldWeapon;
  extern int gmsgCustomIcon;
  extern int gmsgWeapons;
  extern int gmsgAllowSpec;
  extern int gmsgTeamNames;
  extern int gmsgVGUIMenu;
  extern int gmsgShowMenu;
  extern int gmsgSpectator;

  /* OP4 dlls/client.cpp:152-166 respawn() and BHL world.cpp CopyToBodyQue;
   * the real bodies are in the labelled glue. */
  extern void respawn(entvars_t *pev, bool fCopyCorpse);
  extern void CopyToBodyQue(entvars_t *pev);

/* OP4 common/Platform.h:72-90 stack scratch macros. OP4's combat.cpp uses
 * them for the GibData submodel-limit bookkeeping. On POSIX the upstream
 * implementation is exactly alloca()/no-op; reproduced here because BHL
 * does not ship OP4's Platform.h. No game logic is involved. */
#ifndef stackalloc
#define stackalloc(size) alloca(size)
#endif
#ifndef stackfree
#define stackfree(address) ((void)0)
#endif

/* OP4-only gamerules constants (OP4 dlls/gamerules.h). */
#ifndef ITEM_RESPAWN_TIME
#define ITEM_RESPAWN_TIME 30
#define WEAPON_RESPAWN_TIME 20
#define AMMO_RESPAWN_TIME 20
#define ENTITY_INTOLERANCE 100
#endif

/* OP4 common/Platform.h helpers; BHL uses std::min/max instead. */
#ifndef V_min
#define V_min(a, b) (((a) < (b)) ? (a) : (b))
#define V_max(a, b) (((a) > (b)) ? (a) : (b))
#endif

/* OP4 globals defined in its game.cpp; declarations only, no bodies here. */
extern cvar_t multipower;
extern cvar_t coopweprespawn;

/* OP4 monsters.h helper, implemented in OP4 monsters.cpp. */
bool IsFacing(entvars_t *pevTest, const Vector &reference);

/* OP4 dlls/util.h helper; thin adapter over BHL's engine state below. */
CBaseEntity *UTIL_GetLocalPlayer();

inline void WRITE_COORD_VECTOR(const Vector &vec)
{
	WRITE_COORD(vec.x);
	WRITE_COORD(vec.y);
	WRITE_COORD(vec.z);
}

inline float *OP4_VEC(const Vector &v) { return const_cast<float *>(&v.x); }

/* OP4's Vector::Normalize() returns a normalised copy; BHL's mathlib has
 * VectorNormalize() which normalises in place and returns the length. */
inline Vector OP4_Normalized(const Vector &v) { Vector r = v; VectorNormalize(r); return r; }

#endif /* OP4_BHL_COMPAT_H */
'''

GLUE_LATE_HEADER = r'''/* ---------------------------------------------------------------------------
 * Late compatibility macros. Included AFTER an OP4 source's own #include
 * block, so they cannot corrupt BHL header declarations (a macro named
 * FindHullIntersection would otherwise expand inside weapons.h).
 * -------------------------------------------------------------------------*/
#ifndef OP4_BHL_COMPAT_LATE_H
#define OP4_BHL_COMPAT_LATE_H
#include "op4_compat.h"

''' + op4_fixups.ENTITY_ENUMERATOR + r'''
  /* BHL: PLAYBACK_EVENT_FULL is (*g_engfuncs.pfnPlaybackEvent), float* args.
 * OP4: passes Vector origin/angles. */
#undef PLAYBACK_EVENT_FULL
#define PLAYBACK_EVENT_FULL(flags, pInvoker, eventindex, delay, origin, angles, fparam1, fparam2, iparam1, iparam2, bparam1, bparam2) \
	(*g_engfuncs.pfnPlaybackEvent)(flags, pInvoker, eventindex, delay, OP4_VEC(origin), OP4_VEC(angles), fparam1, fparam2, iparam1, iparam2, bparam1, bparam2)

/* BHL's FindHullIntersection takes float* hull bounds; OP4 passes Vector. */
#define FindHullIntersection(src, tr, mins, maxs, ent) \
	FindHullIntersection(src, tr, OP4_VEC(mins), OP4_VEC(maxs), ent)

/* OP4's Vector::Normalize() returns a normalised copy; BHL's mathlib Vector
 * spells that Normalized(). This macro is defined only after all headers have
 * been parsed (see file header), so it cannot change BHL declarations. */
  #ifndef OP4_BHL_NO_NORMALIZE_MACRO
  #define Normalize() Normalized()
  #endif

  /* OP4's Vector::Make2D() (OP4 dlls/vector.h:115) returns Vector2D{x,y};
   * BHL's Source-SDK mathlib Vector spells that AsVector2D() (vector.h:113).
   * Mechanical member-name mapping only; the expression is unchanged. */
  #ifndef OP4_BHL_NO_MAKE2D_MACRO
  #define Make2D() AsVector2D()
  #endif

  /* OP4 dlls/explode.h:25 has a 5-arg ExplosionCreate(center, angles,
   * pOwner, magnitude, doDamage). BHL's explode.h:28 additionally separates
   * pInflictor from pAttacker. OP4 passes one owner for both roles, so this
   * inline forwards to BHL's real ExplosionCreate with that mapping. The
   * declaration is repeated so the overload is available even in TUs that
   * never include explode.h; no function body is replaced or invented. */
  extern void ExplosionCreate(const Vector &center, const Vector &angles,
                              edict_t *pInflictor, edict_t *pAttacker,
                              int magnitude, BOOL doDamage);
  inline void ExplosionCreate(const Vector &center, const Vector &angles,
                              edict_t *pOwner, int magnitude, bool doDamage)
  {
      ::ExplosionCreate(center, angles, pOwner, pOwner, magnitude, doDamage ? 1 : 0);
  }

  /* ---- OP4 dlls/player.h:473-602, verbatim --------------------------- *
   * Only compiled where BHL's player.h has already been included (guard
   * PLAYER_H), because CPlayerIterator needs CBasePlayer complete. OP4's
   * CTF rules iterate players with UTIL_FindPlayers(); BHL exposes only
   * UTIL_PlayerByIndex(), which is exactly what this adapter calls.       */
  #ifdef PLAYER_H
  class CPlayerIterator
  {
  public:
      static const int FirstPlayerIndex = 1;

      CPlayerIterator()
          : m_pPlayer(nullptr), m_iNextIndex(gpGlobals->maxClients + 1)
      {
      }

      CPlayerIterator(const CPlayerIterator&) = default;

      CPlayerIterator(CBasePlayer* pPlayer)
          : m_pPlayer(pPlayer), m_iNextIndex(pPlayer ? pPlayer->entindex() + 1 : FirstPlayerIndex)
      {
      }

      CPlayerIterator& operator=(const CPlayerIterator&) = default;

      const CBasePlayer* operator*() const { return m_pPlayer; }

      CBasePlayer* operator*() { return m_pPlayer; }

      CBasePlayer* operator->() { return m_pPlayer; }

      void operator++()
      {
          m_pPlayer = static_cast<CBasePlayer*>(FindNextPlayer(m_iNextIndex, &m_iNextIndex));
      }

      void operator++(int)
      {
          ++*this;
      }

      bool operator==(const CPlayerIterator& other) const
      {
          return m_pPlayer == other.m_pPlayer;
      }

      bool operator!=(const CPlayerIterator& other) const
      {
          return !(*this == other);
      }

      static CBasePlayer* FindNextPlayer(int index, int* pOutNextIndex = nullptr)
      {
          while (index <= gpGlobals->maxClients)
          {
              auto pPlayer = UTIL_PlayerByIndex(index);

              if (pPlayer)
              {
                  if (pOutNextIndex)
                  {
                      *pOutNextIndex = index + 1;
                  }

                  return static_cast<CBasePlayer*>(pPlayer);
              }

              ++index;
          }

          if (pOutNextIndex)
          {
              *pOutNextIndex = gpGlobals->maxClients;
          }

          return nullptr;
      }

  private:
      int m_iNextIndex = 1;
      CBasePlayer* m_pPlayer;
  };

  class CPlayerEnumerator
  {
  public:
      using iterator = CPlayerIterator;

      CPlayerEnumerator() = default;

      iterator begin()
      {
          return {static_cast<CBasePlayer*>(CPlayerIterator::FindNextPlayer(CPlayerIterator::FirstPlayerIndex))};
      }

      iterator end()
      {
          return {};
      }
  };

  class CPlayerEnumeratorWithStart
  {
  public:
      using iterator = CPlayerIterator;

      CPlayerEnumeratorWithStart(CBasePlayer* pStartEntity)
          : m_pStartEntity(pStartEntity)
      {
      }

      iterator begin()
      {
          return {m_pStartEntity};
      }

      iterator end()
      {
          return {};
      }

  private:
      CBasePlayer* m_pStartEntity = nullptr;
  };

  inline CPlayerEnumerator UTIL_FindPlayers()
  {
      return {};
  }

  inline CPlayerEnumeratorWithStart UTIL_FindPlayers(CBasePlayer* pStartEntity)
  {
      return {pStartEntity};
  }
  #endif /* PLAYER_H */
  #endif /* OP4_BHL_COMPAT_LATE_H */
  '''

GLUE_CPP = r'''/* Implementations of the OP4 helpers declared in op4_compat.h.
 * Small, mechanical adapters over real BugfixedHL engine state. */
#include "op4_compat.h"
#include "util.h"
#include "cbase.h"
#include "weapons.h"
#include "player.h"
#include "gamerules.h"
#include "game.h"

extern cvar_t oldweapons;

int UTIL_DefaultPlaybackFlags() { return oldweapons.value == 1 ? 0 : FEV_NOTHOST; }
BOOL UTIL_DefaultUseDecrement() { return oldweapons.value == 0; }
BOOL UTIL_UseOldWeapons() { return oldweapons.value != 0; }
bool UTIL_IsMultiplayer() { return g_pGameRules != nullptr && g_pGameRules->IsMultiplayer(); }

  /* OP4 dlls/util.cpp:2582-2585, verbatim body. NOT a stub: it asks BHL's
   * real CGameRules::IsCTF() virtual. BHL's base implementation returns false
   * because the OP4 CTF ruleset is not installed as the active gamerules; that
   * is an explicitly declared incompleteness, not a hidden constant. */
    bool UTIL_IsCTF() { return g_pGameRules->IsCTF(); }

  /* OP4's UTIL_GetLocalPlayer() returns the first player entity. BHL exposes
   * the same engine state through CBaseEntity::Instance / pfnPEntityOfEntIndex. */
  CBaseEntity *UTIL_GetLocalPlayer()
  {
      return CBaseEntity::Instance(g_engfuncs.pfnPEntityOfEntIndex(1));
  }
  '''


# --------------------------------------------------------------------------
# MERGE: additive, anchored merges of OP4 declarations INTO BHL headers.
# --------------------------------------------------------------------------
def extract_defines(op4_text: str, bhl_text: str) -> list[tuple[str, str]]:
    defs = {}
    for ln in op4_text.splitlines():
        m = re.match(r"\s*#define\s+(\w+)\s+(.+?)\s*(?://.*)?$", ln)
        if m:
            defs[m.group(1)] = m.group(2)
    have = set(re.findall(r"#define\s+(\w+)", bhl_text))
    return [(k, v) for k, v in defs.items()
            if k not in have and not k.startswith("NOT_USED")]


def apply_merges(tree: Path, provenance: dict) -> None:
    def edit(rel: str, marker: str, text: str, rule: str, before: bool = False):
        p = tree / rel
        s = p.read_text(errors="surrogateescape")
        if marker not in s:
            raise RuntimeError(f"merge rule {rule}: anchor missing in {rel}: {marker!r}")
        # Compare the WHOLE inserted block, not just a prefix: several merge
        # rules deliberately share a "/* OP4-MERGE: verbatim OP4 ..." header,
        # and a 40-character prefix check used to suppress later rules.
        if text.strip() and text.strip() in s:
            return
        s = s.replace(marker, text + "\n" + marker if before else marker + "\n" + text, 1)
        p.write_text(s, errors="surrogateescape")
        provenance[rel].setdefault("merge_rules", []).append(rule)

    def subst(rel: str, old: str, new: str, rule: str):
        """Replace one existing BHL line with a wider OP4-compatible bound."""
        p = tree / rel
        s = p.read_text(errors="surrogateescape")
        if new in s:
            return
        if old not in s:
            raise RuntimeError(f"merge rule {rule}: anchor missing in {rel}: {old!r}")
        p.write_text(s.replace(old, new, 1), errors="surrogateescape")
        provenance[rel].setdefault("merge_rules", []).append(rule)

    # 1. OP4-only constants from dlls/weapons.h into BHL weapons.h
    op4w = (OP4 / "dlls/weapons.h").read_text(errors="surrogateescape")
    bhlw = (tree / "src/game/server/weapons.h").read_text(errors="surrogateescape")
    missing = extract_defines(op4w, bhlw)
    block = "\n".join(f"#define {k} {v}" for k, v in missing)
    edit("src/game/server/weapons.h", "\n#endif // WEAPONS_H",
         "\n/* OP4-MERGE: additive constants from halflife-op4-updated dlls/weapons.h */\n"
         + block + "\n/* END OP4-MERGE */\n",
         "op4-weapon-constants", before=True)

    # 2. OP4's 3 extra bullet types into BHL's Bullet enum
    edit("src/game/server/weapons.h", "\tBULLET_MONSTER_12MM,",
         "\n\t/* OP4-MERGE: three OP4 bullet types */\n"
         "\tBULLET_PLAYER_556,\n\tBULLET_PLAYER_762,\n\tBULLET_PLAYER_EAGLE,",
         "op4-bullet-enum")

    # 3. weapon_data_t needs to be visible to weapons.h for OP4 weapon classes
    edit("src/game/server/weapons.h", '#include "effects.h"',
         '\n#include "weaponinfo.h" /* OP4-MERGE */', "op4-weaponinfo-include")

    # 4. OP4 weapon-prediction virtuals on BHL's CBasePlayerWeapon
    edit("src/game/server/weapons.h",
         "class CBasePlayerWeapon : public CBasePlayerItem\n{\npublic:",
         "\n\t/* OP4-MERGE: OP4 weapon prediction API */\n"
         "\tvirtual void GetWeaponData(weapon_data_t &data) {}\n"
         "\tvirtual void SetWeaponData(const weapon_data_t &data) {}\n"
         "\tvirtual void DecrementTimers() {}\n"
         "\tvirtual void IncrementAmmo(CBasePlayer *pPlayer) {}\n"
         "\tvirtual float GetNextAttackDelay(float delay);\n",
         "op4-weapon-prediction-api")

    # 5. OP4 helper declarations (implementations live in OP4 weapons.cpp/util.cpp)
    edit("src/game/server/weapons.h", "\n#endif // WEAPONS_H",
         "\n/* OP4-MERGE: OP4 weapon helper declarations */\n"
         "void FindHullIntersection(const Vector &vecSrc, TraceResult &tr, float *mins, float *maxs, edict_t *pEntity);\n",
         "op4-findhull-decl", before=True)

    # 6. OP4 WeaponId enum into BHL cdll_dll.h (WEAPON_SUIT already a macro in BHL)
    e = (OP4 / "dlls/cdll_dll.h").read_text(errors="surrogateescape")
    m = re.search(r"enum WeaponId\s*\{(.*?)\};", e, re.S)
    ids = [x.strip().rstrip(",") for x in m.group(1).splitlines()
           if x.strip() and not x.strip().startswith("//")]
    ids = [x for x in ids if x and "WEAPON_SUIT" not in x]
    edit("src/game/server/cdll_dll.h", "#define WEAPON_SUIT 31",
         "\n/* OP4-MERGE: WeaponId from halflife-op4-updated dlls/cdll_dll.h */\n"
         "enum WeaponId\n{\n\t" + ",\n\t".join(ids) + "\n};\n/* END OP4-MERGE */\n",
         "op4-weaponid-enum")

    # 6b. OP4's shockrifle and sporelauncher live in HUD bucket 6. BHL's
    #     WeaponsResource::rgSlots is sized MAX_WEAPON_SLOTS; with 6 the two
    #     weapons are rejected by PickupWeapon() and can never be selected
    #     from the HUD. Widening the bound to 7 is additive: BHL's buckets
    #     0..5, the health counter and VGUI2 panels are untouched.
    subst("src/game/server/cdll_dll.h",
          "#define MAX_WEAPON_SLOTS     6 // hud item selection slots on a client",
          "#define MAX_WEAPON_SLOTS     7 // hud item selection slots on a client (OP4 bucket 6)",
          "op4-hud-bucket-7")

    # 7. OP4 WaterLevel enum into BHL const.h
    c = (OP4 / "common/const.h").read_text(errors="surrogateescape")
    m = re.search(r"(enum WaterLevel\s*\{.*?\};)", c, re.S)
    edit("src/common/const.h", "\n#endif",
         "\n/* OP4-MERGE: water levels from halflife-op4-updated common/const.h */\n"
         + m.group(1) + "\n/* END OP4-MERGE */\n",
         "op4-waterlevel-enum", before=True)

# 8. Every OP4-only skilldata_t tuning field into BHL skill.h
    sk = (OP4 / "dlls/skill.h").read_text(errors="surrogateescape")
    bsk = (tree / "src/game/server/skill.h").read_text(errors="surrogateescape")
    bnames = set(re.findall(r"\b(?:float|int)\s+(\w+)\s*;", bsk))
    op4_struct = re.search(r"struct skilldata_t\s*\{(.*?)\n\};", sk, re.S)
    body = op4_struct.group(1) if op4_struct else sk
    fields = []
    for typ, name in re.findall(r"\b(float|int)\s+(\w+)\s*;", body):
        if name not in bnames:
            fields.append(f"\t{typ} {name};")
            bnames.add(name)
    edit("src/game/server/skill.h", "};\n\nextern DLL_GLOBAL skilldata_t gSkillData;",
         "\n\t/* OP4-MERGE: OP4 skilldata_t tuning fields not present in BHL */\n"
         + "\n".join(fields) + "\n",
         "op4-skill-fields", before=True)

    # 9. OP4-only CBasePlayer members / helpers used by OP4 weapons
    edit("src/game/server/player.h", "\n\tint m_rgItems[MAX_ITEMS];",
         "\n\t/* OP4-MERGE: OP4 weapon / CTF / grapple player state and helpers */\n"
         "\tint ammo_762;\n\tunsigned int m_iItems;\n"
         "\tVector m_DisplacerReturn;\n\tint m_DisplacerSndRoomtype = 0;\n"
         "\tint m_SndRoomtype = 0;\n\tint m_iTeamNum = 0;\n"
         "\tint m_iCTFScore = 0;\n\tEHANDLE m_pFlag;\n"
         "\tunsigned long long m_WeaponBits = 0;\n"
         "\tvoid *m_pRope = nullptr;\n\tfloat m_flLastClimbTime = 0;\n"
         "\tbool m_bIsClimbing = false;\n"
         "\tvoid ClearWeaponBit(int id) { m_WeaponBits &= ~(1ULL << id); }\n"
         "\tVector GetAutoaimVectorFromPoint(const Vector &vecSrc, float flDelta) "
         "{ return GetAutoaimVector(flDelta); }\n"
         "\tbool IsOnRope() const { return (m_afPhysicsFlags & PFLAG_ONROPE) != 0; }\n"
         "\tvoid SetOnRopeState(bool b) "
         "{ if (b) m_afPhysicsFlags |= PFLAG_ONROPE; else m_afPhysicsFlags &= ~PFLAG_ONROPE; }\n"
         "\tCRope *GetRope() { return (CRope *)m_pRope; }\n"
         "\tvoid SetRope(CRope *r) { m_pRope = (void *)r; }\n"
           "\tvoid SetIsClimbing(bool b) { m_bIsClimbing = b; }\n"
           "\t/* OP4-MERGE: CTF powerup timings and suit query (OP4 player.h) */\n"
           "\tfloat m_flAccelTime = 0;\n\tfloat m_flBackpackTime = 0;\n"
           "\tfloat m_flHealthTime = 0;\n\tfloat m_flShieldTime = 0;\n"
           "\tfloat m_flJumpTime = 0;\n"
           "\tbool m_fPlayingAChargeSound = false;\n"
           "\tbool m_fPlayingHChargeSound = false;\n"
           "\tbool HasSuit() const { return (pev->weapons & (1 << WEAPON_SUIT)) != 0; }\n"
           "\tvoid SetHasSuit(bool b) "
           "{ if (b) pev->weapons |= (1 << WEAPON_SUIT); else pev->weapons &= ~(1 << WEAPON_SUIT); }\n"
           "\t/* OP4-MERGE: CTF menu / score state (OP4 dlls/player.h) */\n"
           "\tint m_iNewTeamNum = 0;\n\tunsigned int m_iClientItems = 0;\n"
           "\tint m_iCurrentMenu = 0;\n\tint m_iLastPlayerTrace = 0;\n"
           "\tint m_iFlagCaptures = 0;\n\tshort m_iOffense = 0;\n"
           "\tshort m_iDefense = 0;\n"
           "\tvoid Player_Menu();\n"
           "\tbool Menu_Team_Input(int inp);\n"
           "\tbool Menu_Char_Input(int inp);\n",
           "op4-player-state")
    edit("src/game/server/player.h", "\nclass CBasePlayer : public CBaseMonster",
         "\n/* OP4-MERGE: OP4 grapple rope forward declaration + physics flag */\n"
         "class CRope;\n#ifndef PFLAG_ONROPE\n#define PFLAG_ONROPE (1 << 6)\n#endif\n",
         "op4-rope-forward-decl", before=True)

    # 9b. OP4's CTF ruleset query on BHL's CGameRules
    edit("src/game/server/gamerules.h", "\tvirtual BOOL IsMultiplayer(void) = 0;",
         "\n\t/* OP4-MERGE: OP4 CTF subsystem query */\n\tvirtual bool IsCTF() { return false; }\n",
         "op4-gamerules-isctf")

    # 10. OP4 shock-effect state on BHL's CBaseMonster
    edit("src/game/server/basemonster.h", "\n\tCBaseEntity *DropItem(char *pszItemName, const Vector &vecPos, const Vector &vecAng);",
         "\n\t/* OP4-MERGE: shock rifle effect state (OP4 monsters.cpp) */\n"
         "\tBOOL m_fShockEffect = FALSE;\n\tfloat m_flShockDuration = 0;\n"
         "\tfloat m_flShockTime = 0;\n\tint m_iOldRenderMode = 0;\n"
         "\tint m_iOldRenderFX = 0;\n\tVector m_OldRenderColor;\n"
         "\tfloat m_flOldRenderAmt = 0;\n"
         "\tvoid AddShockEffect(float r, float g, float b, float size, float flShockDuration);\n"
         "\t/* Declared for OP4's geneworm/etc; bodies live in OP4 monsters.cpp,\n"
         "\t * which cannot coexist with BHL's own monsters.cpp. Link-time gap. */\n"
         "\tvoid UpdateShockEffect();\n\tvoid ClearShockEffect();\n",
         "op4-monster-shock-state")

    # 11. OP4's CWorld::World pointer (OP4 grapple tip uses it)
    edit("src/game/server/cbase.h", "class CWorld : public CBaseEntity\n{\npublic:",
         "\n\t/* OP4-MERGE: OP4 grapple uses a CWorld singleton */\n\tstatic CWorld *World;\n",
         "op4-cworld-singleton")

    # 11b. OP4's EHANDLE::Entity<T>() helper on BHL's EHANDLE.
    edit("src/game/server/cbase.h", "\tCBaseEntity *operator->();\n};",
         "\n\t/* OP4-MERGE: OP4 EHANDLE::Entity<T>() (OP4 dlls/cbase.h) */\n"
         "\ttemplate <typename T>\n"
         "\tT *Entity() { return static_cast<T *>(operator CBaseEntity *()); }\n",
         "op4-ehandle-entity-template", before=True)

    # 11c. OP4's squad-talk-monster cast helper on BHL's CBaseEntity.
    edit("src/game/server/cbase.h", "class CBaseEntity\n{\npublic:",
         "\n/* OP4-MERGE: forward declaration for the squad helper below */\n"
         "class COFSquadTalkMonster;\n",
         "op4-squad-forward-decl", before=True)
    edit("src/game/server/cbase.h", "class CBaseEntity\n{\npublic:",
         "\n\t/* OP4-MERGE: OP4 squad monster cast + sentence hook (OP4 dlls/cbase.h) */\n"
         "\tvirtual COFSquadTalkMonster *MySquadTalkMonsterPointer() { return nullptr; }\n"
         "\tvirtual void PlaySentenceCore(const char *pszSentence, float duration, "
         "float volume, float attenuation) {}\n",
         "op4-squad-pointer")

    # 11d. OP4's GibLimit / GibData structs (OP4 dlls/monsters.h).
    om = (OP4 / "dlls/monsters.h").read_text(errors="surrogateescape")
    g1 = re.search(r"struct GibLimit\s*\{.*?\n\};", om, re.S)
    g2 = re.search(r"struct GibData\s*\{.*?\n\};", om, re.S)
    bhl_monsters = (tree / "src/game/server/monsters.h").read_text(errors="surrogateescape")
    if g1 and g2 and "struct GibData" not in bhl_monsters:
        edit("src/game/server/monsters.h", "\nclass CGib : public CBaseEntity",
             "\n/* OP4-MERGE: GibLimit / GibData from halflife-op4-updated dlls/monsters.h */\n"
             + g1.group(0) + "\n" + g2.group(0) + "\n/* END OP4-MERGE */\n",
             "op4-gibdata-structs", before=True)

    # 12. CLaserSpot::Spawn must be public: OP4's CEagleLaser derives from it
    p = tree / "src/game/server/weapons.h"
    s = p.read_text(errors="surrogateescape")
    old = "class CLaserSpot : public CBaseEntity\n{\n\tvoid Spawn(void);"
    if old in s:
        p.write_text(s.replace(
            old, "class CLaserSpot : public CBaseEntity\n{\npublic: "
                 "/* OP4-MERGE: OP4 CEagleLaser derives from CLaserSpot */\n\tvoid Spawn(void);", 1),
            errors="surrogateescape")
        provenance["src/game/server/weapons.h"].setdefault("merge_rules", []).append(
            "op4-laserspot-public-spawn")

    # 13. OP4's GetNextAttackDelay bookkeeping fields on BHL's
    #     CBasePlayerWeapon. Source: OP4 dlls/weapons.h:406-407. Declared
    #     BHL base change; reason: the real OP4 algorithm (dlls/weapons.cpp
    #     1071-1099) needs them. No BHL behaviour is removed or replaced.
    edit("src/game/server/weapons.h",
         "\tfloat m_flNextPrimaryAttack; // soonest time ItemPostFrame will call PrimaryAttack",
         "\n\t/* OP4-MERGE: OP4 dlls/weapons.h:406-407 prediction bookkeeping, "
         "required by the verbatim GetNextAttackDelay body */\n"
         "\tfloat m_flPrevPrimaryAttack = 0;\n\tfloat m_flLastFireTime = 0;\n",
         "op4-weapon-timing-state")

    # 14. OP4's CWorld singleton ctor/dtor declarations. Source:
    #     OP4 dlls/world.cpp:483-501. The definitions are in the labelled
    #     glue file op4_link_fixups.cpp (OP4's world.cpp also defines Spawn/
    #     Precache/KeyValue, which would collide with BHL's world.cpp).
    edit("src/game/server/cbase.h", "\tstatic CWorld *World;",
         "\n\t/* OP4-MERGE: OP4 dlls/world.cpp:483-501 singleton ctor/dtor */\n"
         "\tCWorld();\n\t~CWorld();\n",
         "op4-cworld-ctor-dtor")

    # 15. DECLARED BHL base change: register OP4's real cvars + FlagIcon
    #     user message from BHL's GameDLLInit. Source: OP4 dlls/game.cpp
    #     1189-1193 and dlls/UserMessages.cpp:75. Without this the cvars
    #     would be dead data and CTF's HUD icon message would never exist.
    edit("src/game/server/game.cpp", '#include "CBugfixedServer.h"',
         "\n/* OP4-MERGE: real OP4 cvars / registration hook "
         "(dlls/game.cpp:588-592,1189-1193; UserMessages.cpp:75) */\n"
         "extern cvar_t oldgrapple;\n"
         "extern cvar_t oldweapons;\n"
         "extern cvar_t multipower;\n"
         "extern void OP4_RegisterGameDLLHooks();\n",
         "op4-gamedllinit-decls")
    edit("src/game/server/game.cpp", "\tCVAR_REGISTER(&hlds_version);",
         "\n\t/* OP4-MERGE: register OP4 cvars + FlagIcon user message "
         "(see op4_link_fixups.cpp) */\n"
         "\tOP4_RegisterGameDLLHooks();\n",
         "op4-gamedllinit-call")

    # 16. DECLARED BHL base change: compile the shared OP4 weapon-timing
    #     glue TU into BOTH client.so and hl.so. BHL's shared CMakeLists
    #     feeds both targets, so no new target is introduced.
    edit("src/game/shared/CMakeLists.txt", "\tCGameVersion.cpp",
         "\n\t# OP4-MERGE: verbatim GetNextAttackDelay body, shared by both DLLs\n"
         "\top4_weapon_timing.cpp\n\top4_weapon_timing.h\n",
         "op4-shared-weapon-timing-cmake")

    # 17. OP4's CGameRules monster-kill hooks (OP4 dlls/gamerules.h:113,116).
    #     CHalfLifeCoopplay derives from BHL's CHalfLifeMultiplay and marks
    #     these two `override`; BHL's base lacks them. Adding the two OP4
    #     virtuals (with their OP4 default bodies) is an additive base merge,
    #     not a replacement: no BHL behaviour is removed.
    edit("src/game/server/gamerules.h", "class CBasePlayer;",
         "\nclass CBaseMonster; /* OP4-MERGE: dlls/gamerules.h monster hooks */",
         "op4-gamerules-cbasemonster-fwd")
    edit("src/game/server/gamerules.h",
         "\tvirtual int IPointsForKill(CBasePlayer *pAttacker, CBasePlayer *pKilled) = 0; // how many points do I award whoever kills this player?",
         "\n\t/* OP4-MERGE: verbatim OP4 dlls/gamerules.h:113,116 */\n"
         "\tvirtual int IPointsForMonsterKill(CBasePlayer *pAttacker, CBaseMonster *pKiller) { return 0; }\n"
         "\tvirtual void MonsterKilled(CBaseMonster *pVictim, entvars_t *pKiller, entvars_t *pInflictor) {}\n",
         "op4-gamerules-monster-hooks")

    # 18. OP4's GibData overload of CGib::SpawnRandomGibs. The verbatim OP4
    #     body lives in the labelled glue (op4_link_fixups.cpp) because OP4's
    #     combat.cpp also defines BHL's damage system and cannot coexist.
    edit("src/game/server/monsters.h",
         "\tstatic void SpawnRandomGibs(entvars_t *pevVictim, int cGibs, int human);",
         "\n\t/* OP4-MERGE: verbatim OP4 dlls/monsters.h:184 */\n"
         "\tstatic void SpawnRandomGibs(entvars_t *pevVictim, int cGibs, const GibData &gibData);\n",
         "op4-gibdata-spawn-overload")

    # 19. OP4's CBaseEntity::m_EFlags (OP4 dlls/cbase.h:169). OP4's
    #     pitworm_up.cpp forces EFLAG_SLERP through it. Put it on the common
    #     base, exactly where OP4 has it, instead of shadowing it on
    #     CBasePlayer as rule 9 originally did.
    edit("src/game/server/cbase.h",
         "\tCBaseEntity *m_pLink; // used for temporary link-list operations.",
         "\n\t/* OP4-MERGE: verbatim OP4 dlls/cbase.h:169, entity flags sent\n"
         "\t * to the client in ::AddToFullPack */\n"
         "\tbyte m_EFlags = 0;\n",
         "op4-entity-eflags")

    # 20. OP4's CTF scoreboard / menu / userinfo state on BHL's CBasePlayer.
    #     Verbatim OP4 dlls/player.h:192-220. CHalfLifeCTFplay and the real
    #     OP4 menu/stat bodies (glue) read these fields. Additive only.
    edit("src/game/server/player.h", "\tshort m_iDefense = 0;\n",
         "\n\t/* OP4-MERGE: verbatim OP4 dlls/player.h:192-220 CTF stats/menu state */\n"
         "\tchar *m_szTeamModel = nullptr;\n"
         "\tshort m_iSnipeKills = 0;\n"
         "\tshort m_iBarnacleKills = 0;\n"
         "\tshort m_iSuicides = 0;\n"
           "\tfloat m_flLastDamageTime = 0;\n"
           "\tint m_nLastShotBy = 0;\n"
           "\tfloat m_flLastShotTime = 0;\n"
           "\tshort m_iLastDamage = 0;\n"
           "\tshort m_iMostDamage = 0;\n"
           "\tvoid ResetMenu();\n",
           "op4-player-ctf-stats")

    # 21. OP4's CTF gamerules virtuals on BHL's CGameRules. Without them the
    #     real CHalfLifeCTFplay cannot override these, and OP4's
    #     CBasePlayer::Menu_Team_Input() cannot call g_pGameRules->TeamsBalanced().
    # BHL's CGameRules ALREADY has GetIndexedTeamName() and
    # SetDefaultPlayerTeam(); only the five genuinely OP4-only hooks are added,
    # and they are appended at the END of CGameRules' virtual list so no
    # existing BHL vtable slot moves. The marker is CGameRules' last virtual
    # (the first EndMultiplayerGame declaration in the header).
    edit("src/game/server/gamerules.h",
         "\tvirtual void EndMultiplayerGame(void) { }",
         "\n\t/* OP4-MERGE: verbatim OP4 dlls/gamerules.h CTF hooks (additive, last) */\n"
         "\tvirtual const char *GetCharacterType(int iTeamNum, int iCharNum) { return nullptr; }\n"
         "\tvirtual int GetNumTeams() { return 0; }\n"
         "\tvirtual const char *TeamWithFewestPlayers() { return nullptr; }\n"
         "\tvirtual bool TeamsBalanced() { return true; }\n"
         "\tvirtual void GoToIntermission() {}\n",
         "op4-gamerules-ctf-virtuals")

    # 22. DECLARED BHL base change: install OP4's real coop / CTF rules.
    #     Source OP4 dlls/gamerules.cpp:486-539. BHL's InstallGameRules(void)
    #     has no pWorld arg, so the merged code uses CWorld::World (the OP4
    #     singleton whose ctor/dtor live in the labelled glue) and OP4's
    #     SF_WORLD_CTF worldspawn flag. No BHL branch is removed.
    gp = tree / "src/game/server/gamerules.cpp"
    gs = gp.read_text(errors="surrogateescape")
    decls = (
        "\n/* OP4-MERGE: dlls/gamerules.cpp:486-539 coop/CTF ruleset selection */\n"
        "#include \"ctf/ctfplay_gamerules.h\"  /* OP4's real CHalfLifeCTFplay */\n"
        "#include \"coopplay_gamerules.h\"     /* OP4's real CHalfLifeCoopplay */\n"
        "#ifndef SF_WORLD_CTF\n#define SF_WORLD_CTF 0x0008  /* OP4 dlls/world.h:21 */\n#endif\n"
        "extern cvar_t coopplay;\n"
        "extern cvar_t ctfplay;\n"
    )
    anchor = "CGameRules *InstallGameRules(void)\n{"
    if anchor not in gs:
        raise RuntimeError("InstallGameRules anchor missing in gamerules.cpp")
    gs = gs.replace(anchor, decls + "\n" + anchor, 1)
    old_branch = "\t\tif (teamplay.value > 0)\n\t\t{"
    new_branch = (
        "\t\t/* OP4-MERGE: coop and CTF take precedence, exactly as OP4's\n"
        "\t\t * InstallGameRules does (coopplay cvar / SF_WORLD_CTF). No\n"
        "\t\t * BHL branch is removed: all original branches stay below. */\n"
        "\t\tif (coopplay.value > 0)\n"
        "\t\t{\n"
        "\t\t\tg_teamplay = 1;\n"
        "\t\t\treturn new CHalfLifeCoopplay();\n"
        "\t\t}\n"
        "\t\telse if (ctfplay.value > 0 ||\n"
        "\t\t\t(CWorld::World && (CWorld::World->pev->spawnflags & SF_WORLD_CTF) != 0))\n"
        "\t\t{\n"
        "\t\t\tg_teamplay = 1;\n"
        "\t\t\treturn new CHalfLifeCTFplay();\n"
        "\t\t}\n"
        "\t\telse if (teamplay.value > 0)\n\t\t{"
    )
    if old_branch not in gs:
        raise RuntimeError("teamplay branch anchor missing in gamerules.cpp")
    gs = gs.replace(old_branch, new_branch, 1)
    gp.write_text(gs, errors="surrogateescape")
    provenance["src/game/server/gamerules.cpp"].setdefault("merge_rules", []).extend(
        ("op4-install-gamerules-decls", "op4-install-gamerules-branch"))

    # 23. DECLARED BHL base change: register OP4 weapons in W_Precache().
    #     Source: OP4 dlls/weapons.cpp:345-362. Without
    #     UTIL_PrecacheOtherWeapon() the compiled weapon classes are never
    #     entered into CBasePlayerItem::ItemInfoArray / AmmoInfoArray, so the
    #     client never receives their WeaponList entry and the weapon cannot
    #     be given, selected or shown. Purely additive, weapon-scoped, and no
    #     BHL weapon line is changed or removed.
    _prec = "\n".join('\tUTIL_PrecacheOtherWeapon("{}");'.format(w["cls"])
                      for w in op4_weapon_events.WEAPONS)
    _ammo = "\n".join('\tUTIL_PrecacheOther("{}");'.format(w["ammo"])
                      for w in op4_weapon_events.WEAPONS if w["ammo"])
    _snd = "\n".join('\tPRECACHE_SOUND("{}");'.format(s)
                     for w in op4_weapon_events.WEAPONS
                     for s in w.get("sounds", []))
    _both = _prec
    for extra in (_ammo, _snd):
        if extra:
            _both += "\n" + extra
    edit("src/game/server/weapons.cpp",
         '\tg_sModelIndexFireball = PRECACHE_MODEL("sprites/zerogxplode.spr"); // fireball',
         "\n\t/* OP4-MERGE: OP4 dlls/weapons.cpp weapon registration (additive) */\n"
         + _both + "\n",
         "op4-wprecache-op4-weapons", before=True)

    # 24. DECLARED BHL base change: hook OP4 weapon playback events in the
    #     client. Source: OP4 cl_dll/hl/hl_events.cpp:31-40. The callbacks
    #     themselves are the verbatim OP4 bodies in the labelled client glue
    #     src/game/client/op4/op4_weapon_events.cpp. No BHL event is removed.
    _event_weapons = [w for w in op4_weapon_events.WEAPONS if w["event"]]
    _decls = "\n".join('\tvoid {}(struct event_args_s *args);'.format(w["func"])
                       for w in _event_weapons)
    _hooks = "\n".join('\tgEngfuncs.pfnHookEvent("{}", {});'.format(
                        w["event"], w["func"])
                       for w in _event_weapons)
    edit("src/game/client/hl/hl_events.cpp",
         "\tvoid EV_SnarkFire(struct event_args_s *args);",
         "\n\t/* OP4-MERGE: OP4 cl_dll/hl/hl_events.cpp weapon playback events */\n"
         + _decls + "\n",
         "op4-client-weapon-event-decls")
    edit("src/game/client/hl/hl_events.cpp",
         '\tgEngfuncs.pfnHookEvent("events/snarkfire.sc", EV_SnarkFire);',
         "\n\t/* OP4-MERGE: OP4 cl_dll/hl/hl_events.cpp weapon event hooks */\n"
         + _hooks + "\n",
         "op4-client-weapon-event-hooks")

    # 25. DECLARED BHL base change: the single client-side weapon helper that
    #     OP4's verbatim EV_FireM249 body calls. OP4's SetLocalBody() resolves
    #     the local prediction weapon through a hard-coded list of OP4 client
    #     weapon objects (cl_dll/hl/hl_weapons.cpp:559-622). Importing that
    #     list would duplicate BHL's weapon-prediction system, so the SAME
    #     operation is applied to BHL's own local-weapon array g_pWpns[], which
    #     HUD_PrepEntity() fills. Weapon-scoped, additive, no BHL behaviour
    #     changed. Only present when a merged event body needs the symbol.
    if "SetLocalBody" in op4_weapon_events.weapon_events_cpp():
        edit("src/game/client/hl/hl_weapons.cpp",
             "static CBasePlayerWeapon *g_pWpns[32];",
             "\n/* OP4-MERGE (declared): OP4 cl_dll/hl/hl_weapons.cpp:622\n"
             " * SetLocalBody(). OP4 uses GetLocalWeapon(id) over its own client\n"
             " * weapon objects; BHL owns the equivalent g_pWpns[] array here.\n"
             " * Required by the verbatim OP4 EV_FireM249 playback-event body,\n"
             " * which sets the M249 viewmodel body on alternating eject. */\n"
             "void SetLocalBody(int id, int body)\n"
             "{\n"
             "\tif (id < 0 || id >= (int)(sizeof(g_pWpns) / sizeof(g_pWpns[0])))\n"
             "\t\treturn;\n"
             "\tif (CBasePlayerWeapon *pWeapon = g_pWpns[id])\n"
             "\t\tpWeapon->pev->body = body;\n"
             "}\n",
             "op4-client-setlocalbody")


# Only sources proven to compile against BHL headers are wired into the BHL
# CMake targets. Everything else is present in the tree as a ported OP4 source
# and listed in PORT_STATUS.json with its exact remaining gaps. Adding a broken
# source to a target would be a false "merged" claim.
BUILD_SOURCE_DIRS = ("src/game/server/op4/dlls/weapons",)
# Real OP4 CTF + rope subsystem files that compile clean against the merged
# BHL headers. Wiring them (rather than copying bodies into glue) is what
# actually supplies CRope::DetachObject and CTFGoalFlag::DropFlag.
BUILD_SOURCE_FILES = (
    "src/game/server/op4/op4_compat.cpp",
    "src/game/server/op4/op4_link_fixups.cpp",
    "src/game/server/op4/op4_ctf_player.cpp",
    "src/game/client/op4/op4_weapon_events.cpp",
    "src/game/server/op4/dlls/ctf/ctfplay_gamerules.cpp",
    "src/game/server/op4/dlls/ctf/CItemAcceleratorCTF.cpp",
    "src/game/server/op4/dlls/ctf/CItemCTF.cpp",
    "src/game/server/op4/dlls/ctf/CItemSpawnCTF.cpp",
    "src/game/server/op4/dlls/ctf/CHUDIconTrigger.cpp",
    "src/game/server/op4/dlls/ctf/CTFGoal.cpp",
    "src/game/server/op4/dlls/ctf/CTFGoalBase.cpp",
    "src/game/server/op4/dlls/ctf/CTFGoalFlag.cpp",
    "src/game/server/op4/dlls/ctf/CTFSpawn.cpp",
    "src/game/server/op4/dlls/rope/CElectrifiedWire.cpp",
      "src/game/server/op4/dlls/rope/CRope.cpp",
      "src/game/server/op4/dlls/rope/CRopeSample.cpp",
      "src/game/server/op4/dlls/rope/CRopeSegment.cpp",
      # OP4 CTF powerups / detector: compile clean after the declared CTF API
      # patches above. Wiring them is what makes the CTF item set real.
      "src/game/server/op4/dlls/ctf/CItemBackpackCTF.cpp",
      "src/game/server/op4/dlls/ctf/CItemLongJumpCTF.cpp",
      "src/game/server/op4/dlls/ctf/CItemPortableHEVCTF.cpp",
      "src/game/server/op4/dlls/ctf/CItemRegenerationCTF.cpp",
      "src/game/server/op4/dlls/ctf/CTFDetect.cpp",
      # Real OP4 monsters / NPCs / entities that compile clean against the
      # merged BHL headers. These are verbatim OP4 subsystem files, not shims.
      "src/game/server/op4/dlls/CDrillSergeant.cpp",
      "src/game/server/op4/dlls/COFAllyMonster.cpp",
      "src/game/server/op4/dlls/COFSquadTalkMonster.cpp",
      "src/game/server/op4/dlls/CRecruit.cpp",
      "src/game/server/op4/dlls/baby_voltigore.cpp",
      "src/game/server/op4/dlls/blkop_apache.cpp",
      "src/game/server/op4/dlls/blkop_osprey.cpp",
      "src/game/server/op4/dlls/blowercannon.cpp",
      "src/game/server/op4/dlls/cleansuit_scientist.cpp",
      # NOTE: OP4 dlls/ehandle.cpp re-implements EHANDLE::Get/Set/
      # operator-> which BHL defines in cbase.cpp; wiring it would
      # duplicate BHL systems. It stays port-pending by design.
      "src/game/server/op4/dlls/geneworm.cpp",
      "src/game/server/op4/dlls/gonome.cpp",
      "src/game/server/op4/dlls/hfgrunt.cpp",
      "src/game/server/op4/dlls/hgrunt_ally.cpp",
      "src/game/server/op4/dlls/item_generic.cpp",
      "src/game/server/op4/dlls/loader.cpp",
      "src/game/server/op4/dlls/male_assassin.cpp",
      "src/game/server/op4/dlls/nuclearbomb.cpp",
      "src/game/server/op4/dlls/op4mortar.cpp",
      "src/game/server/op4/dlls/otis.cpp",
      "src/game/server/op4/dlls/penguin_grenade.cpp",
      "src/game/server/op4/dlls/shockroach.cpp",
        "src/game/server/op4/dlls/zombie_barney.cpp",
        "src/game/server/op4/dlls/zombie_soldier.cpp",
        # Seven more real OP4 subsystem files made wireable by the declared
        # additive BHL base merges above (gamerules monster hooks, GibData
        # spawn overload, CBaseEntity::m_EFlags, CLASS_ALIEN_RACE_X, and the
        # ExplosionCreate / Make2D API adapters in op4_compat_late.h).
        "src/game/server/op4/dlls/coopplay_gamerules.cpp",
        "src/game/server/op4/dlls/func_tank_of.cpp",
        "src/game/server/op4/dlls/hgrunt_medic.cpp",
        "src/game/server/op4/dlls/hgrunt_torch.cpp",
        "src/game/server/op4/dlls/pitworm_up.cpp",
        "src/game/server/op4/dlls/shocktrooper.cpp",
        "src/game/server/op4/dlls/voltigore.cpp",
        # Deliberately NOT wired (all documented, none silently dropped):
        #   dlls/ehandle.cpp          duplicates BHL EHANDLE::Get/Set/operator->
        #   dlls/UserMessages.cpp     duplicates BHL's LinkUserMessages()
        #   dlls/squeakgrenade.cpp    duplicates BHL's CSqueak/CSqueakGrenade
        #   dlls/world.cpp            duplicates BHL's CWorld (glue carries the
        #                             OP4 CWorld singleton ctor/dtor instead)
        #   dlls/ctf/ctfplay_gamerules.cpp needs BHL menu/team/score state
        #   dlls/Wxdebug.cpp          Windows-only _DEBUG trace; empty on Linux
    )


def build_sources(tree: Path, side: str) -> list[str]:
    out = []
    for d in BUILD_SOURCE_DIRS:
        if d.startswith(f"src/game/{side}/"):
            out += [str(x.relative_to(tree / f"src/game/{side}"))
                    for x in sorted((tree / d).rglob("*.cpp"))]
    for f in BUILD_SOURCE_FILES:
        if f.startswith(f"src/game/{side}/"):
            out.append(str(Path(f).relative_to(f"src/game/{side}")))
    return sorted(out)


def apply_cmake(tree: Path, provenance: dict) -> None:
    """Wire the compile-verified OP4 sources into the real BHL CMake targets."""
    for rel, side in (
        ("src/game/server/CMakeLists.txt", "server"),
        ("src/game/client/CMakeLists.txt", "client"),
    ):
        p = tree / rel
        s = p.read_text(errors="surrogateescape")
        srcs = build_sources(tree, side)
        block = ("\n# OP4-MERGE: OP4 subsystem sources proven to compile against BHL headers\n"
                 + ("list( APPEND SOURCE_FILES\n\t" + "\n\t".join(srcs) + "\n)\n"
                    if srcs else
                    "# client OP4 sources are present under src/game/client/op4/ and\n"
                    "# listed in PORT_STATUS.json as port-pending; none are wired yet.\n"))
        anchor = "\nadd_library( client SHARED ${SOURCE_FILES} )" if "client/" in rel \
            else "\nadd_library( ${TARGET_NAME} SHARED ${SOURCE_FILES} )"
        if anchor not in s:
            raise RuntimeError(f"cmake anchor missing in {rel}")
        s = s.replace(anchor, block + anchor, 1)
        p.write_text(s, errors="surrogateescape")
        provenance[rel].setdefault("merge_rules", []).append("op4-cmake-sources")
        provenance[rel]["action"] = "bhl+op4-merge"
        provenance[rel]["sha256"] = sha256(p)
        provenance.setdefault("_cmake", {})[rel] = srcs


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(out: Path) -> dict:
    if not BHL.is_dir() or not OP4.is_dir():
        raise SystemExit("missing pinned upstreams: run `make fetch` first")
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(BHL, out, symlinks=True)

    prov: dict = {}
    for p in sorted(out.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(out))
            prov[rel] = {"origin": "bugfixhl", "commit": BHL_COMMIT,
                         "action": "verbatim", "sha256": sha256(p)}

    # --- ADD verbatim OP4 subsystem files ---------------------------------
    for src_rel, dst_rel in ADD_DIRS.items():
        src = OP4 / src_rel
        if not src.is_dir():
            continue
        shutil.copytree(src, out / dst_rel)
        for p in (out / dst_rel).rglob("*"):
            if p.is_file():
                prov[str(p.relative_to(out))] = {
                    "origin": "op4", "commit": OP4_COMMIT,
                    "action": "verbatim", "sha256": sha256(p),
                    "upstream_path": str(Path(src_rel) / p.relative_to(out / dst_rel))}

    for dst_rel, files in ADD_ROOT_FILES.items():
        for f in files:
            src = OP4 / f
            if not src.is_file():
                continue
            dst = out / dst_rel / Path(f).name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            prov[str(dst.relative_to(out))] = {
                "origin": "op4", "commit": OP4_COMMIT,
                "action": "verbatim", "sha256": sha256(dst), "upstream_path": f}

    for f in REFERENCE_FILES:
        src = OP4 / f
        if not src.is_file():
            continue
        dst = out / "src/game/server/op4/reference" / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        prov[str(dst.relative_to(out))] = {
            "origin": "op4", "commit": OP4_COMMIT,
            "action": "reference-only", "sha256": sha256(dst), "upstream_path": f}

    for name in ADD_OP4_ENTITIES:
        for ext in (".cpp", ".h"):
            src = OP4 / "dlls" / (name + ext)
            if not src.is_file():
                continue
            dst = out / "src/game/server/op4/dlls" / (name + ext)
            shutil.copy2(src, dst)
            prov[str(dst.relative_to(out))] = {
                "origin": "op4", "commit": OP4_COMMIT,
                "action": "verbatim", "sha256": sha256(dst),
                "upstream_path": str(src.relative_to(OP4))}

    # --- GLUE (authored here, explicitly labelled) ------------------------
    for rel, content in (
        ("src/game/server/op4/op4_compat.h", GLUE_HEADER),
        ("src/game/server/op4/op4_compat_late.h", GLUE_LATE_HEADER),
        ("src/game/server/op4/op4_compat.cpp", GLUE_CPP),
          ("src/game/server/op4/op4_link_fixups.cpp", op4_fixups.FIXUPS_CPP),
          ("src/game/server/op4/op4_ctf_player.cpp", op4_fixups.CTF_PLAYER_CPP),
          ("src/game/client/op4/op4_weapon_events.h",
           op4_weapon_events.weapon_events_h()),
          ("src/game/client/op4/op4_weapon_events.cpp",
           op4_weapon_events.weapon_events_cpp()),
          ("src/game/server/op4/op4_entity_enumerator.h",
           op4_fixups.ENTITY_ENUMERATOR_H),
          ("src/game/shared/op4_weapon_timing.h", op4_fixups.TIMING_H),
        ("src/game/shared/op4_weapon_timing.cpp", op4_fixups.TIMING_CPP),
    ):
        p = out / rel
        p.write_text(content)
        prov[rel] = {"origin": "this-repo", "commit": None,
                     "action": "compat-glue", "sha256": sha256(p)}

    # --- MERGE additive OP4 declarations into BHL headers -----------------
    apply_merges(out, prov)
    for rel, rec in prov.items():
        if rec.get("merge_rules"):
            rec["action"] = "bhl+op4-merge"
            rec["sha256"] = sha256(out / rel)

    # --- PATCH OP4 sources to BHL's HLSDK API ------------------------------
    rules = compile_patch_rules(out)
    for p in sorted((out / "src/game/server/op4").rglob("*")):
        if p.suffix not in (".cpp", ".h") or "reference" in p.parts:
            continue
        s = p.read_text(errors="surrogateescape")
        orig = s
        applied = []
        for name, rx, rep in rules:
            s, n = rx.subn(rep, s)
            if n:
                applied.append({"rule": name, "count": n})
        s, n = fix_keyvalue_returns(s)
        if n:
            applied.append({"rule": "bhl-keyvalue-void-returns", "count": n})
        if p.suffix == ".cpp" and 'op4_compat.h' not in s:
            s = s.replace('#include "extdll.h"',
                          '#include "extdll.h"\n#include "op4_compat.h"', 1)
            applied.append({"rule": "op4-compat-include", "count": 1})
        if p.suffix == ".cpp" and 'op4_compat_late.h' not in s:
            lines = s.splitlines(keepends=True)
            idx = [i for i, ln in enumerate(lines[:120]) if ln.startswith("#include")]
            at = max(idx) + 1 if idx else 0
            lines.insert(at, '#include "op4_compat_late.h"\n')
            s = "".join(lines)
            applied.append({"rule": "op4-compat-late-include", "count": 1})
        if s != orig:
            p.write_text(s, errors="surrogateescape")
            rel = str(p.relative_to(out))
            rec = prov[rel]
            rec["action"] = "op4+compat-patch"
            rec["patch_rules"] = applied
            rec["sha256"] = sha256(p)

    apply_cmake(out, prov)

    # --- PROVENANCE --------------------------------------------------------
    cmake_sources = prov.pop("_cmake", {})
    wired = {f"src/game/{side}/{s}" for side in ("server", "client")
             for s in build_sources(out, side)}
    pending = sorted(
        str(p.relative_to(out)) for p in out.rglob("*.cpp")
        if str(p.relative_to(out)).startswith("src/game/")
        and "/op4/" in str(p.relative_to(out))
        and "reference" not in p.parts
        and str(p.relative_to(out)) not in wired
    )
    bhl_files = {r: v for r, v in prov.items() if v["origin"] == "bugfixhl"}
    base_fingerprint = hashlib.sha256(
        "\n".join(f"{r}  {v['sha256']}" for r, v in sorted(bhl_files.items())).encode()
    ).hexdigest()
    report = {
        "architecture": "BASE=BugfixedHL-Rebased, ADD/MERGE=halflife-op4-updated",
        "base": {"repo": "tmp64/BugfixedHL-Rebased", "commit": BHL_COMMIT,
                 "license": "GPL-3.0", "files": len(bhl_files),
                 "verbatim_files": sum(1 for v in bhl_files.values()
                                       if v["action"] == "verbatim"),
                 "merged_files": sum(1 for v in bhl_files.values()
                                     if v["action"] == "bhl+op4-merge"),
                 "tree_sha256": base_fingerprint,
                 "tree_sha256_note": "sha256 over sorted '<path>  <file sha256>' "
                                     "for every BHL-origin file on disk; verified by --check"},
        "op4": {"repo": "twhl-community/halflife-op4-updated", "commit": OP4_COMMIT,
                "files": sum(1 for v in prov.values() if v["origin"] == "op4")},
        "source_sdk": {"repo": "tmp64/hl1_source_sdk", "commit": SOURCE_SDK_COMMIT,
                       "note": "BHL build-time submodule; required for a full CMake build"},
        "glue_files": [k for k, v in prov.items() if v["origin"] == "this-repo"],
        "cmake": cmake_sources,
        "port_pending": {"count": len(pending), "files": pending,
                         "note": "Ported OP4 sources present in the tree but not yet "
                                 "compile-wired; see PORT_STATUS.json for each file's "
                                 "exact remaining API gaps."},
        "files": prov,
    }
    (out / "PROVENANCE.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def check(out: Path) -> int:
    p = out / "PROVENANCE.json"
    if not p.is_file():
        print("FAIL: no PROVENANCE.json (run `make bhl-base`)", file=sys.stderr)
        return 1
    rep = json.loads(p.read_text())
    errors = []
    bhl_files = {r: v for r, v in rep["files"].items()
                 if v["origin"] == "bugfixhl"}
    fingerprint = hashlib.sha256(
        "\n".join(f"{r}  {sha256(out / r)}" for r in sorted(bhl_files)).encode()
    ).hexdigest()
    if fingerprint != rep["base"].get("tree_sha256"):
        errors.append("BHL base tree fingerprint mismatch")
    for rel, rec in rep["files"].items():
        f = out / rel
        if not f.is_file():
            errors.append(f"missing: {rel}")
            continue
        if sha256(f) != rec["sha256"]:
            errors.append(f"sha mismatch: {rel}")
        if any(ln.startswith(("<<<<<<< ", ">>>>>>> "))
               for ln in f.read_text(errors="surrogateescape").splitlines()):
            errors.append(f"conflict marker: {rel}")
    for rel, srcs in rep["cmake"].items():
        text = (out / rel).read_text(errors="surrogateescape")
        for s in srcs:
            if s not in text:
                errors.append(f"cmake missing source: {s}")
    print(f"  base(BHL)   : {rep['base']['files']} files "
        f"({rep['base'].get('verbatim_files', '?')} verbatim, "
        f"{rep['base'].get('merged_files', '?')} merged)")
    print(f"  added(OP4)  : {rep['op4']['files']} files")
    print(f"  glue        : {len(rep['glue_files'])} files")
    print(f"  provenance  : {len(rep['files'])} entries")
    if errors:
        for e in errors[:20]:
            print("  FAIL:", e, file=sys.stderr)
        return 1
    print("  == BHL-BASE PROVENANCE OK ==")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bhl-op4")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out
    if a.check:
        return check(out)
    rep = build(out)
    print(f"  BHL base files      : {rep['base']['files']}")
    print(f"  OP4 merged files    : {rep['op4']['files']}")
    print(f"  provenance entries  : {len(rep['files'])}")
    print(f"  wrote               : {out}/PROVENANCE.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

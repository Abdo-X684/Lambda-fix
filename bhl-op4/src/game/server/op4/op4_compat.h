/* ---------------------------------------------------------------------------
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
#ifndef CLIENT_DLL
  /* BHL's client cl_util.h already defines UnpackRGB() in the global
   * namespace; the client build only needs OP4's declarations, not this
   * definition. Server (CTF) sources still get the verbatim OP4 body. */
  inline void UnpackRGB(int &r, int &g, int &b, unsigned long ulRGB)
  {
      r = (ulRGB & 0xFF0000) >> 16;
      g = (ulRGB & 0xFF00) >> 8;
      b = ulRGB & 0xFF;
  }
#endif

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

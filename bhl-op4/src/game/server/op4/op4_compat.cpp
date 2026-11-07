/* Implementations of the OP4 helpers declared in op4_compat.h.
 * Small, mechanical adapters over real BugfixedHL engine state. */
#include "op4_compat.h"
#include "util.h"
#include "cbase.h"
#include "weapons.h"
#include "player.h"
#include "gamerules.h"
#include "game.h"
#include "op4_compat_late.h"

extern cvar_t oldweapons;

int UTIL_DefaultPlaybackFlags() { return oldweapons.value == 1 ? 0 : FEV_NOTHOST; }
BOOL UTIL_DefaultUseDecrement() { return oldweapons.value == 0; }
BOOL UTIL_UseOldWeapons() { return oldweapons.value != 0; }
bool UTIL_IsMultiplayer() { return g_pGameRules != nullptr && g_pGameRules->IsMultiplayer(); }

/* OP4's CTF ruleset is present in the merged tree but is not BHL's active
 * gamerules yet; see docs/BHL_BASE_MERGE.md "Remaining work". */
  bool UTIL_IsCTF() { return false; }

  /* OP4's UTIL_GetLocalPlayer() returns the first player entity. BHL exposes
   * the same engine state through CBaseEntity::Instance / pfnPEntityOfEntIndex. */
  CBaseEntity *UTIL_GetLocalPlayer()
  {
      return CBaseEntity::Instance(g_engfuncs.pfnPEntityOfEntIndex(1));
  }
  
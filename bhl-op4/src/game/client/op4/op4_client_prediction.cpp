/* ---------------------------------------------------------------------------
 * OP4 -> BugfixedHL-Rebased CLIENT prediction glue (authored here).
 *
 * OP4's cl_dll/hl/hl_weapons.cpp owns giOldWeapons, set from OP4's
 * `OldWeapons` user message. Importing that whole file would replace BHL's
 * own prediction loop and its 14 client weapon objects, so instead the five
 * small helpers OP4 weapon bodies call are implemented here against BHL's
 * client engine state. No BHL system is replaced or disabled.
 *
 * sv_oldweapons is an engine cvar registered by the BHL-based server DLL.
 * 0 (OP4's default) = client-predicted weapons (FEV_NOTHOST / UseDecrement).
 * 1 = server-authoritative weapons. Both DLLs read the same engine cvar, so
 * client and server always agree. If the cvar is not visible on the client
 * yet, prediction mode is assumed, matching the server's default of 0.
 * -------------------------------------------------------------------------*/
#include "extdll.h"
#include "wrect.h"
#include "cl_dll.h"
#include "event_flags.h"
#include "op4_compat.h"

static int OP4_OldWeapons()
{
	cvar_t *cv = gEngfuncs.pfnGetCvarPointer("sv_oldweapons");
	return (cv && cv->value > 0.5f) ? 1 : 0;
}

int UTIL_DefaultPlaybackFlags()
{
	return OP4_OldWeapons() ? 0 : FEV_NOTHOST;
}

BOOL UTIL_DefaultUseDecrement()
{
	return OP4_OldWeapons() ? FALSE : TRUE;
}

BOOL UTIL_UseOldWeapons()
{
	return OP4_OldWeapons() ? TRUE : FALSE;
}

bool UTIL_IsMultiplayer()
{
	return gEngfuncs.GetMaxClients() > 1;
}

bool UTIL_IsCTF()
{
	cvar_t *cv = gEngfuncs.pfnGetCvarPointer("mp_ctfplay");
	return cv && cv->value > 0.5f;
}

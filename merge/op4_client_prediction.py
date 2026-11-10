"""Client-DLL glue for OP4 weapon prediction on the BugfixedHL base.

BHL's client DLL already compiles BHL's *server* weapon .cpp files with
CLIENT_DLL to implement client prediction (see src/game/client/CMakeLists.txt,
`../server/glock.cpp` ...). The nine OP4 weapons that have no server-only
beam/tip entity dependency are compiled the same way. This file supplies only
the five OP4 helpers those weapon bodies call; all weapon logic stays in the
verbatim OP4 sources.
"""

CLIENT_PREDICTION_CPP = r'''/* ---------------------------------------------------------------------------
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
'''

# Nine OP4 weapons are predicted client-side. CGrapple is deliberately
# server-authoritative: its beam/tip entities and EHANDLE helpers are
# server-only, and importing them into the client DLL would require stubbing
# out real OP4 code. Its UseDecrement() is overridden to FALSE instead.
CLIENT_PREDICTED_WEAPONS = (
    "CDisplacer",
    "CEagle",
    "CKnife",
    "CM249",
    "CPenguin",
    "CPipewrench",
    "CShockRifle",
    "CSniperRifle",
    "CSporeLauncher",
)

# (class name, WeaponId enum name) -- ids come from the OP4 WeaponId enum
# merged into BHL's cdll_dll.h.
CLIENT_PREDICTED_IDS = (
    ("CDisplacer", "WEAPON_DISPLACER"),
    ("CEagle", "WEAPON_EAGLE"),
    ("CKnife", "WEAPON_KNIFE"),
    ("CM249", "WEAPON_M249"),
    ("CPenguin", "WEAPON_PENGUIN"),
    ("CPipewrench", "WEAPON_PIPEWRENCH"),
    ("CShockRifle", "WEAPON_SHOCKRIFLE"),
    ("CSniperRifle", "WEAPON_SNIPERRIFLE"),
    ("CSporeLauncher", "WEAPON_SPORELAUNCHER"),
)

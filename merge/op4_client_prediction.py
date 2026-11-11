"""Client-DLL prediction for all ten OP4 weapons on the BugfixedHL base.

BHL's client DLL already compiles BHL's *server* weapon .cpp files with
CLIENT_DLL to implement client prediction (see src/game/client/CMakeLists.txt,
`../server/glock.cpp` ...). OP4's own hl_cdll Makefile and VS project compile
the same ten weapon bodies, plus CGrappleTip.cpp and ehandle.cpp, into its
client DLL. This module reproduces that wiring on BHL without replacing BHL's
prediction loop: the weapon logic stays in the pinned OP4 sources and the glue
below only supplies the OP4 helpers plus two BHL/OP4 header-compatibility
symbols. No BHL system is replaced or disabled.
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
 *
 * OP4's CGrappleTip.cpp and ehandle.cpp are also compiled into this DLL with
 * CLIENT_DLL, exactly as in OP4's own hl_cdll build. OP4's cbase.h declares
 * CWorld::World as an inline static pointer; the merged BHL cbase.h declares
 * it out of line and adds EHANDLE::operator int(). The two definitions below
 * close those two header-only link gaps. They contain no weapon behaviour;
 * CWorld::World is null on the client in OP4 as well.
 *
 * A full OP4 server sends the 64-bit weapon bitmask through the `Weapons`
 * user message instead of writing client_data_t::iWeaponBits. BHL's HUD
 * normally trusts that 32-bit engine field, so this glue hooks the OP4
 * message and records that the authoritative lower 32 bits have arrived.
 * All ten shipped OP4 weapon IDs are below 32; the upper half is read and
 * discarded deliberately. No BHL HUD system is replaced.
 * -------------------------------------------------------------------------*/
#include "extdll.h"
#include "util.h"
#include "cbase.h"
#include "weapons.h"
#include "wrect.h"
#include "cl_dll.h"
#include "hud.h"
#include "parsemsg.h"
#include "event_flags.h"
#include "op4_compat.h"

bool g_bOP4WeaponBits = false;

int OP4_MsgFunc_Weapons(const char *pszName, int iSize, void *pbuf)
{
    BEGIN_READ(pbuf, iSize);
    const int lowerBits = READ_LONG();
    (void)READ_LONG(); // OP4's upper 32 bits; all shipped weapon IDs are < 32.
    gHUD.m_iWeaponBits = lowerBits;
    g_bOP4WeaponBits = true;
    return 1;
}

#ifdef CLIENT_DLL
CWorld *CWorld::World = nullptr;

EHANDLE::operator int()
{
	return Get() != nullptr;
}
#endif

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

# All ten OP4 player weapons are predicted client-side. CGrapple, its tip
# entity and OP4's ehandle.cpp are compiled with CLIENT_DLL exactly as in the
# pinned OP4 client project; no weapon is left server-authoritative.
CLIENT_PREDICTED_WEAPONS = (
    "CDisplacer",
    "CEagle",
    "CGrapple",
    "CKnife",
    "CM249",
    "CPenguin",
    "CPipewrench",
    "CShockRifle",
    "CSniperRifle",
    "CSporeLauncher",
)

# Extra OP4 sources from the pinned reference that OP4's own client DLL also
# compiles; required by the real CGrapple/CGrappleTip bodies.
CLIENT_EXTRA_SOURCES = (
    "../server/op4/dlls/weapons/CGrappleTip.cpp",
    "../server/op4/dlls/ehandle.cpp",
)

# (class name, WeaponId enum name) -- ids come from the OP4 WeaponId enum
# merged into BHL's cdll_dll.h.
CLIENT_PREDICTED_IDS = (
    ("CDisplacer", "WEAPON_DISPLACER"),
    ("CEagle", "WEAPON_EAGLE"),
    ("CGrapple", "WEAPON_GRAPPLE"),
    ("CKnife", "WEAPON_KNIFE"),
    ("CM249", "WEAPON_M249"),
    ("CPenguin", "WEAPON_PENGUIN"),
    ("CPipewrench", "WEAPON_PIPEWRENCH"),
    ("CShockRifle", "WEAPON_SHOCKRIFLE"),
    ("CSniperRifle", "WEAPON_SNIPERRIFLE"),
    ("CSporeLauncher", "WEAPON_SPORELAUNCHER"),
)

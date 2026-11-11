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
 * Weapons, OldWeapon and HudColor messages. Weapons records the authoritative
 * lower 32 bits; OldWeapon overrides the cvar fallback; HudColor is recorded
 * without replacing BHL's VGUI2 colour system. InitHUD/ResetHUD clear this
 * per-server state. All ten shipped OP4 weapon IDs are below 32; the upper
 * half is read and discarded deliberately. No BHL HUD system is replaced.
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
#include <cctype>
#include <cstring>

bool g_bOP4WeaponBits = false;
static int g_iOP4OldWeapons = -1;
static int g_iOP4HudColor[3] = { 0, 0, 0 };

/* OP4 builds AmmoInfoArray in W_Precache() / UTIL_PrecacheOtherWeapon() and
 * uses GetAmmoIndex() to map ammo names to the indices sent in WeaponList and
 * AmmoX. BHL's client had only a one-argument no-op registry and a GetAmmoIndex
 * stub returning -1. This is the OP4 registry semantics reproduced for client
 * prediction; it does not replace BHL's VGUI2 HUD or any BHL weapon. */
AmmoInfo CBasePlayerItem::AmmoInfoArray[MAX_AMMO_SLOTS];
static int g_iOP4AmmoIndex = 0;

static bool OP4_AmmoNameEqual(const char *a, const char *b)
{
    if (!a || !b)
        return false;
    while (*a && *b)
    {
        if (std::tolower((unsigned char)*a) != std::tolower((unsigned char)*b))
            return false;
        ++a;
        ++b;
    }
    return *a == *b;
}

int OP4_GetAmmoIndex(const char *psz)
{
    if (!psz || !*psz)
        return -1;
    for (int i = 0; i < MAX_AMMO_SLOTS; ++i)
    {
        const char *name = CBasePlayerItem::AmmoInfoArray[i].pszName;
        if (name && OP4_AmmoNameEqual(name, psz))
            return i;
    }
    return -1;
}

void OP4_ResetAmmoRegistry()
{
    std::memset(CBasePlayerItem::ItemInfoArray, 0,
                sizeof(CBasePlayerItem::ItemInfoArray));
    std::memset(CBasePlayerItem::AmmoInfoArray, 0,
                sizeof(CBasePlayerItem::AmmoInfoArray));
    g_iOP4AmmoIndex = 0;
}

void AddAmmoNameToAmmoRegistry(const char *szAmmoname, const char *weaponName)
{
    if (!szAmmoname || !*szAmmoname || OP4_GetAmmoIndex(szAmmoname) >= 0)
        return;

    ++g_iOP4AmmoIndex;
    if (g_iOP4AmmoIndex >= MAX_AMMO_SLOTS)
        g_iOP4AmmoIndex = 0;

    AmmoInfo &ammoType = CBasePlayerItem::AmmoInfoArray[g_iOP4AmmoIndex];
    ammoType.pszName = szAmmoname;
    ammoType.iId = g_iOP4AmmoIndex;
    ammoType.WeaponName = weaponName;
}

void OP4_ResetNetworkState()
{
    g_bOP4WeaponBits = false;
    g_iOP4OldWeapons = -1;
    g_iOP4HudColor[0] = g_iOP4HudColor[1] = g_iOP4HudColor[2] = 0;
}

int OP4_MsgFunc_Weapons(const char *pszName, int iSize, void *pbuf)
{
    BEGIN_READ(pbuf, iSize);
    const int lowerBits = READ_LONG();
    (void)READ_LONG(); // OP4's upper 32 bits; all shipped weapon IDs are < 32.
    gHUD.m_iWeaponBits = lowerBits;
    g_bOP4WeaponBits = true;
    return 1;
}

int OP4_MsgFunc_OldWeapon(const char *pszName, int iSize, void *pbuf)
{
    BEGIN_READ(pbuf, iSize);
    g_iOP4OldWeapons = READ_BYTE() != 0 ? 1 : 0;
    return 1;
}

/* OP4's HudColor is recorded but does NOT override BHL's VGUI2 colours. */
int OP4_MsgFunc_HudColor(const char *pszName, int iSize, void *pbuf)
{
    BEGIN_READ(pbuf, iSize);
    g_iOP4HudColor[0] = READ_BYTE();
    g_iOP4HudColor[1] = READ_BYTE();
    g_iOP4HudColor[2] = READ_BYTE();
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
	if (g_iOP4OldWeapons >= 0)
		return g_iOP4OldWeapons;
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

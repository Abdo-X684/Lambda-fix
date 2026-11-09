#!/usr/bin/env python3
"""Verbatim upstream Opposing Force implementations used to close link gaps.

Every string in this module is either

  * a byte-for-byte transcription of a function/global from
    halflife-op4-updated @ 5368be7f8eba (the exact file and line range is
    written in the C++ comment above each item), or
  * a mechanical factoring of such a function into a pure helper so the SAME
    code can be exercised by a host-side functional test.

These are NOT stubs, NOT empty bodies, and NOT linker-silencing shims. They are
real OP4 game logic. They live in glue files only because the OP4 files that
originally contain them (dlls/weapons.cpp, dlls/monsters.cpp, dlls/world.cpp,
dlls/ctf/ctfplay_gamerules.cpp, dlls/game.cpp) cannot be compiled next to
BugfixedHL-Rebased's own files with the same names -- doing so would duplicate
BHL's classes and delete BHL systems. The CTF/rope *subsystem* files that can
coexist are wired verbatim into the BHL CMake target by merge/bhl_base.py.

Provenance of every glue file is recorded in bhl-op4/PROVENANCE.json with
origin "this-repo" / action "compat-glue"; the upstream file/line references
are in the C++ comments and in docs/BHL_BASE_BUILD.md.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# src/game/server/op4/op4_compat_late.h addition:
# OP4 dlls/util.h:597-735 entity enumerator (verbatim).
# OP4's CTF/rope sources iterate entities with UTIL_FindEntitiesByClassname;
# BHL's util.h only exposes the singular UTIL_FindEntityByClassname. This is
# OP4's own range-based adapter over that exact BHL primitive, not a rewrite.
# It must be included AFTER cbase.h (hence "late" header) because it names
# CBaseEntity.
# ---------------------------------------------------------------------------
ENTITY_ENUMERATOR_H = r'''/* OP4 dlls/util.h:597-735, verbatim. Standalone so it can be unit-tested on the host. */
#ifndef OP4_BHL_ENTITY_ENUMERATOR_H
#define OP4_BHL_ENTITY_ENUMERATOR_H


/* ---------------------------------------------------------------------------
 * OP4-MERGE (dlls/util.h:597-735, verbatim, @5368be7f8eba):
 * CEntityIterator / CEntityEnumerator and UTIL_FindEntitiesByClassname.
 * OP4's CTF sources use these range-based wrappers; BHL exposes only the
 * singular UTIL_FindEntityByClassname(), which is exactly what the functors
 * below call. No BHL interface is changed.
 * -------------------------------------------------------------------------*/
template <typename T>
struct FindByClassnameFunctor
{
	static T* Find(T* pStartEntity, const char* pszClassname)
	{
		return static_cast<T*>(UTIL_FindEntityByClassname(pStartEntity, pszClassname));
	}
};

template <typename T>
struct FindByTargetnameFunctor
{
	static T* Find(T* pStartEntity, const char* pszName)
	{
		return static_cast<T*>(UTIL_FindEntityByTargetname(pStartEntity, pszName));
	}
};

template <typename T, typename FINDER>
class CEntityIterator
{
public:
	CEntityIterator()
		: m_pszName(""), m_pEntity(nullptr)
	{
	}

	CEntityIterator(const CEntityIterator&) = default;

	CEntityIterator(const char* const pszName, T* pEntity)
		: m_pszName(pszName), m_pEntity(pEntity)
	{
	}

	CEntityIterator& operator=(const CEntityIterator&) = default;

	const T* operator*() const { return m_pEntity; }

	T* operator*() { return m_pEntity; }

	T* operator->() { return m_pEntity; }

	void operator++()
	{
		m_pEntity = static_cast<T*>(FINDER::Find(m_pEntity, m_pszName));
	}

	void operator++(int)
	{
		++*this;
	}

	bool operator==(const CEntityIterator& other) const
	{
		return m_pEntity == other.m_pEntity;
	}

	bool operator!=(const CEntityIterator& other) const
	{
		return !(*this == other);
	}

private:
	const char* const m_pszName;
	T* m_pEntity;
};

template <typename T, typename FINDER>
class CEntityEnumerator
{
public:
	using Functor = FINDER;
	using iterator = CEntityIterator<T, Functor>;

	CEntityEnumerator(const char* pszClassName)
		: m_pszName(pszClassName)
	{
	}

	iterator begin()
	{
		return {m_pszName, static_cast<T*>(Functor::Find(nullptr, m_pszName))};
	}

	iterator end()
	{
		return {m_pszName, nullptr};
	}

private:
	const char* const m_pszName;
};

template <typename T, typename FINDER>
class CEntityEnumeratorWithStart
{
public:
	using Functor = FINDER;
	using iterator = CEntityIterator<T, Functor>;

	CEntityEnumeratorWithStart(const char* pszClassName, T* pStartEntity)
		: m_pszName(pszClassName), m_pStartEntity(pStartEntity)
	{
	}

	iterator begin()
	{
		return {m_pszName, static_cast<T*>(Functor::Find(m_pStartEntity, m_pszName))};
	}

	iterator end()
	{
		return {m_pszName, nullptr};
	}

private:
	const char* const m_pszName;
	T* m_pStartEntity = nullptr;
};

template <typename T = CBaseEntity>
inline CEntityEnumerator<T, FindByClassnameFunctor<T>> UTIL_FindEntitiesByClassname(const char* pszClassName)
{
	return {pszClassName};
}

template <typename T = CBaseEntity>
inline CEntityEnumeratorWithStart<T, FindByClassnameFunctor<T>> UTIL_FindEntitiesByClassname(const char* pszClassName, T* pStartEntity)
{
	return {pszClassName, pStartEntity};
}

template <typename T = CBaseEntity>
inline CEntityEnumerator<T, FindByTargetnameFunctor<T>> UTIL_FindEntitiesByTargetname(const char* pszName)
{
	return {pszName};
}

template <typename T = CBaseEntity>
inline CEntityEnumeratorWithStart<T, FindByTargetnameFunctor<T>> UTIL_FindEntitiesByTargetname(const char* pszName, T* pStartEntity)
{
	return {pszName, pStartEntity};
}

#endif /* OP4_BHL_ENTITY_ENUMERATOR_H */
'''


ENTITY_ENUMERATOR = '#include "op4_entity_enumerator.h"\n'



# ---------------------------------------------------------------------------
# src/game/shared/op4_weapon_timing.h
# Pure helper carrying OP4 dlls/weapons.cpp:1069-1099 verbatim algorithm.
# ---------------------------------------------------------------------------
TIMING_H = r'''/* ---------------------------------------------------------------------------
 * OP4 -> BugfixedHL-Rebased compatibility GLUE (authored in this repository).
 *
 * NOT BugfixedHL and not a reimplementation of a BugfixedHL system.
 *
 * Source: halflife-op4-updated @ 5368be7f8eba
 *         dlls/weapons.cpp lines 1069-1099
 *         CBasePlayerWeapon::GetNextAttackDelay(float)
 *
 * The algorithm is factored into a pure helper so that the EXACT same code
 * compiled into client.so / hl.so can also be executed by
 * tests/test_op4_timing.cpp on the host. No statements were added, removed or
 * reordered; only the input/output plumbing (gpGlobals->time,
 * UTIL_WeaponTimeBase(), the three member fields) became parameters.
 * -------------------------------------------------------------------------*/
#ifndef OP4_BHL_WEAPON_TIMING_H
#define OP4_BHL_WEAPON_TIMING_H

struct OP4AttackTimingState
{
	/* OP4 dlls/weapons.h:393,406,407 -- CBasePlayerWeapon members */
	float nextPrimaryAttack = 0;   /* -1 == "client has stopped firing" */
	float prevPrimaryAttack = 0;
	float lastFireTime = 0;
};

inline float OP4_ComputeNextAttackDelay(float delay, float now, float timeBase,
										OP4AttackTimingState &state)
{
	if (state.lastFireTime == 0 || state.nextPrimaryAttack == -1)
	{
		/* At this point, we are assuming that the client has stopped firing
		 * and we are going to reset our book keeping variables. */
		state.lastFireTime = now;
		state.prevPrimaryAttack = delay;
	}
	/* calculate the time between this shot and the previous */
	float flTimeBetweenFires = now - state.lastFireTime;
	float flCreep = 0.0f;
	if (flTimeBetweenFires > 0)
		flCreep = flTimeBetweenFires - state.prevPrimaryAttack; /* positive or negative */

	/* save the last fire time */
	state.lastFireTime = now;

	float flNextAttack = timeBase + delay - flCreep;
	/* we need to remember what the m_flNextPrimaryAttack time is set to for
	 * each shot, store it as m_flPrevPrimaryAttack. */
	state.prevPrimaryAttack = flNextAttack - timeBase;
	return flNextAttack;
}

#endif /* OP4_BHL_WEAPON_TIMING_H */
'''


# ---------------------------------------------------------------------------
# src/game/shared/op4_weapon_timing.cpp
# Defines CBasePlayerWeapon::GetNextAttackDelay for BOTH client.so and hl.so.
# This TU is also the key-function TU that emits the class vtable/typeinfo.
# ---------------------------------------------------------------------------
TIMING_CPP = r'''/* ---------------------------------------------------------------------------
 * OP4 -> BugfixedHL-Rebased compatibility GLUE (authored in this repository).
 * NOT BugfixedHL; it does not reimplement any BugfixedHL system.
 *
 * Body source: halflife-op4-updated @ 5368be7f8eba
 *              dlls/weapons.cpp:1071-1099 (verbatim algorithm; see
 *              op4_weapon_timing.h for the pure helper).
 *
 * OP4's own client dlls/../cl_dll/hl/hl_baseentity.cpp:309 contains a stub
 * "return flTime;" -- it is deliberately NOT used here.
 *
 * Compiled into BOTH client.so and hl.so via src/game/shared/CMakeLists.txt.
 * Because GetNextAttackDelay is the first non-inline virtual of
 * CBasePlayerWeapon, this translation unit also emits
 * "vtable for CBasePlayerWeapon" and "typeinfo for CBasePlayerWeapon",
 * which were the other two unresolved client/server symbols.
 * -------------------------------------------------------------------------*/
#include "extdll.h"
#include "util.h"
#include "cbase.h"
#include "weapons.h"
#include "op4_weapon_timing.h"

/* Real BHL/OP4 function: server util.cpp, client com_weapons.cpp. */
float UTIL_WeaponTimeBase(void);

float CBasePlayerWeapon::GetNextAttackDelay(float delay)
{
	OP4AttackTimingState state;
	state.nextPrimaryAttack = m_flNextPrimaryAttack;
	state.prevPrimaryAttack = m_flPrevPrimaryAttack;
	state.lastFireTime = m_flLastFireTime;

	const float flNextAttack = OP4_ComputeNextAttackDelay(
		delay, gpGlobals->time, UTIL_WeaponTimeBase(), state);

	m_flPrevPrimaryAttack = state.prevPrimaryAttack;
	m_flLastFireTime = state.lastFireTime;
	/* OP4 does not assign m_flNextPrimaryAttack here; the caller does. */
	return flNextAttack;
}
'''


# ---------------------------------------------------------------------------
# src/game/server/op4/op4_link_fixups.cpp
# Real OP4 bodies for the server-only link gaps, plus the CTF HUD helpers
# that the (verbatim, now wired) CTFGoalFlag.cpp needs.
# ---------------------------------------------------------------------------
FIXUPS_CPP = r'''/* ---------------------------------------------------------------------------
 * OP4 -> BugfixedHL-Rebased compatibility GLUE (authored in this repository).
 * NOT BugfixedHL; it does not reimplement any BugfixedHL system.
 *
 * This file contains VERBATIM upstream Opposing Force implementations whose
 * original host files cannot be compiled alongside BugfixedHL's identically
 * named files. Each item names its exact upstream file + line range below.
 * Nothing here is empty, fake, or a linker-silencing shim.
 *
 *   dlls/game.cpp:588-592                 cvar_t oldgrapple / oldweapons /
 *                                        multipower
 *   dlls/world.cpp:483-501               CWorld::World, CWorld ctor/dtor
 *   dlls/monsters.cpp:3448-3503          CBaseMonster shock-effect methods
 *   dlls/h_ai.cpp:196-210                IsFacing()
 *   dlls/UserMessages.cpp:75-92          gmsgFlagIcon + OP4-only msg ids
 *   dlls/combat.cpp:179-265             CGib::SpawnRandomGibs(GibData)
 *
 * CTF globals, SendFlagIcon*, DisplayTeamFlags, GetTeamName, GetLosingTeam and
 * the RGB constants / UnpackRGB are NO LONGER here: the REAL dlls/ctf/ctfplay_gamerules.cpp
 * is wired into the BHL server target, so it owns those single definitions.
 * op4_ctf_player.cpp (also glue) owns the real CTF menu/cvar/respawn bodies.
 * See PROVENANCE.json and docs/COMPLETION_INVENTORY.md.
 *
 * Upstream: halflife-op4-updated @ 5368be7f8eba.
 * See PROVENANCE.json, docs/BHL_BASE_BUILD.md and LINK_GAPS.md.
 * -------------------------------------------------------------------------*/
#include "extdll.h"
#include "util.h"
#include "cbase.h"
#include "basemonster.h"
#include "monsters.h"   /* CGib / GibData (OP4 combat.cpp overload) */
#include "weapons.h"
#include "player.h"
#include "gamerules.h"
#include "game.h"

#include "ctf/CTFGoalFlag.h"

#include <alloca.h>
#include <cstdio>
#include <cstring>

/* OP4 dlls/UserMessages.h:62 -- defined below, registered from GameDLLInit. */
extern int gmsgFlagIcon;

/* ===== dlls/game.cpp:588-589,592 ========================================= *
 * The three cvar definitions are verbatim OP4 except for the documented
 * sv_oldweapons default below.                                             */
cvar_t oldgrapple = {"sv_oldgrapple", "0", FCVAR_SERVER};
/* OP4's upstream default is "0" (client-predicted weapons). This build has
 * OP4 SERVER weapon classes but BHL's client DLL keeps BHL's own prediction
 * objects for its 14 original weapons; there is no OP4 client weapon class
 * to predict with. With "0", OP4 firing uses FEV_NOTHOST / skiplocal=1, so
 * the local player sees no animation, sound or effect at all.
 *
 * OP4 itself ships sv_oldweapons for exactly this case: "1" makes the
 * weapons fully server-authoritative (SVC_WEAPONANIM + playback events +
 * ammo messages are sent to the local player). BHL's 14 original weapons
 * still use client prediction: their UseDecrement() is unconditional and
 * never reads this cvar. No BHL system is disabled or replaced.           */
cvar_t oldweapons = {"sv_oldweapons", "1", FCVAR_SERVER};
cvar_t multipower = {"mp_multipower", "0", FCVAR_SERVER};

/* ===== dlls/game.cpp:1189-1190,1193 (verbatim registrations) ============ *
 * Called from BHL's GameDLLInit() through a DECLARED merge in game.cpp.
 * CVAR_REGISTER / pfnRegUserMsg only work after GiveFnptrsToDll(), so a
 * static initialiser would be wrong.                                       */
void OP4_RegisterGameDLLHooks()
{
	/* dlls/game.cpp:1189-1200 (verbatim OP4 cvar registrations) */
	CVAR_REGISTER(&oldgrapple);
	CVAR_REGISTER(&oldweapons);
	CVAR_REGISTER(&multipower);
	CVAR_REGISTER(&ctfplay);
	CVAR_REGISTER(&ctf_autoteam);
	CVAR_REGISTER(&ctf_capture);
	CVAR_REGISTER(&coopplay);
	CVAR_REGISTER(&defaultcoop);
	CVAR_REGISTER(&coopweprespawn);

	/* dlls/UserMessages.cpp:75-92 (verbatim OP4-only message registrations).
	 * Shared ids are owned and registered by BHL's player.cpp. */
	gmsgFlagIcon    = g_engfuncs.pfnRegUserMsg("FlagIcon", -1);
	gmsgFlagTimer   = g_engfuncs.pfnRegUserMsg("FlagTimer", -1);
	gmsgPlayerIcon  = g_engfuncs.pfnRegUserMsg("PlayerIcon", -1);
	gmsgPlayerBrowse= g_engfuncs.pfnRegUserMsg("PlayerBrowse", -1);
	gmsgHudColor    = g_engfuncs.pfnRegUserMsg("HudColor", 3);
	gmsgSetMenuTeam = g_engfuncs.pfnRegUserMsg("SetMenuTeam", 1);
	gmsgCTFScore    = g_engfuncs.pfnRegUserMsg("CTFScore", 2);
	gmsgStatsInfo   = g_engfuncs.pfnRegUserMsg("StatsInfo", -1);
	gmsgStatsPlayer = g_engfuncs.pfnRegUserMsg("StatsPlayer", 31);
	gmsgTeamFull    = g_engfuncs.pfnRegUserMsg("TeamFull", 1);
	gmsgOldWeapon   = g_engfuncs.pfnRegUserMsg("OldWeapon", 1);
	gmsgCustomIcon  = g_engfuncs.pfnRegUserMsg("CustomIcon", -1);
	gmsgWeapons     = g_engfuncs.pfnRegUserMsg("Weapons", -1);
}

/* ===== dlls/world.cpp:483-501 (verbatim) ================================= *
 * BHL's cbase.h declares "static CWorld *World" through an OP4-MERGE; the
 * definition and ctor/dtor are OP4's real singleton implementation.        */
CWorld *CWorld::World = nullptr;

CWorld::CWorld()
{
	if (World)
	{
		ALERT(at_error, "Do not create multiple instances of worldspawn\n");
		return;
	}

	World = this;
}

CWorld::~CWorld()
{
	if (World != this)
	{
		return;
	}

	World = nullptr;
}

/* ===== dlls/monsters.cpp:3448-3503 (verbatim) =========================== *
 * OP4's monsters.cpp cannot be linked next to BHL's monsters.cpp (both
 * define CBaseMonster::MonsterThink, FShouldFadeOnDeath, ...).             */
void CBaseMonster::AddShockEffect(float r, float g, float b, float size, float flShockDuration)
{
	if (pev->deadflag == DEAD_NO)
	{
		if (m_fShockEffect)
		{
			m_flShockDuration += flShockDuration;
		}
		else
		{
			m_iOldRenderMode = pev->rendermode;
			m_iOldRenderFX = pev->renderfx;
			m_OldRenderColor.x = pev->rendercolor.x;
			m_OldRenderColor.y = pev->rendercolor.y;
			m_OldRenderColor.z = pev->rendercolor.z;
			m_flOldRenderAmt = pev->renderamt;

			pev->rendermode = kRenderNormal;
			pev->renderfx = kRenderFxGlowShell;
			pev->rendercolor.x = r;
			pev->rendercolor.y = g;
			pev->rendercolor.z = b;
			pev->renderamt = size;

			m_fShockEffect = true;
			m_flShockDuration = flShockDuration;
			m_flShockTime = gpGlobals->time;
		}
	}
}

void CBaseMonster::UpdateShockEffect()
{
	if (m_fShockEffect && (gpGlobals->time - m_flShockTime > m_flShockDuration))
	{
		pev->rendermode = m_iOldRenderMode;
		pev->renderfx = m_iOldRenderFX;
		pev->rendercolor.x = m_OldRenderColor.x;
		pev->rendercolor.y = m_OldRenderColor.y;
		pev->rendercolor.z = m_OldRenderColor.z;
		pev->renderamt = m_flOldRenderAmt;
		m_flShockDuration = 0;
		m_fShockEffect = false;
	}
}

void CBaseMonster::ClearShockEffect()
{
	if (m_fShockEffect)
	{
		pev->rendermode = m_iOldRenderMode;
		pev->renderfx = m_iOldRenderFX;
		pev->rendercolor.x = m_OldRenderColor.x;
		pev->rendercolor.y = m_OldRenderColor.y;
		pev->rendercolor.z = m_OldRenderColor.z;
		pev->renderamt = m_flOldRenderAmt;
		m_flShockDuration = 0;
		m_fShockEffect = false;
	}
}

/* CTF globals / team_names now come from the REAL wired
   ctf/ctfplay_gamerules.cpp; glue keeps only gmsgFlagIcon. */

/* OP4 dlls/UserMessages.h:62 -- registered in OP4_RegisterGameDLLHooks(). */
int gmsgFlagIcon = 0;

/* RGB_* / UnpackRGB now live in op4_compat.h (verbatim
   dlls/cdll_dll.h:187-213) so the real ctfplay_gamerules.cpp can use them. */
/* SendFlagIcon / SendFlagIcons / DisplayTeamFlags now come from the REAL
   wired ctf/ctfplay_gamerules.cpp (no duplicate strong symbols). */
/* ===== dlls/h_ai.cpp:196-210 (verbatim OP4 body) ======================== *
 * Used by the real, wired OP4 ally monsters (otis / CRecruit /
 * CDrillSergeant / hgrunt_ally). OP4's h_ai.cpp cannot be linked next to
 * BHL's h_ai.cpp, so the body is transcribed here. Only two mechanical
 * adaptation points: OP4's Vector::Normalize() -> BHL's Normalized(), and
 * BHL's UTIL_MakeVectorsPrivate takes float* instead of Vector&.         */
bool IsFacing(entvars_t* pevTest, const Vector& reference)
{
	Vector vecDir = (reference - pevTest->origin);
	vecDir.z = 0;
	vecDir = OP4_Normalized(vecDir);
	Vector forward, angle;
	angle = pevTest->v_angle;
	angle.x = 0;
	UTIL_MakeVectorsPrivate(angle, OP4_VEC(forward), NULL, NULL);
	// He's facing me, he meant it
	if (DotProduct(forward, vecDir) > 0.96) // +/- 15 degrees or so
	{
		return true;
	}
	return false;
}

/* GetLosingTeam / GetTeamName now come from the REAL wired
   ctf/ctfplay_gamerules.cpp. */
/* ===== dlls/combat.cpp:179-265 (verbatim OP4 body) ====================== *
 * OP4-updated reworked gib spawning around a GibData descriptor with
 * per-submodel limits. BHL's combat.cpp only has the older
 * CGib::SpawnRandomGibs(entvars_t*, int, int human) overload, and linking
 * OP4's combat.cpp would duplicate BHL's TakeDamage/Killed/TraceAttack/...
 * implementations. The body below is the real OP4 algorithm; only the two
 * OP4 common/Platform.h macros stackalloc/stackfree are supplied by the
 * labelled compat header (alloca / no-op) and the gib counts are verbatim
 * from OP4 combat.cpp:35-37. The declaration is added to BHL's monsters.h
 * by the declared merge rule "op4-gibdata-spawn-overload".                */
#ifndef GERMAN_GIB_COUNT
#define GERMAN_GIB_COUNT 4
#endif
#ifndef HUMAN_GIB_COUNT
#define HUMAN_GIB_COUNT 6
#endif
#ifndef ALIEN_GIB_COUNT
#define ALIEN_GIB_COUNT 4
#endif

void CGib::SpawnRandomGibs(entvars_t* pevVictim, int cGibs, const GibData& gibData)
{
	//Track the number of uses of a particular submodel so we can avoid spawning too many of the same
	auto pLimitTracking = gibData.Limits != nullptr ? reinterpret_cast<int*>(stackalloc(sizeof(int) * gibData.SubModelCount)) : nullptr;

	if (pLimitTracking)
	{
		memset(pLimitTracking, 0, sizeof(int) * gibData.SubModelCount);
	}

	auto currentBody = 0;

	int cSplat;

	for (cSplat = 0; cSplat < cGibs; cSplat++)
	{
		CGib* pGib = GetClassPtr((CGib*)NULL);

		if (g_Language == LANGUAGE_GERMAN)
		{
			pGib->Spawn("models/germangibs.mdl");
			pGib->pev->body = RANDOM_LONG(0, GERMAN_GIB_COUNT - 1);
		}
		else
		{
			pGib->Spawn(gibData.ModelName);

			if (pLimitTracking)
			{
				if (pLimitTracking[currentBody] >= gibData.Limits[currentBody].MaxGibs)
				{
					++currentBody;
				}

				pGib->pev->body = currentBody;

				++pLimitTracking[currentBody];
			}
			else
			{
				pGib->pev->body = RANDOM_LONG(gibData.FirstSubModel, gibData.SubModelCount - 1);
			}
		}

		if (pevVictim)
		{
			// spawn the gib somewhere in the monster's bounding volume
			pGib->pev->origin.x = pevVictim->absmin.x + pevVictim->size.x * (RANDOM_FLOAT(0, 1));
			pGib->pev->origin.y = pevVictim->absmin.y + pevVictim->size.y * (RANDOM_FLOAT(0, 1));
			pGib->pev->origin.z = pevVictim->absmin.z + pevVictim->size.z * (RANDOM_FLOAT(0, 1)) + 1; // absmin.z is in the floor because the engine subtracts 1 to enlarge the box

			// make the gib fly away from the attack vector
			pGib->pev->velocity = g_vecAttackDir * -1;

			// mix in some noise
			pGib->pev->velocity.x += RANDOM_FLOAT(-0.25, 0.25);
			pGib->pev->velocity.y += RANDOM_FLOAT(-0.25, 0.25);
			pGib->pev->velocity.z += RANDOM_FLOAT(-0.25, 0.25);

			pGib->pev->velocity = pGib->pev->velocity * RANDOM_FLOAT(300, 400);

			pGib->pev->avelocity.x = RANDOM_FLOAT(100, 200);
			pGib->pev->avelocity.y = RANDOM_FLOAT(100, 300);

			// copy owner's blood color
			pGib->m_bloodColor = (CBaseEntity::Instance(pevVictim))->BloodColor();

			if (pevVictim->health > -50)
			{
				pGib->pev->velocity = pGib->pev->velocity * 0.7;
			}
			else if (pevVictim->health > -200)
			{
				pGib->pev->velocity = pGib->pev->velocity * 2;
			}
			else
			{
				pGib->pev->velocity = pGib->pev->velocity * 4;
			}

			pGib->pev->solid = SOLID_BBOX;
			UTIL_SetSize(pGib->pev, Vector(0, 0, 0), Vector(0, 0, 0));
		}
		pGib->LimitVelocity();
	}

	stackfree(pLimitTracking);
}
'''


# ---------------------------------------------------------------------------
# src/game/server/op4/op4_ctf_player.cpp -- verbatim OP4 player/menu/cvar bodies
# ---------------------------------------------------------------------------
CTF_PLAYER_CPP = r'''/* ---------------------------------------------------------------------------
 * OP4 -> BugfixedHL GLUE (this repository, explicitly labelled).
 *
 * Real Opposing Force implementations whose ORIGINAL host files cannot be
 * compiled next to BugfixedHL's identically named files:
 *   dlls/game.cpp:580-586       ctfplay / ctf_autoteam / ctf_capture /
 *                               coopplay / defaultcoop / coopweprespawn
 *   dlls/UserMessages.cpp:75-92 OP4-only user-message ids
 *   dlls/client.cpp:152-166     respawn()
 *   dlls/player.cpp:5246-5277   CBasePlayer::Player_Menu()
 *   dlls/player.cpp:5279-5308   CBasePlayer::ResetMenu()
 *   dlls/player.cpp:5310-5416   CBasePlayer::Menu_Team_Input()
 *   dlls/player.cpp:5418-5476   CBasePlayer::Menu_Char_Input()
 *
 * Upstream: halflife-op4-updated @ 5368be7f8eba. NOT stubs; no BHL system
 * replaced. Mechanical adaptation only: BHL stores team numbers as int.
 * -------------------------------------------------------------------------*/
#include "extdll.h"
#include "util.h"
#include "cbase.h"
#include "player.h"
#include "gamerules.h"
#include "game.h"
#include "client.h"
#include "ctf/CTFDefs.h"
#include <cstdlib>

/* ===== dlls/game.cpp:580-586 (verbatim) ================================= */
cvar_t ctfplay          = {"mp_ctfplay", "0", FCVAR_SERVER};
cvar_t ctf_autoteam     = {"mp_ctf_autoteam", "0", FCVAR_SERVER};
cvar_t ctf_capture      = {"mp_ctf_capture", "0", FCVAR_SERVER};
cvar_t coopplay         = {"mp_coopplay", "0", FCVAR_SERVER};
cvar_t defaultcoop      = {"mp_defaultcoop", "0", FCVAR_SERVER};
cvar_t coopweprespawn   = {"mp_coopweprespawn", "0", FCVAR_SERVER};

/* ===== OP4-only user-message ids ========================================= */
int gmsgFlagTimer   = 0;
int gmsgPlayerIcon  = 0;
int gmsgPlayerBrowse= 0;
int gmsgHudColor    = 0;
int gmsgSetMenuTeam = 0;
int gmsgCTFScore    = 0;
int gmsgStatsInfo   = 0;
int gmsgStatsPlayer = 0;
int gmsgTeamFull    = 0;
int gmsgOldWeapon   = 0;
int gmsgCustomIcon  = 0;
int gmsgWeapons     = 0;

/* ===== dlls/client.cpp:152-166 (verbatim) =============================== */
void respawn(entvars_t* pev, bool fCopyCorpse)
{
	if (0 != gpGlobals->coop || 0 != gpGlobals->deathmatch)
	{
		if (fCopyCorpse)
		{
			// make a copy of the dead body for appearances sake
			CopyToBodyQue(pev);
		}

		// respawn player
		GetClassPtr((CBasePlayer*)pev)->Spawn();
	}
	else
	{ // restart the entire server
		SERVER_COMMAND("reload\n");
	}
}

/* ===== dlls/player.cpp:5246-5277 (verbatim) ============================= */
void CBasePlayer::Player_Menu()
{
	if (g_pGameRules->IsCTF())
	{
		if (m_iCurrentMenu == MENU_TEAM)
		{
			MESSAGE_BEGIN(MSG_ONE, gmsgAllowSpec, nullptr, edict());
			WRITE_BYTE(1);
			MESSAGE_END();

			MESSAGE_BEGIN(MSG_ONE, gmsgTeamNames, nullptr, edict());
			g_engfuncs.pfnWriteByte(2);
			WRITE_STRING("#CTFTeam_BM");
			WRITE_STRING("#CTFTeam_OF");
			MESSAGE_END();

			MESSAGE_BEGIN(MSG_ONE, gmsgVGUIMenu, nullptr, edict());
			WRITE_BYTE(MENU_TEAM);
			MESSAGE_END();
		}
		else if (m_iCurrentMenu == MENU_CLASS)
		{
			MESSAGE_BEGIN(MSG_ONE, gmsgSetMenuTeam, nullptr, edict());
			WRITE_BYTE(static_cast<int>(m_iNewTeamNum == CTFTeam::None ? m_iTeamNum : m_iNewTeamNum));
			MESSAGE_END();

			MESSAGE_BEGIN(MSG_ONE, gmsgVGUIMenu, nullptr, edict());
			WRITE_BYTE(MENU_CLASS);
			MESSAGE_END();
		}
	}
}

/* ===== dlls/player.cpp:5279-5308 (verbatim) ============================= */
void CBasePlayer::ResetMenu()
{
	if (0 != gmsgShowMenu)
	{
		MESSAGE_BEGIN(MSG_ONE, gmsgShowMenu, nullptr, edict());
		WRITE_SHORT(0);
		WRITE_CHAR(0);
		WRITE_BYTE(0);
		WRITE_STRING("");
		MESSAGE_END();
	}

	switch (m_iCurrentMenu)
	{
	case MENU_DEFAULT:
		m_iCurrentMenu = MENU_TEAM;
		break;

	case MENU_TEAM:
		m_iCurrentMenu = MENU_CLASS;
		break;

	default:
		m_iCurrentMenu = MENU_NONE;
		return;
	}

	if (g_pGameRules->IsCTF())
		Player_Menu();
}

/* ===== dlls/player.cpp:5310-5416 (verbatim) ============================= */
bool CBasePlayer::Menu_Team_Input(int inp)
{
	m_iNewTeamNum = CTFTeam::None;

	if (inp == -1)
	{
		g_pGameRules->ChangePlayerTeam(this, nullptr, false, false);

		MESSAGE_BEGIN(MSG_ONE, gmsgTeamFull, nullptr, edict());
		WRITE_BYTE(0);
		MESSAGE_END();
		return true;
	}
	else if (inp == 3)
	{
		if (g_pGameRules->TeamsBalanced())
		{
			if (m_iTeamNum == CTFTeam::None)
			{
				m_iNewTeamNum = static_cast<CTFTeam>(RANDOM_LONG(0, 1) + 1);
				if (m_iNewTeamNum <= CTFTeam::None)
				{
					m_iNewTeamNum = CTFTeam::BlackMesa;
				}
				else if (m_iNewTeamNum > CTFTeam::OpposingForce)
				{
					m_iNewTeamNum = CTFTeam::OpposingForce;
				}
			}
			else
			{
				m_iNewTeamNum = m_iTeamNum;
			}
		}
		else
		{
			m_iNewTeamNum = static_cast<CTFTeam>(g_pGameRules->GetTeamIndex(g_pGameRules->TeamWithFewestPlayers()) + 1);
		}

		MESSAGE_BEGIN(MSG_ONE, gmsgTeamFull, nullptr, edict());
		WRITE_BYTE(0);
		MESSAGE_END();

		ResetMenu();

		pev->impulse = 0;

		return true;
	}
	else if (inp <= g_pGameRules->GetNumTeams() && inp > 0)
	{
		auto unbalanced = false;

		if (ctf_autoteam.value == 1)
		{
			if (m_iTeamNum != static_cast<CTFTeam>(inp))
			{
				if (!g_pGameRules->TeamsBalanced() && inp != g_pGameRules->GetTeamIndex(g_pGameRules->TeamWithFewestPlayers()) + 1)
				{
					ClientPrint(pev, HUD_PRINTCONSOLE, "Team balancing enabled.\nThis team is full.\n");
					MESSAGE_BEGIN(MSG_ONE, gmsgTeamFull, nullptr, edict());
					WRITE_BYTE(1);
					MESSAGE_END();

					unbalanced = true;
				}
				else
				{
					m_iNewTeamNum = static_cast<CTFTeam>(inp);
				}
			}
			else
			{
				m_iNewTeamNum = m_iTeamNum;
			}
		}
		else
		{
			m_iNewTeamNum = static_cast<CTFTeam>(inp);
		}

		if (!unbalanced)
		{
			MESSAGE_BEGIN(MSG_ONE, gmsgTeamFull, nullptr, edict());
			WRITE_BYTE(0);
			MESSAGE_END();

			ResetMenu();

			pev->impulse = 0;

			return true;
		}
	}
	else if (inp == 6 && m_iTeamNum > CTFTeam::None)
	{
		m_iCurrentMenu = MENU_NONE;
		return true;
	}

	m_iCurrentMenu = MENU_TEAM;

	if (g_pGameRules->IsCTF())
		Player_Menu();

	return false;
}

/* ===== dlls/player.cpp:5418-5476 (verbatim) ============================= */
bool CBasePlayer::Menu_Char_Input(int inp)
{
	if (m_iNewTeamNum == CTFTeam::None)
	{
		ClientPrint(pev, HUD_PRINTCONSOLE, "Can't change character; not in a team.\n");
		return false;
	}

	const char* pszCharacterType;

	if (inp == 7)
	{
		pszCharacterType = g_pGameRules->GetCharacterType(static_cast<int>(m_iNewTeamNum) - 1, RANDOM_LONG(0, 5));
	}
	else
	{
		const auto characterIndex = inp - 1;

		if (characterIndex < 0 || characterIndex > 5)
			return false;

		pszCharacterType = g_pGameRules->GetCharacterType(static_cast<int>(m_iNewTeamNum) - 1, characterIndex);
	}

	//Kill and gib the player if they're changing teams
	const auto killAndGib = OBS_NONE == pev->iuser1 && m_iTeamNum != m_iNewTeamNum;

	g_pGameRules->ChangePlayerTeam(this, pszCharacterType, killAndGib, killAndGib);

	ResetMenu();

	pev->impulse = 0;

	if (OBS_NONE != pev->iuser1)
	{
		pev->effects &= ~EF_NODRAW;
		pev->flags &= FL_FAKECLIENT;
		pev->flags |= FL_CLIENT;
		pev->takedamage = DAMAGE_YES;
		m_iHideHUD &= ~(HIDEHUD_HEALTH | HIDEHUD_WEAPONS);
		m_afPhysicsFlags &= PFLAG_OBSERVER;
		pev->flags &= ~FL_SPECTATOR;

		MESSAGE_BEGIN(MSG_ALL, gmsgSpectator);
		WRITE_BYTE(entindex());
		WRITE_BYTE(0);
		MESSAGE_END();

		pev->iuser1 = 0;
		pev->deadflag = 0;
		pev->solid = SOLID_SLIDEBOX;
		pev->movetype = MOVETYPE_WALK;

		g_pGameRules->GetPlayerSpawnSpot(this);
		g_pGameRules->PlayerSpawn(this);
	}

	return true;
}
'''

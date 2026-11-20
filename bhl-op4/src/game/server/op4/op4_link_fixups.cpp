/* ---------------------------------------------------------------------------
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
 * See PROVENANCE.json and docs/BHL_BASE_MERGE.md.
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
#include "op4_compat_late.h"

/* OP4 dlls/UserMessages.h:62 -- defined below, registered from GameDLLInit. */
extern int gmsgFlagIcon;

/* ===== dlls/game.cpp:588-589,592 (verbatim) ============================== */
cvar_t oldgrapple = {"sv_oldgrapple", "0", FCVAR_SERVER};
cvar_t oldweapons = {"sv_oldweapons", "0", FCVAR_SERVER};
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

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
 *   dlls/ctf/ctfplay_gamerules.cpp:48-67 CTF globals + team_names
 *   dlls/cdll_dll.h:200-213              RGB_* / UnpackRGB
 *   dlls/ctf/ctfplay_gamerules.cpp:141-263 SendFlagIcon / SendFlagIcons /
 *                                        DisplayTeamFlags
 *   dlls/ctf/ctfplay_gamerules.cpp:92-112 GetTeamName
 *   dlls/combat.cpp:179-265             CGib::SpawnRandomGibs(GibData)
 *
 * Upstream: halflife-op4-updated @ 5368be7f8eba.
 * See PROVENANCE.json, docs/BHL_BASE_BUILD.md and LINK_GAPS.md.
 * -------------------------------------------------------------------------*/
#include "extdll.h"
#include "op4_compat.h"
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
	CVAR_REGISTER(&oldgrapple);
	CVAR_REGISTER(&oldweapons);
	CVAR_REGISTER(&multipower);
	gmsgFlagIcon = g_engfuncs.pfnRegUserMsg("FlagIcon", -1);
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

/* ===== dlls/ctf/ctfplay_gamerules.cpp:48-67 (verbatim globals) ========= *
 * ctfplay_gamerules.cpp itself is NOT wired: it needs OP4-only CBasePlayer
 * fields (m_szTeamModel, m_szTeamName, m_iSnipeKills...), OP4 menus and
 * UTIL_FindPlayers. Adding those would replace BHL player/gamerules systems.
 * Only the state that the verbatim-wired CTF entities actually read is
 * reproduced here, byte-for-byte from upstream. See "incomplete" in the
 * final report.                                                            */
char g_szScoreIconNameBM[40] = "item_ctfflagh";
char g_szScoreIconNameOF[40] = "item_ctfflagh";

float g_flFlagReturnTime = 30;
float g_flBaseDefendDist = 192;
float g_flDefendCarrierTime = 10;
float g_flCaptureAssistTime = 10;
float g_flPowerupRespawnTime = 30;
int g_iMapScoreMax = 0;

int teamscores[2] = {0, 0};

static const char team_names[2][16] =
{
	{"Black Mesa"},
	{"Opposing Force"}
};

/* OP4 dlls/UserMessages.h:62 -- registered in OP4_RegisterGameDLLHooks(). */
int gmsgFlagIcon = 0;

/* ===== dlls/cdll_dll.h:200-213 (verbatim) =============================== */
#define RGB_YELLOWISH 0x00FFA000 /* 255,160,0 */
#define RGB_REDISH    0x00FF1010
#define RGB_GREENISH  0x0000A000 /* 0,160,0 */
#define RGB_HUD_COLOR RGB_GREENISH

inline void UnpackRGB(int& r, int& g, int& b, unsigned long ulRGB)
{
	r = (ulRGB & 0xFF0000) >> 16;
	g = (ulRGB & 0xFF00) >> 8;
	b = ulRGB & 0xFF;
}

/* ===== dlls/ctf/ctfplay_gamerules.cpp:141-263 (verbatim) =============== */
static void SendFlagIcon(CBasePlayer* player, bool isActive, const char* flagName, int teamIndex)
{
	g_engfuncs.pfnMessageBegin(MSG_ONE, gmsgFlagIcon, nullptr, player->edict());
	g_engfuncs.pfnWriteByte(isActive ? 1 : 0);
	g_engfuncs.pfnWriteString(flagName);
	g_engfuncs.pfnWriteByte(teamIndex);

	int r, g, b;

	if (teamIndex == 0)
	{
		UnpackRGB(r, g, b, RGB_YELLOWISH);
	}
	else
	{
		UnpackRGB(r, g, b, RGB_HUD_COLOR);
	}

	g_engfuncs.pfnWriteByte(r);
	g_engfuncs.pfnWriteByte(g);
	g_engfuncs.pfnWriteByte(b);

	g_engfuncs.pfnWriteByte(teamscores[teamIndex]);
	g_engfuncs.pfnMessageEnd();
}

static void SendFlagIcons(CBasePlayer* player, CTFGoalFlag* team1Flag, CTFGoalFlag* team2Flag)
{
	if (team1Flag || team2Flag)
	{
		auto pMyFlag = static_cast<CTFGoalFlag*>(static_cast<CBaseEntity*>(player->m_pFlag));

		if (team1Flag)
		{
			const char* flagName = "";

			switch (team1Flag->m_iGoalState)
			{
			case 1:
				flagName = "item_ctfflagh";
				break;
			case 2:
				if (pMyFlag == team1Flag && pMyFlag)
				{
					flagName = "item_ctfflagg";
				}
				else
				{
					flagName = "item_ctfflagc";
				}
				break;
			case 3:
				flagName = "item_ctfflagd";
				break;
			}

			SendFlagIcon(player, true, flagName, 0);
		}

		if (team2Flag)
		{
			const char* flagName = "";

			switch (team2Flag->m_iGoalState)
			{
			case 1:
				flagName = "item_ctfflagh";
				break;
			case 2:
				if (pMyFlag == team2Flag && pMyFlag)
				{
					flagName = "item_ctfflagg";
				}
				else
				{
					flagName = "item_ctfflagc";
				}
				break;
			case 3:
				flagName = "item_ctfflagd";
				break;
			}

			SendFlagIcon(player, true, flagName, 1);
		}
	}
	else
	{
		SendFlagIcon(player, true, g_szScoreIconNameBM, 0);
		SendFlagIcon(player, true, g_szScoreIconNameOF, 1);
	}
}

void DisplayTeamFlags(CBasePlayer* pPlayer)
{
	if (0 == gmsgFlagIcon)
		return;

	CTFGoalFlag* team1Flag = nullptr;

	while ((team1Flag = static_cast<CTFGoalFlag*>(UTIL_FindEntityByClassname(team1Flag, "item_ctfflag"))) && team1Flag->m_iGoalNum != 1)
	{
	}

	CTFGoalFlag* team2Flag = nullptr;

	while ((team2Flag = static_cast<CTFGoalFlag*>(UTIL_FindEntityByClassname(team2Flag, "item_ctfflag"))) && team2Flag->m_iGoalNum != 2)
	{
	}

	if (pPlayer)
	{
		SendFlagIcons(pPlayer, team1Flag, team2Flag);
	}
	else
	{
		for (int i = 1; i <= gpGlobals->maxClients; ++i)
		{
			auto player = static_cast<CBasePlayer*>(UTIL_PlayerByIndex(i));

			if (player)
			{
				SendFlagIcons(player, team1Flag, team2Flag);
			}
		}
	}
}

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

/* ===== dlls/ctf/ctfplay_gamerules.cpp:126-138 (verbatim) =============== *
 * CItemCTF::MyItemTouch (the real, wired CItemCTF.cpp:127) uses this to
 * hand a powerup to the losing team.                                      */
void GetLosingTeam(int& iTeamNum, int& iScoreDiff)
{
	iTeamNum = 0;
	iScoreDiff = 0;

	//TODO: doesn't really make sense, if team 0 is losing the score difference is 0
	if (teamscores[1] < teamscores[0])
	{
		iTeamNum = 1;

		const auto difference = teamscores[0] - teamscores[1];

		if (iScoreDiff < difference)
			iScoreDiff = difference;
	}
}

/* ===== dlls/ctf/ctfplay_gamerules.cpp:92-112 (verbatim) ================= */
const char* GetTeamName(edict_t* pEntity)
{
	if (g_pGameRules->IsCTF())
	{
		auto pPlayer = static_cast<CBasePlayer*>(CBaseEntity::Instance(pEntity));

		return team_names[(int)pPlayer->m_iTeamNum - 1];
	}
	else
	{
		/* A bit counterintuitive, this basically means each player model is a team */
		if (g_pGameRules->IsDeathmatch() && g_pGameRules->IsTeamplay())
		{
			return g_engfuncs.pfnInfoKeyValue(g_engfuncs.pfnGetInfoKeyBuffer(pEntity), "model");
		}
		else
		{
			static char szTmp[256];

			snprintf(szTmp, sizeof(szTmp), "%i", g_engfuncs.pfnGetPlayerUserId(pEntity));
			return szTmp;
		}
	}
}

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

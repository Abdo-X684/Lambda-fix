/* ---------------------------------------------------------------------------
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
#include "op4_compat.h"
#include "util.h"
#include "cbase.h"
#include "player.h"
#include "gamerules.h"
#include "game.h"
#include "client.h"
#include "ctf/CTFDefs.h"
#include <cstdlib>
#include "op4_compat_late.h"

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
			if (m_iTeamNum == (int)CTFTeam::None)
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

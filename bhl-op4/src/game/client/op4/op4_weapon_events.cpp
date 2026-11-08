/* ---------------------------------------------------------------------------
 * OP4 -> BHL CLIENT WEAPON-EVENT GLUE (authored in this repository).
 *
 * VERBATIM OP4 cl_dll/ev_hldm.cpp playback-event callbacks. Every body
 * below is extracted from the pinned upstream at generation time; the
 * exact function name and upstream file are written above each one.
 * These are real weapon effects, not stubs and not simulations.
 *
 * Wiring cl_dll/ev_hldm.cpp itself is impossible: it also defines BHL's
 * own EV_FireGlock1 / EV_FireMP5 / ... and would duplicate symbols.
 * -------------------------------------------------------------------------*/
/* ../  = BHL src/game/client/. Quoted includes search THIS file's
 * directory first, and src/game/client/op4/ contains OP4's own
 * ev_hldm.h / eventscripts.h, which would shadow BHL's headers and
 * conflict with BHL ev_common.cpp's definitions. */
#include "../hud.h"
#include "../cl_util.h"
#include "../cl_dll.h"
#include "const.h"
#include "entity_state.h"
#include "cl_entity.h"
#include "entity_types.h"
#include "usercmd.h"
#include "pm_defs.h"
#include "pm_materials.h"
#include "../eventscripts.h"
#include "../ev_hldm.h"
#include "r_efx.h"
#include "event_api.h"
#include "event_args.h"
#include "in_defs.h"
#include "r_studioint.h"
#include "com_model.h"
#include "op4_weapon_events.h"

/* BHL client helpers used by the verbatim OP4 bodies. */
void V_PunchAxis(int axis, float punch);
/* Declared OP4-MERGE in BHL src/game/client/hl/hl_weapons.cpp:
 * the same operation as OP4's SetLocalBody(), against BHL's own
 * local-weapon array. Required by the verbatim EV_FireM249 body. */
void SetLocalBody(int id, int body);
/* OP4 cl_dll/ev_hldm.cpp:1653 - OP4-only pipewrench swing counter. */
int g_iClub;
/* BHL src/game/client/ev_hldm.cpp:1183 already owns g_iSwing
 * (same name and purpose as OP4's). Reference it, do not duplicate. */
extern int g_iSwing;

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_FireEagle (verbatim) ===== */
extern "C" void EV_FireEagle(event_args_t *args);
void EV_FireEagle(event_args_t* args)
{
	const bool bEmpty = args->bparam1 != 0;

	Vector up, right, forward;

	AngleVectors(args->angles, forward, right, up);

	const int iShell = gEngfuncs.pEventAPI->EV_FindModelIndex("models/shell.mdl");

	if (EV_IsLocal(args->entindex))
	{
		EV_MuzzleFlash();

		gEngfuncs.pEventAPI->EV_WeaponAnimation(bEmpty ? EAGLE_SHOOT_EMPTY : EAGLE_SHOOT, 0);
		V_PunchAxis(0, -4.0);
	}

	Vector ShellVelocity;
	Vector ShellOrigin;

	EV_GetDefaultShellInfo(
		args,
		args->origin, args->velocity,
		ShellVelocity,
		ShellOrigin,
		forward, right, up,
		-9.0, 14.0, 9.0);

	EV_EjectBrass(ShellOrigin, ShellVelocity, args->angles[1], iShell, TE_BOUNCE_SHELL);

	gEngfuncs.pEventAPI->EV_PlaySound(
		args->entindex,
		args->origin, CHAN_WEAPON, "weapons/desert_eagle_fire.wav",
		gEngfuncs.pfnRandomFloat(0.92, 1), ATTN_NORM, 0, 98 + gEngfuncs.pfnRandomLong(0, 3));

	Vector vecSrc;

	EV_GetGunPosition(args, vecSrc, args->origin);

	Vector vecAiming = forward;

	EV_HLDM_FireBullets(
		args->entindex,
		forward, right, up,
		1,
		vecSrc, vecAiming,
		8192.0,
		BULLET_PLAYER_EAGLE,
		0, nullptr,
		args->fparam1, args->fparam2);
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_Pipewrench (verbatim) ===== */
extern "C" void EV_Pipewrench(event_args_t *args);
void EV_Pipewrench(event_args_t* args)
{
	const int idx = args->entindex;
	Vector origin = args->origin;
	const bool iBigSwing = 0 != args->bparam1;
	const bool hitSomething = 0 != args->bparam2;

	if (!EV_IsLocal(idx))
	{
		return;
	}

	//Play Swing sound
	if (iBigSwing)
	{
		if (hitSomething)
		{
			gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_BIG_SWING_HIT, 0);
		}
		else
		{
			gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_BIG_SWING_MISS, 0);
		}

		gEngfuncs.pEventAPI->EV_PlaySound(idx, origin, CHAN_WEAPON, "weapons/pwrench_big_miss.wav", 1, ATTN_NORM, 0, PITCH_NORM);
	}
	else
	{
		if (hitSomething)
		{
			switch (g_iClub % 3)
			{
			case 0:
				gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_ATTACK1HIT, 0);
				break;
			case 1:
				gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_ATTACK2HIT, 0);
				break;
			case 2:
				gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_ATTACK3HIT, 0);
				break;
			}
		}
		else
		{
			switch (g_iClub % 3)
			{
			case 0:
				gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_ATTACK1MISS, 0);
				break;
			case 1:
				gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_ATTACK2MISS, 0);
				break;
			case 2:
				gEngfuncs.pEventAPI->EV_WeaponAnimation(PIPEWRENCH_ATTACK3MISS, 0);
				break;
			}

			switch (g_iClub % 2)
			{
			case 0:
				gEngfuncs.pEventAPI->EV_PlaySound(idx, origin, CHAN_WEAPON, "weapons/pwrench_miss1.wav", 1, ATTN_NORM, 0, PITCH_NORM);
				break;
			case 1:
				gEngfuncs.pEventAPI->EV_PlaySound(idx, origin, CHAN_WEAPON, "weapons/pwrench_miss2.wav", 1, ATTN_NORM, 0, PITCH_NORM);
				break;
			}
		}

		++g_iClub;
	}
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_FireM249 (verbatim) ===== */
extern "C" void EV_FireM249(event_args_t *args);
void EV_FireM249(event_args_t* args)
{
	int iBody = args->iparam1;

	const bool bAlternatingEject = args->bparam1 != 0;

	Vector up, right, forward;

	AngleVectors(args->angles, forward, right, up);

	int iShell =
		bAlternatingEject ? gEngfuncs.pEventAPI->EV_FindModelIndex("models/saw_link.mdl") : gEngfuncs.pEventAPI->EV_FindModelIndex("models/saw_shell.mdl");

	if (EV_IsLocal(args->entindex))
	{
		SetLocalBody(WEAPON_M249, iBody);
		EV_MuzzleFlash();
		gEngfuncs.pEventAPI->EV_WeaponAnimation(gEngfuncs.pfnRandomLong(0, 2) + M249_SHOOT1, iBody);
		V_PunchAxis(0, gEngfuncs.pfnRandomFloat(-2, 2));
		V_PunchAxis(1, gEngfuncs.pfnRandomFloat(-1, 1));
	}

	Vector ShellVelocity;
	Vector ShellOrigin;

	EV_GetDefaultShellInfo(
		args,
		args->origin, args->velocity,
		ShellVelocity,
		ShellOrigin,
		forward, right, up,
		-28.0, 24.0, 4.0);

	EV_EjectBrass(ShellOrigin, ShellVelocity, args->angles[1], iShell, TE_BOUNCE_SHELL);

	gEngfuncs.pEventAPI->EV_PlaySound(
		args->entindex,
		args->origin, CHAN_WEAPON, "weapons/saw_fire1.wav",
		VOL_NORM, ATTN_NORM, 0, 94 + gEngfuncs.pfnRandomLong(0, 15));

	Vector vecSrc;

	EV_GetGunPosition(args, vecSrc, args->origin);

	Vector vecAiming = forward;

	EV_HLDM_FireBullets(
		args->entindex,
		forward, right, up,
		1,
		vecSrc, vecAiming,
		8192.0,
		BULLET_PLAYER_556,
		0, nullptr,
		args->fparam1, args->fparam2);
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_FireDisplacer (verbatim) ===== */
extern "C" void EV_FireDisplacer(event_args_t *args);
void EV_FireDisplacer(event_args_t* args)
{
	const auto mode = static_cast<DisplacerMode>(args->iparam1);

	switch (mode)
	{
	case DisplacerMode::SPINNING_UP:
	{
		int iAttach = 0;

		int iStartAttach, iEndAttach;

		for (size_t uiIndex = 0; uiIndex < DISPLACER_NUM_BEAMS; ++uiIndex)
		{
			if (iAttach <= 2)
			{
				iStartAttach = iAttach++ + 2;
				iEndAttach = iAttach % 2 + 2;
			}
			else
			{
				iStartAttach = 0;
				iEndAttach = 0;
			}

			gEngfuncs.pEfxAPI->R_BeamEnts(
				args->entindex | (iStartAttach << 12), args->entindex | (iEndAttach << 12),
				gEngfuncs.pEventAPI->EV_FindModelIndex("sprites/lgtning.spr"),
				1,
				1, 60 * 0.01, 190 / 255.0, 30, 0, 10,
				96 / 255.0, 128 / 255.0, 16 / 255.0);
		}

		break;
	}

	case DisplacerMode::FIRED:
	{
		//bparam1 indicates whether it's a primary or secondary attack. - Solokiller
		if (0 == args->bparam1)
		{
			gEngfuncs.pEventAPI->EV_PlaySound(
				args->entindex, args->origin,
				CHAN_WEAPON, "weapons/displacer_fire.wav",
				gEngfuncs.pfnRandomFloat(0.8, 0.9), ATTN_NORM, 0, PITCH_NORM);
		}
		else
		{
			gEngfuncs.pEventAPI->EV_PlaySound(
				args->entindex, args->origin,
				CHAN_WEAPON, "weapons/displacer_self.wav",
				gEngfuncs.pfnRandomFloat(0.8, 0.9), ATTN_NORM, 0, PITCH_NORM);
		}

		if (EV_IsLocal(args->entindex))
		{
			gEngfuncs.pEventAPI->EV_WeaponAnimation(DISPLACER_FIRE, 0);
			V_PunchAxis(0, -2);
		}

		break;
	}

	default:
		break;
	}
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_FireShockRifle (verbatim) ===== */
extern "C" void EV_FireShockRifle(event_args_t *args);
void EV_FireShockRifle(event_args_t* args)
{
	gEngfuncs.pEventAPI->EV_PlaySound(args->entindex, args->origin, CHAN_WEAPON, "weapons/shock_fire.wav", 0.9, ATTN_NORM, 0, PITCH_NORM);

	if (EV_IsLocal(args->entindex))
		gEngfuncs.pEventAPI->EV_WeaponAnimation(SHOCKRIFLE_FIRE, 0);

	for (size_t uiIndex = 0; uiIndex < 3; ++uiIndex)
	{
		gEngfuncs.pEfxAPI->R_BeamEnts(
			args->entindex | 0x1000, args->entindex | ((uiIndex + 2) << 12),
			gEngfuncs.pEventAPI->EV_FindModelIndex("sprites/lgtning.spr"),
			0.08,
			1, 75 * 0.01, 190 / 255.0, 30, 0, 10,
			0, 253 / 255.0, 253 / 255.0);
	}
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_FireSpore (verbatim) ===== */
extern "C" void EV_FireSpore(event_args_t *args);
void EV_FireSpore(event_args_t* args)
{
	gEngfuncs.pEventAPI->EV_PlaySound(
		args->entindex, args->origin,
		CHAN_WEAPON, "weapons/splauncher_fire.wav",
		0.9,
		ATTN_NORM, 0, PITCH_NORM);

	if (EV_IsLocal(args->entindex))
	{
		gEngfuncs.pEventAPI->EV_WeaponAnimation(SPLAUNCHER_FIRE, 0);

		V_PunchAxis(0, -3.0);

		if (cl_entity_t* pViewModel = gEngfuncs.GetViewModel())
		{
			Vector vecSrc = pViewModel->attachment[1];

			Vector forward;

			AngleVectors(args->angles, forward, nullptr, nullptr);

			gEngfuncs.pEfxAPI->R_Sprite_Spray(
				vecSrc, forward,
				gEngfuncs.pEventAPI->EV_FindModelIndex("sprites/tinyspit.spr"),
				10, 10, 180);
		}
	}
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_SniperRifle (verbatim) ===== */
extern "C" void EV_SniperRifle(event_args_t *args);
void EV_SniperRifle(event_args_t* args)
{
	const int idx = args->entindex;
	Vector vecOrigin = args->origin;
	Vector vecAngles = args->angles;

	const int iClip = args->iparam1;

	Vector up, right, forward;

	AngleVectors(vecAngles, forward, right, up);

	if (EV_IsLocal(idx))
	{
		EV_MuzzleFlash();
		gEngfuncs.pEventAPI->EV_WeaponAnimation(iClip <= 0 ? SNIPERRIFLE_FIRELASTROUND : SNIPERRIFLE_FIRE, 0);
		V_PunchAxis(0, -2.0);
	}

	gEngfuncs.pEventAPI->EV_PlaySound(idx, vecOrigin,
		CHAN_WEAPON, "weapons/sniper_fire.wav",
		gEngfuncs.pfnRandomFloat(0.9f, 1.0f), ATTN_NORM, 0, 98 + gEngfuncs.pfnRandomLong(0, 3));

	Vector vecSrc;
	Vector vecAiming = forward;

	EV_GetGunPosition(args, vecSrc, vecOrigin);

	EV_HLDM_FireBullets(
		idx,
		forward,
		right,
		up,
		1,
		vecSrc,
		vecAiming,
		8192.0,
		BULLET_PLAYER_762,
		0,
		0,
		args->fparam1,
		args->fparam2);
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_Knife (verbatim) ===== */
extern "C" void EV_Knife(event_args_t *args);
void EV_Knife(event_args_t* args)
{
	const int idx = args->entindex;
	Vector origin = args->origin;

	const char* pszSwingSound;

	switch (g_iSwing)
	{
	default:
	case 0:
		pszSwingSound = "weapons/knife1.wav";
		break;
	case 1:
		pszSwingSound = "weapons/knife2.wav";
		break;
	case 2:
		pszSwingSound = "weapons/knife3.wav";
		break;
	}

	//Play Swing sound
	gEngfuncs.pEventAPI->EV_PlaySound(idx, origin, CHAN_WEAPON, pszSwingSound, 1, ATTN_NORM, 0, PITCH_NORM);

	if (EV_IsLocal(idx))
	{
		switch ((g_iSwing++) % 3)
		{
		case 0:
			gEngfuncs.pEventAPI->EV_WeaponAnimation(KNIFE_ATTACK1MISS, 0);
			break;
		case 1:
			gEngfuncs.pEventAPI->EV_WeaponAnimation(KNIFE_ATTACK2, 0);
			break;
		case 2:
			gEngfuncs.pEventAPI->EV_WeaponAnimation(KNIFE_ATTACK3, 0);
			break;
		}
	}
}

/* ===== OP4 cl_dll/ev_hldm.cpp : EV_PenguinFire (verbatim) ===== */
extern "C" void EV_PenguinFire(event_args_t *args);
void EV_PenguinFire(event_args_t* args)
{
	Vector origin = args->origin;
	Vector angles = args->angles;
	Vector forward;
	gEngfuncs.pfnAngleVectors(angles, forward, nullptr, nullptr);

	if (EV_IsLocal(args->entindex))
	{
		if (0 != args->ducking)
			origin.z += 18;

		gEngfuncs.pEventAPI->EV_PushPMStates();
		gEngfuncs.pEventAPI->EV_SetSolidPlayers(args->entindex - 1);
		gEngfuncs.pEventAPI->EV_SetTraceHull(2);

		Vector start = origin + (forward * 20);
		Vector end = origin + (forward * 64);

		pmtrace_t tr;
		gEngfuncs.pEventAPI->EV_PlayerTrace(start, end, PM_NORMAL, -1, &tr);

		if (0 == tr.allsolid && 0 == tr.startsolid && tr.fraction > 0.25)
			gEngfuncs.pEventAPI->EV_WeaponAnimation(PENGUIN_THROW, 0);

		gEngfuncs.pEventAPI->EV_PopPMStates();
	}
}


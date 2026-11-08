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

void V_PunchAxis(int axis, float punch);

/* Third-party/BHL client helpers used by the verbatim bodies. */

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


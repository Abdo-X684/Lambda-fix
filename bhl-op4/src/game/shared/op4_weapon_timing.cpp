/* ---------------------------------------------------------------------------
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

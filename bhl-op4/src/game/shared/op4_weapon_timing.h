/* ---------------------------------------------------------------------------
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

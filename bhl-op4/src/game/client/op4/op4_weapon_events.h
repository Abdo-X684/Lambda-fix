/* ---------------------------------------------------------------------------
 * OP4 -> BHL CLIENT WEAPON-EVENT GLUE (authored in this repository).
 *
 * Verbatim animation enums from the pinned OP4 weapon headers. OP4's
 * cl_dll/ev_hldm.cpp includes the SERVER weapon headers for these
 * constants; that cannot be done in BHL's client target, so only the
 * enum blocks (no classes, no server headers) are reproduced here.
 * Upstream: halflife-op4-updated @ 5368be7f8eba.
 * -------------------------------------------------------------------------*/
#pragma once
#include <cstddef>

/* dlls/weapons/CEagle.h : DesertEagleAnim (verbatim) */
enum DesertEagleAnim
{
	EAGLE_IDLE1 = 0,
	EAGLE_IDLE2,
	EAGLE_IDLE3,
	EAGLE_IDLE4,
	EAGLE_IDLE5,
	EAGLE_SHOOT,
	EAGLE_SHOOT_EMPTY,
	EAGLE_RELOAD_NOSHOT,
	EAGLE_RELOAD,
	EAGLE_DRAW,
	EAGLE_HOLSTER
};

/* dlls/weapons/CPipewrench.h : pipewrench_e (verbatim) */
enum pipewrench_e
{
	PIPEWRENCH_IDLE1 = 0,
	PIPEWRENCH_IDLE2,
	PIPEWRENCH_IDLE3,
	PIPEWRENCH_DRAW,
	PIPEWRENCH_HOLSTER,
	PIPEWRENCH_ATTACK1HIT,
	PIPEWRENCH_ATTACK1MISS,
	PIPEWRENCH_ATTACK2HIT,
	PIPEWRENCH_ATTACK2MISS,
	PIPEWRENCH_ATTACK3HIT,
	PIPEWRENCH_ATTACK3MISS,
	PIPEWRENCH_BIG_SWING_START,
	PIPEWRENCH_BIG_SWING_HIT,
	PIPEWRENCH_BIG_SWING_MISS,
	PIPEWRENCH_BIG_SWING_IDLE
};

/* OP4-MERGE bullet ids (verbatim OP4 dlls/weapons.h Bullet enum tail).
 * BHL's client ev_hldm.h stops at BULLET_MONSTER_12MM; these extend it
 * without editing that stable header: EV_HLDM_DecalGunshot/CheckTracer
 * already handle unknown ids through their `default` branch. */
enum OP4BulletType
{
	BULLET_PLAYER_556 = 9,
	BULLET_PLAYER_762 = 10,
	BULLET_PLAYER_EAGLE = 11,
};


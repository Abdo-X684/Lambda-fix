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


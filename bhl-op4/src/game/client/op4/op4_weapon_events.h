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

/* dlls/weapons/CM249.h : M249Anim (verbatim) */
enum M249Anim
{
	M249_SLOWIDLE = 0,
	M249_IDLE2,
	M249_RELOAD_START,
	M249_RELOAD_END,
	M249_HOLSTER,
	M249_DRAW,
	M249_SHOOT1,
	M249_SHOOT2,
	M249_SHOOT3
};

/* dlls/weapons/CDisplacer.h : DisplacerAnim (verbatim) */
enum DisplacerAnim
{
	DISPLACER_IDLE1 = 0,
	DISPLACER_IDLE2,
	DISPLACER_SPINUP,
	DISPLACER_SPIN,
	DISPLACER_FIRE,
	DISPLACER_DRAW,
	DISPLACER_HOLSTER1
};

/* dlls/weapons/CDisplacer.h : DisplacerMode (verbatim) */
enum class DisplacerMode
{
	STARTED = 0,
	SPINNING_UP,
	SPINNING,
	FIRED
};

/* dlls/weapons/CDisplacer.h (verbatim) */
static const size_t DISPLACER_NUM_BEAMS = 4;

/* dlls/weapons/CShockRifle.h : ShockRifleAnim (verbatim) */
enum ShockRifleAnim
{
	SHOCKRIFLE_IDLE1 = 0,
	SHOCKRIFLE_FIRE,
	SHOCKRIFLE_DRAW,
	SHOCKRIFLE_HOLSTER,
	SHOCKRIFLE_IDLE3
};

/* dlls/weapons/CSporeLauncher.h : SporeLauncherAnim (verbatim) */
enum SporeLauncherAnim
{
	SPLAUNCHER_IDLE = 0,
	SPLAUNCHER_FIDGET,
	SPLAUNCHER_RELOAD_REACH,
	SPLAUNCHER_RELOAD,
	SPLAUNCHER_AIM,
	SPLAUNCHER_FIRE,
	SPLAUNCHER_HOLSTER1,
	SPLAUNCHER_DRAW1,
	SPLAUNCHER_IDLE2
};

/* dlls/weapons/CSniperRifle.h : SniperRifleAnim (verbatim) */
enum SniperRifleAnim
{
	SNIPERRIFLE_DRAW = 0,
	SNIPERRIFLE_SLOWIDLE,
	SNIPERRIFLE_FIRE,
	SNIPERRIFLE_FIRELASTROUND,
	SNIPERRIFLE_RELOAD1,
	SNIPERRIFLE_RELOAD2,
	SNIPERRIFLE_RELOAD3,
	SNIPERRIFLE_SLOWIDLE2,
	SNIPERRIFLE_HOLSTER
};

/* dlls/weapons/CKnife.h : KnifeAnim (verbatim) */
enum KnifeAnim
{
	KNIFE_IDLE1 = 0,
	KNIFE_DRAW,
	KNIFE_HOLSTER,
	KNIFE_ATTACK1,
	KNIFE_ATTACK1MISS,
	KNIFE_ATTACK2,
	KNIFE_ATTACK2HIT,
	KNIFE_ATTACK3,
	KNIFE_ATTACK3HIT,
	KNIFE_IDLE2,
	KNIFE_IDLE3,
	KNIFE_CHARGE,
	KNIFE_STAB
};

/* dlls/weapons/CPenguin.h : PenguinAnim (verbatim) */
enum PenguinAnim
{
	PENGUIN_IDLE1 = 0,
	PENGUIN_FIDGETFIT,
	PENGUIN_FIDGETNIP,
	PENGUIN_DOWN,
	PENGUIN_UP,
	PENGUIN_THROW,
};

/* dlls/weapons/CGrapple.h : BarnacleGrappleAnim (verbatim) */
enum BarnacleGrappleAnim
{
	BGRAPPLE_BREATHE = 0,
	BGRAPPLE_LONGIDLE,
	BGRAPPLE_SHORTIDLE,
	BGRAPPLE_COUGH,
	BGRAPPLE_DOWN,
	BGRAPPLE_UP,
	BGRAPPLE_FIRE,
	BGRAPPLE_FIREWAITING,
	BGRAPPLE_FIREREACHED,
	BGRAPPLE_FIRETRAVEL,
	BGRAPPLE_FIRERELEASE
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


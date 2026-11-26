#!/usr/bin/env python3
"""Patch func_pushable in a prepared OP4 server tree.

The OP4 server DLL that ships in the package is built from the pinned
``halflife-op4-updated`` tree, not from ``bhl-op4``. Any fix for pushables has
to be applied to that tree or it never reaches the player.

Why this patch exists
---------------------
HL25 (build 8684) broke ``func_pushable`` for every mod built on this SDK.
``CPushable::Move`` adds an impulse that is scaled by ``frametime``, while the
engine applies player friction once per frame. The two do not cancel, so above
roughly 60 fps the box's velocity decays to zero and the box cannot be moved.
ValveSoftware/halflife#3639 documents the symptom; the only community
workarounds are ``sv_pushable_fixed_tick_fudge 15000`` or ``fps_max 60``,
neither of which is a fix.

What this patch changes
-----------------------
Velocity assignment replaces accumulate-and-decay, and the box drives itself
from its own think instead of depending on the engine delivering a touch to a
``MOVETYPE_PUSHSTEP`` entity:

* ``PushThink()`` runs every frame and finds a player overlapping the box.
* USE held -> pull: the box keeps pace with the player at ``MaxSpeed``.
* USE free -> push: the box takes the player's velocity, capped at ``MaxSpeed``.
* ``Touch()`` stays as a fast path but is no longer required for movement.
* ``Move()`` is kept as a thin wrapper over ``DriveFromToucher()``.

Player friction cannot eat an assigned velocity the way it ate an accumulated
impulse, so the result is the same at 60 fps and at 300 fps.

Usage
-----
    python tools/patch_op4_pushable.py --tree build/op4-msvc
    python tools/patch_op4_pushable.py --check        # verify against the cache
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / ".cache/upstreams/op4/dlls/func_break.cpp"

# ---------------------------------------------------------------------------
# 1. class member declarations
# ---------------------------------------------------------------------------
CLASS_OLD = """	void Use(CBaseEntity* pActivator, CBaseEntity* pCaller, USE_TYPE useType, float value) override;
	void EXPORT StopSound();
"""
CLASS_NEW = """	void Use(CBaseEntity* pActivator, CBaseEntity* pCaller, USE_TYPE useType, float value) override;
	void EXPORT StopSound();

	/* LF-PUSHABLE: self-driven push/pull. HL25 applies player friction every
	 * frame while CPushable::Move adds an impulse scaled by frametime, so above
	 * ~60 fps a box's velocity decays to nothing and it cannot be moved
	 * (ValveSoftware/halflife#3639). Driving the box from its own think and
	 * assigning velocity instead of accumulating it is framerate independent
	 * and removes any reliance on the engine delivering a touch to a
	 * MOVETYPE_PUSHSTEP entity. */
	void EXPORT PushThink();
	void DriveFromToucher(CBaseEntity* pOther, bool push);
	CBaseEntity* FindTouchingEntity();
"""

# ---------------------------------------------------------------------------
# 2. start the think in Spawn()
# ---------------------------------------------------------------------------
SPAWN_OLD = """	pev->skin = (pev->skin * (pev->maxs.x - pev->mins.x) * (pev->maxs.y - pev->mins.y)) * 0.0005;
	m_soundTime = 0;
}
"""
SPAWN_NEW = """	pev->skin = (pev->skin * (pev->maxs.x - pev->mins.x) * (pev->maxs.y - pev->mins.y)) * 0.0005;
	m_soundTime = 0;

	/* LF-PUSHABLE: run our own movement loop. */
	SetThink(&CPushable::PushThink);
	pev->nextthink = gpGlobals->time + 0.05f;
}
"""

# ---------------------------------------------------------------------------
# 3. Use() -> pull
# ---------------------------------------------------------------------------
USE_OLD = """	if (pActivator->pev->velocity != g_vecZero)
		Move(pActivator, false);
}
"""
USE_NEW = """	/* LF-PUSHABLE: the original only moved the box when the player already had
	 * velocity, and Move() with push == false multiplies its factor by
	 * frametime, so a pull shrank to nothing at high frame rates. Drive the box
	 * directly instead. */
	if ((pActivator->pev->button & IN_USE) == 0)
		return;

	if (useType != USE_SET)
		return;

	DriveFromToucher(pActivator, false);

	/* Keep the pull alive every frame even if the engine never sends another
	 * touch for this box. */
	pev->nextthink = gpGlobals->time;
	SetThink(&CPushable::PushThink);
}
"""

# ---------------------------------------------------------------------------
# 4. Touch() -> hint only
# ---------------------------------------------------------------------------
TOUCH_OLD = """	if (FClassnameIs(pOther->pev, "worldspawn"))
		return;

	Move(pOther, true);
}
"""
TOUCH_NEW = """	if (FClassnameIs(pOther->pev, "worldspawn"))
		return;

	/* LF-PUSHABLE: touch is only a hint. PushThink() drives the box, so a
	 * missed touch no longer means a stuck box. */
	DriveFromToucher(pOther, true);
}
"""

# ---------------------------------------------------------------------------
# 5. Move() -> DriveFromToucher(), plus PushThink()/FindTouchingEntity(),
#    plus a Move() wrapper so any other caller keeps working.
# ---------------------------------------------------------------------------
MOVE_BEGIN = "void CPushable::Move(CBaseEntity* pOther, bool push)\n{"
STOP_SOUND_BEGIN = "#if 0\nvoid CPushable::StopSound()"

REPLACEMENT = r'''/* LF-PUSHABLE: velocity is assigned, not accumulated. The old code did
 *     pev->velocity += pevToucher->velocity * factor
 * every frame, which fought the friction the engine applies per frame. Setting
 * the box speed directly to the pusher's speed (capped by MaxSpeed) gives the
 * same result at 60 fps and at 300 fps. */
void CPushable::DriveFromToucher(CBaseEntity* pOther, bool push)
{
	entvars_t* pevToucher = pOther->pev;
	bool playerTouch = false;

	// Is entity standing on this pushable ?
	if (FBitSet(pevToucher->flags, FL_ONGROUND) && pevToucher->groundentity && VARS(pevToucher->groundentity) == pev)
	{
		// Only push if floating
		if (pev->waterlevel > 0)
			pev->velocity.z += pevToucher->velocity.z * 0.1;

		return;
	}

	if (pOther->IsPlayer())
		playerTouch = true;

	float factor;

	if (playerTouch)
	{
		if ((pevToucher->flags & FL_ONGROUND) == 0) // Don't push away from jumping/falling players unless in water
		{
			if (pev->waterlevel < 1)
				return;
			else
				factor = 0.1f;
		}
		else
			factor = 1.0f;
	}
	else
		factor = 0.25f;

	float flSpeed = sqrt(pevToucher->velocity.x * pevToucher->velocity.x + pevToucher->velocity.y * pevToucher->velocity.y) * factor;

	if (flSpeed > MaxSpeed())
		flSpeed = MaxSpeed();

	if (flSpeed > 0.0f)
	{
		float flVelLength = sqrt(pevToucher->velocity.x * pevToucher->velocity.x + pevToucher->velocity.y * pevToucher->velocity.y);

		if (flVelLength > 0.0f)
		{
			pev->velocity.x = (pevToucher->velocity.x / flVelLength) * flSpeed;
			pev->velocity.y = (pevToucher->velocity.y / flVelLength) * flSpeed;
		}
	}

	if (playerTouch && push)
	{
		// Match the player to the box so the player is slowed by it instead of
		// walking straight through the contact.
		pevToucher->velocity.x = pev->velocity.x;
		pevToucher->velocity.y = pev->velocity.y;
	}

	if (playerTouch && (gpGlobals->time - m_soundTime) > 0.7)
	{
		m_soundTime = gpGlobals->time;

		if (flSpeed > 0.0f && FBitSet(pev->flags, FL_ONGROUND))
		{
			m_lastSound = RANDOM_LONG(0, 2);
			EMIT_SOUND(ENT(pev), CHAN_WEAPON, m_soundNames[m_lastSound], 0.5, ATTN_NORM);
		}
		else
			STOP_SOUND(ENT(pev), CHAN_WEAPON, m_soundNames[m_lastSound]);
	}
}

/* LF-PUSHABLE: find a player overlapping our bounding box, so push and pull do
 * not depend on the engine delivering a touch to a MOVETYPE_PUSHSTEP entity. */
CBaseEntity* CPushable::FindTouchingEntity()
{
	Vector vecCenter = (pev->absmin + pev->absmax) * 0.5f;
	float flRadius = (pev->absmax - pev->absmin).Length() * 0.5f + 16.0f;

	CBaseEntity* pEntity = nullptr;

	while ((pEntity = UTIL_FindEntityInSphere(pEntity, vecCenter, flRadius)) != nullptr)
	{
		if (pEntity == this || !pEntity->IsPlayer())
			continue;

		if (!pEntity->IsAlive())
			continue;

		// Bounding box overlap test.
		if (pEntity->pev->absmin.x > pev->absmax.x || pEntity->pev->absmax.x < pev->absmin.x)
			continue;

		if (pEntity->pev->absmin.y > pev->absmax.y || pEntity->pev->absmax.y < pev->absmin.y)
			continue;

		if (pEntity->pev->absmin.z > pev->absmax.z + 8.0f || pEntity->pev->absmax.z < pev->absmin.z)
			continue;

		return pEntity;
	}

	return nullptr;
}

void CPushable::PushThink()
{
	if (FBitSet(pev->flags, FL_KILLME) || pev->solid == SOLID_NOT)
		return;

	CBaseEntity* pPlayer = FindTouchingEntity();

	if (pPlayer != nullptr)
	{
		if ((pPlayer->pev->button & IN_USE) != 0)
		{
			/* Pull: the box keeps pace with the player. */
			float flPlayerSpeed = sqrt(pPlayer->pev->velocity.x * pPlayer->pev->velocity.x + pPlayer->pev->velocity.y * pPlayer->pev->velocity.y);

			if (flPlayerSpeed > 1.0f)
			{
				float flSpeed = flPlayerSpeed;

				if (flSpeed > MaxSpeed())
					flSpeed = MaxSpeed();

				pev->velocity.x = (pPlayer->pev->velocity.x / flPlayerSpeed) * flSpeed;
				pev->velocity.y = (pPlayer->pev->velocity.y / flPlayerSpeed) * flSpeed;
			}
			else
			{
				pev->velocity.x = 0.0f;
				pev->velocity.y = 0.0f;
			}

			if ((gpGlobals->time - m_soundTime) > 0.7)
			{
				m_soundTime = gpGlobals->time;

				if (flPlayerSpeed > 1.0f && FBitSet(pev->flags, FL_ONGROUND))
				{
					m_lastSound = RANDOM_LONG(0, 2);
					EMIT_SOUND(ENT(pev), CHAN_WEAPON, m_soundNames[m_lastSound], 0.5, ATTN_NORM);
				}
			}
		}
		else
		{
			/* Push: the box takes the player's velocity. */
			DriveFromToucher(pPlayer, true);
		}
	}

	pev->nextthink = gpGlobals->time;
}

/* LF-PUSHABLE: wrapper so any remaining caller gets the framerate independent
 * behaviour instead of the old accumulate-and-decay code. */
void CPushable::Move(CBaseEntity* pOther, bool push)
{
	if (pOther == nullptr)
		return;

	DriveFromToucher(pOther, push);
}

'''


def patch_text(text: str) -> tuple[str, list[str]]:
    errors: list[str] = []

    def sub(old: str, new: str, label: str) -> None:
        nonlocal text
        count = text.count(old)
        if count != 1:
            errors.append(f"{label}: expected 1 match, found {count}")
            return
        text = text.replace(old, new, 1)

    sub(CLASS_OLD, CLASS_NEW, "class declarations")
    sub(SPAWN_OLD, SPAWN_NEW, "Spawn()")
    sub(USE_OLD, USE_NEW, "Use()")
    sub(TOUCH_OLD, TOUCH_NEW, "Touch()")

    begin = text.find(MOVE_BEGIN)
    end = text.find(STOP_SOUND_BEGIN)

    if begin < 0:
        errors.append("Move(): definition not found")
    elif end < 0:
        errors.append("StopSound(): marker not found")
    elif end < begin:
        errors.append("StopSound() marker precedes Move()")
    else:
        text = text[:begin] + REPLACEMENT + text[end:]

    return text, errors


def verify_text(text: str) -> list[str]:
    errors: list[str] = []

    for needle, label in (
        ("void CPushable::PushThink()", "PushThink()"),
        ("void CPushable::DriveFromToucher(", "DriveFromToucher()"),
        ("CBaseEntity* CPushable::FindTouchingEntity()", "FindTouchingEntity()"),
        ("SetThink(&CPushable::PushThink);", "Spawn think hook"),
        ("DriveFromToucher(pActivator, false);", "Use pull hook"),
        ("DriveFromToucher(pOther, true);", "Touch hint hook"),
    ):
        if needle not in text:
            errors.append(f"missing {label}")

    # The old accumulate-and-decay body must be gone.
    if "factor *= gpGlobals->frametime * sv_pushable_fixed_tick_fudge.value;" in text:
        errors.append("old frametime-scaled impulse still present")

    if "sv_pushable_fixed_tick_fudge" in text:
        errors.append("sv_pushable_fixed_tick_fudge still referenced")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", type=Path,
                    help="prepared OP4 server tree (contains dlls/func_break.cpp)")
    ap.add_argument("--check", action="store_true",
                    help="patch the pinned upstream copy in memory and verify")
    args = ap.parse_args()

    if args.check:
        if not UPSTREAM.is_file():
            raise SystemExit(f"missing {UPSTREAM} (run: python -m merge.cli fetch)")
        text = UPSTREAM.read_text(encoding="utf-8")
        patched, errors = patch_text(text)
        if errors:
            print("patch failed:", *errors, sep="\n  ")
            return 1
        errors = verify_text(patched)
        if errors:
            print("verify failed:", *errors, sep="\n  ")
            return 1
        print("func_pushable patch OK (dry run against the pinned upstream)")
        return 0

    if not args.tree:
        raise SystemExit("pass --tree <dir> or --check")

    target = args.tree / "dlls/func_break.cpp"
    if not target.is_file():
        raise SystemExit(f"missing {target} (run: python tools/prepare_op4_msvc_server.py)")

    text = target.read_text(encoding="utf-8")

    if "LF-PUSHABLE" in text:
        print(f"{target} already patched")
        return 0

    patched, errors = patch_text(text)
    if errors:
        print("patch failed:", *errors, sep="\n  ")
        return 1

    errors = verify_text(patched)
    if errors:
        print("verify failed:", *errors, sep="\n  ")
        return 1

    target.write_text(patched, encoding="utf-8")
    print(f"patched {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

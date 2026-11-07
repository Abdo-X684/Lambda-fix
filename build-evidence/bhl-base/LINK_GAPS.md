# Unresolved symbols that this build must still supply

Engine-provided symbols (tier0/vstdlib, SDL2, Steam, libc/libm, C++ ABI) are excluded here; the complete list is in `UNDEFINED_SYMBOLS.txt`. These are real link gaps, not hidden errors.

## client.so

- `CBasePlayerWeapon::GetNextAttackDelay(float)`
- `typeinfo for CBasePlayerWeapon`
- `vtable for CBasePlayerWeapon`
## hl.so

- `CBaseMonster::AddShockEffect(float, float, float, float, float)`
- `CBasePlayerWeapon::GetNextAttackDelay(float)`
- `CRope::DetachObject()`
- `CTFGoalFlag::DropFlag(CBasePlayer*)`
- `CWorld::World`
- `oldgrapple`
- `oldweapons`
- `typeinfo for CBasePlayerWeapon`
- `vtable for CBasePlayerWeapon`

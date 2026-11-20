# Required GoldSrc test table

> **There is no GoldSrc engine in this environment.** No in-game test was run here.
> No row is marked as passing until the user tests it on their machine and documents the result.
> The user's report that the game starts with the wrong music and broken weapons is recorded as a bug, not as a pass.

| Item | Server logic | Client prediction | HUD/ammo | Reload | Fire | Animation | Sound | Effects | Model | In-game result |
|---|---|---|---|---|---|---|---|---|---|---|
| Desert Eagle | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Pipe Wrench | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| M249 | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Displacer | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Shock Rifle / weapon_shockroach alias | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Spore Launcher | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Sniper Rifle | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Knife | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Penguin | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Grapple | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | **not tested** |
| Original intro music | — | — | — | — | — | — | copied from `gearbox/media` only | — | — | **not tested** |
| Map music `trigger_cdaudio` | external OP4 maps | — | — | — | — | — | copied from `gearbox/media` only | — | — | **not tested** |
| `of0a0` / `ofboot0` campaign | OP4 server | — | — | — | — | — | — | — | external maps | **not tested** |
| BHL VGUI2 menus | — | BHL client | — | — | — | — | — | — | — | **not tested** |
| `impulse 101` for the ten weapons | OP4 server source | — | — | — | — | — | — | — | — | **not tested** |

## Test protocol for the user

1. Unzip into `Half-Life/lambda-fix/` next to `valve/` and `gearbox/`, then run `setup_op4_media.bat` once.
2. Run `hl.exe -game lambda-fix -console`; record the start of `of0a0`, the intro music, and the music of the first `trigger_cdaudio`.
3. `sv_cheats 1; impulse 101`; for each weapon: select it, HUD icon/ammo, fire, empty magazine, reload, switch away/to, sound, view/world model, effects.
4. Special tests: Grapple on a valid surface; Penguin and watch `monster_penguin`; Displacer primary/secondary/self-teleport; Shock Rifle primary/secondary and recharge.
5. Record video/console for each row. Until then every row stays **not tested**, and nothing is called 'working'.

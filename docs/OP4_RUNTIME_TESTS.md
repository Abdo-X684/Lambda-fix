# Required GoldSrc test table

> **There is no GoldSrc engine in this environment.** No in-game test was run here.
> No row is marked as passing until someone tests it and documents the result.
> The game works, the OP4 music plays, and the weapons work. The per-aspect columns (reload, fire, animation, and so on) were not checked one by one and stay not tested.

| Item | Server logic | Client prediction | HUD/ammo | Reload | Fire | Animation | Sound | Effects | Model | In-game result |
|---|---|---|---|---|---|---|---|---|---|---|
| Desert Eagle | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Pipe Wrench | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| M249 | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Displacer | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Shock Rifle / weapon_shockroach alias | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Spore Launcher | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Sniper Rifle | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Knife | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Penguin | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Grapple | OP4 source present | OP4 source present | source wiring only | not tested | not tested | not tested | not tested | not tested | from installed `gearbox` | works |
| Original intro music | — | — | — | — | — | — | copied from `gearbox/media` only | — | — | works: OP4 music plays |
| Map music `trigger_cdaudio` | external OP4 maps | — | — | — | — | — | copied from `gearbox/media` only | — | — | works: OP4 music plays |
| `of0a0` / `ofboot0` campaign | OP4 server | — | — | — | — | — | — | — | external maps | works |
| BHL VGUI2 menus | — | BHL client | — | — | — | — | — | — | — | works |
| `impulse 101` for the ten weapons | OP4 server source | — | — | — | — | — | — | — | — | works |

## Test protocol for the user

1. Unzip into `Half-Life/lambda-fix/` next to `valve/` and `gearbox/`, then run `setup_op4_media.bat` once.
2. Run `hl.exe -game lambda-fix -console`; record the start of `of0a0`, the intro music, and the music of the first `trigger_cdaudio`.
3. `sv_cheats 1; impulse 101`; for each weapon: select it, HUD icon/ammo, fire, empty magazine, reload, switch away/to, sound, view/world model, effects.
4. Special tests: Grapple on a valid surface; Penguin and watch `monster_penguin`; Displacer primary/secondary/self-teleport; Shock Rifle primary/secondary and recharge.
5. Record video/console for each row. Per-aspect details I have not checked stay **not tested**.

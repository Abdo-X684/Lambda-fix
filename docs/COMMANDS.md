# Commands

This page lists the console commands that Lambda-fix adds, and the cvars its menus write.
Each entry was checked against the source code in this repository. A dash (`—`) means the source has no description for that cvar.

## Startup order

On each start, the client runs:

1. `exec bugfixedhl.cfg`
2. `lambda_apply_defaults`
3. `sv_cheats 0`

Step 3 turns cheats off. To use the cheat commands below, set `sv_cheats 1` after the game has started.

## Console commands

| Command | What it does |
| --- | --- |
| `lambda_apply_defaults` | Sets the HUD color to `0 160 0`, turns on `hud_color_override`, and sets the crosshair color to `cl_cross_red 0`, `cl_cross_green 160`, `cl_cross_blue 0`. It runs at startup and does nothing once the internal version cvar `lambda_defaults_version` is 1, so running it again later has no effect. |

## Opposing Force weapons (cheat commands)

Both commands below need `sv_cheats 1`. Without it, the server ignores them.

- **`impulse 101`** gives the Opposing Force weapons and the base items. The Opposing Force weapons are:
  - Eagle (`weapon_eagle`)
  - Spore Launcher (`weapon_sporelauncher`)
  - Shock Rifle (`weapon_shockrifle`)
  - Knife (`weapon_knife`)
  - M249 (`weapon_m249`)
  - Pipe Wrench (`weapon_pipewrench`)
  - Grapple (`weapon_grapple`)
  - Sniper Rifle (`weapon_sniperrifle`)
  - Displacer (`weapon_displacer`)

  Penguin (`weapon_penguin`) is not given. It is not included yet.

- **`give weapon_<name>`** gives one weapon, using the names above.

The file `op4weapons.cfg` contains `impulse 101` and one `give` line for each weapon above. Run it with `exec op4weapons.cfg`.

The `op4weapons.cfg` comment says `autoexec.cfg` sets `sv_cheats 1`. The release zip does not include `autoexec.cfg`, so you must set `sv_cheats 1` yourself.

## Menu cvars

The client saves its archived cvars to `bugfixedhl.cfg` when the game exits. You can also set any of them in the console, for example `hud_speedometer 1`.

### Advanced > Multiplayer > More options

| Cvar | Default | Description |
| --- | --- | --- |
| `cl_enable_html_motd` | `1` | Enables or disables support for HTML MOTDs |
| `results_log_chat` | `0` | Enable chat logging into a file |
| `results_log_other` | `0` | Enable other messages (like kill messages and others in the console) logging into a file |
| `results_demo_autorecord` | `0` | Record demos when joining a server |
| `results_demo_keepdays` | `14` | Days to keep automatically recorded demos |

### General

| Cvar | Default | Description |
| --- | --- | --- |
| `cl_killsound` | `1` | Play a sound on kill |
| `cl_autojump` | `0` | Jump automatically when ground is hit |

### HUD

| Cvar | Default | Description |
| --- | --- | --- |
| `hud_client_renderer` | `1` | Enable client-side HUD rendering (instead of engine renderer) |
| `hud_dim` | `1` | Dim inactive HUD elements |
| `hud_menu_fkeys` | `1` | Use keys F1-F10 in the menus |
| `hud_weapon` | `0` | Controls displaying sprite of currently selected weapon |
| `hud_centerid` | `0` | Show other players' names in the middle of the screen |
| `hud_rainbow` | `0` | Enable Rainbow HUD |
| `hud_speedometer` | `0` | Enable speedometer |
| `hud_speedometer_below_cross` | `0` | Move speedometer to below the crosshair |
| `hud_jumpspeed` | `0` | Enable jumpspeed |
| `hud_jumpspeed_below_cross` | `0` | Move jumpspeed to below the crosshair |
| `hud_deathnotice_vgui` | `1` | Use VGUI deathnotice panel |
| `hud_custom` | `0` | Custom HUD using VGUI2 |

### HUD colors

| Cvar | Default | Description |
| --- | --- | --- |
| `hud_color_override` | set to `1` by `lambda_apply_defaults` | — |
| `hud_armor_custom` | `0` | Use `hud_armor_color` for armor instead of colors by amount |

### Crosshair

| Cvar | Default | Description |
| --- | --- | --- |
| `cl_cross_enable` | `1` | — |
| `cl_cross_dot` | `0` | — |
| `cl_cross_t` | `0` | — |

### Chat

| Cvar | Default | Description |
| --- | --- | --- |
| `hud_saytext` | `1` | Enable/disable display of new chat messages |
| `hud_saytext_sound` | `1` | Play sound on new chat message |
| `cl_mute_all_comms` | `1` | If 1, then all communications from a player will be blocked when that player is muted, including chat messages |

### Scoreboard

| Cvar | Default | Description |
| --- | --- | --- |
| `hud_scoreboard_showavatars` | `1` | — |
| `hud_scoreboard_showsteamid` | `1` | — |
| `hud_scoreboard_showloss` | `1` | — |
| `hud_scoreboard_showeff` | `1` | — |

### Models

| Cvar | Default | Description |
| --- | --- | --- |
| `cl_hidecorpses` | `0` | — |
| `cl_righthand` | `0` | If enabled, activates the left-handed mode |
| `cl_bob_angled` | `0` | Enables the angled viewmodel bobbing |
| `cl_noshells` | `0` | Disables shells ejected from weapons when firing |
| `r_drawviewmodel` | engine default | Shown in the menu as "No viewmodel", which is inverted: ticking the box sets it to `0` |

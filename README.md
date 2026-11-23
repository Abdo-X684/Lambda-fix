<p align="center">
  <img src="docs/assets/lambda-fix-logo.svg" alt="Lambda-fix" width="480">
</p>

<p align="center">
  A standalone Half-Life mod built on BugfixedHL, with the Opposing Force content in one mod folder.<br>
  It does not bundle Valve or Gearbox assets. It uses your own installed copy.
</p>

## Releases

| Version | Platform | Status | Download |
| --- | --- | --- | --- |
| **1.0.0 (stable)** | Windows | Tested in game | [Release](https://github.com/Abdo-X684/Lambda-fix/releases/tag/v1.0.0) · SHA-256 `6360e78342f83e69658bc292dbd420c31b07bd3951e370701c3d8cbb6cd94a54` |
| 0.9.0 | Linux | Latest Linux release. Linux 1.0.0 will follow later. | [Release](https://github.com/Abdo-X684/Lambda-fix/releases/tag/v0.9.0) · SHA-256 `65b9cab084e7895ae18714ed1b0262e2e14d14a25ead7276b66b9f68aa4a53f7` |

Check a download with `sha256sum <file>`.

## Features

- **Opposing Force weapons:** nine weapons, matching OP4 Updated, given by `impulse 101` and `exec op4weapons.cfg`. Penguin is not in that set.
- **Opposing Force campaign:** runs from your own `gearbox/` folder.
- **Pipe Wrench charge attack:** hold to pull back, release to strike.
- **Speedrun-friendly behavior:** ropes, electrified wire, M249 spread, wrench and knife timing, and frame-rate-consistent trigger cameras, Gargantua stomps, pushables, and monster turning.
- **Multiplayer settings:** Advanced > Multiplayer has Chat, Scoreboard, Models, and More options. More options holds HTML MOTD, chat logging, and demo recording.
- **Create Server:** lists only Opposing Force multiplayer maps.
- **Co-op and CTF:** scoreboard data works in both modes.
- **Advanced menu:** General, HUD, Crosshair, Multiplayer, and About. About shows the version.
- **Console commands:** see [Commands](#commands).

## Install

- **Windows 1.0.0:** you need your own Half-Life with the `valve/` and `gearbox/` folders. Follow `INSTALL.md` inside the zip.
- **Linux 0.9.0:** put `valve/` and `gearbox/` side by side, unzip the package into that folder, and launch with `-game lambda-fix -console`. `INSTALL.md` inside the package has the full steps.

## Build

```bash
make fetch
make bhl-base
make verify
```

Details are in [BUILDING.md](docs/BUILDING.md).

## Commands

Type these in the console (`` ` `` or `~`). The mod sets `sv_cheats 0` at every start, so set `sv_cheats 1` before the weapon commands.

### Weapons

| Command | What it does |
| --- | --- |
| `impulse 101` | Gives the standard weapons and the nine Opposing Force weapons. Penguin is not included. |
| `exec op4weapons.cfg` | Runs `impulse 101`, then gives the nine Opposing Force weapons listed in the file. |

### Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `cl_enable_html_motd` | `1` | Allows HTML message-of-the-day pages from servers. |
| `results_log_chat` | `0` | Logs chat to a file. |
| `results_log_other` | `0` | Logs other messages, such as kill messages, to a file. |
| `results_demo_autorecord` | `0` | Records a demo when you join a server. |
| `results_demo_keepdays` | `14` | Days to keep automatically recorded demos. |
| `sk_plr_pipewrench` | `20` | Pipe Wrench base damage (server skill setting). |

These settings are also on Advanced > Multiplayer > More options, except `sk_plr_pipewrench`.

### Maintenance

| Command | What it does |
| --- | --- |
| `lambda_apply_defaults` | Sets the HUD and crosshair color to OP4 green (`0 160 0`). It runs at startup and applies only once per install, tracked by `lambda_defaults_version`. |

### Engine

| Command | What it does |
| --- | --- |
| `maps *` | Lists the maps the game can find. |

## Known open items

- No Linux 1.0.0 build yet.
- The AG CTF sprites (`ag_ctf.spr`, `ag_ctf_score.spr`) have an unconfirmed license. They are used only by CTF mode.

## Licenses

See [LICENSES.md](LICENSES.md) for the licenses of each component.

## Docs

[Building](docs/BUILDING.md) · [Architecture](docs/ARCHITECTURE.md) · [Weapon inventory](docs/WEAPON_INVENTORY.md) · [OP4 runtime tests](docs/OP4_RUNTIME_TESTS.md) · [Upstreams](docs/UPSTREAMS.md) · [BugfixedHL merge](docs/BHL_BASE_MERGE.md) · [Contributing](CONTRIBUTING.md)

<p align="center">
  <img src="assets/lambda-fix-logo.svg" alt="Lambda-fix" width="480">
</p>

<p align="center">
  A standalone Half-Life mod built on BugfixedHL, with the Opposing Force content in one mod folder.<br>
  It does not bundle Valve or Gearbox assets. It uses your own installed copy.
</p>

## Releases

**[Download the latest release](https://github.com/Abdo-X684/Lambda-fix/releases/latest)**

Choose the zip for your platform (Windows or Linux) from the release page.

### How to update

1. Close the game.
2. Download the latest release for your platform.
3. Extract the zip into your game folder and overwrite the existing files.
4. Start the game and check the About page for the version.

Earlier Windows packages bundled a server DLL that is not an Opposing Force server. Replace them with the latest release.

## Features

- **Opposing Force weapons:** the weapons of OP4 Updated. `impulse 101` gives nine of them (requires `sv_cheats 1`).

  | Weapon | Code name |
  | --- | --- |
  | Eagle | `weapon_eagle` |
  | Pipe Wrench | `weapon_pipewrench` |
  | M249 | `weapon_m249` |
  | Displacer | `weapon_displacer` |
  | Shock Rifle | `weapon_shockrifle` |
  | Spore Launcher | `weapon_sporelauncher` |
  | Sniper Rifle | `weapon_sniperrifle` |
  | Knife | `weapon_knife` |
  | Grapple | `weapon_grapple` |
  | Penguin | `weapon_penguin` (not in the default weapon set) |

- **Opposing Force campaign:** runs from your own `gearbox/` folder.
- **Advanced menu:** General, HUD, Crosshair, Chat, Scoreboard, Models, Multiplayer (with More options), and About. About shows the version.
- **Create Server:** lists only Opposing Force multiplayer maps.

## Install on Windows

You need your own Half-Life with the `valve/` and `gearbox/` folders. The package has no server DLL. It uses the stock Opposing Force server in your `gearbox/` folder. Follow `INSTALL.md` inside the zip.

## Install on Linux

Put `valve/` and `gearbox/` side by side and unzip the package into that folder. The package has no server library. It uses the stock Opposing Force server in your `gearbox/` folder. `INSTALL.md` inside the package has the full steps.

## Build

```bash
make fetch
make bhl-base
make verify
```

## Known open items

- Server-side changes from the speedrun work are not active with the stock server. They return only with our own server, which is not in the current packages.
- The AG CTF sprites (`ag_ctf.spr`, `ag_ctf_score.spr`) have an unconfirmed license. They are used only by CTF mode.

## Commands

The command reference is not included in this repository for now.

## Licenses

See [LICENSES.md](LICENSES.md) for the licenses of each component.

## Docs

[Contributing](CONTRIBUTING.md) · [Licenses](LICENSES.md)

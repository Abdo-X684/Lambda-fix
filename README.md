# Lambda Fix

Lambda Fix is a standalone Half-Life mod. It is built on BugfixedHL and integrates the Opposing Force content into one mod folder, so you do not need to patch the base game.

It includes the ten Opposing Force weapons, the Opposing Force campaign, multiplayer changes for Opposing Force maps and modes, menu and HUD updates, and speedrun fixes.

The project does not bundle Valve or Gearbox assets. It reads them from your own installed copy of Half-Life and Opposing Force.

## Releases

| Version | Platform | Status |
| --- | --- | --- |
| **1.0.0 (stable)** | Windows | Released. Tested in game by the maintainer. |
| 0.9.0 | Linux | Most recent Linux release. A Linux 1.0.0 build will follow later. |

### Windows 1.0.0

- **Download:** [Lambda-fix v1.0.0](https://github.com/Abdo-X684/Lambda-fix/releases/tag/v1.0.0)
- **SHA-256:** `6360e78342f83e69658bc292dbd420c31b07bd3951e370701c3d8cbb6cd94a54`

Check the download:

```bash
sha256sum lambda-fix-windows-mod.zip
```

Install steps are in `INSTALL.md` inside the zip. You need your own Half-Life installation with the `valve/` and `gearbox/` folders.

### Linux 0.9.0

- **SHA-256:** `65b9cab084e7895ae18714ed1b0262e2e14d14a25ead7276b66b9f68aa4a53f7`
- **Release:** [v0.9.0](https://github.com/Abdo-X684/Lambda-fix/releases/tag/v0.9.0)

Check the download:

```bash
sha256sum lambda-fix-bhlbase-linux.zip
```

## Features in 1.0.0

- All ten Opposing Force weapons, matching OP4 Updated. `impulse 101` gives them.
- Console commands use the `lambda_` prefix.
- Advanced settings: General, HUD, Crosshair, Multiplayer, and About.
- Advanced > Multiplayer: Chat, Scoreboard, Models (scrollable), and More options. The HTML MOTD, chat-logging, and demo options are on the More options page.
- Create Server hides story maps. The map cycle lists only Opposing Force multiplayer maps.
- Pipe Wrench: hold right-click to pull back, release to strike.
- Speedrun fixes: ropes, electrified wire, M249 spread, wrench holster cancel, wrench and knife timing, and frame-rate fixes for trigger_camera, the Gargantua stomp, pushable push/pull, and monster turning.
- Co-op and CTF scoreboard data is sent correctly.

Gauss, explosives, and the Pit Worm bridge are unchanged.

## Install (Linux 0.9.0)

You need:

- Half-Life and Opposing Force, with the original `valve/` and `gearbox/` folders.
- Linux with the 32-bit libraries your Half-Life install needs.
- SDL2.
- The `vgui.so` from your own Half-Life installation. It is not in this package.

Steps:

1. Put `valve/` and `gearbox/` next to each other in your Half-Life folder.
2. Unzip the package into that folder. It creates `lambda-fix/`.
3. Do not overwrite anything in `valve/` or `gearbox/`.
4. Launch with `-game lambda-fix -console`, using your own launcher script.

`INSTALL.md` inside the package has the full steps.

## Build from source

```bash
make fetch
make bhl-base
python3 -m venv /tmp/zenv
/tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
/tmp/zenv/bin/python tools/build_bhl_base.py --out scratch/bhl-out --jobs 8
make verify
```

The Linux output is a 32-bit `client.so` with a GLIBC 2.17 baseline. The Windows DLLs are built with MSVC by the GitHub Actions workflows. Details are in [BUILDING.md](docs/BUILDING.md), [BHL_BASE_BUILD.md](docs/BHL_BASE_BUILD.md), and [BHL_WINDOWS_BUILD.md](docs/BHL_WINDOWS_BUILD.md).

## Known open items

- There is no Linux 1.0.0 build yet. The Linux package is 0.9.0.
- The AG CTF sprites (`sprites/ag_ctf.spr`, `ag_ctf_score.spr`) come from Adrenaline Gamer. Their license is not confirmed. They are used only by CTF mode.

## Licenses

- **BugfixedHL:** GPL-3.0 ([tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased))
- **Opposing Force weapons:** Valve Half-Life 1 SDK License. Free distribution only. Commercial use needs Valve's permission ([twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated))
- **Build tools and Linux shims:** MIT

The package has a `LICENSES/` folder with the full texts. See [LICENSES.md](LICENSES.md) for the breakdown. This is not legal advice.

## Docs

- [Building](docs/BUILDING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Weapon inventory](docs/WEAPON_INVENTORY.md)
- [OP4 runtime tests](docs/OP4_RUNTIME_TESTS.md)
- [Upstream sources](docs/UPSTREAMS.md)
- [BugfixedHL merge](docs/BHL_BASE_MERGE.md)
- [Contributing](CONTRIBUTING.md)

## Checks

```bash
make hygiene   # text, JSON, links, docs index
make verify    # full repository checks
```

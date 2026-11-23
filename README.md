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

## Features in 1.0.0

- The ten Opposing Force weapons. `impulse 101` gives them.
- Advanced > Multiplayer: Chat, Scoreboard, Models, and More options.
- Create Server lists only Opposing Force multiplayer maps.
- Pipe Wrench charge attack and speedrun fixes.
- Co-op and CTF scoreboard fixes.

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

## Known open items

- No Linux 1.0.0 build yet.
- The AG CTF sprites (`ag_ctf.spr`, `ag_ctf_score.spr`) have an unconfirmed license. They are used only by CTF mode.

## Licenses

- BugfixedHL: GPL-3.0 ([BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased))
- Opposing Force weapons: Valve Half-Life 1 SDK License. Non-commercial use only ([halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated))
- Build tools and Linux shims: MIT

See [LICENSES.md](LICENSES.md) for the full breakdown. This is not legal advice.

## Docs

[Building](docs/BUILDING.md) · [Architecture](docs/ARCHITECTURE.md) · [Weapon inventory](docs/WEAPON_INVENTORY.md) · [OP4 runtime tests](docs/OP4_RUNTIME_TESTS.md) · [Upstreams](docs/UPSTREAMS.md) · [BugfixedHL merge](docs/BHL_BASE_MERGE.md) · [Contributing](CONTRIBUTING.md)

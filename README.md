<!--
  Lambda Fix
  Keep this README focused on the project, its verified capabilities, and setup.
-->

<div align="center">

<img src="assets/logo.svg" alt="Lambda Fix logo" width="480">

# Lambda Fix

**BugfixedHL × Opposing Force — a GoldSrc integration project for Linux**

[![Platform](https://img.shields.io/badge/platform-Linux-informational?logo=linux&logoColor=white)](https://www.kernel.org/)
[![Engine](https://img.shields.io/badge/engine-GoldSrc-orange)](https://www.valvesoftware.com/)
[![Architecture](https://img.shields.io/badge/architecture-x86%20%2F%2032--bit-blue)](https://en.wikipedia.org/wiki/IA-32)
[![Language](https://img.shields.io/badge/language-C%2B%2B-blue)](https://isocpp.org/)
[![License](https://img.shields.io/badge/license-MIT%20%2B%20upstream%20terms-lightgrey)](LICENSE)

*Bringing the BugfixedHL foundation and the ten Opposing Force weapons together in one dedicated Half-Life mod.*

</div>

---

## Overview

Lambda Fix is a community integration project built around **BugfixedHL** with code and gameplay content from **Half-Life: Opposing Force**. It keeps BugfixedHL as the project base and incorporates the ten Opposing Force weapon implementations into a separate GoldSrc mod.

The Linux package is designed to run alongside the user's existing Half-Life and Opposing Force installations. It uses the original `gearbox/` content through GoldSrc's `fallback_dir` mechanism instead of bundling Valve or Gearbox game assets.

## At a glance

| | |
| --- | --- |
| **Base** | BugfixedHL-Rebased |
| **Game** | Half-Life / Opposing Force |
| **Engine** | GoldSrc |
| **Primary target** | Linux, 32-bit |
| **Client library** | `client.so` |
| **Build output** | 32-bit ELF; GLIBC 2.17 baseline |
| **Mod directory** | `lambda-fix/` |
| **Current package** | Linux ZIP — see [Download](#download) |

## Features

- **BugfixedHL foundation** — BugfixedHL remains the base of the merged game code.
- **Ten Opposing Force weapons** — the OP4 weapon source, client-side code, registrations, and related integration are included in the merged project.
- **Dedicated mod folder** — install `lambda-fix/` beside the original `valve/` and `gearbox/` folders.
- **Original OP4 assets** — the mod reads the user's installed Opposing Force content through `fallback_dir "gearbox"`.
- **Pinned upstream sources** — upstream revisions and archive checksums are recorded for repeatable source fetching.
- **Linux build** — produces 32-bit GoldSrc libraries with a GLIBC 2.17 compatibility baseline.

## Opposing Force weapon set

The project integrates these ten OP4 weapon implementations:

| Weapon | Code identifier |
| --- | --- |
| Desert Eagle | `weapon_eagle` |
| Pipe Wrench | `weapon_pipewrench` |
| M249 | `weapon_m249` |
| Displacer | `weapon_displacer` |
| Shock Rifle | `weapon_shockrifle` |
| Spore Launcher | `weapon_sporelauncher` |
| Sniper Rifle | `weapon_sniperrifle` |
| Knife | `weapon_knife` |
| Penguin | `weapon_penguin` |
| Grapple | `weapon_grapple` |

**Testing note:** the repository's runtime notes report the game, OP4 campaign entry points, menus, music, and weapon access working. However, the detailed per-weapon checks—such as firing, reloading, animations, sounds, effects, and prediction—are not all independently documented as tested. See [OP4 runtime tests](docs/OP4_RUNTIME_TESTS.md) and the [weapon inventory](docs/WEAPON_INVENTORY.md) for the exact verification status.

## Download

| Item | Details |
| --- | --- |
| **Linux package** | [`lambda-fix-bhlbase-linux.zip`](build-evidence/bhl-base-linux-mod/lambda-fix-bhlbase-linux.zip) |
| **SHA-256** | `16193b9f482dc3744217f8c9e095f274e07588561a57172cc6ae2ba03721dba9` |
| **Release** | [v0.9.0](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.9.0) |

> **Repository access:** this repository is private. You must be signed in to GitHub with access to the repository to open its package files.

Always verify the SHA-256 checksum after downloading:

```bash
sha256sum lambda-fix-bhlbase-linux.zip
```

## Installation (Linux)

### Requirements

- A working installation of **Half-Life**.
- **Half-Life: Opposing Force**, including its original `gearbox/` directory.
- Linux with the 32-bit runtime libraries required by your Half-Life installation.
- SDL2.
- The original installation's `vgui.so` file.

Lambda Fix does **not** include commercial Half-Life or Opposing Force assets. You must provide your own legitimate game installation.

### Steps

1. Install Half-Life and Opposing Force.
2. Confirm that `valve/` and `gearbox/` are located next to each other in your Half-Life directory.
3. Extract the Lambda Fix package into that directory. It should create a separate `lambda-fix/` folder.
4. Keep the mod files separate; do not overwrite files inside `valve/` or `gearbox/`.
5. Make sure the required `vgui.so` is available from your own Half-Life installation.
6. Launch Lambda Fix from the Half-Life directory:

   ```bash
   hl_linux -game lambda-fix -console
   ```

The mod uses `fallback_dir "gearbox"` to access Opposing Force assets from the original installation.

For package-specific details, consult `INSTALL.md` included in the archive.

## Build from source

The build process fetches pinned upstream sources, prepares the merged BugfixedHL/OP4 tree, and builds the Linux libraries.

```bash
make fetch
make bhl-base

python3 -m venv /tmp/zenv
/tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3

/tmp/zenv/bin/python tools/build_bhl_base.py --out scratch/bhl-out --jobs 8
make verify
```

The current Linux build targets `i386-unknown-linux-gnu` and uses a GLIBC 2.17 baseline.

### Repository checks

```bash
make hygiene   # text, JSON, links, and documentation checks
make verify    # full repository verification
```

See the [build guide](docs/BUILDING.md) and [BugfixedHL base build notes](docs/BHL_BASE_BUILD.md) for prerequisites and further details.

## Project status

| Area | Status |
| --- | --- |
| Linux package | Available |
| BugfixedHL base integration | Included |
| Ten OP4 weapon source integrations | Included |
| OP4 campaign entry points | Reported working in runtime notes |
| BugfixedHL menus | Reported working in runtime notes |
| OP4 music | Reported working in runtime notes |
| Individual weapon fire/reload/animation/effect checks | Not fully verified weapon by weapon |
| Windows in-game support | Not verified |
| Campaign map-by-map testing | Not completed |
| Auto-update removal and green HUD color | Built; in-game verification pending |

Build success and source-level integration are not substitutes for full in-game testing. The linked test documents distinguish what is present in the source from what has been verified in the GoldSrc engine.

## Upstream projects

Lambda Fix combines and adapts work from these upstream repositories. The exact pinned revisions are documented in [UPSTREAMS.md](docs/UPSTREAMS.md) and `upstreams.json`.

| Project | Role | Pinned revision |
| --- | --- | --- |
| [BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased) | BugfixedHL foundation and systems | `4d32095e3c33` |
| [halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated) | Opposing Force code and community updates | `5368be7f8eba` |
| [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife) | Half-Life SDK base | `b1b5cf589291` |

## Documentation

| Document | Description |
| --- | --- |
| [Building](docs/BUILDING.md) | Build prerequisites and Linux build steps |
| [Architecture](docs/ARCHITECTURE.md) | Project structure and integration approach |
| [Weapon inventory](docs/WEAPON_INVENTORY.md) | Weapon-by-weapon source and integration inventory |
| [OP4 runtime tests](docs/OP4_RUNTIME_TESTS.md) | Runtime test status and test protocol |
| [Upstream sources](docs/UPSTREAMS.md) | Pinned source repositories and revisions |
| [Licensing](LICENSES.md) | License breakdown, attribution, and redistribution requirements |
| [BugfixedHL merge](docs/BHL_BASE_MERGE.md) | BugfixedHL base merge details |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |

## Licensing

Lambda Fix incorporates original code and third-party components under different terms. The root MIT license applies only to original repository-authored code; it does not replace the licenses covering BugfixedHL-derived code, Valve SDK code, or third-party assets.

See **[LICENSES.md](LICENSES.md)** for the license breakdown, attribution, and redistribution requirements before sharing source code or binaries. This summary is not legal advice.

## Contributing

Bug reports, reproducible test results, and carefully documented improvements are useful. Before submitting a change, review [CONTRIBUTING.md](CONTRIBUTING.md) and include the platform, launch parameters, steps to reproduce, and relevant logs.

---

<div align="center">

**Lambda Fix**  
*A community integration project for Half-Life and Opposing Force.*

Half-Life, Opposing Force, BugfixedHL, and their respective names and assets remain the property of their respective owners.

</div>

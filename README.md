# Lambda Fix

**BugfixedHL integrated with all ten Opposing Force weapons for Half-Life on Linux.**

Lambda Fix brings the BugfixedHL codebase together with the ten-weapon Opposing Force set in a dedicated GoldSrc mod. The goal is straightforward: keep the BugfixedHL foundation, add the Opposing Force weapons, and make the result buildable and playable on Linux.

## What’s included

- **BugfixedHL foundation** — the BugfixedHL codebase and its fixes.
- **All ten Opposing Force weapons** — integrated into the mod rather than shipped as loose resource files.
- **Opposing Force integration** — uses the original `gearbox/` game content through GoldSrc's `fallback_dir` setting.
- **Linux builds** — 32-bit `client.so` and `hl.so` outputs.
- **Reproducible upstream inputs** — source repositories are pinned to commits and checked by SHA-256 and file size before extraction.

## Download

| Item | Value |
| --- | --- |
| Linux package | [`lambda-fix-bhlbase-linux.zip`](build-evidence/bhl-base-linux-mod/lambda-fix-bhlbase-linux.zip) |
| SHA-256 | `16193b9f482dc3744217f8c9e095f274e07588561a57172cc6ae2ba03721dba9` |
| Release | [v0.9.0](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.9.0) |

> **Access:** This repository is private. You must be signed in to GitHub with repository access to open its package links.

## Current status

The current Linux build has been tested. The status below distinguishes working features from items that still need testing.

| Area | Status |
| --- | --- |
| Game startup | Working |
| BugfixedHL menu | Working |
| Ten Opposing Force weapons | Integrated and working |
| Opposing Force music | Working |
| Other tested gameplay/features | Working |
| Auto-update removal and green HUD color | Built; in-game testing pending |
| Windows `client.dll` | Not available; Windows build is not complete |
| Campaign maps | Not yet tested individually |

## Requirements

- A working **Half-Life** installation.
- **Half-Life: Opposing Force** installed, with its original `gearbox/` directory.
- Linux and the 32-bit runtime libraries required by the game.
- SDL2.
- The original game installation's `vgui.so` file.

Lambda Fix does not include the commercial game assets. Use your own legitimate installation of Half-Life and Opposing Force.

## Install on Linux

1. Install Half-Life and Opposing Force. Confirm that `valve/` and `gearbox/` are next to each other in your game directory.
2. Extract the package into the Half-Life directory. It should create a separate `lambda-fix/` folder alongside `valve/` and `gearbox/`.
3. Do **not** install the mod's libraries inside `valve/` or `gearbox/`.
4. Make sure the required `vgui.so` is available from your own Half-Life installation.
5. Launch the game with:

   ```bash
   hl_linux -game lambda-fix -console
   ```

The mod uses `fallback_dir "gearbox"` to read Opposing Force content from the original game folder without replacing it.

For the package-specific walkthrough, see `INSTALL.md` inside the archive.

## Build from source

The build fetches pinned upstream sources and generates the merged BugfixedHL/OP4 tree before compiling the Linux libraries.

```bash
make fetch
make bhl-base

python3 -m venv /tmp/zenv
/tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3

/tmp/zenv/bin/python tools/build_bhl_base.py --out scratch/bhl-out --jobs 8
make verify
```

The current build produces 32-bit ELF `client.so` and `hl.so` binaries for `i386-unknown-linux-gnu`, with a GLIBC 2.17 baseline. See [`docs/BUILDING.md`](docs/BUILDING.md) and [`docs/BHL_BASE_BUILD.md`](docs/BHL_BASE_BUILD.md) for details.

### Repository checks

```bash
make hygiene   # text, JSON, links, and documentation checks
make verify    # full repository checks
```

## Upstream sources and credits

Lambda Fix combines code from multiple upstream projects. The source inputs are pinned in [`docs/UPSTREAMS.md`](docs/UPSTREAMS.md) and `upstreams.json`.

| Source | How it is used | Pinned revision | License / terms |
| --- | --- | --- | --- |
| [BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased) | BugfixedHL foundation and systems | `4d32095e3c33` | GPL-3.0 |
| [halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated) | Opposing Force code and community updates | `5368be7f8eba` | Valve Half-Life SDK terms and TWHL contributions |
| [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife) | Pinned Half-Life SDK base | `b1b5cf589291` | Valve Half-Life SDK terms |

The pinned revisions and archive checksums are part of the build inputs; see [`docs/UPSTREAMS.md`](docs/UPSTREAMS.md) for the source-fetching process.

## Licensing and redistribution

**There is no single license that covers every part of the generated project.** The MIT license in this repository's root applies to original code authored for this repository; it does not replace the licenses of upstream code included in the merged source tree or binaries.

- **BugfixedHL-derived code:** GPL-3.0 obligations apply to the merged code and binaries built from it. Review the GPL terms and provide the corresponding source and required notices when distributing covered binaries.
- **Valve Half-Life SDK and Opposing Force SDK-derived code:** the applicable Valve SDK terms restrict redistribution to the permitted non-commercial use. Commercial use requires permission from Valve. Review the license files in the respective upstream repositories before redistributing.
- **AG CTF sprites:** the origin is attributed to Adrenaline Gamer, but their license has not been confirmed. They are used by CTF mode; do not assume they are cleared for redistribution.
- **Game content:** this project does not include Valve/Gearbox models, sounds, or maps. You must supply the original game content yourself. The mod's `delta.lst` is SDK-derived data and remains subject to the applicable SDK terms.

Before publishing or redistributing a build, read [`LICENSE`](LICENSE), [`docs/LICENSES.md`](docs/LICENSES.md), and the upstream license files. This project documentation is not legal advice.

## Known limitations and work in progress

- No current Windows `client.dll` build.
- Campaign maps have not yet been tested one by one.
- Auto-update removal and the green HUD color change are built but still need in-game verification.
- AG CTF sprite licensing remains unconfirmed.

## Documentation

- [Installation and build guide](docs/BUILDING.md)
- [License details and distribution notes](docs/LICENSES.md)
- [Pinned upstream sources](docs/UPSTREAMS.md)
- [BugfixedHL base merge notes](docs/BHL_BASE_MERGE.md)
- [Contributing](CONTRIBUTING.md)

---

**Lambda Fix** is a community integration project. Half-Life, Opposing Force, BugfixedHL, and their respective names and assets remain the property of their respective owners.

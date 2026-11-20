# lambda-fix

BugfixedHL with the ten Opposing Force weapons, for Half-Life on Linux.

## Download

- **Package:** [`build-evidence/bhl-base-linux-mod/lambda-fix-bhlbase-linux.zip`](build-evidence/bhl-base-linux-mod/lambda-fix-bhlbase-linux.zip)
- **SHA-256:** `16193b9f482dc3744217f8c9e095f274e07588561a57172cc6ae2ba03721dba9`
- **Release:** [v0.9.0](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.9.0)

The repository is private, so the links need a GitHub login with access.

## Status

Tested on linux

| Item | Status |
| --- | --- |
| Game starts | ✅ Works |
| BugfixedHL menu opens | ✅ Works |
| Opposing Force weapons | ✅ Work |
| OP4 music | ✅ Plays |
| Everything else | ✅ Works |
| Auto-update removal and green HUD color | Built, not tested in game |
| Windows build | ❌ Not done: GitHub Actions fails before any step runs |

## Install (Linux)

1. Install Half-Life: Opposing Force. The `gearbox/` folder must sit next to `valve/`.
2. Delete any old `lambda-fix` folder.
3. Unzip the package into your game folder, next to `valve/` and `gearbox/`.
4. Launch with `-game lambda-fix`.

Full steps are in `INSTALL.md` inside the package. SDL2 must be installed.

## Licenses

- **BugfixedHL:** GPL-3.0 ([tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased))
- **Opposing Force weapons:** Valve Half-Life 1 SDK License. Free distribution only; commercial use needs Valve's permission ([twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated))
- **Build tools and Linux shims:** MIT

The package has a `LICENSES/` folder with the full texts. It contains no Valve assets (models, sounds, maps); you need your own copy of the game.

## Build from source (Linux)

```bash
make fetch
git clone https://github.com/tmp64/hl1_source_sdk .cache/upstreams/hl1_source_sdk
git -C .cache/upstreams/hl1_source_sdk checkout 11f2665
python3 -m venv /tmp/zenv && /tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
/tmp/zenv/bin/python tools/build_bhl_base.py --out scratch/bhl-out
```

Output: `client.so` (ELF32, needs GLIBC 2.17 at most), built with `-O2`.

## Checks

```bash
make hygiene   # text, JSON, links, docs index
make verify    # full repository checks
```

## Known open items

- The AG CTF sprites (`sprites/ag_ctf.spr`, `ag_ctf_score.spr`) come from Adrenaline Gamer. Their license is not confirmed. They are used only by CTF mode.
- No current Windows `client.dll`.
- Campaign maps are not yet tested one by one.

## Docs

- [`docs/LICENSES.md`](docs/LICENSES.md): license details
- [`docs/BUILDING.md`](docs/BUILDING.md): build instructions
- [`docs/UPSTREAMS.md`](docs/UPSTREAMS.md): pinned upstream sources
- [`CONTRIBUTING.md`](CONTRIBUTING.md): how to contribute
## AI

this was build using arena ai 

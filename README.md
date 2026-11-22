# Lambda Fix

BugfixedHL with the ten Opposing Force weapons, for Half-Life on Linux.

Lambda Fix is a community integration project. It keeps BugfixedHL as the base and adds the Opposing Force weapon code in a separate mod folder. It does not bundle Valve or Gearbox assets. It reads them from your own installed copy of Opposing Force.

## Download
- **SHA-256:** `65b9cab084e7895ae18714ed1b0262e2e14d14a25ead7276b66b9f68aa4a53f7`
- **Release:** [v0.9.0](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/releases/tag/v0.9.0)

The repository is private, so you need a GitHub login with access to open these links.

Check the download:

```bash
sha256sum lambda-fix-bhlbase-linux.zip
```

## Status

Tested on linux:

| Item | Status |
| --- | --- |
| Game starts | ✅ Works |
| BugfixedHL menu opens | ✅ Works |
| Opposing Force weapons | ✅ Work |
| OP4 music | ✅ Plays |
| Everything else | ✅ Works |
| Auto-update removal and green HUD color | Built, not tested in game |
| Windows build | ❌ Not done (GitHub Actions fails before any step runs) |

Not yet verified one by one: each weapon's fire, reload, animation, and effects; campaign maps one by one. See [OP4 runtime tests](docs/OP4_RUNTIME_TESTS.md) for details.

## Install (Linux)

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

The output is a 32-bit `client.so` with a GLIBC 2.17 baseline. Details are in [BUILDING.md](docs/BUILDING.md) and [BHL_BASE_BUILD.md](docs/BHL_BASE_BUILD.md).

## Licenses

- **BugfixedHL:** GPL-3.0 ([tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased))
- **Opposing Force weapons:** Valve Half-Life 1 SDK License. Free distribution only. Commercial use needs Valve's permission ([twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated))
- **Build tools and Linux shims:** MIT

The package has a `LICENSES/` folder with the full texts. See [LICENSES.md](LICENSES.md) for the breakdown. This is not legal advice.

## Known open items

- The AG CTF sprites (`sprites/ag_ctf.spr`, `ag_ctf_score.spr`) come from Adrenaline Gamer. Their license is not confirmed. They are used only by CTF mode.
- There is no current Windows `client.dll`.

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

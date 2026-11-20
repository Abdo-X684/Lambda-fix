# lambda-fix — BugfixedHL + Opposing Force

A Half-Life mod that combines **BugfixedHL** (the base) with the **ten Opposing Force weapons**.
The goal is a clean speedrun mod: timer, BHL menus, and no extra features.

## Current package (Linux)

- **Download:** [lambda-fix-bhlbase-linux.zip](build-evidence/bhl-base-linux-mod/lambda-fix-bhlbase-linux.zip) (in this repository, `build-evidence/bhl-base-linux-mod/`)
- **SHA256:** `17cd673451fb7ca70c7465c5b54c9f97429efe090a9f089316d76cd7177ee699`
- **Install steps:** see `INSTALL.md` inside the package, and the summary below.

The repository is private, so the direct GitHub raw links require a GitHub login with access.

## Status

| Item | Status |
| --- | --- |
| Game starts | ✅ Reported by the user |
| BHL menu opens | ✅ Reported by the user |
| Opposing Force weapons work | ✅ Reported by the user |
| Crash in the ammo HUD | ✅ Fixed (rebuilt with `-O2`, no Zig safety checks); reported gone |
| Game lag | ✅ Greatly reduced after the `-O2` rebuild (reported on a weak PC) |
| Auto-update removed from Advanced > About | ✅ Implemented in source; not yet tested in game |
| Default HUD color green (`0 160 0`) | ✅ Implemented in source; not yet tested in game |
| Localization file `lambda-fix-fix_english.txt` | ✅ Added; not yet confirmed in game |
| Music | ✅ Reported by the user: OP4 music plays |
| Windows build | ❌ Blocked: GitHub Actions runs fail before any step runs |

## Install on Linux

1. Install Half-Life: Opposing Force. The `gearbox/` folder must sit next to `valve/`.
2. Delete any old `lambda-fix` folder.
3. Unzip the package into the main game folder, next to `valve/` and `gearbox/`.
4. Launch with `-game lambda-fix` (depends on your `hl.sh`).

The server is the stock `gearbox/dlls/opfor.so`. The client is the built BugfixedHL client.
SDL2 must be installed on the system.

## Licenses

- **BugfixedHL:** GPL-3.0. Source: [tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased).
- **Opposing Force weapons:** Valve Half-Life 1 SDK License. Free use and distribution only. Commercial use requires permission from Valve. Source: [twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated).
- **Build tools and Linux shims:** MIT.

The package contains a `LICENSES/` folder with these texts, and `NOTICE.txt` explains where each part comes from.
The package does not contain Valve assets (models, sounds, maps). You must own the original game.

## Build from source (Linux)

```bash
make fetch                                   # fetches BugfixedHL, OP4 updated, and the Valve SDK
git clone https://github.com/tmp64/hl1_source_sdk .cache/upstreams/hl1_source_sdk
git -C .cache/upstreams/hl1_source_sdk checkout 11f2665
python3 -m venv /tmp/zenv && /tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
/tmp/zenv/bin/python tools/build_bhl_base.py --out scratch/bhl-out
```

Output: `client.so` (ELF32, needs at most GLIBC 2.17). It is built with `-O2` and `-fno-sanitize=undefined`.

## Checks

```bash
make hygiene   # text, JSON, links, docs index
make verify    # repository checks (Python tests, C++ checks, generation, merge, package)
```

## Open items

1. **Mod name:** `lambda-fix` (folder, zip, and localization file `resource/lambda-fix-fix_english.txt`). The name was chosen by the project owner. Do not use Valve's Lambda logo or the name "Half-Life" in the logo or the title.
2. **Trademarks:** do not use the Lambda logo or the name "Half-Life" in the mod name or logo. Both belong to Valve.
3. **Sprite license:** `sprites/ag_ctf.spr` and `ag_ctf_score.spr` come from the Adrenaline Gamer code base. Their license is not confirmed. They are only used for CTF mode.
4. **Windows:** no current `client.dll`. The Windows source tree in the repo is based on an older OP4 tree, not the current BHL base.
5. **Not yet tested in game:** every map in the campaign, every weapon with ammo, and the items listed as "not yet tested" above.

## Docs

- `docs/LICENSES.md` — license details
- `docs/BUILDING.md` — build instructions
- `docs/UPSTREAMS.md` — pinned upstream sources

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

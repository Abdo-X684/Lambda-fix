# Building `client.so` and `hl.so`

## Do not put the files inside `gearbox/`

If you see this message:

> *This mod has detected that it is being run from a Valve game directory which
> is not supported. Run this mod from its intended location. The game will now
> shut down.*

then the DLLs were copied into `gearbox/cl_dlls/` or `gearbox/dlls/`. The SDK refuses to run
any mod folder whose name starts with `valve`, `gearbox`, `bshift`, `ricochet`, `dmc`,
`cstrike`, `czero`, `dod`, or `tfc` (prefix match, so `gearbox_hd` is refused too).

**Fix:** use a separate mod folder named `bhlop4` next to `valve/` and `gearbox/`. Its
`fallback_dir "gearbox"` setting reads the Opposing Force assets from the original folder without
changing it.

```text
Half-Life/
├── valve/          do not touch
├── gearbox/        do not touch (assets are read from here through fallback_dir)
└── bhlop4/         the mod folder
    ├── liblist.gam
    ├── steam_appid.txt   (50)
    ├── delta.lst
    ├── cl_dlls/client.so
    └── dlls/hl.so
```

Launch with: `hl_linux -game bhlop4 -console`

`liblist.gam`:

```text
game "BugfixedHL x OP4 Speedrun"
type "singleplayer_only"
startmap "of0a0"
trainmap "ofboot0"
cldll "1"
gamedll "dlls\hl.dll"
gamedll_linux "dlls/hl.so"
fallback_dir "gearbox"
```

## Prerequisites

| Item | Where it comes from |
|---|---|
| Pinned upstream sources (BugfixedHL, OP4, HLSDK) | `make fetch` (commit and sha256 pinned in `upstreams.json`) |
| 32-bit toolchain | `pip install ziglang==0.17.1` (used by `tools/build_bhl_base.py`), or `gcc-multilib g++-multilib` |
| `vgui.so` | Your own Half-Life installation. It is **not** distributed and **not** in this repository |
| Game assets (`gearbox/`, maps, sounds, models) | Your own Steam install of Half-Life and Opposing Force |

## Build steps

```bash
make fetch                       # pinned upstream sources
make bhl-base                    # regenerate bhl-op4/ from the BHL base + OP4 merge rules
python3 -m venv /tmp/zenv && /tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
/tmp/zenv/bin/python tools/build_bhl_base.py --out scratch/bhl-out --jobs 8
make verify                      # repository checks
```

`build_bhl_base.py` reproduces the CMake source lists, defines, and precompiled header from
`bhl-op4/CMakeLists.txt` and compiles with Zig's clang for `i386-unknown-linux-gnu`. Output is a
32-bit ELF `client.so` and `hl.so`, linked against a GLIBC 2.17 baseline. See
[`BHL_BASE_BUILD.md`](BHL_BASE_BUILD.md) for the full log and compatibility notes.

## Packaged builds

* `build-evidence/bhl-base-linux-mod/bhlop4-bhlbase-linux.zip`: the current Linux package
  (see its `MOD_MANIFEST.json`, `INSTALL.md`, and `RUNTIME_TESTS.md`).
* Windows build: see [`BHL_WINDOWS_BUILD.md`](BHL_WINDOWS_BUILD.md).

The `v0.1.0-linux32` GitHub release and `dist/` binaries come from the earlier OP4-based tree.
They are **legacy** and are not from the current `bhl-op4/` tree.

## Troubleshooting

| Message | Cause / fix |
|---|---|
| `This mod has detected that it is being run from a Valve game directory` | Files were copied into `gearbox/` or `valve/`. Use `bhlop4/` with `fallback_dir "gearbox"` |
| `could not load library client.so` | Built as 64-bit, or `libstdc++6-i386` is missing. Check with `ldd client.so` |
| `cannot open vgui.so` | Copy `vgui.so` from the Half-Life root folder, where the engine can find it |
| Missing OP4 maps or models | Check `fallback_dir "gearbox"` and `steam_appid.txt = 50` |

## Licenses

`client.so` and `hl.so` are derived from BugfixedHL (GPL-3.0) and OP4 / Valve HLSDK code, so
they follow those licenses. Do not add Valve binaries or `vgui.so` to any package. Read
[`LICENSES.md`](LICENSES.md) before distributing anything.

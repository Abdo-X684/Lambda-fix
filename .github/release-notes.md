# BHL × OP4 Speedrun — Linux 32-bit mod

## ⭐ Start here: `bhl-op4-mod.zip`

Extract it **next to** `valve/` and `gearbox/` in your Half-Life folder
(`Half-Life/bhlop4/`), then launch `-game bhlop4 -console -dev +exec speedrun.cfg`.
It contains `client.so`, `hl.so`, `liblist.gam`, `steam_appid.txt` (50),
`delta.lst`, `speedrun.cfg`, `splits/op4_route.json`, `INSTALL.md` and a sha256
`MANIFEST.json`.

**DO NOT copy `client.so`/`hl.so` into `gearbox/` or `valve/`.**
`halflife-op4-updated` has `UTIL_IsValveGameDirectory()` which aborts startup
for any mod folder starting with `valve`, `gearbox`, `bshift`, `dmc`, `cstrike`,
`czero`, `dod`, `ricochet` or `tfc` — that is the "Run this mod from its
intended location" error. The standalone `bhlop4/` folder with
`fallback_dir "gearbox"` reads OP4 assets from the official folder without
modifying it.

| Asset | Size | Purpose |
| --- | --- | --- |
| `bhl-op4-mod.zip` | ~9.3 MB | complete, ready-to-copy mod folder |
| `client.so` | 9,058,172 B | standalone client binary (`cl_dlls/`) |
| `hl.so` | 15,945,564 B | standalone server binary (`dlls/`) |
| `MANIFEST.json` | sha256 + ELF32 | verification |

Both libraries are **ELF 32-bit i386** (GoldSrc Linux cannot load 64-bit).
Verify with `MANIFEST.json` before use.

**Not included (by design):** the proprietary `vgui.so` and game assets — they
come from your own legally installed Half-Life: Opposing Force. `client.so` has
a `DT_NEEDED vgui.so` entry; only an empty link-time stub was used to build it,
and no Valve/Gearbox binary is redistributed.

Reproduce locally: `make mod` (or `make build-dlls-zig && make mod`).
Full details: `docs/BUILDING.md`.

Licenses: kit code is MIT; the binaries are derived from the OP4 SDK and remain
subject to its terms (`docs/LICENSES.md`). `delta.lst` is shipped from the SDK's
`network/` folder because every GoldSrc mod needs it.

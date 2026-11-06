# BHL × OP4 Speedrun — Linux 32-bit mod — v0.1.1

> The tag `v0.1.0-linux32` is a stable download channel: its four assets were
> replaced with the v0.1.1 build. Re-download from the same links below.

## v0.1.1 — "the merge is now actually visible"

The first build looked exactly like stock Opposing Force. Two real bugs:

* no `sr_*` cvar was registered on the client, so `CVAR_GET_FLOAT` returned 0
  and the whole HUD bailed out unless `+exec speedrun.cfg` ran early;
* the local `RunTimer` was never started, so nothing was drawn until the first
  server split (i.e. after finishing a map). The server cvars were unregistered
  too, which suppressed split broadcasts and console announces.

Now: every cvar is registered with a visible default on the correct side, the
timer starts at `CHud::Init()`, and there is an unmistakable green HUD banner
from frame one. Console banners and the `sr_status` command (`sr_version`
prints `0.1.1`) make it trivial to confirm that THESE binaries are loaded.

| Proof | Where |
| --- | --- |
| `[ BHL x OP4 SPEEDRUN ] v0.1.1` + `RTA` timer | top-left of the screen |
| `[BHLxOP4] client.so LOADED` / `server DLL LOADED` | console at startup |
| `sr_status` | console: version, map, timer, cvars, commands |
| `[BHLxOP4] speedrun.cfg loaded - glhf` | `+exec speedrun.cfg` ran |

If none of those appear, the game is running stock binaries — see
`INSTALL.md` inside the zip for the 5-point checklist (folder location,
`-game bhlop4`, `liblist.gam`, `vgui.so`, ELF32).

## ⭐ Start here: `bhl-op4-mod.zip`

Extract it **next to** `valve/` and `gearbox/` in your Half-Life folder
(`Half-Life/bhlop4/`) and launch
`hl_linux -game bhlop4 -console -dev +exec speedrun.cfg`.
It contains `client.so`, `hl.so`, `liblist.gam`, `steam_appid.txt` (50),
`delta.lst`, `speedrun.cfg`, `splits/op4_route.json`, `INSTALL.md` and a sha256
`MANIFEST.json`.

**DO NOT copy `client.so`/`hl.so` into `gearbox/` or `valve/`.**
`halflife-op4-updated` calls `UTIL_IsValveGameDirectory()`, which aborts startup
for any mod folder starting with `valve`, `gearbox`, `bshift`, `dmc`, `cstrike`,
`czero`, `dod`, `ricochet` or `tfc` — that is the "Run this mod from its
intended location" error. `bhlop4/` + `fallback_dir "gearbox"` reads OP4 assets
from the official folder without modifying it.

| Asset | Size | Purpose |
| --- | --- | --- |
| `bhl-op4-mod.zip` | ~9.3 MB | complete, ready-to-copy mod folder |
| `client.so` | 9,061,532 B | standalone client binary (`cl_dlls/`) |
| `hl.so` | 15,949,616 B | standalone server binary (`dlls/`) |
| `MANIFEST.json` | sha256 + ELF32 | verification |

Both libraries are **ELF 32-bit i386** (GoldSrc Linux cannot load 64-bit).
Verify with `MANIFEST.json` before use.

**Not included (by design):** the proprietary `vgui.so` and game assets — they
come from your own legally installed Half-Life: Opposing Force. `client.so` has
a `DT_NEEDED vgui.so` entry; only an empty link-time stub was used to build it,
and no Valve/Gearbox binary is redistributed.

Reproduce locally: `make build-dlls-zig && make mod`. Full details:
`docs/BUILDING.md`.

Licenses: kit code is MIT; the binaries are derived from the OP4 SDK and remain
subject to its terms (`docs/LICENSES.md`). `delta.lst` is shipped from the SDK's
`network/` folder because every GoldSrc mod needs it.

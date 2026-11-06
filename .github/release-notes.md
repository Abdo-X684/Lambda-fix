# BHL × OP4 Speedrun — Linux 32-bit binaries

Prebuilt GoldSrc libraries from the merged Opposing Force SDK tree, containing
the speedrun HUD, the authoritative `SRSplit` server→client message, PB splits,
auto-demo and the generated `speedrun.cfg` wiring.

| Asset | Size | Where to put it |
| --- | --- | --- |
| `client.so` | 9,058,172 B | `Half-Life/gearbox/cl_dlls/client.so` |
| `hl.so` | 15,945,564 B | `Half-Life/gearbox/dlls/hl.so` |
| `MANIFEST.json` | sha256 + ELF32 | verification only |

Both are **ELF 32-bit i386** (GoldSrc Linux cannot load 64-bit libraries).
Verify with `sha256sum -c` against `MANIFEST.json`, then launch with
`-game gearbox -console -dev +exec speedrun.cfg`.

**Not included (by design):** the proprietary `vgui.so` and the game assets.
They come from your own legally installed Half-Life: Opposing Force (Steam).
The client links with `DT_NEEDED vgui.so`, so the game supplies the real library
at runtime; only an empty link-time stub was used to build it. No Valve/Gearbox
binary is redistributed here.

Reproduce locally: `pip install ziglang && make build-dlls-zig` (no `gcc-multilib`
or `vgui.so` needed). Full details: `docs/BUILDING.md`.

Licenses: the kit's own code is MIT; these binaries are derived from the OP4
SDK and remain subject to its license terms — see `docs/LICENSES.md`.

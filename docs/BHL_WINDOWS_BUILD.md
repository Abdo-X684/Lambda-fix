# Windows build (DLL): same `bhl-op4` tree

> ⚠️ **The tables and hashes below are historical.** They describe the earlier MinGW/Zig build, which
> failed on `vgui2.dll`. The current binaries in [`MANIFEST.json`](../build-evidence/bhl-windows/MANIFEST.json)
> are built with **MSVC 19.44 / Win32** from the same `bhl-op4` tree, with all ten OP4 weapons and client
> prediction. They have **not been tested in the game** here.

A **Windows 32-bit** version was added next to the Linux version. No Linux file was deleted or replaced.
Everything Linux-related (`build-evidence/bhl-base/`, `tools/build_bhl_base.py`, CI) is unchanged, with the
same hashes.

## Output

| File | Type | Size | sha256 |
|---|---|---|---|
| `build-evidence/bhl-windows/client.dll` | PE32 i386 | 14,618,112 B | `cd3e192283d011511c0deb77566cd4fb6bfc3336066a1bc4090bbecaaa3d5509` |
| `build-evidence/bhl-windows/hl.dll` | PE32 i386 | 13,909,504 B | `4e635472b6a11f90cbd6561d44cabcaf3be95542aaa8d74d17aa13db81157af7` |

* Driver: `tools/build_bhl_windows.py` (Zig clang, `-target x86-windows-gnu`).
* BHL source lists for **Windows**, from `CMakeLists.txt`: client `139/139`, server `179/179`. All SDK and
  dependency units are clean, with **zero link gaps**.
* `client.dll` exports `101` symbols (including `ClientFactory`, `CreateInterface`, `HUD_*`,
  `CL_CreateMove`). `hl.dll` exports `715`. The lists are in `EXPORTS_client.txt` / `EXPORTS_hl.txt`.
* OP4 weapon symbols in the client objects: 9 `EV_*` + `SetLocalBody` + `g_iClub`
  ([`OP4_SYMBOLS.txt`](../build-evidence/bhl-windows/OP4_SYMBOLS.txt)).
* Imports: `tier0.dll`, `vstdlib.dll`, `dbghelp.dll`, `DINPUT8.dll`, `WS2_32.dll`, and the CRT / `KERNEL32` /
  `USER32` ([`IMPORTS.txt`](../build-evidence/bhl-windows/IMPORTS.txt)).
* Full evidence: [`MANIFEST.json`](../build-evidence/bhl-windows/MANIFEST.json), `BUILD_COMMANDS.txt`,
  `SOURCES.sha256`, `build.log`, and `patches/` (compatibility diffs applied to **temporary** copies of SDK
  headers and external Windows sources, not to the original tree).

## Limits of the evidence

* ✅ **Shown:** compilation and PE32 linking, sources, symbols, hashes, and exports / imports.
* ❌ **Not shown:** running on Windows, the GoldSrc engine, in-game tests, shooting, reload, ammo, models,
  animations, sound, or legal OP4 assets.
* ❌ **Not claimed:** that any OP4 weapon is "complete", or that the project is complete.
* The Windows build is **cross-compiled**. The DLL loader and dependencies (`SDL2.dll`, `tier0.dll`,
  `vstdlib.dll`, `steam_api.dll`) are provided by the engine at run time.

## Linux is unchanged

`client.so` = `3cae1d779c5a2a2d47e138baa43a45bb06d870037dd6da995f581532d32d9100`
`hl.so` = `09550d9b2acc2f0fca05857d8d6eaf3112f1fcf32d0fd40a6404884463f46cf1`
`make verify`, 30/30 tests, and `verify_bhl_base.py --compile` were green at the time of that build.

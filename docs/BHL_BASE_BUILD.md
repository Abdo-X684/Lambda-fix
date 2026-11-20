# Build evidence: real build of `bhl-op4/`

> **Status:** `client.so` and `hl.so` were built from the `bhl-op4/` tree. Both are ELF32 /
> Intel 80386, and our own build reports **zero** unresolved symbols
> (`unresolved_own_build_symbols: []`). The 12 link symbols were closed with real OP4
> implementations, documented in the build evidence.
>
> **The libraries have not been loaded inside the Half-Life engine and have not been tested in
> Opposing Force.** The reason is recorded in
> [`../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md`](../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md).
> The project is **not** declared complete.
>
> The numbers below are from the build before the later package edits (auto-update removal and
> the default HUD color). A rebuild is needed to match the current source.
>
> None of these binaries are related to `dist/dlls/*.so`, `dist/bhl-op4-mod.zip`, or release
> `v0.1.0-linux32`. Those are old OP4-root files; they were not changed and are not results.

## 1. Environment

The `bhl-op4/` tree is unmodified BugfixedHL-Rebased (694 BHL files). It needs CMake ≥ 3.25,
`nlohmann_json`, `unofficial-pcre` (PCRE1), Python 3.8 to below 4, Threads, SDL2, and `source_sdk`.
The engine is 32-bit. The sandbox has no `g++ -m32` and no 32-bit libstdc++, so the build uses
Zig's clang targeting `i386-unknown-linux-gnu`.

```bash
python3 -m venv /tmp/zenv
/tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
make fetch
#   .cache/upstreams/bugfixhl       = tmp64/BugfixedHL-Rebased @ 4d32095e3c33
#   .cache/upstreams/op4            = twhl-community/halflife-op4-updated @ 5368be7f8eba
#   .cache/upstreams/hl1_source_sdk = tmp64/hl1_source_sdk @ 11f26656677c881c7c630d03957900e7701da62e
```

| Package | Source | sha256 |
|---|---|---|
| nlohmann/json v3.11.3 | `https://codeload.github.com/nlohmann/json/tar.gz/v3.11.3` | `0d8ef5af7f9794e3263480193c491549b2ba6cc74bb018906202ada498a79406` |
| PCRE1 (luvit/pcre mirror) | `https://codeload.github.com/luvit/pcre/tar.gz/master` | `5aa545145f0c5a584b54a34f04c2d61c01d31724d3fbae2ee20cd8e3c422594d` |

32-bit link libraries come from the tree and the pinned SDK: `bhl-op4/lib/public/libSDL2-2.0.so.0`
and `.cache/upstreams/hl1_source_sdk/lib/public/{libtier0,libvstdlib,libsteam_api}.so`.

**CMake was not run in full.** `tools/build_bhl_base.py` copies the `SOURCE_FILES` lists
(including `if/elseif/else` branches and `list(APPEND)`), the definitions, the PCH, and the static
libraries from the real CMake files, then compiles with Zig-clang. This is a stated limit, not a
claim of a full configure.

## 2. Commands

```bash
export PYTHONDONTWRITEBYTECODE=1
python3 -m merge.bhl_base --out bhl-op4
python3 tools/build_bhl_base.py
python3 tools/verify_bhl_base.py --compile
make test-op4 test-op4-fixups
python3 tools/probe_runtime_environment.py
make verify
```

Generated evidence in `build-evidence/bhl-base/`:

| File | Content |
|---|---|
| `BUILD_COMMANDS.txt` | 454 compile and link commands |
| `SOURCES.sha256` | hashes of 459 input source files |
| `compile-units.json` | 446 compile units, all `ok` |
| `build.log` | full compile and link log |
| `UNDEFINED_SYMBOLS.txt` | full `nm -u` output for both libraries |
| `LINK_GAPS.md` | no unresolved symbols (0 gaps) |
| `MANIFEST.json` | hashes, ELF data, exports, `DT_NEEDED`, gaps |
| `patches/` | the three declared compatibility fixes |
| `RUNTIME_ENVIRONMENT.{json,md}` | why the build cannot be tested in the game here |

Each file hash in `MANIFEST.json` matches the file on disk (checked automatically).

## 3. Build log (stage summary)

```
=== bhl-op4 real 32-bit build ===
[deps] nlohmann: nlohmann-json-3.11.3.tar.gz sha256=0d8ef5af...a79406
[deps] pcre: pcre-master.tar.gz sha256=5aa54514...594d
[gen] appversion.h from bhl-op4/src/common/appversion.h.in
[gen] PCRE1 config.h / pcre.h from pcre.h.generic, config.h.generic
[compat] 3 build fixes written to build-evidence/bhl-base/patches
[cmake] client=139 server=179 common=8
[compile] client: 139/139 clean
[compile] server: 179/179 clean
[compile] tier1: 35/35 clean, tier2: 3/3 clean, vgui_controls: 68/68 clean
[compile] glad: 1/1 clean, semver: 1/1 clean, pcre: 20/20 clean
[link] client.so: 139 objects, 6 archives, 4 shared libs -> OK (27802960 bytes)
[link] hl.so: 179 objects, 1 archives, 0 shared libs -> OK (21232512 bytes)
[audit] client.so: 0 unresolved symbols from our own build
[audit] hl.so: 0 unresolved symbols from our own build
[done] 26.7s
```

Full log: `../build-evidence/bhl-base/build.log`.

## 4. Results

| File | Size (bytes) | sha256 | Exported | Undefined | `DT_NEEDED` |
|---|---|---|---|---|---|
| `build-evidence/bhl-base/client.so` | 27,802,960 | `3cae1d779c5a2a2d47e138baa43a45bb06d870037dd6da995f581532d32d9100` | 4,941 | 311 | `libSDL2-2.0.so.0`, `libtier0.so`, `libvstdlib.so`, `libm.so.6`, `libc.so.6`, `ld-linux.so.2` |
| `build-evidence/bhl-base/hl.so` | 21,232,512 | `09550d9b2acc2f0fca05857d8d6eaf3112f1fcf32d0fd40a6404884463f46cf1` | 4,467 | 156 | `libm.so.6`, `libc.so.6`, `ld-linux.so.2` |

The undefined symbols are provided by the engine or the system at load time (tier0/vstdlib,
SDL2, libc/libm, C++ ABI). They are not gaps from our build. The full list is in
`UNDEFINED_SYMBOLS.txt`, and the classification is in `tools/build_bhl_base.py::is_engine_or_libc_symbol`.

## 5. Errors and fixes (no shortcuts, nothing hidden)

| # | Error | Cause | Real fix |
|---|---|---|---|
| 1 | `ctfplay_gamerules.h:102,106,108,110`: `override` has no matching virtual in BHL; `bool` instead of `BOOL` | OP4-updated changed the `CGameRules` interface | Declared patches `bhl-ctf-nonvirtual-overrides` and `bhl-ctf-changeplayerteam-bools`. Only the `override` keyword was removed and one parameter type changed. Function bodies stay OP4 |
| 2 | `UTIL_FindEntitiesByClassname` missing in BHL | BHL only provides the single-result `UTIL_FindEntityByClassname` | `op4_entity_enumerator.h` contains the `dlls/util.h` code and calls BHL's own primitive. The BHL interface is unchanged |
| 3 | `CItemCTF.cpp:220`: `'CBasePlayer' does not refer to a value` | OP4 has a template `Instance<T>()` | Patch `bhl-instance-template` turns it into `static_cast<T*>(CBaseEntity::Instance(...))` |
| 4 | `gmsg*` undefined | `UserMessages.h` defines them `inline` (COMDAT) against BHL's strong definitions | Patch `bhl-ctf-usermsg-extern` changed them to `extern`. 13 OP4-only messages are defined in glue and registered from `GameDLLInit` |
| 5 | `GetLosingTeam(int&,int&)` gap after `CItemCTF.cpp` was wired | The function was in `ctfplay_gamerules.cpp`, which was not wired | Earlier, OP4's real body was in glue. **Now** `ctfplay_gamerules.cpp` is wired and owns the only definition |
| 6 | `op4_compat.h` includes BHL headers, so it cannot be included in a host test | Original file structure | The entity enumerator was split into a standalone `op4_entity_enumerator.h` so it can be tested directly |
| 7 | `hl_baseentity.cpp:309` in the OP4 client is `return flTime;` | A stub | **Rejected explicitly.** The real algorithm from `dlls/weapons.cpp:1069-1099` is used |

## 6. Not touched / not done

* `dist/dlls/client.so`, `dist/dlls/hl.so`, `dist/bhl-op4-mod.zip`, and release `v0.1.0-linux32`
  were not changed. Their hashes are unchanged.
* No PR to `main`, no release update, and no claim of license compliance for distributing the
  binaries (GPL-3.0 versus the non-commercial Valve license).
* **No test inside Opposing Force**: no engine load, no map, no HUD, no weapons, no runtime
  monster, rope, grapple, or CTF checks, and no crash monitoring. See
  `../build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md`.
* `dlls/ctf/ctfplay_gamerules.cpp` (the real CTF rules) is now wired. 25 OP4 files are still
  `port_pending` (21 client, 4 server; the server ones are excluded for stated reasons).

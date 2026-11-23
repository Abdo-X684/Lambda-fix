# Linux OP4 server (opfor.so) for the test package

Built from the same patched tree that produces the Windows `opfor.dll`
(`tools/prepare_op4_msvc_server.py --out build/op4-linux-tree`, upstream
`twhl-community/halflife-op4-updated` @ 5368be7f, via `python3 -m merge.cli fetch`).

- Sources: the 175 `ClCompile` entries of `projects/vs2019/hldll.vcxproj`
  (includes `dlls/bhl_server.cpp`, `dlls/sr_server.cpp`, `game_shared/sr_core.cpp`).
  The upstream `linux/Makefile.hldll` list does not include the BHL/speedrun files.
- Compiler: Zig 0.17.1 (clang), `-target x86-linux-gnu` for compile,
  `-target x86-linux-gnu.2.17` for link.
- Compile flags: `-std=c++17 -fpermissive -fno-strict-aliasing -fno-exceptions -w -O3
  -mcpu=pentium -mfpmath=387` plus the Makefile defines
  (`-DNDEBUG -DPOSIX -D_POSIX -DLINUX -D_LINUX -DGNUC -DNO_MALLOC_OVERRIDE -DCLIENT_WEAPONS`)
  and the vcxproj defines (`-DOPFOR -DVALVE_DLL -DQUIVER -DVOXEL -DQUAKE2`).
  Include dirs: `dlls engine common pm_shared game_shared public`.
- Link: `zig c++ -shared -Wl,-s ... -ldl -lpthread -lm`.
- Result: ELF32 i386, GLIBC max 2.17, exports `GiveFnptrsToDll`, `GetEntityAPI`,
  `GetEntityAPI2`, `GetNewDLLFunctions`. 143 undefined symbols, all from libc/libm/libdl/libpthread.
- Package: `gearbox_addon/dlls/opfor.so` (sha256 b7f1038a99a446c9..., see zip) with
  `liblist.gam` `gamedll_linux "dlls/opfor.so"` (no underscore in the path).

Not tested in game yet.

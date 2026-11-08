# Runtime environment: why there is NO in-game Opposing Force test

**Verdict: NOT EXECUTABLE.** This is a factual statement, not a claim of success.

Reproduce with `python3 tools/probe_runtime_environment.py`.

## Reasons

- No Half-Life engine binary (hl_linux/hw.so) and no vgui.so anywhere in the workspace.
- No legitimate Opposing Force assets (.bsp maps, .mdl models, .spr sprites, .wad textures, pak0.pak).
- No 32-bit dynamic loader ld-linux.so.2; a dynamically linked ELF32 process cannot start.
- A minimal dynamically linked ELF32 executable already fails to run (see elf32_execution_probe.dynamic_run); the delivered client.so/hl.so additionally need libSDL2-2.0.so.0, libtier0.so and libvstdlib.so, which are absent.
- The build environment is a headless x86-64 Linux sandbox without a legitimate Steam/HL installation; there is no display, no engine, and no user-supplied game assets. A library load or a menu screen would not be an in-game test.

## Probes

```json
{
  "delivered_libraries": {
    "client.so": {
      "elf32": true,
      "exists": true,
      "needed": [
        "libSDL2-2.0.so.0",
        "libtier0.so",
        "libvstdlib.so",
        "libm.so.6",
        "libc.so.6",
        "ld-linux.so.2"
      ]
    },
    "hl.so": {
      "elf32": true,
      "exists": true,
      "needed": [
        "libm.so.6",
        "libc.so.6",
        "ld-linux.so.2"
      ]
    }
  },
  "elf32_dynamic_loader_paths_present": [],
  "elf32_execution_probe": {
    "compiler": "/tmp/zig32",
    "dynamic_build_rc": 0,
    "dynamic_build_stderr": "",
    "dynamic_command": "/tmp/zig32 /tmp/op4-runtime-wmdalbqi/run32.cpp -o /tmp/op4-runtime-wmdalbqi/run32",
    "dynamic_run": {
      "error": "FileNotFoundError: [Errno 2] No such file or directory: '/tmp/op4-runtime-wmdalbqi/run32'",
      "rc": null
    },
    "raw_zig": "/tmp/zenv/lib/python3.11/site-packages/ziglang/zig",
    "source": "#include <cstdio>\nint main(){printf(\"ELF32-RUN-OK\\n\");return 0;}\n",
    "static_build_rc": 0,
    "static_build_stderr": "",
    "static_command": "/tmp/zenv/lib/python3.11/site-packages/ziglang/zig c++ -target x86-linux-musl -static /tmp/op4-runtime-wmdalbqi/run32.cpp -o /tmp/op4-runtime-wmdalbqi/run32s",
    "static_run": {
      "rc": 0,
      "stderr": "",
      "stdout": "ELF32-RUN-OK"
    }
  },
  "elf32_shared_libraries": {
    "libSDL2-2.0.so.0": [],
    "libtier0.so": [],
    "libvstdlib.so": []
  },
  "engine_files_found": {},
  "op4_asset_files_found": {},
  "standalone_bhlop4": {
    "contents": [
      "INSTALL.md",
      "MANIFEST.json",
      "cl_dlls",
      "delta.lst",
      "dlls",
      "liblist.gam",
      "speedrun.cfg",
      "splits",
      "steam_appid.txt"
    ],
    "exists": true
  }
}
```

## What WAS tested

- ELF32 compilation of every translation unit into relocatable i386 objects
- static link of both shared libraries with a full undefined-symbol audit
- nm/objdump verification that all 12 former link gaps are real, non-empty definitions
- host-executed functional tests of the exact OP4 GetNextAttackDelay and entity-enumerator code
- provenance and declared-BHL-change verification

## What was NOT tested (explicit incomplete list)

- Loading client.so/hl.so into a real HL engine without errors.
- Starting an actual Opposing Force map.
- HUD/UI rendering, VGUI, flag icons, scoreboard.
- BHL weapons and OP4 weapons: switching, ammo, reload, firing.
- Monster shock effect, rope physics, grapple hook, CTF flag capture in-game.
- Crash / runtime-error monitoring over a real play session.
- Retest after the final edit inside a real game session.

No result above is inferred from compilation, CI, a menu, or a library load.

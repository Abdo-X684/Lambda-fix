# Source audit

This document lists where each part of the package comes from. It audits source files and licenses only.
It does not show that any weapon works in game. Use `RUNTIME_TESTS.md` for test status.

## Sources (pinned)

| Role | Repository | Commit |
| --- | --- | --- |
| Opposing Force weapons and server | [twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated) | `5368be7f8eba14b05236c7c52ad5f6b11fd95e55` |
| BugfixedHL base (client, VGUI2, movement) | [tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased) | `4d32095e3c33d5ca60809d9c51f8aafe51c0a521` |
| Valve HLSDK | [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife) | `b1b5cf5892918535619b2937bb927e46cb097ba1` |
| Build SDK (libraries) | [tmp64/hl1_source_sdk](https://github.com/tmp64/hl1_source_sdk) | `11f2665` |

## Opposing Force weapons

All ten weapons come from the same OP4 repository and commit above:
Desert Eagle, Pipe Wrench, M249, Displacer, Shock Rifle, Spore Launcher, Sniper Rifle, Knife, Penguin, Grapple.

Models, sounds, maps, and music are not in this repository or the package. They are read from your installed `gearbox/` folder.

## Changes

- The BugfixedHL client was merged with the OP4 weapon prediction and event code.
- `client.so` links clean-room replacements for `tier0` and `vstdlib` (`tools/linux_shims/`). They are MIT licensed.
- PCRE tables come from the PCRE default table file (`pcre_chartables.c`).
- The client is built with `-O2` and without Zig's runtime safety checks.
- Advanced > About: the auto-update option and its controls were removed.
- Default `hud_color` changed to `0 160 0` (green).

## Licenses

See `LICENSES/` and `NOTICE.txt` in this package.

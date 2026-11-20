# Roadmap (current status)

## Done (source and package level)

* Pinned upstream fetch (commit + sha256), the merge tooling, and `bhl-op4/` (BugfixedHL base with
  OP4 weapons and systems merged in, with provenance for every file).
* 32-bit Linux `client.so` and `hl.so` built from `bhl-op4/` (no unresolved symbols from our own build).
* Ten OP4 weapons compiled to ELF32 objects; the BHL server sources that are wired into CMake compile.
* Linux package with `MOD_MANIFEST.json`, English install and test documents, and the OP4 media setup
  script (copies the user's own MP3 files only).
* Advanced > About: auto-update entry removed (source level).
* Default HUD color set to OP4 green, `0 160 0` (source level).
* Dashboard and documents in English.

## Not yet verified (needs the user's machine)

1. In-game check of the Linux package: every chapter, every weapon (select, fire, reload,
   ammo, sound, model, effects), menus, and the HUD color and About changes.
2. Windows: the MSVC DLL build (`build-evidence/bhl-windows/`) has not been run in the game. The GitHub
   Actions Windows workflow failed before any step ran; see [`BHL_WINDOWS_BUILD.md`](BHL_WINDOWS_BUILD.md).
3. Timing on real hardware, compared with speedrun.com.

## Open decisions

* The Adrenaline Gamer sprites (`sprites/ag_ctf.spr`, `ag_ctf_score.spr`) have no confirmed license.
  They are loaded by the CTF HUD on non-AG clients. Options: confirm the license, or remove them with the
  matching code change.
* Mod name: `lambda-fix` (chosen by the project owner). Confirm that the name is cleared for distribution, and do not use the Lambda logo.
* Feature list for the final release.

## Optional later improvements

* HUD with sprites, configurable colors, and `hud_scale` / 4K support.
* Split export in LiveSplit format; separate Boot Camp and scripted categories.
* Automated movement tests (bhop cap) inside the game.
* Periodic re-run of `make fetch && make bhl-base && make verify` in CI to catch source drift early.

## Principles

No hidden conflicts, no fake cvars, no blind injection, and no "ready" claim before `make verify`.
Each decision is recorded in [`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md) and in the package's
`SOURCE_AUDIT.md`.

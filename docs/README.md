# Documentation index

Current status of the weapons and the build: [`WEAPON_INVENTORY.md`](WEAPON_INVENTORY.md).

| File | Content |
| --- | --- |
| [WEAPON_INVENTORY.md](WEAPON_INVENTORY.md) | Current status of the ten OP4 weapons (generated from source). |
| [BHL_BASE_MERGE.md](BHL_BASE_MERGE.md) | Current architecture reference: BHL base plus OP4 weapons and systems. |
| [BHL_BASE_BUILD.md](BHL_BASE_BUILD.md) | Build record for `client.so` and `hl.so`: commands, logs, hashes. |
| [BHL_WINDOWS_BUILD.md](BHL_WINDOWS_BUILD.md) | Windows build of the same tree (`client.dll` / `hl.dll`, PE32). |
| [BUILDING.md](BUILDING.md) | Legacy build notes (earlier OP4-based tree). |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Legacy layers of the earlier phase. |
| [BHL_MERGE.md](BHL_MERGE.md) | Legacy description of `bhl-systems-1` on the OP4-based tree. |
| [RESOLUTION.md](RESOLUTION.md) | How the 127 conflicts and deferred ports were resolved. |
| [OP4_SOURCE_AUDIT.md](OP4_SOURCE_AUDIT.md) | Source and asset audit: repositories, commits, licenses. |
| [OP4_RUNTIME_TESTS.md](OP4_RUNTIME_TESTS.md) | In-game test table. Every row is untested unless reported. |
| [SPEEDRUN.md](SPEEDRUN.md) | Timer, `SRSplit`, splits, PB, legitimacy, demos. |
| [UPSTREAMS.md](UPSTREAMS.md) | Pinned sources, sha256, licenses, and why code is not committed. |
| [LICENSES.md](LICENSES.md) | License obligations before any distribution. |
| [ROADMAP.md](ROADMAP.md) | What is done, what needs the game environment, optional improvements. |

From the root: [`README.md`](../README.md) for a quick start,
[`CONTRIBUTING.md`](../CONTRIBUTING.md) to add a rule or update a pin,
and [`tests/fixtures/README.md`](../tests/fixtures/README.md) for fixtures.

Every local link in these documents is checked by `make hygiene`.

These documents are also shown in the project dashboard: run `make serve` and open the
"README and docs" tab, or `/#docs`. Any new `.md` file in `docs/` appears automatically
once it is added to this index.

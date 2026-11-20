# Pinned upstream sources

| Name | Role | Repository | Commit | sha256 (first 16) | License |
| --- | --- | --- | --- | --- | --- |
| `op4` | target | `twhl-community/halflife-op4-updated` | `5368be7f8eba` | `c65e53713b5ef2d3a` | Valve HLSDK + TWHL |
| `bugfixhl` | donor | `tmp64/BugfixedHL-Rebased` | `4d32095e3c33` | `a70ab961de1c40f6` | GPL-3.0 |
| `valve_hlsdk` | base | `ValveSoftware/halflife` | `b1b5cf589291` | `f5e7793f974bc02d` | Valve HLSDK |

The full values are in `upstreams.json`. `fetch.py` checks **sha256 and size** before
extraction, rejects archive path traversal, symlinks, and binary files, and writes
`.cache/upstreams/<name>/.FETCHED.json` so the download can be cached.

## Why don't we include the code in the repository?

1. The Valve SDK license restricts redistribution. GPL-3.0 imposes obligations on derived work.
2. About 21 MB of archives and about 2,600 files are not needed in git.
3. Pinning with a SHA and checksum produces a reproducible result, which is better than a stale copy.

## Offline fixtures

`tests/fixtures/upstreams/` contains small copies with the same paths and the same anchors
for the files used by the merge plan (schema 2) and the audits. They are used in CI and in tests
without network access. `valve_hlsdk` is now only a placeholder folder, because `three_way` is
not used in the current plan. It stays pinned as a shared base for future rules, and is tested
through `ConflictPolicyTests`. Details are in [`tests/fixtures/README.md`](../tests/fixtures/README.md).

Any change to the real source layout must be reflected here. Otherwise `anchor_drift` reveals it
immediately, and `make hygiene` checks that each pinned source has a folder.

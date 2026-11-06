# Offline fixtures

Tiny stand-ins for the three pinned SDKs, used by `make verify`,
`python3 -m merge.cli run --offline` and the dashboard — no network needed.

| dir | what it must contain |
| --- | --- |
| `upstreams/op4` | the target tree: files with the exact injection anchors, the audit patterns, OP4-only files (`CDisplacer.cpp`), and the 4 build files patched by `merge/projects.py` |
| `upstreams/bugfixhl` | only the 5 files copied into `integration/ports/` by the `copy` rules |
| `upstreams/valve_hlsdk` | placeholder only — see its README |

Rules of thumb:

* Anchors in `op4/` are literal strings from the pinned upstream commit; changing
  one without updating `merge/plan.json` produces `anchor_drift` and fails `--strict`.
* Audit patterns in `op4/` mirror the real OP4 source lines documented in
  `docs/RESOLUTION.md`.
* Extra `op4` files (`player.cpp`, `bitvec.h`, `hl_baseentity.cpp`, `BUILDING.md`)
  exist so the fixture behaves like a real SDK tree and so
  `test_op4_only_content_survives` can prove target content is never dropped.
* Never put real upstream source here: it is licensed separately and belongs in
  `.cache/upstreams/` after `make fetch`.

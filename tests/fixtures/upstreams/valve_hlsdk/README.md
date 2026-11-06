# valve_hlsdk (offline fixture placeholder)

`upstreams.json` still pins the vanilla HLSDK as the common ancestor (`role: base`)
for future `three_way` rules. The shipped `merge/plan.json` (schema 2) uses
equivalence audits instead, so no fixture file is needed here today.

This directory must exist because `merge.fetch.resolve_sources()` validates one
directory per pinned upstream, even in `--offline` mode. Three-way merge
behaviour is covered independently by `tests/test_engine.py::ConflictPolicyTests`,
which builds its own base/ours/theirs trees in a temp dir.

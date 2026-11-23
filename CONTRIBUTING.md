# Contributing

Golden rule: **do not add implicit changes**. Every change to the OP4 tree must be declared as a rule in
`merge/plan.json`, and every external source must be pinned in `upstreams.json`.

## Before any commit

```bash
make hygiene     # text, JSON, imports, markdown links, docs index
make verify      # Python tests + C++ checks + generation + merge + package
make fetch && make merge && make verify-sdk   # if you changed pins or injection points
```

`make tidy` removes `__pycache__` and orphaned `.stage-*` folders, then runs the hygiene check again.

## Where does each change go?

| I want to… | Location |
| --- | --- |
| Add a new merge, injection, or audit rule | `merge/plan.json` (plus a snippet in `integration/snippets/` if needed) |
| Change merge engine behavior | `merge/engine.py` + a test in `tests/` |
| C++ code shared by tests and the game | `src/speedrun/`, then a `copy` rule to `game_shared/` |
| Glue that depends on the Half-Life engine | `overlay/cl_dll/` or `overlay/dlls/` + update `merge/projects.py` |
| Map, chapter, or cvar | `data/`, then `python3 tools/gen_route_header.py --write` |
| Test | `tests/test_*.py` or `tests/cpp/test_speedrun.cpp` |
| Change the docs viewer | `web/markdown.py` + `tests/test_markdown.py` (check escaping and links) |
| Build the DLLs | `tools/build_dlls.py`; `make build-dlls-check` does not need a 32-bit toolchain |

## Adding an `inject` rule

1. Make sure the anchor appears **only once** in the real file:
   `grep -c "<anchor>" .cache/upstreams/op4/<path>`.
2. Write the snippet in `integration/snippets/`, add the rule, then update the matching fixture
   in `tests/fixtures/upstreams/op4/` with the same anchor.
3. Run `python3 -m merge.cli run --offline --strict`, then the real merge.

## Updating a pin

Change `ref`, `tarball.sha256`, and `tarball.bytes` in `upstreams.json` (check the commit first),
then run `python3 -m merge.cli fetch --force` and `make merge`, and review
`build/merged-real/MERGE_REPORT.md`. Any `anchor_drift` means upstream changed. Do not hide it:
update the rule and document the change.

## Style

Python 3.9+ with no dependencies, C++17, UTF-8 text with LF line endings and a final newline,
no trailing spaces. `tools/check_hygiene.py` enforces this.

"""Path translation between the two SDK layouts used by this merge.

BugfixedHL-Rebased reorganised the HLSDK into ``src/game/{client,server,shared}``
while the Opposing Force SDK keeps Valve's classic ``cl_dll`` / ``dlls`` /
``game_shared`` layout.  A naive copy therefore lands files in directories that
the OP4 build system does not compile.  Every path that crosses the boundary in
this project goes through :func:`to_classic` / :func:`to_bhl`.
"""

from __future__ import annotations

import re
from typing import Iterable

# Longest prefixes first is not required here (they are disjoint), but keeping
# them ordered longest-first makes the table robust to future additions.
BHL_TO_CLASSIC = (
    ("src/game/client/", "cl_dll/"),
    ("src/game/server/", "dlls/"),
    ("src/game/shared/", "game_shared/"),
    ("src/bugfixedapi_amxx/", "bugfixedapi_amxx/"),
    ("src/pm_shared/", "pm_shared/"),
    ("src/common/", "common/"),
    ("src/public/", "public/"),
    ("src/engine/", "engine/"),
    ("src/tests/", "tests/"),
)

_INCLUDE_RE = re.compile(r'(^[ \t]*#[ \t]*include[ \t]*[<"])([^>"]+)([>"])', re.M)


def _norm(path: str) -> str:
    path = path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def to_classic(path: str) -> str:
    """``src/game/server/player.cpp`` -> ``dlls/player.cpp``.

    Unknown paths are returned normalised but unchanged, which is what we want
    for files that already use the classic layout.
    """
    p = _norm(path)
    for src, dst in BHL_TO_CLASSIC:
        if p.startswith(src):
            return dst + p[len(src):]
    return p


def to_bhl(path: str) -> str:
    """Inverse of :func:`to_classic` for classic-layout paths."""
    p = _norm(path)
    for src, dst in BHL_TO_CLASSIC:
        if p.startswith(dst):
            return src + p[len(dst):]
    return p


def rewrite_includes(
    text: str,
    extra: Iterable[tuple[str, str]] = (),
) -> tuple[str, int]:
    """Rewrite ``#include`` paths that use BHL repository-root prefixes.

    ``extra`` holds ``(old_prefix, new_prefix)`` pairs applied to the include
    string (useful for BHL-relative includes such as ``hud/timer.h``).  Returns
    the new text and the number of rewritten includes so the merge report can
    prove that a ported file was actually adapted.
    """
    rules = list(extra)
    count = 0

    def repl(match: re.Match) -> str:
        nonlocal count
        inc = match.group(2)
        new = inc
        for old, replacement in rules:
            if inc.startswith(old):
                new = replacement + inc[len(old):]
                break
        else:
            if inc.startswith("src/"):
                new = to_classic(inc)
        if new != inc:
            count += 1
        return match.group(1) + new + match.group(3)

    return _INCLUDE_RE.sub(repl, text), count


def is_safe_relative(path: str) -> bool:
    """Guard against path traversal in manifest rules and tar extraction."""
    p = _norm(path)
    return bool(p) and not p.startswith("/") and ".." not in p.split("/")

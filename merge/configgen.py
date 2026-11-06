"""Generate ``speedrun.cfg`` and validate the OP4 route data.

One JSON file is the single source of truth for the route: it feeds the C++
header generator, the dashboard, the cfg comments, and the tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RouteError(ValueError):
    pass


def load_json(root: Path, filename: str) -> dict[str, Any]:
    path = root / "data" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def load_route(root: Path) -> dict[str, Any]:
    return load_json(root, "op4_route.json")


def route_maps(route: dict[str, Any], include_boot_camp: bool = False) -> list[str]:
    maps = [m for ch in route["chapters"] for m in ch["maps"]]
    if include_boot_camp:
        maps += list(route["boot_camp"]["maps"])
    return maps


def validate_route(root: Path) -> list[str]:
    """Return a list of problems (empty == valid)."""
    route = load_route(root)
    problems: list[str] = []
    seen: dict[str, str] = {}
    ids: set[str] = set()
    chapters = route.get("chapters", [])
    if not chapters:
        problems.append("route has no chapters")
    for i, ch in enumerate(chapters):
        cid = ch.get("id", "")
        if not cid or cid in ids:
            problems.append(f"chapter {i}: missing or duplicate id {cid!r}")
        ids.add(cid)
        if not ch.get("maps"):
            problems.append(f"chapter {cid}: no maps")
        for m in ch.get("maps", []):
            if m in seen:
                problems.append(f"map {m!r} appears twice ({seen[m]} and {cid})")
            seen[m] = cid
            if not m.startswith("of"):
                problems.append(f"map {m!r} in {cid} does not look like an OP4 map name")
    for m in route.get("boot_camp", {}).get("maps", []):
        if m in seen:
            problems.append(f"boot camp map {m!r} collides with the main route ({seen[m]})")
    return problems


def render_config(root: Path) -> str:
    route = load_route(root)
    cvars = load_json(root, "cvars.json")["cvars"]
    lines: list[str] = [
        "// ---------------------------------------------------------------------",
        "// BugfixedHL x Opposing Force - Speedrun Merge Kit",
        "// Generated from data/cvars.json and data/op4_route.json. DO NOT EDIT.",
        "// Regenerate with: python3 -m merge.cli config --out gamedir/speedrun.cfg",
        "// ---------------------------------------------------------------------",
        "// Route: " + route["route_id"] + " (" + str(len(route_maps(route))) + " maps, "
        + str(len(route["chapters"])) + " splits by chapter)",
        "//",
    ]
    for ch in route["chapters"]:
        lines.append(f"//   {ch['id']}  {ch['name']:<24} {', '.join(ch['maps'])}")
    lines += [
        "//",
        "// LEGALITY: sv_cheats stays 0. A run with cheats enabled is not submitted.",
        "//",
        "",
        "clear",
    ]
    last_category = ""
    for cvar in cvars:
        if cvar["category"] != last_category:
            last_category = cvar["category"]
            lines.append(f"// --- {last_category} " + "-" * max(0, 50 - len(last_category)))
        lines.append(f"// {cvar['desc']}")
        lines.append(f"{cvar['name']} \"{cvar['value']}\"")
    lines += [
        "",
        "// --- binds (F5/F6 keep jump and use untouched) ----------------------",
        'alias sr_split_now "sr_split"',
        'alias sr_reset_now "sr_reset"',
        'bind "F5" "sr_reset_now"',
        'bind "F6" "sr_split_now"',
        'bind "F7" "sr_practice_toggle"',
        "",
        "// --- stream / demo --------------------------------------------------",
        "echo \"[BHLxOP4] speedrun.cfg loaded - glhf\"",
        "",
    ]
    return "\n".join(lines)


def write_config(root: Path, out: Path) -> str:
    text = render_config(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return text

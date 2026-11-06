"""Loading and validation of ``upstreams.json`` and ``merge/plan.json``.

The manifest is the contract of the whole project: upstreams are pinned to
commit SHAs *and* tarball checksums, and every change made to the OP4 tree is
declared as a rule.  Nothing is applied implicitly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .layout import is_safe_relative

ACTIONS = {"three_way", "copy", "inject", "generate", "skip"}
CONFLICT_POLICIES = {"marker", "ours", "theirs", "fail"}
GENERATORS = {"speedrun_cfg", "route_json"}
WHERE = {"before", "after"}


class ManifestError(ValueError):
    """Raised when a manifest is missing, malformed or internally inconsistent."""


@dataclass(frozen=True)
class Upstream:
    name: str
    role: str
    repo: str
    ref: str
    layout: str
    license: str
    about: str
    tarball: dict[str, Any]


@dataclass(frozen=True)
class Rule:
    id: str
    action: str
    path: str
    raw: dict[str, Any] = field(repr=False)

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)


@dataclass(frozen=True)
class Plan:
    name: str
    target: str
    description: str
    rules: tuple[Rule, ...]
    raw: dict[str, Any] = field(repr=False)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f"missing manifest: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"{path} must contain a JSON object")
    return data


def load_upstreams(root: Path) -> dict[str, Upstream]:
    data = _read_json(root / "upstreams.json")
    out: dict[str, Upstream] = {}
    for entry in data.get("upstreams", []):
        try:
            u = Upstream(
                name=entry["name"],
                role=entry["role"],
                repo=entry["repo"],
                ref=entry["ref"],
                layout=entry["layout"],
                license=entry["license"],
                about=entry.get("about", ""),
                tarball=entry["tarball"],
            )
        except KeyError as exc:
            raise ManifestError(f"upstream entry missing {exc} in upstreams.json") from exc
        if u.name in out:
            raise ManifestError(f"duplicate upstream name: {u.name}")
        if len(u.ref) != 40 or not all(c in "0123456789abcdef" for c in u.ref):
            raise ManifestError(f"upstream {u.name}: ref must be a full 40-char commit SHA")
        sha = u.tarball.get("sha256", "")
        if len(sha) != 64:
            raise ManifestError(f"upstream {u.name}: tarball.sha256 must be a sha256 digest")
        out[u.name] = u
    if not out:
        raise ManifestError("upstreams.json contains no upstreams")
    return out


def load_plan(root: Path) -> Plan:
    data = _read_json(root / "merge" / "plan.json")
    rules = tuple(
        Rule(id=r.get("id", f"rule-{i}"), action=r.get("action", ""), path=r.get("path", ""), raw=r)
        for i, r in enumerate(data.get("rules", []))
    )
    return Plan(
        name=data.get("name", "unnamed"),
        target=data.get("target", ""),
        description=data.get("description", ""),
        rules=rules,
        raw=data,
    )


def validate_plan(plan: Plan, upstreams: dict[str, Upstream]) -> list[str]:
    """Return a list of human-readable errors (empty means valid)."""
    errors: list[str] = []
    if plan.target not in upstreams:
        errors.append(f"plan.target '{plan.target}' is not a known upstream")
    if not plan.rules:
        errors.append("plan contains no rules")

    seen: set[str] = set()
    for rule in plan.rules:
        tag = f"rule '{rule.id}'"
        if rule.id in seen:
            errors.append(f"duplicate rule id: {rule.id}")
        seen.add(rule.id)
        if rule.action not in ACTIONS:
            errors.append(f"{tag}: unknown action '{rule.action}'")
            continue
        if not rule.path or not is_safe_relative(rule.path):
            errors.append(f"{tag}: path must be a safe relative path, got {rule.path!r}")

        specs: list[str] = []
        if rule.action == "three_way":
            for key in ("base", "ours", "theirs"):
                if key not in rule.raw:
                    errors.append(f"{tag}: three_way needs '{key}'")
                else:
                    specs.append(rule.raw[key])
            policy = rule.get("on_conflict", "marker")
            if policy not in CONFLICT_POLICIES:
                errors.append(f"{tag}: bad on_conflict '{policy}'")
        elif rule.action == "copy":
            if "from" not in rule.raw:
                errors.append(f"{tag}: copy needs 'from'")
            else:
                specs.append(rule.raw["from"])
            for pair in rule.get("include_rewrites", []):
                if not (isinstance(pair, list) and len(pair) == 2):
                    errors.append(f"{tag}: include_rewrites entries must be [from, to] pairs")
        elif rule.action == "inject":
            for key in ("anchor", "snippet"):
                if key not in rule.raw:
                    errors.append(f"{tag}: inject needs '{key}'")
            if "snippet" in rule.raw:
                specs.append(rule.raw["snippet"])
            if rule.get("where", "after") not in WHERE:
                errors.append(f"{tag}: 'where' must be before or after")
            if rule.get("anchor_count", 1) != 1:
                errors.append(f"{tag}: anchor_count must be 1 (anchors must be unique)")
        elif rule.action == "generate":
            if rule.get("generator") not in GENERATORS:
                errors.append(f"{tag}: unknown generator '{rule.get('generator')}'")

        for spec in specs:
            name, _, rel = str(spec).partition(":")
            if not rel or not is_safe_relative(rel):
                errors.append(f"{tag}: bad source spec '{spec}'")
            elif name not in upstreams and name not in {"repo", "overlay"}:
                errors.append(f"{tag}: source '{name}' is not a known upstream")

    return errors


def split_spec(spec: str) -> tuple[str, str]:
    """``'bugfixhl:src/...'`` -> ``('bugfixhl', 'src/...')``."""
    name, sep, rel = spec.partition(":")
    if not sep or not rel:
        raise ManifestError(f"source specs must look like 'source:path', got {spec!r}")
    return name, rel

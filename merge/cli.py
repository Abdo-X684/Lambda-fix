"""Command line entry point: ``python3 -m merge.cli <command>``."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .configgen import (
    load_route,
    render_config,
    route_maps,
    validate_route,
    write_config,
)
from .engine import MergeEngine
from .fetch import fetch_all, resolve_sources
from .manifest import load_plan, load_upstreams, validate_plan

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(root: Path):
    upstreams = load_upstreams(root)
    plan = load_plan(root)
    errors = validate_plan(plan, upstreams)
    if errors:
        raise SystemExit("manifest errors:\n  - " + "\n  - ".join(errors))
    return upstreams, plan


def cmd_plan(args: argparse.Namespace) -> int:
    upstreams, plan = _load(args.root)
    print(f"project : {plan.name}  (target={plan.target})")
    print(f"about   : {plan.description}")
    print("upstreams:")
    for u in upstreams.values():
        print(f"  {u.name:<12} {u.role:<7} {u.repo} @ {u.ref[:12]}  [{u.license}]")
    print(f"rules ({len(plan.rules)}):")
    for r in plan.rules:
        print(f"  {r.id:<26} {r.action:<9} {r.path}")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    upstreams, _ = _load(args.root)
    for info in fetch_all(args.root, upstreams, force=args.force):
        print(f"[{info['status']:>7}] {info['name']:<12} {info['ref'][:12]} "
              f"sha256={str(info['sha256'])[:12]}... files={info.get('files', '?')}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    upstreams, plan = _load(args.root)
    mode = "offline" if args.offline else "upstream"
    sources = resolve_sources(args.root, upstreams, offline=args.offline)
    out = Path(args.out)
    if not out.is_absolute():
        out = args.root / out
    engine = MergeEngine(
        root=args.root,
        plan=plan,
        upstreams=upstreams,
        sources=sources,
        mode=mode,
        out=out,
        strict=args.strict,
        patch_build=not args.no_patch_projects,
    )
    try:
        report = engine.run()
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"merge failed: {exc}", file=sys.stderr)
        return 1
    s = report["summary"]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"mode={mode}  tree={out}  files={s['tree_files']}  tree_sha256={report['tree_hash'][:16]}...")
        print("  merged={merged} unchanged={unchanged} conflicts={conflicts} deferred={deferred} "
              "added={added} injected={injected} generated={generated} patched={patched}".format(**s))
        print(f"  anchor_drift={s['anchor_drift']} missing={s['missing']} errors={s['errors']}")
        for w in report["warnings"]:
            print(f"  ! {w}")
        print(f"report: {out / 'MERGE_REPORT.md'}")
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    problems = validate_route(args.root)
    from tools.gen_route_header import check_header  # type: ignore[import-not-found]

    problems += check_header(args.root)
    if problems:
        for p in problems:
            print(f"  ! {p}", file=sys.stderr)
        return 1
    route = load_route(args.root)
    maps = route_maps(route)
    print(f"OK: {len(route['chapters'])} chapters, {len(maps)} maps, "
          f"{len(route['boot_camp']['maps'])} boot camp maps, C++ header in sync")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    root = args.root
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = root / out
        write_config(root, out)
        print(f"wrote {out}")
    else:
        print(render_config(root), end="")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    return subprocess.call(
        [sys.executable, "-m", "unittest", "discover", "-s", str(args.root / "tests"),
         "-p", "test_*.py", "-v"],
        cwd=args.root,
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="merge", description="BugfixedHL x Opposing Force speedrun merge kit"
    )
    p.add_argument("--root", type=Path, default=ROOT, help="repository root (default: %(default)s)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("plan", help="show pinned upstreams and the merge rule list")
    f = sub.add_parser("fetch", help="download pinned + checksum-verified upstream SDKs")
    f.add_argument("--force", action="store_true")
    r = sub.add_parser("run", help="build the merged tree")
    r.add_argument("--offline", action="store_true", help="use tests/fixtures/upstreams (no network)")
    r.add_argument("--strict", action="store_true", help="fail on errors, anchor drift or conflicts")
    r.add_argument("--out", default="build/merged", help="output directory")
    r.add_argument("--json", action="store_true", help="print the full report as JSON")
    r.add_argument("--no-patch-projects", action="store_true")
    rt = sub.add_parser("route", help="validate route data + generated C++ header")
    rt.add_argument("--check", action="store_true", help="check-only (default behaviour, kept for CI)")
    c = sub.add_parser("config", help="render speedrun.cfg")
    c.add_argument("--out", help="write to this path instead of stdout")
    sub.add_parser("verify", help="run the python test suite")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers: dict[str, Any] = {
        "plan": cmd_plan,
        "fetch": cmd_fetch,
        "run": cmd_run,
        "route": cmd_route,
        "config": cmd_config,
        "verify": cmd_verify,
    }
    return int(handlers[args.command](args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())

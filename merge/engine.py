"""The merge engine.

Strategy (in order):

1. Copy the OP4 SDK (the *target*) into a staging directory.
2. ``three_way``: ``git merge-file`` with vanilla HLSDK as the common ancestor,
   OP4 as "ours", BugfixedHL as "theirs".  Conflicting hunks are quarantined
   instead of being written into buildable source files.
3. ``copy``: port donor files for reference (path-translated, provenance banner)
   and inject this kit's own speedrun sources.
4. ``generate``: emit cfg / route data.
5. ``inject``: hook into OP4 functions using unique, anchor-checked snippets.
6. Patch the VS projects and Linux makefiles so the new sources actually build.
7. Write a deterministic report and atomically swap the staging tree into place.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import configgen, projects
from .layout import is_safe_relative, rewrite_includes
from .manifest import Plan, split_spec
from .report import compute_tree_hash, render_markdown

SKIP_DIRS = {".git", ".github", "build", "dist", "__pycache__", "CMakeFiles"}
SKIP_SUFFIXES = {
    ".dll", ".lib", ".so", ".dylib", ".exe", ".pdb", ".obj", ".o", ".a",
    ".zip", ".7z", ".png", ".jpg", ".bmp", ".tga", ".wav", ".mp3", ".pyc",
}
MAX_FILE_BYTES = 4 * 1024 * 1024


class MergeError(RuntimeError):
    pass


def _read(path: Path) -> str:
    # newline='' preserves CRLF in upstream SDK files; Path.read_text() has no
    # newline parameter, so go through open().
    with path.open("r", encoding="utf-8", errors="surrogateescape", newline="") as fh:
        return fh.read()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
        fh.write(text)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


class MergeEngine:
    def __init__(
        self,
        root: Path,
        plan: Plan,
        upstreams: dict[str, Any],
        sources: dict[str, Path],
        mode: str,
        out: Path,
        strict: bool = False,
        patch_build: bool = True,
    ) -> None:
        self.root = root
        self.plan = plan
        self.upstreams = upstreams
        self.sources = sources
        self.mode = mode
        self.out = out
        self.strict = strict
        self.patch_build = patch_build
        self.warnings: list[str] = []
        self.conflicts: list[dict[str, Any]] = []
        self.manual_port: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ utils
    def _spec_path(self, spec: str) -> Path:
        name, rel = split_spec(spec)
        if name not in self.sources:
            raise MergeError(f"unknown source '{name}' in spec '{spec}'")
        if not is_safe_relative(rel):
            raise MergeError(f"unsafe relative path in spec '{spec}'")
        return self.sources[name] / rel

    def _read_spec(self, spec: str) -> str:
        path = self._spec_path(spec)
        if not path.is_file():
            raise FileNotFoundError(f"source file missing: {spec} ({path})")
        return _read(path)

    def _record(
        self, rule: Any, status: str, note: str = "", origin: str = "", path: str | None = None
    ) -> dict[str, Any]:
        target = path or rule.path
        file_path = self.stage / target
        return {
            "rule": rule.id,
            "action": rule.action,
            "path": target,
            "status": status,
            "origin": origin,
            "sha256": _sha256(file_path) if file_path.is_file() else "",
            "note": note,
            "feature": rule.get("feature", ""),
        }

    # ------------------------------------------------------------- target tree
    def _copy_target_tree(self) -> int:
        src = self.sources[self.plan.target]
        count = 0
        for path in sorted(src.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(src)
            if any(part in SKIP_DIRS for part in rel.parts[:-1]):
                continue
            if rel.suffix.lower() in SKIP_SUFFIXES or path.stat().st_size > MAX_FILE_BYTES:
                continue
            dst = self.stage / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
            count += 1
        return count

    # ------------------------------------------------------------------ rules
    def _three_way(self, rule: Any) -> dict[str, Any]:
        try:
            ours = self._read_spec(rule["ours"])
            base = self._read_spec(rule["base"])
            theirs = self._read_spec(rule["theirs"])
        except FileNotFoundError as exc:
            self.warnings.append(f"{rule.id}: {exc}; OP4 version kept unchanged")
            return self._record(rule, "missing", str(exc), origin=rule["ours"])

        with tempfile.TemporaryDirectory(prefix="bhl-op4-merge-") as td:
            tmp = Path(td)
            (tmp / "ours").write_text(ours, encoding="utf-8", errors="surrogateescape")
            (tmp / "base").write_text(base, encoding="utf-8", errors="surrogateescape")
            (tmp / "theirs").write_text(theirs, encoding="utf-8", errors="surrogateescape")
            proc = subprocess.run(
                [
                    "git", "merge-file", "-p", "--diff3",
                    "-L", "op4 (ours)", "-L", "vanilla-hlsdk (base)", "-L", "bugfixhl (theirs)",
                    str(tmp / "ours"), str(tmp / "base"), str(tmp / "theirs"),
                ],
                capture_output=True,
                encoding="utf-8",
                errors="surrogateescape",
                check=False,
            )
        if proc.returncode < 0 or "fatal:" in proc.stderr.lower():
            raise MergeError(f"git merge-file failed for {rule.path}: {proc.stderr.strip()}")

        merged = proc.stdout
        blocks = max(0, proc.returncode)
        policy = rule.get("on_conflict", "marker")
        quarantine = rule.get("quarantine", "")

        if blocks:
            if policy == "fail":
                raise MergeError(f"{rule.path}: {blocks} conflicting hunk(s), policy=fail")
            if policy == "ours":
                reason = rule.get("manual_port", "Donor rewrite diverges too much for an automatic merge.")
                self.manual_port.append(
                    {"path": rule.path, "feature": rule.get("feature", ""), "reason": reason,
                     "blocks": blocks}
                )
                return self._record(rule, "deferred", f"OP4 kept; {blocks} conflicting hunk(s)", origin=rule["ours"])
            if policy == "theirs":
                _write(self.stage / rule.path, theirs)
                self.warnings.append(f"{rule.id}: conflicts auto-resolved with donor version")
                return self._record(rule, "donor", f"{blocks} conflicting hunk(s)", origin=rule["theirs"])
            # marker (default): never poison a buildable source file.
            dest = quarantine or rule.path
            _write(self.stage / dest, merged)
            self.conflicts.append(
                {"path": rule.path, "blocks": blocks, "quarantine": dest, "rule": rule.id}
            )
            if quarantine:
                return self._record(rule, "conflict", f"quarantined in {dest}", origin=rule["base"])
            return self._record(rule, "conflict", f"{blocks} conflicting hunk(s)", origin=rule["base"])

        if merged == ours:
            return self._record(rule, "unchanged", "donor changes already present or not applicable", origin=rule["base"])
        _write(self.stage / rule.path, merged)
        return self._record(rule, "merged", "clean 3-way merge", origin=rule["base"])

    def _copy(self, rule: Any) -> dict[str, Any]:
        spec = rule["from"]
        text = self._read_spec(spec)
        rewrites = [tuple(pair) for pair in rule.get("include_rewrites", [])]
        changed = 0
        if rewrites or any('#include' in line for line in text.splitlines()):
            text, changed = rewrite_includes(text, rewrites)
        if rule.get("banner", False):
            banner = (
                "// ---------------------------------------------------------------------------\n"
                f"// Ported reference from {spec}\n"
                "// Upstream license: see docs/LICENSES.md. Reference only: this file is NOT\n"
                "// compiled. The shipped implementation lives in game_shared/sr_core.*\n"
                "// ---------------------------------------------------------------------------\n"
            )
            text = banner + text
        _write(self.stage / rule.path, text)
        note = f"include rewrites: {changed}" if changed else rule.get("note", "")
        return self._record(rule, "added", note, origin=spec)

    def _inject(self, rule: Any) -> dict[str, Any]:
        target = self.stage / rule.path
        if not target.is_file():
            raise FileNotFoundError(f"inject target missing: {rule.path}")
        text = _read(target)
        snippet = self._read_spec(rule["snippet"])
        if not snippet.endswith("\n"):
            snippet += "\n"
        if snippet.strip() and snippet.strip() in text:
            return self._record(rule, "already_present", "snippet already in target", origin=rule["snippet"])
        anchor = rule["anchor"]
        occurrences = text.count(anchor)
        expected = int(rule.get("anchor_count", 1))
        if occurrences != expected:
            self.warnings.append(
                f"{rule.id}: anchor in {rule.path} found {occurrences}x (expected {expected}x); "
                "upstream drift - review the snippet before merging"
            )
            return self._record(rule, "anchor_drift", f"anchor found {occurrences}x", origin=rule["snippet"])
        idx = text.index(anchor)
        where = rule.get("where", "after")
        pos = idx if where == "before" else idx + len(anchor)
        if where == "after" and pos < len(text):
            # Anchors such as `#include "hud.h"` stop before the line ending:
            # insert after the *whole line*, never in the middle of it.
            if text[pos] == "\r":
                pos += 1
            if pos < len(text) and text[pos] == "\n":
                pos += 1
        _write(target, text[:pos] + snippet + text[pos:])
        return self._record(rule, "injected", f"anchor matched {occurrences}x", origin=rule["snippet"])

    def _generate(self, rule: Any) -> dict[str, Any]:
        generator = rule["generator"]
        if generator == "speedrun_cfg":
            text = configgen.render_config(self.root)
        elif generator == "route_json":
            text = json.dumps(configgen.load_route(self.root), indent=2, ensure_ascii=False) + "\n"
        else:  # guarded by manifest validation
            raise MergeError(f"unknown generator: {generator}")
        _write(self.stage / rule.path, text)
        return self._record(rule, "generated", f"generator={generator}", origin="data/")

    def _apply(self, rule: Any) -> dict[str, Any]:
        if rule.action == "skip":
            return self._record(rule, "skipped", rule.get("note", ""))
        if rule.action == "three_way":
            return self._three_way(rule)
        if rule.action == "copy":
            return self._copy(rule)
        if rule.action == "inject":
            return self._inject(rule)
        if rule.action == "generate":
            return self._generate(rule)
        raise MergeError(f"unsupported action: {rule.action}")

    # ------------------------------------------------------------------- main
    def run(self) -> dict[str, Any]:
        self.stage = self.out.parent / f".stage-{os.getpid()}"
        if self.stage.exists():
            shutil.rmtree(self.stage)
        self.stage.mkdir(parents=True)
        copied = self._copy_target_tree()

        records: list[dict[str, Any]] = []
        for rule in self.plan.rules:
            try:
                records.append(self._apply(rule))
            except (MergeError, FileNotFoundError, OSError) as exc:
                self.warnings.append(f"{rule.id}: {exc}")
                rec = self._record(rule, "error", str(exc))
                records.append(rec)

        build_files: list[dict[str, object]] = []
        if self.patch_build:
            try:
                for change in projects.patch_tree(self.stage):
                    build_files.append(change)
                    if change["changed"] and change["added"]:
                        records.append(
                            {
                                "rule": "build-files",
                                "action": "patch",
                                "path": str(change["file"]),
                                "status": "patched",
                                "origin": "merge/projects.py",
                                "sha256": "",
                                "note": ", ".join(change["added"]),  # type: ignore[arg-type]
                                "feature": "build system integration",
                            }
                        )
            except (projects.ProjectPatchError, OSError) as exc:
                self.warnings.append(f"build file patching failed: {exc}")
                records.append(
                    {"rule": "build-files", "action": "patch", "path": "(build files)",
                     "status": "error", "origin": "", "sha256": "", "note": str(exc), "feature": ""}
                )

        tree_hash, tree_files = compute_tree_hash(self.stage)
        statuses = [r["status"] for r in records]
        summary = {
            "rules": len(records),
            "target_files_copied": copied,
            "tree_files": tree_files,
            "merged": statuses.count("merged"),
            "unchanged": statuses.count("unchanged"),
            "conflicts": len(self.conflicts),
            "deferred": statuses.count("deferred"),
            "added": statuses.count("added"),
            "injected": statuses.count("injected"),
            "generated": statuses.count("generated"),
            "patched": statuses.count("patched"),
            "anchor_drift": statuses.count("anchor_drift"),
            "missing": statuses.count("missing"),
            "errors": statuses.count("error"),
        }
        upstream_report = []
        for name, u in self.upstreams.items():
            upstream_report.append(
                {
                    "name": name,
                    "role": u.role,
                    "repo": u.repo,
                    "ref": u.ref,
                    "license": u.license,
                    "sha256": u.tarball["sha256"],
                    "source": str(self.sources.get(name, "")),
                }
            )
        report: dict[str, Any] = {
            "schema": 1,
            "project": self.plan.name,
            "description": self.plan.description,
            "mode": self.mode,
            "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "target": self.plan.target,
            "upstreams": upstream_report,
            "files": records,
            "summary": summary,
            "conflicts": self.conflicts,
            "manual_port": self.manual_port,
            "warnings": self.warnings,
            "build_files": build_files,
            "tree_hash": tree_hash,
            "tree_files": tree_files,
        }
        (self.stage / "MERGE_REPORT.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (self.stage / "MERGE_REPORT.md").write_text(render_markdown(report), encoding="utf-8")

        # Atomic-ish swap: keep the previous result until the new one is in place.
        self.out.parent.mkdir(parents=True, exist_ok=True)
        backup = self.out.parent / f".old-{os.getpid()}"
        if backup.exists():
            shutil.rmtree(backup)
        if self.out.exists():
            os.replace(self.out, backup)
        try:
            os.replace(self.stage, self.out)
        except OSError:
            if backup.exists():
                os.replace(backup, self.out)
            raise
        if backup.exists():
            shutil.rmtree(backup)

        if self.strict:
            # Conflicts are an expected, *quarantined* outcome of a 3-way
            # merge, not a pipeline failure. Strict mode fails on rules that
            # could not be applied at all (upstream drift / missing inputs).
            failures = [r for r in records if r["status"] in {"error", "anchor_drift", "missing"}]
            if failures:
                raise MergeError(f"strict mode: {len(failures)} rule(s) could not be applied")
        return report

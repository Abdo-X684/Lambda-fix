"""Resolve upstream trees and download them with checksum verification.

The upstream SDKs are *not* vendored: they are licensed separately, they are
large, and pinning them by commit + sha256 is what makes the merge reproducible.
``--offline`` swaps them for the tiny fixtures in ``tests/fixtures/upstreams``
so the whole pipeline can be tested without network access.
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import tarfile
import urllib.request
from pathlib import Path
from typing import Any

from .manifest import Upstream

BINARY_SUFFIXES = {
    ".dll", ".lib", ".so", ".dylib", ".exe", ".pdb", ".obj", ".o", ".a",
    ".zip", ".7z", ".png", ".jpg", ".bmp", ".tga", ".wav", ".mp3",
}
SKIP_DIRS = {".git", ".github", "build", "dist", "__pycache__"}


class FetchError(RuntimeError):
    pass


def cache_dir(root: Path) -> Path:
    return root / ".cache" / "upstreams"


def resolve_sources(
    root: Path, upstreams: dict[str, Upstream], offline: bool
) -> dict[str, Path]:
    """Return the ``source name -> directory`` map used by the merge engine."""
    sources: dict[str, Path] = {"repo": root, "overlay": root / "overlay"}
    if offline:
        base = root / "tests" / "fixtures" / "upstreams"
    else:
        base = cache_dir(root)
    for name in upstreams:
        path = base / name
        if not path.is_dir():
            hint = "check tests/fixtures/upstreams" if offline else "run `make fetch` first"
            raise FetchError(f"source '{name}' not found at {path} ({hint})")
        sources[name] = path
    return sources


def _safe_members(tar: tarfile.TarFile) -> list[tuple[tarfile.TarInfo, str]]:
    """Strip the ``repo-SHA/`` root and reject traversal / special files."""
    out: list[tuple[tarfile.TarInfo, str]] = []
    for member in tar.getmembers():
        parts = member.name.split("/")
        if len(parts) < 2:
            continue
        rel = "/".join(parts[1:])
        if not rel or rel.startswith("/") or ".." in rel.split("/"):
            raise FetchError(f"unsafe path in archive: {member.name}")
        if member.issym() or member.islnk() or member.isdev():
            continue
        if member.isdir():
            continue
        if Path(rel).suffix.lower() in BINARY_SUFFIXES:
            continue
        out.append((member, rel))
    return out


def fetch_one(root: Path, upstream: Upstream, force: bool = False) -> dict[str, Any]:
    dest = cache_dir(root) / upstream.name
    marker = dest / ".FETCHED.json"
    if dest.is_dir() and marker.is_file() and not force:
        info = json.loads(marker.read_text(encoding="utf-8"))
        if info.get("ref") == upstream.ref and info.get("sha256") == upstream.tarball["sha256"]:
            return {"name": upstream.name, "status": "cached", **info}

    url = upstream.tarball["url"]
    expected_sha = upstream.tarball["sha256"]
    try:
        with urllib.request.urlopen(url, timeout=180) as response:
            payload = response.read()
    except OSError as exc:
        raise FetchError(f"failed to download {url}: {exc}") from exc

    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != expected_sha:
        raise FetchError(
            f"{upstream.name}: checksum mismatch (expected {expected_sha}, got {actual_sha}). "
            "The pinned tarball changed - re-pin and review it before merging."
        )
    if "bytes" in upstream.tarball and len(payload) != upstream.tarball["bytes"]:
        raise FetchError(f"{upstream.name}: tarball size changed ({len(payload)} bytes)")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
            for member, rel in _safe_members(tar):
                target = dest / rel
                if any(part in SKIP_DIRS for part in Path(rel).parts[:-1]):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tar.extractfile(member)
                if src is None:
                    continue
                with src, target.open("wb") as fh:
                    shutil.copyfileobj(src, fh)
    except (tarfile.TarError, OSError) as exc:
        raise FetchError(f"{upstream.name}: could not extract archive: {exc}") from exc

    info = {
        "name": upstream.name,
        "status": "fetched",
        "repo": upstream.repo,
        "ref": upstream.ref,
        "sha256": actual_sha,
        "bytes": len(payload),
        "license": upstream.license,
        "files": sum(1 for p in dest.rglob("*") if p.is_file()),
    }
    marker.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return info


def fetch_all(root: Path, upstreams: dict[str, Upstream], force: bool = False) -> list[dict[str, Any]]:
    return [fetch_one(root, u, force=force) for u in upstreams.values()]

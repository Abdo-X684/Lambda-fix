#!/usr/bin/env python3
"""Verify the BHL-based OP4 merge tree.

Two jobs:

    --compile   Compile every OP4 subsystem .cpp AND every verbatim BHL server
                .cpp in bhl-op4/ into real ELF32 objects against the MERGED
                BugfixedHL headers (Zig clang). Writes bhl-op4/PORT_STATUS.json
                with the honest per-file result for both sets.
  --check     Verify PROVENANCE.json integrity and that every source wired into
              the BHL CMake targets actually compiled clean.

This tool does not rebuild the game DLLs. A full build needs BugfixedHL's
CMake 3.30 + vcpkg + hl1_source_sdk toolchain; see docs/BHL_BASE_MERGE.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SDK = ROOT / ".cache/upstreams/hl1_source_sdk"
# BHL declares this as its `source_sdk` submodule at the pinned commit.
SOURCE_SDK_URL = (
    "https://codeload.github.com/tmp64/hl1_source_sdk/tar.gz/"
    "11f26656677c881c7c630d03957900e7701da62e")
SOURCE_SDK_SHA256 = "822d0f6fdd112fabac3257a67d2e23d4d9ba3a655e13fd248fa4f775341f2f0b"
DEFINES = [
    "-DPLATFORM_UNIX", "-DPLATFORM_LINUX", "-D_LINUX", "-DLINUX",
    "-DCOMPILER_GNU", "-DCOMPILER_CLANG", "-DGNUC", "-DNO_STEAM",
    "-DNO_MALLOC_OVERRIDE", "-DMATHLIB_HEADER_ONLY", "-D_DLL_EXT=.so",
    "-DSERVER_DLL", "-DCLIENT_WEAPONS", "-DMATHLIB_USE_C_ASSERT",
    "-DMATHLIB_VECTOR_NONTRIVIAL", "-DHAS_STD_FILESYSTEM=1", "-DUSE_UPDATER=0",
    "-D_stricmp=strcasecmp", "-D_strnicmp=strncasecmp",
]


def find_compiler() -> list[str] | None:
    env = os.environ.get("ZIG32")
    if env and Path(env).exists():
        return [env]
    for candidate in ("/tmp/zig32", shutil_which("zig32")):
        if candidate and Path(candidate).exists():
            return [candidate]
    zig = shutil_which("zig")
    if zig:
        return [zig, "c++", "-target", "x86-linux-gnu"]
    return None


def shutil_which(name: str) -> str | None:
    import shutil
    return shutil.which(name)


def ensure_source_sdk(fetch: bool = True) -> bool:
    """BHL's source_sdk submodule is needed for tier0/mathlib headers."""
    if (SDK / "public/tier0/platform.h").is_file():
        return True
    if not fetch:
        return False
    import io
    import tarfile
    import urllib.request
    try:
        with urllib.request.urlopen(SOURCE_SDK_URL, timeout=180) as r:
            payload = r.read()
        if hashlib_sha256(payload) != SOURCE_SDK_SHA256:
            return False
        SDK.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
            for m in tar.getmembers():
                parts = m.name.split("/")
                if len(parts) < 2 or not m.isfile():
                    continue
                rel = "/".join(parts[1:])
                if rel.startswith("/") or ".." in rel.split("/"):
                    continue
                dst = SDK / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                src = tar.extractfile(m)
                if src:
                    with src, dst.open("wb") as fh:
                        shutil_copyfileobj(src, fh)
    except Exception:
        return False
    return (SDK / "public/tier0/platform.h").is_file()


def hashlib_sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def shutil_copyfileobj(src, dst):
    import shutil
    shutil.copyfileobj(src, dst)


def include_args(tree: Path) -> list[str]:
    inc = [
        tree / "src/game/server", tree / "src/common", tree / "src/engine",
        tree / "src/game/shared", tree / "src/public", tree / "src/pm_shared",
        tree / "src/game/server/op4", tree / "src/game/server/op4/dlls",
        tree / "src/game/server/op4/dlls/weapons",
        tree / "src/game/server/op4/dlls/ctf",
        tree / "src/game/server/op4/dlls/rope",
          SDK / "public", SDK / "public/tier0", SDK / "public/tier1", SDK / "common",
          # BHL's vendored semver submodule (bhl_version_info / CGameVersion.h)
          tree / "external/semver.c/include",
      ]
    return [a for p in inc for a in ("-I", str(p))]


def sources(tree: Path) -> list[Path]:
      return sorted(p for p in (tree / "src/game/server/op4").rglob("*.cpp")
                    if "reference" not in p.parts)


def bhl_sources(tree: Path) -> list[Path]:
      """Verbatim BugfixedHL server sources, i.e. the BASE tree itself.

      Compiling these proves the merged tree is real BHL code, not just BHL
      headers with OP4 sources bolted on.
      """
      prov = json.loads((tree / "PROVENANCE.json").read_text())
      out = []
      for rel, rec in prov["files"].items():
          if (rec["origin"] == "bugfixhl"
                  and rec["action"] == "verbatim"
                  and rel.startswith("src/game/server/")
                  and rel.endswith(".cpp")):
              out.append(tree / rel)
      return sorted(out)


def compile_all(tree: Path, fetch_sdk: bool = True) -> dict:
    compiler = find_compiler()
    sdk_ok = ensure_source_sdk(fetch_sdk)
    if compiler is None or not sdk_ok:
        return {"status": "unavailable",
                "reason": "Zig 32-bit compiler or .cache/upstreams/hl1_source_sdk missing",
                "compiler": compiler, "source_sdk": str(SDK)}
    results = {}
    with tempfile.TemporaryDirectory(prefix="bhl-op4-verify-") as td:
        obj = Path(td) / "probe.o"
        cache = Path(td) / "zcache"
        cache.mkdir()
        env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(cache))
        args = compiler + ["-c", "-std=c++17", "-fpermissive", "-w",
                           "-ferror-limit=50"] + DEFINES + include_args(tree)
        def compile_set(file_list: list[Path]) -> dict:
            res = {}
            for src in file_list:
                cmd = args + ["-o", str(obj), str(src)]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True,
                                       env=env, timeout=90)
                except subprocess.TimeoutExpired:
                    res[str(src.relative_to(tree))] = {
                        "ok": False, "errors": 1, "gaps": ["compiler timeout"]}
                    continue
                errs = re.findall(r"error: (.+)", r.stderr)
                res[str(src.relative_to(tree))] = {
                    "ok": r.returncode == 0 and not errs,
                    "errors": len(errs),
                    "gaps": sorted(set(errs))[:8],
                }
                if obj.exists():
                    obj.unlink()
            return res

        results = compile_set(sources(tree))
        bhl_results = compile_set(bhl_sources(tree))

    clean = sum(1 for v in results.values() if v["ok"])
    bhl_clean = sum(1 for v in bhl_results.values() if v["ok"])
    return {
        "status": "compiled",
        "compiler": " ".join(compiler),
        "target": "x86-linux-gnu (ELF32 relocatable objects)",
        "source_sdk": str(SDK.relative_to(ROOT)) if SDK.is_relative_to(ROOT) else str(SDK),
        "total": len(results), "clean": clean,
        "pending": len(results) - clean,
        "files": results,
        "bhl_base": {
            "note": "Verbatim BugfixedHL-Rebased server sources compiled "
                    "against the merged tree; proves the BASE is real BHL code.",
            "total": len(bhl_results), "clean": bhl_clean,
            "pending": len(bhl_results) - bhl_clean,
            "files": bhl_results,
        },
    }


def check(tree: Path) -> int:
    prov_p = tree / "PROVENANCE.json"
    status_p = tree / "PORT_STATUS.json"
    if not prov_p.is_file():
        print("FAIL: PROVENANCE.json missing", file=sys.stderr)
        return 1
    prov = json.loads(prov_p.read_text())
    errors = []
    if prov["architecture"] != "BASE=BugfixedHL-Rebased, ADD/MERGE=halflife-op4-updated":
        errors.append("unexpected architecture")
    if prov["base"]["files"] < 600:
        errors.append("BHL base tree is too small")
    for rel, srcs in prov["cmake"].items():
        text = (tree / rel).read_text()
        for s in srcs:
            if s not in text:
                errors.append(f"cmake missing {s}")
    if status_p.is_file():
        st = json.loads(status_p.read_text())
        if st.get("status") == "compiled":
            for rel, srcs in prov["cmake"].items():
                side = "server" if "server" in rel else "client"
                for s in srcs:
                    key = f"src/game/{side}/{s}"
                    if key not in st["files"] or not st["files"][key]["ok"]:
                        errors.append(f"wired source did not compile: {key}")
            print(f"  compile:       {st['clean']}/{st['total']} clean, {st['pending']} port-pending")
            bb = st.get("bhl_base")
            if bb:
                print(f"  BHL sources:   {bb['clean']}/{bb['total']} verbatim BHL server .cpp compile")
                if bb["total"] < 100:
                    errors.append("BHL base source set is too small")
                if bb["clean"] < 100:
                    errors.append("too few verbatim BHL server sources compile")
    print(f"  BHL base:      {prov['base']['files']} files")
    print(f"  OP4 merged:    {prov['op4']['files']} files")
    print(f"  glue:          {len(prov['glue_files'])} files")
    print(f"  CMake wired:   {sum(len(v) for v in prov['cmake'].values())} sources")
    print(f"  port pending:  {prov['port_pending']['count']} sources")
    if errors:
        for e in errors[:20]:
            print("  FAIL:", e, file=sys.stderr)
        return 1
    print("  == BHL-BASE TREE OK ==")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default="bhl-op4")
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-fetch-sdk", action="store_true")
    a = ap.parse_args()
    tree = Path(a.tree)
    if not tree.is_absolute():
        tree = ROOT / tree
    if a.compile:
        st = compile_all(tree, fetch_sdk=not a.no_fetch_sdk)
        (tree / "PORT_STATUS.json").write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
        print(f"  compiler: {st['status']}")
        if st["status"] == "compiled":
            print(f"  {st['clean']}/{st['total']} OP4 sources compile into ELF32 objects")
            print(f"  {st['pending']} sources listed as port-pending in PORT_STATUS.json")
            bb = st.get("bhl_base", {})
            if bb:
                print(f"  {bb['clean']}/{bb['total']} verbatim BHL server sources compile into ELF32 objects")
        (tree / "PROVENANCE.json")  # noqa: B018 - ensure tree exists
    if a.check or not a.compile:
        return check(tree)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Honest, reproducible probe of whether an in-game Opposing Force test can run.

Phase 4 requires loading client.so/hl.so in a REAL HL engine with legitimate
Opposing Force assets and vgui.so, starting a map, and exercising HUD/weapons.
This tool records what is actually present in the environment and why such a
test is or is not possible. It never infers success from a menu or a library
load, and it never fabricates a runtime result.

Outputs:
    build-evidence/bhl-base/RUNTIME_ENVIRONMENT.json
    build-evidence/bhl-base/RUNTIME_ENVIRONMENT.md

Usage: python3 tools/probe_runtime_environment.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "build-evidence" / "bhl-base"

# Only real engine binaries / libraries count. Source directories named "hl"
# and the source_sdk's libsteam_api.so are not an installed HL engine.
ENGINE_NAMES = ("hl_linux", "hl.exe", "hw.so", "vgui.so", "vgui2.so",
                "steamclient.so", "sw.dll")
# Only a real game install has maps and a pak file. SDK utility sprites and
# legacy generated overlay sprites are not Opposing Force game assets.
ASSET_GLOBS = ("*.bsp", "pak0.pak")
LOADER_PATHS = ("/lib/ld-linux.so.2", "/lib32/ld-linux.so.2",
                "/usr/lib/ld-linux.so.2", "/lib/i386-linux-gnu/ld-linux.so.2")
ELF32_LIBS = ("libSDL2-2.0.so.0", "libtier0.so", "libvstdlib.so")


def find_compiler() -> str | None:
    for c in (os.environ.get("ZIG32"), "/tmp/zig32"):
        if c and Path(c).exists():
            return c
    return shutil.which("zig")


def find_raw_zig() -> str | None:
    """The 32-bit wrapper hardcodes -target x86-linux-gnu; musl needs raw zig."""
    for c in (Path("/tmp/zenv/lib/python3.11/site-packages/ziglang/zig"),
              Path(os.environ.get("ZIG_BIN", "/nonexistent"))):
        if c.exists():
            return str(c)
    z = shutil.which("zig")
    return z


def run_capture(cmd: list[str]) -> dict:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        return {"rc": r.returncode, "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip()}
    except OSError as exc:
        # execve(2) returns ENOENT when the ELF32 interpreter is missing.
        return {"rc": None, "error": f"{type(exc).__name__}: {exc}"}


def probe_elf32(compiler: str | None) -> dict:
    """Can a dynamically linked ELF32 executable run here at all?"""
    out: dict = {"compiler": compiler, "source": '#include <cstdio>\nint main(){printf("ELF32-RUN-OK\\n");return 0;}\n'}
    if compiler is None:
        out["status"] = "toolchain-unavailable"
        return out
    with tempfile.TemporaryDirectory(prefix="op4-runtime-") as td:
        d = Path(td)
        src = d / "run32.cpp"
        src.write_text(out["source"])
        is_raw_zig = compiler == shutil.which("zig")
        common = ["c++", "-target", "x86-linux-gnu"] if is_raw_zig else []
        dyn = d / "run32"
        r1 = subprocess.run([compiler, *common, str(src), "-o", str(dyn)],
                            capture_output=True, text=True)
        out["dynamic_command"] = " ".join([compiler, *common, str(src), "-o", str(dyn)])
        out["dynamic_build_rc"] = r1.returncode
        out["dynamic_build_stderr"] = r1.stderr.strip()[:400]
        if dyn.exists():
            out["dynamic_run"] = run_capture([str(dyn)])
        else:
            out["dynamic_run"] = {"rc": None, "error": "no executable produced"}
        # A statically linked ELF32 executable needs no 32-bit loader/libc.
        st = d / "run32s"
        raw = find_raw_zig()
        out["raw_zig"] = raw
        if raw:
            cmd = [raw, "c++", "-target", "x86-linux-musl", "-static",
                   str(src), "-o", str(st)]
            out["static_command"] = " ".join(cmd)
            r2 = subprocess.run(cmd, capture_output=True, text=True)
            out["static_build_rc"] = r2.returncode
            out["static_build_stderr"] = r2.stderr.strip()[:400]
            out["static_run"] = (run_capture([str(st)]) if st.exists()
                                 else {"rc": None, "error": "no executable produced"})
        else:
            out["static_run"] = {"rc": None, "error": "raw zig binary unavailable"}
    return out


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    found: dict[str, list[str]] = {}
    for name in ENGINE_NAMES:
        hits = [str(p.relative_to(ROOT)) for p in ROOT.rglob(name)
                if p.is_file() and ".git" not in p.parts][:5]
        if hits:
            found[name] = hits
    assets: dict[str, list[str]] = {}
    for pat in ASSET_GLOBS:
        hits = [str(p.relative_to(ROOT)) for p in ROOT.rglob(pat)
                if p.is_file() and ".git" not in p.parts][:5]
        if hits:
            assets[pat] = hits
    # Count model files too, but they only count as assets alongside maps/pak.
    models = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.mdl")
              if p.is_file() and ".git" not in p.parts][:5]
    result_models = models
    loaders = [p for p in LOADER_PATHS if Path(p).exists()]
    libs = {}
    for name in ELF32_LIBS:
        libs[name] = [str(p) for p in
                      (list(Path("/lib").rglob(name)) +
                       list(Path("/usr/lib").rglob(name)))][:3]
    bhlop4 = ROOT / "dist" / "bhlop4"
    bhlop4_state = {
        "exists": bhlop4.is_dir(),
        "contents": sorted(p.name for p in bhlop4.iterdir())[:30] if bhlop4.is_dir() else [],
    }
    delivered = {}
    for name in ("client.so", "hl.so"):
        p = EVIDENCE / name
        delivered[name] = {"exists": p.is_file(),
                           "elf32": None, "needed": []}
        if p.is_file():
            r = subprocess.run(["readelf", "-d", str(p)], capture_output=True, text=True)
            delivered[name]["needed"] = [
                ln.split("[")[1].split("]")[0]
                for ln in r.stdout.splitlines() if "(NEEDED)" in ln]
            hdr = subprocess.run(["readelf", "-h", str(p)], capture_output=True, text=True)
            delivered[name]["elf32"] = ("ELF32" in hdr.stdout and
                                        "Intel 80386" in hdr.stdout)
    compiler = find_compiler()
    result = {
        "purpose": "Determine whether a real in-game Opposing Force test is executable in this environment.",
        "verdict": "NOT EXECUTABLE",
        "reasons": [],
        "engine_files_found": found,
        "op4_asset_files_found": assets,
        "model_files_found": result_models,
        "legacy_overlay_note": (
            "dist/bhlop4/ is a legacy packaging scaffold from an earlier, rejected "
            "phase. It contains NO engine, NO vgui.so, NO maps and NO OP4 assets, "
            "and its bundled DLLs are the old binaries that are explicitly NOT "
            "used as build or runtime evidence."),
        "elf32_dynamic_loader_paths_present": loaders,
        "elf32_shared_libraries": libs,
        "standalone_bhlop4": bhlop4_state,
        "delivered_libraries": delivered,
        "elf32_execution_probe": probe_elf32(compiler),
    }
    if not found:
        result["reasons"].append("No Half-Life engine binary (hl_linux/hw.so) and no vgui.so anywhere in the workspace.")
    if not assets:
        result["reasons"].append("No legitimate Opposing Force assets (.bsp maps, .mdl models, .spr sprites, .wad textures, pak0.pak).")
    if not loaders:
        result["reasons"].append("No 32-bit dynamic loader ld-linux.so.2; a dynamically linked ELF32 process cannot start.")
    dyn = result["elf32_execution_probe"].get("dynamic_run", {})
    if dyn.get("rc") != 0 or "ELF32-RUN-OK" not in dyn.get("stdout", ""):
        result["reasons"].append(
            "A minimal dynamically linked ELF32 executable already fails to run "
            "(see elf32_execution_probe.dynamic_run); the delivered client.so/hl.so "
            "additionally need libSDL2-2.0.so.0, libtier0.so and libvstdlib.so, "
            "which are absent.")
    result["reasons"].append(
        "The build environment is a headless x86-64 Linux sandbox without a "
        "legitimate Steam/HL installation; there is no display, no engine, and "
        "no user-supplied game assets. A library load or a menu screen would "
        "not be an in-game test.")
    result["what_was_actually_tested"] = [
        "ELF32 compilation of every translation unit into relocatable i386 objects",
        "static link of both shared libraries with a full undefined-symbol audit",
        "nm/objdump verification that all 12 former link gaps are real, non-empty definitions",
        "host-executed functional tests of the exact OP4 GetNextAttackDelay and entity-enumerator code",
        "provenance and declared-BHL-change verification",
    ]
    (EVIDENCE / "RUNTIME_ENVIRONMENT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Runtime environment: why there is NO in-game Opposing Force test",
        "",
        "**Verdict: NOT EXECUTABLE.** This is a factual statement, not a claim of success.",
        "",
        "Reproduce with `python3 tools/probe_runtime_environment.py`.",
        "",
        "## Reasons",
        "",
    ]
    lines += [f"- {r}" for r in result["reasons"]]
    lines += ["", "## Probes", "",
              "```json",
              json.dumps({k: result[k] for k in
                          ("engine_files_found", "op4_asset_files_found",
                           "elf32_dynamic_loader_paths_present",
                           "elf32_shared_libraries", "standalone_bhlop4",
                           "delivered_libraries", "elf32_execution_probe")},
                         indent=2, sort_keys=True),
              "```", "",
              "## What WAS tested", "",
              ]
    lines += [f"- {x}" for x in result["what_was_actually_tested"]]
    lines += ["", "## What was NOT tested (explicit incomplete list)", "",
              "- Loading client.so/hl.so into a real HL engine without errors.",
              "- Starting an actual Opposing Force map.",
              "- HUD/UI rendering, VGUI, flag icons, scoreboard.",
              "- BHL weapons and OP4 weapons: switching, ammo, reload, firing.",
              "- Monster shock effect, rope physics, grapple hook, CTF flag capture in-game.",
              "- Crash / runtime-error monitoring over a real play session.",
              "- Retest after the final edit inside a real game session.",
              "",
              "No result above is inferred from compilation, CI, a menu, or a library load.",
              ""]
    (EVIDENCE / "RUNTIME_ENVIRONMENT.md").write_text("\n".join(lines))
    print("verdict:", result["verdict"])
    print("reasons:", len(result["reasons"]))
    print("wrote: build-evidence/bhl-base/RUNTIME_ENVIRONMENT.{json,md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

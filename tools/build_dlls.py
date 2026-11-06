#!/usr/bin/env python3
"""Build the 32-bit GoldSrc binaries (client.so + hl.so) from the merged tree.

GoldSrc on Linux loads *32-bit* shared libraries, so the OP4 SDK's Linux
Makefiles invoke ``g++ -m32``. This driver does a preflight (merged tree,
patched build files, 32-bit toolchain, proprietary ``vgui.so``), then runs
``make`` and collects the artifacts with a sha256 manifest.

It never downloads or ships Valve/Gearbox binaries: ``vgui.so`` and the game
assets come from your own Half-Life installation. See docs/BUILDING.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TREE = ROOT / "build" / "merged-real"
DEFAULT_OUT = ROOT / "dist" / "dlls"

MAKEFILES = ("Makefile", "Makefile.hl_cdll", "Makefile.hldll")
PATCHED_MARKERS = {
    "Makefile.hl_cdll": ("sr_hud_timer.o", "sr_hud_msg.o", "sr_core.o"),
    "Makefile.hldll": ("sr_server.o", "sr_core.o"),
}
OUR_SOURCES = (
    "cl_dll/sr_hud_timer.cpp", "cl_dll/sr_hud_msg.cpp",
    "dlls/sr_server.cpp", "game_shared/sr_core.cpp",
)
INSTALL_HINT = "sudo apt install build-essential gcc-multilib g++-multilib libgl1-mesa-dev"


def probe_m32(compiler: str = "g++") -> dict:
    """Actually compile AND link a tiny 32-bit program (no guessing)."""
    if not shutil.which(compiler):
        return {"ok": False, "detail": f"{compiler} not found on PATH"}
    if not shutil.which("make"):
        return {"ok": False, "detail": "make not found on PATH"}
    with tempfile.TemporaryDirectory() as td:
        src, exe = Path(td) / "probe.cpp", Path(td) / "probe"
        src.write_text("int main() { return 0; }\n", encoding="utf-8")
        proc = subprocess.run(
            [compiler, "-m32", str(src), "-o", str(exe)],
            capture_output=True, text=True,
        )
        if proc.returncode == 0 and exe.is_file():
            return {"ok": True, "detail": "32-bit compile + link OK"}
        lines = (proc.stderr or proc.stdout).strip().splitlines()
        return {"ok": False, "detail": " / ".join(lines[:3])}


def toolchain(compiler: str = "g++") -> dict:
    m32 = probe_m32(compiler)
    lib = subprocess.run(
        [compiler, "-m32", "-print-file-name=libstdc++.so"],
        capture_output=True, text=True,
    ) if shutil.which(compiler) else None
    libpath = Path(lib.stdout.strip()) if lib and lib.returncode == 0 and lib.stdout.strip() else None
    return {
        "compiler": compiler,
        "compiler_found": shutil.which(compiler) is not None,
        "make_found": shutil.which("make") is not None,
        "m32_ok": m32["ok"],
        "m32_detail": m32["detail"],
        "libstdcxx32": str(libpath) if libpath and libpath.is_file() else None,
        "install_hint": INSTALL_HINT,
    }


def find_vgui(tree: Path, explicit: str | None = None) -> Path | None:
    """Locate the proprietary vgui.so that the client link step requires."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("HL_VGUI_SO"):
        candidates.append(Path(os.environ["HL_VGUI_SO"]))
    candidates += [tree / "linux" / "release" / "vgui.so", tree / "linux" / "vgui.so"]
    if os.environ.get("HL_ROOT"):
        hl = Path(os.environ["HL_ROOT"])
        candidates += [hl / "vgui.so", hl / "valve" / "cl_dlls" / "vgui.so"]
    home = Path.home()
    candidates += [
        home / ".steam" / "steam" / "steamapps" / "common" / "Half-Life" / "vgui.so",
        home / ".local" / "share" / "Steam" / "steamapps" / "common" / "Half-Life" / "vgui.so",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def preflight(tree: Path = DEFAULT_TREE, compiler: str = "g++",
              vgui: str | None = None) -> dict:
    """Structural + environment checks; never lies about what is missing."""
    missing: list[str] = []
    if not tree.is_dir():
        missing.append(f"merged tree not found: {tree} (run: make fetch && make merge)")
    linux = tree / "linux"
    for name in MAKEFILES:
        path = linux / name
        if not path.is_file():
            missing.append(f"linux/{name}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in PATCHED_MARKERS.get(name, ()):
            if marker not in text:
                missing.append(f"linux/{name}: unpatched (missing {marker})")
    for rel in OUR_SOURCES:
        if not (tree / rel).is_file():
            missing.append(rel)

    tc = toolchain(compiler)
    vg = find_vgui(tree, vgui)
    blockers: list[str] = []
    if missing:
        blockers.append("merged tree incomplete: " + ", ".join(missing[:4]))
    if not tc["m32_ok"]:
        blockers.append(f"32-bit toolchain unavailable ({tc['m32_detail']}) -> {INSTALL_HINT}")
    if vg is None:
        blockers.append("vgui.so not found -> pass --vgui /path/to/Half-Life/vgui.so or set HL_ROOT")
    return {
        "tree": str(tree),
        "tree_ready": not missing,
        "missing": missing,
        "toolchain": tc,
        "vgui": {"found": vg is not None, "path": str(vg) if vg else None},
        "blockers": blockers,
        "ready": not blockers,
    }


def is_elf32(path: Path) -> bool:
    with path.open("rb") as fh:
        return fh.read(5) == b"\x7fELF\x01"  # ELFCLASS32


def prepare(tree: Path, cfg: str, vgui: Path) -> None:
    linux = tree / "linux"
    release = linux / cfg
    release.mkdir(parents=True, exist_ok=True)
    target = release / "vgui.so"
    if vgui.resolve() != target.resolve():
        shutil.copy2(vgui, target)
    # Codeload tarballs do not preserve the executable bit for this helper.
    script = linux / "gendbg.sh"
    if script.is_file():
        script.chmod(0o755)


def build(tree: Path, cfg: str, compiler: str, jobs: int, vgui: Path) -> tuple[Path, Path]:
    prepare(tree, cfg, vgui)
    cmd = ["make", "-C", str(tree / "linux"), f"CFG={cfg}", f"COMPILER={compiler}", f"-j{jobs}"]
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=tree / "linux", text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"make failed with exit code {proc.returncode}")
    client = tree / "linux" / cfg / "client.so"
    server = tree / "linux" / cfg / "hl.so"
    for artifact in (client, server):
        if not artifact.is_file():
            raise RuntimeError(f"expected artifact missing: {artifact}")
    return client, server


def write_manifest(out: Path, artifacts: dict[str, Path], meta: dict) -> dict:
    payload: dict[str, Any] = {
        "kind": "goldsrc-linux-binaries",
        "arch": "ELF32 i386",
        "compiler": meta["compiler"],
        "cfg": meta["cfg"],
        "tree": meta["tree"],
        "files": {},
    }
    for name, path in artifacts.items():
        data = path.read_bytes()
        payload["files"][name] = {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "elf32": is_elf32(path),
        }
        shutil.copy2(path, out / name)
    (out / "MANIFEST.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def install_artifacts(out: Path, mod: Path, tree: Path) -> list[str]:
    """Copy binaries into a standalone mod dir (NEVER a Valve game directory)."""
    from tools.create_mod import validate_mod_name  # noqa: PLC0415

    validate_mod_name(mod.name)
    written: list[str] = []

    def place(src: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file() and not dest.with_suffix(dest.suffix + ".orig").is_file():
            shutil.copy2(dest, dest.with_suffix(dest.suffix + ".orig"))
        shutil.copy2(src, dest)
        written.append(str(dest))

    place(out / "client.so", mod / "cl_dlls" / "client.so")
    place(out / "hl.so", mod / "dlls" / "hl.so")
    delta = tree / "network" / "delta.lst"
    if delta.is_file():
        place(delta, mod / "delta.lst")
    cfg = ROOT / "build" / "merged" / "gamedir" / "speedrun.cfg"
    if cfg.is_file():
        place(cfg, mod / "speedrun.cfg")
    route = ROOT / "data" / "op4_route.json"
    if route.is_file():
        place(route, mod / "splits" / "op4_route.json")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=Path, default=DEFAULT_TREE)
    parser.add_argument("--cfg", choices=("release", "debug"), default="release")
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 2))
    parser.add_argument("--vgui", help="path to the game's vgui.so")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--install", type=Path, help="copy artifacts into this mod dir (e.g. .../Half-Life/gearbox)")
    parser.add_argument("--check", action="store_true", help="print preflight JSON only, do not build")
    parser.add_argument("--require-tree", action="store_true", help="with --check, fail if the merged tree is incomplete")
    args = parser.parse_args(argv)

    report = preflight(args.tree, args.compiler, args.vgui)
    if args.check:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if (not args.require_tree or report["tree_ready"]) else 1

    if not report["ready"]:
        print("client.so / hl.so: build blocked", file=sys.stderr)
        for blocker in report["blockers"]:
            print(f"  ! {blocker}", file=sys.stderr)
        print("  see docs/BUILDING.md (also available in the dashboard)", file=sys.stderr)
        return 2

    try:
        client, server = build(args.tree, args.cfg, args.compiler, args.jobs, Path(report["vgui"]["path"]))
    except RuntimeError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = write_manifest(args.out, {"client.so": client, "hl.so": server}, {
        "compiler": args.compiler, "cfg": args.cfg, "tree": str(args.tree),
    })
    for name, info in manifest["files"].items():
        print(f"  {name}: {info['bytes']} bytes, sha256={info['sha256'][:16]}…, "
              f"ELF32={info['elf32']}")
    print(f"wrote {args.out / 'MANIFEST.json'}")
    if args.install:
        try:
            for dest in install_artifacts(args.out, args.install, args.tree):
                print(f"  installed -> {dest}")
        except ValueError as exc:
            print(f"install refused: {exc}", file=sys.stderr)
            print("use: python3 tools/create_mod.py --install <Half-Life dir>", file=sys.stderr)
            return 2
        print(f"launch the mod with: -game {args.install.name} -console -dev")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

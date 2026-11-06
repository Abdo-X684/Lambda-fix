#!/usr/bin/env python3
"""Build the 32-bit client.so / hl.so WITHOUT gcc-multilib or the game's vgui.so.

Uses Zig as a self-contained i386 cross-compiler (`pip install ziglang`).
Two link-time-only stubs are generated in a temp dir:

* ``GL/gl.h``  - just the two matrix constants used by CFrustum.cpp (values from
  the SDK's own external/SDL2/SDL_opengl.h).
* ``vgui.so``  - an empty ELF32 shared object with SONAME ``vgui.so``; it only
  creates a DT_NEEDED entry. At runtime the REAL vgui.so from your Half-Life
  install resolves the VGUI symbols. No proprietary bytes are shipped.

Run:  python3 tools/build_dlls_zig.py
See docs/BUILDING.md.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "build" / "merged-real"
LINUX = TREE / "linux"
OUT = ROOT / "dist" / "dlls"
TARGET = "x86-linux-gnu"

BASE_CFLAGS = (
    "-std=c++17 -fno-strict-aliasing -fno-exceptions -w -DNDEBUG "
    "-DPOSIX -D_POSIX -DLINUX -D_LINUX -DGNUC -DNO_MALLOC_OVERRIDE -DCLIENT_WEAPONS"
)


def find_zig() -> list[str]:
    if shutil.which("zig"):
        return ["zig"]
    try:
        import ziglang  # type: ignore

        binary = Path(ziglang.__file__).resolve().parent / "zig"
        if binary.is_file():
            return [str(binary)]
    except ImportError:
        pass
    raise SystemExit("Zig not found -> pip install ziglang  (or set zig on PATH)")


def make_vars() -> list[str]:
    return [
        "ARCH=i386", "ARCH_CFLAGS=-O2", "SHLIBEXT=so", "SHLIBCFLAGS=",
        "SHLIBLDFLAGS=-shared", "CPP_LIB=", "CFG=release", "OS=Linux",
        f"BASE_CFLAGS={BASE_CFLAGS}",
        "BUILD_DIR=release", "BUILD_OBJ_DIR=release/obj", "SOURCE_DIR=..",
        "ENGINE_SRC_DIR=../engine", "COMMON_SRC_DIR=../common",
        "PUBLIC_SRC_DIR=../public", "GAME_SHARED_SRC_DIR=../game_shared",
        "PM_SRC_DIR=../pm_shared",
    ]


def run(cmd: list[str], log: str) -> None:
    print("$ " + " ".join(cmd[:6]) + " ...", flush=True)
    with open(log, "w", encoding="utf-8") as fh:
        proc = subprocess.run(cmd, cwd=LINUX, stdout=fh, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        print(f"FAILED ({log}):", file=sys.stderr)
        print(Path(log).read_text(encoding="utf-8")[-2500:], file=sys.stderr)
        raise SystemExit(proc.returncode)


def main() -> int:
    if not (LINUX / "Makefile.hl_cdll").is_file():
        raise SystemExit("run `make fetch && make merge` first")
    zig = find_zig()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "GL").mkdir()
        (tmp / "GL" / "gl.h").write_text(
            "#define GL_MODELVIEW_MATRIX 0x0BA6\n"
            "#define GL_PROJECTION_MATRIX 0x0BA7\n", encoding="utf-8")
        (tmp / "vgui_stub.c").write_text("void __vgui_link_stub(void) {}\n", encoding="utf-8")
        subprocess.run(zig + ["cc", "-target", TARGET, "-shared", "-fPIC",
                              "-Wl,-soname,vgui.so", str(tmp / "vgui_stub.c"),
                              "-o", str(tmp / "vgui.so")], check=True)
        wrapper = tmp / "zig32"
        wrapper.write_text("#!/bin/sh\nexec " + " ".join(zig) +
                           f" c++ -target {TARGET} \"$@\"\n", encoding="utf-8")
        wrapper.chmod(0o755)

        (LINUX / "release").mkdir(parents=True, exist_ok=True)
        (LINUX / "gendbg.sh").chmod(0o755)
        dirs = ["hldll/ctf", "hldll/rope", "hldll/weapons", "hldll/wpn_shared",
                "hl1_client", "particleman", "public", "common", "game_shared", "pm_shared"]
        for rel in dirs:
            (LINUX / "release" / "obj" / rel).mkdir(parents=True, exist_ok=True)

        client_inc = (f"-I{tmp} -I../cl_dll -I../cl_dll/particleman -I../dlls "
                      "-I/usr/include/malloc -I../common -I../public -I../pm_shared "
                      "-I../engine -I../utils/vgui/include -I../game_shared -I../external")
        server_inc = (f"-I{tmp} -I../dlls -I../cl_dll -I../common -I../public "
                      "-I../pm_shared -I../engine -I../game_shared -I../external "
                      "-I../utils/vgui/include")
        client_ld = (f"-shared -Wl,--no-as-needed {tmp}/vgui.so -Wl,--as-needed "
                     "-L. libSDL2-2.0.so.0")
        common = [f"CPLUS={wrapper}"] + make_vars()

        run(["make", "-f", "Makefile.hl_cdll", "-j8",
             f"INCLUDEDIRS={client_inc}", f"LDFLAGS={client_ld}"] + common,
            str(tmp / "client.log"))
        run(["make", "-f", "Makefile.hldll", "-j8",
             f"INCLUDEDIRS={server_inc}", "LDFLAGS=-shared"] + common,
            str(tmp / "server.log"))

        sys.path.insert(0, str(ROOT))
        from tools.build_dlls import write_manifest  # noqa: E402

        OUT.mkdir(parents=True, exist_ok=True)
        manifest = write_manifest(OUT, {
            "client.so": LINUX / "release" / "client.so",
            "hl.so": LINUX / "release" / "hl.so",
        }, {"compiler": f"zig c++ -target {TARGET}", "cfg": "release", "tree": str(TREE)})
        for name, info in manifest["files"].items():
            print(f"  {name}: {info['bytes']} bytes | ELF32={info['elf32']} | "
                  f"sha256={info['sha256'][:16]}…")
        print(f"wrote {OUT / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

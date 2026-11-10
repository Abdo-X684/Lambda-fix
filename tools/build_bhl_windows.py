#!/usr/bin/env python3
"""Build 32-bit WINDOWS ``client.dll`` / ``hl.dll`` from the SAME bhl-op4 tree.

This is a cross-compile companion to ``tools/build_bhl_base.py`` (Linux). It
writes ONLY to ``build-evidence/bhl-windows/`` and never touches any Linux
file, source, log or binary. Both builds stay in the repository.

Uses Zig clang with ``-target x86-windows-gnu`` (PE32 / i386), BHL's own
Windows-conditional CMake source lists, the pinned SDK's Windows import
libraries (tier0.lib / vstdlib.lib / steam_api.lib), a generated SDL2 import
library, and a small set of documented build-overlay patches for the pinned
Source SDK headers (MSVC-oriented) so they compile with MinGW-flavoured clang.

TEST KIND: compile + PE32 link. NOT an in-game test, NOT a Windows runtime
test -- there is no Windows loader or GoldSrc engine in this sandbox.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_bhl_base as B  # noqa: E402  (reuse Linux driver's source lists)

ZIG = B.ZIG
WIN_CXX = [str(ZIG), "c++", "-target", "x86-windows-gnu", "-fms-extensions"]
WIN_CC = [str(ZIG), "cc", "-target", "x86-windows-gnu", "-fms-extensions"]

# NOTE: we deliberately keep POSIX defined (the pinned SDK's steamtypes.h sets
# it for any GCC-like compiler, which also selects the portable SSE helpers),
# while _WIN32 selects BHL's Windows CMake branches and the Win32 CRT.
WIN_COMMON = [
    "-DPLATFORM_WINDOWS", "-DWIN32", "-D_WINDOWS", "-D_WIN32",
    "-D_WIN32_WINNT=0x0601", "-DWINVER=0x0601", "-DNOMINMAX",
    "-DNO_STEAM", "-DNO_MALLOC_OVERRIDE", "-DMATHLIB_HEADER_ONLY",
    "-D_DLL_EXT=.dll", "-DCLIENT_WEAPONS", "-DMATHLIB_USE_C_ASSERT",
    "-DMATHLIB_VECTOR_NONTRIVIAL", "-DHAS_STD_FILESYSTEM=1",
    "-DUSE_UPDATER=0", "-DPOSIX", "-D_POSIX", "-DPCRE_STATIC",
    '-DSOURCE_SDK_GFX_PATH="ui/gfx/vgui"',
    "-DSOURCE_SDK_VGUI_NS_ALIAS", "-DVERSION_SAFE_STEAM_API_INTERFACES",
    "-DGNUC", "-DCOMPILER_GNU", "-DCOMPILER_CLANG",
]
WIN_DEFS = WIN_COMMON
WIN_SDK_DEFS = WIN_COMMON + ["-include", "math.h"]

# Windows-only CMake branches, Windows defines, PE32 linker.
B.ZIG_CXX, B.ZIG_CC = WIN_CXX, WIN_CC
B.BHL_DEFS, B.SDK_DEFS = WIN_DEFS, WIN_SDK_DEFS
B.CLIENT_EXTRA = ["-DCLIENT_DLL"]


def _win_condition(cond: str) -> bool:
    c = cond.strip()
    if c.startswith("NOT "):
        return not _win_condition(c[4:])
    if c in {"PLATFORM_WINDOWS", "WIN32", "COMPILER_GNU"}:
        return True
    if c in {"PLATFORM_LINUX", "LINUX", "UNIX", "PLATFORM_MACOS", "OSX",
             "USE_UPDATER", "GENERATE_AMXX_OFFSETS", "USE_VGUI2"}:
        return False
    return False


B.cmake_condition_true = _win_condition


# ---------------------------------------------------------------------------
# Build-overlay patches (applied to COPIES in the Windows work dir only)
# ---------------------------------------------------------------------------
MEMALLOC_WIN = r'''#ifdef POSIX
#include <malloc.h>
// MinGW provides _aligned_malloc(size, alignment) / _aligned_free directly.
inline void *MemAlloc_Alloc( size_t nSize, const char *pFileName = NULL, int nLine = 0 ) { return malloc( nSize ); }
inline void MemAlloc_Free( void *ptr, const char *pFileName = NULL, int nLine = 0 ) { free( ptr ); }
inline void *MemAlloc_AllocAligned( size_t size, size_t align, const char *pszFile = NULL, int nLine = 0 ) { return _aligned_malloc( size, align ); }
inline void *MemAlloc_AllocAlignedFileLine( size_t size, size_t align, const char *pszFile = NULL, int nLine = 0 ) { return _aligned_malloc( size, align ); }
inline void MemAlloc_FreeAligned( void *pMemBlock, const char *pszFile = NULL, int nLine = 0 ) { _aligned_free( pMemBlock ); }
#endif
'''

STACKWALKER_CPP_PATCHES = [
    ("#include <new>", '#include "win_new_shim.h"'),
    ("#if _MSC_VER < 1400", "#if defined(_MSC_VER) && _MSC_VER < 1400"),
]

STACKWALKER_H_PATCHES = [
    ("#if defined(_MSC_VER)", "#if 1"),
    ("#if _MSC_VER < 1300", "#if 0"),
    ("#if _MSC_VER >= 1300", "#if 1"),
    ("#if defined(_M_IX86)", "#if 0"),
]

WIN_NEW_SHIM = r'''#pragma once
// Minimal placement-new shim for the external StackWalker source. It is NOT
// used by the game DLL sources (they use the real libc++ <new>).
#include <stddef.h>
inline void *operator new(size_t, void *p) noexcept { return p; }
inline void *operator new[](size_t, void *p) noexcept { return p; }
inline void operator delete(void *, void *) noexcept {}
inline void operator delete[](void *, void *) noexcept {}
'''

WINSANI_IN = r'''#pragma once
// On MSVC this header hides Windows' HSPRITE typedef behind a macro so the
// engine's `typedef int HSPRITE` does not clash. clang needs it unconditionally.
#ifdef HSPRITE
#undef HSPRITE
#endif
#define HSPRITE WINDOWS_HSPRITE
'''
WINSANI_OUT = "#pragma once\n#undef HSPRITE\n"


class WinBuilder(B.Builder):
    def __init__(self, args, logf):
        super().__init__(args, logf)
        # Keep ALL overlays under the repo root so B.Builder's source records
        # can use relative paths. This is still Windows-only evidence.
        self.compat = self.out / "compat"

    def setup(self) -> None:
        super().setup()
        self._windows_patches()

    def _windows_patches(self) -> None:
        patches = self.out / "patches"
        patches.mkdir(parents=True, exist_ok=True)
        c = self.compat

        # 1. port.h overlay (quoted/angle includes resolve to compat first).
        port_src = B.TREE / "src/common/port.h"
        (c / "port.h").write_text(port_src.read_text())
        (c / "winsani_in.h").write_text(WINSANI_IN)
        (c / "winsani_out.h").write_text(WINSANI_OUT)

        # 2. case-insensitive Windows SDK header shims (MinGW ships lowercase).
        for upper, lower in (("Dbghelp.h", "dbghelp.h"),
                             ("Winternl.h", "winternl.h"),
                             ("Windows.h", "windows.h")):
            (c / upper).write_text(f"#pragma once\n#include <{lower}>\n")

        # 3. tier0/platform.h: Win32 branch + no MSVC-only macro collisions.
        p = self.sdkinc / "public/tier0/platform.h"
        orig = p.read_text()
        s = orig
        s = s.replace("#ifdef POSIX\n// need this for _alloca\n#include <alloca.h>\n#endif",
                      "#if defined(POSIX) && !defined(_WIN32)\n#include <alloca.h>\n#endif")
        s = s.replace("#if defined( GNUC )\n\t#define stackalloc",
                      "#if defined( GNUC ) && !defined( _WIN32 )\n\t#define stackalloc")
        # The POSIX compatibility block must not override the Win32 CRT or
        # redefine Windows handle types when _WIN32 is also defined.
        for line in ("#define _vsnprintf vsnprintf",
                     "#define GetProcAddress dlsym",
                     "#define _snprintf snprintf"):
            s = re.sub(r"(?m)^" + re.escape(line) + r"\n", "", s)
        s = s.replace("typedef uint32 HMODULE;\ntypedef void *HANDLE;",
                      "#if !defined(_WIN32)\n typedef uint32 HMODULE;\n typedef void *HANDLE;\n#endif")
        # The whole POSIX CRT-remap block conflicts with MinGW's Win32 CRT.
        s = s.replace("#ifdef POSIX", "#if defined(POSIX) && !defined(_WIN32)")
        # MSVC's __forceinline / __restrict confuse clang's declaration matching.
        s = re.sub(r"#define\s+FORCEINLINE\s+__forceinline\s*", "#define FORCEINLINE __attribute__((always_inline)) inline\n", s)
        s = re.sub(r"#define\s+FORCEINLINE_TEMPLATE\s+__forceinline\s*", "#define FORCEINLINE_TEMPLATE inline\n", s)
        s = s.replace("#if defined(LINUX) && !defined(DEDICATED)", "#if 1")
        if s == orig:
            raise SystemExit("[compat] platform.h patterns not found")
        p.write_text(s)
        (patches / "platform.h.patch").write_text("".join(difflib.unified_diff(
            orig.splitlines(True), s.splitlines(True),
            fromfile="pinned-SDK", tofile="windows-overlay", n=3)))

        # alloca.h shim for the generated OP4 fixup source.
        (c / "alloca.h").write_text("#pragma once\n#include <malloc.h>\n")

        # Overlay for BHL's vinterface/interface.cpp: MinGW's GetProcAddress
        # returns FARPROC, and clang rejects static_cast<void* -> fn ptr>.
        vi = B.TREE / "src/public/vinterface/interface.cpp"
        v = vi.read_text()
        v = v.replace("return GetProcAddress(GetModuleHandle(pModuleName), pName);",
                      "return (void *)GetProcAddress(GetModuleHandle(pModuleName), pName);")
        v = v.replace("return GetProcAddress((HINSTANCE)pModuleHandle, pName);",
                      "return (void *)GetProcAddress((HINSTANCE)pModuleHandle, pName);")
        v = v.replace("return reinterpret_cast<CreateInterfaceFn>(GetProcAddress(hDLL, CREATEINTERFACE_PROCNAME));",
                      "return (CreateInterfaceFn)GetProcAddress(hDLL, CREATEINTERFACE_PROCNAME);")
        v = v.replace("return static_cast<CreateInterfaceFn>(Sys_GetProcAddress(pModuleName, CREATEINTERFACE_PROCNAME));",
                      "return (CreateInterfaceFn)Sys_GetProcAddress(pModuleName, CREATEINTERFACE_PROCNAME);")
        overlay = self.compat / "src/public/vinterface/interface.cpp"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        overlay.write_text(v)
        (patches / "interface.cpp.patch").write_text("".join(
            difflib.unified_diff(vi.read_text().splitlines(True),
                                 v.splitlines(True),
                                 fromfile="bhl-op4", tofile="windows-overlay", n=3)))
        # SDK tier1/interface.cpp has the same static_cast<void* -> fn ptr>.
        si = self.sdk / "tier1/interface.cpp"
        sv = si.read_text()
        sv = sv.replace("#ifdef POSIX", "#if defined(POSIX) && !defined(_WIN32)")
        sv = sv.replace("#elif defined(POSIX)", "#elif defined(POSIX) && !defined(_WIN32)")
        sv = sv.replace("return static_cast<CreateInterfaceFn>( Sys_GetProcAddress( pModuleName, CREATEINTERFACE_PROCNAME ) );",
                        "return (CreateInterfaceFn)Sys_GetProcAddress( pModuleName, CREATEINTERFACE_PROCNAME );")
        so = self.compat / "src/tier1/interface.cpp"
        so.parent.mkdir(parents=True, exist_ok=True)
        so.write_text(sv)
        st = self.sdk / "tier1/strtools.cpp"
        stv = st.read_text().replace("#ifdef POSIX", "#if defined(POSIX) && !defined(_WIN32)")
        sto = self.compat / "src/tier1/strtools.cpp"
        sto.parent.mkdir(parents=True, exist_ok=True)
        sto.write_text(stv)
        (patches / "sdk-strtools.cpp.patch").write_text("".join(
            difflib.unified_diff(st.read_text().splitlines(True),
                                 stv.splitlines(True),
                                 fromfile="pinned-SDK", tofile="windows-overlay", n=3)))

        (patches / "sdk-interface.cpp.patch").write_text("".join(
            difflib.unified_diff(si.read_text().splitlines(True),
                                 sv.splitlines(True),
                                 fromfile="pinned-SDK", tofile="windows-overlay", n=3)))

        # 4. tier1/interface.h: don't pull dlfcn.h on Windows.
        p = self.sdkinc / "public/tier1/interface.h"
        orig = p.read_text()
        s = orig.replace("#ifdef _LINUX", "#if defined(_LINUX) && !defined(_WIN32)")
        if s == orig:
            raise SystemExit("[compat] interface.h pattern not found")
        p.write_text(s)
        (patches / "interface.h.patch").write_text("".join(difflib.unified_diff(
            orig.splitlines(True), s.splitlines(True),
            fromfile="pinned-SDK", tofile="windows-overlay", n=3)))

        # 5b. strtools.h needs <math.h> for log10 outside MSVC.
        p = self.sdkinc / "public/tier1/strtools.h"
        orig = p.read_text()
        if "#include <math.h>" not in orig:
            p.write_text("#include <math.h>\n" + orig)
        # 5c. bitbuf.h: FORCEINLINE/RESTRICT mismatch under clang -> plain inline.
        p = self.sdkinc / "public/tier1/bitbuf.h"
        orig = p.read_text()
        s5 = orig.replace("#define BITBUF_INLINE FORCEINLINE", "#define BITBUF_INLINE inline")
        p.write_text(s5)

        # 5a. tier1/UtlSortVector.h: Windows branch uses unqualified Base()/Count()
        #     which clang rejects in a template (Linux branch already uses this->).
        p = self.sdkinc / "public/tier1/UtlSortVector.h"
        orig = p.read_text()
        s5 = orig.replace("qsort_s( Base(), Count(), sizeof(T)",
                          "qsort_s( this->Base(), this->Count(), sizeof(T)")
        if s5 == orig:
            raise SystemExit("[compat] UtlSortVector.h pattern not found")
        p.write_text(s5)
        (patches / "UtlSortVector.h.patch").write_text("".join(
            difflib.unified_diff(orig.splitlines(True), s5.splitlines(True),
                                 fromfile="pinned-SDK",
                                 tofile="windows-overlay", n=3)))

        # 5. tier0/memalloc.h: replace the glibc memalign() block with MinGW.
        p = self.sdkinc / "public/tier0/memalloc.h"
        orig = p.read_text()
        pat = re.compile(r"#ifdef POSIX\n#ifdef OSX.*?inline void MemAlloc_FreeAligned.*?free\( pMemBlock \); \}\n#endif\n", re.S)
        m = pat.search(orig)
        if not m:
            raise SystemExit("[compat] memalloc.h block not found")
        s = orig[:m.start()] + MEMALLOC_WIN + orig[m.end():]
        p.write_text(s)
        (patches / "memalloc.h.patch").write_text("".join(difflib.unified_diff(
            orig.splitlines(True), s.splitlines(True),
            fromfile="pinned-SDK", tofile="windows-overlay", n=3)))

        # 6. External BHL Windows dependency: JochenKalmbach/StackWalker.
        # It is fetched from GitHub at build time into the work dir; a few
        # MSVC-oriented guards are patched in the COPY, never in the repo.
        swsrc = self.work / "stackwalker-src"
        if not (swsrc / "Main/StackWalker/StackWalker.cpp").exists():
            r = subprocess.run(
                ["git", "clone", "--depth", "1",
                 "https://github.com/JochenKalmbach/StackWalker.git", str(swsrc)],
                capture_output=True, text=True, timeout=120)
            if r.returncode:
                raise SystemExit(f"StackWalker fetch failed:\n{r.stderr[:2000]}")
        sw_h = swsrc / "Main/StackWalker/StackWalker.h"
        sw_cpp = swsrc / "Main/StackWalker/StackWalker.cpp"
        h = sw_h.read_text()
        for a, b in STACKWALKER_H_PATCHES:
            h = h.replace(a, b, 1)
        (c / "StackWalker.h").write_text(h)
        cpp = sw_cpp.read_text()
        for a, b in STACKWALKER_CPP_PATCHES:
            cpp = cpp.replace(a, b, 1)
        (c / "StackWalker.cpp").write_text(cpp)
        (c / "win_new_shim.h").write_text(WIN_NEW_SHIM)
        (patches / "StackWalker.h.patch").write_text("".join(
            difflib.unified_diff(sw_h.read_text().splitlines(True),
                                 h.splitlines(True), n=2)))
        (patches / "StackWalker.cpp.patch").write_text("".join(
            difflib.unified_diff(sw_cpp.read_text().splitlines(True),
                                 cpp.splitlines(True), n=2)))
        # Minimal client-side Win32 support symbols: Linux resolves these from
        # libvstdlib.so; the pinned Windows vstdlib.lib does not export them.
        shutil.copy(self.deps / "src/pcre-master/pcre_chartables.c.dist",
                    c / "pcre_chartables.c")
        (c / "win_support.cpp").write_text(r"""
#include <windows.h>
struct CSysModule;
extern "C" void *__acrt_heap = nullptr;
CSysModule *Sys_LoadModule(const char *pModuleName)
{
    return (CSysModule *)LoadLibraryA(pModuleName);
}
""")
        # Keep the evidence tree hygiene-clean: upstream overlays contain
        # trailing whitespace; strip it from the copies only.
        for f in c.rglob("*"):
            if f.is_file():
                try:
                    t = f.read_text()
                except UnicodeDecodeError:
                    continue
                clean = "\n".join(line.rstrip() for line in t.splitlines()) + "\n"
                if clean != t:
                    f.write_text(clean)
        B.log("[compat] Windows build overlays written to " + str(patches),
              self.logf)

    def compile_set(self, tag, sources, **kw):
        ov = {
            B.TREE / "src/public/vinterface/interface.cpp":
                self.compat / "src/public/vinterface/interface.cpp",
            self.sdk / "tier1/interface.cpp":
                self.compat / "src/tier1/interface.cpp",
            self.sdk / "tier1/strtools.cpp":
                self.compat / "src/tier1/strtools.cpp",
        }
        patched = [ov.get(src, src) for src in sources]
        return super().compile_set(tag, patched, **kw)

    def compile_stackwalker(self) -> pathlib.Path:
        """Compile the external StackWalker source with its MSVC compat flags."""
        src = self.compat / "StackWalker.cpp"
        obj = self.obj / "stackwalker" / "StackWalker.o"
        obj.parent.mkdir(parents=True, exist_ok=True)
        cmd = (WIN_CXX + ["-c", "-std=c++17", "-fpermissive", "-g0", "-w",
                          "-fPIC", "-ferror-limit=6"]
               + WIN_DEFS + ["-D_MSC_VER=1900"]
               + ["-I", str(self.compat), "-I", str(self.gen)]
               + ["-o", str(obj), str(src)])
        env = dict(B.os.environ,
                   ZIG_GLOBAL_CACHE_DIR=str(self.cache / "stackwalker"))
        pathlib.Path(env["ZIG_GLOBAL_CACHE_DIR"]).mkdir(parents=True,
                                                       exist_ok=True)
        r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           timeout=300)
        self.commands.append(" ".join(cmd))
        if r.returncode:
            (self.out / "StackWalker.compile.log").write_text(r.stderr)
            raise SystemExit(f"[compile] StackWalker.cpp failed:\n{r.stderr[:3000]}")
        # clang with _MSC_VER=1900 emits /DEFAULTLIB:libc++.lib, which the
        # MinGW-flavoured Zig link cannot open. Strip the directive; version.lib
        # is linked explicitly below.
        subprocess.run(["objcopy", "--remove-section=.drectve", str(obj)],
                       check=True, capture_output=True, text=True)
        self.source_records.append({
            "set": "stackwalker", "source": "external/StackWalker.cpp",
            "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "compiled_from": (str(src.relative_to(B.ROOT))
                              if src.is_relative_to(B.ROOT) else str(src)),
            "object": obj.name, "status": "ok"})
        return obj

    def link(self, name, objs, libs, archives=None):
        target = self.out / name
        group = []
        if archives:
            group = (["-Wl,--start-group"] + [str(a) for a in archives]
                     + ["-Wl,--end-group"])
        cmd = (WIN_CXX + ["-shared", "-Wl,--export-all-symbols",
                          "-o", str(target)]
               + [str(o) for o in objs] + group + [str(l) for l in libs]
               + ["-lws2_32", "-lwsock32", "-lwinmm", "-lole32",
                  "-loleaut32", "-luuid", "-lgdi32", "-luser32",
                  "-ladvapi32", "-lshell32", "-lcomdlg32", "-lcomctl32",
                  "-lshlwapi", "-ldbghelp", "-lpsapi", "-lversion",
                  "-ldinput8", "-ldxguid"])
        B.log(f"[link] {name}: {len(objs)} objects, "
              f"{len(archives or [])} archives, {len(libs)} import libs",
              self.logf)
        env = dict(B.os.environ, ZIG_GLOBAL_CACHE_DIR=str(self.cache / "link"))
        pathlib.Path(env["ZIG_GLOBAL_CACHE_DIR"]).mkdir(parents=True,
                                                       exist_ok=True)
        r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           timeout=600)
        self.commands.append(" ".join(cmd))
        if r.returncode != 0:
            (self.out / f"{name}.link.log").write_text(r.stderr)
            raise SystemExit(f"[link] {name} failed:\n{r.stderr[:4000]}")
        B.log(f"[link] {name}: OK ({target.stat().st_size} bytes)", self.logf)
        return target

    def verify(self, targets):
        info = {}
        for name, p in targets.items():
            fmt = subprocess.run(["objdump", "-f", str(p)],
                                 capture_output=True, text=True).stdout
            data = p.read_bytes()
            info[name] = {
                "path": str(p.relative_to(ROOT)),
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(data).hexdigest(),
                "pe32_i386": "pei-i386" in fmt and "i386" in fmt,
                "is_windows_dll": data[:2] == b"MZ",
            }
            if not (info[name]["pe32_i386"] and info[name]["is_windows_dll"]):
                raise SystemExit(f"[verify] {name} is not a PE32 i386 DLL")
        return info


def _make_sdl_import_lib(out: pathlib.Path) -> pathlib.Path:
    """Generate SDL2.lib from the SDL symbols the Linux client.so imports."""
    undef = subprocess.run(
        ["nm", "-u", str(ROOT / "build-evidence/bhl-base/client.so")],
        capture_output=True, text=True, check=True).stdout
    syms = sorted({ln.strip()[2:] for ln in undef.splitlines()
                   if ln.strip().startswith("U SDL_")})
    def_path = out / "SDL2.def"
    lib_path = out / "SDL2.lib"
    def_path.write_text("LIBRARY SDL2.dll\nEXPORTS\n"
                        + "".join(f"    {s}\n" for s in syms))
    r = subprocess.run([str(ZIG), "dlltool", "-m", "i386", "-d",
                        str(def_path), "-D", "SDL2.dll", "-l", str(lib_path)],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"dlltool failed:\n{r.stderr[:2000]}")
    return lib_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path,
                    default=ROOT / "build-evidence/bhl-windows")
    ap.add_argument("--work", type=pathlib.Path,
                    default=pathlib.Path("/tmp/bhlbuild-win"))
    ap.add_argument("--sdk", type=pathlib.Path, default=B.DEFAULT_SDK)
    ap.add_argument("--deps", type=pathlib.Path,
                    default=ROOT / ".cache/bhl-build/deps")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    args.out = args.out.resolve()
    args.work = args.work.resolve()
    args.sdk = args.sdk.resolve()
    args.deps = args.deps.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    logf = (args.out / "build.log").open("w")

    B.log("=== bhl-op4 32-bit WINDOWS cross-build (Linux tree untouched) ===",
          logf)
    B.log(f"out  : {args.out}", logf)
    B.log(f"zig  : {ZIG} (x86-windows-gnu / PE32 i386)", logf)

    B.fetch_deps(args.deps, logf)
    b = WinBuilder(args, logf)
    b.setup()

    common = B.common_sources()
    client = B.game_sources("client", common, logf)
    server = B.game_sources("server", common, logf)
    B.log(f"[cmake] client={len(client)} server={len(server)} "
          f"common={len(common)} (Windows branches)", logf)
    # The vinterface overlay lives outside its original directory; put its
    # header path FIRST so it wins over the SDK's tier1/interface.h.
    game_inc = ["-I", str(B.TREE / "src/public/vinterface")] + b.includes("game")
    sdk_inc = b.includes("sdk")

    c_obj = b.compile_set("client", client, defs=WIN_DEFS + B.CLIENT_EXTRA,
                          includes=game_inc,
                          force_include=B.TREE / "src/game/client/pch.h")
    sw_obj = b.compile_stackwalker()
    sup_obj = b.compile_set("win_support", [b.compat / "win_support.cpp"],
                            defs=WIN_DEFS + B.CLIENT_EXTRA,
                            includes=game_inc)
    c_obj = c_obj + [sw_obj] + sup_obj
    s_obj = b.compile_set("server", server, defs=WIN_DEFS + ["-DSERVER_DLL"],
                          includes=game_inc)

    tier1 = B.sdk_sources(args.sdk, "tier1/CMakeLists.txt",
                          "TIER1_SOURCE_FILES", "tier1")
    tier1 += [args.sdk / "tier1" / f for f in
              ("processor_detect_linux.cpp", "pathmatch.cpp", "qsort_s.cpp")]
    tier1 = sorted(set(tier1))
    tier2 = B.sdk_sources(args.sdk, "tier2/CMakeLists.txt",
                          "TIER2_SOURCE_FILES", "tier2")
    vgui = B.sdk_sources(args.sdk, "vgui2/vgui_controls/CMakeLists.txt",
                         "VGUI_CONTROLS_SOURCE_FILES", "vgui2/vgui_controls")
    t1 = b.compile_set("tier1", tier1, defs=WIN_SDK_DEFS, includes=sdk_inc)
    t2 = b.compile_set("tier2", tier2, defs=WIN_SDK_DEFS, includes=sdk_inc)
    vg = b.compile_set("vgui_controls", vgui, defs=WIN_SDK_DEFS,
                       includes=sdk_inc,
                       force_include=b.compat / "vgui_pch.h")
    gl = b.compile_set("glad", [B.TREE / "external/glad/src/glad.c"],
                       defs=WIN_SDK_DEFS, includes=sdk_inc, cc=WIN_CC,
                       std="-std=c11")
    sv = b.compile_set("semver", [B.TREE / "external/semver.c/semver.c"],
                       defs=WIN_SDK_DEFS, includes=sdk_inc, cc=WIN_CC,
                       std="-std=c11")
    pcre_src = args.deps / "src/pcre-master"
    pcre = sorted(p for p in pcre_src.glob("pcre_*.c")
                  if not p.name.startswith(("pcre16_", "pcre32_", "pcrecpp_",
                                            "pcreposix_", "pcre_jit_test",
                                            "pcre_printint")))
    pcre.append(b.compat / "pcre_chartables.c")
    pc = b.compile_set("pcre", pcre, defs=WIN_SDK_DEFS, includes=sdk_inc,
                       cc=WIN_CC, std="-std=c11",
                       extra=["-DHAVE_CONFIG_H", "-DPCRE_STATIC",
                              "-DSUPPORT_PCRE8", "-DSUPPORT_UTF",
                              "-DSUPPORT_UCP", "-I" + str(pcre_src)])

    sdl_lib = _make_sdl_import_lib(args.out)
    sdk_lib = args.sdk / "lib/public"
    libs = [sdl_lib, sdk_lib / "tier0.lib", sdk_lib / "vstdlib.lib",
            sdk_lib / "steam_api.lib"]
    archives = [b.archive(n, o) for n, o in
                (("vgui_controls", vg), ("tier2", t2), ("tier1", t1),
                 ("glad", gl), ("semver", sv), ("pcre", pc))]

    client_dll = b.link("client.dll", c_obj, libs, archives)
    hl_dll = b.link("hl.dll", s_obj, [], [b.archive("semver", sv)])
    info = b.verify({"client.dll": client_dll, "hl.dll": hl_dll})

    manifest = {
        "target": "x86-windows-gnu / PE32 i386 (MinGW-style import libs)",
        "tree": "bhl-op4 (same generated tree as the Linux build)",
        "note": "Cross-compiled with Zig clang. The engine supplies SDL2.dll, "
                "tier0.dll, vstdlib.dll and steam_api.dll at load time. "
                "Windows-specific BHL sources and the external StackWalker "
                "crash-handler dependency are compiled from upstream.",
        "test_kind": "compile + PE32 link (NOT an in-game / Windows runtime test)",
        "libraries": info,
        "source_lists": {"client": len(client), "server": len(server)},
        "compile_units": len(b.source_records),
    }
    (args.out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (args.out / "BUILD_COMMANDS.txt").write_text("\n".join(b.commands) + "\n")
    (args.out / "SOURCES.sha256").write_text(
        "\n".join(f"{r['sha256']}  {r['compiled_from']}"
                  for r in b.source_records) + "\n")
    B.log(json.dumps(info, indent=2), logf)
    print(f"OK: {client_dll} / {hl_dll}")
    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

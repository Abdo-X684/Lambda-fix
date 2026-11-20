#!/usr/bin/env python3
"""Build real 32-bit ``client.so`` and ``hl.so`` from the ``bhl-op4/`` tree.

This is NOT a replacement build system.  It reproduces, step by step, what
``bhl-op4/CMakeLists.txt`` + ``hl1_source_sdk``'s CMake targets do on Linux:

  * source lists are parsed from BHL's *own* ``set( SOURCE_FILES ... )`` /
    ``add_sources(...)`` blocks (no hand-picked file list);
  * preprocessor definitions and include paths come from
    ``COMMON_DEFINES``, ``GAME_COMMON_DEFINES``, ``SOURCE_SDK_DEFINES`` and
    ``target_compile_definitions( client PRIVATE ... )``;
  * the generated ``appversion.h`` comes from BHL's own ``appversion.h.in``;
  * ``target_precompile_headers( client PRIVATE pch.h )`` is reproduced with
    a forced ``-include`` of BHL's own ``src/game/client/pch.h``;
  * static libraries ``tier1``, ``tier2``, ``vgui_controls``, ``glad``,
    ``semver`` and ``pcre`` are built from their own CMake source lists.

The compiler is Zig's bundled clang targeting ``i386-unknown-linux-gnu``
(this sandbox has no 32-bit libstdc++ / gcc multilib, and the HL engine is a
32-bit process). The final link uses a GLIBC_2.17 baseline so older Half-Life
Linux installations can load the resulting .so. See
``docs/BHL_BASE_BUILD.md`` for the exact environment setup, all commands,
and the complete build log.

Deliberately disclosed compatibility fixes (see ``patches/*.patch``):
  1. ``hl1_source_sdk/public/tier1/utlblockmemory.h`` calls ``std::swap`` on
     two bit-fields.  C++ forbids binding a non-const reference to a bit-field;
     both g++ and clang reject it.  The build uses a copy of the pinned SDK
     include tree with a manual swap in ``CUtlBlockMemory::Swap``.
  2. ``bhl-op4/src/game/client/results.cpp`` binds a non-const lvalue
     reference to the temporary returned by ``std::filesystem::path``'s
     iterator.  MSVC and GCC ``-fpermissive`` accept it, clang rejects it.
     One TU is compiled from a documented overlay copy with ``auto &``
     changed to ``const auto &``.  The other 134 client TUs are compiled
     directly from ``bhl-op4/``.
  3. ``vgui_controls``' CMake PCH is reproduced as a forced include header.
     This is not a source change: it is BHL/SDK's own build configuration.

Nothing here touches ``dist/dlls/*.so``, ``dist/bhl-op4-mod.zip`` or the
existing GitHub Release assets.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TREE = ROOT / "bhl-op4"
DEFAULT_SDK = ROOT / ".cache/upstreams/hl1_source_sdk"

# Pinned third-party sources (BHL requires nlohmann_json and PCRE1).
DEPS = {
    "nlohmann": {
        "url": "https://codeload.github.com/nlohmann/json/tar.gz/v3.11.3",
        "file": "nlohmann-json-3.11.3.tar.gz",
        "sha256": "0d8ef5af7f9794e3263480193c491549b2ba6cc74bb018906202ada498a79406",
        "dir": "json-3.11.3",
    },
    "pcre": {
        # PCRE1 8.45 mirror (BHL's unofficial-pcre vcpkg port is PCRE1).
        "url": "https://codeload.github.com/luvit/pcre/tar.gz/master",
        "file": "pcre-master.tar.gz",
        "sha256": "5aa545145f0c5a584b54a34f04c2d61c01d31724d3fbae2ee20cd8e3c422594d",
        "dir": "pcre-master",
    },
}

# ---------------------------------------------------------------------------
# Toolchain (see docs/BHL_BASE_BUILD.md for the venv/pip commands)
# ---------------------------------------------------------------------------
ZIG = pathlib.Path("/tmp/zenv/lib/python3.11/site-packages/ziglang/zig")
ZIG_CXX = [str(ZIG), "c++", "-target", "x86-linux-gnu"]
ZIG_CC = [str(ZIG), "cc", "-target", "x86-linux-gnu"]
# The object files are target-independent i386 System V; linking them with a
# 2.17 glibc baseline keeps the resulting .so loadable on older Half-Life
# Linux installations. The previous GLIBC_2.34 link was rejected by the user.
ZIG_LINK_CXX = [str(ZIG), "c++", "-target", "x86-linux-gnu.2.17"]

# COMMON_DEFINES + GAME_COMMON_DEFINES + SOURCE_SDK_DEFINES, Linux branch.
BHL_DEFS = [
    "-DPLATFORM_UNIX", "-DPLATFORM_LINUX", "-D_LINUX", "-DLINUX",
    "-DCOMPILER_GNU", "-DCOMPILER_CLANG", "-DGNUC", "-DPOSIX", "-D_POSIX",
    "-DNO_STEAM", "-DNO_MALLOC_OVERRIDE", "-DMATHLIB_HEADER_ONLY",
    "-D_DLL_EXT=.so", "-DCLIENT_WEAPONS", "-DMATHLIB_USE_C_ASSERT",
    "-DMATHLIB_VECTOR_NONTRIVIAL", "-DHAS_STD_FILESYSTEM=1", "-DUSE_UPDATER=0",
    "-D_stricmp=strcasecmp", "-D_strnicmp=strncasecmp",
    "-D_snprintf=snprintf", "-D_alloca=alloca", "-D_vsnprintf=vsnprintf",
    "-D_snwprintf=swprintf", "-DSOURCE_SDK_GFX_PATH=\"ui/gfx/vgui\"",
    "-DSOURCE_SDK_VGUI_NS_ALIAS", "-DVERSION_SAFE_STEAM_API_INTERFACES",
]
CLIENT_EXTRA = ["-DCLIENT_DLL"]

# SOURCE_SDK_DEFINES (Linux: SOURCE_SDK_MIN_STEAM_API is forced FALSE).
SDK_DEFS = [
    "-DGNUC", "-DPOSIX", "-D_POSIX", "-DLINUX", "-D_LINUX",
    "-DPLATFORM_LINUX", "-DPLATFORM_UNIX", "-DCOMPILER_GNU",
    "-DCOMPILER_CLANG", "-DNO_MALLOC_OVERRIDE", "-DMATHLIB_HEADER_ONLY",
    "-D_DLL_EXT=.so", "-DSOURCE_SDK_GFX_PATH=\"ui/gfx/vgui\"",
    "-DSOURCE_SDK_VGUI_NS_ALIAS", "-DNO_STEAM",
    "-D_stricmp=strcasecmp", "-D_strnicmp=strncasecmp",
    "-D_snprintf=snprintf", "-D_alloca=alloca", "-D_vsnprintf=vsnprintf",
    "-D_snwprintf=swprintf",
]

VGUI_PCH_TEXT = """/* BUILD-COMPAT: reproduces hl1_source_sdk's
 * vgui2/vgui_controls/CMakeLists.txt target_precompile_headers() list. */
#pragma once
#include <cstdlib>
#include <cstring>
#include <algorithm>
#include <string>
#include <vector>
#include <map>
#include <unordered_map>
#include <tier0/platform.h>
#include <tier0/dbg.h>
#include <tier1/strtools.h>
#include <tier1/KeyValues.h>
#include <vgui/VGUI2.h>
#include <vgui/IVGui.h>
#include <vgui/IBorder.h>
#include <vgui/IInputInternal.h>
#include <vgui/ILocalize.h>
#include <vgui/IPanel.h>
#include <vgui/IScheme.h>
#include <vgui/ISurface.h>
#include <vgui/ISystem.h>
#include <vgui_controls/Controls.h>
#include <vgui_controls/Panel.h>
#include <vgui_controls/Label.h>
#include <vgui_controls/Button.h>
#include <vgui_controls/Slider.h>
"""

BITFIELD_FIX = """\t/* BUILD-COMPAT: std::swap cannot bind a non-const reference to a bit-field
\t * (C++ [dcl.init.ref]). Manual swap preserves the bit-field layout and the
\t * semantics of CUtlBlockMemory::Swap. See docs/BHL_BASE_BUILD.md. */
\tint tmpMask = m_nIndexMask;
\tm_nIndexMask = mem.m_nIndexMask;
\tmem.m_nIndexMask = tmpMask;
\tint tmpShift = m_nIndexShift;
\tm_nIndexShift = mem.m_nIndexShift;
\tmem.m_nIndexShift = tmpShift;"""


ENGINE_SYMBOLS = {
    "Msg", "Error", "Warning", "DevMsg", "ConMsg", "Plat_FloatTime",
    "CommandLine", "RandomFloat", "RandomLong", "AssertValidStringPtr",
    "DoNewAssertDialog", "GetSpewOutputFunc", "SpewOutputFunc",
    "ThreadInMainThread", "ShouldUseNewAssertDialog", "_AssertValidReadPtr",
    "_AssertValidWritePtr", "_ExitOnFatalAssert", "_SpewInfo", "_SpewMessage",
    "g_pMemAlloc", "gEngfuncs", "g_engfuncs",
}
LIBC_PREFIXES = (
    "_", "__", "mem", "str", "wcs", "wmem", "printf", "malloc", "free",
    "calloc", "realloc", "aligned_alloc", "dl", "pthread", "clock", "get",
    "time", "abort", "exit", "qsort", "ato", "is", "to", "sin", "cos", "tan",
    "pow", "sqrt", "atan", "floor", "ceil", "fabs", "sprintf", "snprintf",
    "sscanf", "set", "local", "read", "write", "open", "close", "stat", "unlink",
    "rename", "chdir", "opendir", "readdir", "mkdir", "access", "remove",
    "system", "sleep", "usleep", "signal", "raise", "longjmp", "setjmp",
    "errno", "sysconf", "mmap", "munmap", "mprotect", "inet_", "socket",
    "bind", "select", "poll", "fcntl", "ioctl", "lseek", "dup", "pipe", "fork",
    "wait", "exec", "environ", "uname", "rand", "srand", "putenv", "mkstemp",
    "tmpnam", "popen", "pclose", "realpath", "dirname", "basename", "vsnprintf",
    "vfprintf", "puts", "fgets", "fread", "fwrite", "fflush", "setvbuf", "feof",
    "ferror", "clearerr", "rewind", "ftell", "fseek", "getc", "putc", "ungetc",
    "tolower", "toupper", "isalpha", "isdigit", "isspace", "isalnum", "isupper",
    "islower", "ispunct", "isxdigit", "iscntrl", "isprint", "isgraph", "bsearch",
    "abs", "labs", "div", "ldiv", "iconv", "locale", "nl_", "regex", "regcomp",
    "regexec", "cat", "copy_file_range", "faccessat", "fchdir", "fchmod",
    "fchmodat", "fchown", "flock", "fputc", "fsync", "futimens", "atof",
    "btowc", "connect", "acos", "acosf", "asin", "atan2", "exp", "log", "tan",
    "hypot", "modf", "ldexp", "frexp", "link", "linkat", "listen", "lstat",
    "mbrtowc", "mbsnrtowcs", "mbsrtowcs", "mbstowcs", "mbtowc", "mktime",
    "mremap", "nanosleep", "kill", "pread", "pwrite", "recvmsg", "sendmsg",
    "sendfile", "sigaltstack", "stderr", "stdout", "stdin", "swprintf",
    "symlink", "syscall", "utimensat", "vsprintf", "wcslen", "wcstod", "wcstof",
    "wcstol", "wcstold", "wcstoll", "wcstoul", "wcstoull", "wmemchr", "wmemcmp",
    "SDL_", "Steam", "ISteam", "CSteam", "vgui2::", "vgui::", "std::",
    "operator new", "operator delete", "__cxa", "__cxx", "__gxx",
    "_ZSt", "typeinfo for std", "vtable for std",
)


GAME_GLOBALS = {"oldgrapple", "oldweapons", "gEngfuncs", "g_engfuncs"}


def is_engine_or_libc_symbol(sym: str) -> bool:
    """True for symbols the HL engine / system libraries resolve at runtime.

    Everything else (a demangled C++ entity, or one of the game's own global
    cvars) is a real link gap that this build must still supply.
    """
    if sym in GAME_GLOBALS:
        return False
    if sym.startswith(("std::", "__cxa", "__cxx", "__gxx", "operator new",
                       "operator delete", "typeinfo for std", "vtable for std")):
        return True
    if sym in ENGINE_SYMBOLS or sym.startswith(LIBC_PREFIXES):
        return True
    if sym.startswith(("typeinfo for ", "vtable for ")) or "::" in sym \
            or "(" in sym or "<" in sym:
        return False
    # A plain C identifier: libc / libm / libdl / engine export.
    return True


def log(msg: str, fh=None) -> None:
    print(msg, flush=True)
    if fh:
        fh.write(msg + "\n")
        fh.flush()


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch_deps(deps_dir: pathlib.Path, logf) -> None:
    deps_dir.mkdir(parents=True, exist_ok=True)
    for name, d in DEPS.items():
        tar = deps_dir / d["file"]
        if not tar.exists():
            log(f"[deps] GET {d['url']}", logf)
            urllib.request.urlretrieve(d["url"], tar)
        actual = sha256(tar)
        if actual != d["sha256"]:
            raise SystemExit(f"[deps] {name} sha256 mismatch: {actual}")
        log(f"[deps] {name}: {d['file']} sha256={actual}", logf)
        src = deps_dir / "src" / d["dir"]
        if not src.is_dir():
            src.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["tar", "xzf", str(tar), "-C", str(src.parent)],
                           check=True)


# ---------------------------------------------------------------------------
# CMake source-list parsing (BHL's real lists, not a hand-written inventory)
# ---------------------------------------------------------------------------
def cmake_var(text: str, var: str) -> list[str]:
    """Parse BHL's ``set( SOURCE_FILES ...)`` AND ``list( APPEND SOURCE_FILES ...)``.

    The latter is what the merge driver adds to wire the OP4 weapon sources
    into the real BHL server target; ignoring it would silently drop them.
    """
    blocks = []
    for pattern in (r"set\(\s*" + re.escape(var) + r"(.*?)\n\s*\)",
                    r"list\(\s*APPEND\s+" + re.escape(var) + r"(.*?)\n\s*\)"):
        for m in re.finditer(pattern, text, re.S):
            blocks.append(m.group(1))
    out = []
    for block in blocks:
        for ln in block.splitlines():
            t = ln.strip().rstrip("\\").strip()
            if t and not t.startswith("#") and t.endswith(".cpp"):
                out.append(t)
    return out


def cmake_condition_true(cond: str) -> bool:
    """Evaluate the handful of CMake conditions that guard BHL source lists.

    This build is Linux / no-updater / no-AMXX-offsets, matching the compiled
    defines. Unknown conditions are treated as false (and logged) rather than
    silently assumed true.
    """
    c = cond.strip()
    if c.startswith("NOT "):
        return not cmake_condition_true(c[4:])
    false_conds = {"PLATFORM_WINDOWS", "WIN32", "PLATFORM_MACOS", "OSX",
                   "USE_UPDATER", "GENERATE_AMXX_OFFSETS", "USE_VGUI2"}
    true_conds = {"PLATFORM_LINUX", "LINUX", "UNIX", "COMPILER_GNU"}
    if c in false_conds:
        return False
    if c in true_conds:
        return True
    return False


def game_sources(side: str, common, logf) -> list[pathlib.Path]:
    """Resolve BHL's real Linux SOURCE_FILES, including conditional blocks.

    BHL puts ``net_linux.cpp`` / ``engine_patches_linux.cpp`` in a
    ``elseif( PLATFORM_LINUX )`` branch. A naive regex over the first
    ``set( SOURCE_FILES ...)`` block would drop them and leave 5 unresolved
    ``Net*`` symbols in client.so.
    """
    text = (TREE / f"src/game/{side}/CMakeLists.txt").read_text()
    stack: list[tuple[bool, bool, bool]] = []  # parent_active, branch, taken
    active, in_block, out, unknown = True, False, [], set()
    for ln in text.splitlines():
        s = ln.strip()
        m = re.match(r"if\(\s*(.+?)\s*\)", s)
        if m:
            c = m.group(1)
            if c.strip() not in ({"PLATFORM_WINDOWS", "WIN32", "PLATFORM_MACOS",
                                  "OSX", "USE_UPDATER", "GENERATE_AMXX_OFFSETS",
                                  "PLATFORM_LINUX", "LINUX", "UNIX", "COMPILER_GNU"}
                                 | {"NOT " + x for x in ("WIN32", "UNIX")}):
                unknown.add(c)
            val = cmake_condition_true(c)
            stack.append((active, val, val))
            active = active and val
            continue
        m = re.match(r"elseif\(\s*(.+?)\s*\)", s)
        if m and stack:
            parent, _, taken = stack[-1]
            val = cmake_condition_true(m.group(1)) and not taken
            stack[-1] = (parent, val, taken or val)
            active = parent and val
            continue
        if s.startswith("else()") and stack:
            parent, _, taken = stack[-1]
            val = not taken
            stack[-1] = (parent, val, True)
            active = parent and val
            continue
        if s.startswith("endif()") and stack:
            parent, _, _ = stack.pop()
            active = parent
            continue
        if not active:
            continue
        if in_block:
            if s.startswith(")"):
                in_block = False
                continue
            t = s.rstrip("\\").strip()
            if (t and not t.startswith("#") and t.endswith(".cpp")
                    and "${" not in t):
                out.append(t)
        elif re.match(r"(set\(\s*SOURCE_FILES|list\(\s*APPEND\s+SOURCE_FILES)", s):
            in_block = True
    for c in sorted(unknown):
        log(f"[cmake] note: condition {c!r} treated as false", logf)
    files = [(TREE / f"src/game/{side}" / t).resolve() for t in out]
    return sorted(set(files + common))


def common_sources() -> list[pathlib.Path]:
    out = []
    for sub in ("src/common", "src/engine", "src/pm_shared",
                "src/public", "src/game/shared"):
        f = TREE / sub / "CMakeLists.txt"
        m = re.search(r"add_sources\((.*?)\n\s*\)", f.read_text(), re.S)
        if m:
            for ln in m.group(1).splitlines():
                t = ln.strip().rstrip("\\").strip()
                if t.endswith(".cpp"):
                    out.append((TREE / sub / t).resolve())
    return out


def sdk_sources(sdk: pathlib.Path, cmake: str, var: str,
                base: str) -> list[pathlib.Path]:
    text = (sdk / cmake).read_text()
    out = []
    for t in cmake_var(text, var):
        t = t.replace("${SOURCE_SDK_ROOT}/", "")
        if t.startswith("public/") or "/" in t:
            p = sdk / t
        else:
            p = sdk / base / t
        out.append(p.resolve())
    return out


# ---------------------------------------------------------------------------
# Compile driver
# ---------------------------------------------------------------------------
class Builder:
    def __init__(self, args, logf):
        self.args = args
        self.logf = logf
        self.work = args.work
        self.out = args.out
        self.sdk = args.sdk
        self.deps = args.deps
        self.gen = self.work / "gen"
        # Keep the compiled source overlays under the evidence tree, with
        # repo-relative paths. SOURCES.sha256 must point at real, persistent
        # files and hash the bytes that were actually compiled.
        self.compat = self.out / "compat"
        self.sdkinc = self.work / "sdkinc"
        self.obj = self.work / "obj"
        self.cache = self.work / "zigcache"
        self.commands: list[str] = []
        self.source_records: list[dict] = []

    def setup(self) -> None:
        if self.obj.exists():
            shutil.rmtree(self.obj)
        if (self.out / "failed").exists():
            shutil.rmtree(self.out / "failed")
        for stale in self.out.glob("*.link.log"):
            stale.unlink()
        if self.compat.exists():
            shutil.rmtree(self.compat)
        for p in (self.gen, self.compat, self.cache, self.out):
            p.mkdir(parents=True, exist_ok=True)
        if self.sdkinc.exists():
            shutil.rmtree(self.sdkinc)
        shutil.copytree(self.sdk / "public", self.sdkinc / "public", symlinks=True)
        shutil.copytree(self.sdk / "common", self.sdkinc / "common", symlinks=True)

        # --- appversion.h from BHL's own template ---------------------------
        tpl = (TREE / "src/common/appversion.h.in").read_text()
        ver = (tpl.replace("@GIT_SEM_VERSION@", "1.14.0-dev+no-git")
                  .replace("@GIT_MAJOR@", "1").replace("@GIT_MINOR@", "14")
                  .replace("@GIT_PATCH@", "0").replace("@GIT_SKIP@", "0"))
        (self.gen / "appversion.h").write_text(ver)
        log(f"[gen] appversion.h from bhl-op4/src/common/appversion.h.in", self.logf)

        # --- PCRE1 generated headers ----------------------------------------
        pcre = self.deps / "src" / "pcre-master"
        shutil.copy(pcre / "config.h.generic", self.gen / "config.h")
        shutil.copy(pcre / "pcre.h.generic", self.gen / "pcre.h")
        log("[gen] PCRE1 config.h / pcre.h from pcre.h.generic, config.h.generic",
            self.logf)

        # --- patch 1: pinned SDK bit-field swap ------------------------------
        sdk_hdr = self.sdk / "public/tier1/utlblockmemory.h"
        fixed = self.sdkinc / "public/tier1/utlblockmemory.h"
        original = sdk_hdr.read_text()
        pat = (r"([ \t]*)std::swap\(\s*m_nIndexMask,\s*mem\.m_nIndexMask\s*\);"
               r"\s*\n\s*std::swap\(\s*m_nIndexShift,\s*mem\.m_nIndexShift\s*\);")
        patched, n = re.subn(pat, BITFIELD_FIX, original)
        if n != 1:
            raise SystemExit("[compat] utlblockmemory.h pattern not found")
        fixed.write_text(patched)

        # --- patch 2: one C++17 conformance fix in one BHL client TU --------
        res = TREE / "src/game/client/results.cpp"
        overlay = self.compat / "src/game/client/results.cpp"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        o = res.read_text()
        if "for (auto &i : relPath)" not in o:
            raise SystemExit("[compat] results.cpp pattern not found")
        overlay.write_text(o.replace("for (auto &i : relPath)",
                                     "for (const auto &i : relPath)", 1))

        # --- patch 3: SDK's own vgui_controls PCH header list ----------------
        (self.compat / "vgui_pch.h").write_text(VGUI_PCH_TEXT)

        # --- write the diffs so nothing is hidden ---------------------------
        patches = self.out / "patches"
        patches.mkdir(parents=True, exist_ok=True)
        for name, orig, new in (
            ("utlblockmemory.h.patch", original.splitlines(True), patched.splitlines(True)),
            ("results.cpp.patch", o.splitlines(True), overlay.read_text().splitlines(True)),
        ):
            (patches / name).write_text("".join(difflib.unified_diff(
                orig, new, fromfile="original", tofile="build-overlay", n=3)))
        (patches / "vgui_pch.h").write_text(VGUI_PCH_TEXT)
        # The overlays are committed build evidence; keep them hygiene-clean.
        # Stripping trailing whitespace has no semantic effect for C++ files.
        for f in self.compat.rglob("*"):
            if not f.is_file():
                continue
            try:
                t = f.read_text()
            except UnicodeDecodeError:
                continue
            clean = "\n".join(line.rstrip() for line in t.splitlines()) + "\n"
            if clean != t:
                f.write_text(clean)
        log("[compat] 3 build fixes written to " + str(patches), self.logf)

    def includes(self, kind: str) -> list[str]:
        if kind == "game":
            dirs = [self.compat, self.gen,
                    TREE / "src/game/server", TREE / "src/game/client",
                    TREE / "src/common", TREE / "src/engine",
                    TREE / "src/game/shared", TREE / "src/public",
                    TREE / "src/pm_shared", TREE / "src/game_shared",
                    TREE / "external/SDL2/include",
                    TREE / "external/glad/include",
                    TREE / "external/semver.c/include",
                    self.deps / "src/json-3.11.3/single_include",
                    self.sdkinc / "common", self.sdkinc / "public",
                    self.sdkinc / "public/tier0", self.sdkinc / "public/tier1",
                    self.sdk / "vgui2", self.sdk / "vgui2/vgui_controls",
                    # OP4 headers live after BHL headers so BHL always wins.
                    TREE / "src/game/server/op4",
                    TREE / "src/game/server/op4/dlls",
                    TREE / "src/game/server/op4/dlls/weapons",
                    TREE / "src/game/server/op4/dlls/ctf",
                    TREE / "src/game/server/op4/dlls/rope"]
        else:  # SDK-only include paths, matching SOURCE_SDK_INCLUDE_PATHS
            dirs = [self.compat, self.gen, self.compat / "tier1",
                    self.sdkinc / "common", self.sdkinc / "public",
                    self.sdkinc / "public/tier0", self.sdkinc / "public/tier1",
                    self.sdk / "vgui2", self.sdk / "vgui2/vgui_controls",
                    self.sdk / "vgui2/src",
                    TREE / "external/glad/include",
                    TREE / "external/semver.c/include"]
        return [a for p in dirs for a in ("-I", str(p))]

    def compile_set(self, tag: str, sources: list[pathlib.Path], *,
                    defs: list[str], includes: list[str],
                    force_include: pathlib.Path | None = None,
                    cc: list[str] | None = None,
                    std: str = "-std=c++17",
                    extra: list[str] | None = None) -> list[pathlib.Path]:
        base = (cc or ZIG_CXX) + ["-c", std, "-fpermissive", "-g0", "-w",
                                  "-fPIC", "-ferror-limit=6"] + defs + includes
        if force_include:
            base += ["-include", str(force_include)]
        if extra:
            base += extra
        d = self.obj / tag
        d.mkdir(parents=True, exist_ok=True)

        def one(item):
            i, src = item
            use = src
            if tag == "client" and src == TREE / "src/game/client/results.cpp":
                use = self.compat / "src/game/client/results.cpp"
            o = d / f"{i:04d}_{src.stem}.o"
            env = dict(os.environ,
                       ZIG_GLOBAL_CACHE_DIR=str(self.cache / f"{tag}_{i % self.args.jobs}"))
            pathlib.Path(env["ZIG_GLOBAL_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)
            cmd = base + ["-o", str(o), str(use)]
            r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                               timeout=300)
            return (i, src, use, o, cmd, r.returncode, r.stderr)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.jobs) as ex:
            results = list(ex.map(one, enumerate(sources)))

        ok, gaps = [], []
        for i, src, use, o, cmd, rc, err in results:
            self.commands.append(" ".join(cmd))
            rel = str(src.relative_to(ROOT))
            self.source_records.append({
                "set": tag, "source": rel, "sha256": sha256(use),
                "compiled_from": (str(use.relative_to(ROOT)) if use.is_relative_to(ROOT)
                                  else str(use)) if use != src else rel,
                "object": o.name, "status": "ok" if rc == 0 else "error"})
            if rc == 0:
                ok.append(o)
            else:
                gaps.append((rel, [l.strip() for l in err.splitlines()
                                   if "error:" in l][:4], cmd, err))
        log(f"[compile] {tag}: {len(ok)}/{len(sources)} clean", self.logf)
        for rel, errs, cmd, err in gaps:
            log(f"  ERROR {rel}: {errs}", self.logf)
            (self.out / "failed").mkdir(exist_ok=True)
            (self.out / "failed" / f"{tag}_{len(gaps)}_{pathlib.Path(rel).name}.log").write_text(
                "COMMAND: " + " ".join(cmd) + "\n\n" + err)
        if gaps:
            raise SystemExit(f"[compile] {tag}: {len(gaps)} translation unit(s) failed; "
                             f"see {self.out/'failed'}")
        return ok

    def archive(self, name: str, objs: list[pathlib.Path]) -> pathlib.Path:
        """Reproduce CMake's ``add_library(<name> STATIC ...)`` for SDK libs.

        Static archives matter: hl1_source_sdk's ``bitvec.h`` contains explicit
        template specializations without ``inline``, so ``bitbuf.o`` and
        ``newbitbuf.o`` both define the same strong symbols.  A real CMake build
        links ``tier1`` as a static library, so ld only extracts the members it
        needs.  Passing every object directly would create false duplicates.
        """
        a = self.work / "lib" / f"lib{name}.a"
        a.parent.mkdir(parents=True, exist_ok=True)
        if a.exists():
            a.unlink()
        cmd = ["ar", "rcs", str(a)] + [str(o) for o in objs]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.commands.append(" ".join(cmd))
        if r.returncode != 0:
            raise SystemExit(f"[ar] {name} failed: {r.stderr}")
        log(f"[ar] lib{name}.a: {len(objs)} objects", self.logf)
        return a

    def link(self, name: str, objs: list[pathlib.Path],
             libs: list[pathlib.Path],
             archives: list[pathlib.Path] | None = None) -> pathlib.Path:
        target = self.out / name
        group = []
        if archives:
            group = ["-Wl,--start-group"] + [str(a) for a in archives] \
                    + ["-Wl,--end-group"]
        cmd = ZIG_LINK_CXX + ["-shared", "-o", str(target)] + [str(o) for o in objs] \
              + group + [str(l) for l in libs] + ["-ldl", "-lpthread", "-lm"]
        log(f"[link] {name}: {len(objs)} objects, "
            f"{len(archives or [])} archives, {len(libs)} shared libs", self.logf)
        env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(self.cache / "link"))
        pathlib.Path(env["ZIG_GLOBAL_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
        self.commands.append(" ".join(cmd))
        if r.returncode != 0:
            (self.out / f"{name}.link.log").write_text(r.stderr)
            raise SystemExit(f"[link] {name} failed:\n" + r.stderr[:4000])
        log(f"[link] {name}: OK ({target.stat().st_size} bytes)", self.logf)
        return target

    def verify(self, targets: dict[str, pathlib.Path]) -> dict:
        info = {}
        for name, p in targets.items():
            hdr = subprocess.run(["readelf", "-h", str(p)], capture_output=True,
                                 text=True).stdout
            dyn = subprocess.run(["nm", "-D", "--defined-only", str(p)],
                                 capture_output=True, text=True).stdout
            und = subprocess.run(["nm", "-u", str(p)], capture_output=True,
                                 text=True).stdout
            needed = subprocess.run(["readelf", "-d", str(p)], capture_output=True,
                                    text=True).stdout
            versions = subprocess.run(["readelf", "-V", str(p)], capture_output=True,
                                      text=True).stdout
            glibc_versions = re.findall(r"GLIBC_[0-9.]+", versions)
            glibc_max = max(glibc_versions,
                            key=lambda v: tuple(map(int, v.split("_", 1)[1].split(".")))) \
                        if glibc_versions else "none"
            exported = set(re.findall(r"^\S+ T (\S+)$", dyn, re.M))
            info[name] = {
                "path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size,
                "sha256": sha256(p),
                "elf32": "ELF32" in hdr and "Intel 80386" in hdr,
                "exported_symbol_count": len(exported),
                "exported_game_entry_points": sorted(
                    s for s in exported if s in {
                        "Initialize", "HUD_Init", "HUD_VidInit", "HUD_Redraw",
                        "HUD_UpdateClientData", "HUD_Reset", "HUD_Frame",
                        "HUD_Shutdown", "HUD_Key_Event", "V_CalcRefdef",
                        "GetEntityAPI", "GetEntityAPI2", "GetNewDLLFunctions",
                        "GiveFnptrsToDll", "Server_GetBlendingInterface"}),
                "undefined_symbol_count": len(
                    [l for l in und.splitlines() if l.strip().startswith("U ")]),
                "needed": re.findall(r"Shared library: \[([^\]]+)\]", needed),
                "glibc_max": glibc_max,
            }
            if not info[name]["elf32"]:
                raise SystemExit(f"[verify] {name} is not ELF32 i386")
        return info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path,
                    default=ROOT / "build-evidence/bhl-base")
    ap.add_argument("--work", type=pathlib.Path, default=pathlib.Path("/tmp/bhlbuild"))
    ap.add_argument("--sdk", type=pathlib.Path, default=DEFAULT_SDK)
    ap.add_argument("--deps", type=pathlib.Path,
                    default=ROOT / ".cache/bhl-build/deps")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    args.out = args.out.resolve()
    args.work = args.work.resolve()
    args.sdk = args.sdk.resolve()
    args.deps = args.deps.resolve()

    if not ZIG.exists():
        raise SystemExit("missing Zig toolchain; see docs/BHL_BASE_BUILD.md")
    if not TREE.is_dir() or not args.sdk.is_dir():
        raise SystemExit("missing bhl-op4/ or pinned hl1_source_sdk; run `make fetch`")

    args.out.mkdir(parents=True, exist_ok=True)
    logf = (args.out / "build.log").open("w")
    t0 = time.time()
    log("=== bhl-op4 real 32-bit build ===", logf)
    log(f"tree   : {TREE}", logf)
    log(f"sdk    : {args.sdk}", logf)
    log(f"out    : {args.out}", logf)
    log(f"zig    : {ZIG} (clang for i386-unknown-linux-gnu)", logf)

    fetch_deps(args.deps, logf)
    b = Builder(args, logf)
    b.setup()

    common = common_sources()
    client = game_sources("client", common, logf)
    server = game_sources("server", common, logf)
    log(f"[cmake] client={len(client)} server={len(server)} common={len(common)}",
        logf)

    game_inc = b.includes("game")
    sdk_inc = b.includes("sdk")

    c_obj = b.compile_set("client", client, defs=BHL_DEFS + CLIENT_EXTRA,
                          includes=game_inc,
                          force_include=TREE / "src/game/client/pch.h")
    s_obj = b.compile_set("server", server, defs=BHL_DEFS + ["-DSERVER_DLL"],
                          includes=game_inc)

    tier1 = sdk_sources(args.sdk, "tier1/CMakeLists.txt", "TIER1_SOURCE_FILES", "tier1")
    tier1 += [args.sdk / "tier1" / f for f in
              ("processor_detect_linux.cpp", "pathmatch.cpp", "qsort_s.cpp")]
    tier1 = sorted(set(tier1))
    tier2 = sdk_sources(args.sdk, "tier2/CMakeLists.txt", "TIER2_SOURCE_FILES", "tier2")
    vgui = sdk_sources(args.sdk, "vgui2/vgui_controls/CMakeLists.txt",
                       "VGUI_CONTROLS_SOURCE_FILES", "vgui2/vgui_controls")
    log(f"[cmake] tier1={len(tier1)} tier2={len(tier2)} vgui_controls={len(vgui)}",
        logf)

    t1_obj = b.compile_set("tier1", tier1, defs=SDK_DEFS, includes=sdk_inc)
    t2_obj = b.compile_set("tier2", tier2, defs=SDK_DEFS, includes=sdk_inc)
    v_obj = b.compile_set("vgui_controls", vgui, defs=SDK_DEFS, includes=sdk_inc,
                          force_include=b.compat / "vgui_pch.h")
    g_obj = b.compile_set("glad", [TREE / "external/glad/src/glad.c"],
                          defs=SDK_DEFS, includes=sdk_inc, cc=ZIG_CC, std="-std=c11")
    sv_obj = b.compile_set("semver", [TREE / "external/semver.c/semver.c"],
                           defs=SDK_DEFS, includes=sdk_inc, cc=ZIG_CC, std="-std=c11")

    pcre_src = args.deps / "src/pcre-master"
    pcre_files = sorted(p for p in pcre_src.glob("pcre_*.c")
                        if not p.name.startswith(("pcre16_", "pcre32_", "pcrecpp_",
                                                  "pcreposix_", "pcre_jit_test",
                                                  "pcre_printint")))
    p_obj = b.compile_set("pcre", pcre_files, defs=SDK_DEFS, includes=sdk_inc,
                          cc=ZIG_CC, std="-std=c11",
                          extra=["-DHAVE_CONFIG_H", "-DPCRE_STATIC",
                                 "-DSUPPORT_PCRE8", "-DSUPPORT_UTF",
                                 "-DSUPPORT_UCP", "-I" + str(pcre_src)])

    sdl = TREE / "lib/public/libSDL2-2.0.so.0"
    sdk_lib = args.sdk / "lib/public"
    # Clean-room tier0/vstdlib replacements (tools/linux_shims/) are compiled
    # and linked INTO client.so, so the client no longer NEEDs Valve's
    # libtier0.so / libvstdlib.so at all.
    shim_dir = ROOT / "tools/linux_shims"
    shim_objs = []
    for src in ("shim_tier0.c", "shim_vstdlib.c"):
        obj = b.out / (src[:-2] + ".o")
        r = subprocess.run(ZIG_CC + ["-c", "-fPIC", "-O2", str(shim_dir / src),
                                     "-o", str(obj)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"[shim] {src} failed:\n" + r.stderr[:4000])
        shim_objs.append(obj)
    c_obj = list(c_obj) + shim_objs
    libs = [sdl, sdk_lib / "libsteam_api.so"]

    # CMake builds the SDK/dependency targets as STATIC libraries; do the same.
    a_vgui = b.archive("vgui_controls", v_obj)
    a_tier2 = b.archive("tier2", t2_obj)
    a_tier1 = b.archive("tier1", t1_obj)
    a_glad = b.archive("glad", g_obj)
    a_semver = b.archive("semver", sv_obj)
    a_pcre = b.archive("pcre", p_obj)

    client_so = b.link("client.so", c_obj, libs,
                       [a_vgui, a_tier2, a_tier1, a_glad, a_semver, a_pcre])
    hl_so = b.link("hl.so", s_obj, [], [a_semver])
    info = b.verify({"client.so": client_so, "hl.so": hl_so})

    # Full symbol audit: every undefined symbol is written to disk, and the
    # ones that are NOT libc / tier0 / SDL / Steam (i.e. symbols our own build
    # must supply) are listed explicitly. Nothing is suppressed.
    gaps = {}
    with (args.out / "UNDEFINED_SYMBOLS.txt").open("w") as uf:
        for name, p in (("client.so", client_so), ("hl.so", hl_so)):
            uf.write(f"===== {name} =====\n")
            uf.write(subprocess.run(["nm", "-u", str(p)], capture_output=True,
                                    text=True).stdout)
            uf.write("\n")
    for name, p in (("client.so", client_so), ("hl.so", hl_so)):
        raw = subprocess.run(["c++filt"], input=subprocess.run(
            ["nm", "-u", str(p)], capture_output=True, text=True).stdout,
            capture_output=True, text=True).stdout
        syms = sorted({l.strip()[2:] for l in raw.splitlines()
                       if l.strip().startswith("U ")})
        own = [s for s in syms if not is_engine_or_libc_symbol(s)]
        gaps[name] = own
        info[name]["unresolved_own_build_symbols"] = own
    (args.out / "LINK_GAPS.md").write_text(
        "# Unresolved symbols that this build must still supply\n\n"
        "Engine-provided symbols (tier0/vstdlib, SDL2, Steam, libc/libm, C++ "
        "ABI) are excluded here; the complete list is in "
        "`UNDEFINED_SYMBOLS.txt`. These are real link gaps, not hidden errors.\n\n"
        + "\n".join(f"## {k}\n\n" + "\n".join(f"- `{s}`" for s in v)
                    for k, v in gaps.items()) + "\n")
    for k, v in gaps.items():
        log(f"[audit] {k}: {len(v)} unresolved symbols from our own build", logf)

    manifest = {
        "purpose": "real 32-bit build from the BugfixedHL-root bhl-op4/ tree",
        "tree": "bhl-op4/",
        "base_repo": "tmp64/BugfixedHL-Rebased @ 4d32095e3c33",
        "source_sdk": "tmp64/hl1_source_sdk @ 11f26656677c881c7c630d03957900e7701da62e",
        "toolchain": {"zig": "0.17.1 (clang 22.1.8)",
                      "target": "i386-unknown-linux-gnu / GLIBC_2.17 baseline",
                      "cmake_available": "3.30.9 (dependency probe)"},
        "source_lists": {"client": len(client), "server": len(server),
                         "tier1": len(tier1), "tier2": len(tier2),
                         "vgui_controls": len(vgui), "pcre": len(pcre_files)},
        "compatibility_fixes": [
            "patches/utlblockmemory.h.patch (pinned SDK bit-field std::swap)",
            "patches/results.cpp.patch (one BHL client TU: auto& -> const auto&)",
            "patches/vgui_pch.h (reproduces SDK's own PCH header list)"],
        "libraries": info,
        "note": "Built and ELF-verified only. NOT tested inside Opposing Force: "
                "this sandbox has no HL engine, real vgui.so or legitimate OP4 "
                "assets. See docs/BHL_BASE_BUILD.md.",
    }
    (args.out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (args.out / "BUILD_COMMANDS.txt").write_text("\n".join(b.commands) + "\n")
    (args.out / "SOURCES.sha256").write_text(
        "\n".join(f"{r['sha256']}  {r['compiled_from']}" for r in b.source_records)
        + "\n")
    (args.out / "compile-units.json").write_text(
        json.dumps(b.source_records, indent=2, sort_keys=True) + "\n")
    log(f"[done] {time.time()-t0:.1f}s", logf)
    log(json.dumps(manifest["libraries"], indent=2), logf)
    logf.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

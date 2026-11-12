#!/usr/bin/env python3
"""EXPERIMENT: cross-compile the OP4 BHL client for Windows (x86) with zig.

Inputs come from a finished Linux build (tools/build_linux_op4_bhl.sh):
  --log   the build log (contains the exact client compile commands)
  --tree  the generated Linux tree (<OUT>/tree/linux)
  --zig   python inside the zig venv (<OUT>/zigvenv/bin/python)
  --cache OP4 upstream checkout (.cache/upstreams/op4) for SDL2.lib
Writes everything under --out. Never fails the job; results are in summary.txt.

Known blocker: utils/vgui/lib/win32_vc16/vgui.lib is MSVC C++ ABI. Linking it
with mingw/zig objects is expected to fail (undefined vgui:: symbols).
"""
import argparse, concurrent.futures as cf, pathlib, re, shutil, subprocess, urllib.request

VGUI_URL = ("https://github.com/twhl-community/halflife-op4-updated/raw/"
            "5368be7f8eba14b05236c7c52ad5f6b11fd95e55/utils/vgui/lib/win32_vc16/vgui.lib")
DROP = {"-m32", "-march=i686", "-mfpmath=387", "-mno-sse", "-fPIC",
        "-DLINUX", "-D_LINUX", "-DPOSIX", "-D_POSIX", "-I/usr/include/malloc"}


def client_compile_cmds(log_path, cc_hint):
    lines = pathlib.Path(log_path).read_text(errors="replace").splitlines()
    starts = [i for i, l in enumerate(lines) if l.startswith("make") and "Makefile.hl_cdll" in l]
    ends = [i for i, l in enumerate(lines) if l.startswith("make") and "Makefile.hldll" in l]
    if not starts:
        raise SystemExit("no hl_cdll section in log")
    end = ends[0] if ends else len(lines)
    cmds = []
    for l in lines[starts[0]:end]:
        toks = l.split()
        if toks and toks[0].endswith("/cc32") and " -c " in l:
            cmds.append(l)
    return cmds


def convert(cmd, zig, out_obj, shim, stub):
    toks = cmd.split()[1:]  # drop cc32 path
    toks = [t for t in toks if t != "-m32"]
    res, k = [], 0
    while k < len(toks):
        t = toks[k]
        if t in DROP or t.startswith("-march"):
            k += 1
            continue
        if t == "-o":
            res += ["-o", out_obj]
            k += 2
            continue
        res.append(t)
        k += 1
    return zig + ["-target", "x86-windows-gnu", "-D_WIN32", "-DWIN32",
                  "-I" + stub, "-I" + shim] + res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--zig", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--stub", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    obj = out / "obj"
    shutil.rmtree(obj, ignore_errors=True)
    obj.mkdir(parents=True, exist_ok=True)
    shim = out / "shim"
    shim.mkdir(exist_ok=True)
    (shim / "Windows.h").write_text("#include <windows.h>\n")
    summary = []

    # Windows-only compile fix (in the generated tree, not in the repo):
    iface = pathlib.Path(a.tree) / ".." / "public" / "interface.cpp"
    if iface.exists():
        s = iface.read_text(encoding="latin1")
        iface.write_text(s.replace("return GetProcAddress(", "return (void*)GetProcAddress("), encoding="latin1")
        summary.append("patched public/interface.cpp (GetProcAddress cast)")

    cmds = client_compile_cmds(a.log, "cc32")
    summary.append(f"client compile commands: {len(cmds)}")
    zig = [a.zig, "-m", "ziglang", "c++"]
    jobs = [(i, convert(c, zig, str(obj / f"{i:03d}.o"), str(shim), a.stub)) for i, c in enumerate(cmds)]

    def run(job):
        i, cmd = job
        r = subprocess.run(cmd, cwd=a.tree, capture_output=True, text=True)
        return i, r.returncode, (r.stderr or "") + (r.stdout or "")

    fails = []
    with cf.ThreadPoolExecutor(8) as ex:
        for i, rc, text in ex.map(run, jobs):
            if rc != 0:
                fails.append((i, text))
    (out / "compile_errors.txt").write_text("\n\n".join(f"== cmd {i}\n{t}" for i, t in fails))
    summary.append(f"compile failures: {len(fails)} of {len(cmds)}")

    vgui = out / "vgui.lib"
    try:
        urllib.request.urlretrieve(VGUI_URL, vgui)
        summary.append(f"vgui.lib downloaded: {vgui.stat().st_size} bytes")
    except Exception as e:  # network may be blocked
        summary.append(f"vgui.lib download failed: {e}")
    sdl = pathlib.Path(a.cache) / "lib" / "public" / "SDL2.lib"
    libs = [str(vgui)] if vgui.exists() else []
    if sdl.exists():
        libs.append(str(sdl))
        summary.append("SDL2.lib found")
    else:
        summary.append("SDL2.lib missing")

    if not fails and libs:
        dll = out / "client.dll"
        r = subprocess.run(zig + ["-target", "x86-windows-gnu", "-shared", "-o", str(dll)]
                           + [str(p) for p in obj.glob("*.o")] + libs
                           + ["-luser32", "-lgdi32", "-lwinmm", "-ladvapi32", "-lws2_32"],
                           capture_output=True, text=True)
        (out / "link.log").write_text(r.stdout + r.stderr)
        undefined = len(re.findall(r"undefined symbol", r.stderr))
        summary.append(f"link rc={r.returncode} undefined_symbols={undefined}")
        if r.returncode == 0 and dll.exists():
            summary.append(f"client.dll size={dll.stat().st_size}")
    else:
        summary.append("link skipped (compile failures or missing libs)")
    (out / "summary.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    main()

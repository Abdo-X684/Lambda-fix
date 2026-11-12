#!/usr/bin/env bash
# Build the OP4-based BugfixedHL Linux client + server (ELF32 i386) on a Linux
# host. Uses Zig's clang as a cross compiler (x86-linux-gnu, glibc 2.17 floor),
# so it runs on x86_64 and aarch64 hosts alike. Windows MSVC DLLs are NOT built
# here; they need Visual Studio.
#
# Needs: python3 (venv), make, binutils (objcopy), bash, network access to
# api.github.com (OP4 tarball + vgui.so) and pypi.org (ziglang).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${OUT:-$ROOT/build/linux-op4}"
ZIG_VERSION="${ZIG_VERSION:-0.17.1}"
rm -rf "$OUT"
mkdir -p "$OUT"

for tool in python3 make objcopy; do
  command -v "$tool" >/dev/null || { echo "missing tool: $tool" >&2; exit 2; }
done

echo "== 1. fetch pinned OP4 upstream"
python3 -m merge.cli fetch

echo "== 2. generate OP4-based BHL tree (+ linux/vgui.so, SHA-checked)"
python3 tools/build_op4_bhl.py --out "$OUT/tree"

echo "== 3. Zig cross compiler (ziglang $ZIG_VERSION)"
python3 -m venv "$OUT/zigvenv"
"$OUT/zigvenv/bin/pip" install --quiet "ziglang==$ZIG_VERSION"
cat > "$OUT/cc32" <<WRAP
#!/bin/bash
args=()
for a in "\$@"; do [ "\$a" = "-m32" ] || args+=("\$a"); done
exec "$OUT/zigvenv/bin/python" -m ziglang c++ -target x86-linux-gnu.2.17 -I"$ROOT/tools/stubinc" "\${args[@]}"
WRAP
chmod +x "$OUT/cc32"

echo "== 4. compile and link client.so + hl.so"
L="$OUT/tree/linux"
mkdir -p "$L/release"
cp "$OUT/tree/linux/vgui.so" "$L/release/vgui.so"
chmod +x "$L/gendbg.sh"
cd "$L"
MKFLAGS=(COMPILER="$OUT/cc32" CPP_LIB="-ldl -lpthread"
  ARCH_CFLAGS="-march=i686 -mfpmath=387 -mno-sse -O3"
  SHLIBLDFLAGS="-shared -Wl,--no-undefined")
make -f Makefile hl_cdll "${MKFLAGS[@]}"
# hldll object subdirectories are not created by the makefile.
mkdir -p release/obj/hldll/{ctf,rope,weapons,pm_shared,game_shared,public,common}
make -f Makefile hl "${MKFLAGS[@]}"
cd "$ROOT"

echo "== 5. collect and verify outputs"
D="$OUT/dist"
mkdir -p "$D"
cp "$L/release/client.so" "$L/release/hl.so" "$L/release/vgui.so" "$D/"
cp "$OUT/tree/OP4_BHL_PROVENANCE.json" "$D/PROVENANCE.json"
python3 - "$D" <<'PY'
import hashlib, pathlib, re, struct, sys
d = pathlib.Path(sys.argv[1])
lines = []
for name in ("client.so", "hl.so", "vgui.so"):
    b = (d / name).read_bytes()
    assert b[:4] == b"\x7fELF" and b[4] == 1 and struct.unpack("<H", b[18:20])[0] == 3, f"{name}: not ELF32 i386"
    vers = [tuple(map(int, v.split(b"."))) for v in re.findall(rb"GLIBC_(\d+\.\d+)", b)]
    assert not vers or max(vers) <= (2, 17), f"{name}: glibc {max(vers)} > 2.17"
    lines.append(f"{hashlib.sha256(b).hexdigest()}  {name}")
(d / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
PY
echo "== DONE: $D (Linux ELF32 only; not runtime-tested)"

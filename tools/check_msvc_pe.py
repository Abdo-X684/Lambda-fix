"""Fail if the MSVC client DLL has Wine-hostile loader features.

GoldSrc/Wine loads client.dll with LoadLibrary. MSVC's thread-safe static
initialization emits TLS callbacks that the original BHL client.dll does not
have, and the Windows SDK's wsock32.lib can emit ordinal-only imports. Both
can make LoadLibrary fail before DllMain is reached.
"""
from __future__ import annotations

import struct
import sys

import pefile


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_msvc_pe.py <client.dll>")
    path = sys.argv[1]
    pe = pefile.PE(path)

    tls = getattr(pe, "DIRECTORY_ENTRY_TLS", None)
    if tls and tls.struct.AddressOfCallBacks:
        rva = tls.struct.AddressOfCallBacks - pe.OPTIONAL_HEADER.ImageBase
        first = struct.unpack_from("<I", pe.get_data(rva, 4))[0]
        if first:
            print(
                f"WARNING: MSVC TLS callbacks still present (first=0x{first:08x})",
                file=sys.stderr)
        else:
            print("MSVC TLS callbacks: none")

    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            if not imp.name:
                raise SystemExit(
                    f"ordinal-only import remains in {entry.dll.decode()}: "
                    f"{imp.ordinal}")

    print("MSVC PE OK: no TLS callbacks, no ordinal-only imports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

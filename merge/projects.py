"""Add the speedrun sources to the OP4 build files after the merge.

The OP4 SDK has two build systems: Visual Studio 2019 projects and the Linux
makefiles.  Both enumerate source files explicitly, so simply dropping new
``.cpp`` files into ``cl_dll/`` is not enough - they would never be compiled.
These helpers patch the lists in an idempotent, anchor-checked way.
"""

from __future__ import annotations

from pathlib import Path

# (build target, source path relative to the SDK root, object-dir variable)
CLIENT_SOURCES = (
    ("cl_dll/sr_hud_timer.cpp", "HL1_OBJ_DIR"),
    ("cl_dll/sr_hud_msg.cpp", "HL1_OBJ_DIR"),
    ("game_shared/sr_core.cpp", "GAME_SHARED_OBJ_DIR"),
)
SERVER_SOURCES = (
    ("dlls/sr_server.cpp", "HLDLL_OBJ_DIR"),
    ("game_shared/sr_core.cpp", "GAME_SHARED_OBJ_DIR"),
)

BUILD_FILES = (
    ("projects/vs2019/hl_cdll.vcxproj", "vcxproj", CLIENT_SOURCES),
    ("projects/vs2019/hldll.vcxproj", "vcxproj", SERVER_SOURCES),
    ("linux/Makefile.hl_cdll", "makefile", ("HL1_OBJS", CLIENT_SOURCES)),
    ("linux/Makefile.hldll", "makefile", ("HLDLL_OBJS", SERVER_SOURCES)),
)


class ProjectPatchError(RuntimeError):
    pass


def patch_vcxproj(text: str, sources: tuple[tuple[str, str], ...]) -> tuple[str, list[str]]:
    """Insert ``<ClCompile Include="..." />`` before the first existing entry."""
    needle = "<ClCompile Include="
    if needle not in text:
        raise ProjectPatchError("vcxproj has no <ClCompile> entries; build system changed")
    lines = text.splitlines(keepends=True)
    index = next((i for i, line in enumerate(lines) if needle in line), None)
    if index is None:
        raise ProjectPatchError("could not locate <ClCompile> insertion point")
    indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
    added: list[str] = []
    block: list[str] = []
    for rel, _objdir in sources:
        win_path = "..\\..\\" + rel.replace("/", "\\")
        if win_path in text:
            continue
        block.append(f'{indent}<ClCompile Include="{win_path}" />\n')
        added.append(rel)
    if not block:
        return text, []
    eol = "\r\n" if lines[index].endswith("\r\n") else "\n"
    block = [line.rstrip("\r\n") + eol for line in block]
    lines[index:index] = block
    return "".join(lines), added


def patch_makefile(
    text: str, obj_var: str, sources: tuple[tuple[str, str], ...]
) -> tuple[str, list[str]]:
    """Insert ``$(OBJ_DIR)/name.o \\`` lines right after ``OBJS = \\``."""
    needle = f"{obj_var} = \\\n"
    if needle not in text:
        raise ProjectPatchError(f"makefile has no '{obj_var} = \\' list")
    added: list[str] = []
    block: list[str] = []
    for rel, objdir in sources:
        name = Path(rel).stem
        entry = f"\t$({objdir})/{name}.o \\\n"
        if entry in text:
            continue
        block.append(entry)
        added.append(rel)
    if not block:
        return text, []
    return text.replace(needle, needle + "".join(block), 1), added


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="surrogateescape", newline="") as fh:
        return fh.read()


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
        fh.write(text)


def patch_tree(root: Path) -> list[dict[str, object]]:
    """Patch every build file that exists under ``root``. Returns a change log."""
    changes: list[dict[str, object]] = []
    for rel, kind, payload in BUILD_FILES:
        path = root / rel
        if not path.is_file():
            continue
        original = read_text(path)
        if kind == "vcxproj":
            new, added = patch_vcxproj(original, payload)  # type: ignore[arg-type]
        else:
            obj_var, sources = payload  # type: ignore[misc]
            new, added = patch_makefile(original, obj_var, sources)  # type: ignore[arg-type]
        if new != original:
            write_text(path, new)
        changes.append({"file": rel, "added": added, "changed": new != original})
    return changes

#!/usr/bin/env python3
"""Generate the OP4-BASED tree with BugfixedHL features merged in.

Base: the pinned, unmodified twhl-community/halflife-op4-updated SDK
(``.cache/upstreams/op4``). Nothing is rewritten: the tree is a copy of OP4
plus

  1. BugfixedHL's real systems via ``merge.bhl`` (speedometer, jumpspeed,
     strafeguide, ConVar/CvarSystem, bugfixedhl.cfg, sv_bhl_* server cvars);
  2. BugfixedHL's autojump and ducktap input logic (``input.cpp``), anchored
     into OP4's own input code;
  3. Visual Studio project fixes so MSVC can build the tree (toolset v143,
     no Steam post-build copy, server output ``opfor.dll``).

OP4 stays on its own VGUI1 menus. BHL's VGUI2 menus/options are NOT merged
(the user accepted VGUI1 with the same gameplay features).

Every change is an anchored, count-checked text edit listed in
``PROVENANCE.json`` so the result can be audited file by file.

Usage:
    python3 tools/build_op4_bhl.py --out build/op4bhl
    python3 tools/build_op4_bhl.py --check   # temp tree + verification only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge import bhl as bhl_merge  # noqa: E402

UPSTREAM = ROOT / ".cache/upstreams/op4"
UPSTREAMS_JSON = ROOT / "upstreams.json"

# Binary build dependencies that the source tarball deliberately omits.
# Pinned to the OP4 commit and verified by SHA-256 before use.
BINARY_DEPS = (
    ("utils/vgui/lib/win32_vc16/vgui.lib",
     "14a98470c100aa3f319d864523d239ecc48fb2a548ffe8c4c7f12a8ac8521182"),
    ("lib/public/SDL2.lib",
     "26cb03139b3c8d2bc8d0f6a8db839eba74c930be9ef52a42f9f2f46d043e267f"),
)

# ---------------------------------------------------------------------------
# Feature edits to OP4 files. (file, rule id, where, anchor, snippet)
#   where = "after" | "before" | "replace-block"
#   anchor must occur EXACTLY once in the file.
# ---------------------------------------------------------------------------
INPUT_DECLS = """\
kbutton_t in_ducktap; // BHL: +ducktap (merged by tools/build_op4_bhl.py)
// BHL cl_autojump / cl_autojump_priority, registered in KB_Init().
cvar_t* cl_autojump_cv = NULL;
cvar_t* cl_autojump_priority_cv = NULL;
int PM_GetOnGround();   // pm_shared.cpp (BHL accessor, added by this generator)
int PM_GetWaterLevel();
int PM_GetMoveType();
"""

INPUT_AUTOFUNCS = """\
// ---------------------------------------------------------------------
// BugfixedHL autojump / ducktap (BHL src/game/client/input.cpp,
// GPL-3.0-or-later). Logic copied; PM accessors come from OP4 pm_shared.
// ---------------------------------------------------------------------
namespace bhl_autofuncs
{
static bool CvarOn(cvar_t* c)
{
\treturn c != NULL && c->value != 0.0f;
}

static void HandleAutojump(struct usercmd_s* cmd)
{
\tstatic bool s_bJumpWasDownLastFrame = false;

\tbool inWater = PM_GetWaterLevel() > 1;
\tbool isWalking = PM_GetMoveType() == MOVETYPE_WALK;

\tif (CvarOn(cl_autojump_cv))
\t{
\t\tbool shouldReleaseJump = (!PM_GetOnGround() && !inWater && isWalking);

\t\t// Spam press/release when jumping still lands us on the ground, so +jump
\t\t// does not stay held (BHL comment, unchanged).
\t\tif (s_bJumpWasDownLastFrame && PM_GetOnGround() && !inWater && isWalking)
\t\t\tshouldReleaseJump = true;

\t\tif (shouldReleaseJump)
\t\t\tcmd->buttons &= ~IN_JUMP;
\t}

\ts_bJumpWasDownLastFrame = ((cmd->buttons & IN_JUMP) != 0);
}

static void HandleDucktap(struct usercmd_s* cmd)
{
\tstatic bool s_bDuckWasDownLastFrame = false;

\tbool inWater = PM_GetWaterLevel() > 1;
\tbool isWalking = PM_GetMoveType() == MOVETYPE_WALK;
\tbool duckIsPressed = (in_duck.state & 1) != 0;

\tbool shouldReleaseDuck = (!PM_GetOnGround() && !inWater && isWalking && !duckIsPressed);

\tif (s_bDuckWasDownLastFrame && PM_GetOnGround() && !inWater && isWalking)
\t\tshouldReleaseDuck = true;

\tif (shouldReleaseDuck)
\t{
\t\tcmd->buttons &= ~IN_DUCK;
\t\tin_duck.state &= 0;
\t}

\ts_bDuckWasDownLastFrame = ((cmd->buttons & IN_DUCK) != 0);
}
} // namespace bhl_autofuncs

"""

INPUT_CREATEMOVE = """\
\t// BHL autojump / ducktap (BugfixedHL input.cpp order, unchanged)
\tif (CvarOn_BHL(cl_autojump_priority_cv))
\t\tbhl_autofuncs::HandleAutojump(cmd);

\tif (in_ducktap.state & 1)
\t{
\t\tcmd->buttons |= IN_DUCK;
\t\tbhl_autofuncs::HandleDucktap(cmd); // Ducktap takes priority over autojump
\t}
\telse if (!CvarOn_BHL(cl_autojump_priority_cv))
\t{
\t\tbhl_autofuncs::HandleAutojump(cmd);
\t}
"""

INPUT_CVAR_HELPER = """\
// BHL: tiny helper used by CL_CreateMove (defined before first use).
static bool CvarOn_BHL(cvar_t* c)
{
\treturn c != NULL && c->value != 0.0f;
}

"""

INPUT_KB_REGISTER = """\
\t// BHL autojump cvars (BugfixedHL input.cpp). FCVAR_ARCHIVE persists them.
\tcl_autojump_cv = CVAR_CREATE("cl_autojump", "0", FCVAR_ARCHIVE);
\tcl_autojump_priority_cv = CVAR_CREATE("cl_autojump_priority", "0", FCVAR_ARCHIVE);
"""

INPUT_DUCKTAP_FUNCS = """\
void IN_DucktapDown() { KeyDown(&in_ducktap); } // BHL +ducktap
void IN_DucktapUp() { KeyUp(&in_ducktap); }     // BHL -ducktap
"""

PM_ACCESSORS = """\
// BHL accessors (merged by tools/build_op4_bhl.py) used by the client
// autojump/ducktap code. Read-only views of the last PM_Move state.
int PM_GetOnGround()
{
\treturn pmove ? (pmove->onground != -1) : 0;
}

int PM_GetWaterLevel()
{
\treturn pmove ? pmove->waterlevel : 0;
}

int PM_GetMoveType()
{
\treturn pmove ? pmove->movetype : 0;
}

"""

FEATURE_EDITS = (
    # client input.cpp: state, helpers, commands, reset, CL_CreateMove, cvars
    ("cl_dll/input.cpp", "bhl-input-decls", "after",
     "kbutton_t in_graph; // Display the netgraph\n", INPUT_DECLS),
    ("cl_dll/input.cpp", "bhl-input-ducktap-funcs", "after",
     "void IN_DuckUp() { KeyUp(&in_duck); }\n", INPUT_DUCKTAP_FUNCS),
    ("cl_dll/input.cpp", "bhl-input-cmds", "after",
     "\tgEngfuncs.pfnAddCommand(\"-jump\", IN_JumpUp);\n",
     "\tgEngfuncs.pfnAddCommand(\"+ducktap\", IN_DucktapDown); // BHL\n"
     "\tgEngfuncs.pfnAddCommand(\"-ducktap\", IN_DucktapUp);\n"),
    ("cl_dll/input.cpp", "bhl-input-kb-cvars", "after",
     "void KB_Init()\n{\n", INPUT_KB_REGISTER),
    ("cl_dll/input.cpp", "bhl-input-autofuncs", "before",
     "/*\n================\nCL_CreateMove\n", INPUT_CVAR_HELPER + INPUT_AUTOFUNCS),
    ("cl_dll/input.cpp", "bhl-input-createmove", "after",
     "\tcmd->buttons = CL_ButtonBits(true);\n", INPUT_CREATEMOVE),
    ("cl_dll/input.cpp", "bhl-input-reset-ducktap", "after",
     "\t\tin_jump.state &= ~2;\n", "\t\tin_ducktap.state &= ~2;\n"),
    # shared pm: read-only accessors
    ("pm_shared/pm_shared.cpp", "bhl-pm-accessors", "before",
     "void PM_Init(", PM_ACCESSORS),
)

# ---------------------------------------------------------------------------


class BuildError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_upstream() -> dict:
    if not (UPSTREAM / ".FETCHED.json").is_file():
        raise BuildError("OP4 upstream not fetched (run: python3 -m merge.cli fetch)")
    fetched = json.loads((UPSTREAM / ".FETCHED.json").read_text(encoding="utf-8"))
    pin = next(u for u in json.loads(UPSTREAMS_JSON.read_text(encoding="utf-8"))["upstreams"]
               if u["name"] == "op4")
    if fetched.get("ref") != pin["ref"] or fetched.get("sha256") != pin["tarball"]["sha256"]:
        raise BuildError("OP4 cache does not match the pin in upstreams.json")
    return fetched


def fetch_binary_deps(dest_root: Path, ref: str) -> list[dict]:
    rows = []
    for rel, want in BINARY_DEPS:
        dst = dest_root / rel
        if not (dst.is_file() and sha256(dst) == want):
            dst.parent.mkdir(parents=True, exist_ok=True)
            url = (f"https://api.github.com/repos/twhl-community/halflife-op4-updated/"
                   f"contents/{rel}?ref={ref}")
            req = urllib.request.Request(url, headers={
                "Accept": "application/vnd.github.raw",
                "User-Agent": "bhl-op4-build"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            if hashlib.sha256(data).hexdigest() != want:
                raise BuildError(f"binary dependency checksum mismatch: {rel}")
            dst.write_bytes(data)
        rows.append({"path": rel, "sha256": want, "origin": f"api.github.com contents @ {ref[:12]}"})
    return rows


def replace_once(text: str, where: str, anchor: str, snippet: str, label: str) -> str:
    count = text.count(anchor)
    if count != 1:
        raise BuildError(f"{label}: anchor found {count} times (need exactly 1): {anchor[:60]!r}")
    at = text.index(anchor)
    if where == "after":
        at += len(anchor)
        return text[:at] + snippet + text[at:]
    if where == "before":
        return text[:at] + snippet + text[at:]
    raise BuildError(f"{label}: unknown placement {where}")


def apply_features(tree: Path, log: list[dict]) -> None:
    for rel, rule, where, anchor, snippet in FEATURE_EDITS:
        path = tree / rel
        if not path.is_file():
            raise BuildError(f"feature target missing: {rel}")
        raw = path.read_bytes().decode("utf-8", errors="surrogateescape")
        eol = "\r\n" if "\r\n" in raw else "\n"
        text = raw.replace("\r\n", "\n")
        new = replace_once(text, where, anchor, snippet, rule)
        out_text = new.replace("\n", eol)
        path.write_bytes(out_text.encode("utf-8", errors="surrogateescape"))
        log.append({"file": rel, "rule": rule, "kind": "feature-edit"})


def patch_vs_projects(tree: Path, log: list[dict]) -> None:
    """Make the OP4 VS projects build on the windows-2022 runner."""
    proj_dir = tree / "projects/vs2019"
    for name, target in (("hl_cdll.vcxproj", None), ("hldll.vcxproj", "opfor")):
        path = proj_dir / name
        text = path.read_text(encoding="utf-8")
        if text.count("<PlatformToolset>v142</PlatformToolset>") != 2:
            raise BuildError(f"{name}: expected two v142 toolset entries")
        text = text.replace("<PlatformToolset>v142</PlatformToolset>",
                            "<PlatformToolset>v143</PlatformToolset>")
        text, n = re.subn(r"(?s)<Command>cmd /c .*?</Command>",
                          "<Command>echo Built " + name.replace('.vcxproj', '') + "</Command>", text)
        if n != 2:
            raise BuildError(f"{name}: expected two post-build blocks, found {n}")
        if target:
            if text.count("<TargetName>hl</TargetName>") != 2:
                raise BuildError(f"{name}: expected two hl target names")
            text = text.replace("<TargetName>hl</TargetName>",
                                f"<TargetName>{target}</TargetName>")
        path.write_text(text, encoding="utf-8")
        log.append({"file": f"projects/vs2019/{name}", "rule": "vs-toolset-v143-no-steam-copy",
                    "kind": "build-fix"})


def build_tree(out: Path) -> dict:
    fetched = check_upstream()
    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(UPSTREAM, out, ignore=shutil.ignore_patterns(".git", ".FETCHED.json"))

    log: list[dict] = []
    # 1. BugfixedHL systems (real files from integration/bhl, merged by merge.bhl).
    bhl_report = bhl_merge.merge_into(out)
    log.append({"file": "(merge.bhl)", "rule": "bhl-systems", "kind": "bhl-merge",
                "copied": bhl_report["copied_files"],
                "injections": bhl_report["injections_added"]})
    # 2. Autojump/ducktap + accessors.
    apply_features(out, log)
    # 3. VS project fixes.
    patch_vs_projects(out, log)
    # 4. Binary deps for MSVC linking.
    deps = fetch_binary_deps(out, fetched["ref"])

    # Provenance: every file classified by origin.
    prov_files = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        rel = path.relative_to(out).as_posix()
        if rel.startswith("BHL_MERGE_REPORT") or rel.endswith("MERGE_REPORT.md"):
            continue
        base = UPSTREAM / rel
        if base.is_file():
            origin = "op4-verbatim" if sha256(base) == sha256(path) else "op4-patched"
        elif rel.startswith(("cl_dll/bhl_", "cl_dll/base.", "cl_dll/speedometer.",
                             "cl_dll/jumpspeed.", "cl_dll/strafeguide.", "cl_dll/bhlcfg.",
                             "dlls/bhl_")):
            origin = "bhl-copied"
        else:
            origin = "generated-or-binary"
        prov_files.append({"path": rel, "origin": origin, "sha256": sha256(path)})

    provenance = {
        "kind": "op4-base-with-bhl-systems",
        "base": {"name": "op4", "repo": fetched["repo"], "ref": fetched["ref"],
                 "tarball_sha256": fetched["sha256"]},
        "bhl_source": "tmp64/BugfixedHL-Rebased @ 4d32095e3c33 (GPL-3.0-or-later)",
        "vgui": "VGUI1 (OP4 native). BHL VGUI2 menus/options not merged.",
        "edits": log,
        "binary_deps": deps,
        "counts": {k: sum(1 for f in prov_files if f["origin"] == k)
                   for k in ("op4-verbatim", "op4-patched", "bhl-copied", "generated-or-binary")},
        "files": prov_files,
        "in_game_tested_here": False,
    }
    (out / "OP4_BHL_PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return provenance


def verify(tree: Path) -> list[str]:
    errs: list[str] = []
    for rel in ("cl_dll/bhl_compat.cpp", "cl_dll/speedometer.cpp", "dlls/bhl_server.cpp"):
        if not (tree / rel).is_file():
            errs.append(f"missing {rel}")
    text = (tree / "cl_dll/input.cpp").read_bytes().decode("utf-8", errors="replace")
    for needle in ("bhl_autofuncs::HandleDucktap", "\"+ducktap\"", "cl_autojump_priority",
                   "in_ducktap.state &= ~2;"):
        if needle not in text:
            errs.append(f"input.cpp missing {needle!r}")
    pm = (tree / "pm_shared/pm_shared.cpp").read_bytes().decode("utf-8", errors="replace")
    if "int PM_GetOnGround()" not in pm:
        errs.append("pm_shared.cpp missing PM_GetOnGround")
    for rel in ("cl_dll/input.cpp", "pm_shared/pm_shared.cpp", "cl_dll/hud.h"):
        body = (tree / rel).read_bytes().decode("utf-8", errors="replace")
        if re.search(r"^(<{7} |>{7} |={7}\r?$)", body, re.M):
            errs.append(f"conflict marker in {rel}")
    for rel in ("projects/vs2019/hl_cdll.vcxproj", "projects/vs2019/hldll.vcxproj"):
        body = (tree / rel).read_text(encoding="utf-8")
        if "v142" in body or "cmd /c" in body:
            errs.append(f"{rel}: toolset/post-build not patched")
    if "<TargetName>opfor</TargetName>" not in (tree / "projects/vs2019/hldll.vcxproj").read_text(encoding="utf-8"):
        errs.append("hldll.vcxproj not renamed to opfor")
    for rel, want in BINARY_DEPS:
        p = tree / rel
        if not p.is_file() or sha256(p) != want:
            errs.append(f"binary dep missing or wrong: {rel}")
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", type=Path, default=ROOT / "build/op4bhl")
    ap.add_argument("--check", action="store_true",
                    help="build into a temp dir and verify only")
    args = ap.parse_args(argv)
    try:
        if args.check:
            with tempfile.TemporaryDirectory(prefix="op4bhl-") as td:
                tree = Path(td) / "tree"
                prov = build_tree(tree)
                errs = verify(tree)
        else:
            out = args.out if args.out.is_absolute() else ROOT / args.out
            prov = build_tree(out)
            errs = verify(out)
            print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    except BuildError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if errs:
        for e in errs:
            print("FAIL:", e, file=sys.stderr)
        return 1
    print(f"op4 base: {len(prov['files'])} files  counts={prov['counts']}")
    print(f"edits: {len(prov['edits'])}")
    print("== OP4-BASED BHL TREE OK (source only; not runtime-tested) ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

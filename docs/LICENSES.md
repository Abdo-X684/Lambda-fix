# Licenses and obligations

> **Note:** The tree `bhl-op4/` ([PROVENANCE.json](../bhl-op4/PROVENANCE.json)) contains
> **694 complete files from BugfixedHL-Rebased (GPL-3.0)**, tracked in Git, plus 154 files from
> OP4 and the Valve SDK. This is not "for review only" as in the earlier phase. Any distribution
> of this tree, or of any binary built from it, is subject to **GPL-3.0** in full, and to the
> Valve non-commercial license for the OP4 code. This document does not claim legal compliance.
> See [`BHL_BASE_MERGE.md`](BHL_BASE_MERGE.md).

* **This repository's code** (engine, C++ core, glue, panel, tests, docs): MIT.
  Commercial use is allowed within the limits of the source licenses below.
* **BugfixedHL-Rebased**: GPL-3.0. Files in `integration/ports/` are for review only;
  they are not compiled or linked. If you distribute a merged tree that contains code derived
  from it, follow GPL-3.0 (source, attribution, same license).
* **Valve HALF-LIFE SDK** and **halflife-op4-updated**: Valve license for non-commercial use
  in improvements to Valve products, with TWHL community fixes. Read the `LICENSE` in each
  repository before distributing anything.
* **Route data**: map and chapter names come from the SourceRuns Wiki. Rights to the names
  and marks belong to Valve and Gearbox.

The `dist/*.zip` package contains only our code and a `MANIFEST.json` with a sha256 for each file.
The generated tree in `build/` is not a standalone distributable: it combines licensed sources
that have separate licenses. Review those obligations before publishing any mod package.

This document is not legal advice.

`data/delta.lst` (in the mod folder) is copied from the OP4 SDK `network/` folder because
GoldSrc mods need it for client/server network data. It is SDK data, not kit code, and remains
under the SDK's terms.

## Update for bhl-systems-1: GPL code is now compiled into the binaries

Up to `0.1.x`, the files in `integration/ports/` were **uncompiled reference copies**.
Starting with `bhl-systems-1`, the real BugfixedHL systems are moved to `integration/bhl/`
and compiled into `client.so` / `hl.so` (see [`BHL_MERGE.md`](BHL_MERGE.md)).
Distributing these binaries means distributing work derived from code under **GPL-3.0-or-later**,
so it must follow those terms (corresponding source, notices, same license). The kit code
(`merge/`, `tools/`, `src/speedrun/`, `web/`) stays MIT and does not change this obligation.

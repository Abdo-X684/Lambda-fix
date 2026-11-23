# Licensing, copyright, and redistribution

Lambda Fix is a combined project. **There is no single license that covers every file in the repository, the merged source tree, or every generated binary.** The applicable terms depend on the origin of the code or asset.

This document is a practical project-level guide, not legal advice. Preserve the original license files, copyright notices, and attribution supplied by each upstream project.

## License summary

| Component | Applicable terms | Important note |
| --- | --- | --- |
| Original code authored for this repository | MIT — see [LICENSE](LICENSE) | The root MIT license does not relicense third-party or merged upstream code. |
| BugfixedHL-derived code | GPL-3.0 | The merged BugfixedHL code is part of the built game libraries; distribution must satisfy the GPL obligations that apply to the covered work. |
| Valve Half-Life SDK and Opposing Force SDK-derived code | Valve Half-Life 1 SDK License | The applicable terms restrict use and redistribution to the permitted non-commercial context. Commercial use requires permission from Valve. |
| TWHL community changes | Terms accompanying the upstream project | Retain and review the upstream notices and license files. |
| AG CTF sprites | Unconfirmed | The license has not been confirmed; do not assume these assets are cleared for redistribution. |
| Game content (models, sounds, maps, etc.) | Valve/Gearbox rights and applicable game terms | Commercial game assets are not included in the Lambda Fix package; users must provide their own legitimate installation. |

## Repository-authored code: MIT

The root [LICENSE](LICENSE) applies to original code authored for this repository, subject to the limits stated in that file.

It does **not** replace or override the licenses of upstream code incorporated into `bhl-op4/`, generated build outputs, or third-party assets. A file being present in this repository does not automatically make it MIT-licensed.

## BugfixedHL-derived code: GPL-3.0

The merged tree `bhl-op4/` contains substantial code from [BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased), which is licensed under GPL-3.0.

The BugfixedHL systems are compiled into the project libraries. Therefore, distributing the merged source tree or binaries derived from that code requires compliance with the applicable GPL-3.0 terms. This includes providing the corresponding source code and preserving required notices and license text, as applicable to the distribution.

Do not interpret the MIT license at the repository root as permission to distribute BugfixedHL-derived code under MIT.

## Valve Half-Life and Opposing Force SDK code

The project also incorporates code from the Valve Half-Life SDK and the Opposing Force source project, [halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated).

The Valve Half-Life 1 SDK license permits use and distribution only within its stated conditions, including the permitted non-commercial context of modifications for the Valve Half-Life engine. **Commercial use requires permission from Valve.**

The exact license files shipped by the upstream repositories govern their respective material. Review and preserve those files before copying, modifying, or redistributing the relevant code. TWHL community contributions may also carry attribution or other notices that must be retained.

## Third-party assets and game content

- **AG CTF sprites:** attributed to Adrenaline Gamer. The applicable license has not been confirmed. Treat redistribution rights as unresolved until the original license or explicit permission is obtained.
- **Half-Life and Opposing Force assets:** the project package does not include commercial game content such as original models, sounds, maps, or other game assets. The mod expects the user to supply these from a legitimate installation.
- **`data/delta.lst`:** this file is derived from the Opposing Force SDK network data and remains subject to the applicable SDK terms.
- **Route and chapter names:** project documentation references information from the SourceRuns Wiki. Valve and Gearbox retain rights to their respective names and marks.

## Redistribution checklist

Before publishing or sharing a source archive, binary, or mod package:

1. Identify which upstream components and assets are included in the specific distribution.
2. Include the applicable license texts, copyright notices, and required attributions.
3. For BugfixedHL-derived binaries or source, meet the applicable GPL-3.0 requirements, including access to the corresponding source.
4. Check the Valve SDK terms before distributing material derived from the Half-Life or Opposing Force SDKs. Do not use or distribute that material commercially without the required permission from Valve.
5. Do not redistribute AG CTF sprites until their license or permission has been confirmed.
6. Do not bundle Valve or Gearbox commercial game assets unless you have the rights to do so.

The obligations can differ between the repository's original code, the merged development tree, and a particular packaged build. Review the contents of the actual distribution rather than relying on the repository's root license alone.

## Upstream references

- [BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased) — GPL-3.0.
- [halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated) — Valve Half-Life 1 SDK terms and upstream community notices.
- [ValveSoftware/halflife](https://github.com/ValveSoftware/halflife) — Valve Half-Life SDK source and license.

Pinned revisions are listed in `upstreams.json`. The source and asset audit is generated by `tools/audit_op4_sources.py`.

---

If you are unsure whether a particular file or binary may be redistributed, do not assume that the root MIT license grants permission. Check the file's provenance and the relevant upstream license, and obtain legal advice where necessary.

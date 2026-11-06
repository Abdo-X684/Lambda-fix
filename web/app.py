#!/usr/bin/env python3
"""Live dashboard for the BugfixedHL x Opposing Force speedrun merge kit.

Standard library only. Binds 0.0.0.0 (Arena proxy friendly) and uses relative
API URLs, so it works behind the preview host without any CORS or host
allowlist configuration.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge.configgen import load_route, render_config, route_maps  # noqa: E402
from tools.package_mod import build as build_package  # noqa: E402
from web.markdown import DocumentStore  # noqa: E402

STATIC = {
    "/static/style.css": ("web/static/style.css", "text/css; charset=utf-8"),
    "/static/app.js": ("web/static/app.js", "application/javascript; charset=utf-8"),
}
DLL_DOWNLOADS = {
    "/dist/dlls/client.so": "client.so",
    "/dist/dlls/hl.so": "hl.so",
    "/dist/dlls/MANIFEST.json": "MANIFEST.json",
}
MOD_ZIP = ROOT / "dist" / "bhl-op4-mod.zip"


def _report_path(name: str) -> Path:
    return ROOT / "build" / name / "MERGE_REPORT.json"


def _read_report(name: str):
    path = _report_path(name)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def docs_store() -> DocumentStore:
    """Rebuilt per request so newly added docs show up without a restart."""
    return DocumentStore(ROOT)


def docs_payload() -> dict:
    return {"docs": docs_store().index()}


def doc_payload(name: str) -> dict | None:
    return docs_store().get(name)


def status_payload() -> dict:
    upstreams = json.loads((ROOT / "upstreams.json").read_text(encoding="utf-8"))["upstreams"]
    plan = json.loads((ROOT / "merge" / "plan.json").read_text(encoding="utf-8"))
    route = load_route(ROOT)
    report = _read_report("merged")
    return {
        "project": plan["name"],
        "version": "0.1.0",
        "upstreams": [
            {k: u[k] for k in ("name", "role", "repo", "ref", "license", "about")}
            for u in upstreams
        ],
        "rules": len(plan["rules"]),
        "route": {
            "chapters": len(route["chapters"]),
            "maps": len(route_maps(route)),
            "boot_camp": len(route["boot_camp"]["maps"]),
        },
        "sdk_cached": (ROOT / ".cache" / "upstreams" / "op4" / ".FETCHED.json").is_file(),
        "real_sdk_cached": (ROOT / "build" / "merged-real" / "MERGE_REPORT.json").is_file(),
        "package_ready": (ROOT / "dist" / "bhl-op4-speedrun-overlay.zip").is_file(),
        "dlls_ready": (ROOT / "dist" / "dlls" / "client.so").is_file(),
        "mod_zip_ready": MOD_ZIP.is_file(),
        "last_report": (
            {
                "mode": report["mode"],
                "tree_hash": report["tree_hash"],
                "summary": report["summary"],
                "started_at": report["started_at"],
            }
            if report
            else None
        ),
    }


def run_merge(mode: str) -> dict:
    if mode not in {"offline", "upstream"}:
        return {"ok": False, "error": f"unknown mode: {mode}"}
    out = "build/merged" if mode == "offline" else "build/merged-real"
    cmd = [sys.executable, "-m", "merge.cli", "run", "--out", out]
    if mode == "offline":
        cmd.append("--offline")
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "merge timed out (180s)"}
    report = _read_report("merged" if mode == "offline" else "merged-real")
    if proc.returncode != 0 or report is None:
        return {"ok": False, "error": (proc.stderr or proc.stdout or "merge failed").strip()[:2000]}
    return {"ok": True, "cli": proc.stdout.strip(), "report": report}


def run_tests() -> dict:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "tests timed out"}
    return {"ok": proc.returncode == 0, "output": (proc.stderr or proc.stdout)[-4000:]}


class Handler(BaseHTTPRequestHandler):
    server_version = "BHLxOP4/0.1"

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, code: int = 200) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _text(self, text: str, ctype: str = "text/plain; charset=utf-8", code: int = 200) -> None:
        self._send(code, text.encode("utf-8"), ctype)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)
        try:
            if path in ("/", "/index.html"):
                self._text((WEB / "index.html").read_text(encoding="utf-8"),
                           "text/html; charset=utf-8")
            elif path in STATIC:
                rel, ctype = STATIC[path]
                self._text((ROOT / rel).read_text(encoding="utf-8"), ctype)
            elif path == "/dist/bhl-op4-mod.zip":
                if not MOD_ZIP.is_file():
                    self._json({"error": "mod archive not built yet (make mod)"}, 404)
                else:
                    self._send(200, MOD_ZIP.read_bytes(), "application/zip")
            elif path in DLL_DOWNLOADS:
                dll = ROOT / "dist" / "dlls" / DLL_DOWNLOADS[path]
                if not dll.is_file():
                    self._json({"error": "binaries not built yet"}, 404)
                else:
                    ctype = "application/json; charset=utf-8" if dll.suffix == ".json" else "application/octet-stream"
                    self._send(200, dll.read_bytes(), ctype)
            elif path == "/dist/bhl-op4-speedrun-overlay.zip":
                zip_path = ROOT / "dist" / "bhl-op4-speedrun-overlay.zip"
                if not zip_path.is_file():
                    self._json({"error": "package not built yet"}, 404)
                else:
                    self._send(200, zip_path.read_bytes(), "application/zip")
            elif path == "/api/status":
                self._json(status_payload())
            elif path == "/api/route":
                self._json(load_route(ROOT))
            elif path == "/api/plan":
                self._json({
                    "upstreams": json.loads((ROOT / "upstreams.json").read_text()),
                    "plan": json.loads((ROOT / "merge" / "plan.json").read_text()),
                })
            elif path == "/api/config":
                self._text(render_config(ROOT))
            elif path == "/api/report":
                p = ROOT / "build" / "merged" / "MERGE_REPORT.md"
                self._text(p.read_text(encoding="utf-8") if p.is_file()
                           else "No report yet - run the merge first.")
            elif path == "/api/readme":
                self._text((ROOT / "README.md").read_text(encoding="utf-8"))
            elif path == "/api/docs":
                self._json(docs_payload())
            elif path == "/api/doc":
                name = query.get("name", ["README.md"])[0]
                payload = doc_payload(name)
                if payload is None:
                    self._json({"error": "unknown document", "name": name}, 404)
                elif query.get("raw", [""])[0] == "1":
                    self._send(200, payload["markdown"].encode("utf-8"),
                               "text/markdown; charset=utf-8")
                else:
                    self._json(payload)
            else:
                self._json({"error": "not found", "path": path}, 404)
        except (OSError, ValueError) as exc:
            self._json({"error": str(exc)}, 500)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            payload = {}
        if path == "/api/merge":
            self._json(run_merge(payload.get("mode", "offline")))
        elif path == "/api/package":
            try:
                self._json(build_package(ROOT))
            except (OSError, ValueError) as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
        elif path == "/api/tests":
            self._json(run_tests())
        else:
            self._json({"error": "not found", "path": path}, 404)

    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        sys.stdout.write(f"[{self.server_version}] {self.address_string()} - {fmt % args}\n")
        sys.stdout.flush()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"BHL x OP4 dashboard listening on 0.0.0.0:{port} (root={ROOT})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

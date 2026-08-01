#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
runtime = root / "services/brain-api/src/aion_brain/operator_console_runtime"
contract = root / "services/brain-api/src/aion_brain/contracts/operator_console_integration.py"
runtime_files = sorted(runtime.glob("*.py")) + [contract]
allowed_socket_file = runtime / "local_http.py"
forbidden_import_roots = {
    "aiohttp",
    "httpx",
    "importlib",
    "pathlib",
    "requests",
    "subprocess",
    "urllib.request",
}
forbidden_call_names = {
    "__import__",
    "eval",
    "exec",
    "open",
}
forbidden_socket_attrs = {
    "AF_INET6",
    "connect",
    "connect_ex",
    "create_connection",
    "getaddrinfo",
    "gethostbyaddr",
    "gethostbyname",
    "sendto",
}
for path in runtime_files:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                full_name = alias.name
                if full_name in forbidden_import_roots or root_name in forbidden_import_roots:
                    raise SystemExit(f"forbidden import in {path}: {alias.name}")
                if root_name == "socket" and path != allowed_socket_file:
                    raise SystemExit(f"socket import outside local_http.py: {path}")
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root_name = module.split(".", 1)[0]
            if module in forbidden_import_roots or root_name in forbidden_import_roots:
                raise SystemExit(f"forbidden import in {path}: {module}")
            if root_name == "socket" and path != allowed_socket_file:
                raise SystemExit(f"socket import outside local_http.py: {path}")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in forbidden_call_names:
                raise SystemExit(f"forbidden call in {path}: {func.id}")
            if isinstance(func, ast.Attribute):
                if func.attr in forbidden_socket_attrs:
                    raise SystemExit(f"forbidden socket call in {path}: {func.attr}")
                if func.attr in {"write_text", "write_bytes", "mkdir", "rename", "unlink"}:
                    raise SystemExit(f"filesystem mutation call in runtime source: {path}")
        if path == allowed_socket_file and isinstance(node, ast.Attribute):
            if node.attr == "AF_INET6":
                raise SystemExit("IPv6 address family is not authorized")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.lower()
            if path == allowed_socket_file and value in {"0.0.0.0", "::", "localhost"}:
                raise SystemExit(f"forbidden bind literal in local_http.py: {node.value}")
            if "apirouter(" in value or "create_app(" in value:
                raise SystemExit(f"production route marker in runtime source: {path}")

prohibited_paths = (
    "services/brain-api/src/aion_brain/operator_console_runtime/public_server.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/network_client.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/websocket.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/event_stream.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/cors.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/credential_store.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/token_store.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/cookie_store.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/browser_storage.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/file_upload.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/filesystem.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/process_runtime.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/background_worker.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/scheduler.py",
)
for item in prohibited_paths:
    if (root / item).exists():
        raise SystemExit(f"prohibited AION-237 source surface exists: {item}")
PY

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import re
from pathlib import Path

root = Path.cwd()
live = (root / "operator-console-static/live-console.js").read_text(encoding="utf-8")
app = (root / "operator-console-static/app.js").read_text(encoding="utf-8")
html = (root / "operator-console-static/index.html").read_text(encoding="utf-8")
combined = "\n".join([live, app, html])
for marker in (
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "document.cookie",
    "serviceWorker",
    "WebSocket",
    "EventSource",
    "eval(",
    "new Function",
    "credentials: \"include\"",
    "credentials: 'include'",
):
    if marker in combined:
        raise SystemExit(f"forbidden browser runtime marker: {marker}")
if re.search(r"(?<!127\\.0\\.0\\.1:)https?://", live):
    raise SystemExit("external URL found in live-console.js")
if re.search(r"(^|[^:])//[A-Za-z0-9_.-]+", live):
    raise SystemExit("protocol-relative URL found in live-console.js")
if "import(" in live:
    raise SystemExit("dynamic import found in live-console.js")
if 'path.indexOf("/aion/local/v1/") !== 0' not in live:
    raise SystemExit("live-console.js local route guard missing")
for match in re.finditer(r"fetch\(([^,\n]+)", live):
    target = match.group(1).strip().strip("\"'")
    if target != "path" and not target.startswith("/aion/local/v1/"):
        raise SystemExit(f"live fetch target is not same-origin local API: {target}")
if "/aion/local/v1/" in app:
    raise SystemExit("AION-237 local runtime routes must stay in live-console.js")
if re.search(r"method:\\s*[\"']POST[\"']", app):
    raise SystemExit("automatic POST marker found outside live-console.js")
PY

echo "controlled operator console integration no-go PASS"

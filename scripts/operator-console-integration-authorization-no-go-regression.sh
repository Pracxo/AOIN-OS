#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import os
import subprocess
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
authorized_source = {
    "services/brain-api/src/aion_brain/contracts/operator_console_integration.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/__init__.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/authorization.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/component_binding.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/origin_policy.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/request_nonce.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/session_bridge.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/request_router.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/view_models.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/local_http.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/audit.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/observability.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/integrity.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/evidence.py",
}
authorized_static = {
    "operator-console-static/index.html",
    "operator-console-static/app.js",
    "operator-console-static/styles.css",
    "operator-console-static/README.md",
    "operator-console-static/live-console.js",
}
authorized_scripts = {
    "scripts/operator-console-integrated-local-run.py",
    "scripts/operator-console-integration-check.sh",
    "scripts/operator-console-integration-no-go-regression.sh",
    "scripts/operator-console-integrated-pilot-evidence-check.sh",
    "scripts/operator-console-static-check.sh",
}
package_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
}
status = subprocess.run(
    ["git", "status", "--porcelain=v1", "--untracked-files=all"],
    cwd=root,
    text=True,
    capture_output=True,
    check=True,
).stdout.splitlines()
for line in status:
    path = line[3:].replace("\\", "/")
    if Path(path).name in package_names:
        raise SystemExit(f"package/dependency file changed: {path}")
    if path.startswith(".github/workflows/") or "migrations/" in path:
        raise SystemExit(f"workflow or migration changed: {path}")
    if path.startswith("services/brain-api/src/aion_brain/"):
        if path not in authorized_source:
            raise SystemExit(f"unauthorized runtime source changed: {path}")
    if path.startswith("operator-console-static/") and not (
        path in authorized_static or path.startswith("operator-console-static/demo-data/")
    ):
        raise SystemExit(f"unauthorized static console change: {path}")
    if path.startswith("scripts/operator-console") and path not in authorized_scripts and not path.endswith("authorization-check.sh") and not path.endswith("authorization-no-go-regression.sh") and not path.endswith("integration-runtime-hold.sh"):
        raise SystemExit(f"unauthorized operator console script change: {path}")
PY

if rg -n "<input[^>]+type=[\"']password|localStorage\.setItem|sessionStorage\.setItem|indexedDB|serviceWorker|WebSocket|Access-Control-Allow-Origin:[[:space:]]*\*|/aion/local/v1/.*register|create_app\(|APIRouter\(" \
  operator-console-static/index.html operator-console-static/app.js operator-console-static/live-console.js \
  scripts/operator-console-integration-authorization-check.sh \
  scripts/operator-console-integration-runtime-hold.sh; then
  echo "ERROR: prohibited Operator Console runtime behavior detected" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "controlled operator console integration authorization no-go PASS"

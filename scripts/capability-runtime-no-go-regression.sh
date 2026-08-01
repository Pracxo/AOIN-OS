#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])

SOURCE_SCOPE = {
    "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/__init__.py",
    "services/brain-api/src/aion_brain/capability_runtime/authorization.py",
    "services/brain-api/src/aion_brain/capability_runtime/component_binding.py",
    "services/brain-api/src/aion_brain/capability_runtime/manifests.py",
    "services/brain-api/src/aion_brain/capability_runtime/request_envelope.py",
    "services/brain-api/src/aion_brain/capability_runtime/input_validation.py",
    "services/brain-api/src/aion_brain/capability_runtime/execution_plan.py",
    "services/brain-api/src/aion_brain/capability_runtime/sandbox.py",
    "services/brain-api/src/aion_brain/capability_runtime/guard.py",
    "services/brain-api/src/aion_brain/capability_runtime/dispatcher.py",
    "services/brain-api/src/aion_brain/capability_runtime/reference_capabilities.py",
    "services/brain-api/src/aion_brain/capability_runtime/reference_connector.py",
    "services/brain-api/src/aion_brain/capability_runtime/budget.py",
    "services/brain-api/src/aion_brain/capability_runtime/audit.py",
    "services/brain-api/src/aion_brain/capability_runtime/observability.py",
    "services/brain-api/src/aion_brain/capability_runtime/integrity.py",
    "services/brain-api/src/aion_brain/capability_runtime/evidence.py",
}
AION237_SOURCE_SCOPE = {
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
PROHIBITED_SOURCE = {
    "services/brain-api/src/aion_brain/capability_runtime/network.py",
    "services/brain-api/src/aion_brain/capability_runtime/live_connector.py",
    "services/brain-api/src/aion_brain/capability_runtime/tool_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/shell_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/process_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/browser_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/filesystem.py",
    "services/brain-api/src/aion_brain/capability_runtime/module_loader.py",
    "services/brain-api/src/aion_brain/capability_runtime/credential_store.py",
    "services/brain-api/src/aion_brain/capability_runtime/token_store.py",
    "services/brain-api/src/aion_brain/capability_runtime/background_worker.py",
    "services/brain-api/src/aion_brain/capability_runtime/scheduler.py",
    "services/brain-api/src/aion_brain/api/capability_runtime.py",
}
PROHIBITED_IMPORT_ROOTS = {
    "aiohttp",
    "httpx",
    "importlib",
    "os",
    "pathlib",
    "playwright",
    "requests",
    "selenium",
    "shutil",
    "socket",
    "ssl",
    "subprocess",
    "tempfile",
    "urllib",
}
PROHIBITED_CALLS = {"open", "eval", "exec", "__import__"}
PROHIBITED_NAMES = {
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
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    if os.environ.get("GITHUB_BASE_REF"):
        candidates.extend([f"origin/{os.environ['GITHUB_BASE_REF']}", os.environ["GITHUB_BASE_REF"]])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge.returncode == 0 and merge.stdout.strip():
                return merge.stdout.strip()
    if ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []
    base = comparison_base()
    if base is not None:
        entries.extend(
            line.split("\t")
            for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines()
            if line.strip()
        )
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


def aion237_source_allowed() -> bool:
    ledger = ROOT / "docs/secure-runtime-integration/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    return (
        payload.get("operator_console_integration_implemented") is True
        and payload.get("integrated_authenticated_local_pilot_completed") is True
        and payload.get("active_sri_implementation_authorization") == "AION-236-SRI-0004"
        and payload.get("formal_closeout_task") == "AION-238"
    )


aion237_allowed = aion237_source_allowed()
for path in SOURCE_SCOPE:
    if not (ROOT / path).is_file():
        raise SystemExit(f"missing AION-235 runtime source: {path}")
for path in PROHIBITED_SOURCE:
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited runtime source exists: {path}")

for parts in changed_entries():
    if parts[0].startswith(("D", "R")):
        raise SystemExit(f"source deletion or rename is not authorized: {parts}")
    for raw_path in parts[1:]:
        path = raw_path.replace("\\", "/")
        if Path(path).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {path}")
        if path.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited release path changed: {path}")
        if path.startswith("services/brain-api/src/aion_brain/"):
            if path not in SOURCE_SCOPE and not (aion237_allowed and path in AION237_SOURCE_SCOPE):
                raise SystemExit(f"source change outside AION-235 scope: {path}")
        if path == "scripts/capability-runtime-local-sandbox-run.py":
            continue

for relative in sorted(SOURCE_SCOPE):
    tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in PROHIBITED_IMPORT_ROOTS:
                    raise SystemExit(f"prohibited import in {relative}: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".", 1)[0]
            if module in PROHIBITED_IMPORT_ROOTS:
                raise SystemExit(f"prohibited import in {relative}: {node.module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in PROHIBITED_CALLS:
                raise SystemExit(f"prohibited call in {relative}: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in PROHIBITED_CALLS:
                raise SystemExit(f"prohibited call in {relative}: {node.func.attr}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "sandboxed capability runtime no-go PASS"

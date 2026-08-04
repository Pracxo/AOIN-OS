#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
import os
import tomllib
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AION248_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/__init__.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/authorization.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/component_binding.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/provider_selection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/operator_approval.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/credential_boundary.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/endpoint_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/request_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/response_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/usage_budget.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/retention_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/transport.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/openai_responses_adapter.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/trust.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/redaction.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/replay.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/audit.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/observability.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/integrity.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/evidence.py",
}
RUNNER = "scripts/live-provider-pilot-local-run.py"
PROHIBITED_FILES = {
    "services/brain-api/src/aion_brain/live_provider_pilot/provider_tools.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/web_search.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/file_search.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/code_interpreter.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/computer_use.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/credential_store.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/token_store.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/background_worker.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/scheduler.py",
    "services/brain-api/src/aion_brain/api/live_provider_pilot.py",
}
DISALLOWED_INSTALLED_IMPORT_ROOTS = {
    "aiohttp",
    "http",
    "httpx",
    "openai",
    "os",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
}
DISALLOWED_INSTALLED_CALLS = {"eval", "exec", "__import__", "compile", "open"}
DISALLOWED_RUNNER_IMPORT_ROOTS = {"aiohttp", "httpx", "openai", "requests"}
RUNNER_REQUIRED_IMPORTS = {"http.client", "socket", "ssl"}
RUNNER_FORBIDDEN_ARGS = {
    "--api-key",
    "--credential-file",
    "--token",
    "--endpoint",
    "--host",
    "--path",
    "--proxy",
    "--provider",
    "--tools",
    "--files",
    "--previous-response-id",
}

for path in sorted(AION248_SOURCE):
    if not (ROOT / path).is_file():
        raise SystemExit(f"required AION-248 source missing: {path}")
for path in sorted(PROHIBITED_FILES):
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited AION-248 runtime source exists: {path}")
if not (ROOT / RUNNER).is_file():
    raise SystemExit("AION-248 uninstalled runner missing")

for path in sorted(AION248_SOURCE):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in DISALLOWED_INSTALLED_IMPORT_ROOTS:
                    raise SystemExit(f"disallowed installed import in {path}: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            if root in DISALLOWED_INSTALLED_IMPORT_ROOTS:
                raise SystemExit(f"disallowed installed import in {path}: {module}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in DISALLOWED_INSTALLED_CALLS:
                raise SystemExit(f"disallowed installed call in {path}: {func.id}")
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "os"
            ):
                raise SystemExit(f"installed package cannot access environment: {path}")

runner_tree = ast.parse((ROOT / RUNNER).read_text(encoding="utf-8"), filename=RUNNER)
runner_imports: set[str] = set()
runner_text = (ROOT / RUNNER).read_text(encoding="utf-8")
contract_text = (
    ROOT / "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py"
).read_text(encoding="utf-8")
for forbidden in RUNNER_FORBIDDEN_ARGS:
    if forbidden in runner_text:
        raise SystemExit(f"runner accepts prohibited argument: {forbidden}")
for node in ast.walk(runner_tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            runner_imports.add(alias.name)
            root = alias.name.split(".", 1)[0]
            if root in DISALLOWED_RUNNER_IMPORT_ROOTS:
                raise SystemExit(f"disallowed runner import: {alias.name}")
    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        runner_imports.add(module)
        root = module.split(".", 1)[0]
        if root in DISALLOWED_RUNNER_IMPORT_ROOTS:
            raise SystemExit(f"disallowed runner import: {module}")
if not RUNNER_REQUIRED_IMPORTS.issubset(runner_imports):
    raise SystemExit("runner must use standard-library HTTPS/DNS/TLS imports")
if "OPENAI_API_KEY" not in runner_text:
    raise SystemExit("runner must read only OPENAI_API_KEY at live execution time")
for required in ("api.openai.com", "/v1/responses", "gpt-5.6-terra"):
    if required not in runner_text and required not in contract_text:
        raise SystemExit(f"runner missing exact policy value: {required}")

pyproject = tomllib.loads((ROOT / "services/brain-api/pyproject.toml").read_text())
dependencies = "\n".join(pyproject["project"]["dependencies"])
if "openai" in dependencies.lower() or "requests" in dependencies.lower() or "aiohttp" in dependencies.lower():
    raise SystemExit("provider/request dependency added to Brain API")

print("single OpenAI live provider pilot no-go PASS")
PY

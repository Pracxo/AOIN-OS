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

import ast
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AION235_SOURCE_ALLOWED_STATES = {
    "sandboxed_capability_runtime_implemented_reference_only_pending_closeout": (
        "AION-234-SRI-0003",
        "AION-235",
        "AION-236",
    ),
    "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented": (
        "AION-236-SRI-0004",
        "AION-237",
        "AION-238",
    ),
}

AION233_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/model_gateway.py",
    "services/brain-api/src/aion_brain/model_gateway/__init__.py",
    "services/brain-api/src/aion_brain/model_gateway/authorization.py",
    "services/brain-api/src/aion_brain/model_gateway/manifests.py",
    "services/brain-api/src/aion_brain/model_gateway/request_envelope.py",
    "services/brain-api/src/aion_brain/model_gateway/context_budget.py",
    "services/brain-api/src/aion_brain/model_gateway/routing.py",
    "services/brain-api/src/aion_brain/model_gateway/circuit_breaker.py",
    "services/brain-api/src/aion_brain/model_gateway/guard.py",
    "services/brain-api/src/aion_brain/model_gateway/response_validation.py",
    "services/brain-api/src/aion_brain/model_gateway/provider_registry.py",
    "services/brain-api/src/aion_brain/model_gateway/provider_adapter.py",
    "services/brain-api/src/aion_brain/model_gateway/reference_provider.py",
    "services/brain-api/src/aion_brain/model_gateway/audit.py",
    "services/brain-api/src/aion_brain/model_gateway/observability.py",
    "services/brain-api/src/aion_brain/model_gateway/integrity.py",
    "services/brain-api/src/aion_brain/model_gateway/evidence.py",
}
AION235_SOURCE_EXACT = {
    "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py",
}
AION235_SOURCE_PREFIXES = ("services/brain-api/src/aion_brain/capability_runtime/",)
RUNNER = "scripts/model-gateway-local-simulation-run.py"
ALLOWED_PREFIXES = (
    "docs/",
    "examples/",
    "operator-console-static/",
    "scripts/",
    "services/brain-api/tests/",
)
ALLOWED_EXACT = {"README.md", "AGENTS.md", RUNNER}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "packages/aion-sdk-python/",
)
PROHIBITED_RUNTIME_PREFIXES = (
    "services/brain-api/src/aion_brain/secure_runtime/",
    "services/brain-api/src/aion_brain/production_auth/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/tools/",
)
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
PROHIBITED_MODEL_GATEWAY_FILES = {
    "services/brain-api/src/aion_brain/model_gateway/network.py",
    "services/brain-api/src/aion_brain/model_gateway/live_provider.py",
    "services/brain-api/src/aion_brain/model_gateway/openai.py",
    "services/brain-api/src/aion_brain/model_gateway/anthropic.py",
    "services/brain-api/src/aion_brain/model_gateway/google.py",
    "services/brain-api/src/aion_brain/model_gateway/credential_store.py",
    "services/brain-api/src/aion_brain/model_gateway/token_store.py",
    "services/brain-api/src/aion_brain/model_gateway/tool_runtime.py",
    "services/brain-api/src/aion_brain/model_gateway/connector_runtime.py",
    "services/brain-api/src/aion_brain/model_gateway/background_worker.py",
    "services/brain-api/src/aion_brain/model_gateway/scheduler.py",
    "services/brain-api/src/aion_brain/api/model_gateway.py",
}
DISALLOWED_IMPORT_ROOTS = {
    "aiohttp",
    "anthropic",
    "boto3",
    "botocore",
    "httpx",
    "importlib",
    "openai",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
    "vertexai",
}
DISALLOWED_IMPORT_PREFIXES = ("google.generativeai",)
DISALLOWED_CALLS = {"eval", "exec", "__import__", "compile"}


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        candidates.extend([f"origin/{github_base}", github_base])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if not ref_exists(candidate):
            continue
        merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None


def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []
    base = comparison_base()
    if base:
        entries.extend(
            line.split("\t")
            for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines()
            if line.strip()
        )
    else:
        print("WARN: comparison base unavailable; relying on working tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


def aion235_implementation_state_active() -> bool:
    ledger = ROOT / "docs/secure-runtime-integration/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    expected = AION235_SOURCE_ALLOWED_STATES.get(payload.get("program_state"))
    return (
        expected is not None
        and payload.get("active_sri_implementation_authorization") == expected[0]
        and payload.get("active_sri_implementation_task") == expected[1]
        and payload.get("formal_closeout_task") == expected[2]
        and payload.get("sandboxed_capability_runtime_implemented") is True
    )


def aion235_source_allowed(path: str) -> bool:
    if not aion235_active:
        return False
    return path in AION235_SOURCE_EXACT or path.startswith(AION235_SOURCE_PREFIXES)


def allowed(path: str) -> bool:
    return (
        path in AION233_SOURCE
        or aion235_source_allowed(path)
        or path in ALLOWED_EXACT
        or path.startswith(ALLOWED_PREFIXES)
    )


aion235_active = aion235_implementation_state_active()
changed_paths: set[str] = set()
for parts in changed_entries():
    status = parts[0]
    if status.startswith(("D", "R")):
        raise SystemExit(f"source deletion or rename is not authorized: {parts}")
    for raw_path in parts[1:]:
        path = raw_path.replace("\\", "/")
        changed_paths.add(path)
        if Path(path).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {path}")
        if path.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited path changed: {path}")
        if path.startswith(PROHIBITED_RUNTIME_PREFIXES) and path not in AION233_SOURCE:
            raise SystemExit(f"protected runtime source changed: {path}")
        if (
            path.startswith("services/brain-api/src/aion_brain/")
            and path not in AION233_SOURCE
            and not aion235_source_allowed(path)
        ):
            raise SystemExit(f"only exact AION-233 model-gateway source may change: {path}")
        if not allowed(path):
            raise SystemExit(f"disallowed AION-233 changed path: {path}")

for path in PROHIBITED_MODEL_GATEWAY_FILES:
    if path in changed_paths:
        raise SystemExit(f"prohibited model-gateway runtime surface changed: {path}")

for path in sorted(AION233_SOURCE | {RUNNER}):
    target = ROOT / path
    if not target.exists():
        raise SystemExit(f"required AION-233 file missing: {path}")
    tree = ast.parse(target.read_text(encoding="utf-8"), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                root = name.split(".", 1)[0]
                if root in DISALLOWED_IMPORT_ROOTS or name.startswith(DISALLOWED_IMPORT_PREFIXES):
                    raise SystemExit(f"disallowed import in {path}: {name}")
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            root = name.split(".", 1)[0]
            if root in DISALLOWED_IMPORT_ROOTS or name.startswith(DISALLOWED_IMPORT_PREFIXES):
                raise SystemExit(f"disallowed import in {path}: {name}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in DISALLOWED_CALLS:
                raise SystemExit(f"disallowed dynamic execution call in {path}: {func.id}")
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "environ":
                raise SystemExit(f"os.environ credential access is not authorized: {path}")

program = json.loads((ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/secure-runtime-integration/authorization-ledger.json").read_text())
for payload in (program, auth):
    if payload["model_gateway_implemented"] is not True:
        raise SystemExit("model gateway must be implemented")
    if payload["model_gateway_state"] not in {
        "implemented_provider_neutral_reference_simulation_only_pending_AION-234_closeout",
        "implemented_provider_neutral_reference_simulation_only",
    }:
        raise SystemExit("model gateway state mismatch")
    for key in (
        "actual_model_provider_call_enabled",
        "provider_network_egress_enabled",
        "public_network_access_enabled",
        "general_network_access_enabled",
        "provider_sdk_enabled",
        "provider_endpoint_connection_enabled",
        "provider_streaming_connection_enabled",
        "provider_credential_read_enabled",
        "provider_credential_persistence_enabled",
        "api_key_persistence_enabled",
        "token_persistence_enabled",
        "authorization_header_creation_enabled",
        "live_model_session_enabled",
        "automatic_model_routing_execution_enabled",
        "automatic_fallback_execution_enabled",
        "automatic_retry_execution_enabled",
        "tool_calling_enabled",
        "function_calling_enabled",
        "connector_execution_enabled",
        "actual_tool_execution_enabled",
        "shell_command_execution_enabled",
        "subprocess_execution_enabled",
        "browser_automation_enabled",
        "module_activation_enabled",
        "module_code_loading_enabled",
        "package_installation_enabled",
        "dynamic_route_registration_enabled",
        "public_model_api_route_enabled",
        "prompt_persistence_enabled",
        "model_response_persistence_enabled",
        "hidden_reasoning_retention_enabled",
        "provider_raw_payload_retention_enabled",
        "cross_session_context_retention_enabled",
        "automatic_memory_write_enabled",
        "production_memory_write_enabled",
        "production_policy_mutation_enabled",
        "cognitive_memory_write_enabled",
        "actual_belief_creation_enabled",
        "actual_belief_mutation_enabled",
        "glm_live_execution_enabled",
        "source_rewrite_enabled",
        "git_mutation_enabled",
        "runtime_pull_request_creation_enabled",
        "automatic_merge_enabled",
        "production_canary_enabled",
        "production_deployment_enabled",
        "model_weight_training_enabled",
        "production_runtime_authorized",
        "production_exposure",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(key) is not False:
            raise SystemExit(f"no-go flag must remain false: {key}")
    limits = payload["model_gateway_resource_limits"]
    for key, value in limits.items():
        if key.startswith("maximum_") and (
            key
            in {
                "maximum_public_network_calls",
                "maximum_model_provider_calls",
                "maximum_provider_sdk_calls",
                "maximum_provider_endpoint_connections",
                "maximum_provider_stream_connections",
                "maximum_provider_credentials_read",
                "maximum_provider_credentials_persisted",
                "maximum_api_keys_persisted",
                "maximum_tokens_persisted",
                "maximum_authorization_headers_created",
                "maximum_live_model_sessions",
                "maximum_tool_calls",
                "maximum_function_calls",
                "maximum_connector_calls",
                "maximum_actual_tool_executions",
                "maximum_shell_commands",
                "maximum_subprocess_executions",
                "maximum_browser_actions",
                "maximum_modules_activated",
                "maximum_packages_installed",
                "maximum_dynamic_routes_registered",
                "maximum_public_api_routes_added",
                "maximum_prompts_persisted",
                "maximum_model_responses_persisted",
                "maximum_hidden_reasoning_records",
                "maximum_provider_raw_payloads_retained",
                "maximum_cross_session_context_records",
                "maximum_automatic_memory_writes",
                "maximum_production_memory_writes",
                "maximum_production_policy_mutations",
                "maximum_cognitive_memory_writes",
                "maximum_actual_belief_creations",
                "maximum_actual_belief_mutations",
                "maximum_glm_live_executions",
                "maximum_source_mutations",
                "maximum_git_operations",
                "maximum_runtime_created_pull_requests",
                "maximum_automatic_merges",
                "maximum_production_canary_executions",
                "maximum_deployments",
                "maximum_model_weight_changes",
            }
            and value != 0
        ):
            raise SystemExit(f"zero-effect resource limit mismatch: {key}")

if run(["git", "tag", "--list", "v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag is not authorized")
PY

aion_confirm_immutable_v01_tag_history >/dev/null

echo "controlled model gateway no-go PASS"

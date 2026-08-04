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
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AION246_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/external_cognition.py",
    "services/brain-api/src/aion_brain/external_cognition/__init__.py",
    "services/brain-api/src/aion_brain/external_cognition/authorization.py",
    "services/brain-api/src/aion_brain/external_cognition/component_binding.py",
    "services/brain-api/src/aion_brain/external_cognition/provider_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/model_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/request_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/response_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/message_normalization.py",
    "services/brain-api/src/aion_brain/external_cognition/structured_output.py",
    "services/brain-api/src/aion_brain/external_cognition/routing_policy.py",
    "services/brain-api/src/aion_brain/external_cognition/budgets.py",
    "services/brain-api/src/aion_brain/external_cognition/trust.py",
    "services/brain-api/src/aion_brain/external_cognition/redaction.py",
    "services/brain-api/src/aion_brain/external_cognition/circuit_breaker.py",
    "services/brain-api/src/aion_brain/external_cognition/fixture_provider.py",
    "services/brain-api/src/aion_brain/external_cognition/replay.py",
    "services/brain-api/src/aion_brain/external_cognition/observability.py",
    "services/brain-api/src/aion_brain/external_cognition/audit.py",
    "services/brain-api/src/aion_brain/external_cognition/integrity.py",
    "services/brain-api/src/aion_brain/external_cognition/evidence.py",
}
AION246_RUNNER = "scripts/external-cognition-fixture-local-run.py"
AION246_TESTS = {
    "services/brain-api/tests/aion243_release_candidate_scope.py",
    "services/brain-api/tests/test_adaptive_intelligence_program_authorization_aion245.py",
    "services/brain-api/tests/test_external_cognition_foundation_aion246.py",
}
AION246_SCRIPTS = {
    "scripts/adaptive-intelligence-program-authorization-check.sh",
    "scripts/adaptive-intelligence-program-authorization-no-go-regression.sh",
    "scripts/adaptive-intelligence-runtime-hold.sh",
    "scripts/connector-platform-checkpoint.sh",
    "scripts/connector-release-no-go-regression.sh",
    "scripts/connector-runtime-no-external-call-regression.sh",
    "scripts/external-cognition-fixture-pilot-evidence-check.sh",
    "scripts/external-cognition-foundation-check.sh",
    "scripts/external-cognition-foundation-no-go-regression.sh",
    "scripts/external-cognition-runtime-hold.sh",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/model-gateway-authorization-no-go-regression.sh",
    "scripts/model-gateway-no-go-regression.sh",
    "scripts/model-gateway-operator-evaluation-no-go-regression.sh",
    "scripts/operator-action-write-path-no-go-regression.sh",
    "scripts/operator-console-static-check.sh",
    "scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh",
    "scripts/secure-runtime-foundation-no-go-regression.sh",
    "scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh",
    "scripts/secure-runtime-integration-program-no-go-regression.sh",
    "scripts/self-improvement-shadow-activation-authorization-no-go-regression.sh",
    "scripts/self-improvement-shadow-activation-operator-evaluation-no-go-regression.sh",
    "scripts/self-improvement-shadow-mode-operator-evaluation-no-go-regression.sh",
    "scripts/static-console-safety-check.sh",
    "scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh",
    "scripts/v02-release-candidate-no-go-regression.sh",
    "scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh",
}
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "docs/project-status.md",
    "docs/adr/README.md",
    "docs/adr/0210-controlled-provider-neutral-external-cognition-gateway-foundation.md",
    "operator-console-static/README.md",
    "operator-console-static/app.js",
    "operator-console-static/index.html",
    AION246_RUNNER,
    *AION246_SOURCE,
    *AION246_TESTS,
    *AION246_SCRIPTS,
}
ALLOWED_PREFIXES = (
    "docs/adaptive-intelligence/",
    "docs/release/v03-external-cognition-",
    "examples/adaptive-intelligence/",
    "operator-console-static/demo-data/",
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
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "packages/aion-sdk-python/src/",
    "packages/aion-sdk-python/aionctl/",
)
PROHIBITED_SOURCE = {
    "services/brain-api/src/aion_brain/external_cognition/network.py",
    "services/brain-api/src/aion_brain/external_cognition/http_client.py",
    "services/brain-api/src/aion_brain/external_cognition/openai.py",
    "services/brain-api/src/aion_brain/external_cognition/anthropic.py",
    "services/brain-api/src/aion_brain/external_cognition/google.py",
    "services/brain-api/src/aion_brain/external_cognition/azure_openai.py",
    "services/brain-api/src/aion_brain/external_cognition/credential_store.py",
    "services/brain-api/src/aion_brain/external_cognition/token_store.py",
    "services/brain-api/src/aion_brain/external_cognition/background_worker.py",
    "services/brain-api/src/aion_brain/external_cognition/scheduler.py",
    "services/brain-api/src/aion_brain/api/external_cognition.py",
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
DISALLOWED_ENV_NAMES = {"environ", "getenv", "putenv"}
ENABLED_BOOLEAN_MARKERS = {
    "actual_model_provider_call_enabled",
    "provider_network_adapter_enabled",
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "provider_credential_input_enabled",
    "provider_credential_read_enabled",
    "provider_credential_generation_enabled",
    "provider_credential_persistence_enabled",
    "provider_token_input_enabled",
    "provider_token_read_enabled",
    "provider_token_persistence_enabled",
    "provider_authorization_header_creation_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "hidden_reasoning_capture_enabled",
    "model_output_triggered_execution_enabled",
    "model_output_tool_call_enabled",
    "persistent_memory_write_enabled",
    "verified_knowledge_promotion_enabled",
    "actual_belief_mutation_enabled",
    "engagement_learning_enabled",
    "adaptive_routing_runtime_enabled",
    "external_connector_execution_enabled",
    "external_tool_execution_enabled",
    "autonomous_background_loop_enabled",
    "scheduled_provider_calls_enabled",
    "source_rewrite_enabled",
    "runtime_git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_runtime_authorized",
    "implementation_approved",
    "privileged_bypass",
}


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


def allowed_path(path: str) -> bool:
    return path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)


changed_paths: set[str] = set()
for parts in changed_entries():
    status = parts[0]
    if status.startswith(("D", "R")):
        raise SystemExit(f"AION-246 deletion or rename is not authorized: {parts}")
    for raw_path in parts[1:]:
        path = raw_path.replace("\\", "/")
        changed_paths.add(path)
        name = Path(path).name
        if name in PROHIBITED_NAMES:
            raise SystemExit(f"package/dependency file change is prohibited: {path}")
        if path.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited path changed: {path}")
        if path.startswith("services/brain-api/src/aion_brain/") and path not in AION246_SOURCE:
            raise SystemExit(f"only exact AION-246 external cognition source may change: {path}")
        if path.startswith("services/brain-api/src/aion_brain/api/"):
            raise SystemExit(f"API runtime route change is prohibited: {path}")
        if not allowed_path(path):
            raise SystemExit(f"disallowed AION-246 changed path: {path}")

for path in PROHIBITED_SOURCE:
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited external cognition runtime/provider file exists: {path}")

for path in sorted(AION246_SOURCE | {AION246_RUNNER}):
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"required AION-246 source missing: {path}")
    tree = ast.parse(target.read_text(encoding="utf-8"), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                root = name.split(".", 1)[0]
                if root in DISALLOWED_IMPORT_ROOTS or name.startswith(DISALLOWED_IMPORT_PREFIXES):
                    raise SystemExit(f"disallowed provider/network import in {path}: {name}")
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            root = name.split(".", 1)[0]
            if root in DISALLOWED_IMPORT_ROOTS or name.startswith(DISALLOWED_IMPORT_PREFIXES):
                raise SystemExit(f"disallowed provider/network import in {path}: {name}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in DISALLOWED_CALLS:
                raise SystemExit(f"disallowed dynamic execution call in {path}: {func.id}")
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in {"subprocess", "socket"}
            ):
                raise SystemExit(f"disallowed runtime call in {path}: {func.value.id}.{func.attr}")
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "os"
                and func.attr in DISALLOWED_ENV_NAMES
            ):
                raise SystemExit(f"environment credential access is not authorized: {path}")
        elif isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "os"
                and node.attr in DISALLOWED_ENV_NAMES
            ):
                raise SystemExit(f"environment credential access is not authorized: {path}")

for json_path in (
    "docs/adaptive-intelligence/program-ledger.json",
    "docs/adaptive-intelligence/authorization-ledger.json",
    "examples/adaptive-intelligence/external-cognition-runtime-hold.json",
    "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json",
):
    if not (ROOT / json_path).exists():
        continue
    payload = json.loads((ROOT / json_path).read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True)
    for marker in ENABLED_BOOLEAN_MARKERS:
        if f'"{marker}": true' in serialized:
            raise SystemExit(f"prohibited AION-246 boolean enabled in {json_path}: {marker}")

if run(["git", "tag", "--list", "aion-v0.2.0", "v0.2.0*", "aion-v0.3*", "v0.3*"]).stdout.strip():
    raise SystemExit("stable v0.2 or v0.3 tag exists")

print("controlled external cognition gateway foundation no-go PASS")
PY

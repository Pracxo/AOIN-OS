#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/connector-runtime-review-gate.md
  docs/connectors/no-external-call-evidence-pack.md
  docs/connectors/connector-credential-token-absence-proof.md
  docs/connectors/connector-egress-ingress-traceability-matrix.md
  docs/connectors/connector-runtime-disabled-proof.md
  docs/connectors/connector-pre-implementation-gate.md
  docs/connectors/connector-runtime-review-no-go-pack.md
  docs/connectors/future-connector-runtime-implementation-plan.md
  docs/adr/0100-connector-runtime-review-gate.md
)

required_examples=(
  examples/connectors/connector-runtime-review-gate.json
  examples/connectors/no-external-call-evidence-pack.json
  examples/connectors/connector-credential-token-absence-proof.json
  examples/connectors/connector-egress-ingress-traceability-matrix.json
  examples/connectors/connector-runtime-review-no-go-result.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing connector runtime review artifact: $file" >&2
    exit 1
  }
done

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-109: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-109 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-109 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$|^services/brain-api/src/aion_brain/api/connector_credentials\.py$' \
  | rg -n '.'; then
  echo "AION-109 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$|^services/brain-api/src/aion_brain/api/connector_credentials\.py$' \
  | rg -n '.'; then
  echo "AION-109 must not add API router files" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src packages/aion-sdk-python/src .env.example \
	  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$|^services/brain-api/src/aion_brain/api/connector_credentials\.py$|^services/brain-api/src/aion_brain/connector_simulator/|^services/brain-api/src/aion_brain/connector_policy/|^services/brain-api/src/aion_brain/connector_sandbox/|^services/brain-api/src/aion_brain/connector_credentials/|^services/brain-api/src/aion_brain/production_auth/|^services/brain-api/src/aion_brain/contracts/connector_simulator\.py$|^services/brain-api/src/aion_brain/contracts/connector_policy\.py$|^services/brain-api/src/aion_brain/contracts/connector_sandbox\.py$|^services/brain-api/src/aion_brain/contracts/connector_credentials\.py$|^services/brain-api/src/aion_brain/contracts/production_auth\.py$|^services/brain-api/src/aion_brain/local_auth/audit\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials\.py$|^packages/aion-sdk-python/src/aion_sdk/client\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$|^services/brain-api/src/aion_brain/config\.py$|^services/brain-api/src/aion_brain/policy_catalog/defaults\.py$|^services/brain-api/src/aion_brain/kernel/app_factory\.py$|^services/brain-api/src/aion_brain/kernel/container\.py$|^services/brain-api/src/aion_brain/kernel/diagnostics\.py$|^services/brain-api/src/aion_brain/audit_integrity/ledger\.py$|^services/brain-api/src/aion_brain/audit_integrity/provenance\.py$|^services/brain-api/src/aion_brain/contracts/telemetry\.py$|^services/brain-api/src/aion_brain/telemetry/visual\.py$|^services/brain-api/src/aion_brain/freeze/gate\.py$|^services/brain-api/src/aion_brain/security_baseline/hardening_gate\.py$|^services/brain-api/src/aion_brain/release_package/packager\.py$|^\.env\.example$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/request_identity\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/actor_context_resolution\.py$|^services/brain-api/src/aion_brain/identity/dev_auth\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/(identity_assertion|identity_assertion_replay)\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/self_improvement\.py$|^services/brain-api/src/aion_brain/self_improvement/(__init__|approval|change_budget|evidence|governance|ledger|lifecycle|protected_paths|risk)\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(benchmark_contracts|benchmark_registry|benchmark_runner|comparison|evaluation_evidence|holdout|scoring)\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(experiment|experiment_runner|hypothesis|observation|pattern_intake|proposal_service|regression_proposal)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(ci_monitor|diff_hash|git_controller|merge_controller|patch_generator|patch_validator|pr_controller|rollback|sandbox|test_first|worktree)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(canary_contracts|canary|monitoring|rollback_controller|outcome_ledger|strategy_selector|retrieval_optimizer|case_based_planner|preference_learning|skill_evolution|integrated_pipeline)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/contracts/self_improvement_shadow\.py$|^services/brain-api/src/aion_brain/self_improvement/shadow_(budget|evidence|mode|observation|pipeline|redaction|runner)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/(explanations|grounding|model_outputs|prompts)/redaction\.py$' \
		  | rg -n '.'; then
  echo "AION-109 must not change runtime, SDK, CLI, or config source files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src packages/aion-sdk-python/src \
	  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$|^services/brain-api/src/aion_brain/api/connector_credentials\.py$|^services/brain-api/src/aion_brain/connector_simulator/|^services/brain-api/src/aion_brain/connector_policy/|^services/brain-api/src/aion_brain/connector_sandbox/|^services/brain-api/src/aion_brain/connector_credentials/|^services/brain-api/src/aion_brain/production_auth/|^services/brain-api/src/aion_brain/contracts/connector_simulator\.py$|^services/brain-api/src/aion_brain/contracts/connector_policy\.py$|^services/brain-api/src/aion_brain/contracts/connector_sandbox\.py$|^services/brain-api/src/aion_brain/contracts/connector_credentials\.py$|^services/brain-api/src/aion_brain/contracts/production_auth\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/request_identity\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/actor_context_resolution\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/(identity_assertion|identity_assertion_replay)\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/contracts/self_improvement\.py$|^services/brain-api/src/aion_brain/self_improvement/(__init__|approval|change_budget|evidence|governance|ledger|lifecycle|protected_paths|risk)\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(benchmark_contracts|benchmark_registry|benchmark_runner|comparison|evaluation_evidence|holdout|scoring)\.py$' \
	  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(experiment|experiment_runner|hypothesis|observation|pattern_intake|proposal_service|regression_proposal)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(ci_monitor|diff_hash|git_controller|merge_controller|patch_generator|patch_validator|pr_controller|rollback|sandbox|test_first|worktree)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/self_improvement/(canary_contracts|canary|monitoring|rollback_controller|outcome_ledger|strategy_selector|retrieval_optimizer|case_based_planner|preference_learning|skill_evolution|integrated_pipeline)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/contracts/self_improvement_shadow\.py$|^services/brain-api/src/aion_brain/self_improvement/shadow_(budget|evidence|mode|observation|pipeline|redaction|runner)\.py$' \
		  | rg -v '^services/brain-api/src/aion_brain/(explanations|grounding|model_outputs|prompts)/redaction\.py$' \
		  | rg -n '.'; then
  echo "AION-109 must not add runtime, SDK, or CLI source files" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request' \
  services/brain-api/src/aion_brain/connector_runtime \
  services/brain-api/src/aion_brain/api/connector_runtime.py; then
  echo "connector runtime network call pattern found" >&2
  exit 1
fi

if rg -n '\b(connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==)\b' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "connector or provider SDK dependency found" >&2
  exit 1
fi

if rg -n '\b(connector_runtime_enabled|connector_external_calls_enabled|connector_credentials_enabled|connector_token_storage_enabled|connector_activation_enabled|connector_route_registration_enabled)\s*[:=]\s*true\b' \
  services/brain-api/src .env.example operator-console-static examples/connectors; then
  echo "connector unsafe enablement found" >&2
  exit 1
fi

if rg -n 'add_api_route|dynamic[_-]?route|route_registration_enabled[[:space:]]*[:=][[:space:]]*true' \
  services/brain-api/src/aion_brain/connector_runtime services/brain-api/src/aion_brain/api/connector_runtime.py; then
  echo "connector dynamic route registration pattern found" >&2
  exit 1
fi

if rg -n 'store_credential|credential_store|secret_store|token_store|store_token|external_endpoint|provider_endpoint' \
  services/brain-api/src/aion_brain/connector_runtime services/brain-api/src/aion_brain/api/connector_runtime.py examples/connectors \
  | rg -v '^examples/connectors/connector-credential-|^examples/connectors/connector-secret-'; then
  echo "connector credential, token, or endpoint pattern found" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  "${required_examples[@]}"; then
  echo "blocked marker found in AION-109 connector examples" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-109 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
examples = [
    root / "examples/connectors/connector-runtime-review-gate.json",
    root / "examples/connectors/no-external-call-evidence-pack.json",
    root / "examples/connectors/connector-credential-token-absence-proof.json",
    root / "examples/connectors/connector-egress-ingress-traceability-matrix.json",
    root / "examples/connectors/connector-runtime-review-no-go-result.json",
]

false_keys = {
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_enabled",
    "token_storage_enabled",
    "activation_enabled",
    "route_registration_enabled",
    "network_clients_present",
    "connector_sdk_dependency_present",
    "provider_sdk_dependency_present",
    "api_router_added",
    "migration_added",
    "package_files_present",
    "external_calls_found",
    "external_destination_present",
    "credentials_present",
    "token_storage_present",
    "provider_sdk_present",
    "secret_examples_present",
    "static_console_secret_input_present",
    "secret_storage_present",
    "migration_present",
    "external_identity_runtime_present",
    "connector_credentials_enabled",
    "connector_token_storage_enabled",
    "external_call",
    "present",
}


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key == "synthetic" and nested is not True:
                raise SystemExit(f"{context}.synthetic must be true")
            if key == "expected_status" and nested != "passed":
                raise SystemExit(f"{context}.expected_status must be passed")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in examples:
    payload = json.loads(path.read_text())
    if payload.get("synthetic") is not True:
        raise SystemExit(f"example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"example status must be passed: {path}")
    walk(payload, path.relative_to(root).as_posix())

no_go = json.loads((root / "examples/connectors/connector-runtime-review-no-go-result.json").read_text())
required_checks = {
    "connector runtime enabled",
    "external call path added",
    "network client connector runtime usage",
    "connector SDK dependency added",
    "credentials stored",
    "tokens stored",
    "dynamic route registration added",
    "connector activation enabled",
    "source prompt egress allowed",
    "private reasoning egress allowed",
    "secret egress allowed",
    "policy bypass",
    "audit bypass",
}
present = {item.get("check") for item in no_go.get("checks", [])}
missing = required_checks - present
if missing:
    raise SystemExit(f"missing no-go checks: {sorted(missing)}")

print("Connector runtime no-external-call JSON checks PASS")
PY

echo "Connector runtime no-external-call regression result:"
echo "- connector_runtime: disabled"
echo "- external_calls: absent"
echo "- credentials_tokens: absent"
echo "- network_clients: absent"
echo "- connector_sdk_dependencies: absent"
echo "- routes_activation: disabled"
echo "Connector runtime no-external-call regression PASS"

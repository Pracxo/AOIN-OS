#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local candidates=()
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    candidates+=("origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}")
  fi
  candidates+=(origin/main main)

  for candidate in "${candidates[@]}"; do
    if git_ref_exists "$candidate"; then
      git merge-base HEAD "$candidate" 2>/dev/null && return 0
    fi
  done
  if git_ref_exists HEAD~1; then
    printf '%s\n' "HEAD~1"
    return 0
  fi
  return 1
}

changed_files() {
  local base
  if base="$(comparison_base)"; then
    git diff --name-only --diff-filter=ACMRT "$base" HEAD --
  fi
  git diff --name-only --diff-filter=ACMRT --
  git diff --cached --name-only --diff-filter=ACMRT --
  git ls-files --others --exclude-standard
}

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_V02_PROPOSAL_REGISTRY_SKIP_NESTED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

required_docs=(
  docs/release/v02-workstream-proposal-registry.md
  docs/release/v02-implementation-request-index.md
  docs/release/v02-approval-queue-preview.md
  docs/release/v02-proposal-review-rules.md
  docs/release/v02-proposal-state-machine.md
  docs/release/v02-proposal-evidence-requirements.md
  docs/release/v02-proposal-registry-no-go.md
  docs/adr/0117-v02-workstream-proposal-registry.md
)

required_examples=(
  examples/release/v02-workstream-proposal-registry.json
  examples/release/v02-implementation-request-index.json
  examples/release/v02-approval-queue-preview.json
  examples/release/v02-proposal-state-machine.json
  examples/release/v02-proposal-evidence-requirements.json
  operator-console-static/demo-data/v02-workstream-proposal-registry.json
  operator-console-static/demo-data/v02-approval-queue-preview.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-126 workstream proposal registry artifact: $file" >&2
    exit 1
  }
done

grep -q "0117-v02-workstream-proposal-registry.md" docs/adr/README.md || {
  echo "ADR 0117 is not indexed" >&2
  exit 1
}

if is_nested_gate_context; then
  echo "PASS: v0.2 proposal registry inherited gates deferred to outer aggregate gate"
else
  AION_V02_PREIMPLEMENTATION_BASELINE_SKIP_FULL_CHECK=1 ./scripts/v02-preimplementation-final-baseline-check.sh
  ./scripts/v02-preimplementation-master-no-go-regression.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-126" >&2
  exit 1
fi

if rg -n 'gh[[:space:]]+release[[:space:]]+create[[:space:]]+|release[[:space:]]+created[[:space:]]*[:=][[:space:]]*true|v02_release_created[[:space:]]*[:=][[:space:]]*true' \
  docs/release docs/adr/0117-v02-workstream-proposal-registry.md examples/release operator-console-static/demo-data; then
  echo "v0.2 release creation marker found" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-126: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-126 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-126 must not add or change API router files" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-126 must not add or change SDK resources or CLI implementations" >&2
  exit 1
fi

scan_paths=(
  .env.example
  docs/release
  docs/platform
  docs/connectors
  docs/auth
  docs/modules
  docs/operator-console
  examples/release
  examples/platform
  examples/connectors
  examples/auth
  examples/modules
  operator-console-static/demo-data
  services/brain-api/src
)

if rg -n '\b(runtime_implementation_approved|operator_write_execution_approved|connector_implementation_approved|production_auth_approved|module_activation_approved|external_calls_approved|credential_storage_approved|token_storage_approved|sandbox_execution_approved|oauth_oidc_saml_runtime_approved|code_loading_approved|runtime_registration_approved|capability_activation_approved|v02_release_approved|v02_release_created|package_files_added|migrations_added|api_runtime_execution_route_added|sdk_resource_implementation_added|cli_command_implementation_added|frontend_dependencies_added|backlog_implementation_items_approved|workstream_implementation_approved|approval_queue_item_approved|approval_workflow_bypassed|approval_record_missing|adr_dependency_bypassed|gate_dependency_bypassed|approval_expiry_bypassed|approval_revocation_bypassed|dual_control_bypassed)\s*[:=]\s*true\b' \
  "${scan_paths[@]}"; then
  echo "implementation approval, approval queue approval, missing approval record, bypass, or drift boolean was enabled" >&2
  exit 1
fi

if rg -n '\b(v02_tag_created|v0_2_tag_created|v0\.2_tag_created)\s*[:=]\s*true\b|git[[:space:]]+tag[[:space:]]+(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)' \
  docs/release docs/adr examples/release operator-console-static/demo-data; then
  echo "v0.2 tag creation marker found" >&2
  exit 1
fi

if rg -n '\b(connector_runtime_enabled|connector_external_calls_enabled|connector_credentials_enabled|connector_token_storage_enabled|connector_activation_enabled|connector_route_registration_enabled|external_calls_enabled|sandbox_execution_enabled|route_registration_enabled|implementation_approved|provider_sdk_dependency_added|api_runtime_execution_route_added)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors examples/platform examples/release; then
  echo "connector runtime unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(production_auth_enabled|auth_runtime_enabled|credentials_enabled|token_issuance_enabled|cookie_issuance_enabled|session_persistence_enabled|login_endpoint_enabled|logout_endpoint_enabled|external_identity_provider_enabled|provider_sdk_present)\s*[:=]\s*true\b|PRODUCTION_AUTH_ENABLED=true|AUTH_RUNTIME_ENABLED=true' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/auth examples/platform examples/release; then
  echo "production auth unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(activation_enabled|code_loading_enabled|runtime_registration_enabled|capability_activation_enabled|controlled_execution_enabled|package_installation_enabled|external_dependency_download_enabled|executable_payload_accepted|policy_bypass_enabled|audit_bypass_enabled|module_writes_enabled|activation_ready_default)\s*[:=]\s*true\b' \
  services/brain-api/src operator-console-static/demo-data examples/modules examples/platform examples/release; then
  echo "module activation unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(connector_sandbox_runtime_execution_enabled|connector_sandbox_filesystem_enabled|connector_sandbox_network_enabled|connector_sandbox_process_spawn_enabled|connector_sandbox_dynamic_import_enabled|connector_sandbox_package_install_enabled|connector_sandbox_activation_enabled)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors examples/platform examples/release; then
  echo "sandbox unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(connector_credentials_storage_enabled|connector_tokens_storage_enabled|connector_secret_material_enabled|connector_external_identity_runtime_enabled|connector_runtime_credential_access_enabled|credential_storage_enabled|token_storage_enabled|secret_material_present|credentials_present|credential_values_present|token_values_present)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors examples/platform examples/release; then
  echo "credential or token unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(oauth|oidc|saml)[-_ ]?runtime[-_ ]?enabled\s*[:=]\s*true\b|external_identity_runtime_enabled\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/auth examples/connectors examples/platform examples/release; then
  echo "external identity runtime enablement found" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  services/brain-api/src/aion_brain operator-console-static examples/release examples/platform examples/connectors; then
  echo "external call path found" >&2
  exit 1
fi

if rg -n 'execute_connector|run_connector|connector_runtime_execute|execute_operator_write|operator_write_execute|register_runtime_route|sandbox_execute|\b(hard_delete_enabled|hard_delete_allowed)\s*[:=]\s*true\b' \
  operator-console-static/app.js operator-console-static/index.html services/brain-api/src/aion_brain; then
  echo "runtime execution, route registration, sandbox execution, or hard-delete pattern found" >&2
  exit 1
fi

if rg -n '<input|<textarea|<select|contenteditable' operator-console-static/index.html operator-console-static/app.js; then
  echo "static console input control found" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-126 artifacts" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  "${required_examples[@]}"; then
  echo "blocked marker found in AION-126 examples or static data" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/release/v02-workstream-proposal-registry.json",
    root / "examples/release/v02-implementation-request-index.json",
    root / "examples/release/v02-approval-queue-preview.json",
    root / "examples/release/v02-proposal-state-machine.json",
    root / "examples/release/v02-proposal-evidence-requirements.json",
    root / "operator-console-static/demo-data/v02-workstream-proposal-registry.json",
    root / "operator-console-static/demo-data/v02-approval-queue-preview.json",
]
false_keys = {
    "runtime_implementation_approved",
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
    "package_files_added",
    "migrations_added",
    "backlog_implementation_items_approved",
    "workstream_implementation_approved",
    "approval_queue_item_approved",
    "approval_workflow_bypassed",
    "approval_record_missing",
    "adr_dependency_bypassed",
    "gate_dependency_bypassed",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "secrets_present",
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in {"implementation_approved", "approval_queue_item_approved"} and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    relative = path.relative_to(root).as_posix()
    if relative.startswith("examples/") and payload.get("synthetic") is not True:
        raise SystemExit(f"proposal registry example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"proposal registry artifact must be passed: {path}")
    if payload.get("task_id") != "AION-126":
        raise SystemExit(f"proposal registry task id must be AION-126: {path}")
    if payload.get("v02_workstream_proposal_registry_created") is not True:
        raise SystemExit(f"proposal registry created flag must be true: {path}")
    if payload.get("proposal_registry_preview_only") is not True:
        raise SystemExit(f"proposal registry preview flag must be true: {path}")
    if payload.get("approval_queue_preview_only") is not True:
        raise SystemExit(f"approval queue preview flag must be true: {path}")
    walk(payload, relative)

request_index = json.loads((root / "examples/release/v02-implementation-request-index.json").read_text())
request_types = {item["request_type"] for item in request_index["requests"]}
required_types = {
    "production auth implementation proposal",
    "audit/provenance hardening proposal",
    "rollback/recovery proposal",
    "external call release gate proposal",
    "connector runtime implementation proposal",
    "credential store implementation proposal",
    "sandbox runtime implementation proposal",
    "operator write execution proposal",
    "module activation proposal",
    "production UI decision proposal",
}
missing = required_types - request_types
if missing:
    raise SystemExit(f"missing implementation request types: {sorted(missing)}")

state_machine = json.loads((root / "examples/release/v02-proposal-state-machine.json").read_text())
required_states = {
    "drafted",
    "submitted",
    "intake_review",
    "evidence_required",
    "adr_required",
    "gate_required",
    "security_review_required",
    "architecture_review_required",
    "operator_review_required",
    "queued_for_future_decision",
    "rejected",
    "expired",
    "revoked",
    "implementation_unapproved",
}
if required_states - set(state_machine["states"]):
    raise SystemExit("proposal state machine is incomplete")

print("v0.2 workstream proposal registry JSON checks PASS")
PY

cat <<'SUMMARY'
v0.2 workstream proposal registry check result:
- v02_workstream_proposal_registry_created: true
- proposal_registry_preview_only: true
- approval_queue_preview_only: true
- approval_queue_item_approved: false
- v02_tag_created: false
- v02_release_created: false
- runtime_implementation_approved: false
- backlog_implementation_items_approved: false
- workstream_implementation_approved: false
- approval_workflow_bypassed: false
- approval_record_missing: false
- adr_dependency_bypassed: false
- gate_dependency_bypassed: false
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
v0.2 workstream proposal registry check PASS
SUMMARY

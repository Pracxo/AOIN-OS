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

required_docs=(
  docs/release/v02-implementation-authorization-preview.md
  docs/release/v02-explicit-approval-record-schema.md
  docs/release/v02-runtime-enablement-guard-boundary.md
  docs/release/v02-authorization-state-model.md
  docs/release/v02-authorization-evidence-matrix.md
  docs/release/v02-implementation-authorization-no-go.md
  docs/release/v02-implementation-authorization-checklist.md
  docs/adr/0138-v02-implementation-authorization-preview.md
)

required_examples=(
  examples/release/v02-implementation-authorization-preview.json
  examples/release/v02-explicit-approval-record-schema.json
  examples/release/v02-runtime-enablement-guard-boundary.json
  examples/release/v02-authorization-state-model.json
  examples/release/v02-authorization-evidence-matrix.json
  operator-console-static/demo-data/v02-implementation-authorization-preview.json
  operator-console-static/demo-data/v02-runtime-enablement-guard-boundary.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-147 implementation authorization artifact: $file" >&2
    exit 1
  }
done

scan_paths=(
  .env.example
  docs/release
  docs/adr
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

if rg -n '\b(implementation_authorization_approved|explicit_approval_record_approval|runtime_enablement_guard_release_approved|runtime_approval_board_final_review_approval|runtime_approval_board_decision_approved|runtime_approval_board_stabilization_approval|approval_vote_record_approval|approval_vote_record_closeout_approval|approval_vote_record_runtime_effect|implementation_go_status|implementation_go_final_approval|go_no_go_ledger_runtime_effect|approval_docket_final_review_approval|approval_docket_stabilization_approval|approval_docket_item_approved|implementation_decision_record_closeout_approval|implementation_decision_record_freeze_approval|implementation_decision_record_approval|runtime_approval_lock_release_approved|runtime_approval_review_evidence_approved|runtime_approval_review_approved|runtime_decision_lock_release_approved|decision_package_approval|approval_readiness_approved|runtime_decision_readiness_approved|review_board_decision_approval|routing_decision_approval|reviewer_signoff_implementation_approval|preapproval_queue_item_approved|request_pack_approval|submission_approval|request_package_implementation_approved|proposal_template_implementation_approved|approval_evidence_approval|evidence_completeness_bypassed|submission_freeze_bypassed|preapproval_gate_bypassed|approval_queue_item_approved|proposal_implementation_approved|runtime_implementation_approved|implementation_approval|operator_write_execution_approved|connector_implementation_approved|production_auth_approved|module_activation_approved|external_calls_approved|credential_storage_approved|token_storage_approved|sandbox_execution_approved|oauth_oidc_saml_runtime_approved|code_loading_approved|runtime_registration_approved|capability_activation_approved|v02_release_approved|v02_release_created|package_files_added|migrations_added|api_runtime_execution_route_added|sdk_resource_implementation_added|cli_command_implementation_added|frontend_dependencies_added|backlog_implementation_items_approved|workstream_implementation_approved|approval_workflow_bypassed|approval_record_missing|adr_dependency_bypassed|gate_dependency_bypassed|approval_expiry_bypassed|approval_revocation_bypassed|dual_control_bypassed|privileged_bypass)\s*[:=]\s*true\b' \
  "${scan_paths[@]}"; then
  echo "implementation authorization, guard release, approval, bypass, runtime, or drift boolean was enabled" >&2
  exit 1
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-147" >&2
  exit 1
fi

if rg -n '\b(v02_tag_created|v0_2_tag_created|v0\.2_tag_created)\s*[:=]\s*true\b|git[[:space:]]+tag[[:space:]]+(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)' \
  docs/release docs/adr examples/release operator-console-static/demo-data; then
  echo "v0.2 tag creation marker found" >&2
  exit 1
fi

if rg -n 'gh[[:space:]]+release[[:space:]]+create[[:space:]]+|release[[:space:]]+created[[:space:]]*[:=][[:space:]]*true|v02_release_created[[:space:]]*[:=][[:space:]]*true' \
  docs/release docs/adr examples/release operator-console-static/demo-data; then
  echo "v0.2 release creation marker found" >&2
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

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-147: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-147 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-147 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-147 must not add or change SDK resources or CLI implementations" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-147 artifacts" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  "${required_examples[@]}"; then
  echo "blocked marker found in AION-147 examples or static data" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 implementation authorization no-go regression result:
- implementation authorization approved true: absent
- explicit approval record approval true: absent
- runtime enablement guard release approved true: absent
- runtime approval board final review approval true: absent
- runtime approval board decision approved true: absent
- approval vote record approval true: absent
- approval vote record runtime effect true: absent
- implementation go status true: absent
- implementation go final approval true: absent
- approval docket item approved true: absent
- implementation decision record approval true: absent
- runtime approval lock release approved true: absent
- runtime approval review approved true: absent
- decision package approval true: absent
- approval readiness approval true: absent
- review board decision approval true: absent
- routing decision approval true: absent
- request pack approval true: absent
- submission approval true: absent
- implementation approval true: absent
- v0.2 tag created: absent
- v0.2 release created: absent
- production auth enabled: absent
- connector runtime enabled: absent
- operator write execution enabled: absent
- module activation enabled: absent
- external calls enabled: absent
- credential/token storage enabled: absent
- sandbox execution enabled: absent
- package files added: absent
- migrations added: absent
- runtime API execution routes added: absent
v0.2 implementation authorization no-go regression PASS
SUMMARY

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

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
  docs/release/v02-implementation-authorization-final-review.md
  docs/release/v02-explicit-approval-record-closeout.md
  docs/release/v02-runtime-enablement-guard-final-lock.md
  docs/release/v02-authorization-final-evidence-matrix.md
  docs/release/v02-final-authorization-approval-guard.md
  docs/release/v02-implementation-authorization-final-no-go.md
  docs/release/v02-implementation-authorization-final-checklist.md
  docs/adr/0140-v02-implementation-authorization-final-review.md
)

required_examples=(
  examples/release/v02-implementation-authorization-final-review.json
  examples/release/v02-explicit-approval-record-closeout.json
  examples/release/v02-runtime-enablement-guard-final-lock.json
  examples/release/v02-authorization-final-evidence-matrix.json
  examples/release/v02-final-authorization-approval-guard.json
  operator-console-static/demo-data/v02-implementation-authorization-final-review.json
  operator-console-static/demo-data/v02-runtime-enablement-guard-final-lock.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing AION-149 implementation authorization final artifact: $file" >&2
    exit 1
  }
done

scan_paths=(
  .env.example
  docs/release
  docs/adr
  docs/platform
  examples/release
  examples/platform
  examples/connectors
  examples/auth
  examples/modules
  operator-console-static/demo-data
  services/brain-api/src
)

aion151_validate_scoped_authorization_if_present
scan_files=()
while IFS= read -r file; do
  scan_files+=("$file")
done < <(aion151_scan_files_excluding_scoped_authorization "${scan_paths[@]}")

if ((${#scan_files[@]})) && rg -n '\b(implementation_authorization_approved|implementation_authorization_stabilization_approval|implementation_authorization_final_review_approval|explicit_approval_record_approval|explicit_approval_record_freeze_approval|explicit_approval_record_closeout_approval|runtime_enablement_guard_release_approved|runtime_enablement_guard_final_lock_release_approved|runtime_approval_board_final_review_approval|runtime_approval_board_decision_approved|runtime_approval_board_stabilization_approval|approval_vote_record_approval|approval_vote_record_closeout_approval|approval_vote_record_runtime_effect|implementation_go_status|implementation_go_final_approval|go_no_go_ledger_runtime_effect|approval_docket_final_review_approval|approval_docket_item_approved|approval_docket_stabilization_approval|implementation_decision_record_approval|implementation_decision_record_closeout_approval|runtime_approval_lock_release_approved|runtime_approval_review_approved|runtime_decision_lock_release_approved|decision_package_approval|approval_readiness_approved|runtime_decision_readiness_approved|review_board_decision_approval|routing_decision_approval|reviewer_signoff_implementation_approval|preapproval_queue_item_approved|request_pack_approval|submission_approval|request_package_implementation_approved|proposal_template_implementation_approved|approval_evidence_approval|evidence_completeness_bypassed|submission_freeze_bypassed|preapproval_gate_bypassed|implementation_approval|workstream_implementation_approval|proposal_implementation_approval|approval_queue_item_approved|approval_workflow_bypassed|approval_record_missing|adr_dependency_bypassed|gate_dependency_bypassed|runtime_implementation_approved|operator_write_execution_approved|connector_implementation_approved|production_auth_approved|module_activation_approved|external_calls_approved|credential_storage_approved|token_storage_approved|sandbox_execution_approved|package_files_added|migrations_added|api_runtime_execution_route_added|connector_runtime_enabled|production_auth_enabled|module_activation_enabled|operator_write_execution_enabled|external_calls_enabled|sandbox_execution_enabled|credentials_present|tokens_present|secrets_present)\s*[:=]\s*true\b' "${scan_files[@]}"; then
  echo "implementation authorization final review, approval, bypass, runtime, or drift boolean was enabled" >&2
  exit 1
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-149" >&2
  exit 1
fi

if rg -n '\b(v02_tag_created|v0_2_tag_created|v0\.2_tag_created)\s*[:=]\s*true\b|git[[:space:]]+tag[[:space:]]+(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)' docs/release docs/adr examples/release operator-console-static/demo-data; then
  echo "v0.2 tag creation marker found" >&2
  exit 1
fi

if rg -n 'gh[[:space:]]+release[[:space:]]+create[[:space:]]+|release[[:space:]]+created[[:space:]]*[:=][[:space:]]*true|v02_release_created[[:space:]]*[:=][[:space:]]*true' docs/release docs/adr examples/release operator-console-static/demo-data; then
  echo "v0.2 release creation marker found" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' services/brain-api/src/aion_brain operator-console-static examples/release examples/platform examples/connectors; then
  echo "external call path found" >&2
  exit 1
fi

if rg -n 'execute_connector|run_connector|connector_runtime_execute|execute_operator_write|operator_write_execute|register_runtime_route|sandbox_execute|\b(hard_delete_enabled|hard_delete_allowed)\s*[:=]\s*true\b' operator-console-static/app.js operator-console-static/index.html services/brain-api/src/aion_brain; then
  echo "runtime execution, route registration, sandbox execution, or hard-delete pattern found" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-149 artifacts" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' "${required_examples[@]}"; then
  echo "blocked marker found in AION-149 examples or static data" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-149: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-149 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-149 must not add or change API runtime execution routes" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-149 must not add or change SDK resources or CLI implementations" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 implementation authorization final no-go regression result:
- implementation authorization approved true: absent
- implementation authorization final review approval true: absent
- explicit approval record approval true: absent
- explicit approval record closeout approval true: absent
- runtime enablement guard release approved true: absent
- runtime enablement guard final lock release approved true: absent
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
v0.2 implementation authorization final no-go regression PASS
SUMMARY

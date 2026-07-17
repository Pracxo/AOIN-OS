#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

AION160_FEATURE_COMMIT="085b1b9d9cbbc23a735c1a82be66a2e901a56761"
AION160_MERGE_COMMIT="bfc2afdc96358559027ee36efc0bc26ed3bb796d"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

git_commit_exists() {
  git cat-file -e "$1^{commit}" >/dev/null 2>&1
}

verify_aion160_commit_in_history() {
  local commit="$1"
  local label="$2"

  if git_commit_exists "$commit"; then
    git merge-base --is-ancestor "$commit" HEAD || {
      echo "AION-160 $label commit is not in current history: $commit" >&2
      exit 1
    }
  else
    echo "WARN: AION-160 $label commit unavailable in this checkout; skipping shallow-checkout ancestry confirmation"
  fi
}

required_files=(
  docs/release/v02-actor-context-trust-boundary-remediation-closeout.md
  docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md
  docs/release/v02-offline-identity-assertion-verification-explicit-approval-record.md
  docs/release/v02-offline-identity-assertion-verification-scope.md
  docs/release/v02-offline-identity-assertion-verification-threat-model.md
  docs/release/v02-offline-identity-assertion-verification-runtime-hold.md
  docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md
  docs/release/v02-offline-identity-assertion-verification-no-go.md
  docs/release/v02-offline-identity-assertion-verification-checklist.md
  docs/adr/0152-v02-offline-ed25519-identity-assertion-verification-authorization.md
  examples/release/v02-actor-context-trust-boundary-remediation-closeout.json
  examples/release/v02-offline-identity-assertion-verification-authorization.json
  examples/release/v02-offline-identity-assertion-verification-explicit-approval-record.json
  examples/release/v02-offline-identity-assertion-verification-runtime-hold.json
  examples/release/v02-offline-identity-assertion-verification-evidence-matrix.json
  operator-console-static/demo-data/v02-offline-identity-assertion-verification-authorization.json
  scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh
  scripts/v02-offline-identity-assertion-verification-authorization-check.sh
  services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-161 offline identity assertion verification artifact: $file" >&2
    exit 1
  }
done

grep -q "0152-v02-offline-ed25519-identity-assertion-verification-authorization.md" docs/adr/README.md || {
  echo "ADR 0152 is not indexed" >&2
  exit 1
}

grep -F "Current authorization: AION-161-PA-0006 active for AION-162." docs/project-status.md >/dev/null || {
  echo "project status does not describe AION-161 as the current authorization" >&2
  exit 1
}

grep -F "AION-161-PA-0006" docs/release/v02-explicit-approval-record-master-ledger.md >/dev/null || {
  echo "master ledger does not include AION-161-PA-0006" >&2
  exit 1
}

for marker in \
  'approved_dependency_name=cryptography' \
  'approved_dependency_specifier=>=49.0.0,<50.0.0' \
  'approved_dependency_manifest=services/brain-api/pyproject.toml' \
  'approved_dependency_change_count=1'; do
  grep -F "$marker" docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md >/dev/null || {
    echo "authorized cryptography dependency metadata is not documented: $marker" >&2
    exit 1
  }
done

if git diff --name-only --diff-filter=ACMRT "$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main 2>/dev/null || echo HEAD)" HEAD -- services/brain-api/pyproject.toml | rg -n '.'; then
  echo "AION-161 must not change services/brain-api/pyproject.toml" >&2
  exit 1
fi

verify_aion160_commit_in_history "$AION160_FEATURE_COMMIT" "feature"
verify_aion160_commit_in_history "$AION160_MERGE_COMMIT" "merge"

"$PYTHON_BIN" scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode check
./scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py \
    -q
fi

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-actor-context-trust-boundary-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/v02-actor-context-trust-boundary-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-request-identity-stabilization-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

cat <<'SUMMARY'
v0.2 offline identity assertion verification authorization result:
- AION-151-PA-0001: historical, consumed, expired, non-reusable
- AION-153-PA-0002: historical, consumed, expired, non-reusable
- AION-155-PA-0003: historical, consumed, expired, non-reusable
- AION-157-PA-0004: historical, consumed by AION-158 PR 68, expired, non-reusable
- AION-159-PA-0005: historical, consumed by AION-160 PR 70, expired, non-reusable
- AION-161-PA-0006: only active approved authorization
- candidate_id: production-auth-offline-identity-assertion-verification
- workstream: production-auth-verification-core
- implementation_task: AION-162
- authorization_scope: offline-ed25519-identity-assertion-verification
- approved future dependency: cryptography>=49.0.0,<50.0.0 in services/brain-api/pyproject.toml
- AION-161 implementation source and dependency changes: absent
- runtime authentication, request parsing, runtime private keys, provider networking, replay runtime, endpoints, packages, migrations, SDK/CLI runtime surfaces, connector runtime, operator writes, module activation, sandbox execution, tags, and releases: false or absent
v0.2 offline identity assertion verification authorization PASS
SUMMARY

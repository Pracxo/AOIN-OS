#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

AION158_FEATURE_COMMIT="767fd9b228b00b04569df2e3b1b3f6bc9ecd846f"
AION158_MERGE_COMMIT="f792c92e1d8a73ec8e7377b5d59269dea359006d"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

git_commit_exists() {
  git cat-file -e "$1^{commit}" >/dev/null 2>&1
}

verify_aion158_commit_in_history() {
  local commit="$1"
  local label="$2"

  if git_commit_exists "$commit"; then
    git merge-base --is-ancestor "$commit" HEAD || {
      echo "AION-158 $label commit is not in current history: $commit" >&2
      exit 1
    }
  else
    echo "WARN: AION-158 $label commit unavailable in this checkout; skipping shallow-checkout ancestry confirmation"
  fi
}

required_files=(
  docs/release/v02-request-identity-stabilization-closeout.md
  docs/release/v02-actor-context-trust-boundary-authorization-transaction.md
  docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md
  docs/release/v02-actor-context-trust-boundary-scope.md
  docs/release/v02-actor-context-trust-boundary-runtime-hold.md
  docs/release/v02-actor-context-trust-boundary-evidence-matrix.md
  docs/release/v02-actor-context-trust-boundary-no-go.md
  docs/release/v02-actor-context-trust-boundary-checklist.md
  docs/adr/0150-v02-actor-context-trust-boundary-authorization.md
  examples/release/v02-request-identity-stabilization-closeout.json
  examples/release/v02-actor-context-trust-boundary-authorization.json
  examples/release/v02-actor-context-trust-boundary-explicit-approval-record.json
  examples/release/v02-actor-context-trust-boundary-runtime-hold.json
  examples/release/v02-actor-context-trust-boundary-evidence-matrix.json
  operator-console-static/demo-data/v02-actor-context-trust-boundary-authorization.json
  services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-159 actor-context trust-boundary artifact: $file" >&2
    exit 1
  }
done

grep -q "0150-v02-actor-context-trust-boundary-authorization.md" docs/adr/README.md || {
  echo "ADR 0150 is not indexed" >&2
  exit 1
}

grep -F "non-development identity-header trust fallback" \
  docs/release/v02-actor-context-trust-boundary-authorization-transaction.md >/dev/null || {
    echo "current actor-context trust-boundary finding is not documented" >&2
    exit 1
  }

for header in \
  X-AION-Actor-ID \
  X-AION-Workspace-ID \
  X-AION-Roles \
  X-AION-Permissions \
  X-AION-Security-Scope; do
  grep -F "$header" services/brain-api/src/aion_brain/identity/dev_auth.py >/dev/null || {
    echo "expected current dev_auth header behavior missing: $header" >&2
    exit 1
  }
  grep -F "$header" docs/release/v02-actor-context-trust-boundary-authorization-transaction.md >/dev/null || {
    echo "header behavior is not documented: $header" >&2
    exit 1
  }
done

if grep -F 'dev_enabled = settings.env == "development" and settings.dev_auth_enabled' \
  services/brain-api/src/aion_brain/identity/dev_auth.py >/dev/null; then
  grep -F "AION-159 changes no implementation source" \
    docs/release/v02-actor-context-trust-boundary-authorization-transaction.md >/dev/null || {
      echo "AION-159 pre-remediation source state is not documented" >&2
      exit 1
    }
elif grep -F 'return settings.env == "development" and settings.dev_auth_enabled is True' \
  services/brain-api/src/aion_brain/identity/dev_auth.py >/dev/null; then
  test -f docs/release/v02-actor-context-trust-boundary-remediation.md || {
    echo "AION-160 remediated actor-context state is missing implementation evidence" >&2
    exit 1
  }
else
  echo "dev_auth development gate expression changed unexpectedly" >&2
  exit 1
fi

verify_aion158_commit_in_history "$AION158_FEATURE_COMMIT" "feature"
verify_aion158_commit_in_history "$AION158_MERGE_COMMIT" "merge"

"$PYTHON_BIN" scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode check

./scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh
./scripts/production-auth-request-identity-stabilization-check.sh
./scripts/production-auth-request-identity-stabilization-no-go-regression.sh
./scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

cat <<'SUMMARY'
v0.2 actor context trust boundary authorization result:
- AION-151-PA-0001: historical, inactive, consumed, expired, non-reusable
- AION-153-PA-0002: historical, inactive, consumed, expired, non-reusable
- AION-155-PA-0003: historical, inactive, consumed, expired, non-reusable
- AION-157-PA-0004: historical, consumed by AION-158 PR 68, expired, non-reusable
- AION-159-PA-0005: only active approved authorization
- candidate_id: production-auth-actor-context-trust-boundary
- workstream: production-auth-route-context-hardening
- implementation_task: AION-160
- authorization_scope: fail-closed-actor-context-resolution
- runtime implementation approved: false
- production auth runtime enabled: false
- identity verification enabled: false
- authenticated requests enabled: false
- authenticated actor context enabled: false
- production identity, role, permission, and security-scope header trust: false
- endpoint, header, cookie, protected-material, provider, external-call, package, migration, SDK, CLI, connector, operator, module, sandbox, tag, and release approvals: false
v0.2 actor context trust boundary authorization PASS
SUMMARY

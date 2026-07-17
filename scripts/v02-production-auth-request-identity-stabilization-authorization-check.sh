#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

AION156_FEATURE_COMMIT="2fbeb77bdc33772c46a679cbfa0bdafe327abb42"
AION156_MERGE_COMMIT="051f6f2e8b901863f8dc9cad405e5b5401db3695"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local merge_base
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        if [[ -n "$merge_base" ]]; then
          echo "$merge_base"
          return 0
        fi
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      if [[ -n "$merge_base" ]]; then
        echo "$merge_base"
        return 0
      fi
    fi
  done
  if git_ref_exists HEAD~1; then
    echo "HEAD~1"
    return 0
  fi
  return 1
}

changed_files() {
  local base
  {
    if base="$(comparison_base)"; then
      git diff --name-only --diff-filter=ACMRT "$base" HEAD -- "$@"
    fi
    git diff --name-only --diff-filter=ACMRT HEAD -- "$@"
    git diff --cached --name-only --diff-filter=ACMRT -- "$@"
    git ls-files --others --exclude-standard -- "$@"
  } | sort -u
}

verify_commit_in_history() {
  local commit="$1"
  local label="$2"
  if git cat-file -e "${commit}^{commit}" 2>/dev/null; then
    git merge-base --is-ancestor "$commit" HEAD || {
      echo "AION-156 ${label} commit is not in current history" >&2
      exit 1
    }
  else
    echo "WARN: AION-156 ${label} commit unavailable in this checkout; skipping shallow-checkout ancestry confirmation"
  fi
}

fetch_aion156_pr_evidence() {
  local gh_command=(gh pr view 66 --json state,baseRefName,headRefName,headRefOid,mergeCommit)
  if ! command -v gh >/dev/null 2>&1; then
    return 1
  fi
  if [[ -n "${CI:-}" || -n "${GITHUB_ACTIONS:-}" ]] && [[ -z "${GH_TOKEN:-}${GITHUB_TOKEN:-}" ]]; then
    return 1
  fi
  if command -v timeout >/dev/null 2>&1; then
    GH_PROMPT_DISABLED=1 timeout 20 "${gh_command[@]}" >/tmp/aion157-pr66.json 2>/dev/null
  elif command -v gtimeout >/dev/null 2>&1; then
    GH_PROMPT_DISABLED=1 gtimeout 20 "${gh_command[@]}" >/tmp/aion157-pr66.json 2>/dev/null
  else
    GH_PROMPT_DISABLED=1 "${gh_command[@]}" >/tmp/aion157-pr66.json 2>/dev/null
  fi
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 \
    AION_PRODUCTION_AUTH_REQUEST_IDENTITY_INHERITED_GATE=1 \
    "$@"
}

required_files=(
  docs/release/v02-production-auth-request-identity-boundary-closeout.md
  docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md
  docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md
  docs/release/v02-production-auth-request-identity-stabilization-scope.md
  docs/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.md
  docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md
  docs/release/v02-production-auth-request-identity-stabilization-no-go.md
  docs/release/v02-production-auth-request-identity-stabilization-checklist.md
  docs/adr/0148-v02-production-auth-request-identity-stabilization-authorization.md
  examples/release/v02-production-auth-request-identity-boundary-closeout.json
  examples/release/v02-production-auth-request-identity-stabilization-authorization.json
  examples/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.json
  examples/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.json
  examples/release/v02-production-auth-request-identity-stabilization-evidence-matrix.json
  operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json
  services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py
)

implementation_files=(
  services/brain-api/src/aion_brain/contracts/request_identity.py
  services/brain-api/src/aion_brain/production_auth/verifier.py
  services/brain-api/src/aion_brain/production_auth/request_boundary.py
  services/brain-api/src/aion_brain/production_auth/request_middleware.py
  services/brain-api/src/aion_brain/production_auth/request_evidence.py
)

for file in "${required_files[@]}" "${implementation_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-157 request identity stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0148-v02-production-auth-request-identity-stabilization-authorization.md" docs/adr/README.md || {
  echo "ADR 0148 is not indexed" >&2
  exit 1
}

verify_commit_in_history "$AION156_FEATURE_COMMIT" "feature"
verify_commit_in_history "$AION156_MERGE_COMMIT" "merge"

if fetch_aion156_pr_evidence; then
  "$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/aion157-pr66.json").read_text())
assert payload["state"] == "MERGED"
assert payload["baseRefName"] == "main"
assert payload["headRefName"] == "phase/v02-production-auth-request-identity-boundary"
assert payload["headRefOid"] == "2fbeb77bdc33772c46a679cbfa0bdafe327abb42"
assert payload["mergeCommit"]["oid"] == "051f6f2e8b901863f8dc9cad405e5b5401db3695"
PY
else
  echo "WARN: gh PR 66 evidence unavailable; verified AION-156 commits from git history when available"
fi

"$PYTHON_BIN" scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode check

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  if aion158_is_scoped_request_identity_stabilization_path "$file"; then
    continue
  fi
  if aion162_is_scoped_offline_identity_assertion_verification_path "$file"; then
    continue
  fi
  echo "AION-157 must not modify request-identity, production-auth, config, kernel, API, SDK, or CLI implementation source: $file" >&2
  exit 1
done < <(
  changed_files \
    services/brain-api/src/aion_brain/contracts/request_identity.py \
    services/brain-api/src/aion_brain/production_auth \
    services/brain-api/src/aion_brain/api_support \
    services/brain-api/src/aion_brain/config.py \
    services/brain-api/src/aion_brain/kernel \
    services/brain-api/src/aion_brain/api \
    packages/aion-sdk-python/src
)

test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "production-auth API router must remain absent" >&2
  exit 1
}

test ! -e services/brain-api/src/aion_brain/api/request_identity.py || {
  echo "request-identity API router must remain absent" >&2
  exit 1
}

./scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh
./scripts/production-auth-request-identity-check.sh
./scripts/production-auth-request-identity-no-go-regression.sh
run_inherited_gate ./scripts/production-auth-core-stabilization-check.sh
run_inherited_gate ./scripts/v02-production-auth-request-boundary-authorization-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

cat <<'SUMMARY'
v0.2 production auth request identity stabilization authorization result:
- AION-151-PA-0001: historical, inactive, consumed, expired, non-reusable
- AION-153-PA-0002: historical, inactive, consumed, expired, non-reusable
- AION-155-PA-0003: historical, inactive, consumed by AION-156 PR 66, expired, non-reusable
- AION-157-PA-0004: historical, consumed by AION-158 PR 68, expired, non-reusable
- AION-159-PA-0005: historical, consumed by AION-160 PR 70, expired, non-reusable
- AION-161-PA-0006: only active approved authorization
- candidate_id: production-auth-request-identity-boundary-stabilization
- workstream: production-auth-request-integration-hardening
- implementation_task: AION-158
- authorization_scope: disabled-request-identity-boundary-stabilization
- runtime implementation approved: false
- production auth runtime enabled: false
- identity verification enabled: false
- authenticated requests enabled: false
- endpoint, header, cookie, protected-material, provider, external-call, package, migration, SDK, CLI, connector, operator, module, sandbox, tag, and release approvals: false
v0.2 production auth request identity stabilization authorization PASS
SUMMARY

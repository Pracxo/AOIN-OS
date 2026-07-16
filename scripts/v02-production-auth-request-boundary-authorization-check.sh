#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

AION154_FEATURE_COMMIT="f001632ed0566bcf7facfe8905a2781ff9fa6ce9"
AION154_MERGE_COMMIT="85584ea1976fd6f2cb73a641464b3caf87481618"
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

required_docs=(
  docs/project-status.md
  docs/release/v02-production-auth-core-stabilization-closeout.md
  docs/release/v02-production-auth-request-boundary-authorization-transaction.md
  docs/release/v02-production-auth-request-boundary-scope.md
  docs/release/v02-production-auth-request-boundary-runtime-hold.md
  docs/release/v02-production-auth-request-boundary-authorization-checklist.md
  docs/release/v02-release-readiness-delta.md
  docs/adr/0146-v02-production-auth-request-boundary-authorization.md
)

required_json=(
  examples/release/v02-production-auth-core-stabilization-closeout.json
  examples/release/v02-production-auth-request-boundary-authorization.json
  examples/release/v02-production-auth-request-boundary-runtime-hold.json
  operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json
)

for file in "${required_docs[@]}" "${required_json[@]}"; do
  test -f "$file" || {
    echo "missing AION-155 request boundary authorization artifact: $file" >&2
    exit 1
  }
done

grep -q "0146-v02-production-auth-request-boundary-authorization.md" docs/adr/README.md || {
  echo "ADR 0146 is not indexed" >&2
  exit 1
}

grep -q "Current Project State" README.md || {
  echo "README missing Current Project State section" >&2
  exit 1
}

if grep -q "currently contains only the AION Brain v0.1 scaffold" README.md; then
  echo "README still contains obsolete v0.1-only scaffold statement" >&2
  exit 1
fi

git merge-base --is-ancestor "$AION154_FEATURE_COMMIT" HEAD || {
  echo "AION-154 feature commit is not in current history" >&2
  exit 1
}
git merge-base --is-ancestor "$AION154_MERGE_COMMIT" HEAD || {
  echo "AION-154 merge commit is not in current history" >&2
  exit 1
}

if command -v gh >/dev/null 2>&1 && gh pr view 64 --json state,baseRefName,headRefOid,mergeCommit >/tmp/aion155-pr64.json 2>/dev/null; then
  "$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/aion155-pr64.json").read_text())
assert payload["state"] == "MERGED"
assert payload["baseRefName"] == "main"
assert payload["headRefOid"] == "f001632ed0566bcf7facfe8905a2781ff9fa6ce9"
assert payload["mergeCommit"]["oid"] == "85584ea1976fd6f2cb73a641464b3caf87481618"
PY
else
  echo "WARN: gh PR evidence unavailable; verified AION-154 commits from git history"
fi

"$PYTHON_BIN" scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode check

./scripts/production-auth-core-stabilization-check.sh
./scripts/production-auth-core-stabilization-no-go-regression.sh
./scripts/v02-production-auth-stabilization-authorization-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  echo "AION-155 must not modify production-auth, kernel, API, SDK, or CLI implementation source: $file" >&2
  exit 1
done < <(
  changed_files \
    services/brain-api/src/aion_brain/production_auth \
    services/brain-api/src/aion_brain/contracts/production_auth.py \
    services/brain-api/src/aion_brain/config.py \
    services/brain-api/src/aion_brain/kernel \
    services/brain-api/src/aion_brain/api \
    packages/aion-sdk-python/src
)

cat <<'SUMMARY'
v0.2 production auth request boundary authorization result:
- AION-153-PA-0002: historical, inactive, consumed, expired, non-reusable
- AION-155-PA-0003: only active approved authorization
- candidate_id: production-auth-request-identity-boundary
- workstream: production-auth-request-integration
- implementation_task: AION-156
- authorization_scope: disabled-request-identity-boundary
- runtime implementation approved: false
- production auth runtime enabled: false
- identity verification enabled: false
- authenticated requests enabled: false
- endpoint, header, cookie, protected-material, provider, external-call, package, migration, SDK, CLI, connector, operator, module, sandbox, tag, and release approvals: false
v0.2 production auth request boundary authorization PASS
SUMMARY

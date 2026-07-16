#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

AION_152_MERGE_COMMIT="bc0614bcde19448b2a423614836bee3c06728c98"

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
  docs/release/v02-production-auth-core-implementation-closeout.md
  docs/release/v02-production-auth-stabilization-authorization-transaction.md
  docs/release/v02-production-auth-stabilization-explicit-approval-record.md
  docs/release/v02-production-auth-stabilization-scope.md
  docs/release/v02-production-auth-stabilization-runtime-guard-renewal.md
  docs/release/v02-production-auth-stabilization-authorization-evidence-matrix.md
  docs/release/v02-production-auth-stabilization-authorization-no-go.md
  docs/release/v02-production-auth-stabilization-authorization-checklist.md
  docs/adr/0144-v02-production-auth-core-stabilization-authorization.md
)

required_json=(
  examples/release/v02-production-auth-core-implementation-closeout.json
  examples/release/v02-production-auth-stabilization-authorization.json
  examples/release/v02-production-auth-stabilization-explicit-approval-record.json
  examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json
  examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json
  operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json
  operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json
)

for file in "${required_docs[@]}" "${required_json[@]}"; do
  test -f "$file" || {
    echo "missing AION-153 production auth stabilization authorization artifact: $file" >&2
    exit 1
  }
done

grep -q "0144-v02-production-auth-core-stabilization-authorization.md" docs/adr/README.md || {
  echo "ADR 0144 is not indexed" >&2
  exit 1
}

if git cat-file -e "${AION_152_MERGE_COMMIT}^{commit}" 2>/dev/null; then
  if git_ref_exists origin/main; then
    git merge-base --is-ancestor "$AION_152_MERGE_COMMIT" origin/main || {
      echo "AION-152 merge commit is not in origin/main history" >&2
      exit 1
    }
  elif git_ref_exists main; then
    git merge-base --is-ancestor "$AION_152_MERGE_COMMIT" main || {
      echo "AION-152 merge commit is not in main history" >&2
      exit 1
    }
  else
    echo "WARN: origin/main unavailable in this checkout; skipping AION-152 main ancestry confirmation"
  fi
else
  echo "WARN: AION-152 merge commit unavailable in this checkout; skipping shallow-checkout ancestry confirmation"
fi

python3 scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode check

if [[ "${AION_PRODUCTION_AUTH_REQUEST_IDENTITY_INHERITED_GATE:-}" = "1" ]]; then
  echo "PASS: v0.2 production-auth stabilization downstream gates deferred to AION-156 outer gate"
else
  ./scripts/production-auth-core-no-go-regression.sh
  AION_PRODUCTION_AUTH_CORE_RUNTIME_HOLD_SKIP_FULL_CHECK=1 ./scripts/production-auth-core-check.sh
  ./scripts/v02-production-auth-authorization-no-go-regression.sh
  AION_V02_PRODUCTION_AUTH_RUNTIME_GUARD_HOLD_SKIP_FULL_CHECK=1 ./scripts/v02-production-auth-authorization-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/v02-authorization-track-closeout.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  if aion154_is_scoped_stabilization_path "$file"; then
    continue
  fi
  if aion156_is_scoped_request_identity_path "$file"; then
    continue
  fi
  if aion158_is_scoped_request_identity_stabilization_path "$file"; then
    continue
  fi
  echo "AION-153 must not modify production-auth source, config, or kernel wiring: $file" >&2
  exit 1
done < <(
  changed_files \
    services/brain-api/src/aion_brain/production_auth \
    services/brain-api/src/aion_brain/contracts/production_auth.py \
    services/brain-api/src/aion_brain/config.py \
    services/brain-api/src/aion_brain/kernel/container.py \
    services/brain-api/src/aion_brain/kernel/diagnostics.py
)

if changed_files services/brain-api/src/aion_brain/api packages/aion-sdk-python/src | rg -n '.'; then
  echo "AION-153 must not modify API routes, SDK resources, or CLI source" >&2
  exit 1
fi

if changed_files | rg -n '(^|/)(migrations|alembic)/|(^|/).*migration.*\.(py|sql)$'; then
  echo "AION-153 must not add or change migrations" >&2
  exit 1
fi

if changed_files packages | rg -n '(^|/)(pyproject\.toml|package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb)$'; then
  echo "AION-153 must not add package files or lockfiles" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 production auth stabilization authorization check result:
- AION-151-PA-0001: approved historical, inactive, consumed, expired, non-reusable
- AION-153-PA-0002: approved historical, inactive, consumed, expired, non-reusable
- AION-155-PA-0003: approved historical, inactive, consumed, expired, non-reusable
- AION-157-PA-0004: only active approved authorization
- candidate_id: production-auth-core-stabilization
- workstream: production-auth-hardening
- implementation_task: AION-154
- authorization_scope: disabled-production-auth-core-stabilization
- runtime implementation approved: false
- production auth runtime enabled: false
- endpoint, storage, provider, external-call, package, migration, connector, operator, module, and sandbox approvals: false
v0.2 production auth stabilization authorization check PASS
SUMMARY

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

EXPECTED_AION_V01_SHA="105fe29348160a2218ac095cfffadcb6f234421f"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

ensure_aion_v01_tag() {
  if git_ref_exists "aion-v0.1.0^{commit}"; then
    return 0
  fi

  git fetch --quiet --no-tags origin "refs/tags/aion-v0.1.0:refs/tags/aion-v0.1.0" >/dev/null 2>&1 || true
  git_ref_exists "aion-v0.1.0^{commit}"
}

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_V02_PRODUCTION_AUTH_STABILIZATION_RUNTIME_GUARD_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/v02-production-auth-stabilization-authorization-check.sh
python3 scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode guard

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/check.sh
fi

tag_ref="unavailable"
if ensure_aion_v01_tag; then
  tag_ref="$(git rev-list -n 1 aion-v0.1.0)"
  if [[ "$tag_ref" != "$EXPECTED_AION_V01_SHA" ]]; then
    echo "aion-v0.1.0 must remain at $EXPECTED_AION_V01_SHA" >&2
    exit 1
  fi

  if git_ref_exists origin/main; then
    git merge-base --is-ancestor aion-v0.1.0 origin/main || {
      echo "aion-v0.1.0 must remain in origin/main history" >&2
      exit 1
    }
  elif git_ref_exists main; then
    git merge-base --is-ancestor aion-v0.1.0 main || {
      echo "aion-v0.1.0 must remain in main history" >&2
      exit 1
    }
  else
    echo "WARN: origin/main unavailable in this checkout; skipping non-release tag ancestry confirmation"
  fi
else
  echo "aion-v0.1.0 tag is missing" >&2
  exit 1
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-153" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-153" >&2
  exit 1
fi

cat <<SUMMARY
v0.2 production auth stabilization runtime guard hold result:
- authorization_transaction_id: AION-153-PA-0002
- runtime_guard_hold_active: true
- runtime_no_go_status: true
- runtime_implementation_approved: false
- production_auth_runtime_enabled: false
- aion_v0_1_0: ${tag_ref}
v0.2 production auth stabilization runtime guard hold PASS
SUMMARY

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

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
    git ls-files --others --exclude-standard -- "$@"
  } | sort -u
}

required_files=(
  services/brain-api/src/aion_brain/contracts/production_auth.py
  services/brain-api/src/aion_brain/production_auth/__init__.py
  services/brain-api/src/aion_brain/production_auth/config.py
  services/brain-api/src/aion_brain/production_auth/core.py
  services/brain-api/src/aion_brain/production_auth/policy.py
  services/brain-api/src/aion_brain/production_auth/audit.py
  services/brain-api/src/aion_brain/production_auth/provenance.py
  services/brain-api/src/aion_brain/production_auth/diagnostics.py
  docs/auth/production-auth-core.md
  docs/auth/production-auth-core-runtime-boundary.md
  docs/auth/production-auth-policy-audit.md
  docs/release/v02-production-auth-core-implementation.md
  docs/release/v02-production-auth-core-runtime-hold.md
  docs/release/v02-production-auth-core-evidence-matrix.md
  docs/release/v02-production-auth-core-no-go.md
  docs/release/v02-production-auth-core-checklist.md
  docs/adr/0143-v02-disabled-production-auth-core-implementation.md
  examples/auth/production-auth-core-config.json
  examples/auth/production-auth-core-status.json
  examples/auth/production-auth-policy-decision.json
  examples/auth/production-auth-audit-event.json
  examples/auth/production-auth-provenance-record.json
  operator-console-static/demo-data/production-auth-core-status.json
  operator-console-static/demo-data/production-auth-runtime-hold.json
  scripts/production-auth-core-check.sh
  scripts/production-auth-core-runtime-hold.sh
  scripts/production-auth-core-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-152 production-auth core artifact: $file" >&2
    exit 1
  }
done

grep -q "0143-v02-disabled-production-auth-core-implementation.md" docs/adr/README.md || {
  echo "ADR 0143 is not indexed" >&2
  exit 1
}

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
json_files = [
    "examples/auth/production-auth-core-config.json",
    "examples/auth/production-auth-core-status.json",
    "examples/auth/production-auth-policy-decision.json",
    "examples/auth/production-auth-audit-event.json",
    "examples/auth/production-auth-provenance-record.json",
    "operator-console-static/demo-data/production-auth-core-status.json",
    "operator-console-static/demo-data/production-auth-runtime-hold.json",
]
required_true = {
    "production_auth_core_implemented",
    "runtime_guard_hold_active",
    "runtime_no_go_status",
}
required_false = {
    "runtime_implementation_approved",
    "production_auth_runtime_enabled",
    "runtime_enablement_guard_release_approved",
    "runtime_enablement_guard_final_lock_release_approved",
    "runtime_enablement_master_lock_release_approved",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "callback_endpoint_enabled",
    "credential_storage_enabled",
    "password_storage_enabled",
    "token_issuance_enabled",
    "token_storage_enabled",
    "session_creation_enabled",
    "session_storage_enabled",
    "cookie_issuance_enabled",
    "cookie_session_persistence_enabled",
    "external_identity_provider_enabled",
    "oauth_runtime_enabled",
    "oidc_runtime_enabled",
    "saml_runtime_enabled",
    "external_calls_enabled",
    "network_client_enabled",
    "provider_sdk_enabled",
    "operator_write_execution_enabled",
    "connector_runtime_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "package_files_added",
    "lockfiles_added",
    "migrations_added",
    "runtime_api_routes_added",
    "v02_tag_created",
    "v02_release_created",
}
unsafe_values = (
    "sk-",
    "ghp_",
    "xoxb-",
    "bearer ",
    "-----begin private key-----",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
)


def walk_values(value: object, path: Path) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            walk_values(nested, path)
    elif isinstance(value, list):
        for item in value:
            walk_values(item, path)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in unsafe_values:
            if marker in lowered:
                raise SystemExit(f"unsafe protected material marker in {path}: {marker}")


for relative in json_files:
    path = root / relative
    payload = json.loads(path.read_text())
    if payload.get("synthetic") is not True:
        raise SystemExit(f"synthetic must be true: {relative}")
    if payload.get("read_only") is not True:
        raise SystemExit(f"read_only must be true: {relative}")
    if payload.get("authorization_transaction_id") != "AION-151-PA-0001":
        raise SystemExit(f"authorization transaction mismatch: {relative}")
    if payload.get("authorization_scope") != "disabled-production-auth-core":
        raise SystemExit(f"authorization scope mismatch: {relative}")
    if payload.get("implementation_task") != "AION-152":
        raise SystemExit(f"implementation task mismatch: {relative}")
    if payload.get("authorization_consumed_by_task") != "AION-152":
        raise SystemExit(f"authorization consumption mismatch: {relative}")
    if payload.get("authorization_reusable") is not False:
        raise SystemExit(f"authorization_reusable must be false: {relative}")
    if payload.get("production_auth_core_state") != "implemented_disabled":
        raise SystemExit(f"production auth core state mismatch: {relative}")
    for key in required_true:
        if payload.get(key) is not True:
            raise SystemExit(f"{key} must be true in {relative}")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{key} must be false in {relative}")
    walk_values(payload, path)
PY

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_production_auth_contracts.py \
  services/brain-api/tests/test_production_auth_config.py \
  services/brain-api/tests/test_production_auth_core.py \
  services/brain-api/tests/test_production_auth_policy.py \
  services/brain-api/tests/test_production_auth_audit_provenance.py \
  services/brain-api/tests/test_production_auth_diagnostics.py \
  services/brain-api/tests/test_kernel_production_auth_wiring.py \
  services/brain-api/tests/test_production_auth_no_runtime_routes.py \
  -q

./scripts/v02-production-auth-authorization-check.sh
"$PYTHON_BIN" scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode no-go

test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "production auth API router must not exist" >&2
  exit 1
}

changed_api_files="$(
  changed_files services/brain-api/src/aion_brain/api
)"
if [[ -n "$changed_api_files" ]]; then
  if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(production-auth|auth/production|login|logout|callback|oauth|oidc|saml|token|credentials)' $changed_api_files; then
    echo "production-auth runtime route surface found in changed API files" >&2
    exit 1
  fi
fi

if changed_files packages/aion-sdk-python/src | rg -n '.'; then
  echo "SDK runtime resources must not change for AION-152" >&2
  exit 1
fi

if changed_files packages | rg -n '(^|/)(pyproject\.toml|package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb)$'; then
  echo "package files or lockfiles must not change for AION-152" >&2
  exit 1
fi

if changed_files | rg -n '(^|/)(migrations|alembic)/|(^|/).*migration.*\.(py|sql)$'; then
  echo "migrations must not change for AION-152" >&2
  exit 1
fi

./scripts/auth-design-check.sh
./scripts/auth-runtime-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

echo "production auth core check PASS"

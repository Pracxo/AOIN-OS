#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_PRODUCTION_AUTH_CORE_STABILIZATION_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/production-auth-core-stabilization-check.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
payload = json.loads(
    (root / "operator-console-static/demo-data/production-auth-core-stabilization-runtime-hold.json").read_text()
)
required_false = [
    "production_auth_runtime_enabled",
    "runtime_implementation_approved",
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
]
if payload.get("runtime_guard_hold_active") is not True:
    raise SystemExit("runtime_guard_hold_active must be true")
if payload.get("runtime_no_go_status") is not True:
    raise SystemExit("runtime_no_go_status must be true")
for key in required_false:
    if payload.get(key) is not False:
        raise SystemExit(f"{key} must be false")
PY

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/check.sh
fi

tag_ref="$(aion_confirm_immutable_v01_tag_history)"

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-154" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-154" >&2
  exit 1
fi

cat <<SUMMARY
production auth core stabilization runtime hold result:
- runtime_guard_hold_active: true
- runtime_no_go_status: true
- production_auth_runtime_enabled: false
- aion_v0_1_0: ${tag_ref}
production auth core stabilization runtime hold PASS
SUMMARY

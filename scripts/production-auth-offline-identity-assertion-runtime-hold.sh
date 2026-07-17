#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/production-auth-offline-identity-assertion-check.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
payloads = [
    json.loads((root / "operator-console-static/demo-data/offline-identity-assertion-runtime-hold.json").read_text()),
    json.loads((root / "operator-console-static/demo-data/offline-identity-assertion-verification.json").read_text()),
]
required_false = [
    "request_authenticated",
    "actor_context_applied",
    "request_identity_context_applied",
    "runtime_effect",
    "runtime_integration_allowed",
    "runtime_private_key_material_present",
    "replay_check_performed",
    "identity_assertion_header_parsing_enabled",
    "authorization_header_parsing_enabled",
    "cookie_parsing_enabled",
    "identity_assertion_middleware_registered",
    "external_identity_provider_enabled",
    "jwks_network_fetch_enabled",
    "provider_discovery_enabled",
    "external_calls_enabled",
    "identity_assertion_endpoint_enabled",
    "runtime_api_routes_added",
    "openapi_security_scheme_added",
    "sdk_runtime_resource_added",
    "cli_runtime_command_added",
    "new_package_manifest_added",
    "lockfiles_added",
    "migrations_added",
    "connector_runtime_enabled",
    "operator_write_execution_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "v02_tag_created",
    "v02_release_created",
]
for payload in payloads:
    assert payload["authorization_transaction_id"] == "AION-161-PA-0006"
    assert payload["implementation_task"] == "AION-162"
    assert payload["authorization_scope"] == "offline-ed25519-identity-assertion-verification"
    assert payload["offline_identity_assertion_verification_implemented"] is True
    assert payload["offline_identity_assertion_verification_state"] == "implemented_unintegrated"
    assert payload["replay_protection_required_before_request_integration"] is True
    for key in required_false:
        if key in payload and payload[key] is not False:
            raise SystemExit(f"{key} must be false")
PY

test "$(aion_ensure_immutable_v01_tag)" = "105fe29348160a2218ac095cfffadcb6f234421f"
test -z "$(git tag --list 'v0.2*')"
test -z "$(git tag --list 'aion-v0.2*')"
gh release view v0.2 >/dev/null 2>&1 && exit 1 || true
gh release view aion-v0.2 >/dev/null 2>&1 && exit 1 || true

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "production auth offline identity assertion runtime hold PASS"

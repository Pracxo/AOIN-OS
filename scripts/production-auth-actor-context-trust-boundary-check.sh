#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 "$@"
}

required_files=(
  services/brain-api/src/aion_brain/contracts/actor_context_resolution.py
  services/brain-api/src/aion_brain/production_auth/actor_context.py
  services/brain-api/src/aion_brain/production_auth/actor_context_evidence.py
  docs/auth/actor-context-trust-boundary.md
  docs/auth/development-identity-simulation.md
  docs/release/v02-actor-context-trust-boundary-remediation.md
  docs/release/v02-actor-context-trust-boundary-runtime-hold.md
  docs/release/v02-actor-context-trust-boundary-evidence-matrix.md
  docs/release/v02-actor-context-trust-boundary-no-go.md
  docs/release/v02-actor-context-trust-boundary-checklist.md
  docs/adr/0151-v02-actor-context-trust-boundary-remediation.md
  examples/auth/actor-context-anonymous-resolution.json
  examples/auth/actor-context-request-identity-resolution.json
  examples/auth/actor-context-development-simulation.json
  examples/auth/actor-context-resolution-audit-event.json
  examples/auth/actor-context-resolution-provenance.json
  examples/auth/actor-context-resolution-diagnostics.json
  operator-console-static/demo-data/actor-context-trust-boundary.json
  operator-console-static/demo-data/actor-context-runtime-hold.json
  scripts/production-auth-actor-context-trust-boundary-check.sh
  scripts/production-auth-actor-context-trust-boundary-runtime-hold.sh
  scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-160 actor-context artifact: $file" >&2
    exit 1
  }
done

grep -q "0151-v02-actor-context-trust-boundary-remediation.md" docs/adr/README.md || {
  echo "ADR 0151 is not indexed" >&2
  exit 1
}

grep -F "AION-160 actor-context trust-boundary remediation implemented" docs/project-status.md >/dev/null || \
grep -F "Fail-closed ActorContext resolution" docs/project-status.md >/dev/null || {
  echo "project status does not describe AION-160 implementation" >&2
  exit 1
}

dev_auth="services/brain-api/src/aion_brain/identity/dev_auth.py"
grep -F 'return settings.env == "development" and settings.dev_auth_enabled is True' "$dev_auth" >/dev/null || {
  echo "exact development identity simulation gate is missing" >&2
  exit 1
}

for header in \
  X-AION-Actor-ID \
  X-AION-Workspace-ID \
  X-AION-Roles \
  X-AION-Permissions \
  X-AION-Security-Scope; do
  grep -F "$header" docs/auth/actor-context-trust-boundary.md >/dev/null || {
    echo "actor-context trust-boundary doc missing header: $header" >&2
    exit 1
  }
done

test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "new production-auth API router is forbidden" >&2
  exit 1
}
test ! -e services/brain-api/src/aion_brain/api/request_identity.py || {
  echo "new request-identity API router is forbidden" >&2
  exit 1
}
test ! -e services/brain-api/src/aion_brain/api/actor_context.py || {
  echo "new actor-context API router is forbidden" >&2
  exit 1
}

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from aion_brain.config import Settings
from aion_brain.contracts.actor_context_resolution import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    IMPLEMENTATION_TASK,
    ActorContextResolutionAuditEvent,
    ActorContextResolutionDiagnosticSnapshot,
    ActorContextResolutionInput,
    ActorContextResolutionProvenanceRecord,
)
from aion_brain.identity.dev_auth import development_identity_simulation_enabled
from aion_brain.kernel.app_factory import create_app
from aion_brain.kernel.container import KernelContainer

root = Path(sys.argv[1])
assert AUTHORIZATION_TRANSACTION_ID == "AION-159-PA-0005"
assert IMPLEMENTATION_TASK == "AION-160"
assert AUTHORIZATION_SCOPE == "fail-closed-actor-context-resolution"

gate_matrix = {
    ("development", True): True,
    ("development", False): False,
    ("production", True): False,
    ("staging", True): False,
    ("test", True): False,
    ("ci", True): False,
    ("local", True): False,
    ("", True): False,
}
for (env, enabled), expected in gate_matrix.items():
    settings = Settings(env=env, dev_auth_enabled=enabled)
    if development_identity_simulation_enabled(settings) is not expected:
        raise SystemExit(f"development gate mismatch for env={env!r}, enabled={enabled}")

required_true = [
    "actor_context_trust_boundary_remediated",
    "authorization_expires_on_aion_160_merge",
    "development_identity_simulation_available",
    "request_identity_context_precedence",
    "request_context_correlation_projection",
    "request_context_identity_metadata_ignored",
    "non_development_identity_headers_ignored",
    "runtime_no_go_status",
]
required_false = [
    "authenticated_actor_context_enabled",
    "identity_verification_enabled",
    "authenticated_requests_enabled",
    "production_auth_runtime_enabled",
    "runtime_effect",
    "runtime_implementation_approved",
    "runtime_enablement_guard_release_approved",
    "production_actor_header_trust_enabled",
    "production_workspace_header_trust_enabled",
    "production_role_header_trust_enabled",
    "production_permission_header_trust_enabled",
    "production_security_scope_header_trust_enabled",
    "authorization_header_parsing_enabled",
    "cookie_parsing_enabled",
    "credential_verification_enabled",
    "password_verification_enabled",
    "token_parsing_enabled",
    "token_issuance_enabled",
    "token_storage_enabled",
    "token_refresh_enabled",
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
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "callback_endpoint_enabled",
    "token_endpoint_enabled",
    "session_endpoint_enabled",
    "credential_endpoint_enabled",
    "openapi_security_scheme_added",
    "runtime_api_routes_added",
    "sdk_runtime_resource_added",
    "cli_runtime_command_added",
    "package_files_added",
    "lockfiles_added",
    "migrations_added",
    "v02_tag_created",
    "v02_release_created",
]
json_paths = [
    "examples/auth/actor-context-anonymous-resolution.json",
    "examples/auth/actor-context-request-identity-resolution.json",
    "operator-console-static/demo-data/actor-context-trust-boundary.json",
    "operator-console-static/demo-data/actor-context-runtime-hold.json",
]
for relative in json_paths:
    payload = json.loads((root / relative).read_text())
    if payload.get("authorization_transaction_id") != "AION-159-PA-0005":
        raise SystemExit(f"{relative}: authorization mismatch")
    if payload.get("implementation_task") != "AION-160":
        raise SystemExit(f"{relative}: implementation task mismatch")
    if payload.get("authorization_scope") != "fail-closed-actor-context-resolution":
        raise SystemExit(f"{relative}: scope mismatch")
    if payload.get("actor_context_resolution_state") != "implemented_fail_closed":
        raise SystemExit(f"{relative}: resolution state mismatch")
    for key in required_true:
        if key in payload and payload.get(key) is not True:
            raise SystemExit(f"{relative}: {key} must be true")
    for key in required_false:
        if key in payload and payload.get(key) is not False:
            raise SystemExit(f"{relative}: {key} must be false")

ActorContextResolutionInput(metadata={"safe": {"nested": ("value",)}})
ActorContextResolutionAuditEvent(**{
    key: value
    for key, value in json.loads((root / "examples/auth/actor-context-resolution-audit-event.json").read_text()).items()
    if key in ActorContextResolutionAuditEvent.model_fields
})
ActorContextResolutionProvenanceRecord(**{
    key: value
    for key, value in json.loads((root / "examples/auth/actor-context-resolution-provenance.json").read_text()).items()
    if key in ActorContextResolutionProvenanceRecord.model_fields
})
ActorContextResolutionDiagnosticSnapshot(**{
    key: value
    for key, value in json.loads((root / "examples/auth/actor-context-resolution-diagnostics.json").read_text()).items()
    if key in ActorContextResolutionDiagnosticSnapshot.model_fields
})

container = KernelContainer(
    Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_DEFAULT_SEMANTIC_ADAPTER="in_memory",
        AION_GRAPH_MEMORY_ADAPTER="in_memory",
    )
)
app = create_app(container)
if "securitySchemes" in app.openapi().get("components", {}):
    raise SystemExit("OpenAPI security schemes must remain absent")
PY

./scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused pytest and inherited gates deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_dev_auth_context.py \
    services/brain-api/tests/test_actor_context_in_brain_routes.py \
    services/brain-api/tests/test_local_auth_context.py \
    services/brain-api/tests/test_request_identity_contracts.py \
    services/brain-api/tests/test_request_identity_middleware.py \
    services/brain-api/tests/test_request_identity_stabilization_concurrency.py \
    services/brain-api/tests/test_actor_context_resolution_contracts.py \
    services/brain-api/tests/test_actor_context_fail_closed.py \
    services/brain-api/tests/test_actor_context_development_simulation.py \
    services/brain-api/tests/test_actor_context_request_identity_precedence.py \
    services/brain-api/tests/test_actor_context_request_context_correlation.py \
    services/brain-api/tests/test_actor_context_privilege_escalation.py \
    services/brain-api/tests/test_actor_context_route_integration.py \
    services/brain-api/tests/test_actor_context_payload_metadata.py \
    services/brain-api/tests/test_actor_context_audit_provenance.py \
    services/brain-api/tests/test_actor_context_concurrency.py \
    services/brain-api/tests/test_actor_context_redaction.py \
    services/brain-api/tests/test_actor_context_diagnostics.py \
    services/brain-api/tests/test_actor_context_no_runtime_surface.py \
    services/brain-api/tests/test_actor_context_trust_boundary_docs.py \
    -q

  run_inherited_gate ./scripts/production-auth-request-identity-stabilization-check.sh
  run_inherited_gate ./scripts/production-auth-request-identity-stabilization-no-go-regression.sh
  run_inherited_gate ./scripts/v02-actor-context-trust-boundary-authorization-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

echo "production auth actor context trust boundary PASS"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 \
    AION_PRODUCTION_AUTH_REQUEST_IDENTITY_INHERITED_GATE=1 \
    "$@"
}

required_files=(
  services/brain-api/src/aion_brain/contracts/request_identity.py
  services/brain-api/src/aion_brain/production_auth/verifier.py
  services/brain-api/src/aion_brain/production_auth/request_boundary.py
  services/brain-api/src/aion_brain/production_auth/request_middleware.py
  services/brain-api/src/aion_brain/production_auth/request_evidence.py
  services/brain-api/tests/test_request_identity_pure_asgi_middleware.py
  services/brain-api/tests/test_request_identity_streaming_preservation.py
  services/brain-api/tests/test_request_identity_request_body_preservation.py
  services/brain-api/tests/test_request_identity_cancellation.py
  services/brain-api/tests/test_request_identity_client_disconnect.py
  services/brain-api/tests/test_request_identity_non_http_scopes.py
  services/brain-api/tests/test_request_identity_state_integrity.py
  services/brain-api/tests/test_request_identity_duplicate_registration.py
  services/brain-api/tests/test_request_identity_stabilization_concurrency.py
  services/brain-api/tests/test_request_identity_stabilization_idempotency.py
  services/brain-api/tests/test_request_identity_stabilization_diagnostics.py
  services/brain-api/tests/test_request_identity_stabilization_performance.py
  docs/auth/request-identity-stabilization.md
  docs/auth/request-identity-asgi-middleware.md
  docs/release/v02-production-auth-request-identity-stabilization.md
  docs/release/v02-production-auth-request-identity-stabilization-runtime-hold.md
  docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md
  docs/release/v02-production-auth-request-identity-stabilization-no-go.md
  docs/release/v02-production-auth-request-identity-stabilization-checklist.md
  docs/adr/0149-v02-production-auth-request-identity-stabilization.md
  examples/auth/request-identity-stabilized-boundary-status.json
  examples/auth/request-identity-stabilized-disabled-context.json
  examples/auth/request-identity-stabilized-audit-event.json
  examples/auth/request-identity-stabilized-provenance-record.json
  examples/auth/request-identity-stabilized-diagnostics.json
  operator-console-static/demo-data/production-auth-request-identity-stabilization.json
  operator-console-static/demo-data/production-auth-request-identity-stabilization-runtime-hold.json
  scripts/production-auth-request-identity-stabilization-check.sh
  scripts/production-auth-request-identity-stabilization-runtime-hold.sh
  scripts/production-auth-request-identity-stabilization-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-158 request identity stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0149-v02-production-auth-request-identity-stabilization.md" docs/adr/README.md || {
  echo "ADR 0149 is not indexed" >&2
  exit 1
}

request_middleware="services/brain-api/src/aion_brain/production_auth/request_middleware.py"
if rg -n 'BaseHTTPMiddleware|from +fastapi +import +(Request|Response)|Request\(|Response\(' "$request_middleware"; then
  echo "request identity middleware must remain pure ASGI" >&2
  exit 1
fi

if rg -n 'scope\[("headers"|'\''headers'\'')\]|scope\[("query_string"|'\''query_string'\'')\]|scope\[("client"|'\''client'\'')\]|scope\[("server"|'\''server'\'')\]' "$request_middleware"; then
  echo "request identity middleware must not inspect HTTP material from scope" >&2
  exit 1
fi

if rg -n 'request\.(headers|cookies|query_params|body)\b|receive_wrapper|wrapped_receive|send_wrapper|wrapped_send|body_chunks|response_body|buffered_response' "$request_middleware"; then
  echo "request identity middleware must not access HTTP material or wrap ASGI channels" >&2
  exit 1
fi

grep -q "await self.app(scope, receive, send)" "$request_middleware" || {
  echo "request identity middleware must pass receive and send unchanged" >&2
  exit 1
}

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from aion_brain.contracts.request_identity import (
    RequestIdentityAuditEvent,
    RequestIdentityBoundaryStatus,
    RequestIdentityContext,
    RequestIdentityDiagnosticSnapshot,
    RequestIdentityProvenanceRecord,
)
from aion_brain.config import Settings
from aion_brain.kernel.app_factory import create_app
from aion_brain.kernel.container import KernelContainer

root = Path(sys.argv[1])
models = [
    ("examples/auth/request-identity-stabilized-boundary-status.json", RequestIdentityBoundaryStatus),
    ("examples/auth/request-identity-stabilized-disabled-context.json", RequestIdentityContext),
    ("examples/auth/request-identity-stabilized-audit-event.json", RequestIdentityAuditEvent),
    ("examples/auth/request-identity-stabilized-provenance-record.json", RequestIdentityProvenanceRecord),
    ("examples/auth/request-identity-stabilized-diagnostics.json", RequestIdentityDiagnosticSnapshot),
]
for relative, model in models:
    payload = json.loads((root / relative).read_text())
    parsed = model(**payload)
    if parsed.stabilization_authorization_transaction_id != "AION-157-PA-0004":
        raise SystemExit(f"{relative}: stabilization authorization mismatch")
    if parsed.stabilization_authorization_scope != "disabled-request-identity-boundary-stabilization":
        raise SystemExit(f"{relative}: stabilization scope mismatch")
    if parsed.request_identity_middleware_implementation != "pure_asgi":
        raise SystemExit(f"{relative}: middleware implementation mismatch")
    if parsed.fingerprint is None or len(parsed.fingerprint) != 64:
        raise SystemExit(f"{relative}: missing fingerprint")

required_true = [
    "synthetic",
    "read_only",
    "request_identity_boundary_implemented",
    "streaming_passthrough",
    "request_body_passthrough",
    "cancellation_propagation",
    "non_http_scope_bypass",
    "duplicate_registration_prevented",
    "runtime_guard_hold_active",
    "runtime_no_go_status",
    "stabilization_authorization_expires_on_aion_158_merge",
]
required_false = [
    "request_identity_boundary_default_enabled",
    "stabilization_authorization_reusable",
    "identity_verification_enabled",
    "authenticated_requests_enabled",
    "production_auth_runtime_enabled",
    "runtime_effect",
    "runtime_implementation_approved",
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
    "operator_write_execution_enabled",
    "connector_runtime_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "package_files_added",
    "lockfiles_added",
    "migrations_added",
    "v02_tag_created",
    "v02_release_created",
]
for relative in [
    "operator-console-static/demo-data/production-auth-request-identity-stabilization.json",
    "operator-console-static/demo-data/production-auth-request-identity-stabilization-runtime-hold.json",
]:
    payload = json.loads((root / relative).read_text())
    for key in required_true:
        if payload.get(key) is not True:
            raise SystemExit(f"{relative}: {key} must be true")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{relative}: {key} must be false")
    if payload.get("stabilization_authorization_transaction_id") != "AION-157-PA-0004":
        raise SystemExit(f"{relative}: stabilization transaction mismatch")
    if payload.get("request_identity_middleware_implementation") != "pure_asgi":
        raise SystemExit(f"{relative}: pure ASGI marker missing")

container = KernelContainer(
    Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_DEFAULT_SEMANTIC_ADAPTER="in_memory",
        AION_GRAPH_MEMORY_ADAPTER="in_memory",
    )
)
container.settings.production_auth_request_boundary_enabled = True
app = create_app(container)
middleware_count = sum(
    1
    for item in app.user_middleware
    if item.cls.__name__ == "ProductionAuthRequestIdentityMiddleware"
)
if middleware_count != 1:
    raise SystemExit("enabled app must register exactly one request identity middleware")
if "securitySchemes" in app.openapi().get("components", {}):
    raise SystemExit("request identity stabilization must not add OpenAPI security")
PY

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_request_identity_contracts.py \
  services/brain-api/tests/test_request_identity_verifiers.py \
  services/brain-api/tests/test_request_identity_boundary.py \
  services/brain-api/tests/test_request_identity_middleware.py \
  services/brain-api/tests/test_request_identity_app_factory.py \
  services/brain-api/tests/test_request_identity_audit_provenance.py \
  services/brain-api/tests/test_request_identity_concurrency.py \
  services/brain-api/tests/test_request_identity_redaction.py \
  services/brain-api/tests/test_request_identity_config.py \
  services/brain-api/tests/test_request_identity_no_runtime_routes.py \
  services/brain-api/tests/test_request_identity_pure_asgi_middleware.py \
  services/brain-api/tests/test_request_identity_streaming_preservation.py \
  services/brain-api/tests/test_request_identity_request_body_preservation.py \
  services/brain-api/tests/test_request_identity_cancellation.py \
  services/brain-api/tests/test_request_identity_client_disconnect.py \
  services/brain-api/tests/test_request_identity_non_http_scopes.py \
  services/brain-api/tests/test_request_identity_state_integrity.py \
  services/brain-api/tests/test_request_identity_duplicate_registration.py \
  services/brain-api/tests/test_request_identity_stabilization_concurrency.py \
  services/brain-api/tests/test_request_identity_stabilization_idempotency.py \
  services/brain-api/tests/test_request_identity_stabilization_diagnostics.py \
  services/brain-api/tests/test_request_identity_stabilization_performance.py \
  -q

./scripts/production-auth-request-identity-stabilization-no-go-regression.sh
run_inherited_gate ./scripts/production-auth-request-identity-check.sh
run_inherited_gate ./scripts/production-auth-core-stabilization-check.sh
run_inherited_gate ./scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "production-auth API router must remain absent" >&2
  exit 1
}

test ! -e services/brain-api/src/aion_brain/api/request_identity.py || {
  echo "request-identity API router must remain absent" >&2
  exit 1
}

test -z "$(git diff --name-only origin/main...HEAD -- packages/aion-sdk-python/src)" || {
  echo "SDK runtime source changes are forbidden for AION-158" >&2
  exit 1
}

echo "production auth request identity stabilization PASS"

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
  services/brain-api/tests/test_request_identity_contracts.py
  services/brain-api/tests/test_request_identity_verifiers.py
  services/brain-api/tests/test_request_identity_boundary.py
  services/brain-api/tests/test_request_identity_middleware.py
  services/brain-api/tests/test_request_identity_app_factory.py
  services/brain-api/tests/test_request_identity_audit_provenance.py
  services/brain-api/tests/test_request_identity_concurrency.py
  services/brain-api/tests/test_request_identity_redaction.py
  services/brain-api/tests/test_request_identity_config.py
  services/brain-api/tests/test_request_identity_no_runtime_routes.py
  docs/auth/request-identity-boundary.md
  docs/auth/request-identity-runtime-boundary.md
  docs/release/v02-production-auth-request-identity-boundary-implementation.md
  docs/release/v02-production-auth-request-identity-boundary-runtime-hold.md
  docs/release/v02-production-auth-request-identity-boundary-evidence-matrix.md
  docs/release/v02-production-auth-request-identity-boundary-no-go.md
  docs/release/v02-production-auth-request-identity-boundary-checklist.md
  docs/adr/0147-v02-disabled-production-auth-request-identity-boundary.md
  examples/auth/request-identity-boundary-status.json
  examples/auth/request-identity-disabled-context.json
  examples/auth/request-identity-verification-result.json
  examples/auth/request-identity-audit-event.json
  examples/auth/request-identity-provenance-record.json
  operator-console-static/demo-data/production-auth-request-identity-boundary.json
  operator-console-static/demo-data/production-auth-request-identity-runtime-hold.json
  scripts/production-auth-request-identity-check.sh
  scripts/production-auth-request-identity-runtime-hold.sh
  scripts/production-auth-request-identity-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-156 request identity artifact: $file" >&2
    exit 1
  }
done

grep -q "0147-v02-disabled-production-auth-request-identity-boundary.md" docs/adr/README.md || {
  echo "ADR 0147 is not indexed" >&2
  exit 1
}

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from aion_brain.config import Settings
from aion_brain.contracts.request_identity import (
    RequestIdentityAuditEvent,
    RequestIdentityBoundaryStatus,
    RequestIdentityContext,
    RequestIdentityProvenanceRecord,
    RequestIdentityVerificationResult,
)
from aion_brain.kernel.app_factory import create_app
from aion_brain.kernel.container import KernelContainer

root = Path(sys.argv[1])
model_examples = [
    ("examples/auth/request-identity-boundary-status.json", RequestIdentityBoundaryStatus),
    ("examples/auth/request-identity-disabled-context.json", RequestIdentityContext),
    ("examples/auth/request-identity-verification-result.json", RequestIdentityVerificationResult),
    ("examples/auth/request-identity-audit-event.json", RequestIdentityAuditEvent),
    ("examples/auth/request-identity-provenance-record.json", RequestIdentityProvenanceRecord),
]
for relative, model in model_examples:
    payload = json.loads((root / relative).read_text())
    parsed = model(**payload)
    if parsed.schema_version != "request-identity/v1":
        raise SystemExit(f"{relative}: schema_version mismatch")
    if parsed.boundary_version != "request-identity-boundary/v1":
        raise SystemExit(f"{relative}: boundary_version mismatch")
    if parsed.fingerprint is None or len(parsed.fingerprint) != 64:
        raise SystemExit(f"{relative}: missing fingerprint")

for relative in [
    "operator-console-static/demo-data/production-auth-request-identity-boundary.json",
    "operator-console-static/demo-data/production-auth-request-identity-runtime-hold.json",
]:
    payload = json.loads((root / relative).read_text())
    required_true = [
        "synthetic",
        "read_only",
        "request_identity_boundary_implemented",
        "runtime_guard_hold_active",
        "runtime_no_go_status",
    ]
    required_false = [
        "request_identity_boundary_default_enabled",
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
        "runtime_api_routes_added",
        "package_files_added",
        "lockfiles_added",
        "migrations_added",
        "v02_tag_created",
        "v02_release_created",
    ]
    for key in required_true:
        if payload.get(key) is not True:
            raise SystemExit(f"{relative}: {key} must be true")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{relative}: {key} must be false")
    if payload.get("authorization_transaction_id") != "AION-155-PA-0003":
        raise SystemExit(f"{relative}: authorization transaction mismatch")
    if payload.get("implementation_task") != "AION-156":
        raise SystemExit(f"{relative}: implementation task mismatch")
    if payload.get("authorization_scope") != "disabled-request-identity-boundary":
        raise SystemExit(f"{relative}: authorization scope mismatch")

if Settings(_env_file=None).production_auth_request_boundary_enabled is not False:
    raise SystemExit("request boundary setting must default false")
enabled_container = KernelContainer(
    Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_DEFAULT_SEMANTIC_ADAPTER="in_memory",
        AION_GRAPH_MEMORY_ADAPTER="in_memory",
    )
)
enabled_container.settings.production_auth_request_boundary_enabled = True
enabled_app = create_app(enabled_container)
if enabled_app.state.aion_request_identity_boundary_present is not True:
    raise SystemExit("enabled app must register request identity boundary")
if enabled_app.state.aion_request_identity_boundary_mode != "observe_only_disabled":
    raise SystemExit("enabled app must remain observe-only")
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
  -q

./scripts/production-auth-request-identity-no-go-regression.sh
run_inherited_gate ./scripts/production-auth-core-stabilization-check.sh
./scripts/production-auth-core-stabilization-no-go-regression.sh
run_inherited_gate ./scripts/v02-production-auth-request-boundary-authorization-check.sh
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

echo "production auth request identity check PASS"

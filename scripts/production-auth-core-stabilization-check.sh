#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

required_files=(
  services/brain-api/src/aion_brain/production_auth/canonical.py
  services/brain-api/src/aion_brain/production_auth/reason_codes.py
  services/brain-api/src/aion_brain/contracts/production_auth.py
  docs/auth/production-auth-core-stabilization.md
  docs/auth/production-auth-canonical-evidence.md
  docs/release/v02-production-auth-core-stabilization.md
  docs/release/v02-production-auth-core-stabilization-evidence-matrix.md
  docs/release/v02-production-auth-core-stabilization-runtime-hold.md
  docs/release/v02-production-auth-core-stabilization-no-go.md
  docs/release/v02-production-auth-core-stabilization-checklist.md
  docs/adr/0145-v02-production-auth-core-stabilization.md
  examples/auth/production-auth-stabilized-core-status.json
  examples/auth/production-auth-stabilized-policy-decision.json
  examples/auth/production-auth-stabilized-audit-event.json
  examples/auth/production-auth-stabilized-provenance-record.json
  examples/auth/production-auth-stabilized-diagnostics.json
  operator-console-static/demo-data/production-auth-core-stabilization.json
  operator-console-static/demo-data/production-auth-core-stabilization-runtime-hold.json
  scripts/production-auth-core-stabilization-check.sh
  scripts/production-auth-core-stabilization-runtime-hold.sh
  scripts/production-auth-core-stabilization-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-154 production-auth stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0145-v02-production-auth-core-stabilization.md" docs/adr/README.md || {
  echo "ADR 0145 is not indexed" >&2
  exit 1
}

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from aion_brain.contracts.production_auth import (
    ProductionAuthAuditEvent,
    ProductionAuthCoreStatus,
    ProductionAuthDiagnosticSnapshot,
    ProductionAuthPolicyDecision,
    ProductionAuthProvenanceRecord,
)
from aion_brain.production_auth.canonical import sha256_fingerprint
from aion_brain.production_auth.reason_codes import REQUIRED_REASON_CODES

root = Path(sys.argv[1])
model_examples = [
    ("examples/auth/production-auth-stabilized-core-status.json", ProductionAuthCoreStatus),
    ("examples/auth/production-auth-stabilized-policy-decision.json", ProductionAuthPolicyDecision),
    ("examples/auth/production-auth-stabilized-audit-event.json", ProductionAuthAuditEvent),
    ("examples/auth/production-auth-stabilized-provenance-record.json", ProductionAuthProvenanceRecord),
    ("examples/auth/production-auth-stabilized-diagnostics.json", ProductionAuthDiagnosticSnapshot),
]
for relative, model in model_examples:
    payload = json.loads((root / relative).read_text())
    parsed = model(**payload)
    expected = sha256_fingerprint(parsed.model_dump(mode="json", exclude={"fingerprint"}))
    if parsed.fingerprint != expected:
        raise SystemExit(f"fingerprint mismatch: {relative}")
    if getattr(parsed, "schema_version") != "production-auth-core/v1":
        raise SystemExit(f"schema_version mismatch: {relative}")
    if getattr(parsed, "reason_code_registry_version") != "production-auth-reason-codes/v1":
        raise SystemExit(f"reason registry mismatch: {relative}")

for relative in [
    "operator-console-static/demo-data/production-auth-core-stabilization.json",
    "operator-console-static/demo-data/production-auth-core-stabilization-runtime-hold.json",
]:
    payload = json.loads((root / relative).read_text())
    required_true = [
        "synthetic",
        "read_only",
        "production_auth_core_implemented",
        "runtime_guard_hold_active",
        "runtime_no_go_status",
    ]
    required_false = [
        "production_auth_runtime_enabled",
        "runtime_implementation_approved",
        "runtime_enablement_guard_release_approved",
        "login_endpoint_enabled",
        "logout_endpoint_enabled",
        "callback_endpoint_enabled",
        "credential_storage_enabled",
        "password_storage_enabled",
        "token_issuance_enabled",
        "token_storage_enabled",
        "session_creation_enabled",
        "session_storage_enabled",
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
    for key in required_true:
        if payload.get(key) is not True:
            raise SystemExit(f"{relative}: {key} must be true")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{relative}: {key} must be false")
    if payload.get("stabilization_authorization_transaction_id") != "AION-153-PA-0002":
        raise SystemExit(f"{relative}: stabilization authorization mismatch")
    if tuple(payload.get("reason_codes", REQUIRED_REASON_CODES)) != REQUIRED_REASON_CODES:
        raise SystemExit(f"{relative}: reason codes are not registry ordered")
PY

required_markers=(
  "AION-153-PA-0002"
  "disabled-production-auth-core-stabilization"
  "production-auth-core/v1"
  "production-auth-canonical-json/v1"
  "production-auth-policy/v1"
  "production-auth-reason-codes/v1"
)

for marker in "${required_markers[@]}"; do
  rg -n "$marker" \
    services/brain-api/src/aion_brain/contracts/production_auth.py \
    docs/auth/production-auth-core-stabilization.md \
    docs/auth/production-auth-canonical-evidence.md \
    docs/adr/0145-v02-production-auth-core-stabilization.md \
    examples/auth/production-auth-stabilized-core-status.json \
    operator-console-static/demo-data/production-auth-core-stabilization.json \
    >/dev/null || {
      echo "missing stabilization marker: $marker" >&2
      exit 1
    }
done

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_production_auth_stabilization_contracts.py \
  services/brain-api/tests/test_production_auth_canonicalization.py \
  services/brain-api/tests/test_production_auth_fingerprints.py \
  services/brain-api/tests/test_production_auth_reason_codes.py \
  services/brain-api/tests/test_production_auth_idempotency.py \
  services/brain-api/tests/test_production_auth_concurrency.py \
  services/brain-api/tests/test_production_auth_stabilization_redaction.py \
  services/brain-api/tests/test_production_auth_stabilization_config_matrix.py \
  services/brain-api/tests/test_production_auth_stabilization_kernel.py \
  services/brain-api/tests/test_production_auth_stabilization_routes.py \
  services/brain-api/tests/test_production_auth_stabilization_performance.py \
  -q

./scripts/production-auth-core-no-go-regression.sh
./scripts/production-auth-core-check.sh
./scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh
./scripts/v02-production-auth-stabilization-authorization-check.sh
./scripts/v02-production-auth-authorization-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "production-auth API router must remain absent" >&2
  exit 1
}

echo "production auth core stabilization check PASS"

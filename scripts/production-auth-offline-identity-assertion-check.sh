#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
"$PYTHON_BIN" - <<'PY'
import cryptography

if cryptography.__version__.split(".", 1)[0] != "49":
    raise SystemExit("cryptography major version must be 49")
PY

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

required_files=(
  services/brain-api/src/aion_brain/contracts/identity_assertion.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py
  services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py
  docs/auth/offline-identity-assertion-verification.md
  docs/auth/identity-assertion-public-key-registry.md
  docs/auth/identity-assertion-runtime-boundary.md
  docs/release/v02-offline-identity-assertion-verification-implementation.md
  docs/release/v02-offline-identity-assertion-verification-security-evidence.md
  docs/release/v02-offline-identity-assertion-verification-runtime-hold.md
  docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md
  docs/release/v02-offline-identity-assertion-verification-no-go.md
  docs/release/v02-offline-identity-assertion-verification-checklist.md
  docs/adr/0153-v02-offline-ed25519-identity-assertion-verification.md
  examples/auth/offline-identity-assertion-verification-result.json
  examples/auth/offline-identity-assertion-rejection-result.json
  examples/auth/offline-identity-assertion-audit-event.json
  examples/auth/offline-identity-assertion-provenance-record.json
  examples/auth/offline-identity-assertion-diagnostics.json
  examples/auth/offline-identity-public-key-registry-status.json
  operator-console-static/demo-data/offline-identity-assertion-verification.json
  operator-console-static/demo-data/offline-identity-assertion-runtime-hold.json
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-162 artifact: $file" >&2
    exit 1
  }
done

grep -q "0153-v02-offline-ed25519-identity-assertion-verification.md" docs/adr/README.md || {
  echo "ADR 0153 is not indexed" >&2
  exit 1
}

grep -F '"cryptography>=49.0.0,<50.0.0",' services/brain-api/pyproject.toml >/dev/null || {
  echo "exact cryptography dependency is missing" >&2
  exit 1
}

for json_file in examples/auth/offline-identity-assertion-*.json examples/auth/offline-identity-public-key-registry-status.json operator-console-static/demo-data/offline-identity-assertion-*.json; do
  "$PYTHON_BIN" -m json.tool "$json_file" >/dev/null
done

grep -F 'DOMAIN_SEPARATOR = b"AION-IDENTITY-ASSERTION-V1\0"' services/brain-api/src/aion_brain/contracts/identity_assertion.py >/dev/null || {
  echo "domain separator is missing" >&2
  exit 1
}
grep -F "canonical_json_bytes" services/brain-api/src/aion_brain/production_auth/identity_assertion.py >/dev/null || {
  echo "canonical serializer reuse is missing" >&2
  exit 1
}
grep -F "decode_base64url_unpadded" services/brain-api/src/aion_brain/production_auth/identity_assertion.py >/dev/null || {
  echo "strict base64url helper is missing" >&2
  exit 1
}
grep -F "TrustedPublicKeyRegistry" services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py >/dev/null || {
  echo "public-key registry is missing" >&2
  exit 1
}

if rg -n 'Ed25519PrivateKey|private_bytes\(|load_pem_private_key|BEGIN PRIVATE KEY|BEGIN OPENSSH PRIVATE KEY|signing_key|private_key_seed|private_key_base64' services/brain-api/src/aion_brain; then
  echo "runtime private-key material or API detected" >&2
  exit 1
fi

test ! -e services/brain-api/src/aion_brain/api/identity_assertion.py
test ! -e services/brain-api/src/aion_brain/api/production_auth.py
test ! -e services/brain-api/src/aion_brain/api/request_identity.py
test ! -e services/brain-api/src/aion_brain/api/actor_context.py
test ! -e services/brain-api/uv.lock
test ! -e services/brain-api/poetry.lock

"$PYTHON_BIN" - <<'PY'
from aion_brain.contracts.identity_assertion import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    IMPLEMENTATION_TASK,
)

assert AUTHORIZATION_TRANSACTION_ID == "AION-161-PA-0006"
assert IMPLEMENTATION_TASK == "AION-162"
assert AUTHORIZATION_SCOPE == "offline-ed25519-identity-assertion-verification"
PY

./scripts/production-auth-offline-identity-assertion-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused identity assertion pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_identity_assertion_contracts.py \
    services/brain-api/tests/test_identity_assertion_base64url.py \
    services/brain-api/tests/test_identity_assertion_canonical_payload.py \
    services/brain-api/tests/test_trusted_public_key_registry.py \
    services/brain-api/tests/test_offline_identity_assertion_verifier.py \
    services/brain-api/tests/test_identity_assertion_temporal_validation.py \
    services/brain-api/tests/test_identity_assertion_claim_constraints.py \
    services/brain-api/tests/test_identity_assertion_negative_crypto.py \
    services/brain-api/tests/test_identity_assertion_key_rotation.py \
    services/brain-api/tests/test_identity_assertion_evidence.py \
    services/brain-api/tests/test_identity_assertion_replay_boundary.py \
    services/brain-api/tests/test_identity_assertion_concurrency.py \
    services/brain-api/tests/test_identity_assertion_dependency_boundary.py \
    services/brain-api/tests/test_identity_assertion_no_runtime_integration.py \
    services/brain-api/tests/test_identity_assertion_performance.py \
    -q
fi

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-actor-context-trust-boundary-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/v02-offline-identity-assertion-verification-authorization-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

echo "production auth offline identity assertion verification PASS"

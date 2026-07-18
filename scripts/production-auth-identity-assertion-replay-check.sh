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

required_files=(
  services/brain-api/src/aion_brain/contracts/identity_assertion_replay.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_evidence.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py
  docs/auth/identity-assertion-replay-protection.md
  docs/auth/identity-assertion-replay-ledger.md
  docs/auth/identity-assertion-replay-runtime-boundary.md
  docs/release/v02-identity-assertion-replay-protection-implementation.md
  docs/release/v02-identity-assertion-replay-protection-security-evidence.md
  docs/release/v02-identity-assertion-replay-protection-runtime-hold.md
  docs/release/v02-identity-assertion-replay-protection-evidence-matrix.md
  docs/release/v02-identity-assertion-replay-protection-no-go.md
  docs/release/v02-identity-assertion-replay-protection-checklist.md
  docs/adr/0155-v02-persistent-identity-assertion-replay-protection.md
  examples/auth/identity-assertion-replay-first-claim.json
  examples/auth/identity-assertion-replay-detected.json
  examples/auth/identity-assertion-identifier-collision.json
  examples/auth/identity-assertion-replay-repository-failure.json
  examples/auth/identity-assertion-replay-audit-event.json
  examples/auth/identity-assertion-replay-provenance-record.json
  examples/auth/identity-assertion-replay-diagnostics.json
  examples/auth/offline-identity-assertion-pipeline-result.json
  operator-console-static/demo-data/identity-assertion-replay-protection.json
  operator-console-static/demo-data/identity-assertion-replay-runtime-hold.json
  scripts/production-auth-identity-assertion-replay-check.sh
  scripts/production-auth-identity-assertion-replay-runtime-hold.sh
  scripts/production-auth-identity-assertion-replay-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-164 artifact: $file" >&2
    exit 1
  }
done

grep -q "0155-v02-persistent-identity-assertion-replay-protection.md" docs/adr/README.md || {
  echo "ADR 0155 is not indexed" >&2
  exit 1
}

for json_file in \
  examples/auth/identity-assertion-replay-*.json \
  examples/auth/offline-identity-assertion-pipeline-result.json \
  operator-console-static/demo-data/identity-assertion-replay-*.json; do
  "$PYTHON_BIN" -m json.tool "$json_file" >/dev/null
done

"$PYTHON_BIN" - <<'PY'
from aion_brain.contracts.identity_assertion_replay import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    IMPLEMENTATION_TASK,
    REPLAY_KEY_DOMAIN_SEPARATOR,
    TABLE_NAME,
)
from aion_brain.production_auth.identity_assertion_replay_repository import (
    aion_identity_assertion_replay_claims,
)

assert AUTHORIZATION_TRANSACTION_ID == "AION-163-PA-0007"
assert IMPLEMENTATION_TASK == "AION-164"
assert AUTHORIZATION_SCOPE == "persistent-identity-assertion-replay-protection-core"
assert REPLAY_KEY_DOMAIN_SEPARATOR == b"AION-IDENTITY-ASSERTION-REPLAY-V1\0"
assert aion_identity_assertion_replay_claims.name == TABLE_NAME
assert set(aion_identity_assertion_replay_claims.c.keys()) == {
    "replay_key",
    "issuer_fingerprint",
    "assertion_fingerprint",
    "claimed_at",
    "assertion_expires_at",
    "retain_until",
    "created_at",
}
assert {index.name for index in aion_identity_assertion_replay_claims.indexes} == {
    "ix_aion_identity_assertion_replay_retain_until",
    "ix_aion_identity_assertion_replay_claimed_at",
    "ix_aion_identity_assertion_replay_assertion_expires_at",
}
PY

./scripts/production-auth-identity-assertion-replay-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused identity assertion replay pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_identity_assertion_replay_contracts.py \
    services/brain-api/tests/test_identity_assertion_replay_key.py \
    services/brain-api/tests/test_identity_assertion_replay_policy.py \
    services/brain-api/tests/test_identity_assertion_replay_table_contract.py \
    services/brain-api/tests/test_identity_assertion_replay_repository_schema.py \
    services/brain-api/tests/test_identity_assertion_replay_repository_claim.py \
    services/brain-api/tests/test_identity_assertion_replay_repository_concurrency.py \
    services/brain-api/tests/test_identity_assertion_replay_multiple_engines.py \
    services/brain-api/tests/test_identity_assertion_replay_service.py \
    services/brain-api/tests/test_identity_assertion_replay_pipeline.py \
    services/brain-api/tests/test_identity_assertion_replay_retention.py \
    services/brain-api/tests/test_identity_assertion_replay_cleanup.py \
    services/brain-api/tests/test_identity_assertion_replay_cleanup_race.py \
    services/brain-api/tests/test_identity_assertion_replay_failure_safety.py \
    services/brain-api/tests/test_identity_assertion_replay_evidence.py \
    services/brain-api/tests/test_identity_assertion_replay_redaction.py \
    services/brain-api/tests/test_identity_assertion_replay_concurrency.py \
    services/brain-api/tests/test_identity_assertion_replay_no_runtime_integration.py \
    services/brain-api/tests/test_identity_assertion_replay_no_dependency_or_migration.py \
    services/brain-api/tests/test_identity_assertion_replay_performance.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited replay gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-offline-identity-assertion-no-go-regression.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-offline-identity-assertion-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/v02-identity-assertion-replay-protection-authorization-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-actor-context-trust-boundary-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

echo "production auth identity assertion replay PASS"

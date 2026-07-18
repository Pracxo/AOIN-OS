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
  docs/release/v02-offline-identity-assertion-verification-closeout.md
  docs/release/v02-identity-assertion-replay-protection-authorization-transaction.md
  docs/release/v02-identity-assertion-replay-protection-explicit-approval-record.md
  docs/release/v02-identity-assertion-replay-protection-scope.md
  docs/release/v02-identity-assertion-replay-protection-persistence-model.md
  docs/release/v02-identity-assertion-replay-protection-threat-model.md
  docs/release/v02-identity-assertion-replay-protection-runtime-hold.md
  docs/release/v02-identity-assertion-replay-protection-evidence-matrix.md
  docs/release/v02-identity-assertion-replay-protection-no-go.md
  docs/release/v02-identity-assertion-replay-protection-checklist.md
  docs/adr/0154-v02-identity-assertion-replay-protection-authorization.md
  examples/release/v02-offline-identity-assertion-verification-closeout.json
  examples/release/v02-identity-assertion-replay-protection-authorization.json
  examples/release/v02-identity-assertion-replay-protection-explicit-approval-record.json
  examples/release/v02-identity-assertion-replay-protection-runtime-hold.json
  examples/release/v02-identity-assertion-replay-protection-evidence-matrix.json
  operator-console-static/demo-data/v02-identity-assertion-replay-protection-authorization.json
  scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh
  scripts/v02-identity-assertion-replay-protection-authorization-check.sh
  services/brain-api/tests/test_v02_identity_assertion_replay_protection_authorization_docs.py
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-163 artifact: $file" >&2
    exit 1
  }
done

grep -q "0154-v02-identity-assertion-replay-protection-authorization.md" docs/adr/README.md || {
  echo "ADR 0154 is not indexed" >&2
  exit 1
}

grep -F "AION-162 PR #72" docs/release/v02-offline-identity-assertion-verification-closeout.md >/dev/null || {
  echo "AION-162 PR 72 closeout evidence missing" >&2
  exit 1
}
grep -F "PR #73" docs/release/v02-offline-identity-assertion-verification-closeout.md >/dev/null || {
  echo "AION-162 PR 73 corrective evidence missing" >&2
  exit 1
}
grep -F "AION-163-PA-0007" docs/release/v02-identity-assertion-replay-protection-authorization-transaction.md >/dev/null || {
  echo "AION-163 authorization transaction missing" >&2
  exit 1
}
grep -F "AION-161-PA-0006" docs/release/v02-identity-assertion-replay-protection-authorization-transaction.md >/dev/null || {
  echo "AION-161 parent transaction missing" >&2
  exit 1
}

"$PYTHON_BIN" scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode check
./scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_v02_identity_assertion_replay_protection_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-offline-identity-assertion-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-offline-identity-assertion-no-go-regression.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/v02-offline-identity-assertion-verification-authorization-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/production-auth-actor-context-trust-boundary-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

cat <<'SUMMARY'
v0.2 identity assertion replay protection authorization result:
- AION-161-PA-0006: historical, consumed by AION-162 PR 72 and corrective PR 73, expired, non-reusable
- AION-163-PA-0007: only active approved authorization for AION-164
- replay key: domain-separated issuer plus assertion ID
- replay ledger: dedicated SQLAlchemy unique-insert claim, hashes and timestamps only
- dependency change, migration, production schema auto-create, runtime integration, request authentication, raw persistence, provider/network, endpoint, SDK/CLI, connector, operator, module, sandbox, tag, and release approvals: false
v0.2 identity assertion replay protection authorization PASS
SUMMARY

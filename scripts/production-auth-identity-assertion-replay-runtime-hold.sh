#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_IDENTITY_ASSERTION_REPLAY_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
payloads = [
    json.loads((root / "operator-console-static/demo-data/identity-assertion-replay-protection.json").read_text()),
    json.loads((root / "operator-console-static/demo-data/identity-assertion-replay-runtime-hold.json").read_text()),
]
for payload in payloads:
    assert payload["synthetic"] is True
    assert payload["read_only"] is True
    assert payload["authorization_transaction_id"] == "AION-163-PA-0007"
    assert payload["implementation_task"] == "AION-164"
    for key in (
        "request_authenticated",
        "actor_context_applied",
        "request_identity_context_applied",
        "runtime_effect",
        "runtime_integration_allowed",
        "production_auth_runtime_enabled",
        "replay_protection_core_runtime_enabled",
        "replay_repository_runtime_registered",
        "migrations_added",
        "v02_tag_created",
        "v02_release_created",
    ):
        assert payload.get(key) is False, key
PY

./scripts/production-auth-identity-assertion-replay-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/check.sh
fi

echo "production auth identity assertion replay runtime hold PASS"

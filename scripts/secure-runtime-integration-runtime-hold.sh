#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_SECURE_RUNTIME_INTEGRATION_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_SECURE_RUNTIME_INTEGRATION_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

nested_gate_context=0
if is_nested_gate_context; then
  nested_gate_context=1
fi

export AION_SECURE_RUNTIME_INTEGRATION_RUNTIME_HOLD_RUNNING=1
./scripts/secure-runtime-integration-program-authorization-check.sh
./scripts/secure-runtime-integration-program-no-go-regression.sh

if [[ -e services/brain-api/src/aion_brain/contracts/secure_runtime.py ]]; then
  echo "ERROR: secure runtime contract source exists before AION-231" >&2
  exit 1
fi
if [[ -d services/brain-api/src/aion_brain/secure_runtime ]]; then
  echo "ERROR: secure runtime source package exists before AION-231" >&2
  exit 1
fi
if find services/brain-api/src/aion_brain -path '*secure_runtime*' -print -quit | grep -q .; then
  echo "ERROR: secure runtime implementation source exists before AION-231" >&2
  exit 1
fi

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

aion_confirm_immutable_v01_tag_history >/dev/null

echo "secure runtime integration runtime hold PASS"

#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
is_nested_gate_context(){ [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0; [[ "${AION_GLM_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0; [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0; [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0; return 1; }
./scripts/governed-learning-memory-promotion-transaction-check.sh
"$PYTHON_BIN" -m scripts.lib.governed_learning_memory_local_persistence_authorization >/dev/null
if is_nested_gate_context; then echo "PASS: full repository check deferred to outer gate"; else AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh; fi
echo "governed learning memory runtime hold PASS"

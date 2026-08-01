#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_CAPABILITY_RUNTIME_OPERATOR_EVALUATION_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

nested_gate_context=0
if is_nested_gate_context; then
  nested_gate_context=1
fi
export AION_CAPABILITY_RUNTIME_OPERATOR_EVALUATION_RUNNING=1

./scripts/capability-runtime-operator-evaluation-no-go-regression.sh

REPORT="examples/secure-runtime-integration/capability-runtime-operator-evaluation-report.json"
if [[ -f "$REPORT" ]]; then
  "$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
  "$PYTHON_BIN" scripts/lib/capability_runtime_operator_evaluation.py \
    --validate-report "$REPORT"
else
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  "$PYTHON_BIN" scripts/lib/capability_runtime_operator_evaluation.py \
    --repo-root "$ROOT_DIR" \
    --evaluation-id AION-SRIPE-003 \
    --implementation-main-commit 39eff73b76f8b68a956f0a852bf8fbd71d36654d \
    --evaluation-base-commit "$(git rev-parse HEAD)" \
    --pilot-evidence examples/secure-runtime-integration/capability-runtime-local-sandbox-pilot-evidence.json \
    --temporary-output-directory "$tmp_dir" \
    --report "$tmp_dir/AION-SRIPE-003.json" >/dev/null
  "$PYTHON_BIN" scripts/lib/capability_runtime_operator_evaluation.py \
    --validate-report "$tmp_dir/AION-SRIPE-003.json"
fi

if [[ "$nested_gate_context" == "1" ]]; then
  echo "PASS: inherited capability-runtime gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/capability-runtime-check.sh
fi

echo "sandboxed capability runtime operator evaluation PASS"

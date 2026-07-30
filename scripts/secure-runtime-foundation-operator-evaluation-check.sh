#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_SECURE_RUNTIME_FOUNDATION_OPERATOR_EVALUATION_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

export AION_SECURE_RUNTIME_FOUNDATION_OPERATOR_EVALUATION_RUNNING=1

./scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh

REPORT="examples/secure-runtime-integration/runtime-foundation-operator-evaluation-report.json"
if [[ -f "$REPORT" ]]; then
  "$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
  "$PYTHON_BIN" scripts/lib/secure_runtime_foundation_operator_evaluation.py \
    --validate-report "$REPORT"
else
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  "$PYTHON_BIN" scripts/lib/secure_runtime_foundation_operator_evaluation.py \
    --repo-root "$ROOT_DIR" \
    --evaluation-id AION-SRIPE-001 \
    --evaluation-base-commit "$(git rev-parse HEAD)" \
    --pilot-evidence examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json \
    --temporary-output-directory "$tmp_dir" \
    --report "$tmp_dir/AION-SRIPE-001.json" >/dev/null
  "$PYTHON_BIN" scripts/lib/secure_runtime_foundation_operator_evaluation.py \
    --validate-report "$tmp_dir/AION-SRIPE-001.json"
fi

if is_nested_gate_context; then
  echo "PASS: inherited secure-runtime gates deferred to outer gate"
else
  ./scripts/secure-runtime-foundation-no-go-regression.sh
  ./scripts/secure-runtime-foundation-pilot-evidence-check.sh
  ./scripts/secure-runtime-foundation-check.sh
fi

echo "secure runtime foundation operator evaluation PASS"

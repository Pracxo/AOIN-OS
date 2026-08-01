#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

./scripts/secure-runtime-integration-final-evaluation-no-go-regression.sh

REPORT="examples/secure-runtime-integration/secure-runtime-integration-final-evaluation-report.json"
if [[ -f "$REPORT" ]]; then
  "$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
  "$PYTHON_BIN" scripts/lib/secure_runtime_integration_final_evaluation.py \
    --validate-report "$REPORT"
else
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  mkdir -m 700 "$tmp_dir/out"
  "$PYTHON_BIN" scripts/lib/secure_runtime_integration_final_evaluation.py \
    --repo-root "$ROOT_DIR" \
    --evaluation-id AION-SRIPE-004 \
    --implementation-main-commit 55f2721bb036886a693a36d870d49f49f7ecc6d1 \
    --evaluation-base-commit "$(git rev-parse HEAD)" \
    --pilot-evidence examples/secure-runtime-integration/operator-console-integrated-local-runtime-pilot-evidence.json \
    --temporary-output-directory "$tmp_dir/out" \
    --report "$tmp_dir/out/AION-SRIPE-004.json" >/dev/null
  "$PYTHON_BIN" scripts/lib/secure_runtime_integration_final_evaluation.py \
    --validate-report "$tmp_dir/out/AION-SRIPE-004.json"
fi

echo "secure runtime integration final evaluation PASS"

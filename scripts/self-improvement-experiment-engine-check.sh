#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
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
  services/brain-api/src/aion_brain/self_improvement/observation.py
  services/brain-api/src/aion_brain/self_improvement/pattern_intake.py
  services/brain-api/src/aion_brain/self_improvement/hypothesis.py
  services/brain-api/src/aion_brain/self_improvement/regression_proposal.py
  services/brain-api/src/aion_brain/self_improvement/experiment.py
  services/brain-api/src/aion_brain/self_improvement/proposal_service.py
  services/brain-api/src/aion_brain/self_improvement/experiment_runner.py
  services/brain-api/tests/test_self_improvement_experiment_engine.py
  scripts/self-improvement-experiment-engine-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-170 artifact: $file" >&2
    exit 1
  }
done

./scripts/self-improvement-experiment-engine-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused experiment-engine checks deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest services/brain-api/tests/test_self_improvement_experiment_engine.py -q
  "$PYTHON_BIN" -m ruff check \
    services/brain-api/src/aion_brain/self_improvement/observation.py \
    services/brain-api/src/aion_brain/self_improvement/pattern_intake.py \
    services/brain-api/src/aion_brain/self_improvement/hypothesis.py \
    services/brain-api/src/aion_brain/self_improvement/regression_proposal.py \
    services/brain-api/src/aion_brain/self_improvement/experiment.py \
    services/brain-api/src/aion_brain/self_improvement/experiment_runner.py \
    services/brain-api/src/aion_brain/self_improvement/proposal_service.py \
    services/brain-api/src/aion_brain/self_improvement/__init__.py \
    services/brain-api/tests/test_self_improvement_experiment_engine.py
  "$PYTHON_BIN" -m mypy \
    services/brain-api/src/aion_brain/self_improvement/observation.py \
    services/brain-api/src/aion_brain/self_improvement/pattern_intake.py \
    services/brain-api/src/aion_brain/self_improvement/hypothesis.py \
    services/brain-api/src/aion_brain/self_improvement/regression_proposal.py \
    services/brain-api/src/aion_brain/self_improvement/experiment.py \
    services/brain-api/src/aion_brain/self_improvement/experiment_runner.py \
    services/brain-api/src/aion_brain/self_improvement/proposal_service.py \
    services/brain-api/tests/test_self_improvement_experiment_engine.py
fi

cat <<'SUMMARY'
self-improvement experiment engine result:
- failure-pattern intake: implemented
- improvement hypotheses: disabled by default, deterministic test double available
- regression-test proposals: disabled by default, deterministic test double available
- experiment plans and candidate slots: metric-only and side-effect-free
- approval-pending proposal lifecycle: implemented
- source_modified=false
- git_branch_created=false
- pr_created=false
- runtime_effect=false
self-improvement experiment engine PASS
SUMMARY

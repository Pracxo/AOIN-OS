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
  services/brain-api/src/aion_brain/self_improvement/canary_contracts.py
  services/brain-api/src/aion_brain/self_improvement/canary.py
  services/brain-api/src/aion_brain/self_improvement/monitoring.py
  services/brain-api/src/aion_brain/self_improvement/rollback_controller.py
  services/brain-api/src/aion_brain/self_improvement/outcome_ledger.py
  services/brain-api/src/aion_brain/self_improvement/strategy_selector.py
  services/brain-api/src/aion_brain/self_improvement/retrieval_optimizer.py
  services/brain-api/src/aion_brain/self_improvement/case_based_planner.py
  services/brain-api/src/aion_brain/self_improvement/preference_learning.py
  services/brain-api/src/aion_brain/self_improvement/skill_evolution.py
  services/brain-api/src/aion_brain/self_improvement/integrated_pipeline.py
  services/brain-api/tests/test_self_improvement_canary_adaptation.py
  scripts/self-improvement-canary-adaptation-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-174 artifact: $file" >&2
    exit 1
  }
done

./scripts/self-improvement-canary-adaptation-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused canary-adaptation checks deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest services/brain-api/tests/test_self_improvement_canary_adaptation.py -q
  "$PYTHON_BIN" -m ruff check \
    services/brain-api/src/aion_brain/self_improvement/canary_contracts.py \
    services/brain-api/src/aion_brain/self_improvement/canary.py \
    services/brain-api/src/aion_brain/self_improvement/monitoring.py \
    services/brain-api/src/aion_brain/self_improvement/rollback_controller.py \
    services/brain-api/src/aion_brain/self_improvement/outcome_ledger.py \
    services/brain-api/src/aion_brain/self_improvement/strategy_selector.py \
    services/brain-api/src/aion_brain/self_improvement/retrieval_optimizer.py \
    services/brain-api/src/aion_brain/self_improvement/case_based_planner.py \
    services/brain-api/src/aion_brain/self_improvement/preference_learning.py \
    services/brain-api/src/aion_brain/self_improvement/skill_evolution.py \
    services/brain-api/src/aion_brain/self_improvement/integrated_pipeline.py \
    services/brain-api/src/aion_brain/self_improvement/__init__.py \
    services/brain-api/tests/test_self_improvement_canary_adaptation.py
  (
    cd services/brain-api
    .venv/bin/python -m mypy \
      src/aion_brain/self_improvement/canary_contracts.py \
      src/aion_brain/self_improvement/canary.py \
      src/aion_brain/self_improvement/monitoring.py \
      src/aion_brain/self_improvement/rollback_controller.py \
      src/aion_brain/self_improvement/outcome_ledger.py \
      src/aion_brain/self_improvement/strategy_selector.py \
      src/aion_brain/self_improvement/retrieval_optimizer.py \
      src/aion_brain/self_improvement/case_based_planner.py \
      src/aion_brain/self_improvement/preference_learning.py \
      src/aion_brain/self_improvement/skill_evolution.py \
      src/aion_brain/self_improvement/integrated_pipeline.py \
      tests/test_self_improvement_canary_adaptation.py
  )
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/self-improvement-canary-authorization-check.sh
  ./scripts/self-improvement-rewrite-controller-check.sh
  ./scripts/production-auth-core-no-go-regression.sh
  ./scripts/connector-runtime-no-external-call-regression.sh
fi

cat <<'SUMMARY'
self-improvement canary adaptation result:
- canary control: exact approval binding, disabled local simulation, metric thresholds
- rollback control: automatic rollback only inside approved running canary
- outcome ledger: proposal through survival-review records plus final outcomes
- retrieval optimizer: bounded reversible candidate versions
- case-based planning: policy-preserving and non-executing
- strategy selector: allowlisted shadow-mode Beta-Bernoulli policy
- preference learning: user-scoped, reversible, protected-attribute blocked
- procedural skill evolution: data-only and approval-gated
- integrated dry-run: isolated, simulated PR/CI/merge, healthy promotion, degraded rollback
self-improvement canary adaptation PASS
SUMMARY

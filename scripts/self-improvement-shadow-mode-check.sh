#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
"$PYTHON_BIN" - <<'PY'
import pydantic
import pytest

assert pydantic is not None
assert pytest is not None
PY

required_files=(
  services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py
  services/brain-api/src/aion_brain/self_improvement/shadow_mode.py
  services/brain-api/src/aion_brain/self_improvement/shadow_observation.py
  services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py
  services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py
  services/brain-api/src/aion_brain/self_improvement/shadow_budget.py
  services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py
  services/brain-api/src/aion_brain/self_improvement/shadow_runner.py
  docs/self-improvement/shadow-mode-implementation.md
  docs/self-improvement/shadow-mode-reference-adapters.md
  docs/self-improvement/shadow-mode-pipeline.md
  docs/self-improvement/shadow-mode-evidence.md
  docs/self-improvement/shadow-mode-output-and-retention.md
  docs/self-improvement/shadow-mode-operator-runbook.md
  docs/self-improvement/shadow-mode-security-review.md
  docs/self-improvement/aion-178-checklist.md
  docs/release/self-improvement-shadow-mode-implementation.md
  docs/release/self-improvement-shadow-mode-security-evidence.md
  docs/release/self-improvement-shadow-mode-implementation-runtime-hold.md
  docs/release/self-improvement-shadow-mode-implementation-no-go.md
  docs/release/self-improvement-shadow-mode-implementation-checklist.md
  docs/release/self-improvement-shadow-mode-implementation-evidence-matrix.md
  docs/adr/0163-controlled-self-improvement-shadow-mode-plane.md
  operator-console-static/demo-data/self-improvement-shadow-mode-plane.json
  operator-console-static/demo-data/self-improvement-shadow-mode-review-items.json
  operator-console-static/demo-data/self-improvement-shadow-mode-runtime-hold.json
)

json_files=(
  docs/self-improvement/authorization-ledger.json
  docs/self-improvement/program-ledger.json
  examples/self-improvement/shadow-observation-manifest.json
  examples/self-improvement/shadow-reference-snapshot.json
  examples/self-improvement/shadow-evaluation-summary.json
  examples/self-improvement/shadow-failure-pattern.json
  examples/self-improvement/shadow-hypothesis.json
  examples/self-improvement/shadow-regression-test-proposal.json
  examples/self-improvement/shadow-improvement-proposal.json
  examples/self-improvement/shadow-operator-review-item.json
  examples/self-improvement/shadow-budget-failure.json
  examples/self-improvement/shadow-run-diagnostics.json
  examples/self-improvement/shadow-evidence-bundle.json
  examples/self-improvement/shadow-mode-runtime-hold.json
  operator-console-static/demo-data/self-improvement-shadow-mode-plane.json
  operator-console-static/demo-data/self-improvement-shadow-mode-review-items.json
  operator-console-static/demo-data/self-improvement-shadow-mode-runtime-hold.json
)

for file in "${required_files[@]}" "${json_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-178 artifact: $file" >&2
    exit 1
  }
done

grep -F "0163-controlled-self-improvement-shadow-mode-plane.md" docs/adr/README.md >/dev/null || {
  echo "ADR 0163 is not indexed" >&2
  exit 1
}

for file in "${json_files[@]}"; do
  "$PYTHON_BIN" -m json.tool "$file" >/dev/null
done

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode check

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_self_improvement_shadow_contracts.py \
  services/brain-api/tests/test_self_improvement_shadow_manifest.py \
  services/brain-api/tests/test_self_improvement_shadow_redaction.py \
  services/brain-api/tests/test_self_improvement_shadow_reference_adapter.py \
  services/brain-api/tests/test_self_improvement_shadow_observation.py \
  services/brain-api/tests/test_self_improvement_shadow_evaluation.py \
  services/brain-api/tests/test_self_improvement_shadow_pattern_mining.py \
  services/brain-api/tests/test_self_improvement_shadow_hypotheses.py \
  services/brain-api/tests/test_self_improvement_shadow_regression_proposals.py \
  services/brain-api/tests/test_self_improvement_shadow_proposals.py \
  services/brain-api/tests/test_self_improvement_shadow_review_items.py \
  services/brain-api/tests/test_self_improvement_shadow_budget.py \
  services/brain-api/tests/test_self_improvement_shadow_pipeline.py \
  services/brain-api/tests/test_self_improvement_shadow_evidence.py \
  services/brain-api/tests/test_self_improvement_shadow_output_boundary.py \
  services/brain-api/tests/test_self_improvement_shadow_retention.py \
  services/brain-api/tests/test_self_improvement_shadow_deterministic_replay.py \
  services/brain-api/tests/test_self_improvement_shadow_concurrency.py \
  services/brain-api/tests/test_self_improvement_shadow_no_runtime_influence.py \
  services/brain-api/tests/test_self_improvement_shadow_no_network_git_or_pr.py \
  services/brain-api/tests/test_self_improvement_shadow_performance.py \
  -q

./scripts/self-improvement-shadow-mode-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_SHADOW_MODE_CHECK_RUNNING=1 ./scripts/self-improvement-shadow-mode-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_SHADOW_MODE_CHECK_RUNNING=1 ./scripts/self-improvement-final-check.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_SHADOW_MODE_CHECK_RUNNING=1 ./scripts/self-improvement-runtime-hold.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

echo "self improvement shadow mode PASS"

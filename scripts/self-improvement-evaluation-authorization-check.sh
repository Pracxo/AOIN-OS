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
  docs/self-improvement/governance-charter.md
  docs/self-improvement/evaluation-authorization.md
  docs/self-improvement/experiment-authorization.md
  docs/self-improvement/rewrite-authorization.md
  docs/self-improvement/protected-core-boundary.md
  docs/self-improvement/approval-model.md
  docs/self-improvement/change-budget-model.md
  docs/self-improvement/risk-model.md
  docs/self-improvement/aion-164-closeout-evidence.md
  docs/self-improvement/authorization-ledger.json
  docs/self-improvement/program-ledger.json
  docs/adr/0156-governed-self-improvement-control-plane.md
  docs/adr/0157-self-improvement-evaluation-authorization.md
  docs/adr/0158-self-improvement-experiment-authorization.md
  docs/adr/0159-self-improvement-rewrite-authorization.md
  scripts/lib/self_improvement_governance.py
  scripts/self-improvement-governance-no-go-regression.sh
  scripts/self-improvement-governance-authorization-check.sh
  scripts/self-improvement-evaluation-no-go-regression.sh
  scripts/self-improvement-evaluation-authorization-check.sh
  scripts/self-improvement-experiment-no-go-regression.sh
  scripts/self-improvement-experiment-authorization-check.sh
  scripts/self-improvement-rewrite-no-go-regression.sh
  scripts/self-improvement-rewrite-authorization-check.sh
  services/brain-api/tests/test_self_improvement_governance_authorization_docs.py
  services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py
  services/brain-api/tests/test_self_improvement_experiment_authorization_docs.py
  services/brain-api/tests/test_self_improvement_rewrite_authorization_docs.py
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-167 artifact: $file" >&2
    exit 1
  }
done

grep -F "0157-self-improvement-evaluation-authorization.md" docs/adr/README.md >/dev/null || {
  echo "ADR 0157 is not indexed" >&2
  exit 1
}

grep -F "0158-self-improvement-experiment-authorization.md" docs/adr/README.md >/dev/null || {
  echo "ADR 0158 is not indexed" >&2
  exit 1
}

grep -F "0159-self-improvement-rewrite-authorization.md" docs/adr/README.md >/dev/null || {
  echo "ADR 0159 is not indexed" >&2
  exit 1
}

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode check
./scripts/self-improvement-evaluation-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_experiment_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_rewrite_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

cat <<'SUMMARY'
self-improvement evaluation authorization result:
- AION-165-SI-0001: consumed by AION-166 PR 77 and closed by AION-167
- AION-167-SI-0002: consumed by AION-168 PR 79 and closed by AION-169
- AION-169-SI-0003: consumed by AION-170 PR 81 and closed by AION-171
- AION-171-SI-0004: consumed by AION-172 PR 83 and closed by AION-173
- AION-173-SI-0005: active authorization for AION-174 canary and adaptive policy
- source_rewriting_enabled=false
- pull_request_creation_enabled=false
- automatic_approval_enabled=false
- production_deployment_enabled=false
- model_weight_training_enabled=false
self-improvement evaluation authorization PASS
SUMMARY

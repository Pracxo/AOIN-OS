#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_SHADOW_MODE_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  return 1
}

required_files=(
  docs/self-improvement/operator-evaluation-closeout.md
  docs/self-improvement/shadow-mode-architecture.md
  docs/self-improvement/shadow-mode-boundary.md
  docs/self-improvement/shadow-mode-data-governance.md
  docs/self-improvement/shadow-mode-resource-budgets.md
  docs/self-improvement/shadow-mode-threat-model.md
  docs/self-improvement/shadow-mode-operator-workflow.md
  docs/self-improvement/shadow-mode-roadmap.md
  docs/release/self-improvement-shadow-mode-authorization-transaction.md
  docs/release/self-improvement-shadow-mode-explicit-approval-record.md
  docs/release/self-improvement-shadow-mode-scope.md
  docs/release/self-improvement-shadow-mode-runtime-hold.md
  docs/release/self-improvement-shadow-mode-no-go.md
  docs/release/self-improvement-shadow-mode-checklist.md
  docs/release/self-improvement-shadow-mode-evidence-matrix.md
  docs/adr/0162-controlled-self-improvement-shadow-mode-authorization.md
  examples/self-improvement/operator-evaluation-closeout.json
  examples/self-improvement/shadow-mode-authorization.json
  examples/self-improvement/shadow-mode-runtime-hold.json
  examples/self-improvement/shadow-mode-resource-budget.json
  examples/self-improvement/shadow-mode-data-boundary.json
  examples/self-improvement/shadow-mode-output-boundary.json
  examples/self-improvement/shadow-mode-operator-review-item.json
  operator-console-static/demo-data/self-improvement-shadow-mode-authorization.json
  operator-console-static/demo-data/self-improvement-shadow-mode-runtime-hold.json
  scripts/self-improvement-shadow-mode-authorization-check.sh
  scripts/self-improvement-shadow-mode-authorization-no-go-regression.sh
  scripts/self-improvement-shadow-mode-runtime-hold.sh
  services/brain-api/tests/test_self_improvement_operator_evaluation_closeout.py
  services/brain-api/tests/test_self_improvement_shadow_mode_authorization_docs.py
  services/brain-api/tests/test_self_improvement_shadow_mode_authorization_validator.py
  services/brain-api/tests/test_self_improvement_shadow_mode_boundary_spec.py
  services/brain-api/tests/test_self_improvement_shadow_mode_budget_spec.py
  services/brain-api/tests/test_self_improvement_shadow_mode_threat_model.py
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-177 artifact: $file" >&2
    exit 1
  }
done

grep -F "0162-controlled-self-improvement-shadow-mode-authorization.md" docs/adr/README.md >/dev/null || {
  echo "ADR 0162 is not indexed" >&2
  exit 1
}

"$PYTHON_BIN" -m json.tool docs/self-improvement/authorization-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool docs/self-improvement/program-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/operator-evaluation-closeout.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/shadow-mode-authorization.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/shadow-mode-runtime-hold.json >/dev/null
"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode check
"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode no-go
AION_SHADOW_MODE_RUNTIME_HOLD_RUNNING=1 ./scripts/self-improvement-shadow-mode-runtime-hold.sh

if command -v gh >/dev/null 2>&1; then
  pr_state="$(gh pr view 87 --json state --jq .state)"
  merge_commit="$(gh pr view 87 --json mergeCommit --jq .mergeCommit.oid)"
  test "$pr_state" = "MERGED" || {
    echo "AION-176 PR 87 must be merged" >&2
    exit 1
  }
  test "$merge_commit" = "ee50f1cc9ed3573661d1571954421abfb749e877" || {
    echo "AION-176 merge commit mismatch" >&2
    exit 1
  }
else
  echo "WARN: gh unavailable; relying on local AION-176 evidence files" >&2
fi

if is_nested_gate_context; then
  echo "PASS: inherited self-improvement and repository checks deferred to outer gate"
else
  ./scripts/self-improvement-runtime-hold.sh
  ./scripts/self-improvement-final-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

cat <<'SUMMARY'
self-improvement shadow-mode authorization result:
- AION-OE-001 closeout decision recorded
- AION-177-SI-0006 active for AION-178 only
- shadow mode authorized and implemented as operator-invoked disabled infrastructure
- shadow-mode runtime disabled
- source mutation, Git writes, PR creation, merge, deployment, provider calls, connector calls, and model training disabled
- v0.2 tags and releases absent
self-improvement shadow-mode authorization PASS
SUMMARY

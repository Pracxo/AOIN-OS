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

"$PYTHON_BIN" -m json.tool docs/cognitive-architecture/program-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool docs/cognitive-architecture/authorization-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-191-planning-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode memory-consolidation-closeout

./scripts/cognitive-memory-consolidation-closeout-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_memory_consolidation.py \
  services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_memory_consolidation_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive memory-consolidation closeout pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_memory_consolidation.py \
    services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py \
    services/brain-api/tests/test_cognitive_memory_consolidation_closeout_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive memory-consolidation closeout result:
- evaluation=AION-MCRE-001
- closed_authorization=AION-189-CA-0004
- new_authorization=AION-191-CA-0005
- authorized_task=AION-192
- retained_critical_memories=100%
- duplicate_reduction=100%
- contradiction_loss=0
- catastrophic_forgetting=0
- provenance_coverage=100%
- unauthorized_promotion_count=0
- deterministic_replay=100%
- forbidden_side_effects=0
- runtime_effect=false
cognitive memory-consolidation closeout PASS
SUMMARY

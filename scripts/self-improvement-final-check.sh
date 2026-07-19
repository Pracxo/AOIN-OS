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
  [[ "${AION_SELF_IMPROVEMENT_FINAL_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

required_files=(
  docs/self-improvement/final-architecture.md
  docs/self-improvement/operator-evaluation-guide.md
  docs/self-improvement/security-review.md
  docs/self-improvement/benchmark-report.md
  docs/self-improvement/end-to-end-evidence.md
  docs/self-improvement/known-limitations.md
  docs/self-improvement/runtime-activation-checklist.md
  docs/self-improvement/future-model-training-boundary.md
  docs/self-improvement/canary-authorization.md
  docs/self-improvement/authorization-ledger.json
  docs/self-improvement/program-ledger.json
  docs/adr/0161-governed-self-improvement-platform-complete.md
  examples/self-improvement/final-readiness-report.json
  scripts/self-improvement-runtime-hold.sh
  scripts/self-improvement-final-check.sh
  services/brain-api/tests/test_self_improvement_final_closeout_docs.py
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-175 artifact: $file" >&2
    exit 1
  }
done

grep -F "0161-governed-self-improvement-platform-complete.md" docs/adr/README.md >/dev/null || {
  echo "ADR 0161 is not indexed" >&2
  exit 1
}

"$PYTHON_BIN" -m json.tool docs/self-improvement/authorization-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool docs/self-improvement/program-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/final-readiness-report.json >/dev/null
"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode check
"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode no-go
./scripts/self-improvement-runtime-hold.sh

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-governance-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-evaluation-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-experiment-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-rewrite-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-rewrite-controller-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-canary-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-canary-adaptation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-governance-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-evaluation-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-experiment-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-rewrite-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-rewrite-controller-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-canary-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-canary-adaptation-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused final pytest, lint, type, docs, and full repository checks deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_experiment_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_rewrite_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_canary_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_evaluation_plane.py \
    services/brain-api/tests/test_self_improvement_experiment_engine.py \
    services/brain-api/tests/test_self_improvement_rewrite_controller.py \
    services/brain-api/tests/test_self_improvement_canary_adaptation.py \
    services/brain-api/tests/test_self_improvement_final_closeout_docs.py \
    -q
  "$PYTHON_BIN" -m ruff check \
    scripts/lib/self_improvement_governance.py \
    services/brain-api/src/aion_brain/self_improvement \
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_experiment_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_rewrite_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_canary_authorization_docs.py \
    services/brain-api/tests/test_self_improvement_evaluation_plane.py \
    services/brain-api/tests/test_self_improvement_experiment_engine.py \
    services/brain-api/tests/test_self_improvement_rewrite_controller.py \
    services/brain-api/tests/test_self_improvement_canary_adaptation.py \
    services/brain-api/tests/test_self_improvement_final_closeout_docs.py
  (
    cd services/brain-api
    MYPYPATH="$ROOT_DIR/scripts/lib" .venv/bin/python -m mypy \
      src/aion_brain/self_improvement \
      tests/test_self_improvement_final_closeout_docs.py
  )
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  git diff --check
  ./scripts/check.sh
fi

# aion-v0.1.0 exact-fetch and immutable SHA verification live in scripts/lib/immutable-tags.sh.
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
self-improvement final closeout result:
- platform: implemented_disabled
- authorization: AION-173-SI-0005 consumed by AION-174 and closed by AION-175
- final evaluation package: present
- runtime self-improvement: disabled
- runtime source rewrite: disabled
- automatic merge and production deployment: disabled
- exact human approval remains required
- protected core and holdout controls remain active
- v0.2 tags and releases absent
- aion-v0.1.0 immutable tag unchanged
self-improvement final closeout PASS
SUMMARY

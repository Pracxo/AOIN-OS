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
  services/brain-api/src/aion_brain/self_improvement/worktree.py
  services/brain-api/src/aion_brain/self_improvement/test_first.py
  services/brain-api/src/aion_brain/self_improvement/patch_generator.py
  services/brain-api/src/aion_brain/self_improvement/patch_validator.py
  services/brain-api/src/aion_brain/self_improvement/sandbox.py
  services/brain-api/src/aion_brain/self_improvement/diff_hash.py
  services/brain-api/src/aion_brain/self_improvement/git_controller.py
  services/brain-api/src/aion_brain/self_improvement/pr_controller.py
  services/brain-api/src/aion_brain/self_improvement/ci_monitor.py
  services/brain-api/src/aion_brain/self_improvement/merge_controller.py
  services/brain-api/src/aion_brain/self_improvement/rollback.py
  services/brain-api/tests/test_self_improvement_rewrite_controller.py
  scripts/self-improvement-rewrite-controller-no-go-regression.sh
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing AION-172 artifact: $file" >&2
    exit 1
  }
done

./scripts/self-improvement-rewrite-controller-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused rewrite-controller checks deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest services/brain-api/tests/test_self_improvement_rewrite_controller.py -q
  "$PYTHON_BIN" -m ruff check \
    services/brain-api/src/aion_brain/self_improvement/worktree.py \
    services/brain-api/src/aion_brain/self_improvement/test_first.py \
    services/brain-api/src/aion_brain/self_improvement/patch_generator.py \
    services/brain-api/src/aion_brain/self_improvement/patch_validator.py \
    services/brain-api/src/aion_brain/self_improvement/sandbox.py \
    services/brain-api/src/aion_brain/self_improvement/diff_hash.py \
    services/brain-api/src/aion_brain/self_improvement/git_controller.py \
    services/brain-api/src/aion_brain/self_improvement/pr_controller.py \
    services/brain-api/src/aion_brain/self_improvement/ci_monitor.py \
    services/brain-api/src/aion_brain/self_improvement/merge_controller.py \
    services/brain-api/src/aion_brain/self_improvement/rollback.py \
    services/brain-api/src/aion_brain/self_improvement/__init__.py \
    services/brain-api/tests/test_self_improvement_rewrite_controller.py
  (
    cd services/brain-api
    .venv/bin/python -m mypy \
      src/aion_brain/self_improvement/worktree.py \
      src/aion_brain/self_improvement/test_first.py \
      src/aion_brain/self_improvement/patch_generator.py \
      src/aion_brain/self_improvement/patch_validator.py \
      src/aion_brain/self_improvement/sandbox.py \
      src/aion_brain/self_improvement/diff_hash.py \
      src/aion_brain/self_improvement/git_controller.py \
      src/aion_brain/self_improvement/pr_controller.py \
      src/aion_brain/self_improvement/ci_monitor.py \
      src/aion_brain/self_improvement/merge_controller.py \
      src/aion_brain/self_improvement/rollback.py \
      tests/test_self_improvement_rewrite_controller.py
  )
fi

cat <<'SUMMARY'
self-improvement rewrite controller result:
- isolated worktree creation: implemented for explicitly supplied local repos
- test-first evidence: baseline-failure bound
- patch generation: disabled by default, deterministic test double available
- path, budget, protected-core, and test-weakening validation: implemented
- PR, CI, and merge operations: adapter-driven and disabled by default
- direct main push: rejected
- rollback metadata: exact candidate and rollback commit bound
self-improvement rewrite controller PASS
SUMMARY

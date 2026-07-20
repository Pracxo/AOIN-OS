#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "$GITHUB_BASE_REF"; do
      if git_ref_exists "$candidate" && git merge-base HEAD "$candidate" >/dev/null 2>&1; then
        git merge-base HEAD "$candidate"
        return 0
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate" && git merge-base HEAD "$candidate" >/dev/null 2>&1; then
      git merge-base HEAD "$candidate"
      return 0
    fi
  done
  if git_ref_exists HEAD~1; then
    printf '%s\n' HEAD~1
    return 0
  fi
  return 1
}

if base="$(comparison_base)"; then
  while IFS= read -r changed; do
    [[ -z "$changed" ]] && continue
    case "$changed" in
      services/brain-api/src/aion_brain/*)
        echo "blocked AION-181 runtime source change: $changed" >&2
        exit 1
        ;;
      .github/workflows/*|migrations/*|package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb)
        echo "blocked protected change: $changed" >&2
        exit 1
        ;;
      services/brain-api/pyproject.toml|services/brain-api/poetry.lock|services/brain-api/requirements.txt)
        echo "blocked Brain API dependency change: $changed" >&2
        exit 1
        ;;
      packages/aion-sdk-python/src/*|packages/aion-sdk-python/pyproject.toml)
        echo "blocked SDK runtime/dependency change: $changed" >&2
        exit 1
        ;;
    esac
  done < <(git diff --name-only "$base" HEAD)
else
  echo "WARN: comparison base unavailable; relying on current-tree checks" >&2
fi

HARNESS="scripts/lib/self_improvement_shadow_activation_operator_evaluation.py"
test -f "$HARNESS" || {
  echo "missing AION-182 harness: $HARNESS" >&2
  exit 1
}

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(subprocess|socket|requests|httpx|aiohttp|git|github)([[:space:].]|$)' "$HARNESS"; then
  echo "ERROR: prohibited network/Git import detected in AION-182 harness" >&2
  exit 1
fi

if rg -n 'self_improvement\.(worktree|patch_generator|git_controller|pr_controller|merge_controller|canary|rollback_controller)' "$HARNESS"; then
  echo "ERROR: prohibited controller dependency detected in AION-182 harness" >&2
  exit 1
fi

if rg -n '(shadow_activation_enabled[[:space:]]*=[[:space:]]*True|runtime_effect[[:space:]]*=[[:space:]]*True|approval_created[[:space:]]*=[[:space:]]*True|implementation_authorization_created[[:space:]]*=[[:space:]]*True)' "$HARNESS"; then
  echo "ERROR: AION-182 harness attempts to enable runtime or approval side effects" >&2
  exit 1
fi

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-activation-operator-evaluation-no-go

aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "self improvement shadow activation operator evaluation no-go PASS"

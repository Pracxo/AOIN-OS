#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

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

allowed_exact=(
  "services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_observation.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_budget.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_runner.py"
)

protected_paths=(
  ".github/workflows/"
  "services/brain-api/src/aion_brain/self_improvement/governance.py"
  "services/brain-api/src/aion_brain/self_improvement/approval.py"
  "services/brain-api/src/aion_brain/self_improvement/protected_paths.py"
  "services/brain-api/src/aion_brain/self_improvement/risk.py"
  "services/brain-api/src/aion_brain/self_improvement/worktree.py"
  "services/brain-api/src/aion_brain/self_improvement/patch_generator.py"
  "services/brain-api/src/aion_brain/self_improvement/git_controller.py"
  "services/brain-api/src/aion_brain/self_improvement/pr_controller.py"
  "services/brain-api/src/aion_brain/self_improvement/merge_controller.py"
  "services/brain-api/src/aion_brain/self_improvement/canary.py"
  "services/brain-api/src/aion_brain/self_improvement/rollback_controller.py"
  "services/brain-api/src/aion_brain/policy/"
  "services/brain-api/src/aion_brain/audit/"
  "services/brain-api/src/aion_brain/security/"
  "services/brain-api/src/aion_brain/kernel/"
  "services/brain-api/src/aion_brain/api/"
  "services/brain-api/src/aion_brain/api_support/"
  "services/brain-api/src/aion_brain/config.py"
  "services/brain-api/pyproject.toml"
  "packages/aion-sdk-python/src/"
  "migrations/"
)

is_allowed_shadow_source() {
  local changed="$1"
  local exact
  for exact in "${allowed_exact[@]}"; do
    [[ "$changed" == "$exact" ]] && return 0
  done
  return 1
}

if base="$(comparison_base)"; then
  while IFS= read -r changed; do
    [[ -z "$changed" ]] && continue
    if [[ "$changed" == services/brain-api/src/aion_brain/contracts/* ]] ||
       [[ "$changed" == services/brain-api/src/aion_brain/self_improvement/* ]]; then
      is_allowed_shadow_source "$changed" || {
        echo "blocked AION-178 source path changed: $changed" >&2
        exit 1
      }
    fi
    for protected in "${protected_paths[@]}"; do
      if [[ "$changed" == "$protected" || "$changed" == "$protected"* ]]; then
        echo "protected path changed: $changed" >&2
        exit 1
      fi
    done
  done < <(git diff --name-only "$base" HEAD)
else
  echo "WARN: comparison base unavailable; relying on current-tree checks" >&2
fi

for file in "${allowed_exact[@]}"; do
  test -f "$file" || {
    echo "missing AION-178 source file: $file" >&2
    exit 1
  }
done

if grep -R -n -E '^[[:space:]]*(import|from)[[:space:]]+(subprocess|socket|requests|httpx|aiohttp|git|github)' \
  services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_*.py; then
  echo "ERROR: prohibited import detected" >&2
  exit 1
fi

if grep -R -n -E 'self_improvement\.(worktree|patch_generator|git_controller|pr_controller|merge_controller|canary|rollback_controller)' \
  services/brain-api/src/aion_brain/self_improvement/shadow_*.py; then
  echo "ERROR: prohibited protected-controller dependency detected" >&2
  exit 1
fi

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode no-go
aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "self improvement shadow mode no-go PASS"

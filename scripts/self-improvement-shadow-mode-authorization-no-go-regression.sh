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

blocked_paths=(
  ".github/workflows/"
  "services/brain-api/src/aion_brain/"
  "packages/aion-sdk-python/src/"
  "services/brain-api/pyproject.toml"
  "migrations/"
)

if base="$(comparison_base)"; then
  while IFS= read -r changed; do
    [[ -z "$changed" ]] && continue
    for blocked in "${blocked_paths[@]}"; do
      if [[ "$changed" == "$blocked"* || "$changed" == "$blocked" ]]; then
        echo "blocked AION-177 path changed: $changed" >&2
        exit 1
      fi
    done
  done < <(git diff --name-only "$base" HEAD)
else
  echo "WARN: comparison base unavailable; relying on current-tree no-go checks" >&2
fi

prohibited_source_files=(
  "services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_observation.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_budget.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py"
  "services/brain-api/src/aion_brain/self_improvement/shadow_runner.py"
)

for file in "${prohibited_source_files[@]}"; do
  if [[ -e "$file" ]]; then
    echo "AION-178 runtime source must be absent during AION-177: $file" >&2
    exit 1
  fi
done

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

cat <<'SUMMARY'
self-improvement shadow-mode no-go result:
- runtime source absent
- workflow, runtime source, SDK runtime, pyproject, and migration paths unchanged
- source mutation, Git writes, PR creation, merge, deployment, provider calls, connector calls, model training, approval creation, and self approval disabled
- v0.2 tags and releases absent
self-improvement shadow-mode no-go PASS
SUMMARY

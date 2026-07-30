#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        git merge-base HEAD "$candidate" 2>/dev/null && return 0
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      git merge-base HEAD "$candidate" 2>/dev/null && return 0
    fi
  done
  if git_ref_exists HEAD~1; then
    printf '%s\n' HEAD~1
    return 0
  fi
  return 1
}

is_allowed_path() {
  case "$1" in
    docs/*|examples/*|operator-console-static/*|scripts/*|services/brain-api/tests/*|README.md|AGENTS.md)
      return 0
      ;;
  esac
  return 1
}

is_prohibited_path() {
  case "$1" in
    .github/workflows/*|services/brain-api/src/aion_brain/*|services/brain-api/pyproject.toml|packages/aion-sdk-python/src/*|migrations/*|services/brain-api/migrations/*|infra/postgres/migrations/*|package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|poetry.lock|uv.lock|Pipfile|Pipfile.lock)
      return 0
      ;;
  esac
  return 1
}

changed_entries() {
  local base
  if base="$(comparison_base)"; then
    git diff --name-status "$base" HEAD
  else
    echo "WARN: comparison base unavailable; relying on current tree checks" >&2
  fi
  git diff --name-status
  git diff --cached --name-status
  git status --porcelain=v1 --untracked-files=all | awk '/^\?\? / {print "A\t" substr($0, 4)}'
}

while IFS=$'\t' read -r status path extra; do
  [[ -n "${status:-}" ]] || continue
  if [[ "$status" == D* || "$status" == R* ]]; then
    echo "ERROR: deletion or rename is not authorized: $status $path ${extra:-}" >&2
    exit 1
  fi
  for changed in "$path" "${extra:-}"; do
    [[ -n "$changed" ]] || continue
    if is_prohibited_path "$changed"; then
      echo "ERROR: prohibited AION-229 surface changed: $changed" >&2
      exit 1
    fi
    if ! is_allowed_path "$changed"; then
      echo "ERROR: path outside AION-229 final-evaluation scope: $changed" >&2
      exit 1
    fi
  done
done < <(changed_entries)

if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(socket|ssl|requests|httpx|aiohttp|urllib\.request|subprocess|sqlite3|selenium|playwright|openai|anthropic)\b|socket\.|ssl\.|requests\.|httpx\.|aiohttp\.|urllib\.request\.|subprocess\.|os\.system\(' scripts/lib/governed_learning_memory_program_final_evaluation.py; then
  echo "ERROR: AION-229 evaluation harness includes prohibited network/process/runtime imports" >&2
  exit 1
fi

glm_final_evidence_paths=(
  docs/governed-learning-memory
  docs/release/governed-learning-memory-*
  examples/governed-learning-memory
  operator-console-static/demo-data/governed-learning-memory-*.json
)
if rg -n '(AION-230|successor GLM implementation authorization|successor_glm_implementation_authorization_created": true|production_runtime_authorized": true|repeat_live_pilot_authorized": true|background_continual_learning_enabled": true|scheduled_continual_learning_enabled": true|automatic_cycle_continuation_enabled": true|automatic_source_discovery_enabled": true|web_crawler_enabled": true|automatic_candidate_approval_enabled": true|automatic_knowledge_promotion_enabled": true|automatic_persistence_enabled": true|retained_pilot_store_enabled": true|production_memory_write_enabled": true|production_policy_mutation_enabled": true|cognitive_memory_write_enabled": true|actual_belief_creation_enabled": true|actual_belief_mutation_enabled": true|self_rewrite_enabled": true|runtime_source_rewrite_enabled": true|model_weight_training_enabled": true|production_exposure": true|v02_release_ready": true|v02_tag_created": true|v02_release_created": true)' "${glm_final_evidence_paths[@]}"; then
  echo "ERROR: prohibited AION-229 final-program capability enabled in evidence" >&2
  exit 1
fi

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*.jsonl' '*.state' | rg -n '.+'; then
  echo "ERROR: tracked runtime state/database candidate exists" >&2
  exit 1
fi

if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi
aion_confirm_immutable_v01_tag_history >/dev/null

echo "governed learning memory program final evaluation no-go PASS"

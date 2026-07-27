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
    README.md|AGENTS.md|docs/*|examples/*|operator-console-static/*|scripts/auth-design-check.sh|scripts/operator-console-static-check.sh|scripts/knowledge-intelligence-program-*|scripts/lib/knowledge_intelligence_program_final_evaluation.py|scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py|scripts/lib/knowledge_intelligence_public_research_pilot_authorization.py|scripts/lib/knowledge_intelligence_tool_verification_authorization.py|scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py|services/brain-api/tests/*)
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
  git status --porcelain=v1 | awk '/^\?\? / {print "A\t" substr($0, 4)}'
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
      echo "ERROR: prohibited AION-220 surface changed: $changed" >&2
      exit 1
    fi
    if ! is_allowed_path "$changed"; then
      echo "ERROR: path outside AION-220 final-evaluation scope: $changed" >&2
      exit 1
    fi
  done
done < <(changed_entries)

if find services/brain-api/src/aion_brain -type f \
  \( -name '*program_final_evaluation*.py' \
  -o -name '*program_complete*.py' \
  -o -name '*runtime_activation*.py' \
  -o -name '*knowledge_promotion*.py' \
  -o -name '*cognitive_memory_writer*.py' \) | rg -n '.+'; then
  echo "ERROR: prohibited runtime source for AION-220 exists" >&2
  exit 1
fi

if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(socket|ssl|requests|httpx|aiohttp|urllib\.request|subprocess|sqlite3|selenium|playwright|openai|anthropic)\b|socket\.|ssl\.|requests\.|httpx\.|aiohttp\.|urllib\.request\.|subprocess\.|os\.system\(' scripts/lib/knowledge_intelligence_program_final_evaluation.py; then
  echo "ERROR: AION-220 evaluation files include prohibited network/process/runtime imports" >&2
  exit 1
fi

if rg -n '(public_network_fetch_enabled": true|unrestricted_network_access_enabled": true|background_network_access_enabled": true|scheduled_public_research_enabled": true|background_crawler_enabled": true|search_provider_integration_enabled": true|connector_integration_enabled": true|model_provider_integration_enabled": true|browser_automation_enabled": true|actual_tool_execution_enabled": true|automatic_candidate_approval_enabled": true|automatic_verified_knowledge_promotion_enabled": true|persistent_verified_knowledge_write_enabled": true|cognitive_memory_write_enabled": true|belief_mutation_enabled": true|production_exposure": true|v02_release_ready": true|v02_tag_created": true|v02_release_created": true)' docs examples operator-console-static; then
  echo "ERROR: prohibited final-program capability enabled in evidence" >&2
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

echo "knowledge intelligence program final evaluation no-go PASS"

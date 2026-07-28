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
  local candidate merge_base
  if [[ "${1:-}" == "--merged-main" ]]; then
    echo "HEAD~1"
    return 0
  fi
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        [[ -n "$merge_base" ]] && { echo "$merge_base"; return 0; }
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      [[ -n "$merge_base" ]] && { echo "$merge_base"; return 0; }
    fi
  done
  git_ref_exists HEAD~1 && { echo HEAD~1; return 0; }
  return 1
}

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*-wal' '*-shm' '*.backup' | rg -n '.+'; then
  echo "ERROR: tracked SQLite, WAL, SHM, or backup artifact exists" >&2
  exit 1
fi

if base="$(comparison_base "${1:-}")"; then
  if git diff --name-only "$base" HEAD -- .github/workflows services/brain-api/src/aion_brain services/brain-api/pyproject.toml packages/aion-sdk-python/src migrations package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb | rg -n '.+'; then
    echo "ERROR: AION-225 branch touched prohibited runtime, workflow, dependency, or migration surface" >&2
    exit 1
  fi
fi

if rg -n '(engagement_application_implemented": true|operator_invoked_engagement_shadow_application_available": true|automatic_engagement_learning_application_enabled": true|persistent_engagement_overlay_write_enabled": true|production_policy_mutation_enabled": true|engagement_signal_as_fact_enabled": true|engagement_confidence_effect_enabled": true|engagement_knowledge_effect_enabled": true|cognitive_memory_write_enabled": true|actual_belief_creation_enabled": true|actual_belief_mutation_enabled": true|network_access_enabled": true|actual_tool_execution_enabled": true|v02_release_ready": true)' docs examples operator-console-static; then
  echo "ERROR: engagement application authorization no-go boundary violated" >&2
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
echo "governed learning memory engagement application authorization no-go PASS"

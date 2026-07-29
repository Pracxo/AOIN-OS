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

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*-wal' '*-shm' '*.backup' '*.state' | rg -n '.+'; then
  echo "ERROR: tracked database, WAL, SHM, backup, or state artifact exists" >&2
  exit 1
fi

if base="$(comparison_base "${1:-}")"; then
  changed="$(git diff --name-status "$base" HEAD)"
  if printf '%s\n' "$changed" | awk '$1 ~ /^D|R/ {print}' | rg -n '.+'; then
    echo "ERROR: AION-227 branch deletes or renames existing files" >&2
    exit 1
  fi
  if printf '%s\n' "$changed" | awk '{for (i=2; i<=NF; i++) print $i}' | rg -n '^services/brain-api/src/aion_brain/'; then
    echo "ERROR: AION-227 branch must not modify runtime source" >&2
    exit 1
  fi
  if printf '%s\n' "$changed" | awk '{for (i=2; i<=NF; i++) print $i}' | rg -n '^\.github/workflows/|^services/brain-api/pyproject\.toml$|^packages/aion-sdk-python/src/|^migrations/|^(package|package-lock|pnpm-lock|yarn)\.json$|^bun\.lockb$'; then
    echo "ERROR: AION-227 touched prohibited workflow, dependency, SDK, or migration surface" >&2
    exit 1
  fi
else
  echo "WARN: comparison base unavailable; skipping feature diff surface check" >&2
fi

if git ls-files | rg -n 'services/brain-api/src/aion_brain/(contracts/governed_continual_learning\.py|governed_learning_memory/continual_learning_)|scripts/governed-learning-memory-controlled-local-continual-learning-run\.py'; then
  echo "ERROR: AION-228 continual-learning source exists on AION-227 branch" >&2
  exit 1
fi

if rg -n \
  -g 'governed-learning-memory*' \
  '(network_calls": [1-9]|dns_resolutions": [1-9]|connector_calls": [1-9]|model_provider_calls": [1-9]|source_mutations": [1-9]|git_operations": [1-9]|production_exposure": true|v02_release_ready": true|background_continual_learning_enabled": true|scheduled_continual_learning_enabled": true|automatic_knowledge_promotion_enabled": true|automatic_candidate_approval_enabled": true|model_weight_training_enabled": true)' \
  docs/governed-learning-memory docs/release examples/governed-learning-memory operator-console-static/demo-data; then
  echo "ERROR: AION-227 continual-learning authorization no-go boundary violated" >&2
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
echo "governed learning memory continual learning pilot authorization no-go PASS"

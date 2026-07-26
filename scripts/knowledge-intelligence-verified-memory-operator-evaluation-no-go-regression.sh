#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

ALLOWED_PREFIXES=(
  "docs/"
  "examples/"
  "operator-console-static/"
  "scripts/"
  "services/brain-api/tests/"
)
ALLOWED_EXACT=(
  "README.md"
  "AGENTS.md"
)
PROHIBITED_PREFIXES=(
  ".github/workflows/"
  "migrations/"
  "services/brain-api/migrations/"
  "infra/postgres/migrations/"
  "services/brain-api/src/aion_brain/"
  "packages/aion-sdk-python/src/"
)
PROHIBITED_NAMES=(
  "package.json"
  "package-lock.json"
  "pnpm-lock.yaml"
  "yarn.lock"
  "bun.lockb"
  "poetry.lock"
  "uv.lock"
  "Pipfile"
  "Pipfile.lock"
)

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
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
  local path="$1"
  local item
  for item in "${ALLOWED_EXACT[@]}"; do
    [[ "$path" == "$item" ]] && return 0
  done
  for item in "${ALLOWED_PREFIXES[@]}"; do
    [[ "$path" == "$item"* ]] && return 0
  done
  return 1
}

is_prohibited_path() {
  local path="$1"
  local item
  for item in "${PROHIBITED_PREFIXES[@]}"; do
    [[ "$path" == "$item"* ]] && return 0
  done
  for item in "${PROHIBITED_NAMES[@]}"; do
    [[ "$(basename "$path")" == "$item" ]] && return 0
  done
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
  git status --porcelain=v1 | awk '/^\\?\\? / {print "A\t" substr($0, 4)}'
}

while IFS=$'\t' read -r status path extra; do
  [[ -z "${status:-}" ]] && continue
  if [[ "$status" == D* || "$status" == R* ]]; then
    echo "ERROR: deletion or rename is not authorized: $status $path ${extra:-}" >&2
    exit 1
  fi
  for changed in "$path" "${extra:-}"; do
    [[ -z "$changed" ]] && continue
    if is_prohibited_path "$changed"; then
      echo "ERROR: protected path changed: $changed" >&2
      exit 1
    fi
    if ! is_allowed_path "$changed"; then
      echo "ERROR: path outside AION-218 scope: $changed" >&2
      exit 1
    fi
  done
done < <(changed_entries)

if git ls-files | rg -n '\.(db|sqlite|sqlite3|jsonl|state)$'; then
  echo "ERROR: tracked persistence/state file detected" >&2
  exit 1
fi

if find services/brain-api/src/aion_brain -type f \( \
  -name 'knowledge_public_research_pilot.py' -o \
  -name 'public_research_dns.py' -o \
  -name 'public_research_http_transport.py' -o \
  -name 'public_research_policy.py' -o \
  -name 'public_research_claims.py' -o \
  -name 'public_research_pilot.py' -o \
  -name 'public_research_session.py' -o \
  -name 'public_research_evidence.py' -o \
  -name 'public_research_integrity.py' \
\) | rg -n '.+'; then
  echo "ERROR: AION-219 source exists on AION-218 branch" >&2
  exit 1
fi

if rg -n '^\s*(import|from)\s+(socket|ssl|http\.client|requests|httpx|aiohttp|urllib\.request|subprocess|sqlite3|git|github|selenium|playwright)\b' scripts/lib/knowledge_intelligence_verified_memory_operator_evaluation.py; then
  echo "ERROR: evaluation harness imports prohibited network/process/database/Git modules" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
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

echo "knowledge intelligence verified memory operator evaluation no-go PASS"

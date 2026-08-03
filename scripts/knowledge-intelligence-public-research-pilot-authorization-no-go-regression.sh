#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

changed_files="$(mktemp "${TMPDIR:-/tmp}/aion219-public-research-changed.XXXXXX")"
trap 'rm -f "$changed_files"' EXIT

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
  if git_ref_exists "HEAD~1"; then
    printf '%s\n' "HEAD~1"
    return 0
  fi
  return 1
}

is_aion219_source_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py)
      return 0
      ;;
  esac
  return 1
}

base="$(comparison_base || true)"
if [[ -n "$base" ]]; then
  git diff --name-only "$base" HEAD -- >"$changed_files"
else
  : >"$changed_files"
  echo "WARN: comparison base unavailable; branch-diff no-go checks are limited to current file inventory" >&2
fi

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  case "$path" in
    .github/workflows/*|migrations/*|services/brain-api/pyproject.toml|packages/aion-sdk-python/src/*|package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb)
      echo "ERROR: prohibited workflow/dependency/migration/API surface changed: $path" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py)
      ;;
    services/brain-api/src/aion_brain/*)
      if ! is_aion219_source_path "$path"; then
        echo "ERROR: unauthorized runtime source changed for AION-219: $path" >&2
        exit 1
      fi
      ;;
  esac
done <"$changed_files"

if find services/brain-api/src/aion_brain -type f \
  \( -name 'public_research_crawler.py' \
  -o -name 'public_research_search.py' \
  -o -name 'public_research_browser.py' \
  -o -name 'public_research_model.py' \
  -o -name 'public_research_connector.py' \
  -o -name 'public_research_scheduler.py' \
  -o -name 'public_research_worker.py' \
  -o -name 'public_research_database.py' \
  -o -name 'knowledge_promotion.py' \
  -o -name 'cognitive_memory_writer.py' \) | rg -n '.+'; then
  echo "ERROR: prohibited public research runtime expansion source exists" >&2
  exit 1
fi

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  if ! is_aion219_source_path "$path"; then
    echo "ERROR: unauthorized public_research source exists: $path" >&2
    exit 1
  fi
done < <(find services/brain-api/src/aion_brain -type f \( -name 'public_research_*.py' -o -name 'knowledge_public_research_pilot.py' \))

scan_path_if_present() {
  [[ -f "$1" ]] || return 0
  if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(requests|httpx|aiohttp|urllib\.request|selenium|playwright)\b|urllib\.request\.|requests\.|httpx\.|aiohttp\.|playwright|selenium|subprocess\.(run|Popen|check_call|check_output)|os\.system\(' "$1"; then
    echo "ERROR: prohibited public research network/tool client detected in $1" >&2
    exit 1
  fi
}

scan_path_if_present services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py
scan_path_if_present services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py
scan_path_if_present scripts/knowledge-intelligence-public-research-pilot-run.py

for path in \
  services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py; do
  if [[ -f "$path" ]] && rg -n '(^|[[:space:]])(import|from)[[:space:]]+(socket|ssl|http\.client)\b|socket\.|ssl\.' "$path"; then
    echo "ERROR: low-level network primitives are limited to DNS and HTTPS transport modules: $path" >&2
    exit 1
  fi
done

if [[ -f services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py ]] \
  && rg -n '(^|[[:space:]])(import|from)[[:space:]]+(socket|ssl|http\.client)\b|socket\.|ssl\.' services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py; then
  echo "ERROR: policy module must not own socket or TLS transport" >&2
  exit 1
fi

if [[ -f services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py ]] \
  && rg -n '(^|[[:space:]])(import|from)[[:space:]]+(ssl|http\.client)\b|ssl\.' services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py; then
  echo "ERROR: DNS module must not own TLS or HTTP transport" >&2
  exit 1
fi
if rg -n '(automatic_claim_extraction_enabled": true|automatic_verified_knowledge_promotion_enabled": true|persistent_verified_knowledge_write_enabled": true|cognitive_memory_write_enabled": true|belief_mutation_enabled": true)' docs examples operator-console-static; then
  echo "ERROR: prohibited public pilot capability enabled" >&2
  exit 1
fi
aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -v '^aion-v0\.2\.0-rc\.1$' | rg -n '.+'; then echo "ERROR: v0.2 tag exists" >&2; exit 1; fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then echo "ERROR: v0.2 release exists" >&2; exit 1; fi
fi
echo "knowledge intelligence public research pilot authorization no-go PASS"

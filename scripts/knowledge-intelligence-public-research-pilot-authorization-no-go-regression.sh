#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
AION219_NAMES=(knowledge_public_research_pilot.py public_research_dns.py public_research_http_transport.py public_research_policy.py public_research_claims.py public_research_pilot.py public_research_session.py public_research_evidence.py public_research_integrity.py)
CHANGED_FILES=()
while IFS= read -r path; do
  [[ -n "$path" ]] && CHANGED_FILES+=("$path")
done < <(git diff --name-only origin/main...HEAD -- 2>/dev/null || git diff --name-only HEAD~1...HEAD --)
for name in "${AION219_NAMES[@]}"; do
  if find services/brain-api/src/aion_brain -type f -name "$name" | rg -n '.+'; then
    echo "ERROR: AION-219 source exists on AION-218 branch: $name" >&2
    exit 1
  fi
done
for path in "${CHANGED_FILES[@]}"; do
  case "$path" in
    .github/workflows/*|migrations/*|services/brain-api/pyproject.toml|packages/aion-sdk-python/src/*|package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb)
      echo "ERROR: prohibited workflow/dependency/migration/API surface changed: $path" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/*)
      echo "ERROR: runtime source changed on AION-218 branch: $path" >&2
      exit 1
      ;;
  esac
done
SCAN_FILES=()
for path in "${CHANGED_FILES[@]}"; do
  case "$path" in
    scripts/lib/*.py)
      SCAN_FILES+=("$path")
      ;;
  esac
done
if ((${#SCAN_FILES[@]})); then
  if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(socket|ssl|http\.client|requests|httpx|aiohttp|urllib\.request|subprocess|selenium|playwright)\b|subprocess\.(run|Popen|check_call|check_output)|socket\.|ssl\.|urllib\.request\.|requests\.|httpx\.|aiohttp\.|playwright|selenium' "${SCAN_FILES[@]}"; then
    echo "ERROR: prohibited runtime/network implementation source detected" >&2
    exit 1
  fi
fi
if rg -n '(automatic_claim_extraction_enabled": true|automatic_verified_knowledge_promotion_enabled": true|persistent_verified_knowledge_write_enabled": true|cognitive_memory_write_enabled": true|belief_mutation_enabled": true)' docs examples operator-console-static; then
  echo "ERROR: prohibited public pilot capability enabled" >&2
  exit 1
fi
aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then echo "ERROR: v0.2 tag exists" >&2; exit 1; fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then echo "ERROR: v0.2 release exists" >&2; exit 1; fi
fi
echo "knowledge intelligence public research pilot authorization no-go PASS"

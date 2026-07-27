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

is_exact_aion219_source() {
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

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|docs/*|examples/*|operator-console-static/*|scripts/knowledge-intelligence-public-research-pilot-*|scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|scripts/knowledge-intelligence-domain-expert-mesh-check.sh|scripts/knowledge-intelligence-domain-expert-mesh-no-go-regression.sh|scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|scripts/knowledge-intelligence-epistemic-assessment-check.sh|scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh|scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh|scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh|scripts/knowledge-intelligence-claim-graph-authorization-check.sh|scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh|scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh|scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|scripts/knowledge-intelligence-source-registry-authorization-check.sh|scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh|scripts/knowledge-intelligence-source-registry-check.sh|scripts/knowledge-intelligence-source-registry-no-go-regression.sh|scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh|scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh|scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|scripts/knowledge-intelligence-research-runtime-hold.sh|scripts/auth-design-check.sh|scripts/connector-platform-checkpoint.sh|scripts/connector-release-no-go-regression.sh|scripts/connector-runtime-no-external-call-regression.sh|scripts/operator-console-static-check.sh|scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|scripts/production-auth-core-no-go-regression.sh|scripts/static-console-safety-check.sh|scripts/lib/knowledge_intelligence_public_research_pilot_authorization.py|scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py|scripts/lib/knowledge_intelligence_tool_verification_authorization.py|scripts/lib/v02-production-auth-scan-exclusions.sh|services/brain-api/tests/*)
      return 0
      ;;
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-authorization-check.sh|\
    scripts/knowledge-intelligence-research-authorization-no-go-regression.sh|\
    scripts/production-auth-identity-assertion-replay-no-go-regression.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh)
      return 0
      ;;
    services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py)
      return 0
      ;;
  esac
  is_exact_aion219_source "$1"
}

is_prohibited_path() {
  case "$1" in
    .github/workflows/*|migrations/*|services/brain-api/migrations/*|infra/postgres/migrations/*|packages/aion-sdk-python/src/*|services/brain-api/pyproject.toml|package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|poetry.lock|uv.lock|Pipfile|Pipfile.lock)
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
      echo "ERROR: prohibited workflow/dependency/migration/API surface changed: $changed" >&2
      exit 1
    fi
    if [[ "$changed" == services/brain-api/src/aion_brain/* ]] && ! is_exact_aion219_source "$changed" && [[ "$changed" != "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py" ]]; then
      echo "ERROR: unauthorized runtime source changed: $changed" >&2
      exit 1
    fi
    if ! is_allowed_path "$changed"; then
      echo "ERROR: path outside AION-219 scope: $changed" >&2
      exit 1
    fi
  done
done < <(changed_entries)

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
  echo "ERROR: prohibited crawler/search/browser/model/connector/scheduler/database source exists" >&2
  exit 1
fi

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  if ! is_exact_aion219_source "$path"; then
    echo "ERROR: unauthorized public research source exists: $path" >&2
    exit 1
  fi
done < <(find services/brain-api/src/aion_brain -type f \( -name 'public_research_*.py' -o -name 'knowledge_public_research_pilot.py' \))

scan_path_if_present() {
  [[ -f "$1" ]] || return 0
  if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(requests|httpx|aiohttp|urllib\.request|subprocess|selenium|playwright|openai|anthropic|boto3|google\.generativeai)\b|urllib\.request\.|requests\.|httpx\.|aiohttp\.|playwright|selenium|subprocess\.|os\.system\(|openai\.|anthropic\.' "$1"; then
    echo "ERROR: prohibited client/process/model-provider usage detected in $1" >&2
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
  services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py; do
  if [[ -f "$path" ]] && rg -n '(^|[[:space:]])(import|from)[[:space:]]+(socket|ssl|http\.client)\b|socket\.|ssl\.' "$path"; then
    echo "ERROR: socket/ssl/http.client are limited to DNS and HTTPS transport modules: $path" >&2
    exit 1
  fi
done

if [[ -f services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py ]] \
  && rg -n '(^|[[:space:]])(import|from)[[:space:]]+(ssl|http\.client)\b|ssl\.' services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py; then
  echo "ERROR: DNS module must not own TLS or HTTP transport" >&2
  exit 1
fi
if [[ -f services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py ]] \
  && rg -n 'urllib\.request|(^|[[:space:]])(import|from)[[:space:]]+(socket|ssl|http\.client)\b|socket\.|ssl\.' services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py; then
  echo "ERROR: policy module must stay separate from transport and urllib.request" >&2
  exit 1
fi

if git ls-files | rg -n '\.(db|sqlite|sqlite3|jsonl|state)$'; then
  echo "ERROR: tracked runtime state/database file detected" >&2
  exit 1
fi

if rg -n '(api_route_enabled": true|installed_cli_command_enabled": true|background_pilot_worker_enabled": true|pilot_scheduler_enabled": true|automatic_claim_extraction_enabled": true|automatic_verified_knowledge_promotion_enabled": true|persistent_verified_knowledge_write_enabled": true|cognitive_memory_write_enabled": true|belief_mutation_enabled": true|git_mutation_enabled": true|real_pull_request_creation_enabled": true|approval_creation_enabled": true)' docs examples operator-console-static; then
  echo "ERROR: prohibited runtime capability enabled in evidence" >&2
  exit 1
fi

./scripts/knowledge-intelligence-public-research-pilot-authorization-no-go-regression.sh >/dev/null
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

echo "knowledge intelligence public research pilot no-go PASS"

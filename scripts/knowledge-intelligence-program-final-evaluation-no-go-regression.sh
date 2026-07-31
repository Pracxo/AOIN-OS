#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

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
    docs/governed-learning-memory/*|\
    docs/release/governed-learning-memory-*|\
    docs/adr/0185-governed-learning-and-memory-integration-program-charter.md|\
    examples/governed-learning-memory/*|\
    operator-console-static/demo-data/governed-learning-memory-*.json|\
    scripts/governed-learning-memory-promotion-transaction-check.sh|\
    scripts/governed-learning-memory-promotion-transaction-no-go-regression.sh|\
    scripts/governed-learning-memory-promotion-operator-evaluation-check.sh|\
    scripts/governed-learning-memory-promotion-operator-evaluation-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-authorization-check.sh|\
    scripts/governed-learning-memory-local-persistence-authorization-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-runtime-hold.sh|\
    scripts/governed-learning-memory-local-persistence-operator-evaluation-check.sh|\
    scripts/governed-learning-memory-local-persistence-operator-evaluation-no-go-regression.sh|\
    scripts/governed-learning-memory-engagement-application-authorization-check.sh|\
    scripts/governed-learning-memory-engagement-application-authorization-no-go-regression.sh|\
    scripts/governed-learning-memory-engagement-application-operator-evaluation-check.sh|\
    scripts/governed-learning-memory-engagement-application-operator-evaluation-no-go-regression.sh|\
    scripts/governed-learning-memory-engagement-application-runtime-hold.sh|\
    scripts/governed-learning-memory-controlled-local-continual-learning-run.py|\
    scripts/governed-learning-memory-continual-learning-live-pilot-evidence-check.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-check.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-authorization-check.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-authorization-no-go-regression.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-no-go-regression.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-runtime-hold.sh|\
    scripts/governed-learning-memory-program-authorization-check.sh|\
    scripts/governed-learning-memory-program-final-*.sh|\
    scripts/governed-learning-memory-program-complete*.sh|\
    scripts/governed-learning-memory-program-no-go-regression.sh|\
    scripts/governed-learning-memory-runtime-hold.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/operator-runbook-check.sh|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/lib/governed_learning_memory_promotion_operator_evaluation.py|\
    scripts/lib/governed_learning_memory_local_persistence_authorization.py|\
    scripts/lib/governed_learning_memory_local_persistence_operator_evaluation.py|\
    scripts/lib/governed_learning_memory_engagement_application_authorization.py|\
    scripts/lib/governed_learning_memory_engagement_application_operator_evaluation.py|\
    scripts/lib/governed_learning_memory_continual_learning_pilot_authorization.py|\
    scripts/lib/governed_learning_memory_program_final_evaluation.py|\
    services/brain-api/tests/test_governed_learning_memory_*.py)
      return 0
      ;;
  esac
  case "$1" in
    README.md|AGENTS.md|docs/*|examples/*|operator-console-static/*|scripts/auth-design-check.sh|scripts/operator-console-static-check.sh|scripts/secure-runtime-integration-*.sh|scripts/knowledge-intelligence-program-*|scripts/lib/knowledge_intelligence_program_final_evaluation.py|scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py|scripts/lib/knowledge_intelligence_public_research_pilot_authorization.py|scripts/lib/knowledge_intelligence_tool_verification_authorization.py|scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py|services/brain-api/tests/*)
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

aion222_is_scoped_promotion_transaction_compatibility_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/governed_learning_memory.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/integrity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/rollback.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/self_improvement_governance.py|\
    scripts/operator-action-write-path-no-go-regression.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
    scripts/production-auth-core-stabilization-no-go-regression.sh|\
    scripts/production-auth-identity-assertion-replay-no-go-regression.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh)
      return 0
      ;;
  esac
  return 1
}

aion224_is_scoped_local_persistence_compatibility_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/governed_learning_memory_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/backup_restore.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_content.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_persistence_policy.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_schema.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/memory_projection_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_approval.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_integrity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_transactions.py|\
    scripts/governed-learning-memory-local-persistence-check.sh|\
    scripts/governed-learning-memory-local-persistence-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-pilot-evidence-check.sh|\
    scripts/governed-learning-memory-local-persistence-run.py|\
    scripts/governed-learning-memory-local-persistence-operator-evaluation-check.sh|\
    scripts/governed-learning-memory-local-persistence-operator-evaluation-no-go-regression.sh)
      return 0
      ;;
  esac
  return 1
}

aion226_is_scoped_engagement_application_compatibility_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/governed_engagement_learning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_identity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_planning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_application_approval.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_candidate_binding.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_counterfactual_evaluation.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_integrity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_overlay.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_rollback.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_shadow_application.py|\
    scripts/governed-learning-memory-engagement-application-check.sh|\
    scripts/governed-learning-memory-engagement-application-no-go-regression.sh|\
    scripts/governed-learning-memory-engagement-shadow-pilot-evidence-check.sh|\
    scripts/governed-learning-memory-engagement-shadow-run.py|\
    scripts/lib/governed_learning_memory_engagement_application.py)
      return 0
      ;;
  esac
  return 1
}

aion228_is_scoped_continual_learning_compatibility_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/governed_continual_learning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_*.py)
      return 0
      ;;
  esac
  return 1
}

aion234_is_scoped_model_gateway_evaluation_compatibility_path() {
  case "$1" in
    scripts/model-gateway-operator-evaluation-check.sh|\
    scripts/model-gateway-operator-evaluation-no-go-regression.sh|\
    scripts/capability-runtime-authorization-check.sh|\
    scripts/capability-runtime-authorization-no-go-regression.sh|\
    scripts/capability-runtime-runtime-hold.sh|\
    scripts/lib/model_gateway_operator_evaluation.py|\
    services/brain-api/tests/aion234_test_support.py|\
    services/brain-api/tests/test_capability_runtime_*.py|\
    services/brain-api/tests/test_model_gateway_aion233_delivery_reconciliation.py|\
    services/brain-api/tests/test_model_gateway_authorization_closeout.py|\
    services/brain-api/tests/test_model_gateway_evaluation_*.py|\
    services/brain-api/tests/test_model_gateway_operator_evaluation.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion234.py)
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
    if aion222_is_scoped_promotion_transaction_compatibility_path "$changed"; then
      continue
    fi
    if aion224_is_scoped_local_persistence_compatibility_path "$changed"; then
      continue
    fi
    if aion226_is_scoped_engagement_application_compatibility_path "$changed"; then
      continue
    fi
    if aion228_is_scoped_continual_learning_compatibility_path "$changed"; then
      continue
    fi
    if aion234_is_scoped_model_gateway_evaluation_compatibility_path "$changed"; then
      continue
    fi
    if aion231_is_scoped_secure_runtime_foundation_path "$changed"; then
      continue
    fi
    if aion232_is_scoped_secure_runtime_foundation_evaluation_path "$changed"; then
      continue
    fi
    if aion233_is_scoped_controlled_model_gateway_path "$changed"; then
      continue
    fi
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

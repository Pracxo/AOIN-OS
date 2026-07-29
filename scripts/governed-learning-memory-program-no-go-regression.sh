#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

mode="${1:-feature}"
case "$mode" in
  feature|--feature)
    mode="feature"
    ;;
  merged-main|--merged-main)
    mode="merged-main"
    ;;
  *)
    echo "usage: $0 [feature|merged-main]" >&2
    exit 2
    ;;
esac

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local merge_base
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        if [[ -n "$merge_base" ]]; then
          echo "$merge_base"
          return 0
        fi
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      if [[ -n "$merge_base" ]]; then
        echo "$merge_base"
        return 0
      fi
    fi
  done
  if git_ref_exists HEAD~1; then
    echo "HEAD~1"
    return 0
  fi
  return 1
}

aion224_implemented_state() {
  rg -q '"program_state"[[:space:]]*:[[:space:]]*"(governed_learning_memory_local_append_only_persistence_implemented_operator_invoked_isolated_pending_closeout|governed_learning_memory_engagement_application_authorized_not_implemented|governed_learning_memory_engagement_application_implemented_shadow_only_pending_closeout|governed_learning_memory_controlled_local_continual_learning_pilot_authorized_not_implemented|governed_learning_memory_controlled_local_continual_learning_pilot_implemented_completed_pending_final_closeout)"' \
    docs/governed-learning-memory/program-ledger.json
}

is_aion224_source_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/governed_learning_memory_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_persistence_policy.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_schema.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_approval.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_content.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/memory_projection_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_transactions.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_integrity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/backup_restore.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py)
      return 0
      ;;
  esac
  return 1
}

is_aion226_path() {
  case "$1" in
    docs/adr/0190-operator-approved-non-factual-engagement-learning-shadow-application.md|\
    scripts/governed-learning-memory-engagement-*.sh|\
    scripts/governed-learning-memory-engagement-*.py|\
    scripts/lib/governed_learning_memory_engagement_*.py|\
    services/brain-api/src/aion_brain/contracts/governed_engagement_learning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/engagement_*.py|\
    services/brain-api/tests/governed_engagement_learning_test_helpers.py|\
    services/brain-api/tests/test_governed_engagement_learning_*.py)
      return 0
      ;;
  esac
  return 1
}

is_aion228_path() {
  case "$1" in
    docs/adr/0192-controlled-operator-invoked-local-continual-learning-pilot-composition-and-execution.md|\
    scripts/governed-learning-memory-controlled-local-continual-learning-run.py|\
    scripts/governed-learning-memory-continual-learning-*.sh|\
    scripts/lib/governed_learning_memory_continual_learning_pilot_authorization.py|\
    services/brain-api/src/aion_brain/contracts/governed_continual_learning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_*.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/tests/test_governed_learning_memory_continual_learning_*.py)
      return 0
      ;;
  esac
  return 1
}

is_allowed_path() {
  if is_aion226_path "$1"; then
    return 0
  fi
  if is_aion228_path "$1"; then
    return 0
  fi
  if aion224_implemented_state && is_aion224_source_path "$1"; then
    return 0
  fi
  case "$1" in
    README.md|AGENTS.md|\
    docs/governed-learning-memory/*|\
    docs/release/governed-learning-memory-*|\
    docs/adr/0185-governed-learning-and-memory-integration-program-charter.md|\
    docs/adr/0186-approval-bound-knowledge-promotion-transaction-core.md|\
    docs/adr/0187-promotion-transaction-evaluation-and-local-append-only-knowledge-persistence-authorization.md|\
    docs/adr/0188-operator-approved-local-append-only-knowledge-and-memory-projection-persistence.md|\
    docs/adr/0191-engagement-shadow-application-evaluation-and-controlled-local-continual-learning-pilot-authorization.md|\
    docs/adr/README.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    examples/governed-learning-memory/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/governed-learning-memory-*.json|\
    scripts/auth-design-check.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/governed-learning-memory-program-authorization-check.sh|\
    scripts/governed-learning-memory-program-no-go-regression.sh|\
    scripts/governed-learning-memory-runtime-hold.sh|\
    scripts/governed-learning-memory-promotion-transaction-check.sh|\
    scripts/governed-learning-memory-promotion-transaction-no-go-regression.sh|\
    scripts/governed-learning-memory-promotion-operator-evaluation-check.sh|\
    scripts/governed-learning-memory-promotion-operator-evaluation-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-authorization-check.sh|\
    scripts/governed-learning-memory-local-persistence-authorization-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-runtime-hold.sh|\
    scripts/governed-learning-memory-local-persistence-check.sh|\
    scripts/governed-learning-memory-local-persistence-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-pilot-evidence-check.sh|\
    scripts/governed-learning-memory-local-persistence-run.py|\
    scripts/governed-learning-memory-engagement-application-operator-evaluation-check.sh|\
    scripts/governed-learning-memory-engagement-application-operator-evaluation-no-go-regression.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-authorization-check.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-authorization-no-go-regression.sh|\
    scripts/governed-learning-memory-continual-learning-pilot-runtime-hold.sh|\
    scripts/lib/governed_learning_memory_promotion_operator_evaluation.py|\
    scripts/lib/governed_learning_memory_local_persistence_authorization.py|\
    scripts/lib/governed_learning_memory_engagement_application_operator_evaluation.py|\
    scripts/lib/governed_learning_memory_continual_learning_pilot_authorization.py|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/self_improvement_governance.py|\
    scripts/auth-design-check.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/operator-action-write-path-no-go-regression.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    services/brain-api/tests/conftest.py|\
    services/brain-api/tests/test_governed_learning_memory_*.py)
      return 0
      ;;
    services/brain-api/src/aion_brain/contracts/governed_learning_memory.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/rollback.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/integrity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/evidence.py)
      return 0
      ;;
  esac
  return 1
}

is_prohibited_path() {
  if is_aion226_path "$1"; then
    return 1
  fi
  if is_aion228_path "$1"; then
    return 1
  fi
  if aion224_implemented_state && is_aion224_source_path "$1"; then
    return 1
  fi
  case "$1" in
    services/brain-api/src/aion_brain/contracts/governed_learning_memory.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/rollback.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/integrity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/evidence.py)
      return 1
      ;;
    .github/workflows/*|\
    services/brain-api/src/aion_brain/*|\
    services/brain-api/pyproject.toml|\
    packages/aion-sdk-python/src/*|\
    migrations/*|services/brain-api/migrations/*|infra/postgres/migrations/*|\
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|poetry.lock|uv.lock|Pipfile|Pipfile.lock|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      return 0
      ;;
  esac
  return 1
}

changed_entries() {
  local base
  if [[ "$mode" == "feature" ]]; then
    if base="$(comparison_base)"; then
      git diff --name-status "$base" HEAD --
    else
      echo "WARN: comparison base unavailable; relying on working tree and committed artifacts" >&2
    fi
  fi
  git diff --name-status HEAD --
  git diff --cached --name-status --
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
      echo "ERROR: prohibited AION-221 surface changed: $changed" >&2
      exit 1
    fi
    if ! is_allowed_path "$changed"; then
      echo "ERROR: path outside AION-221 scope: $changed" >&2
      exit 1
    fi
  done
done < <(changed_entries)

for path in \
  services/brain-api/src/aion_brain/contracts/governed_learning_memory.py \
  services/brain-api/src/aion_brain/governed_learning_memory/__init__.py \
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py \
  services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py \
  services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py \
  services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py \
  services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py \
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py \
  services/brain-api/src/aion_brain/governed_learning_memory/rollback.py \
  services/brain-api/src/aion_brain/governed_learning_memory/integrity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/evidence.py; do
  if [[ ! -f "$path" ]]; then
    echo "ERROR: AION-222 implementation source missing: $path" >&2
    exit 1
  fi
done

scan_paths=(
  docs/governed-learning-memory
  docs/release/governed-learning-memory-program-authorization.md
  docs/release/governed-learning-memory-explicit-approval-record.md
  docs/release/governed-learning-memory-scope.md
  docs/release/governed-learning-memory-runtime-hold.md
  docs/release/governed-learning-memory-no-go.md
  docs/release/governed-learning-memory-checklist.md
  docs/release/governed-learning-memory-evidence-matrix.md
  examples/governed-learning-memory
  operator-console-static/demo-data/governed-learning-memory-program.json
  operator-console-static/demo-data/governed-learning-memory-authorization.json
  operator-console-static/demo-data/governed-learning-memory-roadmap.json
  operator-console-static/demo-data/governed-learning-memory-boundary.json
  operator-console-static/demo-data/governed-learning-memory-runtime-hold.json
)

if rg -n '\b(implementation_approved|runtime_enabled|actual_knowledge_promotion_enabled|persistent_knowledge_write_enabled|persistent_verified_knowledge_write_enabled|knowledge_database_enabled|cognitive_memory_write_enabled|semantic_memory_write_enabled|episodic_memory_write_enabled|procedural_memory_write_enabled|cognitive_belief_creation_enabled|cognitive_belief_mutation_enabled|automatic_candidate_approval_enabled|automatic_knowledge_promotion_enabled|automatic_memory_ingestion_enabled|automatic_engagement_learning_application_enabled|engagement_factual_effect_enabled|engagement_confidence_effect_enabled|background_learning_enabled|scheduled_learning_enabled|runtime_source_rewrite_enabled|source_mutation_enabled|git_mutation_enabled|real_pull_request_creation_enabled|approval_creation_by_runtime_enabled|automatic_merge_enabled|production_deployment_enabled|model_weight_training_enabled|public_network_access_enabled|search_provider_integration_enabled|connector_integration_enabled|model_provider_integration_enabled|actual_tool_execution_enabled|shell_command_execution_enabled|subprocess_execution_enabled|browser_automation_enabled|api_route_enabled|installed_cli_command_enabled|kernel_registration_enabled|application_startup_registration_enabled|scheduler_enabled|background_worker_enabled|production_exposure|v02_release_ready|v02_tag_created|v02_release_created)\s*[:=]\s*true\b|"(runtime_enabled|actual_knowledge_promotion_enabled|persistent_knowledge_write_enabled|persistent_verified_knowledge_write_enabled|knowledge_database_enabled|cognitive_memory_write_enabled|semantic_memory_write_enabled|episodic_memory_write_enabled|procedural_memory_write_enabled|cognitive_belief_creation_enabled|cognitive_belief_mutation_enabled|automatic_candidate_approval_enabled|automatic_knowledge_promotion_enabled|automatic_memory_ingestion_enabled|automatic_engagement_learning_application_enabled|engagement_factual_effect_enabled|engagement_confidence_effect_enabled|background_learning_enabled|scheduled_learning_enabled|runtime_source_rewrite_enabled|source_mutation_enabled|git_mutation_enabled|real_pull_request_creation_enabled|approval_creation_by_runtime_enabled|automatic_merge_enabled|production_deployment_enabled|model_weight_training_enabled|public_network_access_enabled|search_provider_integration_enabled|connector_integration_enabled|model_provider_integration_enabled|actual_tool_execution_enabled|shell_command_execution_enabled|subprocess_execution_enabled|browser_automation_enabled|api_route_enabled|installed_cli_command_enabled|kernel_registration_enabled|application_startup_registration_enabled|scheduler_enabled|background_worker_enabled|production_exposure|v02_release_ready|v02_tag_created|v02_release_created)"[[:space:]]*:[[:space:]]*true' "${scan_paths[@]}"; then
  echo "ERROR: prohibited governed-learning-memory runtime or release flag enabled" >&2
  exit 1
fi

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*.jsonl' '*.state' | rg -n '(^|/)governed-learning-memory|knowledge.*state|memory.*state'; then
  echo "ERROR: tracked persistent knowledge or memory state candidate exists" >&2
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

echo "governed learning memory program no-go PASS"

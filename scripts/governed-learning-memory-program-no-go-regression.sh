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

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/governed-learning-memory/*|\
    docs/release/governed-learning-memory-*|\
    docs/adr/0185-governed-learning-and-memory-integration-program-charter.md|\
    docs/adr/0186-approval-bound-knowledge-promotion-transaction-core.md|\
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
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/self_improvement_governance.py|\
    scripts/operator-action-write-path-no-go-regression.sh|\
    scripts/production-auth-architecture-check.sh|\
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

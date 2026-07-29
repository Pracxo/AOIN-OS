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
  rg -q '"program_state"[[:space:]]*:[[:space:]]*"(governed_learning_memory_local_append_only_persistence_implemented_operator_invoked_isolated_pending_closeout|governed_learning_memory_engagement_application_authorized_not_implemented)"' \
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

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/governed-learning-memory/*|\
    docs/release/governed-learning-memory-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0187-promotion-transaction-evaluation-and-local-append-only-knowledge-persistence-authorization.md|\
    docs/adr/0188-operator-approved-local-append-only-knowledge-and-memory-projection-persistence.md|\
    docs/adr/README.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    examples/governed-learning-memory/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/governed-learning-memory-*.json|\
    scripts/governed-learning-memory-promotion-operator-evaluation-check.sh|\
    scripts/governed-learning-memory-promotion-operator-evaluation-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-authorization-check.sh|\
    scripts/governed-learning-memory-local-persistence-authorization-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-runtime-hold.sh|\
    scripts/governed-learning-memory-local-persistence-check.sh|\
    scripts/governed-learning-memory-local-persistence-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-pilot-evidence-check.sh|\
    scripts/governed-learning-memory-local-persistence-run.py|\
    scripts/governed-learning-memory-program-authorization-check.sh|\
    scripts/governed-learning-memory-program-no-go-regression.sh|\
    scripts/governed-learning-memory-runtime-hold.sh|\
    scripts/governed-learning-memory-promotion-transaction-check.sh|\
    scripts/governed-learning-memory-promotion-transaction-no-go-regression.sh|\
    scripts/lib/governed_learning_memory_promotion_operator_evaluation.py|\
    scripts/lib/governed_learning_memory_local_persistence_authorization.py|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/auth-design-check.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/operator-action-write-path-no-go-regression.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/knowledge-intelligence-*-no-go-regression.sh|\
    services/brain-api/tests/conftest.py|\
    services/brain-api/tests/test_governed_learning_memory_*.py)
      return 0
      ;;
  esac
  is_aion224_source_path "$1" && return 0
  return 1
}

is_prohibited_path() {
  case "$1" in
    .github/workflows/*|\
    services/brain-api/src/aion_brain/*|\
    services/brain-api/pyproject.toml|\
    packages/aion-sdk-python/src/*|\
    migrations/*|services/brain-api/migrations/*|infra/postgres/migrations/*|\
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|poetry.lock|uv.lock|Pipfile|Pipfile.lock|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      if aion224_implemented_state && is_aion224_source_path "$1"; then
        return 1
      fi
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
      echo "ERROR: prohibited AION-223 surface changed: $changed" >&2
      exit 1
    fi
    if ! is_allowed_path "$changed"; then
      echo "ERROR: path outside AION-223 scope: $changed" >&2
      exit 1
    fi
  done
done < <(changed_entries)

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*.jsonl' '*.state' | rg -n '(^|/)governed-learning-memory|knowledge.*state|memory.*state|local-persistence'; then
  echo "ERROR: tracked persistent state candidate exists" >&2
  exit 1
fi

if ! aion224_implemented_state && git ls-files | rg -n 'services/brain-api/src/aion_brain/(contracts/governed_learning_memory_persistence.py|governed_learning_memory/local_.*|governed_learning_memory/.*persistence.*[.]py|governed_learning_memory/backup_restore.py)'; then
  echo "ERROR: AION-224 source exists on AION-223 branch" >&2
  exit 1
fi

python_scan_paths=()
for path in \
  scripts/lib/governed_learning_memory_promotion_operator_evaluation.py \
  scripts/lib/governed_learning_memory_local_persistence_authorization.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_operator_evaluation.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_docs.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_scenarios.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_approvals.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_identity.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_conflicts.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_versions.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_projections.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_rollback.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_no_side_effects.py \
  services/brain-api/tests/test_governed_learning_memory_authorization_closeout.py \
  services/brain-api/tests/test_governed_learning_memory_local_persistence_authorization_docs.py \
  services/brain-api/tests/test_governed_learning_memory_local_persistence_authorization_validator.py \
  services/brain-api/tests/test_governed_learning_memory_local_persistence_scope_spec.py \
  services/brain-api/tests/test_governed_learning_memory_local_persistence_budget_spec.py \
  services/brain-api/tests/test_governed_learning_memory_local_persistence_sqlite_policy.py \
  services/brain-api/tests/test_governed_learning_memory_local_persistence_approval_policy.py \
  services/brain-api/tests/test_governed_learning_memory_local_persistence_threat_model.py; do
  [[ -e "$path" ]] && python_scan_paths+=("$path")
done

docs_scan_paths=()
for path in \
  docs/governed-learning-memory \
  docs/release/governed-learning-memory-promotion-evaluation-closeout.md \
  docs/release/governed-learning-memory-promotion-evaluation-checklist.md \
  docs/release/governed-learning-memory-promotion-evaluation-evidence-matrix.md \
  docs/release/governed-learning-memory-promotion-evaluation-runtime-hold.md \
  docs/release/governed-learning-memory-local-persistence-authorization-transaction.md \
  docs/release/governed-learning-memory-local-persistence-explicit-approval-record.md \
  docs/release/governed-learning-memory-local-persistence-scope.md \
  docs/release/governed-learning-memory-local-persistence-runtime-hold.md \
  docs/release/governed-learning-memory-local-persistence-no-go.md \
  docs/release/governed-learning-memory-local-persistence-checklist.md \
  docs/release/governed-learning-memory-local-persistence-evidence-matrix.md \
  examples/governed-learning-memory \
  operator-console-static/demo-data/governed-learning-memory-promotion-evaluation.json \
  operator-console-static/demo-data/governed-learning-memory-local-persistence-authorization.json \
  operator-console-static/demo-data/governed-learning-memory-local-persistence-approval.json \
  operator-console-static/demo-data/governed-learning-memory-local-persistence-schema.json \
  operator-console-static/demo-data/governed-learning-memory-local-persistence-version.json \
  operator-console-static/demo-data/governed-learning-memory-local-persistence-projection.json \
  operator-console-static/demo-data/governed-learning-memory-local-persistence-integrity.json \
  operator-console-static/demo-data/governed-learning-memory-local-persistence-runtime-hold.json; do
  [[ -e "$path" ]] && docs_scan_paths+=("$path")
done

if ((${#python_scan_paths[@]})) && rg -n '^[[:space:]]*(from|import)[[:space:]]+(subprocess|socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|git|github|playwright|selenium)([[:space:].]|$)' "${python_scan_paths[@]}"; then
  echo "ERROR: prohibited runtime, network, Git, browser, or SQLite import found" >&2
  exit 1
fi

if ((${#python_scan_paths[@]})) && rg -n '(^|[^[:alnum:]_])(subprocess|socket|requests|httpx|aiohttp|sqlite3|git|github|playwright|selenium)[.]|urllib[.]request|(^|[^[:alnum:]_])os[.]system|ApprovalService|ApprovalRepository|MemoryRepository|BeliefRepository|create_belief[(]|persist_knowledge[(]' "${python_scan_paths[@]}"; then
  echo "ERROR: prohibited runtime or write primitive found" >&2
  exit 1
fi

if ((${#docs_scan_paths[@]})) && rg -n 'automatic_knowledge_promotion_enabled[\"[:space:]]*:[[:space:]]*true|production_exposure[\"[:space:]]*:[[:space:]]*true|v02_release_ready[\"[:space:]]*:[[:space:]]*true' "${docs_scan_paths[@]}"; then
  echo "ERROR: prohibited governed-learning-memory safety flag enabled" >&2
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

echo "governed learning memory promotion operator evaluation no-go PASS"

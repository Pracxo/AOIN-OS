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

AUTHORIZED_SOURCE=(
  services/brain-api/src/aion_brain/contracts/governed_learning_memory.py
  services/brain-api/src/aion_brain/governed_learning_memory/__init__.py
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py
  services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py
  services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py
  services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py
  services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py
  services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py
  services/brain-api/src/aion_brain/governed_learning_memory/rollback.py
  services/brain-api/src/aion_brain/governed_learning_memory/integrity.py
  services/brain-api/src/aion_brain/governed_learning_memory/evidence.py
)

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

is_authorized_source() {
  local candidate="$1"
  local path
  for path in "${AUTHORIZED_SOURCE[@]}"; do
    [[ "$candidate" == "$path" ]] && return 0
  done
  return 1
}

is_allowed_path() {
  if is_authorized_source "$1"; then
    return 0
  fi
  case "$1" in
    README.md|AGENTS.md|\
    docs/governed-learning-memory/*|\
    docs/release/governed-learning-memory-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0186-approval-bound-knowledge-promotion-transaction-core.md|\
    docs/adr/0187-promotion-transaction-evaluation-and-local-append-only-knowledge-persistence-authorization.md|\
    docs/adr/README.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    examples/governed-learning-memory/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/governed-learning-memory-*.json|\
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
    scripts/lib/governed_learning_memory_promotion_operator_evaluation.py|\
    scripts/lib/governed_learning_memory_local_persistence_authorization.py|\
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
    scripts/auth-design-check.sh|\
    scripts/operator-action-write-path-no-go-regression.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/static-console-safety-check.sh|\
    services/brain-api/tests/conftest.py|\
    services/brain-api/tests/test_governed_learning_memory_*.py)
      return 0
      ;;
  esac
  return 1
}

is_prohibited_path() {
  if is_authorized_source "$1"; then
    return 1
  fi
  case "$1" in
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
      echo "ERROR: prohibited AION-222 surface changed: $changed" >&2
      exit 1
    fi
    if ! is_allowed_path "$changed"; then
      echo "ERROR: path outside AION-222 scope: $changed" >&2
      exit 1
    fi
  done
done < <(changed_entries)

for path in "${AUTHORIZED_SOURCE[@]}"; do
  [[ -f "$path" ]] || {
    echo "ERROR: authorized AION-222 source missing: $path" >&2
    exit 1
  }
done

source_files=("${AUTHORIZED_SOURCE[@]}")
if rg -n 'ApprovalService|ApprovalRepository|MemoryRepository|BeliefRepository|memory_write_service|belief_write_service|semantic_index_write|connector_runtime_call|external_connector_call|runtime_pull_request|runtime_approval|create_memory_record|create_belief|persist_knowledge|persist_candidate' "${source_files[@]}"; then
  echo "ERROR: prohibited approval, memory, belief, or persistence primitive found in AION-222 source" >&2
  exit 1
fi

if rg -n '^[[:space:]]*(from|import)[[:space:]]+(subprocess|socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|git|github|playwright|selenium)([[:space:].]|$)' "${source_files[@]}"; then
  echo "ERROR: prohibited runtime or persistence primitive found in AION-222 source" >&2
  exit 1
fi

if rg -n 'subprocess[.]|socket[.]|requests[.]|httpx[.]|aiohttp[.]|urllib[.]request|sqlite3[.]|os[.]system|[.]write_text[(]|[.]write_bytes[(]|git[.]|github[.]|playwright[.]|selenium[.]' "${source_files[@]}"; then
  echo "ERROR: prohibited runtime call found in AION-222 source" >&2
  exit 1
fi

if rg -n '\b(APIRouter|FastAPI|click[.]command|argparse[.]ArgumentParser|celery|scheduler|background_worker|startup|add_event_handler|include_router)\b' "${source_files[@]}"; then
  echo "ERROR: runtime registration primitive found in AION-222 source" >&2
  exit 1
fi

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*.jsonl' '*.state' | rg -n '(^|/)governed-learning-memory|knowledge.*state|memory.*state|promotion.*journal'; then
  echo "ERROR: tracked persistent knowledge, memory, or promotion state candidate exists" >&2
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

echo "governed learning memory promotion transaction no-go PASS"

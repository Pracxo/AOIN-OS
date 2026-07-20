#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "$GITHUB_BASE_REF"; do
      if git_ref_exists "$candidate" && git merge-base HEAD "$candidate" >/dev/null 2>&1; then
        git merge-base HEAD "$candidate"
        return 0
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate" && git merge-base HEAD "$candidate" >/dev/null 2>&1; then
      git merge-base HEAD "$candidate"
      return 0
    fi
  done
  if git_ref_exists HEAD~1; then
    printf '%s\n' HEAD~1
    return 0
  fi
  return 1
}

is_allowed_activation_source() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_activation.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_activation_policy.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_activation_approval.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_activation_monitoring.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_activation_deactivation.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_activation_evidence.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_activation_simulator.py)
      return 0
      ;;
  esac
  return 1
}

if base="$(comparison_base)"; then
  while IFS= read -r changed; do
    [[ -z "$changed" ]] && continue
    case "$changed" in
      .github/workflows/*|migrations/*|packages/aion-sdk-python/src/*)
        echo "blocked protected change: $changed" >&2
        exit 1
        ;;
      services/brain-api/pyproject.toml|services/brain-api/poetry.lock|services/brain-api/requirements.txt)
        echo "blocked dependency change: $changed" >&2
        exit 1
        ;;
      package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|packages/*/package.json|packages/*/package-lock.json)
        echo "blocked package file change: $changed" >&2
        exit 1
        ;;
      services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_mode.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_observation.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_budget.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py|\
services/brain-api/src/aion_brain/self_improvement/shadow_runner.py|\
services/brain-api/src/aion_brain/self_improvement/governance.py|\
services/brain-api/src/aion_brain/self_improvement/approval.py|\
services/brain-api/src/aion_brain/self_improvement/protected_paths.py|\
services/brain-api/src/aion_brain/self_improvement/risk.py|\
services/brain-api/src/aion_brain/self_improvement/worktree.py|\
services/brain-api/src/aion_brain/self_improvement/patch_generator.py|\
services/brain-api/src/aion_brain/self_improvement/git_controller.py|\
services/brain-api/src/aion_brain/self_improvement/pr_controller.py|\
services/brain-api/src/aion_brain/self_improvement/merge_controller.py|\
services/brain-api/src/aion_brain/self_improvement/canary.py|\
services/brain-api/src/aion_brain/self_improvement/rollback_controller.py)
        echo "blocked shadow source change: $changed" >&2
        exit 1
        ;;
      services/brain-api/src/aion_brain/policy/*|services/brain-api/src/aion_brain/audit/*|\
services/brain-api/src/aion_brain/security/*|services/brain-api/src/aion_brain/kernel/*|\
services/brain-api/src/aion_brain/api/*|services/brain-api/src/aion_brain/api_support/*|\
services/brain-api/src/aion_brain/config.py)
        echo "blocked runtime source change: $changed" >&2
        exit 1
        ;;
      services/brain-api/src/aion_brain/*)
        if ! is_allowed_activation_source "$changed"; then
          echo "blocked unapproved activation source change: $changed" >&2
          exit 1
        fi
        ;;
    esac
  done < <(git diff --name-only "$base" HEAD)
else
  echo "WARN: comparison base unavailable; relying on current-tree checks" >&2
fi

for path in \
  services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_policy.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_approval.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_monitoring.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_deactivation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_evidence.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_simulator.py; do
  test -f "$path" || {
    echo "missing AION-181 activation source: $path" >&2
    exit 1
  }
done

if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(subprocess|socket|requests|httpx|aiohttp|git|github)' \
  services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation*.py; then
  echo "prohibited import detected" >&2
  exit 1
fi

if rg -n 'self_improvement\.(worktree|patch_generator|git_controller|pr_controller|merge_controller|canary|rollback_controller)' \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation*.py; then
  echo "prohibited controller dependency detected" >&2
  exit 1
fi

if rg -n 'KernelContainer|include_router|add_event_handler|on_event|startup|scheduler|create_task' \
  services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation*.py; then
  echo "runtime registration detected" >&2
  exit 1
fi

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-activation-control-plane-no-go

aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "self improvement shadow activation control plane no-go PASS"

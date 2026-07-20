#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

CONTROL_PLANE_STAGE="$("$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ledger = json.loads(Path("docs/self-improvement/authorization-ledger.json").read_text())
print(ledger.get("current_stage", ""))
PY
)"

is_allowed_activation_source() {
  [[ "$CONTROL_PLANE_STAGE" == "shadow_activation_control_plane_implemented_disabled_pending_closeout" ]] || return 1
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

if base="$(comparison_base)"; then
  while IFS= read -r changed; do
    [[ -z "$changed" ]] && continue
    case "$changed" in
      .github/workflows/*|migrations/*|packages/aion-sdk-python/src/*)
        echo "blocked runtime/protected source change: $changed" >&2
        exit 1
        ;;
      services/brain-api/src/aion_brain/*)
        if ! is_allowed_activation_source "$changed"; then
          echo "blocked runtime/protected source change: $changed" >&2
          exit 1
        fi
        ;;
      services/brain-api/pyproject.toml|services/brain-api/poetry.lock|services/brain-api/requirements.txt)
        echo "blocked dependency change: $changed" >&2
        exit 1
        ;;
      package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|packages/*/package.json|packages/*/package-lock.json)
        echo "blocked package file change: $changed" >&2
        exit 1
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
  if [[ "$CONTROL_PLANE_STAGE" == "shadow_activation_control_plane_implemented_disabled_pending_closeout" ]]; then
    test -f "$path" || {
      echo "AION-181 activation source must exist after implementation: $path" >&2
      exit 1
    }
  else
    test ! -e "$path" || {
      echo "AION-181 runtime source must be absent in AION-180: $path" >&2
      exit 1
    }
  fi
done

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-activation-authorization-no-go

aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "self improvement shadow activation authorization no-go PASS"

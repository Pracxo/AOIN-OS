#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

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
  if git_ref_exists HEAD^1; then
    echo "HEAD^1"
    return 0
  fi
  return 1
}

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/adr/0202-final-secure-runtime-integration-evaluation-and-v02-release-qualification-program-authorization.md|\
    docs/adr/README.md|\
    docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/project-status.md|docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/v02-release-qualification/*|\
    docs/release/secure-runtime-integration-*|\
    docs/release/v02-release-qualification-*|\
    docs/release/operator-console-integration-implementation.md|\
    docs/release/operator-console-integrated-local-pilot.md|\
    docs/release/operator-console-integration-runtime-hold.md|\
    docs/release/v02-release-readiness-delta.md|\
    examples/secure-runtime-integration/*|\
    examples/v02-release-qualification/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/secure-runtime-integration-*.json|\
    operator-console-static/demo-data/v02-release-qualification-*.json|\
    scripts/secure-runtime-integration-final-evaluation-check.sh|\
    scripts/secure-runtime-integration-final-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-complete-check.sh|\
    scripts/v02-release-qualification-program-authorization-check.sh|\
    scripts/v02-release-qualification-program-authorization-no-go-regression.sh|\
    scripts/v02-release-qualification-runtime-hold.sh|\
    scripts/lib/secure_runtime_integration_final_evaluation.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    services/brain-api/tests/secure_runtime_integration_final_evaluation_test_support.py|\
    services/brain-api/tests/test_secure_runtime_integration_final_evaluation_aion238.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion232.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion234.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion236.py|\
    services/brain-api/tests/test_secure_runtime_current_state_consistency.py|\
    services/brain-api/tests/test_secure_runtime_integration_authorization.py|\
    services/brain-api/tests/test_secure_runtime_integration_program_charter.py|\
    services/brain-api/tests/test_secure_runtime_integration_project_status.py|\
    services/brain-api/tests/test_secure_runtime_integration_scope.py|\
    services/brain-api/tests/test_operator_console_integration_authorization.py)
      return 0
      ;;
  esac
  return 1
}

base="$(comparison_base || true)"
if [[ -n "$base" ]]; then
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    if ! is_allowed_path "$path"; then
      echo "AION-238 changed path outside final-evaluation boundary: $path" >&2
      exit 1
    fi
  done < <(git diff --name-only "$base" HEAD)
fi

if git diff --name-only "${base:-HEAD}" HEAD | rg -n '^\.github/workflows/' >/dev/null 2>&1; then
  echo "AION-238 must not modify GitHub workflows" >&2
  exit 1
fi

if git diff --name-only "${base:-HEAD}" HEAD | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|pyproject\.toml)$' >/dev/null 2>&1; then
  echo "AION-238 must not modify package manifests or lockfiles" >&2
  exit 1
fi

if git diff --name-only "${base:-HEAD}" HEAD | rg -n '(^migrations/|/migrations/)' >/dev/null 2>&1; then
  echo "AION-238 must not add migrations" >&2
  exit 1
fi

if git diff --name-only "${base:-HEAD}" HEAD | rg -n '^services/brain-api/src/aion_brain/' >/dev/null 2>&1; then
  echo "AION-238 primary branch must not modify runtime source" >&2
  exit 1
fi

if [[ -e services/brain-api/src/aion_brain/contracts/v02_release_qualification.py || \
  -e services/brain-api/src/aion_brain/v02_release_qualification ]]; then
  echo "AION-238 must not create AION-239 runtime source" >&2
  exit 1
fi

if git tag -l 'aion-v0.2*' 'v0.2*' | rg -n '.' >/dev/null 2>&1; then
  echo "AION-238 must not create a v0.2 tag" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

paths = [
    Path("docs/secure-runtime-integration/program-ledger.json"),
    Path("docs/secure-runtime-integration/authorization-ledger.json"),
]
for path in paths:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("v02_release_ready") is not False:
            raise SystemExit(f"{path} must keep v02_release_ready=false")
        for key in (
            "production_runtime_authorized",
            "public_listener_enabled",
            "external_network_egress_enabled",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"{path} must keep {key}=false")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
echo "secure runtime integration final evaluation no-go PASS"

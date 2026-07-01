#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_POST_V01_RELEASE_CANDIDATE_FREEZE_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

if is_nested_gate_context; then
  echo "PASS: post-v0.1 release candidate gate deferred to outer aggregate gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/post-v01-release-candidate-gate.sh
fi
git diff --check

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/check.sh
fi

echo "Post-v0.1 release candidate working tree summary:"
git status --short --branch

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0)$'; then
  echo "v0.2 tag must not exist for AION-118" >&2
  exit 1
fi

tag_ref="unavailable"
if git_ref_exists aion-v0.1.0; then
  tag_ref="$(git rev-parse aion-v0.1.0)"
  if git_ref_exists origin/main; then
    if git merge-base --is-ancestor aion-v0.1.0 origin/main; then
      echo "aion-v0.1.0 is in origin/main history"
    else
      echo "WARN: aion-v0.1.0 ancestry could not be confirmed against origin/main" >&2
    fi
  elif git_ref_exists main; then
    if git merge-base --is-ancestor aion-v0.1.0 main; then
      echo "aion-v0.1.0 is in main history"
    else
      echo "WARN: aion-v0.1.0 ancestry could not be confirmed against main" >&2
    fi
  else
    echo "WARN: origin/main unavailable in this checkout; skipping non-release tag ancestry confirmation"
  fi
else
  if is_nested_gate_context || [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    echo "WARN: aion-v0.1.0 tag unavailable in this checkout; skipping non-release tag ancestry confirmation"
  else
    echo "aion-v0.1.0 tag is missing" >&2
    exit 1
  fi
fi

cat <<SUMMARY
Post-v0.1 release candidate freeze result:
- v02_tag_created: false
- v02_release_approved: false
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
- aion_v0_1_0: ${tag_ref}
post-v0.1 release candidate freeze PASS
SUMMARY

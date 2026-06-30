#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local candidates=()
  candidates+=(origin/main main)
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    candidates+=("origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}")
  fi

  for candidate in "${candidates[@]}"; do
    if git_ref_exists "$candidate"; then
      git merge-base HEAD "$candidate" 2>/dev/null && return 0
    fi
  done
  if git_ref_exists HEAD~1; then
    printf '%s\n' "HEAD~1"
    return 0
  fi
  return 1
}

changed_files() {
  local base
  if base="$(comparison_base)"; then
    git diff --name-only --diff-filter=ACMRT "$base" HEAD --
  fi
  git ls-files --others --exclude-standard
}

required_docs=(
  docs/platform/post-v01-platform-integration-checkpoint.md
  docs/platform/cross-phase-evidence-pack.md
  docs/platform/operator-connector-boundary-matrix.md
  docs/platform/future-runtime-boundary-freeze.md
  docs/platform/platform-integration-risk-register.md
  docs/platform/implementation-approval-state-summary.md
  docs/platform/platform-integration-closeout-checklist.md
  docs/adr/0108-post-v01-platform-integration-checkpoint.md
)

required_examples=(
  examples/platform/post-v01-platform-integration-checkpoint.json
  examples/platform/cross-phase-evidence-pack.json
  examples/platform/operator-connector-boundary-matrix.json
  examples/platform/future-runtime-boundary-freeze.json
  examples/platform/implementation-approval-state-summary.json
  operator-console-static/demo-data/platform-integration-checkpoint.json
  operator-console-static/demo-data/future-runtime-boundary-freeze.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing platform integration artifact: $file" >&2
    exit 1
  }
done

grep -q "0108-post-v01-platform-integration-checkpoint.md" docs/adr/README.md || {
  echo "ADR 0108 is not indexed" >&2
  exit 1
}

./scripts/platform-integration-no-go-regression.sh

AION_OPERATOR_PLATFORM_SKIP_FULL_CHECK=1 ./scripts/operator-platform-regression.sh
AION_OPERATOR_PLATFORM_SKIP_FULL_CHECK=1 AION_OPERATOR_PLATFORM_FREEZE_SKIP_REGRESSION=1 ./scripts/operator-platform-freeze-gate.sh
export AION_CONNECTOR_RUNTIME_REVIEW_SKIP_OPERATOR_FREEZE=1
AION_AGGREGATE_GATE_RUNNING=1 AION_CONNECTOR_PLATFORM_REGRESSION_SKIP_NESTED_GATES=1 ./scripts/connector-platform-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_CONNECTOR_PLATFORM_REGRESSION_SKIP_NESTED_GATES=1 ./scripts/connector-platform-stabilization-gate.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_CONNECTOR_PLATFORM_CHECKPOINT_SKIP_RELEASE_GATES=1 ./scripts/connector-platform-checkpoint.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_CONNECTOR_PLATFORM_FREEZE_SKIP_CHECKPOINT=1 ./scripts/connector-platform-freeze-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-release-gate.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_CONNECTOR_SAFETY_FREEZE_SKIP_RELEASE_GATE=1 ./scripts/connector-safety-freeze.sh
./scripts/auth-prototype-review.sh
./scripts/auth-no-go-regression.sh
AION_OPERATOR_PLATFORM_SKIP_FULL_CHECK=1 ./scripts/module-activation-design-review.sh
./scripts/module-activation-no-go-regression.sh
./scripts/ui-release-gate.sh
./scripts/static-console-safety-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-117: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-117 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-117 must not add or change API router files" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-117 must not add or change SDK resources or CLI implementations" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/platform/post-v01-platform-integration-checkpoint.json",
    root / "examples/platform/cross-phase-evidence-pack.json",
    root / "examples/platform/operator-connector-boundary-matrix.json",
    root / "examples/platform/future-runtime-boundary-freeze.json",
    root / "examples/platform/implementation-approval-state-summary.json",
    root / "operator-console-static/demo-data/platform-integration-checkpoint.json",
    root / "operator-console-static/demo-data/future-runtime-boundary-freeze.json",
]
false_keys = {
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "oauth_oidc_saml_runtime_approved",
    "code_loading_approved",
    "runtime_registration_approved",
    "capability_activation_approved",
    "package_files_added",
    "migrations_added",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "aion_v0_1_0_touched",
}
required_true = {
    "checkpoint_passed",
    "integration_gate_passed",
}
blocked_fragments = (
    "http://",
    "https://",
    "sk-",
    "ghp_",
    "xoxb-",
    "-----BEGIN PRIVATE KEY-----",
    "bearer ",
    "basic ",
    "api_key",
    "private_key",
    "access_token",
    "refresh_token",
    "id_token",
    "client_secret",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
)


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in required_true and nested is not True:
                raise SystemExit(f"{context}.{key} must be true")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for fragment in blocked_fragments:
            if fragment in lowered:
                raise SystemExit(f"{context} contains blocked marker: {fragment}")


for path in paths:
    payload = json.loads(path.read_text())
    if path.relative_to(root).as_posix().startswith("examples/"):
        if payload.get("synthetic") is not True:
            raise SystemExit(f"platform example must be synthetic: {path}")
    walk(payload, path.relative_to(root).as_posix())

print("Platform integration JSON checks PASS")
PY

cat <<'SUMMARY'
Platform integration checkpoint result:
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
- package_files_added: false
- migrations_added: false
platform integration checkpoint PASS
SUMMARY

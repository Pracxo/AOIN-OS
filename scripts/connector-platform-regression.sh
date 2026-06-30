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
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    candidates+=("origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}")
  fi
  candidates+=(origin/main main)

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
  docs/connectors/connector-platform-stabilization-runbook.md
  docs/connectors/connector-long-running-regression-matrix.md
  docs/connectors/connector-phase-freeze-gate.md
  docs/connectors/connector-stabilization-evidence-pack.md
  docs/connectors/connector-safety-baseline-lock.md
  docs/connectors/connector-regression-evidence.md
  docs/adr/0107-connector-platform-stabilization-gate.md
)

required_examples=(
  examples/connectors/connector-platform-stabilization-result.json
  examples/connectors/connector-long-running-regression-matrix.json
  examples/connectors/connector-phase-freeze-gate-result.json
  examples/connectors/connector-stabilization-evidence-pack.json
  operator-console-static/demo-data/connector-platform-stabilization.json
  operator-console-static/demo-data/connector-phase-freeze-gate.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing connector platform stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0107-connector-platform-stabilization-gate.md" docs/adr/README.md || {
  echo "ADR 0107 is not indexed" >&2
  exit 1
}

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-platform-checkpoint.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-platform-freeze-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-release-gate.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-safety-freeze.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-release-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-runtime-review.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-runtime-no-external-call-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-simulator-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-simulator-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-policy-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-policy-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-sandbox-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-sandbox-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-credential-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/connector-credential-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/docs-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/final-docs-audit.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/verify-no-domain-drift.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/boundary-check.sh

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-116: $file" >&2
    exit 1
  fi
done

if changed_files | rg -n '^infra/postgres/migrations/|^services/brain-api/migrations/'; then
  echo "AION-116 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/api/'; then
  echo "AION-116 must not add or change API router files" >&2
  exit 1
fi

if changed_files | rg -n '^packages/aion-sdk-python/src/aion_sdk/(resources/|cli/commands/|client\.py|cli/main\.py)'; then
  echo "AION-116 must not add or change SDK resources or CLI implementations" >&2
  exit 1
fi

if changed_files | rg -n '^services/brain-api/src/aion_brain/(connector_runtime|connector_simulator|connector_policy|connector_sandbox|connector_credentials)/|^services/brain-api/src/aion_brain/config\.py$|^\.env\.example$'; then
  echo "AION-116 must not add or change connector runtime source or runtime config defaults" >&2
  exit 1
fi

if rg -n '\b(connector_runtime_enabled|connector_external_calls_enabled|connector_credentials_enabled|connector_token_storage_enabled|connector_activation_enabled|connector_route_registration_enabled|external_calls_enabled|sandbox_execution_enabled|connector_activation_enabled|route_registration_enabled|implementation_approved|package_files_added|migrations_added)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors; then
  echo "connector platform unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(connector_sandbox_runtime_execution_enabled|connector_sandbox_filesystem_enabled|connector_sandbox_network_enabled|connector_sandbox_process_spawn_enabled|connector_sandbox_dynamic_import_enabled|connector_sandbox_package_install_enabled|connector_sandbox_activation_enabled)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors; then
  echo "connector sandbox unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(connector_credentials_storage_enabled|connector_tokens_storage_enabled|connector_secret_material_enabled|connector_external_identity_runtime_enabled|connector_runtime_credential_access_enabled|credential_storage_enabled|token_storage_enabled|secret_material_present|credentials_present)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors; then
  echo "connector credential/token unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(oauth|oidc|saml)[-_ ]?runtime[-_ ]?enabled\s*[:=]\s*true\b|external_identity_runtime_enabled\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors; then
  echo "external identity runtime enablement found" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  services/brain-api/src/aion_brain operator-console-static examples/connectors; then
  echo "connector platform external call pattern found" >&2
  exit 1
fi

if rg -n '\b(connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==)\b' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "connector or provider SDK dependency found" >&2
  exit 1
fi

if rg -n 'execute_connector|run_connector|connector_runtime_execute' \
  operator-console-static/app.js operator-console-static/index.html; then
  echo "connector runtime execution route pattern found" >&2
  exit 1
fi

if rg -n '<input|<textarea|<select|contenteditable' operator-console-static/index.html operator-console-static/app.js; then
  echo "static console input control found" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-116 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-platform-stabilization-result.json",
    root / "examples/connectors/connector-long-running-regression-matrix.json",
    root / "examples/connectors/connector-phase-freeze-gate-result.json",
    root / "examples/connectors/connector-stabilization-evidence-pack.json",
    root / "operator-console-static/demo-data/connector-platform-stabilization.json",
    root / "operator-console-static/demo-data/connector-phase-freeze-gate.json",
]
false_keys = {
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_present",
    "token_storage_enabled",
    "sandbox_execution_enabled",
    "connector_activation_enabled",
    "route_registration_enabled",
    "implementation_approved",
    "package_files_added",
    "migrations_added",
    "provider_sdk_dependency_added",
    "api_runtime_execution_route_added",
    "endpoint_references_present",
    "secret_material_present",
    "credential_values_present",
    "token_values_present",
    "private_prompt_material_present",
    "private_reasoning_present",
    "runtime_approval",
}
required_true = {
    "release_gate_passed",
    "checkpoint_passed",
    "stabilization_gate_passed",
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
            raise SystemExit(f"stabilization example must be synthetic: {path}")
    walk(payload, path.relative_to(root).as_posix())

print("Connector platform stabilization JSON checks PASS")
PY

cat <<'SUMMARY'
Connector platform regression result:
- connector_runtime: disabled
- external_calls: absent
- credentials_tokens: absent
- sandbox_execution: absent
- implementation_approved: false
- package_files: absent
- migrations: absent
connector platform regression PASS
SUMMARY

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

required_artifacts=(
  docs/platform/post-v01-platform-integration-checkpoint.md
  docs/platform/cross-phase-evidence-pack.md
  docs/platform/operator-connector-boundary-matrix.md
  docs/platform/future-runtime-boundary-freeze.md
  docs/platform/platform-integration-risk-register.md
  docs/platform/implementation-approval-state-summary.md
  docs/platform/platform-integration-closeout-checklist.md
  docs/adr/0108-post-v01-platform-integration-checkpoint.md
  examples/platform/post-v01-platform-integration-checkpoint.json
  examples/platform/cross-phase-evidence-pack.json
  examples/platform/operator-connector-boundary-matrix.json
  examples/platform/future-runtime-boundary-freeze.json
  examples/platform/implementation-approval-state-summary.json
  operator-console-static/demo-data/platform-integration-checkpoint.json
  operator-console-static/demo-data/future-runtime-boundary-freeze.json
)

for file in "${required_artifacts[@]}"; do
  test -f "$file" || {
    echo "missing AION-117 platform integration artifact: $file" >&2
    exit 1
  }
done

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

if changed_files | rg -n '^services/brain-api/src/aion_brain/(connector_runtime|connector_simulator|connector_policy|connector_sandbox|connector_credentials|auth_runtime|local_auth|local_session|action_authorization|modules)/|^services/brain-api/src/aion_brain/config\.py$|^\.env\.example$'; then
  echo "AION-117 must not add or change runtime source or runtime config defaults" >&2
  exit 1
fi

scan_paths=(
  .env.example
  services/brain-api/src
  operator-console-static/demo-data
  examples/platform
  examples/connectors
  examples/auth
  examples/modules
)

if rg -n '\b(operator_write_execution_approved|connector_implementation_approved|production_auth_approved|module_activation_approved|external_calls_approved|credential_storage_approved|token_storage_approved|sandbox_execution_approved|oauth_oidc_saml_runtime_approved|code_loading_approved|runtime_registration_approved|capability_activation_approved|package_files_added|migrations_added|api_runtime_execution_route_added|sdk_resource_implementation_added|cli_command_implementation_added|frontend_dependencies_added)\s*[:=]\s*true\b' \
  "${scan_paths[@]}"; then
  echo "platform integration approval or drift boolean was enabled" >&2
  exit 1
fi

if rg -n '\b(connector_runtime_enabled|connector_external_calls_enabled|connector_credentials_enabled|connector_token_storage_enabled|connector_activation_enabled|connector_route_registration_enabled|external_calls_enabled|sandbox_execution_enabled|connector_activation_enabled|route_registration_enabled|implementation_approved|provider_sdk_dependency_added|api_runtime_execution_route_added)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors examples/platform; then
  echo "connector runtime unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(production_auth_enabled|auth_runtime_enabled|credentials_enabled|token_issuance_enabled|cookie_issuance_enabled|session_persistence_enabled|login_endpoint_enabled|logout_endpoint_enabled|external_identity_provider_enabled|provider_sdk_present)\s*[:=]\s*true\b|PRODUCTION_AUTH_ENABLED=true|AUTH_RUNTIME_ENABLED=true' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/auth examples/platform; then
  echo "production auth unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(activation_enabled|code_loading_enabled|runtime_registration_enabled|capability_activation_enabled|controlled_execution_enabled|package_installation_enabled|external_dependency_download_enabled|executable_payload_accepted|policy_bypass_enabled|audit_bypass_enabled|module_writes_enabled|activation_ready_default)\s*[:=]\s*true\b' \
  services/brain-api/src operator-console-static/demo-data examples/modules examples/platform; then
  echo "module activation unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(connector_sandbox_runtime_execution_enabled|connector_sandbox_filesystem_enabled|connector_sandbox_network_enabled|connector_sandbox_process_spawn_enabled|connector_sandbox_dynamic_import_enabled|connector_sandbox_package_install_enabled|connector_sandbox_activation_enabled)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors examples/platform; then
  echo "connector sandbox unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(connector_credentials_storage_enabled|connector_tokens_storage_enabled|connector_secret_material_enabled|connector_external_identity_runtime_enabled|connector_runtime_credential_access_enabled|credential_storage_enabled|token_storage_enabled|secret_material_present|credentials_present|credential_values_present|token_values_present)\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/connectors examples/platform; then
  echo "credential or token unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(oauth|oidc|saml)[-_ ]?runtime[-_ ]?enabled\s*[:=]\s*true\b|external_identity_runtime_enabled\s*[:=]\s*true\b' \
  .env.example services/brain-api/src operator-console-static/demo-data examples/auth examples/connectors examples/platform; then
  echo "external identity runtime enablement found" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  services/brain-api/src/aion_brain operator-console-static examples/platform examples/connectors; then
  echo "platform integration external call pattern found" >&2
  exit 1
fi

if rg -n '\b(connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==|authlib|python-jose|okta|auth0)\b' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "provider, connector, or auth SDK dependency found" >&2
  exit 1
fi

if rg -n 'execute_connector|run_connector|connector_runtime_execute|execute_operator_write|operator_write_execute|register_runtime_route|sandbox_execute' \
  operator-console-static/app.js operator-console-static/index.html services/brain-api/src/aion_brain; then
  echo "runtime execution, activation, or registration pattern found" >&2
  exit 1
fi

if rg -n '<input|<textarea|<select|contenteditable' operator-console-static/index.html operator-console-static/app.js; then
  echo "static console input control found" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_artifacts[@]}"; then
  echo "package install instruction found in AION-117 artifacts" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  examples/platform operator-console-static/demo-data/platform-integration-checkpoint.json operator-console-static/demo-data/future-runtime-boundary-freeze.json; then
  echo "blocked marker found in AION-117 examples or static data" >&2
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


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    if path.relative_to(root).as_posix().startswith("examples/"):
        if payload.get("synthetic") is not True:
            raise SystemExit(f"platform example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"platform artifact must be passed: {path}")
    walk(payload, path.relative_to(root).as_posix())

print("Platform integration no-go JSON checks PASS")
PY

cat <<'SUMMARY'
Platform integration no-go regression result:
- operator_write_execution: not approved
- connector_runtime: disabled
- production_auth: not approved
- module_activation: not approved
- external_calls: absent
- credentials_tokens: absent
- sandbox_execution: absent
- package_files: absent
- migrations: absent
platform integration no-go regression PASS
SUMMARY

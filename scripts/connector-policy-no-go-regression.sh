#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

policy_source=(
  services/brain-api/src/aion_brain/contracts/connector_policy.py
  services/brain-api/src/aion_brain/api/connector_policy.py
  services/brain-api/src/aion_brain/connector_policy
  packages/aion-sdk-python/src/aion_sdk/resources/connector_policy.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy.py
)

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-111: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-111 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-111 must not add untracked migrations" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  "${policy_source[@]}"; then
  echo "connector policy network call pattern found" >&2
  exit 1
fi

if rg -n '\b(connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==)\b' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "connector or provider SDK dependency found" >&2
  exit 1
fi

if rg -n '\b(connector_policy_runtime_allow_enabled|connector_policy_external_calls_enabled|connector_policy_credentials_enabled|connector_policy_tokens_enabled|connector_policy_activation_enabled)\s*[:=]\s*true\b' \
  services/brain-api/src .env.example operator-console-static examples/connectors; then
  echo "connector policy unsafe enablement found" >&2
  exit 1
fi

if rg -n 'add_api_route|dynamic[_-]?route|route_registration_enabled[[:space:]]*[:=][[:space:]]*true' \
  services/brain-api/src/aion_brain/connector_policy services/brain-api/src/aion_brain/api/connector_policy.py; then
  echo "connector policy route registration pattern found" >&2
  exit 1
fi

if rg -n 'store_credential|credential_store|secret_store|token_store|store_token|external_endpoint|provider_endpoint' \
  services/brain-api/src/aion_brain/connector_policy services/brain-api/src/aion_brain/api/connector_policy.py; then
  echo "connector policy credential, token, or endpoint pattern found" >&2
  exit 1
fi

if rg -n '^\s*@connector_policy_app\.command\("(allow|enable|grant|connect|call|execute)"\)' \
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy.py; then
  echo "connector policy CLI exposes forbidden command" >&2
  exit 1
fi

if rg -n '<button[^>]*>([^<]*)(allow|enable|grant|connect|call)([^<]*)</button>' \
  operator-console-static/index.html operator-console-static/app.js; then
  echo "static console exposes connector policy runtime button" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  examples/connectors/connector-policy-action-catalog.json \
  examples/connectors/connector-authorization-matrix.json \
  examples/connectors/connector-policy-dry-run-request.json \
  examples/connectors/connector-policy-dry-run-result.json \
  examples/connectors/connector-policy-denial-result.json \
  examples/connectors/connector-policy-traceability.json \
  operator-console-static/demo-data/connector-policy-catalog.json \
  operator-console-static/demo-data/connector-policy-dry-run.json; then
  echo "blocked marker found in connector policy examples" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  docs/connectors/connector-policy-action-catalog.md \
  docs/connectors/connector-authorization-matrix.md \
  docs/connectors/connector-policy-dry-run-gate.md \
  docs/connectors/connector-policy-denial-rules.md \
  docs/connectors/connector-policy-traceability.md \
  docs/connectors/connector-policy-no-go.md \
  docs/adr/0102-connector-policy-action-catalog.md; then
  echo "package install instruction found in AION-111 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-policy-action-catalog.json",
    root / "examples/connectors/connector-authorization-matrix.json",
    root / "examples/connectors/connector-policy-dry-run-result.json",
    root / "examples/connectors/connector-policy-denial-result.json",
    root / "operator-console-static/demo-data/connector-policy-catalog.json",
    root / "operator-console-static/demo-data/connector-policy-dry-run.json",
]

false_keys = {
    "allowed_in_runtime",
    "runtime_allowed",
    "external_call_allowed",
    "credential_access_allowed",
    "token_access_allowed",
    "activation_allowed",
    "connector_policy_runtime_allow_enabled",
    "connector_policy_external_calls_enabled",
    "connector_policy_credentials_enabled",
    "connector_policy_tokens_enabled",
    "connector_policy_activation_enabled",
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
    walk(json.loads(path.read_text()), path.relative_to(root).as_posix())

print("Connector policy no-go JSON checks PASS")
PY

echo "Connector policy no-go regression result:"
echo "- connector_runtime: disabled"
echo "- runtime_policy_allow_paths: absent"
echo "- external_calls: absent"
echo "- credentials_tokens: absent"
echo "- activation_routes: disabled"
echo "- forbidden_cli_buttons: absent"
echo "Connector policy no-go regression PASS"

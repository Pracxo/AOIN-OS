#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

simulator_source=(
  services/brain-api/src/aion_brain/contracts/connector_simulator.py
  services/brain-api/src/aion_brain/api/connector_simulator.py
  services/brain-api/src/aion_brain/connector_simulator
  packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator.py
)

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-110: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-110 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-110 must not add untracked migrations" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  "${simulator_source[@]}"; then
  echo "connector simulator network call pattern found" >&2
  exit 1
fi

if rg -n '\b(connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==)\b' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "connector or provider SDK dependency found" >&2
  exit 1
fi

if rg -n '\b(connector_runtime_enabled|connector_external_calls_enabled|connector_credentials_enabled|connector_token_storage_enabled|connector_activation_enabled|connector_route_registration_enabled|connector_simulator_external_calls_enabled|connector_simulator_credentials_enabled|connector_simulator_tokens_enabled|connector_simulator_runtime_activation_enabled)\s*[:=]\s*true\b' \
  services/brain-api/src .env.example operator-console-static examples/connectors; then
  echo "connector unsafe enablement found" >&2
  exit 1
fi

if rg -n 'add_api_route|dynamic[_-]?route|route_registration_enabled[[:space:]]*[:=][[:space:]]*true' \
  services/brain-api/src/aion_brain/connector_simulator services/brain-api/src/aion_brain/api/connector_simulator.py; then
  echo "connector simulator route registration pattern found" >&2
  exit 1
fi

if rg -n 'store_credential|credential_store|secret_store|token_store|store_token|external_endpoint|provider_endpoint' \
  services/brain-api/src/aion_brain/connector_simulator services/brain-api/src/aion_brain/api/connector_simulator.py examples/connectors/connector-simulation*.json examples/connectors/connector-replay-fixture.json examples/connectors/connector-policy-readiness*.json; then
  echo "connector simulator credential, token, or endpoint pattern found" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  examples/connectors/connector-simulation-request.json \
  examples/connectors/connector-simulation-result.json \
  examples/connectors/connector-replay-fixture.json \
  examples/connectors/connector-policy-readiness-request.json \
  examples/connectors/connector-policy-readiness-result.json \
  examples/connectors/connector-simulator-findings.json \
  operator-console-static/demo-data/connector-simulation-preview.json \
  operator-console-static/demo-data/connector-policy-readiness.json; then
  echo "blocked marker found in connector simulator examples" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  docs/connectors/connector-dry-run-simulator.md \
  docs/connectors/synthetic-connector-replay.md \
  docs/connectors/connector-policy-readiness-gate.md \
  docs/connectors/connector-simulation-safety.md \
  docs/connectors/connector-simulator-no-go.md \
  docs/adr/0101-connector-dry-run-simulator-hardening.md; then
  echo "package install instruction found in AION-110 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-simulation-request.json",
    root / "examples/connectors/connector-simulation-result.json",
    root / "examples/connectors/connector-replay-fixture.json",
    root / "examples/connectors/connector-policy-readiness-request.json",
    root / "examples/connectors/connector-policy-readiness-result.json",
    root / "operator-console-static/demo-data/connector-simulation-preview.json",
    root / "operator-console-static/demo-data/connector-policy-readiness.json",
]

false_keys = {
    "trusted",
    "external_calls_made",
    "credentials_used",
    "tokens_used",
    "connector_runtime_enabled",
    "external_calls_allowed",
    "credentials_allowed",
    "activation_allowed",
    "connector_simulator_external_calls_enabled",
    "connector_simulator_credentials_enabled",
    "connector_simulator_tokens_enabled",
    "connector_simulator_runtime_activation_enabled",
}
true_keys = {
    "synthetic",
    "connector_simulator_enabled",
    "connector_dry_run_simulation_enabled",
    "sandbox_required",
    "audit_required",
    "provenance_required",
    "redaction_applied",
    "read_only",
}


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in true_keys and nested is not True:
                raise SystemExit(f"{context}.{key} must be true")
            if key == "simulation_type" and nested != "dry_run":
                raise SystemExit(f"{context}.simulation_type must be dry_run")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    walk(payload, path.relative_to(root).as_posix())

print("Connector simulator no-go JSON checks PASS")
PY

echo "Connector simulator no-go regression result:"
echo "- connector_runtime: disabled"
echo "- external_calls: absent"
echo "- credentials_tokens: absent"
echo "- route_registration_activation: disabled"
echo "- network_clients: absent"
echo "Connector simulator no-go regression PASS"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/disabled-connector-prototype.md
  docs/connectors/mock-connector-manifest.md
  docs/connectors/connector-runtime-gate.md
  docs/connectors/connector-egress-preview.md
  docs/connectors/connector-ingress-preview.md
  docs/connectors/connector-runtime-audit.md
  docs/connectors/connector-runtime-no-go.md
  docs/adr/0099-disabled-external-connector-prototype.md
)

required_examples=(
  examples/connectors/connector-runtime-status.json
  examples/connectors/mock-connector-manifest.json
  examples/connectors/mock-connector-egress-preview-request.json
  examples/connectors/mock-connector-egress-preview-result.json
  examples/connectors/mock-connector-ingress-preview-request.json
  examples/connectors/mock-connector-ingress-preview-result.json
  examples/connectors/connector-runtime-audit-request.json
  examples/connectors/connector-runtime-blockers.json
  operator-console-static/demo-data/connector-runtime-status.json
  operator-console-static/demo-data/connector-boundary-preview.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing connector runtime artifact: $file" >&2
    exit 1
  }
done

grep -q "0099-disabled-external-connector-prototype.md" docs/adr/README.md || {
  echo "ADR 0099 is not indexed" >&2
  exit 1
}

for key in \
  AION_CONNECTOR_RUNTIME_ENABLED=false \
  AION_CONNECTOR_EXTERNAL_CALLS_ENABLED=false \
  AION_CONNECTOR_CREDENTIALS_ENABLED=false \
  AION_CONNECTOR_TOKEN_STORAGE_ENABLED=false \
  AION_CONNECTOR_ACTIVATION_ENABLED=false \
  AION_CONNECTOR_ROUTE_REGISTRATION_ENABLED=false; do
  grep -q "$key" .env.example || {
    echo ".env.example missing disabled connector flag: $key" >&2
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
    echo "package manager file is not allowed for AION-108: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-108 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-108 must not add untracked migrations" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request' \
  services/brain-api/src/aion_brain/connector_runtime \
  services/brain-api/src/aion_brain/api/connector_runtime.py; then
  echo "connector runtime network call pattern found" >&2
  exit 1
fi

if rg -n 'connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "connector or provider SDK dependency found" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |raw_prompt|hidden_reasoning|chain_of_thought' \
  "${required_examples[@]}"; then
  echo "blocked marker found in connector runtime examples" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
examples = [
    root / "examples/connectors/connector-runtime-status.json",
    root / "examples/connectors/mock-connector-manifest.json",
    root / "examples/connectors/mock-connector-egress-preview-request.json",
    root / "examples/connectors/mock-connector-egress-preview-result.json",
    root / "examples/connectors/mock-connector-ingress-preview-request.json",
    root / "examples/connectors/mock-connector-ingress-preview-result.json",
    root / "examples/connectors/connector-runtime-audit-request.json",
    root / "examples/connectors/connector-runtime-blockers.json",
    root / "operator-console-static/demo-data/connector-runtime-status.json",
    root / "operator-console-static/demo-data/connector-boundary-preview.json",
]

false_keys = {
    "connector_runtime_enabled",
    "connector_external_calls_enabled",
    "connector_credentials_enabled",
    "connector_token_storage_enabled",
    "connector_activation_enabled",
    "connector_route_registration_enabled",
    "external_calls_required",
    "credentials_required",
    "egress_allowed",
    "external_call_allowed",
    "credentials_present",
    "trusted",
    "trusted_ingress",
    "network_calls_allowed",
    "runtime_activation_allowed",
    "route_registration_allowed",
    "activation_allowed",
}
true_keys = {
    "connector_mock_preview_enabled",
    "connector_egress_preview_enabled",
    "connector_ingress_preview_enabled",
    "dry_run_supported",
    "provenance_required",
    "redaction_applied",
    "prompt_injection_scan_required",
}


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in true_keys and nested is not True:
                raise SystemExit(f"{context}.{key} must be true")
            if key == "routes_declared" and nested != []:
                raise SystemExit(f"{context}.routes_declared must be empty")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in examples:
    walk(json.loads(path.read_text()), path.relative_to(root).as_posix())

print("Connector runtime JSON checks PASS")
PY

echo "Connector runtime check result:"
echo "- connector_runtime: disabled"
echo "- external_calls: absent"
echo "- credentials_tokens: absent"
echo "- activation_routes: disabled"
echo "- network_clients: absent"
echo "Connector runtime check PASS"

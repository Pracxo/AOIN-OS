#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

credential_source=(
  services/brain-api/src/aion_brain/contracts/connector_credentials.py
  services/brain-api/src/aion_brain/api/connector_credentials.py
  services/brain-api/src/aion_brain/connector_credentials
  packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials.py
)

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-113: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-113 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-113 must not add untracked migrations" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  "${credential_source[@]}"; then
  echo "connector credential network call pattern found" >&2
  exit 1
fi

if rg -n '\b(connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==)\b' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "connector or provider SDK dependency found" >&2
  exit 1
fi

if rg -n '\b(connector_credentials_storage_enabled|connector_tokens_storage_enabled|connector_secret_material_enabled|connector_external_identity_runtime_enabled|connector_runtime_credential_access_enabled)\s*[:=]\s*true\b' \
  services/brain-api/src .env.example operator-console-static examples/connectors; then
  echo "connector credential unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(credential_storage_enabled|token_storage_enabled|secret_material_present|plaintext_secret_allowed|browser_secret_storage_allowed|log_secret_allowed|external_identity_runtime_enabled|connector_runtime_credential_access_enabled|credential_storage_allowed|token_storage_allowed|credential_access_allowed|token_access_allowed|secret_material_allowed|storage_allowed|rotation_allowed|revocation_allowed)\s*[:=]\s*true\b' \
  services/brain-api/src/aion_brain/connector_credentials \
  services/brain-api/src/aion_brain/contracts/connector_credentials.py \
  services/brain-api/src/aion_brain/api/connector_credentials.py \
  examples/connectors/connector-credential-*.json \
  examples/connectors/connector-secret-*.json \
  operator-console-static/demo-data/connector-credential-*.json; then
  echo "connector credential true storage or material permission found" >&2
  exit 1
fi

if rg -n '^\s*@connector_credentials_app\.command\("(store|read|rotate|revoke|token|oauth|oidc|saml|login|bind)"\)' \
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials.py; then
  echo "connector credential CLI exposes forbidden command" >&2
  exit 1
fi

if rg -n '<input|<textarea|<select' operator-console-static/index.html operator-console-static/app.js; then
  echo "static console exposes credential input control" >&2
  exit 1
fi

if rg -n '<button[^>]*>([^<]*)(store|read|rotate|revoke|login|connect|call)([^<]*)</button>' \
  operator-console-static/index.html operator-console-static/app.js; then
  echo "static console exposes connector credential runtime button" >&2
  exit 1
fi

if rg -n 'add_api_route|dynamic[_-]?route|route_registration_enabled[[:space:]]*[:=][[:space:]]*true' \
  services/brain-api/src/aion_brain/connector_credentials services/brain-api/src/aion_brain/api/connector_credentials.py; then
  echo "connector credential route registration pattern found" >&2
  exit 1
fi

if rg -n 'open\(|write_text|sqlite|insert\s+into|update\s+.*set|delete\s+from|upsert|commit\(' \
  services/brain-api/src/aion_brain/connector_credentials services/brain-api/src/aion_brain/api/connector_credentials.py; then
  echo "connector credential persistence pattern found" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  docs/connectors/connector-credential-*.md \
  docs/connectors/connector-secret-handling-design.md \
  docs/connectors/connector-token-lifecycle.md \
  docs/adr/0104-connector-credential-store-architecture.md; then
  echo "package install instruction found in AION-113 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-credential-boundary.json",
    root / "examples/connectors/connector-credential-readiness-result.json",
    root / "examples/connectors/connector-credential-authorization-matrix.json",
    root / "examples/connectors/connector-credential-denial-result.json",
    root / "operator-console-static/demo-data/connector-credential-boundary.json",
    root / "operator-console-static/demo-data/connector-credential-readiness.json",
]

false_keys = {
    "credential_storage_enabled",
    "token_storage_enabled",
    "secret_material_present",
    "plaintext_secret_allowed",
    "browser_secret_storage_allowed",
    "log_secret_allowed",
    "external_identity_runtime_enabled",
    "connector_runtime_credential_access_enabled",
    "credential_ready",
    "credential_storage_allowed",
    "token_storage_allowed",
    "credential_access_allowed",
    "token_access_allowed",
    "external_identity_runtime_allowed",
    "secret_material_allowed",
    "storage_allowed",
    "rotation_allowed",
    "revocation_allowed",
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

print("Connector credential no-go JSON checks PASS")
PY

echo "Connector credential no-go regression result:"
echo "- credential_storage: absent"
echo "- token_storage: absent"
echo "- secret_material: absent"
echo "- oauth_oidc_saml_runtime: absent"
echo "- forbidden_cli_buttons_inputs: absent"
echo "- external_calls: absent"
echo "Connector credential no-go regression PASS"

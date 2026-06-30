#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

sandbox_source=(
  services/brain-api/src/aion_brain/contracts/connector_sandbox.py
  services/brain-api/src/aion_brain/api/connector_sandbox.py
  services/brain-api/src/aion_brain/connector_sandbox
  packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox.py
)

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-112: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-112 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-112 must not add untracked migrations" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  "${sandbox_source[@]}"; then
  echo "connector sandbox network call pattern found" >&2
  exit 1
fi

if rg -n 'subprocess\.|os\.system|pty\.|multiprocessing|Process\(|Popen\(|exec\(|eval\(' \
  services/brain-api/src/aion_brain/connector_sandbox services/brain-api/src/aion_brain/api/connector_sandbox.py; then
  echo "connector sandbox execution or process pattern found" >&2
  exit 1
fi

if rg -n 'importlib|__import__|pip[[:space:]]+install|poetry[[:space:]]+add|package_install_enabled[[:space:]]*[:=][[:space:]]*true' \
  services/brain-api/src/aion_brain/connector_sandbox services/brain-api/src/aion_brain/api/connector_sandbox.py packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox.py; then
  echo "connector sandbox dynamic import or package install pattern found" >&2
  exit 1
fi

if rg -n '\b(connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==)\b' \
  pyproject.toml setup.cfg setup.py requirements*.txt services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "connector or provider SDK dependency found" >&2
  exit 1
fi

if rg -n '\b(connector_sandbox_runtime_execution_enabled|connector_sandbox_filesystem_enabled|connector_sandbox_network_enabled|connector_sandbox_credentials_enabled|connector_sandbox_tokens_enabled|connector_sandbox_process_spawn_enabled|connector_sandbox_dynamic_import_enabled|connector_sandbox_package_install_enabled|connector_sandbox_activation_enabled)\s*[:=]\s*true\b' \
  services/brain-api/src .env.example operator-console-static examples/connectors; then
  echo "connector sandbox unsafe enablement found" >&2
  exit 1
fi

if rg -n '\b(runtime_execution_allowed|filesystem_access_allowed|network_access_allowed|credential_access_allowed|token_access_allowed|process_spawn_allowed|dynamic_import_allowed|package_install_allowed|connector_activation_allowed|runtime_allowed)\s*[:=]\s*true\b' \
  services/brain-api/src/aion_brain/connector_sandbox services/brain-api/src/aion_brain/contracts/connector_sandbox.py services/brain-api/src/aion_brain/api/connector_sandbox.py examples/connectors operator-console-static/demo-data; then
  echo "connector sandbox true runtime permission found" >&2
  exit 1
fi

if rg -n 'add_api_route|dynamic[_-]?route|route_registration_enabled[[:space:]]*[:=][[:space:]]*true' \
  services/brain-api/src/aion_brain/connector_sandbox services/brain-api/src/aion_brain/api/connector_sandbox.py; then
  echo "connector sandbox route registration pattern found" >&2
  exit 1
fi

if rg -n 'store_credential|credential_store|secret_store|token_store|store_token|external_endpoint|provider_endpoint' \
  services/brain-api/src/aion_brain/connector_sandbox services/brain-api/src/aion_brain/api/connector_sandbox.py; then
  echo "connector sandbox credential, token, or endpoint pattern found" >&2
  exit 1
fi

if rg -n '^\s*@connector_sandbox_app\.command\("(allow|enable|grant|connect|call|execute|run|install|activate)"\)' \
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox.py; then
  echo "connector sandbox CLI exposes forbidden command" >&2
  exit 1
fi

if rg -n '<button[^>]*>([^<]*)(allow|enable|grant|connect|call|execute|run|install|activate)([^<]*)</button>' \
  operator-console-static/index.html operator-console-static/app.js; then
  echo "static console exposes connector sandbox runtime button" >&2
  exit 1
fi

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  examples/connectors/connector-sandbox-*.json \
  operator-console-static/demo-data/connector-sandbox-*.json; then
  echo "blocked marker found in connector sandbox examples" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  docs/connectors/connector-sandbox-*.md docs/adr/0103-connector-sandbox-design.md; then
  echo "package install instruction found in AION-112 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-sandbox-boundary.json",
    root / "examples/connectors/connector-sandbox-capability-rules.json",
    root / "examples/connectors/connector-sandbox-readiness-result.json",
    root / "examples/connectors/connector-sandbox-denial-result.json",
    root / "examples/connectors/connector-sandbox-status.json",
    root / "examples/connectors/connector-sandbox-no-go-result.json",
    root / "operator-console-static/demo-data/connector-sandbox-status.json",
    root / "operator-console-static/demo-data/connector-sandbox-readiness.json",
]

false_keys = {
    "runtime_execution_allowed",
    "filesystem_access_allowed",
    "network_access_allowed",
    "credential_access_allowed",
    "token_access_allowed",
    "process_spawn_allowed",
    "dynamic_import_allowed",
    "package_install_allowed",
    "connector_activation_allowed",
    "runtime_allowed",
    "connector_runtime_enabled",
    "connector_sandbox_runtime_execution_enabled",
    "connector_sandbox_filesystem_enabled",
    "connector_sandbox_network_enabled",
    "connector_sandbox_credentials_enabled",
    "connector_sandbox_tokens_enabled",
    "connector_sandbox_process_spawn_enabled",
    "connector_sandbox_dynamic_import_enabled",
    "connector_sandbox_package_install_enabled",
    "connector_sandbox_activation_enabled",
    "present",
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

print("Connector sandbox no-go JSON checks PASS")
PY

echo "Connector sandbox no-go regression result:"
echo "- real_sandbox_runtime: absent"
echo "- filesystem_network: disabled"
echo "- credentials_tokens: absent"
echo "- process_import_install: absent"
echo "- activation_routes: disabled"
echo "- forbidden_cli_buttons: absent"
echo "Connector sandbox no-go regression PASS"

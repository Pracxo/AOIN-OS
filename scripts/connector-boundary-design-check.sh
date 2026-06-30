#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/external-connector-boundary-design.md
  docs/connectors/connector-trust-model.md
  docs/connectors/connector-credential-boundary.md
  docs/connectors/connector-egress-guard.md
  docs/connectors/connector-ingress-guard.md
  docs/connectors/connector-capability-declaration.md
  docs/connectors/connector-threat-model.md
  docs/connectors/connector-release-gates.md
  docs/connectors/connector-no-go-regression-pack.md
  docs/connectors/future-connector-implementation-prerequisites.md
  docs/adr/0097-external-connector-boundary-design.md
)

required_examples=(
  examples/connectors/connector-boundary-design.json
  examples/connectors/connector-trust-model.json
  examples/connectors/connector-threat-model.json
  examples/connectors/connector-release-gates.json
  examples/connectors/connector-no-go-regression-result.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || {
    echo "missing connector boundary doc: $file" >&2
    exit 1
  }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing connector boundary example: $file" >&2
    exit 1
  }
done

test -x scripts/connector-no-go-regression.sh || {
  echo "connector-no-go-regression.sh must be executable" >&2
  exit 1
}

grep -q "0097-external-connector-boundary-design.md" docs/adr/README.md || {
  echo "ADR 0097 is not indexed" >&2
  exit 1
}

grep -R -qi "no connector runtime" docs/connectors docs/adr/0097-external-connector-boundary-design.md || {
  echo "connector docs must state no connector runtime" >&2
  exit 1
}

grep -R -qi "external calls.*disabled\\|no external call\\|external calls remain disabled" docs/connectors docs/adr/0097-external-connector-boundary-design.md || {
  echo "connector docs must state no external calls" >&2
  exit 1
}

grep -R -qi "credentials.*absent\\|no credentials\\|credentials and tokens remain absent" docs/connectors docs/adr/0097-external-connector-boundary-design.md || {
  echo "connector docs must state no credentials or tokens" >&2
  exit 1
}

grep -R -qi "untrusted by default" docs/connectors docs/adr/0097-external-connector-boundary-design.md || {
  echo "connector docs must state connectors are untrusted by default" >&2
  exit 1
}

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-106: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-106 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-106 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not add API router files" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not add SDK resources or CLI command implementations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-106 must not add untracked SDK resources or CLI command implementations" >&2
  exit 1
fi

if rg -n 'connector[-_ ]?sdk|provider[-_ ]?sdk|requests[[:space:]]*==|httpx[[:space:]]*==|aiohttp[[:space:]]*==' pyproject.toml setup.cfg setup.py requirements*.txt 2>/dev/null; then
  echo "connector or network SDK dependency found" >&2
  exit 1
fi

if rg -n 'https?://' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "external URL or endpoint found in connector boundary artifacts" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in connector boundary artifacts" >&2
  exit 1
fi

./scripts/connector-no-go-regression.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
example_dir = root / "examples/connectors"

boundary = json.loads((example_dir / "connector-boundary-design.json").read_text())
for key in (
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_present",
    "token_storage_enabled",
    "dynamic_routes_enabled",
    "activation_enabled",
    "connector_sdk_dependency_present",
    "provider_sdk_dependency_present",
    "network_client_present",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
):
    if boundary.get(key) is not False:
        raise SystemExit(f"{key} must be false in connector boundary design")

release = json.loads((example_dir / "connector-release-gates.json").read_text())
required_gates = {
    "threat model approved",
    "credential boundary approved",
    "egress guard approved",
    "ingress guard approved",
    "policy model approved",
    "action authorization integration tested",
    "audit provenance tested",
    "operator review tested",
    "sandbox requirements approved",
    "disabled-by-default prototype green",
    "release freeze gate green",
}
gates = {row.get("gate") for row in release.get("gates", [])}
missing = required_gates - gates
if missing:
    raise SystemExit(f"connector release gates missing: {sorted(missing)}")
for row in release.get("gates", []):
    if row.get("release_blocker") is not True:
        raise SystemExit(f"connector release gate must be blocker: {row}")

print("Connector boundary design JSON checks PASS")
PY

echo "Connector boundary design result:"
echo "- connector_runtime: absent"
echo "- external_calls: disabled"
echo "- credentials_tokens: absent"
echo "- connector_sdk_dependencies: absent"
echo "- no_go_regression: passed"
echo "Connector boundary design check PASS"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/connector-policy-action-catalog.md
  docs/connectors/connector-authorization-matrix.md
  docs/connectors/connector-policy-dry-run-gate.md
  docs/connectors/connector-policy-denial-rules.md
  docs/connectors/connector-policy-traceability.md
  docs/connectors/connector-policy-no-go.md
  docs/adr/0102-connector-policy-action-catalog.md
)

required_examples=(
  examples/connectors/connector-policy-action-catalog.json
  examples/connectors/connector-authorization-matrix.json
  examples/connectors/connector-policy-dry-run-request.json
  examples/connectors/connector-policy-dry-run-result.json
  examples/connectors/connector-policy-denial-result.json
  examples/connectors/connector-policy-traceability.json
  operator-console-static/demo-data/connector-policy-catalog.json
  operator-console-static/demo-data/connector-policy-dry-run.json
)

required_source=(
  services/brain-api/src/aion_brain/contracts/connector_policy.py
  services/brain-api/src/aion_brain/api/connector_policy.py
  services/brain-api/src/aion_brain/connector_policy/__init__.py
  services/brain-api/src/aion_brain/connector_policy/catalog.py
  services/brain-api/src/aion_brain/connector_policy/matrix.py
  services/brain-api/src/aion_brain/connector_policy/dry_run.py
  services/brain-api/src/aion_brain/connector_policy/denials.py
  services/brain-api/src/aion_brain/connector_policy/traceability.py
  services/brain-api/src/aion_brain/connector_policy/audit.py
  services/brain-api/src/aion_brain/connector_policy/query.py
  packages/aion-sdk-python/src/aion_sdk/resources/connector_policy.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy.py
)

for file in "${required_docs[@]}" "${required_examples[@]}" "${required_source[@]}"; do
  test -f "$file" || {
    echo "missing connector policy artifact: $file" >&2
    exit 1
  }
done

grep -q "0102-connector-policy-action-catalog.md" docs/adr/README.md || {
  echo "ADR 0102 is not indexed" >&2
  exit 1
}

for key in \
  AION_CONNECTOR_POLICY_CATALOG_ENABLED=true \
  AION_CONNECTOR_POLICY_DRY_RUN_ENABLED=true \
  AION_CONNECTOR_POLICY_RUNTIME_ALLOW_ENABLED=false \
  AION_CONNECTOR_POLICY_EXTERNAL_CALLS_ENABLED=false \
  AION_CONNECTOR_POLICY_CREDENTIALS_ENABLED=false \
  AION_CONNECTOR_POLICY_TOKENS_ENABLED=false \
  AION_CONNECTOR_POLICY_ACTIVATION_ENABLED=false; do
  grep -q "$key" .env.example || {
    echo ".env.example missing connector policy flag: $key" >&2
    exit 1
  }
done

./scripts/connector-policy-no-go-regression.sh

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
    root / "examples/connectors/connector-policy-traceability.json",
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
    "requires_external_call",
}


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key == "synthetic" and nested is not True:
                raise SystemExit(f"{context}.synthetic must be true")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    walk(payload, path.relative_to(root).as_posix())

catalog = json.loads(
    (root / "examples/connectors/connector-policy-action-catalog.json").read_text()
)
catalog_keys = {item.get("action_key") for item in catalog.get("actions", [])}
required_catalog = {
    "connector_policy.catalog.read",
    "connector_policy.matrix.read",
    "connector_policy.dry_run",
    "connector_policy.traceability.read",
}
missing = required_catalog - catalog_keys
if missing:
    raise SystemExit(f"missing connector policy actions: {sorted(missing)}")

denial = json.loads((root / "examples/connectors/connector-policy-denial-result.json").read_text())
if denial.get("decision") != "deny":
    raise SystemExit("denial result must have decision=deny")

print("Connector policy JSON checks PASS")
PY

echo "Connector policy check result:"
echo "- catalog: read-only"
echo "- matrix: runtime permissions false"
echo "- dry_run: policy decision only"
echo "- denials: future runtime actions fail closed"
echo "- external_calls: absent"
echo "- credentials_tokens: absent"
echo "Connector policy check PASS"

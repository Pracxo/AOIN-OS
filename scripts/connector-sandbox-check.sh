#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/connector-sandbox-boundary.md
  docs/connectors/connector-sandbox-isolation-model.md
  docs/connectors/connector-sandbox-capability-rules.md
  docs/connectors/connector-sandbox-readiness-gate.md
  docs/connectors/connector-sandbox-audit-provenance.md
  docs/connectors/connector-sandbox-no-go.md
  docs/adr/0103-connector-sandbox-design.md
)

required_examples=(
  examples/connectors/connector-sandbox-boundary.json
  examples/connectors/connector-sandbox-capability-rules.json
  examples/connectors/connector-sandbox-readiness-request.json
  examples/connectors/connector-sandbox-readiness-result.json
  examples/connectors/connector-sandbox-denial-result.json
  examples/connectors/connector-sandbox-status.json
  examples/connectors/connector-sandbox-no-go-result.json
  examples/connectors/connector-sandbox-audit-provenance.json
  operator-console-static/demo-data/connector-sandbox-status.json
  operator-console-static/demo-data/connector-sandbox-readiness.json
)

required_source=(
  services/brain-api/src/aion_brain/contracts/connector_sandbox.py
  services/brain-api/src/aion_brain/api/connector_sandbox.py
  services/brain-api/src/aion_brain/connector_sandbox/__init__.py
  services/brain-api/src/aion_brain/connector_sandbox/design.py
  services/brain-api/src/aion_brain/connector_sandbox/isolation.py
  services/brain-api/src/aion_brain/connector_sandbox/capabilities.py
  services/brain-api/src/aion_brain/connector_sandbox/readiness.py
  services/brain-api/src/aion_brain/connector_sandbox/denials.py
  services/brain-api/src/aion_brain/connector_sandbox/audit.py
  services/brain-api/src/aion_brain/connector_sandbox/query.py
  packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox.py
)

for file in "${required_docs[@]}" "${required_examples[@]}" "${required_source[@]}"; do
  test -f "$file" || {
    echo "missing connector sandbox artifact: $file" >&2
    exit 1
  }
done

grep -q "0103-connector-sandbox-design.md" docs/adr/README.md || {
  echo "ADR 0103 is not indexed" >&2
  exit 1
}

for key in \
  AION_CONNECTOR_SANDBOX_DESIGN_ENABLED=true \
  AION_CONNECTOR_SANDBOX_READINESS_ENABLED=true \
  AION_CONNECTOR_SANDBOX_RUNTIME_EXECUTION_ENABLED=false \
  AION_CONNECTOR_SANDBOX_FILESYSTEM_ENABLED=false \
  AION_CONNECTOR_SANDBOX_NETWORK_ENABLED=false \
  AION_CONNECTOR_SANDBOX_CREDENTIALS_ENABLED=false \
  AION_CONNECTOR_SANDBOX_TOKENS_ENABLED=false \
  AION_CONNECTOR_SANDBOX_PROCESS_SPAWN_ENABLED=false \
  AION_CONNECTOR_SANDBOX_DYNAMIC_IMPORT_ENABLED=false \
  AION_CONNECTOR_SANDBOX_PACKAGE_INSTALL_ENABLED=false \
  AION_CONNECTOR_SANDBOX_ACTIVATION_ENABLED=false; do
  grep -q "$key" .env.example || {
    echo ".env.example missing connector sandbox flag: $key" >&2
    exit 1
  }
done

./scripts/connector-sandbox-no-go-regression.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-sandbox-boundary.json",
    root / "examples/connectors/connector-sandbox-capability-rules.json",
    root / "examples/connectors/connector-sandbox-readiness-request.json",
    root / "examples/connectors/connector-sandbox-readiness-result.json",
    root / "examples/connectors/connector-sandbox-denial-result.json",
    root / "examples/connectors/connector-sandbox-status.json",
    root / "examples/connectors/connector-sandbox-no-go-result.json",
    root / "examples/connectors/connector-sandbox-audit-provenance.json",
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
            if key in {"audit_required", "provenance_required"} and nested is not True:
                raise SystemExit(f"{context}.{key} must be true")
            if key == "synthetic" and nested is not True:
                raise SystemExit(f"{context}.synthetic must be true")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in paths:
    walk(json.loads(path.read_text()), path.relative_to(root).as_posix())

rules = json.loads((root / "examples/connectors/connector-sandbox-capability-rules.json").read_text())
rule_keys = {item.get("rule_key") for item in rules.get("rules", [])}
if "connector.sandbox.readiness.preview" not in rule_keys:
    raise SystemExit("missing sandbox readiness preview rule")

denial = json.loads((root / "examples/connectors/connector-sandbox-denial-result.json").read_text())
if denial.get("decision") != "deny":
    raise SystemExit("connector sandbox denial result must have decision=deny")

print("Connector sandbox JSON checks PASS")
PY

echo "Connector sandbox check result:"
echo "- boundary: design-only"
echo "- readiness: preview-only"
echo "- runtime_execution: disabled"
echo "- filesystem_network: disabled"
echo "- credentials_tokens: disabled"
echo "- process_import_install_activation: disabled"
echo "Connector sandbox check PASS"

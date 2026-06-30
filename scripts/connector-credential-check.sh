#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/connector-credential-store-architecture.md
  docs/connectors/connector-secret-handling-design.md
  docs/connectors/connector-credential-lifecycle.md
  docs/connectors/connector-token-lifecycle.md
  docs/connectors/connector-credential-authorization-matrix.md
  docs/connectors/connector-credential-redaction-logging.md
  docs/connectors/connector-credential-rotation-revocation.md
  docs/connectors/connector-credential-audit-provenance.md
  docs/connectors/connector-credential-readiness-gate.md
  docs/connectors/connector-credential-no-go.md
  docs/adr/0104-connector-credential-store-architecture.md
)

required_examples=(
  examples/connectors/connector-credential-boundary.json
  examples/connectors/connector-credential-readiness-request.json
  examples/connectors/connector-credential-readiness-result.json
  examples/connectors/connector-credential-authorization-matrix.json
  examples/connectors/connector-credential-denial-result.json
  examples/connectors/connector-secret-redaction-result.json
  operator-console-static/demo-data/connector-credential-boundary.json
  operator-console-static/demo-data/connector-credential-readiness.json
)

required_source=(
  services/brain-api/src/aion_brain/contracts/connector_credentials.py
  services/brain-api/src/aion_brain/api/connector_credentials.py
  services/brain-api/src/aion_brain/connector_credentials/__init__.py
  services/brain-api/src/aion_brain/connector_credentials/architecture.py
  services/brain-api/src/aion_brain/connector_credentials/lifecycle.py
  services/brain-api/src/aion_brain/connector_credentials/redaction.py
  services/brain-api/src/aion_brain/connector_credentials/authorization.py
  services/brain-api/src/aion_brain/connector_credentials/readiness.py
  services/brain-api/src/aion_brain/connector_credentials/denials.py
  services/brain-api/src/aion_brain/connector_credentials/audit.py
  services/brain-api/src/aion_brain/connector_credentials/query.py
  packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials.py
)

for file in "${required_docs[@]}" "${required_examples[@]}" "${required_source[@]}"; do
  test -f "$file" || {
    echo "missing connector credential artifact: $file" >&2
    exit 1
  }
done

grep -q "0104-connector-credential-store-architecture.md" docs/adr/README.md || {
  echo "ADR 0104 is not indexed" >&2
  exit 1
}

for key in \
  AION_CONNECTOR_CREDENTIALS_ARCHITECTURE_ENABLED=true \
  AION_CONNECTOR_CREDENTIALS_READINESS_ENABLED=true \
  AION_CONNECTOR_CREDENTIALS_REDACTION_PREVIEW_ENABLED=true \
  AION_CONNECTOR_CREDENTIALS_STORAGE_ENABLED=false \
  AION_CONNECTOR_TOKENS_STORAGE_ENABLED=false \
  AION_CONNECTOR_SECRET_MATERIAL_ENABLED=false \
  AION_CONNECTOR_EXTERNAL_IDENTITY_RUNTIME_ENABLED=false \
  AION_CONNECTOR_RUNTIME_CREDENTIAL_ACCESS_ENABLED=false; do
  grep -q "$key" .env.example || {
    echo ".env.example missing connector credential flag: $key" >&2
    exit 1
  }
done

./scripts/connector-credential-no-go-regression.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-credential-boundary.json",
    root / "examples/connectors/connector-credential-readiness-request.json",
    root / "examples/connectors/connector-credential-readiness-result.json",
    root / "examples/connectors/connector-credential-authorization-matrix.json",
    root / "examples/connectors/connector-credential-denial-result.json",
    root / "examples/connectors/connector-secret-redaction-result.json",
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
true_keys = {"rotation_required", "revocation_required", "audit_required", "provenance_required"}


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in true_keys and nested is not True:
                raise SystemExit(f"{context}.{key} must be true")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in paths:
    walk(json.loads(path.read_text()), path.relative_to(root).as_posix())

denial = json.loads((root / "examples/connectors/connector-credential-denial-result.json").read_text())
if denial.get("decision") != "deny":
    raise SystemExit("connector credential denial result must have decision=deny")

redaction = json.loads((root / "examples/connectors/connector-secret-redaction-result.json").read_text())
if redaction.get("redaction_applied") is not True:
    raise SystemExit("connector secret redaction result must apply redaction")
if "[REDACTED]" not in json.dumps(redaction):
    raise SystemExit("connector secret redaction result must contain redacted placeholders")

print("Connector credential JSON checks PASS")
PY

echo "Connector credential check result:"
echo "- credential_storage: disabled"
echo "- token_storage: disabled"
echo "- secret_material: absent"
echo "- external_identity_runtime: disabled"
echo "- runtime_credential_access: disabled"
echo "- redaction_preview: enabled"
echo "Connector credential check PASS"

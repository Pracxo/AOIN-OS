#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/connectors/connector-dry-run-simulator.md
  docs/connectors/synthetic-connector-replay.md
  docs/connectors/connector-policy-readiness-gate.md
  docs/connectors/connector-simulation-safety.md
  docs/connectors/connector-simulator-no-go.md
  docs/adr/0101-connector-dry-run-simulator-hardening.md
)

required_examples=(
  examples/connectors/connector-simulation-request.json
  examples/connectors/connector-simulation-result.json
  examples/connectors/connector-replay-fixture.json
  examples/connectors/connector-policy-readiness-request.json
  examples/connectors/connector-policy-readiness-result.json
  examples/connectors/connector-simulator-findings.json
  operator-console-static/demo-data/connector-simulation-preview.json
  operator-console-static/demo-data/connector-policy-readiness.json
)

required_source=(
  services/brain-api/src/aion_brain/contracts/connector_simulator.py
  services/brain-api/src/aion_brain/api/connector_simulator.py
  services/brain-api/src/aion_brain/connector_simulator/__init__.py
  services/brain-api/src/aion_brain/connector_simulator/redaction.py
  services/brain-api/src/aion_brain/connector_simulator/hash.py
  services/brain-api/src/aion_brain/connector_simulator/request_shapes.py
  services/brain-api/src/aion_brain/connector_simulator/response_shapes.py
  services/brain-api/src/aion_brain/connector_simulator/simulator.py
  services/brain-api/src/aion_brain/connector_simulator/replay.py
  services/brain-api/src/aion_brain/connector_simulator/policy_readiness.py
  services/brain-api/src/aion_brain/connector_simulator/findings.py
  services/brain-api/src/aion_brain/connector_simulator/audit.py
  services/brain-api/src/aion_brain/connector_simulator/query.py
  packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator.py
  packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator.py
)

for file in "${required_docs[@]}" "${required_examples[@]}" "${required_source[@]}"; do
  test -f "$file" || {
    echo "missing connector simulator artifact: $file" >&2
    exit 1
  }
done

grep -q "0101-connector-dry-run-simulator-hardening.md" docs/adr/README.md || {
  echo "ADR 0101 is not indexed" >&2
  exit 1
}

for key in \
  AION_CONNECTOR_SIMULATOR_ENABLED=true \
  AION_CONNECTOR_DRY_RUN_SIMULATION_ENABLED=true \
  AION_CONNECTOR_REPLAY_FIXTURES_ENABLED=true \
  AION_CONNECTOR_POLICY_READINESS_ENABLED=true \
  AION_CONNECTOR_SIMULATOR_EXTERNAL_CALLS_ENABLED=false \
  AION_CONNECTOR_SIMULATOR_CREDENTIALS_ENABLED=false \
  AION_CONNECTOR_SIMULATOR_TOKENS_ENABLED=false \
  AION_CONNECTOR_SIMULATOR_RUNTIME_ACTIVATION_ENABLED=false; do
  grep -q "$key" .env.example || {
    echo ".env.example missing connector simulator flag: $key" >&2
    exit 1
  }
done

./scripts/connector-simulator-no-go-regression.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])

result = json.loads((root / "examples/connectors/connector-simulation-result.json").read_text())
for key in (
    "synthetic",
):
    if result.get(key) is not True:
        raise SystemExit(f"simulation result {key} must be true")
for key in (
    "trusted",
    "external_calls_made",
    "credentials_used",
    "tokens_used",
    "connector_runtime_enabled",
):
    if result.get(key) is not False:
        raise SystemExit(f"simulation result {key} must be false")

readiness = json.loads(
    (root / "examples/connectors/connector-policy-readiness-result.json").read_text()
)
for key in ("external_calls_allowed", "credentials_allowed", "activation_allowed"):
    if readiness.get(key) is not False:
        raise SystemExit(f"readiness {key} must be false")

fixture = json.loads((root / "examples/connectors/connector-replay-fixture.json").read_text())
if fixture.get("synthetic") is not True or fixture.get("trusted") is not False:
    raise SystemExit("replay fixture must be synthetic and untrusted")

print("Connector simulator JSON checks PASS")
PY

echo "Connector simulator check result:"
echo "- simulator: synthetic-only"
echo "- replay: local fixture only"
echo "- policy_readiness: not runtime approval"
echo "- external_calls: absent"
echo "- credentials_tokens: absent"
echo "Connector simulator check PASS"

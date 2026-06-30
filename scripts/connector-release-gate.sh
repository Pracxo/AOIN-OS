#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/connector-release-gate.md
  docs/connectors/connector-safety-freeze.md
  docs/connectors/end-to-end-connector-readiness-evidence.md
  docs/connectors/connector-release-evidence-matrix.md
  docs/connectors/connector-implementation-readiness-decision.md
  docs/connectors/connector-release-no-go.md
  docs/adr/0105-connector-release-gate.md
)

required_examples=(
  examples/connectors/connector-release-gate-result.json
  examples/connectors/connector-safety-freeze-result.json
  examples/connectors/end-to-end-connector-readiness-evidence.json
  examples/connectors/connector-release-evidence-matrix.json
  examples/connectors/connector-implementation-readiness-decision.json
  operator-console-static/demo-data/connector-release-gate.json
  operator-console-static/demo-data/connector-safety-freeze.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing connector release gate artifact: $file" >&2
    exit 1
  }
done

grep -q "0105-connector-release-gate.md" docs/adr/README.md || {
  echo "ADR 0105 is not indexed" >&2
  exit 1
}

./scripts/connector-runtime-review.sh
./scripts/connector-runtime-no-external-call-regression.sh
./scripts/connector-simulator-check.sh
./scripts/connector-simulator-no-go-regression.sh
./scripts/connector-policy-check.sh
./scripts/connector-policy-no-go-regression.sh
./scripts/connector-sandbox-check.sh
./scripts/connector-sandbox-no-go-regression.sh
./scripts/connector-credential-check.sh
./scripts/connector-credential-no-go-regression.sh
./scripts/connector-release-no-go-regression.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
paths = [
    root / "examples/connectors/connector-release-gate-result.json",
    root / "examples/connectors/connector-safety-freeze-result.json",
    root / "examples/connectors/end-to-end-connector-readiness-evidence.json",
    root / "examples/connectors/connector-release-evidence-matrix.json",
    root / "examples/connectors/connector-implementation-readiness-decision.json",
]
required_false = (
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_present",
    "token_storage_enabled",
    "sandbox_execution_enabled",
    "connector_activation_enabled",
    "route_registration_enabled",
    "package_files_added",
    "migrations_added",
    "implementation_approved",
)

for path in paths:
    payload = json.loads(path.read_text())
    if payload.get("synthetic") is not True:
        raise SystemExit(f"release example must be synthetic: {path}")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{path.relative_to(root)} must keep {key}=false")

print("Connector release gate JSON checks PASS")
PY

cat <<'SUMMARY'
Connector release gate result:
- connector_runtime: disabled
- external_calls: absent
- credentials_tokens: absent
- sandbox_execution: absent
- implementation_approved: false
- package_files: absent
- migrations: absent
Connector release gate PASS
SUMMARY

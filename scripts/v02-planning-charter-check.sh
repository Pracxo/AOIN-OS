#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/release/v02-planning-charter.md
  docs/release/v02-runtime-implementation-decision-framework.md
  docs/release/v02-candidate-workstream-map.md
  docs/release/v02-adr-requirements.md
  docs/release/v02-gate-dependency-matrix.md
  docs/release/v02-no-go-planning-boundary.md
  docs/release/v02-backlog-intake-criteria.md
  docs/release/v02-planning-closeout-checklist.md
  docs/adr/0110-v02-planning-charter.md
)

required_examples=(
  examples/release/v02-planning-charter.json
  examples/release/v02-runtime-decision-framework.json
  examples/release/v02-candidate-workstream-map.json
  examples/release/v02-gate-dependency-matrix.json
  examples/release/v02-backlog-intake-result.json
  operator-console-static/demo-data/v02-planning-charter.json
  operator-console-static/demo-data/v02-gate-dependency-matrix.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing v0.2 planning artifact: $file" >&2
    exit 1
  }
done

grep -q "0110-v02-planning-charter.md" docs/adr/README.md || {
  echo "ADR 0110 is not indexed" >&2
  exit 1
}

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0)$'; then
  echo "v0.2 tag must not exist for AION-119" >&2
  exit 1
fi

./scripts/v02-planning-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/post-v01-release-candidate-gate.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_POST_V01_RELEASE_CANDIDATE_FREEZE_SKIP_FULL_CHECK=1 ./scripts/post-v01-release-candidate-freeze.sh
./scripts/post-v01-release-candidate-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/platform-integration-checkpoint.sh
AION_AGGREGATE_GATE_RUNNING=1 AION_PLATFORM_INTEGRATION_FREEZE_SKIP_FULL_CHECK=1 ./scripts/platform-integration-freeze-check.sh
./scripts/platform-integration-no-go-regression.sh
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
    root / "examples/release/v02-planning-charter.json",
    root / "examples/release/v02-runtime-decision-framework.json",
    root / "examples/release/v02-candidate-workstream-map.json",
    root / "examples/release/v02-gate-dependency-matrix.json",
    root / "examples/release/v02-backlog-intake-result.json",
    root / "operator-console-static/demo-data/v02-planning-charter.json",
    root / "operator-console-static/demo-data/v02-gate-dependency-matrix.json",
]
false_keys = {
    "runtime_implementation_approved",
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
    "package_files_added",
    "migrations_added",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "secrets_present",
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
}
required_true = {
    "v02_planning_charter_created",
}


def walk(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys and nested is not False:
                raise SystemExit(f"{context}.{key} must be false")
            if key in required_true and nested is not True:
                raise SystemExit(f"{context}.{key} must be true")
            walk(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f"{context}[{index}]")


for path in paths:
    payload = json.loads(path.read_text())
    relative = path.relative_to(root).as_posix()
    if relative.startswith("examples/") and payload.get("synthetic") is not True:
        raise SystemExit(f"planning example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"planning artifact must be passed: {path}")
    walk(payload, relative)

print("v0.2 planning JSON checks PASS")
PY

cat <<'SUMMARY'
v0.2 planning charter check result:
- v02_planning_charter_created: true
- v02_tag_created: false
- v02_release_created: false
- runtime_implementation_approved: false
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
v0.2 planning charter check PASS
SUMMARY

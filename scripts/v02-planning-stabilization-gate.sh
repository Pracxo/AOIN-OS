#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/release/v02-planning-stabilization-gate.md
  docs/release/v02-backlog-governance-freeze.md
  docs/release/v02-implementation-readiness-scorecard.md
  docs/release/v02-planning-evidence-pack.md
  docs/release/v02-decision-review-calendar.md
  docs/release/v02-blocked-work-register.md
  docs/release/v02-planning-stabilization-no-go.md
  docs/adr/0111-v02-planning-stabilization-gate.md
)

required_examples=(
  examples/release/v02-planning-stabilization-gate.json
  examples/release/v02-backlog-governance-freeze.json
  examples/release/v02-implementation-readiness-scorecard.json
  examples/release/v02-planning-evidence-pack.json
  examples/release/v02-blocked-work-register.json
  operator-console-static/demo-data/v02-planning-stabilization.json
  operator-console-static/demo-data/v02-implementation-readiness-scorecard.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing v0.2 planning stabilization artifact: $file" >&2
    exit 1
  }
done

grep -q "0111-v02-planning-stabilization-gate.md" docs/adr/README.md || {
  echo "ADR 0111 is not indexed" >&2
  exit 1
}

test -f operator-console-static/demo-data/v02-planning-stabilization.json || {
  echo "missing static console planning stabilization data" >&2
  exit 1
}
test -f operator-console-static/demo-data/v02-implementation-readiness-scorecard.json || {
  echo "missing static console implementation readiness data" >&2
  exit 1
}

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0)$'; then
  echo "v0.2 tag must not exist for AION-120" >&2
  exit 1
fi

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_V02_PLANNING_STABILIZATION_SKIP_NESTED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/v02-planning-stabilization-no-go-regression.sh
AION_V02_PLANNING_CHARTER_SKIP_NESTED_GATES=1 ./scripts/v02-planning-charter-check.sh
./scripts/v02-planning-no-go-regression.sh
if is_nested_gate_context; then
  echo "PASS: v0.2 planning stabilization downstream release gates deferred to outer aggregate gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_POST_V01_RELEASE_CANDIDATE_SKIP_DOWNSTREAM_GATES=1 ./scripts/post-v01-release-candidate-gate.sh
  AION_AGGREGATE_GATE_RUNNING=1 AION_POST_V01_RELEASE_CANDIDATE_FREEZE_SKIP_FULL_CHECK=1 ./scripts/post-v01-release-candidate-freeze.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/platform-integration-checkpoint.sh
  AION_AGGREGATE_GATE_RUNNING=1 AION_PLATFORM_INTEGRATION_FREEZE_SKIP_FULL_CHECK=1 ./scripts/platform-integration-freeze-check.sh
fi
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
    root / "examples/release/v02-planning-stabilization-gate.json",
    root / "examples/release/v02-backlog-governance-freeze.json",
    root / "examples/release/v02-implementation-readiness-scorecard.json",
    root / "examples/release/v02-planning-evidence-pack.json",
    root / "examples/release/v02-blocked-work-register.json",
    root / "operator-console-static/demo-data/v02-planning-stabilization.json",
    root / "operator-console-static/demo-data/v02-implementation-readiness-scorecard.json",
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
    "backlog_implementation_items_approved",
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
    payload = json.loads(path.read_text())
    relative = path.relative_to(root).as_posix()
    if relative.startswith("examples/") and payload.get("synthetic") is not True:
        raise SystemExit(f"planning example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"planning artifact must be passed: {path}")
    if payload.get("v02_planning_stabilized") is not True:
        raise SystemExit(f"planning stabilization flag must be true: {path}")
    walk(payload, relative)

print("v0.2 planning stabilization JSON checks PASS")
PY

cat <<'SUMMARY'
v0.2 planning stabilization gate result:
- v02_planning_stabilized: true
- v02_tag_created: false
- v02_release_created: false
- runtime_implementation_approved: false
- backlog_implementation_items_approved: false
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
v0.2 planning stabilization gate PASS
SUMMARY

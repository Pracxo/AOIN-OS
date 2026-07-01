#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/release/v02-implementation-kickoff-boundary.md
  docs/release/v02-approval-workflow-blueprint.md
  docs/release/v02-runtime-workstream-lock.md
  docs/release/v02-implementation-request-template.md
  docs/release/v02-approval-decision-record.md
  docs/release/v02-workstream-sequencing-plan.md
  docs/release/v02-implementation-kickoff-no-go.md
  docs/adr/0113-v02-implementation-kickoff-boundary.md
)

required_examples=(
  examples/release/v02-implementation-kickoff-boundary.json
  examples/release/v02-approval-workflow-blueprint.json
  examples/release/v02-runtime-workstream-lock.json
  examples/release/v02-implementation-request-template.json
  examples/release/v02-approval-decision-record.json
  operator-console-static/demo-data/v02-implementation-kickoff-boundary.json
  operator-console-static/demo-data/v02-runtime-workstream-lock.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing v0.2 implementation kickoff artifact: $file" >&2
    exit 1
  }
done

grep -q "0113-v02-implementation-kickoff-boundary.md" docs/adr/README.md || {
  echo "ADR 0113 is not indexed" >&2
  exit 1
}

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0)$'; then
  echo "v0.2 tag must not exist for AION-122" >&2
  exit 1
fi

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_V02_IMPLEMENTATION_KICKOFF_SKIP_NESTED_GATES:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/v02-implementation-kickoff-no-go-regression.sh
AION_V02_READINESS_FINAL_REVIEW_SKIP_NESTED_GATES=1 ./scripts/v02-readiness-final-review.sh
AION_V02_READINESS_FINAL_FREEZE_SKIP_FULL_CHECK=1 ./scripts/v02-readiness-final-freeze.sh
./scripts/v02-readiness-final-no-go-regression.sh
AION_V02_PLANNING_STABILIZATION_SKIP_NESTED_GATES=1 ./scripts/v02-planning-stabilization-gate.sh
AION_V02_PLANNING_CHARTER_SKIP_NESTED_GATES=1 ./scripts/v02-planning-charter-check.sh

if is_nested_gate_context; then
  echo "PASS: v0.2 implementation kickoff downstream release gates deferred to outer aggregate gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 AION_POST_V01_RELEASE_CANDIDATE_SKIP_DOWNSTREAM_GATES=1 ./scripts/post-v01-release-candidate-gate.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/platform-integration-checkpoint.sh
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
    root / "examples/release/v02-implementation-kickoff-boundary.json",
    root / "examples/release/v02-approval-workflow-blueprint.json",
    root / "examples/release/v02-runtime-workstream-lock.json",
    root / "examples/release/v02-implementation-request-template.json",
    root / "examples/release/v02-approval-decision-record.json",
    root / "operator-console-static/demo-data/v02-implementation-kickoff-boundary.json",
    root / "operator-console-static/demo-data/v02-runtime-workstream-lock.json",
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
    "approval_workflow_bypassed",
    "adr_dependency_bypassed",
    "gate_dependency_bypassed",
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
        raise SystemExit(f"implementation kickoff example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"implementation kickoff artifact must be passed: {path}")
    if payload.get("task_id") != "AION-122":
        raise SystemExit(f"implementation kickoff task id must be AION-122: {path}")
    if payload.get("v02_implementation_kickoff_boundary_created") is not True:
        raise SystemExit(f"implementation kickoff boundary flag must be true: {path}")
    walk(payload, relative)

print("v0.2 implementation kickoff JSON checks PASS")
PY

cat <<'SUMMARY'
v0.2 implementation kickoff boundary result:
- v02_implementation_kickoff_boundary_created: true
- v02_tag_created: false
- v02_release_created: false
- runtime_implementation_approved: false
- backlog_implementation_items_approved: false
- approval_workflow_bypassed: false
- adr_dependency_bypassed: false
- gate_dependency_bypassed: false
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
v0.2 implementation kickoff boundary check PASS
SUMMARY

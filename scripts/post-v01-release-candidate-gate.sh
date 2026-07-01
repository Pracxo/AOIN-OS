#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/release/post-v01-release-candidate-gate.md
  docs/release/cross-phase-freeze-evidence.md
  docs/release/post-v01-release-candidate-checklist.md
  docs/release/v02-planning-boundary.md
  docs/release/implementation-approval-lock.md
  docs/release/post-v01-release-candidate-no-go.md
  docs/adr/0109-post-v01-release-candidate-gate.md
)

required_examples=(
  examples/release/post-v01-release-candidate-gate.json
  examples/release/cross-phase-freeze-evidence.json
  examples/release/post-v01-release-candidate-checklist.json
  examples/release/v02-planning-boundary.json
  examples/release/implementation-approval-lock.json
  operator-console-static/demo-data/post-v01-release-candidate.json
  operator-console-static/demo-data/v02-planning-boundary.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing release candidate artifact: $file" >&2
    exit 1
  }
done

grep -q "0109-post-v01-release-candidate-gate.md" docs/adr/README.md || {
  echo "ADR 0109 is not indexed" >&2
  exit 1
}

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0)$'; then
  echo "v0.2 tag must not exist for AION-118" >&2
  exit 1
fi

skip_downstream_gates() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_POST_V01_RELEASE_CANDIDATE_SKIP_DOWNSTREAM_GATES:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/post-v01-release-candidate-no-go-regression.sh
if skip_downstream_gates; then
  echo "PASS: post-v0.1 downstream platform and runtime gates deferred to outer aggregate gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/platform-integration-checkpoint.sh
  AION_AGGREGATE_GATE_RUNNING=1 AION_PLATFORM_INTEGRATION_FREEZE_SKIP_FULL_CHECK=1 ./scripts/platform-integration-freeze-check.sh
  ./scripts/platform-integration-no-go-regression.sh
  AION_OPERATOR_PLATFORM_SKIP_FULL_CHECK=1 ./scripts/operator-platform-regression.sh
  AION_OPERATOR_PLATFORM_SKIP_FULL_CHECK=1 AION_OPERATOR_PLATFORM_FREEZE_SKIP_REGRESSION=1 ./scripts/operator-platform-freeze-gate.sh
  export AION_CONNECTOR_RUNTIME_REVIEW_SKIP_OPERATOR_FREEZE=1
  AION_AGGREGATE_GATE_RUNNING=1 AION_CONNECTOR_PLATFORM_REGRESSION_SKIP_NESTED_GATES=1 ./scripts/connector-platform-regression.sh
  AION_AGGREGATE_GATE_RUNNING=1 AION_CONNECTOR_PLATFORM_REGRESSION_SKIP_NESTED_GATES=1 ./scripts/connector-platform-stabilization-gate.sh
  ./scripts/auth-prototype-review.sh
  AION_OPERATOR_PLATFORM_SKIP_FULL_CHECK=1 ./scripts/module-activation-design-review.sh
  ./scripts/ui-release-gate.sh
  ./scripts/static-console-safety-check.sh
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
    root / "examples/release/post-v01-release-candidate-gate.json",
    root / "examples/release/cross-phase-freeze-evidence.json",
    root / "examples/release/post-v01-release-candidate-checklist.json",
    root / "examples/release/v02-planning-boundary.json",
    root / "examples/release/implementation-approval-lock.json",
    root / "operator-console-static/demo-data/post-v01-release-candidate.json",
    root / "operator-console-static/demo-data/v02-planning-boundary.json",
]
false_keys = {
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "production_auth_approved",
    "module_activation_approved",
    "external_calls_approved",
    "credential_storage_approved",
    "token_storage_approved",
    "sandbox_execution_approved",
    "v02_tag_created",
    "v02_release_approved",
    "package_files_added",
    "migrations_added",
    "api_runtime_execution_route_added",
    "sdk_resource_implementation_added",
    "cli_command_implementation_added",
    "frontend_dependencies_added",
    "aion_v0_1_0_touched",
    "secrets_present",
    "credential_values_present",
    "token_values_present",
    "endpoints_present",
    "prompt_payloads_present",
    "private_reasoning_present",
    "implementation_allowed",
}
required_true = {
    "post_v01_release_candidate_passed",
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
    if path.relative_to(root).as_posix().startswith("examples/"):
        if payload.get("synthetic") is not True:
            raise SystemExit(f"release example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"release artifact must be passed: {path}")
    walk(payload, path.relative_to(root).as_posix())

print("Post-v0.1 release candidate JSON checks PASS")
PY

cat <<'SUMMARY'
Post-v0.1 release candidate gate result:
- post_v01_release_candidate_passed: true
- v02_tag_created: false
- v02_release_approved: false
- operator_write_execution_approved: false
- connector_implementation_approved: false
- production_auth_approved: false
- module_activation_approved: false
- external_calls_approved: false
- credential_storage_approved: false
- token_storage_approved: false
- sandbox_execution_approved: false
post-v0.1 release candidate gate PASS
SUMMARY

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  operator-console-static/demo-data/module-lifecycle-dashboard.json
  operator-console-static/demo-data/generic-knowledge-trail.json
  operator-console-static/demo-data/module-activation-blockers.json
  operator-console-static/demo-data/module-mock-runtime-trail.json
  operator-console-static/demo-data/module-review-checklist.json
  docs/operator-console/module-lifecycle-dashboard.md
  docs/operator-console/generic-knowledge-trail-view.md
  docs/operator-console/module-review-panel.md
  docs/operator-console/module-dashboard-safety-review.md
  docs/adr/0081-read-only-module-lifecycle-dashboard.md
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing module lifecycle dashboard artifact: $file" >&2
    exit 1
  }
done

grep -q "Module Lifecycle" operator-console-static/index.html || {
  echo "Module Lifecycle navigation is missing" >&2
  exit 1
}

grep -q "This dashboard is read-only. Activation is blocked by design." operator-console-static/index.html || {
  echo "read-only activation block banner is missing" >&2
  exit 1
}

grep -q "isLocalApiOrigin" operator-console-static/app.js || {
  echo "localhost API guard missing" >&2
  exit 1
}

grep -q "127.0.0.1" operator-console-static/app.js || {
  echo "127.0.0.1 API guard missing" >&2
  exit 1
}

for key in raw_prompt hidden_reasoning; do
  grep -q "$key" operator-console-static/app.js || {
    echo "redaction key missing from app.js: $key" >&2
    exit 1
  }
done

if grep -n -E "method:[[:space:]]*[\"'](PUT|PATCH|DELETE)[\"']" operator-console-static/app.js; then
  echo "write HTTP method found in app.js" >&2
  exit 1
fi

if grep -R -n -E "https?://" operator-console-static | grep -v -E "localhost|127\\.0\\.0\\.1"; then
  echo "non-local URL found in static console" >&2
  exit 1
fi

grep -q "0081-read-only-module-lifecycle-dashboard.md" docs/adr/README.md || {
  echo "ADR 0081 is not indexed" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

root = Path(sys.argv[1])
demo_dir = root / "operator-console-static" / "demo-data"


def load(name: str) -> dict[str, Any]:
    return json.loads((demo_dir / name).read_text())


dashboard = load("module-lifecycle-dashboard.json")
if dashboard.get("read_only") is not True:
    raise SystemExit("lifecycle dashboard must be read_only")
if dashboard.get("redaction_applied") is not True:
    raise SystemExit("lifecycle dashboard must be redaction_applied")
labels = dashboard.get("safety_labels", {})
for key in (
    "activation_allowed",
    "execution_allowed",
    "registration_allowed",
    "code_loaded",
    "external_calls_made",
):
    if labels.get(key) is not False:
        raise SystemExit(f"{key} must be false")
stage_keys = {stage.get("stage_key") for stage in dashboard.get("stages", [])}
for key in ("activation_gate", "module_mock_runtime", "operator_review"):
    if key not in stage_keys:
        raise SystemExit(f"missing lifecycle stage: {key}")

trail = load("generic-knowledge-trail.json")
capabilities = trail.get("capabilities", [])
expected_capabilities = {
    "generic.knowledge.retrieve",
    "generic.knowledge.summarize",
    "generic.knowledge.ground",
    "generic.knowledge.explain",
    "generic.knowledge.answer",
}
if {item.get("capability_key") for item in capabilities} != expected_capabilities:
    raise SystemExit("generic knowledge capability keys mismatch")
for item in capabilities:
    for key, expected in (
        ("controlled_supported", False),
        ("dry_run_supported", True),
        ("activation_allowed", False),
        ("external_calls_made", False),
        ("code_loaded", False),
    ):
        if item.get(key) is not expected:
            raise SystemExit(f"{item.get('capability_key')} {key} must be {expected}")

blockers = load("module-activation-blockers.json")
blocker_keys = {item.get("blocker_key") for item in blockers.get("blockers", [])}
for key in (
    "activation_disabled",
    "code_loading_disabled",
    "package_install_disabled",
    "dynamic_route_registration_disabled",
    "runtime_registration_disabled",
):
    if key not in blocker_keys:
        raise SystemExit(f"missing expected blocker: {key}")
for item in blockers.get("blockers", []):
    if item.get("bypassable") is not False:
        raise SystemExit(f"blocker must not be bypassable: {item}")

mock = load("module-mock-runtime-trail.json")
if mock.get("synthetic") is not True:
    raise SystemExit("mock runtime trail must be synthetic")
for key in ("external_calls_made", "code_loaded", "activation_allowed", "execution_allowed"):
    if mock.get(key) is not False:
        raise SystemExit(f"mock runtime {key} must be false")
if "confidence" not in mock:
    raise SystemExit("mock runtime confidence missing")

review = load("module-review-checklist.json")
checks = {item.get("check_key") for item in review.get("checklist", [])}
for key in (
    "manifest_valid",
    "no_executable_payload",
    "no_external_source",
    "no_dynamic_route",
    "no_full_autonomy",
    "bindings_validated",
    "conformance_dry_run_passed",
    "readiness_created",
    "activation_blocked",
    "mock_runtime_synthetic",
    "audit_provenance_expected",
):
    if key not in checks:
        raise SystemExit(f"missing review check: {key}")
if review.get("approval_scope") != "review_only":
    raise SystemExit("review approval scope must stay review_only")

changed = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
untracked = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()

blocked_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
blocked_prefixes = (
    "vite.config.",
    "next.config.",
    "tailwind.config.",
    "webpack.config.",
)
blocked_paths = (
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "packages/aion-sdk-python/src/aion_sdk/resources/",
    "packages/aion-sdk-python/src/aion_sdk/cli.py",
)
allowed_runtime_paths = {
    "services/brain-api/src/aion_brain/api/local_auth.py",
    "services/brain-api/src/aion_brain/api/local_session.py",
    "services/brain-api/src/aion_brain/api/action_authorization.py",
    "services/brain-api/src/aion_brain/api/auth_runtime.py",
    "services/brain-api/src/aion_brain/api/connector_runtime.py",
    "services/brain-api/src/aion_brain/api/connector_simulator.py",
    "services/brain-api/src/aion_brain/api/connector_policy.py",
    "services/brain-api/src/aion_brain/api/connector_sandbox.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/local_auth.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/local_session.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/action_authorization.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/auth_runtime.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_policy.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox.py",
}
for name in [*changed, *untracked]:
    basename = Path(name).name
    if basename in blocked_names or any(basename.startswith(prefix) for prefix in blocked_prefixes):
        raise SystemExit(f"frontend package or build file changed: {name}")
    if name.startswith(blocked_paths) and name not in allowed_runtime_paths:
        raise SystemExit(f"out-of-scope runtime file changed: {name}")

print("Module lifecycle dashboard JSON and boundary checks PASS")
PY

echo "Module lifecycle dashboard check PASS"

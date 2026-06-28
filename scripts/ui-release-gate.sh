#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

checks=(
  ./scripts/operator-console-static-check.sh
  ./scripts/module-lifecycle-dashboard-check.sh
  ./scripts/provider-dashboard-check.sh
  ./scripts/operator-actions-check.sh
  ./scripts/local-auth-check.sh
  ./scripts/local-session-check.sh
  ./scripts/role-filter-check.sh
  ./scripts/action-authorization-check.sh
  ./scripts/auth-runtime-check.sh
  ./scripts/static-console-safety-check.sh
)

for check in "${checks[@]}"; do
  "$check"
done

required_files=(
  docs/operator-console/ui-release-gate.md
  docs/operator-console/static-console-safety-matrix.md
  docs/operator-console/operator-platform-checkpoint.md
  docs/operator-console/post-v0.1-ui-no-go-conditions.md
  docs/operator-console/static-console-artifact-manifest.md
  docs/operator-console/ui-release-evidence-summary.md
  docs/adr/0091-static-console-ui-release-gate.md
  examples/operator-console/static-console-artifact-manifest.json
  examples/operator-console/ui-release-gate-result.json
  examples/operator-console/ui-safety-matrix.json
  operator-console-static/index.html
  operator-console-static/app.js
  operator-console-static/styles.css
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing UI release gate artifact: $file" >&2
    exit 1
  }
done

grep -q "0091-static-console-ui-release-gate.md" docs/adr/README.md || {
  echo "ADR 0091 is not indexed" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
examples = [
    root / "examples/operator-console/static-console-artifact-manifest.json",
    root / "examples/operator-console/ui-release-gate-result.json",
    root / "examples/operator-console/ui-safety-matrix.json",
]
for path in examples:
    payload = json.loads(path.read_text())
    serialized = json.dumps(payload, sort_keys=True).lower()
    for marker in (
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
        "password",
        "api_key",
        "private_key",
        "bearer ",
        "sk-",
        "ghp_",
        "xoxb-",
    ):
        if marker in serialized:
            raise SystemExit(f"unsafe UI release example marker in {path}: {marker}")

result = json.loads((root / "examples/operator-console/ui-release-gate-result.json").read_text())
if result.get("status") != "passed":
    raise SystemExit("UI release gate result example must pass")
for key, value in result.get("safety_flags", {}).items():
    if key.startswith("no_"):
        if value is not True:
            raise SystemExit(f"{key} must be true in gate result")
    elif value is not False:
        raise SystemExit(f"{key} must be false in gate result")

matrix = json.loads((root / "examples/operator-console/ui-safety-matrix.json").read_text())
for row in matrix.get("controls", []):
    if row.get("checked_by_script") is not True:
        raise SystemExit(f"matrix control is not checked by script: {row}")
    if row.get("release_blocker_if_failed") is not True:
        raise SystemExit(f"matrix control is not a release blocker: {row}")

manifest = json.loads(
    (root / "examples/operator-console/static-console-artifact-manifest.json").read_text()
)
for key in ("static_files", "demo_data", "scripts", "docs", "tests"):
    if not manifest.get(key):
        raise SystemExit(f"manifest missing {key}")
for key, value in manifest.get("safety_flags", {}).items():
    if value is not False:
        raise SystemExit(f"manifest unsafe flag must be false: {key}")

print("UI release gate examples PASS")
PY

echo "UI release gate PASS"

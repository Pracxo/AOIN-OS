#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  services/brain-api/src/aion_brain/contracts/operator_actions.py
  services/brain-api/src/aion_brain/operator_actions/repository.py
  services/brain-api/src/aion_brain/api/operator_actions.py
  infra/postgres/migrations/0092_operator_actions.sql
  operator-console-static/demo-data/operator-action-preview.json
  operator-console-static/demo-data/operator-action-blockers.json
  operator-console-static/demo-data/operator-action-review.json
  docs/operator-console/governed-operator-actions.md
  docs/operator-console/action-preview-panel.md
  docs/operator-console/action-review-flow.md
  docs/operator-console/action-boundary-matrix.md
  docs/adr/0083-governed-operator-actions-dry-run-only.md
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing operator action artifact: $file" >&2
    exit 1
  }
done

grep -q "Operator Actions" operator-console-static/index.html || {
  echo "operator actions panel missing" >&2
  exit 1
}

grep -q "operator_actions" operator-console-static/app.js || {
  echo "operator actions renderer missing" >&2
  exit 1
}

if grep -n -E "method:[[:space:]]*[\"'](PUT|PATCH|DELETE)[\"']" operator-console-static/app.js; then
  echo "write HTTP method found in static app" >&2
  exit 1
fi

if grep -R -n -E "https?://" operator-console-static | grep -v -E "localhost|127\\.0\\.0\\.1"; then
  echo "non-local URL found in static console" >&2
  exit 1
fi

grep -q "0083-governed-operator-actions-dry-run-only.md" docs/adr/README.md || {
  echo "ADR 0083 is not indexed" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
demo_names = [
    "operator-action-preview.json",
    "operator-action-blockers.json",
    "operator-action-review.json",
]
for name in demo_names:
    payload = json.loads((root / "operator-console-static" / "demo-data" / name).read_text())
    if payload.get("read_only") is not True:
        raise SystemExit(f"read_only must be true: {name}")
    if payload.get("redaction_applied") is not True:
        raise SystemExit(f"redaction_applied must be true: {name}")
    for key in ("execution_allowed", "external_calls_allowed", "activation_allowed"):
        if payload.get(key) is not False:
            raise SystemExit(f"{key} must be false: {name}")
    if name == "operator-action-preview.json" and payload.get("would_execute") is not False:
        raise SystemExit("would_execute must be false in preview demo")
    serialized = json.dumps(payload, sort_keys=True).lower()
    blocked = (
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
        "password",
        "api_key",
        "private_key",
        "authorization",
        "bearer ",
        "sk-",
        "ghp_",
        "xoxb-",
    )
    if any(value in serialized for value in blocked):
        raise SystemExit(f"unsafe demo content: {name}")

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
for name in [*changed, *untracked]:
    basename = Path(name).name
    if basename in blocked_names or any(basename.startswith(prefix) for prefix in blocked_prefixes):
        raise SystemExit(f"frontend package or build file changed: {name}")

print("Operator action dry-run checks PASS")
PY

echo "Operator actions check PASS"

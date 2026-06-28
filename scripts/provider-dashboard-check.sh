#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  operator-console-static/demo-data/provider-hardening-view-model.json
  docs/operator-console/operator-console-strategy.md
  docs/operator-console/static-console-safety-review.md
  examples/operator-console/provider-hardening-flow.json
  examples/operator-console/provider-hardening-view-model-example.json
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing provider dashboard artifact: $file" >&2
    exit 1
  }
done

grep -q "Model Provider Hardening" operator-console-static/index.html || {
  echo "provider dashboard navigation missing" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
payload = json.loads(
    (root / "operator-console-static/demo-data/provider-hardening-view-model.json").read_text()
)
if payload.get("read_only") is not True:
    raise SystemExit("provider dashboard demo must be read_only")
if payload.get("redaction_applied") is not True:
    raise SystemExit("provider dashboard demo must be redacted")
for action in payload.get("forbidden_actions", []):
    if action.get("enabled") is True:
        raise SystemExit(f"provider forbidden action must be disabled: {action}")
serialized = json.dumps(payload, sort_keys=True).lower()
for marker in (
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
    "api_key",
    "private_key",
    "authorization",
    "bearer ",
    "sk-",
    "ghp_",
    "xoxb-",
):
    if marker in serialized:
        raise SystemExit(f"unsafe provider dashboard demo marker: {marker}")

print("Provider dashboard static checks PASS")
PY

./scripts/model-provider-check.sh --skip-api

echo "Provider dashboard check PASS"

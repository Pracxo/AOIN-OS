#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

docs=(
  docs/operator-console/view-model-contract.md
  docs/operator-console/data-source-map.md
  docs/operator-console/api-contract-audit.md
  docs/operator-console/read-only-action-model.md
  docs/operator-console/view-redaction-rules.md
  docs/operator-console/console-api-examples.md
  docs/adr/0079-operator-console-read-only-view-models.md
)

for file in "${docs[@]}"; do
  test -f "$file" || { echo "missing operator console contract doc: $file" >&2; exit 1; }
done

grep -q "0079-operator-console-read-only-view-models.md" docs/adr/README.md || {
  echo "ADR 0079 is not indexed" >&2
  exit 1
}

python3 - <<'PY'
import json
from pathlib import Path

root = Path("examples/operator-console")
required = {
    "view-model-request.json",
    "console-audit-request.json",
    "overview-view-model-example.json",
    "module-lifecycle-view-model-example.json",
    "provider-hardening-view-model-example.json",
}
missing = sorted(name for name in required if not (root / name).is_file())
if missing:
    raise SystemExit(f"missing operator console examples: {missing}")

unsafe = (
    "sk-",
    "xoxb-",
    "ghp_",
    "api_key",
    "authorization",
    "password",
    "private_key",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
)
ui_release_gate_examples = {
    "static-console-artifact-manifest.json",
    "ui-release-gate-result.json",
    "ui-safety-matrix.json",
}
for path in sorted(root.glob("*.json")):
    if path.name in ui_release_gate_examples:
        continue
    payload = json.loads(path.read_text())
    serialized = json.dumps(payload, sort_keys=True).lower()
    for marker in unsafe:
        if marker in serialized:
            raise SystemExit(f"unsafe operator console example content: {path}")
PY

frontend_files=(
  package.json
  pnpm-lock.yaml
  yarn.lock
  package-lock.json
)

for file in "${frontend_files[@]}"; do
  if find . -path ./.git -prune -o -name "$file" -print | grep -q .; then
    echo "frontend package file is forbidden: $file" >&2
    exit 1
  fi
done

for pattern in "vite.config.*" "next.config.*" "tailwind.config.*"; do
  if find . -path ./.git -prune -o -name "$pattern" -print | grep -q .; then
    echo "frontend config file is forbidden: $pattern" >&2
    exit 1
  fi
done

grep -q "AION_OPERATOR_CONSOLE_READ_ONLY=true" .env.example
grep -q "AION_OPERATOR_CONSOLE_WRITE_ACTIONS_ENABLED=false" .env.example
grep -q "AION_OPERATOR_CONSOLE_FRONTEND_ENABLED=false" .env.example

combined="$(cat "${docs[@]}" README.md AGENTS.md)"
for statement in \
  "read-only" \
  "no runtime UI" \
  "no raw prompt exposure" \
  "no hidden reasoning exposure" \
  "no secret exposure" \
  "no activation" \
  "no execution"; do
  grep -i -q "$statement" <<<"$combined" || {
    echo "operator console docs missing required statement: $statement" >&2
    exit 1
  }
done

echo "Operator console contract check PASS"

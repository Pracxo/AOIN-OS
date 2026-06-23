#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/operator-console/operator-console-strategy.md
  docs/operator-console/operator-console-workflows.md
  docs/operator-console/operator-view-spec.md
  docs/operator-console/operator-data-safety.md
  docs/operator-console/operator-action-boundaries.md
  docs/operator-console/operator-demo-map.md
  docs/operator-console/operator-console-no-go.md
  docs/operator-console/future-ui-milestones.md
  docs/adr/0078-operator-console-cli-api-first-decision.md
)

for file in "${required_docs[@]}"; do
  test -f "$file" || { echo "missing operator console artifact: $file" >&2; exit 1; }
done

grep -q "0078-operator-console-cli-api-first-decision.md" docs/adr/README.md || {
  echo "ADR 0078 is not indexed" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
example_dir = root / "examples" / "operator-console"
required_examples = {
    "operator-overview-flow.json",
    "release-readiness-flow.json",
    "module-lifecycle-flow.json",
    "provider-hardening-flow.json",
    "incident-review-flow.json",
    "golden-path-flow.json",
    "console-view-map.json",
}

for name in required_examples:
    path = example_dir / name
    if not path.exists():
        raise SystemExit(f"missing operator console example: {path}")
    payload = json.loads(path.read_text())
    text = json.dumps(payload, sort_keys=True).lower()
    forbidden = ("api_key", "apikey", "authorization", "bearer ", "secret=", "sk-")
    if any(item in text for item in forbidden):
        raise SystemExit(f"unsafe operator console example content: {path}")
    if payload.get("external_calls_allowed") is not False:
        raise SystemExit(f"example must disable external calls: {path}")

module_flow = json.loads((example_dir / "module-lifecycle-flow.json").read_text())
if module_flow["expected"].get("activation_allowed") is not False:
    raise SystemExit("module lifecycle flow must expect activation_allowed=false")

provider_flow = json.loads((example_dir / "provider-hardening-flow.json").read_text())
if provider_flow["expected"].get("external_call_ready") is not False:
    raise SystemExit("provider hardening flow must expect external_call_ready=false")

view_map = json.loads((example_dir / "console-view-map.json").read_text())
views = {item["view"] for item in view_map.get("views", [])}
if "Module Lifecycle" not in views:
    raise SystemExit("console view map must include Module Lifecycle")
for item in view_map.get("views", []):
    if item.get("write_actions") not in {"dry_run", "forbidden"}:
        raise SystemExit(f"view write action must be dry_run or forbidden: {item}")

diff_names = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
untracked_names = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
frontend_files = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
}
frontend_prefixes = (
    "vite.config.",
    "next.config.",
    "tailwind.config.",
)
for name in [*diff_names, *untracked_names]:
    basename = Path(name).name
    if basename in frontend_files or any(basename.startswith(prefix) for prefix in frontend_prefixes):
        raise SystemExit(f"frontend package/build file changed: {name}")

print("Operator console JSON and diff checks PASS")
PY

combined_docs="$(mktemp)"
trap 'rm -f "$combined_docs"' EXIT
cat "${required_docs[@]}" README.md AGENTS.md > "$combined_docs"

for statement in \
  "CLI/API-first" \
  "AION-087 adds no runtime UI" \
  "no frontend dependencies" \
  "raw prompts" \
  "hidden reasoning" \
  "secrets" \
  "activate module" \
  "external model calls"; do
  grep -i -q "$statement" "$combined_docs" || {
    echo "operator console docs missing required statement: $statement" >&2
    exit 1
  }
done

if grep -R -i -E "npm install|pnpm add|yarn add|bun add|create vite|next dev" docs/operator-console docs/adr/0078-operator-console-cli-api-first-decision.md README.md AGENTS.md; then
  echo "frontend dependency install instruction found" >&2
  exit 1
fi

echo "Operator console check PASS"

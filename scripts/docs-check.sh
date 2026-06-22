#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

key_docs=(
  README.md
  AGENTS.md
  docs/operations/operator-runbook.md
  docs/operations/local-demo-pack.md
  docs/operations/troubleshooting.md
  docs/operations/v0.1-release-handoff.md
  docs/release/v0.1-release-candidate-checklist.md
  docs/release/v0.1-demo-script.md
  docs/release/v0.1-no-go-conditions.md
  docs/release/v0.1-post-release-roadmap.md
)

for file in "${key_docs[@]}"; do
  test -f "$file" || { echo "missing doc: $file" >&2; exit 1; }
done

for adr in 0069 0070 0071; do
  grep -q "$adr" docs/adr/README.md || {
    echo "ADR index missing $adr" >&2
    exit 1
  }
done

for link in \
  "docs/operations/operator-runbook.md" \
  "docs/operations/local-demo-pack.md" \
  "docs/operations/troubleshooting.md" \
  "docs/operations/v0.1-release-handoff.md" \
  "docs/release/v0.1-no-go-conditions.md" \
  "docs/release/v0.1-post-release-roadmap.md"; do
  grep -q "$link" README.md || {
    echo "README missing link: $link" >&2
    exit 1
  }
done

for boundary in \
  "production auth" \
  "full autonomy" \
  "extension code loading" \
  "capability activation" \
  "hard-delete"; do
  grep -R -i -q "$boundary" docs/operations/operator-runbook.md docs/release/v0.1-no-go-conditions.md || {
    echo "docs missing disabled boundary: $boundary" >&2
    exit 1
  }
done

python3 - <<'PY'
import json
from pathlib import Path

for path in sorted(Path("examples/demo").glob("*.json")):
    with path.open() as handle:
        json.load(handle)
print("JSON examples valid")
PY

test -x examples/demo/operator-overview-curl.sh
test -x examples/demo/local-demo-sequence.sh
test -x scripts/demo-local.sh
test -x scripts/operator-runbook-check.sh
test -x scripts/docs-check.sh
test -x scripts/final-docs-audit.sh

echo "Docs check PASS"

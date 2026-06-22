#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/operator-runbook-check.sh
./scripts/docs-check.sh

audit_paths=(
  docs/operations/operator-runbook.md
  docs/operations/local-demo-pack.md
  docs/operations/troubleshooting.md
  docs/operations/v0.1-release-handoff.md
  docs/release/v0.1-release-candidate-checklist.md
  docs/release/v0.1-demo-script.md
  docs/release/v0.1-no-go-conditions.md
  docs/release/v0.1-post-release-roadmap.md
  examples/demo
)

if grep -R -F -q "TODO_RELEASE_BLOCKER" "${audit_paths[@]}"; then
  echo "TODO_RELEASE_BLOCKER marker found" >&2
  exit 1
fi

for marker in "raw prompt" "raw_prompt" "hidden reasoning" "hidden_reasoning" "chain-of-thought" "chain_of_thought"; do
  if grep -R -i -F -q "$marker" "${audit_paths[@]}"; then
    echo "private reasoning or source prompt marker found: $marker" >&2
    exit 1
  fi
done

for vertical in finance trading medical healthcare legal procurement payments; do
  if grep -R -i -F -q "$vertical" examples/demo; then
    echo "vertical demo term found: $vertical" >&2
    exit 1
  fi
done

echo "Final docs audit PASS"

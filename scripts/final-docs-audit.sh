#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/operator-runbook-check.sh
./scripts/docs-check.sh

audit_paths=(
  VERSION
  CHANGELOG.md
  RELEASE_NOTES.md
  docs/operations/operator-runbook.md
  docs/operations/local-demo-pack.md
  docs/operations/troubleshooting.md
  docs/operations/v0.1-release-handoff.md
  docs/release/v0.1-final-freeze.md
  docs/release/v0.1-final-evidence-summary.md
  docs/release/v0.1-tagging-guide.md
  docs/release/v0.1-release-baseline.md
  docs/release/v0.1-operator-acceptance.md
  docs/release/v0.1-known-limitations.md
  docs/release/v0.1-release-candidate-checklist.md
  docs/release/v0.1-demo-script.md
  docs/release/v0.1-no-go-conditions.md
  docs/release/v0.1-post-release-roadmap.md
  docs/adr/0072-v0.1-release-freeze-baseline.md
  examples/demo
)

for file in VERSION CHANGELOG.md RELEASE_NOTES.md; do
  test -f "$file" || { echo "missing release artifact: $file" >&2; exit 1; }
done

grep -qx "0.1.0" VERSION || {
  echo "VERSION must equal 0.1.0" >&2
  exit 1
}

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

for claim in "production ready" "production-ready" "ready for production"; do
  if grep -R -i -F -q "$claim" "${audit_paths[@]}"; then
    echo "production readiness claim found: $claim" >&2
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

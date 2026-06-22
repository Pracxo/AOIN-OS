#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  docs/operations/operator-runbook.md
  docs/operations/local-demo-pack.md
  docs/operations/troubleshooting.md
  docs/operations/v0.1-release-handoff.md
  docs/release/v0.1-release-candidate-checklist.md
  docs/release/v0.1-demo-script.md
  docs/release/v0.1-no-go-conditions.md
  docs/release/v0.1-post-release-roadmap.md
)

for file in "${required_files[@]}"; do
  test -f "$file" || { echo "missing required runbook file: $file" >&2; exit 1; }
done

grep -q "AION = Adaptive Intelligence Orchestration Nexus" docs/operations/operator-runbook.md
grep -q "AION OS = Adaptive Intelligence Orchestration Nexus Operating System" docs/operations/operator-runbook.md

required_strings=(
  "docker compose config --quiet"
  "docker compose up --build -d brain-api postgres redis nats opa"
  "curl -fsS http://localhost:8080/health"
  "curl -fsS http://localhost:8080/health/ready"
  "./scripts/setup-doctor.sh --fast --offline-ok"
  "./scripts/golden-path.sh --offline-ok"
  "./scripts/rc-check.sh --offline-ok"
  "./scripts/demo-local.sh --offline-ok"
  "docker compose down"
)

for expected in "${required_strings[@]}"; do
  if ! grep -R -F -q "$expected" docs/operations docs/release README.md; then
    echo "missing required command string: $expected" >&2
    exit 1
  fi
done

for boundary in \
  "does not enable production auth" \
  "does not enable full autonomy" \
  "does not execute model-generated tool calls" \
  "does not load extension code" \
  "does not activate capability bindings" \
  "does not send external notifications" \
  "does not hard-delete records"; do
  grep -q "$boundary" docs/operations/operator-runbook.md || {
    echo "missing disabled boundary: $boundary" >&2
    exit 1
  }
done

for claim in \
  "production ready" \
  "full autonomy enabled" \
  "external model calls enabled" \
  "extension code loading enabled" \
  "hard delete enabled"; do
  if grep -R -i -F -q "$claim" docs/operations/operator-runbook.md docs/operations/local-demo-pack.md docs/operations/v0.1-release-handoff.md; then
    echo "forbidden positive claim found: $claim" >&2
    exit 1
  fi
done

for marker in "sk-" "OPENAI_API_KEY=" "password=" "bearer token" "private_key"; do
  if grep -R -i -F -q "$marker" docs/operations docs/release examples/demo; then
    echo "raw secret example marker found: $marker" >&2
    exit 1
  fi
done

echo "Operator runbook check PASS"

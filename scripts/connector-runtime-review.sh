#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/connectors/connector-runtime-review-gate.md
  docs/connectors/no-external-call-evidence-pack.md
  docs/connectors/connector-credential-token-absence-proof.md
  docs/connectors/connector-egress-ingress-traceability-matrix.md
  docs/connectors/connector-runtime-disabled-proof.md
  docs/connectors/connector-pre-implementation-gate.md
  docs/connectors/connector-runtime-review-no-go-pack.md
  docs/connectors/future-connector-runtime-implementation-plan.md
  docs/adr/0100-connector-runtime-review-gate.md
)

required_examples=(
  examples/connectors/connector-runtime-review-gate.json
  examples/connectors/no-external-call-evidence-pack.json
  examples/connectors/connector-credential-token-absence-proof.json
  examples/connectors/connector-egress-ingress-traceability-matrix.json
  examples/connectors/connector-runtime-review-no-go-result.json
)

for file in "${required_docs[@]}" "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing connector runtime review artifact: $file" >&2
    exit 1
  }
done

grep -q "0100-connector-runtime-review-gate.md" docs/adr/README.md || {
  echo "ADR 0100 is not indexed" >&2
  exit 1
}

./scripts/connector-runtime-check.sh
./scripts/connector-boundary-design-check.sh
./scripts/connector-no-go-regression.sh
./scripts/connector-runtime-no-external-call-regression.sh
./scripts/operator-action-write-path-design-check.sh
AION_OPERATOR_PLATFORM_SKIP_FULL_CHECK=1 ./scripts/operator-platform-freeze-gate.sh
./scripts/ui-release-gate.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-109 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-109 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$' \
  | rg -n '.'; then
  echo "AION-109 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$|^services/brain-api/src/aion_brain/api/connector_sandbox\.py$' \
  | rg -n '.'; then
  echo "AION-109 must not add API router files" >&2
  exit 1
fi

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-109: $file" >&2
    exit 1
  fi
done

if rg -n 'https?://|sk-|ghp_|xoxb-|-----BEGIN PRIVATE KEY-----|bearer |basic |api_key|private_key|access_token|refresh_token|id_token|client_secret|raw_prompt|hidden_reasoning|chain_of_thought' \
  "${required_examples[@]}"; then
  echo "blocked marker found in AION-109 connector examples" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-109 artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
patterns = [
    "examples/connectors/connector-runtime-review*.json",
    "examples/connectors/no-external-call*.json",
    "examples/connectors/connector-credential-token*.json",
    "examples/connectors/connector-egress-ingress-traceability-matrix.json",
    "examples/connectors/connector-runtime-review-no-go-result.json",
]
paths: list[Path] = []
for pattern in patterns:
    paths.extend(sorted(root.glob(pattern)))

if len({path for path in paths}) != 5:
    raise SystemExit("AION-109 connector review examples are incomplete")

for path in sorted(set(paths)):
    payload = json.loads(path.read_text())
    if payload.get("synthetic") is not True:
        raise SystemExit(f"example must be synthetic: {path}")
    if payload.get("status") != "passed":
        raise SystemExit(f"example status must be passed: {path}")

review = json.loads((root / "examples/connectors/connector-runtime-review-gate.json").read_text())
for key in (
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_enabled",
    "token_storage_enabled",
    "activation_enabled",
    "route_registration_enabled",
):
    if review.get(key) is not False:
        raise SystemExit(f"{key} must be false")

evidence = json.loads((root / "examples/connectors/no-external-call-evidence-pack.json").read_text())
if evidence.get("external_calls_found") is not False:
    raise SystemExit("external_calls_found must be false")
for item in evidence.get("evidence", []):
    if item.get("expected_status") != "passed":
        raise SystemExit(f"evidence row must be passed: {item}")
    if item.get("release_blocker") is not True:
        raise SystemExit(f"evidence row must be release blocking: {item}")

proof = json.loads((root / "examples/connectors/connector-credential-token-absence-proof.json").read_text())
for key in (
    "credentials_present",
    "token_storage_present",
    "provider_sdk_present",
    "secret_examples_present",
):
    if proof.get(key) is not False:
        raise SystemExit(f"{key} must be false")

trace = json.loads(
    (root / "examples/connectors/connector-egress-ingress-traceability-matrix.json").read_text()
)
if trace.get("no_external_call") is not True:
    raise SystemExit("traceability matrix must declare no_external_call=true")
if trace.get("external_calls_found") is not False:
    raise SystemExit("traceability matrix must keep external_calls_found=false")

no_go = json.loads((root / "examples/connectors/connector-runtime-review-no-go-result.json").read_text())
for item in no_go.get("checks", []):
    if item.get("expected_status") != "passed" or item.get("present") is not False:
        raise SystemExit(f"no-go row must be passed and absent: {item}")

print("Connector runtime review JSON checks PASS")
PY

cat <<'SUMMARY'
Connector runtime review result:
- connector_runtime: disabled
- external_calls: absent
- credentials_tokens: absent
- activation_routes: disabled
- no_external_call_regression: passed
- pre_implementation_gate: frozen
Connector runtime review PASS
SUMMARY

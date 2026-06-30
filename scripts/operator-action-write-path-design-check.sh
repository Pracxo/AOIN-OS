#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/operator-actions/write-path-architecture.md
  docs/operator-actions/approval-boundary-design.md
  docs/operator-actions/execution-boundary-design.md
  docs/operator-actions/action-intent-lifecycle.md
  docs/operator-actions/controlled-execution-prerequisites.md
  docs/operator-actions/rollback-and-undo-model.md
  docs/operator-actions/separation-of-duties.md
  docs/operator-actions/write-path-threat-model.md
  docs/operator-actions/write-path-release-gates.md
  docs/operator-actions/write-path-no-go-regression-pack.md
  docs/adr/0098-operator-action-write-path-architecture.md
)

required_examples=(
  examples/operator-actions/write-path-architecture.json
  examples/operator-actions/action-intent-lifecycle.json
  examples/operator-actions/write-path-release-gates.json
  examples/operator-actions/write-path-no-go-regression-result.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || {
    echo "missing operator action write-path doc: $file" >&2
    exit 1
  }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing operator action write-path example: $file" >&2
    exit 1
  }
done

test -x scripts/operator-action-write-path-no-go-regression.sh || {
  echo "operator-action-write-path-no-go-regression.sh must be executable" >&2
  exit 1
}

grep -q "0098-operator-action-write-path-architecture.md" docs/adr/README.md || {
  echo "ADR 0098 is not indexed" >&2
  exit 1
}

grep -R -qi "no write execution" docs/operator-actions docs/adr/0098-operator-action-write-path-architecture.md || {
  echo "write-path docs must state no write execution" >&2
  exit 1
}

grep -R -qi "current lifecycle stops at previewed/reviewed/blocked" docs/operator-actions/action-intent-lifecycle.md || {
  echo "lifecycle doc must state the current lifecycle stop" >&2
  exit 1
}

grep -q "future_execution_ready and future_executed are not reachable today" docs/operator-actions/action-intent-lifecycle.md || {
  echo "lifecycle doc must state future execution states are unreachable today" >&2
  exit 1
}

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-107: $file" >&2
    exit 1
  fi
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-107 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations services/brain-api/migrations | rg -n '.'; then
  echo "AION-107 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$|^services/brain-api/src/aion_brain/api/connector_simulator\.py$|^services/brain-api/src/aion_brain/api/connector_policy\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not add API router files" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not add SDK resources or CLI command implementations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard packages/aion-sdk-python/src/aion_sdk/resources packages/aion-sdk-python/src/aion_sdk/cli.py packages/aion-sdk-python/src/aion_sdk/cli \
  | rg -v '^packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/resources/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy\.py$|^packages/aion-sdk-python/src/aion_sdk/cli/main\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not add untracked SDK resources or CLI command implementations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/config.py services/brain-api/src/aion_brain/settings.py \
  | rg -v '^services/brain-api/src/aion_brain/config\.py$' \
  | rg -n '.'; then
  echo "AION-107 must not change runtime config defaults" >&2
  exit 1
fi

if rg -n 'https?://' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "external URL or endpoint found in AION-107 artifacts" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in AION-107 artifacts" >&2
  exit 1
fi

./scripts/operator-action-write-path-no-go-regression.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
example_dir = root / "examples/operator-actions"

examples = [
    example_dir / "write-path-architecture.json",
    example_dir / "action-intent-lifecycle.json",
    example_dir / "write-path-release-gates.json",
    example_dir / "write-path-no-go-regression-result.json",
]

false_keys = {
    "execution_enabled",
    "external_calls_enabled",
    "activation_enabled",
    "write_execution_enabled",
    "tool_execution_enabled",
    "model_generated_execution_enabled",
    "controlled_handoff_execution_enabled",
    "connector_runtime_enabled",
    "production_auth_enabled",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "approval_bypass_enabled",
    "hard_delete_enabled",
    "contains_secrets",
    "contains_credentials",
    "contains_tokens",
    "contains_external_endpoints",
    "contains_unredacted_prompts",
    "contains_private_reasoning",
}


def assert_false_keys(value: object, context: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in false_keys and item is not False:
                raise SystemExit(f"{context}.{key} must be false")
            assert_false_keys(item, f"{context}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_false_keys(item, f"{context}[{index}]")


payloads = []
for path in examples:
    payload = json.loads(path.read_text())
    if payload.get("status") != "passed":
        raise SystemExit(f"{path.name}.status must be passed")
    assert_false_keys(payload, path.name)
    payloads.append(payload)

serialized = json.dumps(payloads, sort_keys=True).lower()
for marker in (
    "sk-",
    "ghp_",
    "xoxb-",
    "-----begin private key-----",
    "bearer ",
    "basic ",
    "api_key",
    "private_key",
    "access_token",
    "refresh_token",
    "id_token",
    "client_secret",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
    "http://",
    "https://",
):
    if marker in serialized:
        raise SystemExit(f"blocked marker found in AION-107 examples: {marker}")

lifecycle = json.loads((example_dir / "action-intent-lifecycle.json").read_text())
required_states = {
    "drafted",
    "requested",
    "dry_run_authorized",
    "previewed",
    "reviewed",
    "approval_required",
    "approved_for_future_execution",
    "blocked",
    "expired",
    "cancelled",
    "future_execution_ready",
    "future_executed",
    "rollback_requested",
    "rollback_completed",
    "archived",
}
missing = required_states - set(lifecycle.get("states", []))
if missing:
    raise SystemExit(f"lifecycle example missing states: {sorted(missing)}")

release = json.loads((example_dir / "write-path-release-gates.json").read_text())
required_gates = {
    "write-path ADR approved",
    "threat model approved",
    "production auth ready",
    "connector boundary ready",
    "approval workflow tested",
    "rollback tested",
    "policy enforcement tested",
    "audit/provenance tested",
    "dry-run parity tested",
    "release/freeze gate green",
}
gates = {row.get("gate") for row in release.get("gates", [])}
missing = required_gates - gates
if missing:
    raise SystemExit(f"write-path release gates missing: {sorted(missing)}")
for row in release.get("gates", []):
    if row.get("release_blocker") is not True:
        raise SystemExit(f"write-path release gate must be blocker: {row}")

print("AION-107 operator action write-path JSON checks PASS")
PY

echo "Operator action write-path design result:"
echo "- write_execution: absent"
echo "- execution: future-only"
echo "- external_calls: disabled"
echo "- activation: disabled"
echo "- no_go_regression: passed"
echo "Operator action write-path design check PASS"

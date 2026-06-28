#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "services/brain-api/src/aion_brain/contracts/action_authorization.py"
  "services/brain-api/src/aion_brain/action_authorization/evaluator.py"
  "services/brain-api/src/aion_brain/action_authorization/audit.py"
  "services/brain-api/src/aion_brain/api/action_authorization.py"
  "packages/aion-sdk-python/src/aion_sdk/resources/action_authorization.py"
  "packages/aion-sdk-python/src/aion_sdk/cli/commands/action_authorization.py"
  "docs/operator-console/dry-run-action-authorization.md"
  "docs/operator-console/action-authorization-preview.md"
  "docs/operator-console/action-authorization-deny-matrix.md"
  "docs/auth/dry-run-action-permission-model.md"
  "docs/auth/action-authorization-audit.md"
  "docs/adr/0088-dry-run-action-authorization-enforcement.md"
  "examples/auth/dry-run-action-authorization-request.json"
  "examples/auth/dry-run-action-authorization-decision.json"
  "examples/auth/action-authorization-deny-examples.json"
  "examples/auth/action-authorization-audit-result.json"
  "operator-console-static/demo-data/action-authorization-preview.json"
  "operator-console-static/demo-data/action-authorization-deny-matrix.json"
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing action authorization artifact: $file" >&2
    exit 1
  }
done

grep -q "0088-dry-run-action-authorization-enforcement.md" docs/adr/README.md || {
  echo "ADR 0088 is not indexed" >&2
  exit 1
}

grep -q "AION_ACTION_AUTHORIZATION_ENABLED=true" .env.example || {
  echo "action authorization env flag missing" >&2
  exit 1
}

for key in \
  AION_ACTION_AUTHORIZATION_WRITE_ALLOWED=false \
  AION_ACTION_AUTHORIZATION_EXECUTION_ALLOWED=false \
  AION_ACTION_AUTHORIZATION_ACTIVATION_ALLOWED=false \
  AION_ACTION_AUTHORIZATION_EXTERNAL_CALLS_ALLOWED=false; do
  grep -q "$key" .env.example || {
    echo "disabled env flag missing: $key" >&2
    exit 1
  }
done

grep -q "action-authorization-panel" operator-console-static/index.html || {
  echo "static action authorization panel missing" >&2
  exit 1
}

grep -q "ACTION_AUTHORIZATION_DEMOS" operator-console-static/app.js || {
  echo "static action authorization renderer missing" >&2
  exit 1
}

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(execute|activation|external)' \
  services/brain-api/src/aion_brain/api/action_authorization.py; then
  echo "action authorization API must not expose execute, activation, or external-call route" >&2
  exit 1
fi

python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

paths = [
    *sorted(Path("examples/auth").glob("*authorization*.json")),
    Path("operator-console-static/demo-data/action-authorization-preview.json"),
    Path("operator-console-static/demo-data/action-authorization-deny-matrix.json"),
]
blocked_key_parts = {
    "api_key",
    "apikey",
    "bearer",
    "cookie",
    "credential",
    "hidden_reasoning",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
blocked_value_markers = {
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
    "raw prompt",
    "raw_prompt",
    "hidden reasoning",
    "hidden_reasoning",
    "chain-of-thought",
    "chain_of_thought",
}
false_flags = {
    "write_allowed",
    "execution_allowed",
    "activation_allowed",
    "external_calls_allowed",
}


def walk(value: object, path: Path) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in blocked_key_parts):
                raise SystemExit(f"unsafe key {key!r} in {path}")
            if normalized in false_flags and nested is not False:
                raise SystemExit(f"{normalized} must be false in {path}")
            walk(nested, path)
    elif isinstance(value, list):
        for item in value:
            walk(item, path)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in blocked_value_markers):
            raise SystemExit(f"unsafe value in {path}")


for path in paths:
    payload = json.loads(path.read_text())
    walk(payload, path)
    serialized = json.dumps(payload, sort_keys=True).lower()
    if "execute_allowed\": true" in serialized or "activation_allowed\": true" in serialized:
        raise SystemExit(f"privileged allowed flag found in {path}")

preview = json.loads(Path("operator-console-static/demo-data/action-authorization-preview.json").read_text())
if preview.get("dry_run_only") is not True:
    raise SystemExit("static action authorization preview must be dry_run_only")
for key in false_flags:
    if preview.get(key) is not False:
        raise SystemExit(f"static action authorization preview {key} must be false")

deny = json.loads(Path("operator-console-static/demo-data/action-authorization-deny-matrix.json").read_text())
if not deny.get("denials"):
    raise SystemExit("deny matrix must include denied decisions")
PY

test -z "$(find infra/postgres/migrations -type f -name '*097*' -print)"

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations | rg -n '097|authorization|authz'; then
  echo "AION-097 must not add a migration" >&2
  exit 1
fi

if git ls-files --others --exclude-standard | rg -n '^infra/postgres/migrations/.*(097|authorization|authz)'; then
  echo "AION-097 must not add an untracked migration" >&2
  exit 1
fi

blocked_frontend_files=(
  package.json
  package-lock.json
  pnpm-lock.yaml
  yarn.lock
  bun.lockb
)
for file in "${blocked_frontend_files[@]}"; do
  test ! -e "$file"
done

install_patterns="npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install"
if rg -n "$install_patterns" docs/auth docs/operator-console operator-console-static; then
  echo "Unexpected package install instruction found" >&2
  exit 1
fi

if rg -n 'httpx|requests|openai|oauth|saml|oidc|ldap|webauthn|passkey' \
  services/brain-api/src/aion_brain/action_authorization; then
  echo "External identity or call dependency found in action authorization runtime" >&2
  exit 1
fi

echo "Action authorization check PASS"

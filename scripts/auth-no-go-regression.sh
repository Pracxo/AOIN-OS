#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

runtime_paths=(
  services/brain-api/src/aion_brain/api
  services/brain-api/src/aion_brain/auth_runtime
  services/brain-api/src/aion_brain/local_auth
  services/brain-api/src/aion_brain/local_session
  services/brain-api/src/aion_brain/action_authorization
  packages/aion-sdk-python/src/aion_sdk
)

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(login|logout|callback|token|oauth|saml|oidc)' \
  services/brain-api/src/aion_brain/api; then
  echo "forbidden auth route found" >&2
  exit 1
fi

if rg -n 'set_cookie|delete_cookie|cookie_issuance_enabled[[:space:]]*=[[:space:]]*True|COOKIE_ISSUANCE_ENABLED=true' \
  "${runtime_paths[@]}" .env.example; then
  echo "cookie issuance path found" >&2
  exit 1
fi

if rg -n 'session_persistence_enabled[[:space:]]*=[[:space:]]*True|SESSION_PERSISTENCE_ENABLED=true|sessionStorage|localStorage' \
  "${runtime_paths[@]}" operator-console-static .env.example; then
  echo "session persistence or browser storage path found" >&2
  exit 1
fi

if rg -n 'password_hash|password_store|store_password|credential_store|credentials_enabled[[:space:]]*=[[:space:]]*True|CREDENTIALS_ENABLED=true' \
  "${runtime_paths[@]}" .env.example; then
  echo "password or credential storage path found" >&2
  exit 1
fi

if rg -n 'authlib|oauth|saml|oidc|ldap|webauthn|passkey|python-jose|jwt|okta|auth0' \
  pyproject.toml services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "provider SDK dependency found" >&2
  exit 1
fi

if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(httpx|requests|authlib|jwt|okta|auth0|jose|python_jose)' \
  services/brain-api/src/aion_brain/auth_runtime \
  services/brain-api/src/aion_brain/local_auth \
  services/brain-api/src/aion_brain/local_session \
  services/brain-api/src/aion_brain/action_authorization; then
  echo "external identity or provider-call dependency found" >&2
  exit 1
fi

if rg -n 'production_auth_enabled[[:space:]]*[:=][[:space:]]*true|PRODUCTION_AUTH_ENABLED=true|auth_runtime_enabled[[:space:]]*[:=][[:space:]]*true|AUTH_RUNTIME_ENABLED=true' \
  services .env.example examples/auth operator-console-static; then
  echo "production auth or auth runtime enablement found" >&2
  exit 1
fi

if rg -n '<form|<input|type=["'\'']password|name=["'\'']?(password|token|cookie|credential)' \
  operator-console-static; then
  echo "auth form or sensitive input found" >&2
  exit 1
fi

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  test ! -e "$file" || {
    echo "package file is not allowed: $file" >&2
    exit 1
  }
done

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations | rg -n '.'; then
  echo "AION-104 must not add or change migrations" >&2
  exit 1
fi

if git ls-files --others --exclude-standard infra/postgres/migrations | rg -n '.'; then
  echo "AION-104 must not add untracked migrations" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_policy\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_sandbox\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_credentials\.py$' \
  | rg -n '.'; then
  echo "AION-104 must not change API router files" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_runtime\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_simulator\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_policy\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_sandbox\.py$' \
  | rg -v '^services/brain-api/src/aion_brain/api/connector_credentials\.py$' \
  | rg -n '.'; then
  echo "AION-104 must not add API router files" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
result_path = root / "examples/auth/auth-no-go-regression-result.json"
payload = json.loads(result_path.read_text())
if payload.get("status") != "passed":
    raise SystemExit("auth no-go regression result must be passed")
checks = payload.get("checks")
if not isinstance(checks, list) or not checks:
    raise SystemExit("auth no-go regression checks must be present")
for check in checks:
    if check.get("expected_status") != "passed":
        raise SystemExit(f"auth no-go check is not passed: {check}")
required = {
    "login route",
    "logout route",
    "token route",
    "callback route",
    "session storage",
    "cookie issuance",
    "password field",
    "token field",
    "credential field",
    "provider SDK",
    "package file",
    "external identity call",
    "production auth enabled",
    "auth bypass",
}
present = {item.get("name") for item in checks}
missing = required - present
if missing:
    raise SystemExit(f"auth no-go regression missing checks: {sorted(missing)}")
for key in (
    "production_auth_enabled",
    "protected_material_present",
    "external_identity_provider_enabled",
):
    if payload.get(key) is not False:
        raise SystemExit(f"{key} must be false")

print("Auth no-go regression JSON checks PASS")
PY

echo "Auth no-go regression PASS"

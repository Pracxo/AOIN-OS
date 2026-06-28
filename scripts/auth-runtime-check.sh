#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "services/brain-api/src/aion_brain/contracts/auth_runtime.py"
  "services/brain-api/src/aion_brain/auth_runtime/__init__.py"
  "services/brain-api/src/aion_brain/auth_runtime/actor_mapping.py"
  "services/brain-api/src/aion_brain/auth_runtime/audit.py"
  "services/brain-api/src/aion_brain/auth_runtime/blockers.py"
  "services/brain-api/src/aion_brain/auth_runtime/gate.py"
  "services/brain-api/src/aion_brain/auth_runtime/mock_claims.py"
  "services/brain-api/src/aion_brain/auth_runtime/query.py"
  "services/brain-api/src/aion_brain/auth_runtime/redaction.py"
  "services/brain-api/src/aion_brain/api/auth_runtime.py"
  "packages/aion-sdk-python/src/aion_sdk/resources/auth_runtime.py"
  "packages/aion-sdk-python/src/aion_sdk/cli/commands/auth_runtime.py"
  "docs/auth/disabled-production-auth-prototype.md"
  "docs/auth/mock-claims-adapter.md"
  "docs/auth/auth-runtime-gate.md"
  "docs/auth/auth-runtime-audit.md"
  "docs/auth/auth-runtime-no-go.md"
  "docs/adr/0090-disabled-production-auth-prototype.md"
  "examples/auth/auth-runtime-status.json"
  "examples/auth/mock-claims-preview-request.json"
  "examples/auth/mock-claims-preview-result.json"
  "examples/auth/auth-runtime-audit-request.json"
  "examples/auth/auth-runtime-blockers.json"
  "operator-console-static/demo-data/auth-runtime-status.json"
  "operator-console-static/demo-data/mock-claims-preview.json"
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing auth runtime artifact: $file" >&2
    exit 1
  }
done

grep -q "0090-disabled-production-auth-prototype.md" docs/adr/README.md || {
  echo "ADR 0090 is not indexed" >&2
  exit 1
}

for key in \
  AION_AUTH_RUNTIME_ENABLED=false \
  AION_AUTH_RUNTIME_MOCK_CLAIMS_PREVIEW_ENABLED=true \
  AION_AUTH_RUNTIME_ACTOR_MAPPING_PREVIEW_ENABLED=true \
  AION_AUTH_RUNTIME_EXTERNAL_IDENTITY_ENABLED=false \
  AION_AUTH_RUNTIME_CREDENTIALS_ENABLED=false \
  AION_AUTH_RUNTIME_TOKEN_ISSUANCE_ENABLED=false \
  AION_AUTH_RUNTIME_COOKIE_ISSUANCE_ENABLED=false \
  AION_AUTH_RUNTIME_SESSION_PERSISTENCE_ENABLED=false \
  AION_AUTH_RUNTIME_LOGIN_ENDPOINT_ENABLED=false \
  AION_AUTH_RUNTIME_LOGOUT_ENDPOINT_ENABLED=false; do
  grep -qx "$key" .env.example || {
    echo "auth runtime env flag missing: $key" >&2
    exit 1
  }
done

grep -q "auth-runtime-panel" operator-console-static/index.html || {
  echo "static auth runtime panel missing" >&2
  exit 1
}

grep -q "AUTH_RUNTIME_DEMOS" operator-console-static/app.js || {
  echo "static auth runtime renderer missing" >&2
  exit 1
}

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(login|logout|callback|token|session|authorize|oauth|saml|oidc)' \
  services/brain-api/src/aion_brain/api/auth_runtime.py; then
  echo "auth runtime API must not expose login/logout/provider/session/token routes" >&2
  exit 1
fi

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(login|logout)' services/brain-api/src/aion_brain/api; then
  echo "unexpected login/logout API route found" >&2
  exit 1
fi

python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

paths = [
    Path("examples/auth/auth-runtime-status.json"),
    Path("examples/auth/mock-claims-preview-request.json"),
    Path("examples/auth/mock-claims-preview-result.json"),
    Path("examples/auth/auth-runtime-audit-request.json"),
    Path("examples/auth/auth-runtime-blockers.json"),
    Path("operator-console-static/demo-data/auth-runtime-status.json"),
    Path("operator-console-static/demo-data/mock-claims-preview.json"),
]
allowed_keys = {
    "credentials_enabled",
    "credentials_present",
    "token_issuance_enabled",
    "token_present",
    "cookie_issuance_enabled",
    "cookie_present",
    "session_persistence_enabled",
    "session_persisted",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "external_identity_provider_enabled",
}
blocked_key_parts = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
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
    "bearer ",
    "basic ",
    "raw prompt",
    "raw_prompt",
    "hidden reasoning",
    "hidden_reasoning",
    "chain-of-thought",
    "chain_of_thought",
}
false_flags = {
    "production_auth_enabled",
    "auth_runtime_enabled",
    "external_identity_provider_enabled",
    "credentials_enabled",
    "token_issuance_enabled",
    "cookie_issuance_enabled",
    "session_persistence_enabled",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "production_identity",
    "credentials_present",
    "token_present",
    "cookie_present",
    "session_persisted",
    "write_allowed",
    "execute_allowed",
    "activation_allowed",
    "external_calls_allowed",
}


def walk(value: object, path: Path) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized not in allowed_keys and any(part in normalized for part in blocked_key_parts):
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

request = json.loads(Path("examples/auth/mock-claims-preview-request.json").read_text())
if request.get("issuer") not in {"mock.local", "test.local"}:
    raise SystemExit("mock claims issuer must be mock.local or test.local")
if request.get("mode") != "preview":
    raise SystemExit("mock claims request must be preview mode")

status = json.loads(Path("examples/auth/auth-runtime-status.json").read_text())
if status.get("mock_claims_preview_enabled") is not True:
    raise SystemExit("mock claims preview flag must be true in status example")
if status.get("actor_mapping_preview_enabled") is not True:
    raise SystemExit("actor mapping preview flag must be true in status example")
PY

test -z "$(find infra/postgres/migrations -type f -name '*099*' -print)"

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations | rg -n '099|auth.runtime|auth_runtime|token|cookie|session'; then
  echo "AION-099 must not add a migration" >&2
  exit 1
fi

if git ls-files --others --exclude-standard | rg -n '^infra/postgres/migrations/.*(099|auth.runtime|auth_runtime|token|cookie|session)'; then
  echo "AION-099 must not add an untracked migration" >&2
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

if rg -n '<form|<input|type="password"|localStorage|sessionStorage|name="token"|name="cookie"|name="credential"' operator-console-static; then
  echo "unexpected static auth input or browser storage found" >&2
  exit 1
fi

install_patterns="npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install"
if rg -n "$install_patterns" docs/auth/disabled-production-auth-prototype.md docs/auth/mock-claims-adapter.md docs/auth/auth-runtime-gate.md docs/auth/auth-runtime-audit.md docs/auth/auth-runtime-no-go.md operator-console-static; then
  echo "unexpected package install instruction found" >&2
  exit 1
fi

if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(httpx|requests|openai|authlib|jwt|okta|auth0|jose|python_jose)' \
  services/brain-api/src/aion_brain/auth_runtime \
  services/brain-api/src/aion_brain/api/auth_runtime.py; then
  echo "provider SDK or external-call dependency found in auth runtime" >&2
  exit 1
fi

if rg -n 'authlib|oauth|saml|oidc|ldap|webauthn|passkey|python-jose|jwt|okta|auth0' \
  pyproject.toml services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml 2>/dev/null; then
  echo "provider SDK dependency found" >&2
  exit 1
fi

echo "Auth runtime check PASS"

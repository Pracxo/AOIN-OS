#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "docs/auth/local-session-prototype.md"
  "docs/auth/local-session-boundary.md"
  "docs/auth/session-safety-audit.md"
  "docs/auth/session-preview-console-panel.md"
  "docs/auth/future-session-implementation-plan.md"
  "docs/adr/0086-read-only-local-session-prototype.md"
  "operator-console-static/demo-data/local-session-status.json"
  "operator-console-static/demo-data/local-session-preview.json"
  "examples/auth/local-session-preview-request.json"
  "examples/auth/local-session-status.json"
  "examples/auth/local-session-boundary-audit-request.json"
  "examples/auth/role-aware-session-context.json"
)

for file in "${required_files[@]}"; do
  test -f "$file"
done

python3 - <<'PY'
import json
from pathlib import Path

paths = [
    *Path("examples/auth").glob("*session*.json"),
    Path("operator-console-static/demo-data/local-session-status.json"),
    Path("operator-console-static/demo-data/local-session-preview.json"),
]
blocked_key_parts = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
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
allowed_keys = {
    "token_issued",
    "tokens_enabled",
    "cookie_issued",
    "cookies_enabled",
    "credential_backed",
    "credentials_enabled",
}


def walk(value, path):
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized not in allowed_keys and any(part in normalized for part in blocked_key_parts):
                raise SystemExit(f"unsafe key {key!r} in {path}")
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
PY

grep -q "0086-read-only-local-session-prototype.md" docs/adr/README.md

grep -q "AION_LOCAL_SESSION_PREVIEW_ENABLED=true" .env.example
grep -q "AION_LOCAL_SESSION_CONTEXT_ENABLED=true" .env.example
grep -q "AION_LOCAL_SESSION_AUDIT_ENABLED=true" .env.example
grep -q "AION_LOCAL_SESSION_DEV_ONLY=true" .env.example
grep -q "AION_LOCAL_SESSION_READ_ONLY=true" .env.example
grep -q "AION_LOCAL_SESSION_CREDENTIALS_ENABLED=false" .env.example
grep -q "AION_LOCAL_SESSION_TOKENS_ENABLED=false" .env.example
grep -q "AION_LOCAL_SESSION_COOKIES_ENABLED=false" .env.example
grep -q "AION_LOCAL_SESSION_PERSISTENCE_ENABLED=false" .env.example
grep -q "AION_LOCAL_SESSION_WRITE_ACTIONS_ENABLED=false" .env.example
grep -q "AION_LOCAL_SESSION_EXECUTION_ENABLED=false" .env.example
grep -q "AION_LOCAL_SESSION_ACTIVATION_ENABLED=false" .env.example
grep -q "AION_LOCAL_SESSION_EXTERNAL_CALLS_ENABLED=false" .env.example

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(login|logout)' services/brain-api/src/aion_brain/api; then
  echo "Unexpected login/logout API route found" >&2
  exit 1
fi

test -z "$(find infra/postgres/migrations -type f -name '*095*' -print)"

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

if find . -maxdepth 1 -type f \( -name 'vite.config.*' -o -name 'next.config.*' -o -name 'tailwind.config.*' -o -name 'webpack.config.*' \) | grep -q .; then
  echo "Unexpected frontend config file found" >&2
  exit 1
fi

install_patterns="npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install"
if rg -n "$install_patterns" operator-console-static docs/auth/local-session-prototype.md docs/auth/local-session-boundary.md docs/auth/session-safety-audit.md docs/auth/session-preview-console-panel.md docs/auth/future-session-implementation-plan.md; then
  echo "Unexpected package install instruction found" >&2
  exit 1
fi

if rg -n '<form|type="password"|localStorage|sessionStorage' operator-console-static; then
  echo "Unexpected login form or browser session storage found" >&2
  exit 1
fi

echo "Local session check PASS"

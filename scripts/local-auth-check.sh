#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/auth/local-auth-contract.md
  docs/auth/dev-identity-simulation.md
  docs/auth/role-aware-console-filtering.md
  docs/auth/local-auth-audit.md
  docs/auth/local-auth-runtime-boundaries.md
  docs/adr/0085-local-auth-contract-dev-identity-simulation.md
)

required_examples=(
  examples/auth/local-auth-status.json
  examples/auth/dev-identity-simulation-request.json
  examples/auth/role-filtered-viewer-console.json
  examples/auth/role-filtered-operator-console.json
  examples/auth/local-auth-audit-request.json
  operator-console-static/demo-data/local-auth-status.json
  operator-console-static/demo-data/role-filtered-view-model.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || { echo "missing local auth doc: $file" >&2; exit 1; }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || { echo "missing local auth example: $file" >&2; exit 1; }
done

grep -q "0085-local-auth-contract-dev-identity-simulation.md" docs/adr/README.md || {
  echo "ADR 0085 is not indexed" >&2
  exit 1
}

for line in \
  "AION_PRODUCTION_AUTH_ENABLED=false" \
  "AION_AUTH_CREDENTIALS_ENABLED=false" \
  "AION_AUTH_SESSIONS_ENABLED=false" \
  "AION_EXTERNAL_IDENTITY_PROVIDER_ENABLED=false" \
  "AION_LOCAL_AUTH_WRITE_ACTIONS_ENABLED=false"; do
  grep -qx "$line" .env.example || {
    echo ".env.example missing disabled auth flag: $line" >&2
    exit 1
  }
done

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*login' services/brain-api/src/aion_brain/api; then
  echo "login endpoint string found in API routes" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations | rg -n '094|local.auth|local_auth|auth'; then
  echo "AION-094 must not add a migration" >&2
  exit 1
fi

if git ls-files --others --exclude-standard | rg -n '^infra/postgres/migrations/.*(094|local.auth|local_auth|auth)'; then
  echo "AION-094 must not add an untracked migration" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- . | rg -n '(^|/)(package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb)$'; then
  echo "frontend dependency file changed" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
aion_104_review_examples = {
    "auth-safety-evidence-pack.json",
    "auth-runtime-disabled-proof.json",
    "auth-traceability-matrix.json",
    "auth-no-go-regression-result.json",
}
for path in sorted((root / "examples" / "auth").glob("*.json")):
    if path.name in aion_104_review_examples:
        continue
    if path.name.startswith("local-session") or path.name == "role-aware-session-context.json":
        continue
    if "authorization" in path.name:
        continue
    if "auth-runtime" in path.name or "mock-claims" in path.name:
        continue
    if "production-auth" in path.name or path.name == "disabled-auth-prototype-plan.json":
        continue
    payload = json.loads(path.read_text())
    serialized = json.dumps(payload, sort_keys=True).lower()
    blocked = (
        "password",
        "token",
        "secret",
        "api_key",
        "private_key",
        "authorization",
        "bearer",
        "sk-",
        "ghp_",
        "xoxb-",
    )
    if any(item in serialized for item in blocked):
        raise SystemExit(f"auth example contains blocked material: {path}")

for path in sorted((root / "operator-console-static" / "demo-data").glob("*auth*.json")):
    payload = json.loads(path.read_text())
    if payload.get("read_only") is not True:
        raise SystemExit(f"static auth demo must be read_only: {path}")
    if payload.get("redaction_applied") is not True:
        raise SystemExit(f"static auth demo must be redacted: {path}")

print("Local auth examples valid")
PY

if rg -n 'httpx|requests|openai|oauth|saml|oidc|ldap|webauthn|passkey' \
  services/brain-api/src/aion_brain/local_auth \
  services/brain-api/src/aion_brain/api/local_auth.py; then
  echo "external identity or call dependency found in local auth runtime" >&2
  exit 1
fi

echo "Local auth check PASS"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "services/brain-api/src/aion_brain/local_auth/permission_matrix.py"
  "services/brain-api/src/aion_brain/local_auth/console_filter.py"
  "services/brain-api/src/aion_brain/local_auth/access_audit.py"
  "docs/auth/role-permission-proof-matrix.md"
  "docs/auth/console-view-access-filtering.md"
  "docs/auth/role-aware-action-descriptors.md"
  "docs/auth/role-access-audit.md"
  "docs/operator-console/role-aware-console-preview.md"
  "docs/adr/0087-role-aware-console-view-filtering.md"
  "examples/auth/role-permission-proof-matrix.json"
  "examples/auth/viewer-access-filter-result.json"
  "examples/auth/operator-access-filter-result.json"
  "examples/auth/reviewer-access-filter-result.json"
  "examples/auth/auditor-access-filter-result.json"
  "examples/auth/admin-access-filter-result.json"
  "examples/auth/role-access-audit-result.json"
  "operator-console-static/demo-data/role-viewer-dashboard.json"
  "operator-console-static/demo-data/role-operator-dashboard.json"
  "operator-console-static/demo-data/role-reviewer-dashboard.json"
  "operator-console-static/demo-data/role-auditor-dashboard.json"
  "operator-console-static/demo-data/role-admin-dashboard.json"
  "operator-console-static/demo-data/role-access-matrix.json"
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing role filter artifact: $file" >&2
    exit 1
  }
done

grep -q "0087-role-aware-console-view-filtering.md" docs/adr/README.md || {
  echo "ADR 0087 is not indexed" >&2
  exit 1
}

grep -q "role-switcher" operator-console-static/index.html || {
  echo "static role switcher missing" >&2
  exit 1
}

for role in viewer operator reviewer admin auditor; do
  grep -q "data-role=\"$role\"" operator-console-static/index.html || {
    echo "static role switcher missing role: $role" >&2
    exit 1
  }
done

if grep -q "data-role=\"system_service\"" operator-console-static/index.html; then
  echo "system_service must not be offered in static role switcher" >&2
  exit 1
fi

python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

paths = sorted(
    {
        *Path("examples/auth").glob("*role*.json"),
        *Path("examples/auth").glob("*access*.json"),
        *Path("operator-console-static/demo-data").glob("role-*.json"),
    }
)
blocked_key_parts = {
    "api_key",
    "apikey",
    "authorization",
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
    "execute_allowed",
    "activation_allowed",
    "external_calls_allowed",
}
proof_files = {
    "role-permission-proof-matrix.json",
    "viewer-access-filter-result.json",
    "operator-access-filter-result.json",
    "reviewer-access-filter-result.json",
    "auditor-access-filter-result.json",
    "admin-access-filter-result.json",
    "role-access-audit-result.json",
}
aion_096_static_role_files = {
    "role-viewer-dashboard.json",
    "role-operator-dashboard.json",
    "role-reviewer-dashboard.json",
    "role-auditor-dashboard.json",
    "role-admin-dashboard.json",
    "role-access-matrix.json",
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
    is_static_role_demo = path.parent.name == "demo-data" and path.name in aion_096_static_role_files
    if is_static_role_demo and payload.get("read_only") is not True:
        raise SystemExit(f"role static demo must be read_only: {path}")
    if is_static_role_demo and payload.get("redaction_applied") is not True:
        raise SystemExit(f"role static demo must be redacted: {path}")
    if path.name in proof_files and payload.get("forbidden_actions_visible") is not True:
        raise SystemExit(f"forbidden actions must remain visible: {path}")
    if is_static_role_demo and payload.get("forbidden_actions_visible") is not True:
        raise SystemExit(f"static role demo must keep forbidden actions visible: {path}")

matrix = json.loads(Path("operator-console-static/demo-data/role-access-matrix.json").read_text())
if "system_service" in matrix.get("static_console_roles", []):
    raise SystemExit("system_service must not appear in static_console_roles")
if matrix.get("system_service_exposed_in_static_console") is not False:
    raise SystemExit("system_service exposure flag must be false")
PY

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(login|logout)' services/brain-api/src/aion_brain/api; then
  echo "Unexpected login/logout API route found" >&2
  exit 1
fi

if rg -n '<form|type="password"|localStorage|sessionStorage|name="token"|name="cookie"' operator-console-static; then
  echo "Unexpected form, sensitive input, or browser storage found" >&2
  exit 1
fi

test -z "$(find infra/postgres/migrations -type f -name '*096*' -print)"

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations | rg -n '096|role.filter|role_filter|role.matrix|role_matrix'; then
  echo "AION-096 must not add a migration" >&2
  exit 1
fi

if git ls-files --others --exclude-standard | rg -n '^infra/postgres/migrations/.*(096|role.filter|role_filter|role.matrix|role_matrix)'; then
  echo "AION-096 must not add an untracked migration" >&2
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

if find . -maxdepth 1 -type f \( -name 'vite.config.*' -o -name 'next.config.*' -o -name 'tailwind.config.*' -o -name 'webpack.config.*' \) | grep -q .; then
  echo "Unexpected frontend config file found" >&2
  exit 1
fi

install_patterns="npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install"
if rg -n "$install_patterns" operator-console-static docs/auth docs/operator-console/role-aware-console-preview.md; then
  echo "Unexpected package install instruction found" >&2
  exit 1
fi

if rg -n 'httpx|requests|openai|oauth|saml|oidc|ldap|webauthn|passkey' \
  services/brain-api/src/aion_brain/local_auth/permission_matrix.py \
  services/brain-api/src/aion_brain/local_auth/console_filter.py \
  services/brain-api/src/aion_brain/local_auth/access_audit.py; then
  echo "External identity or call dependency found in role filtering runtime" >&2
  exit 1
fi

echo "Role filter check PASS"

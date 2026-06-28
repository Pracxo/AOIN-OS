#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/auth/local-auth-design.md
  docs/auth/local-auth-contract.md
  docs/auth/dev-identity-simulation.md
  docs/auth/role-aware-console-filtering.md
  docs/auth/local-auth-audit.md
  docs/auth/local-auth-runtime-boundaries.md
  docs/auth/operator-identity-model.md
  docs/auth/operator-session-boundary.md
  docs/auth/operator-role-model.md
  docs/auth/operator-access-matrix.md
  docs/auth/operator-auth-threat-model.md
  docs/auth/production-auth-prerequisites.md
  docs/auth/auth-no-go-conditions.md
  docs/auth/future-auth-implementation-plan.md
  docs/adr/0084-local-auth-design-for-operator-console.md
  docs/adr/0085-local-auth-contract-dev-identity-simulation.md
)

required_examples=(
  examples/auth/local-operator-identity.json
  examples/auth/operator-role-matrix.json
  examples/auth/session-boundary-example.json
  examples/auth/console-access-policy-example.json
  examples/auth/local-auth-status.json
  examples/auth/dev-identity-simulation-request.json
  examples/auth/role-filtered-viewer-console.json
  examples/auth/role-filtered-operator-console.json
  examples/auth/local-auth-audit-request.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || { echo "missing auth doc: $file" >&2; exit 1; }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || { echo "missing auth example: $file" >&2; exit 1; }
done

grep -q "0084-local-auth-design-for-operator-console.md" docs/adr/README.md || {
  echo "ADR 0084 is not indexed" >&2
  exit 1
}

grep -q "0085-local-auth-contract-dev-identity-simulation.md" docs/adr/README.md || {
  echo "ADR 0085 is not indexed" >&2
  exit 1
}

grep -q "docs/auth/local-auth-design.md" README.md || {
  echo "README missing local auth design link" >&2
  exit 1
}

grep -q "Do not implement production auth" AGENTS.md || {
  echo "AGENTS missing auth guardrails" >&2
  exit 1
}

grep -R -q "no production auth is implemented" docs/auth README.md || {
  echo "docs must state no production auth is implemented" >&2
  exit 1
}

grep -R -q "No credentials are stored" docs/auth README.md || {
  echo "docs must state no credentials are stored" >&2
  exit 1
}

grep -R -q "No login endpoint is added" docs/auth README.md || {
  echo "docs must state no login endpoint is added" >&2
  exit 1
}

grep -R -q "No external identity provider is integrated" docs/auth README.md || {
  echo "docs must state no external identity provider is integrated" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
for path in sorted((root / "examples" / "auth").glob("*.json")):
    if path.name.startswith("local-session") or path.name == "role-aware-session-context.json":
        continue
    payload = json.loads(path.read_text())
    serialized = json.dumps(payload, sort_keys=True).lower()
    blocked = (
        "token",
        "password",
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

changed = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
untracked = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()

allowed_auth_paths = {
    "docs/auth/local-auth-design.md",
    "docs/auth/local-auth-contract.md",
    "docs/auth/dev-identity-simulation.md",
    "docs/auth/role-aware-console-filtering.md",
    "docs/auth/local-auth-audit.md",
    "docs/auth/local-auth-runtime-boundaries.md",
    "docs/auth/operator-identity-model.md",
    "docs/auth/operator-session-boundary.md",
    "docs/auth/operator-role-model.md",
    "docs/auth/operator-access-matrix.md",
    "docs/auth/operator-auth-threat-model.md",
    "docs/auth/production-auth-prerequisites.md",
    "docs/auth/auth-no-go-conditions.md",
    "docs/auth/future-auth-implementation-plan.md",
    "docs/adr/0084-local-auth-design-for-operator-console.md",
    "docs/adr/0085-local-auth-contract-dev-identity-simulation.md",
    "examples/auth/local-operator-identity.json",
    "examples/auth/operator-role-matrix.json",
    "examples/auth/session-boundary-example.json",
    "examples/auth/console-access-policy-example.json",
    "examples/auth/local-auth-status.json",
    "examples/auth/dev-identity-simulation-request.json",
    "examples/auth/role-filtered-viewer-console.json",
    "examples/auth/role-filtered-operator-console.json",
    "examples/auth/local-auth-audit-request.json",
    "operator-console-static/demo-data/local-auth-status.json",
    "operator-console-static/demo-data/role-filtered-view-model.json",
    "scripts/auth-design-check.sh",
    "scripts/local-auth-check.sh",
    "services/brain-api/src/aion_brain/contracts/local_auth.py",
    "services/brain-api/src/aion_brain/local_auth/__init__.py",
    "services/brain-api/src/aion_brain/local_auth/redaction.py",
    "services/brain-api/src/aion_brain/local_auth/roles.py",
    "services/brain-api/src/aion_brain/local_auth/identity.py",
    "services/brain-api/src/aion_brain/local_auth/context.py",
    "services/brain-api/src/aion_brain/local_auth/simulator.py",
    "services/brain-api/src/aion_brain/local_auth/access_matrix.py",
    "services/brain-api/src/aion_brain/local_auth/audit.py",
    "services/brain-api/src/aion_brain/local_auth/query.py",
    "services/brain-api/src/aion_brain/api/local_auth.py",
    "services/brain-api/src/aion_brain/identity/dev_auth.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/local_auth.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/local_auth.py",
    "packages/aion-sdk-python/tests/test_local_auth_resource.py",
    "packages/aion-sdk-python/tests/test_cli_local_auth.py",
    "services/brain-api/tests/test_auth_design_docs.py",
    "services/brain-api/tests/test_local_auth_contracts.py",
    "services/brain-api/tests/test_local_auth_redaction.py",
    "services/brain-api/tests/test_local_auth_roles.py",
    "services/brain-api/tests/test_local_auth_identity.py",
    "services/brain-api/tests/test_local_auth_context.py",
    "services/brain-api/tests/test_local_auth_simulator.py",
    "services/brain-api/tests/test_local_auth_access_matrix.py",
    "services/brain-api/tests/test_local_auth_audit.py",
    "services/brain-api/tests/test_local_auth_api.py",
    "services/brain-api/tests/test_operator_console_role_filtering.py",
    "services/brain-api/tests/test_kernel_local_auth_wiring.py",
    "services/brain-api/tests/test_visual_telemetry_local_auth.py",
    "docs/auth/local-session-prototype.md",
    "docs/auth/local-session-boundary.md",
    "docs/auth/session-safety-audit.md",
    "docs/auth/session-preview-console-panel.md",
    "docs/auth/future-session-implementation-plan.md",
    "docs/adr/0086-read-only-local-session-prototype.md",
    "examples/auth/local-session-preview-request.json",
    "examples/auth/local-session-status.json",
    "examples/auth/local-session-boundary-audit-request.json",
    "examples/auth/role-aware-session-context.json",
    "operator-console-static/demo-data/local-session-status.json",
    "operator-console-static/demo-data/local-session-preview.json",
    "scripts/local-session-check.sh",
    "services/brain-api/src/aion_brain/contracts/local_session.py",
    "services/brain-api/src/aion_brain/local_session/__init__.py",
    "services/brain-api/src/aion_brain/local_session/redaction.py",
    "services/brain-api/src/aion_brain/local_session/preview.py",
    "services/brain-api/src/aion_brain/local_session/context.py",
    "services/brain-api/src/aion_brain/local_session/boundary.py",
    "services/brain-api/src/aion_brain/local_session/audit.py",
    "services/brain-api/src/aion_brain/local_session/query.py",
    "services/brain-api/src/aion_brain/api/local_session.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/local_session.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/local_session.py",
    "packages/aion-sdk-python/tests/test_local_session_resource.py",
    "packages/aion-sdk-python/tests/test_cli_local_session.py",
    "services/brain-api/tests/test_local_session_contracts.py",
    "services/brain-api/tests/test_local_session_redaction.py",
    "services/brain-api/tests/test_local_session_preview.py",
    "services/brain-api/tests/test_local_session_context.py",
    "services/brain-api/tests/test_local_session_boundary.py",
    "services/brain-api/tests/test_local_session_audit.py",
    "services/brain-api/tests/test_local_session_api.py",
    "services/brain-api/tests/test_operator_console_session_preview.py",
    "services/brain-api/tests/test_kernel_local_session_wiring.py",
    "services/brain-api/tests/test_visual_telemetry_local_session.py",
}

blocked_package_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
blocked_build_prefixes = (
    "vite.config.",
    "next.config.",
    "tailwind.config.",
    "webpack.config.",
)

for name in [*changed, *untracked]:
    path = Path(name)
    basename = path.name
    if basename in blocked_package_names or any(
        basename.startswith(prefix) for prefix in blocked_build_prefixes
    ):
        raise SystemExit(f"frontend package or build file changed: {name}")
    if name.startswith("infra/postgres/migrations/"):
        raise SystemExit(f"AION-093 must not add a migration: {name}")
    if name.startswith("services/brain-api/src/aion_brain/api/auth"):
        raise SystemExit(f"AION-093 must not add an auth API route: {name}")
    if "auth" in name.lower() and name not in allowed_auth_paths:
        raise SystemExit(f"unexpected auth runtime or artifact path: {name}")

print("Auth examples valid and runtime boundaries clean")
PY

echo "Auth design check PASS"

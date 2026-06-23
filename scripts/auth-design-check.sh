#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/auth/local-auth-design.md
  docs/auth/operator-identity-model.md
  docs/auth/operator-session-boundary.md
  docs/auth/operator-role-model.md
  docs/auth/operator-access-matrix.md
  docs/auth/operator-auth-threat-model.md
  docs/auth/production-auth-prerequisites.md
  docs/auth/auth-no-go-conditions.md
  docs/auth/future-auth-implementation-plan.md
  docs/adr/0084-local-auth-design-for-operator-console.md
)

required_examples=(
  examples/auth/local-operator-identity.json
  examples/auth/operator-role-matrix.json
  examples/auth/session-boundary-example.json
  examples/auth/console-access-policy-example.json
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
    "docs/auth/operator-identity-model.md",
    "docs/auth/operator-session-boundary.md",
    "docs/auth/operator-role-model.md",
    "docs/auth/operator-access-matrix.md",
    "docs/auth/operator-auth-threat-model.md",
    "docs/auth/production-auth-prerequisites.md",
    "docs/auth/auth-no-go-conditions.md",
    "docs/auth/future-auth-implementation-plan.md",
    "docs/adr/0084-local-auth-design-for-operator-console.md",
    "examples/auth/local-operator-identity.json",
    "examples/auth/operator-role-matrix.json",
    "examples/auth/session-boundary-example.json",
    "examples/auth/console-access-policy-example.json",
    "scripts/auth-design-check.sh",
    "services/brain-api/tests/test_auth_design_docs.py",
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

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/auth/local-auth-prototype-review.md
  docs/auth/auth-safety-evidence-pack.md
  docs/auth/auth-runtime-disabled-proof.md
  docs/auth/auth-traceability-matrix.md
  docs/auth/auth-no-go-regression-pack.md
  docs/auth/pre-implementation-auth-gate.md
  docs/adr/0095-local-auth-prototype-review-gate.md
)

required_examples=(
  examples/auth/auth-safety-evidence-pack.json
  examples/auth/auth-runtime-disabled-proof.json
  examples/auth/auth-traceability-matrix.json
  examples/auth/auth-no-go-regression-result.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || {
    echo "missing auth prototype review doc: $file" >&2
    exit 1
  }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing auth prototype review example: $file" >&2
    exit 1
  }
done

grep -q "0095-local-auth-prototype-review-gate.md" docs/adr/README.md || {
  echo "ADR 0095 is not indexed" >&2
  exit 1
}

./scripts/auth-design-check.sh
./scripts/local-auth-check.sh
./scripts/local-session-check.sh
./scripts/role-filter-check.sh
./scripts/action-authorization-check.sh
./scripts/production-auth-architecture-check.sh
./scripts/auth-runtime-check.sh
./scripts/static-console-safety-check.sh
./scripts/ui-release-gate.sh
./scripts/auth-no-go-regression.sh

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

if find . -maxdepth 2 -type f \( \
  -name 'vite.config.*' -o \
  -name 'next.config.*' -o \
  -name 'tailwind.config.*' -o \
  -name 'webpack.config.*' \
\) | rg -n '.'; then
  echo "frontend build config is not allowed" >&2
  exit 1
fi

if rg -n 'https?://' "${required_docs[@]}" "${required_examples[@]}"; then
  echo "external URL found in auth prototype review artifacts" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add|pip[[:space:]]+install' \
  "${required_docs[@]}" "${required_examples[@]}"; then
  echo "package install instruction found in auth prototype review artifacts" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
example_dir = root / "examples/auth"

evidence = json.loads((example_dir / "auth-safety-evidence-pack.json").read_text())
if evidence.get("status") != "passed":
    raise SystemExit("auth safety evidence pack status must be passed")
required_areas = {
    "local auth design",
    "local auth contract",
    "dev identity simulation",
    "local session preview",
    "role filtering",
    "dry-run action authorization",
    "production auth architecture",
    "disabled auth runtime",
    "static console auth panels",
    "docs audit",
    "boundary checks",
}
areas = {row.get("area") for row in evidence.get("evidence", [])}
missing = required_areas - areas
if missing:
    raise SystemExit(f"auth evidence pack missing areas: {sorted(missing)}")
for row in evidence["evidence"]:
    if row.get("expected_status") != "passed":
        raise SystemExit(f"auth evidence row must be passed: {row}")
    if row.get("release_blocker") is not True:
        raise SystemExit(f"auth evidence row must be release blocker: {row}")
    if not str(row.get("script", "")).startswith("./scripts/"):
        raise SystemExit(f"auth evidence row must use local script: {row}")

proof = json.loads((example_dir / "auth-runtime-disabled-proof.json").read_text())
for key in (
    "production_auth_enabled",
    "auth_runtime_enabled",
    "credentials_enabled",
    "token_issuance_enabled",
    "cookie_issuance_enabled",
    "session_persistence_enabled",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "external_identity_provider_enabled",
    "provider_sdk_present",
    "package_files_present",
    "migration_present",
    "token_present",
    "cookie_present",
    "session_persisted",
    "protected_material_present",
    "write_allowed",
    "execute_allowed",
    "activation_allowed",
    "external_calls_allowed",
):
    if proof.get(key) is not False:
        raise SystemExit(f"{key} must be false in disabled proof")

trace = json.loads((example_dir / "auth-traceability-matrix.json").read_text())
surfaces = {row.get("surface") for row in trace.get("rows", [])}
required_surfaces = {
    "role",
    "session",
    "action authorization",
    "policy",
    "static console",
    "audit",
    "forbidden action",
}
missing_surfaces = required_surfaces - surfaces
if missing_surfaces:
    raise SystemExit(f"auth traceability missing surfaces: {sorted(missing_surfaces)}")
for row in trace["rows"]:
    for key in ("write_allowed", "execute_allowed", "activation_allowed", "external_calls_allowed"):
        if row.get(key) is not False:
            raise SystemExit(f"{key} must be false in traceability row: {row}")

no_go = json.loads((example_dir / "auth-no-go-regression-result.json").read_text())
if no_go.get("status") != "passed":
    raise SystemExit("auth no-go regression result must be passed")
if any(item.get("expected_status") != "passed" for item in no_go.get("checks", [])):
    raise SystemExit("all auth no-go checks must be passed")

serialized = json.dumps([evidence, proof, trace, no_go], sort_keys=True).lower()
secret_markers = (
    "sk-",
    "ghp_",
    "xoxb-",
    "-----begin private key-----",
    "bearer ",
    "basic ",
    "api_key",
    "private_key",
)
for marker in secret_markers:
    if marker in serialized:
        raise SystemExit(f"secret-like marker found in AION-104 auth examples: {marker}")

print("Auth prototype review JSON checks PASS")
PY

echo "Auth prototype review result:"
echo "- local_auth_contract: passed"
echo "- local_session_preview: passed"
echo "- role_filtering: passed"
echo "- action_authorization: passed"
echo "- disabled_auth_runtime: passed"
echo "- auth_no_go_regression: passed"
echo "Auth prototype review PASS"

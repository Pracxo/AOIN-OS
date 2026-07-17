#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local merge_base
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        if [[ -n "$merge_base" ]]; then
          echo "$merge_base"
          return 0
        fi
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      if [[ -n "$merge_base" ]]; then
        echo "$merge_base"
        return 0
      fi
    fi
  done
  if git_ref_exists HEAD~1; then
    echo "HEAD~1"
    return 0
  fi
  return 1
}

changed_files() {
  local base
  {
    if base="$(comparison_base)"; then
      git diff --name-only --diff-filter=ACMRT "$base" HEAD --
    fi
    git diff --name-only --diff-filter=ACMRT HEAD --
    git diff --cached --name-only --diff-filter=ACMRT --
    git ls-files --others --exclude-standard --
  } | sort -u
}

changed_file_list="$(mktemp)"
trap 'rm -f "$changed_file_list"' EXIT
changed_files > "$changed_file_list"

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  case "$file" in
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb|\
    uv.lock|poetry.lock|Pipfile|Pipfile.lock|requirements.txt|requirements/*.txt)
      echo "new dependency manifests and lockfiles are forbidden for AION-162: $file" >&2
      exit 1
      ;;
    *migrations/*|migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-162: $file" >&2
      exit 1
      ;;
    packages/aion-sdk-python/src/*)
      echo "SDK runtime source changes are forbidden for AION-162: $file" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/api/*)
      echo "API runtime routes are forbidden for AION-162: $file" >&2
      exit 1
      ;;
  esac
done < "$changed_file_list"

python3 - "$ROOT_DIR" "$(comparison_base || true)" <<'PY'
from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

root = Path(sys.argv[1])
base = sys.argv[2]
current = tomllib.loads((root / "services/brain-api/pyproject.toml").read_text())
current_deps = set(current["project"]["dependencies"])
if "cryptography>=49.0.0,<50.0.0" not in current_deps:
    raise SystemExit("authorized cryptography dependency is missing")
if base:
    base_resolved = subprocess.run(
        ["git", "rev-parse", base],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    head_resolved = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        base_resolved.returncode == 0
        and head_resolved.returncode == 0
        and base_resolved.stdout.strip() == head_resolved.stdout.strip()
    ):
        raise SystemExit(0)
    proc = subprocess.run(
        ["git", "show", f"{base}:services/brain-api/pyproject.toml"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        base_deps = set(tomllib.loads(proc.stdout)["project"]["dependencies"])
        added = current_deps - base_deps
        removed = base_deps - current_deps
        if added != {"cryptography>=49.0.0,<50.0.0"}:
            raise SystemExit(f"unexpected dependency additions: {sorted(added)}")
        if removed:
            raise SystemExit(f"unexpected dependency removals: {sorted(removed)}")
PY

test ! -e services/brain-api/src/aion_brain/api/identity_assertion.py || {
  echo "identity assertion API route is forbidden" >&2
  exit 1
}
test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "production auth API route is forbidden" >&2
  exit 1
}
test ! -e services/brain-api/src/aion_brain/api/request_identity.py || {
  echo "request identity API route is forbidden" >&2
  exit 1
}
test ! -e services/brain-api/src/aion_brain/api/actor_context.py || {
  echo "actor context API route is forbidden" >&2
  exit 1
}

new_assertion_sources=(
  services/brain-api/src/aion_brain/contracts/identity_assertion.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py
  services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py
  services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py
)

if rg -n 'Ed25519PrivateKey|private_bytes\(|load_pem_private_key|BEGIN PRIVATE KEY|BEGIN OPENSSH PRIVATE KEY|signing_key|private_key_seed|private_key_base64' services/brain-api/src/aion_brain; then
  echo "runtime private-key material or API detected" >&2
  exit 1
fi

if rg -n 'private_bytes\(' services/brain-api/tests; then
  echo "private-key serialization is forbidden in tests" >&2
  exit 1
fi

if rg -n 'IdentityAssertionSigner|sign_identity_assertion|issue_identity_assertion|mint_identity_assertion' "${new_assertion_sources[@]}"; then
  echo "runtime signer implementation is forbidden" >&2
  exit 1
fi

if rg -n 'from +fastapi +import|APIRouter|Request\(|request\.(headers|cookies|body|query_params)|scope\["headers"\]|scope\['\''headers'\''\]' "${new_assertion_sources[@]}"; then
  echo "HTTP parsing or route surface is forbidden in identity assertion source" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(AsyncClient|Client|get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.(socket|create_connection)|dns\.resolver|jwks_network_fetch_enabled\s*[:=]\s*true|provider_discovery_enabled\s*[:=]\s*true|replay_cache|redis\.(Redis|asyncio)|session_storage|verified_claims_persisted\s*[:=]\s*true' "${new_assertion_sources[@]}"; then
  echo "network, provider, replay, session, or persistence path is forbidden" >&2
  exit 1
fi

if [[ -s "$changed_file_list" ]] && rg -n '\b(request_authenticated|actor_context_applied|request_identity_context_applied|runtime_effect|runtime_integration_allowed|production_auth_runtime_enabled|identity_verification_enabled|authenticated_requests_enabled|identity_assertion_header_parsing_enabled|authorization_header_parsing_enabled|cookie_parsing_enabled|identity_assertion_middleware_registered|external_identity_provider_enabled|jwks_network_fetch_enabled|provider_discovery_enabled|external_calls_enabled|identity_assertion_endpoint_enabled|runtime_api_routes_added|openapi_security_scheme_added|sdk_runtime_resource_added|cli_runtime_command_added|new_package_manifest_added|lockfiles_added|migrations_added|connector_runtime_enabled|operator_write_execution_enabled|module_activation_enabled|sandbox_execution_enabled|v02_tag_created|v02_release_created)\s*[:=]\s*true\b' $(cat "$changed_file_list"); then
  echo "runtime, route, package, execution, tag, or release flag was enabled" >&2
  exit 1
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2|aion-v0\.2\.0)$'; then
  echo "v0.2 tag must not exist for AION-162" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-162" >&2
  exit 1
fi

echo "production auth offline identity assertion no-go PASS"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

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

base_ref="$(comparison_base || true)"
changed_file_list="$(mktemp)"
trap 'rm -f "$changed_file_list"' EXIT

if [[ -n "$base_ref" ]]; then
  {
    git diff --name-only --diff-filter=ACMRT "$base_ref" HEAD --
    git diff --name-only --diff-filter=ACMRT HEAD --
    git diff --cached --name-only --diff-filter=ACMRT --
    git ls-files --others --exclude-standard --
  } | sort -u > "$changed_file_list"
else
  {
    git diff --name-only --diff-filter=ACMRT HEAD --
    git diff --cached --name-only --diff-filter=ACMRT --
    git ls-files --others --exclude-standard --
  } | sort -u > "$changed_file_list"
fi

test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "new production-auth API router is forbidden" >&2
  exit 1
}

if rg -n '(^|/)services/brain-api/src/aion_brain/api/production_auth\.py$' "$changed_file_list"; then
  echo "new production-auth API router is forbidden" >&2
  exit 1
fi

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  case "$file" in
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      echo "package files and lockfiles are forbidden for AION-152: $file" >&2
      exit 1
      ;;
    packages/aion-sdk-python/src/*)
      echo "SDK runtime resources are forbidden for AION-152: $file" >&2
      exit 1
      ;;
    *migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-152: $file" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/production_auth/*|\
    services/brain-api/src/aion_brain/contracts/production_auth.py|\
    services/brain-api/src/aion_brain/config.py|\
    services/brain-api/src/aion_brain/kernel/container.py|\
    services/brain-api/src/aion_brain/kernel/diagnostics.py)
      echo "production-auth source, config, or kernel changes are forbidden for AION-152: $file" >&2
      exit 1
      ;;
  esac
done < "$changed_file_list"

changed_existing_files="$(mktemp)"
trap 'rm -f "$changed_file_list" "$changed_existing_files"' EXIT
while IFS= read -r file; do
  [[ -f "$file" ]] || continue
  if aion151_is_scoped_authorization_path "$file"; then
    continue
  fi
  case "$file" in
    # Exact self-scan exemptions keep authorized validation-script edits from
    # failing on their own guard text while continuing to scan the rest of scripts/.
    scripts/production-auth-core-check.sh|scripts/production-auth-core-no-go-regression.sh)
      continue
      ;;
  esac
  printf '%s\n' "$file" >> "$changed_existing_files"
done < "$changed_file_list"

if [[ -s "$changed_existing_files" ]]; then
  if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(production-auth|auth/production|login|logout|callback|oauth|oidc|saml|token|session|credentials)' $(cat "$changed_existing_files"); then
    echo "runtime auth route surface found in changed files" >&2
    exit 1
  fi

  if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' $(cat "$changed_existing_files"); then
    echo "network or external call path found in changed files" >&2
    exit 1
  fi

  if rg -n '\b(oauth|oidc|saml|authlib|okta|auth0|webauthn|passkey|python-jose|jwt)\b.*\b(enabled|client|provider|runtime|sdk)\b' $(cat "$changed_existing_files"); then
    echo "provider runtime or SDK surface found in changed files" >&2
    exit 1
  fi

  if rg -n '\b(runtime_implementation_approved|production_auth_runtime_enabled|runtime_enablement_guard_release_approved|runtime_enablement_guard_final_lock_release_approved|runtime_enablement_master_lock_release_approved|login_endpoint_enabled|logout_endpoint_enabled|callback_endpoint_enabled|credential_storage_enabled|password_storage_enabled|token_issuance_enabled|token_storage_enabled|session_creation_enabled|session_storage_enabled|cookie_issuance_enabled|cookie_session_persistence_enabled|external_identity_provider_enabled|oauth_runtime_enabled|oidc_runtime_enabled|saml_runtime_enabled|external_calls_enabled|network_client_enabled|provider_sdk_enabled|operator_write_execution_enabled|connector_runtime_enabled|module_activation_enabled|sandbox_execution_enabled|package_files_added|lockfiles_added|migrations_added|runtime_api_routes_added|v02_tag_created|v02_release_created)\s*[:=]\s*true\b' $(cat "$changed_existing_files"); then
    echo "runtime, route, storage, provider, package, migration, execution, tag, or release flag was enabled" >&2
    exit 1
  fi

  if rg -n '\bauthorization_scope\s*[:=]\s*"?[^"\n]*"?' $(cat "$changed_existing_files") | rg -v 'disabled-production-auth-core'; then
    echo "authorization scope expansion found" >&2
    exit 1
  fi
fi

python3 scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode no-go

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-152" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-152" >&2
  exit 1
fi

echo "production auth core no-go PASS"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
"$PYTHON_BIN" scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode no-go

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
      git diff --name-only --diff-filter=ACMRT "$base" HEAD -- "$@"
    fi
    git diff --name-only --diff-filter=ACMRT HEAD -- "$@"
    git diff --cached --name-only --diff-filter=ACMRT -- "$@"
    git ls-files --others --exclude-standard -- "$@"
  } | sort -u
}

changed_file_list="$(mktemp)"
scan_file_list="$(mktemp)"
trap 'rm -f "$changed_file_list" "$scan_file_list"' EXIT
changed_files > "$changed_file_list"

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  case "$file" in
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      echo "package files and lockfiles are forbidden for AION-159: $file" >&2
      exit 1
      ;;
    *migrations/*|migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-159: $file" >&2
      exit 1
      ;;
  esac

  if aion160_is_scoped_actor_context_trust_boundary_remediation_path "$file"; then
    continue
  fi

  case "$file" in
    services/brain-api/src/aion_brain/identity/dev_auth.py|\
    services/brain-api/src/aion_brain/contracts/scopes.py|\
    services/brain-api/src/aion_brain/contracts/request_identity.py|\
    services/brain-api/src/aion_brain/production_auth/*|\
    services/brain-api/src/aion_brain/config.py|\
    services/brain-api/src/aion_brain/kernel/*|\
    services/brain-api/src/aion_brain/api_support/*|\
    services/brain-api/src/aion_brain/api/*|\
    packages/aion-sdk-python/src/*)
      echo "protected implementation source changes are forbidden for AION-159: $file" >&2
      exit 1
      ;;
  esac

  if [[ -f "$file" ]] && ! aion159_is_scoped_actor_context_trust_boundary_authorization_path "$file"; then
    printf '%s\n' "$file" >> "$scan_file_list"
  fi
done < "$changed_file_list"

test ! -e services/brain-api/src/aion_brain/api/production_auth.py || {
  echo "new production-auth API router is forbidden" >&2
  exit 1
}

test ! -e services/brain-api/src/aion_brain/api/request_identity.py || {
  echo "new request-identity API router is forbidden" >&2
  exit 1
}

if [[ -s "$scan_file_list" ]]; then
  if rg -n '\b(runtime_implementation_approved|production_auth_runtime_enabled|identity_verification_enabled|authenticated_requests_enabled|authenticated_actor_context_enabled|non_development_identity_header_trust_enabled|production_identity_header_trust_approved|production_actor_header_trust_enabled|production_role_header_trust_enabled|production_permission_header_trust_enabled|production_security_scope_header_trust_enabled|authorization_header_parsing_approved|cookie_parsing_approved|credential_verification_approved|password_verification_approved|credential_storage_approved|password_storage_approved|token_parsing_approved|token_issuance_approved|token_storage_approved|token_refresh_approved|session_creation_approved|session_storage_approved|cookie_issuance_approved|cookie_session_persistence_approved|protected_material_handling_approved|external_identity_provider_approved|oauth_runtime_approved|oidc_runtime_approved|saml_runtime_approved|external_calls_approved|network_client_approved|provider_sdk_approved|login_endpoint_approved|logout_endpoint_approved|callback_endpoint_approved|token_endpoint_approved|session_endpoint_approved|credential_endpoint_approved|openapi_security_scheme_added|package_files_added|lockfiles_added|migrations_added|runtime_api_routes_added|api_runtime_execution_route_added|sdk_runtime_resource_added|cli_runtime_command_added|operator_write_execution_approved|connector_implementation_approved|connector_runtime_enabled|module_activation_approved|sandbox_execution_approved|v02_tag_created|v02_release_created|v02_release_approved)\s*[:=]\s*true\b' $(cat "$scan_file_list"); then
    echo "runtime, production header trust, parsing, protected-material, provider, package, migration, route, release, or execution approval was enabled" >&2
    exit 1
  fi

  if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(production-auth|request-identity|auth/production|login|logout|callback|oauth|oidc|saml|token|session|credential)' $(cat "$scan_file_list"); then
    echo "runtime auth route surface found in changed files" >&2
    exit 1
  fi

  if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' $(cat "$scan_file_list"); then
    echo "network or external call path found in changed files" >&2
    exit 1
  fi
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-159" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-159" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 actor context trust boundary authorization no-go result:
- exactly one active authorization tuple: AION-159-PA-0005
- AION-157 historical consumed record: present
- duplicate active authorization tuple: absent
- unknown approved authorization: absent
- historical reactivation: absent
- wrong parent, task, candidate, workstream, or scope: absent
- partial remediation permission set: absent
- extra approved permission: absent
- missing prohibited scope entry: absent
- dev_auth.py changes: absent
- ActorContext contract changes: absent
- production-auth, config, kernel, API, SDK, and CLI source changes: absent
- runtime authentication, production header trust, protected material, providers, network calls, endpoints, packages, lockfiles, migrations, connector runtime, operator writes, module activation, sandbox execution, v0.2 tags, and v0.2 releases: absent
v0.2 actor context trust boundary authorization no-go PASS
SUMMARY

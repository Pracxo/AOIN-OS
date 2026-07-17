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
    services/brain-api/pyproject.toml)
      echo "AION-161 authorizes a future AION-162 dependency change but must not modify pyproject.toml" >&2
      exit 1
      ;;
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      echo "package files and lockfiles are forbidden for AION-161: $file" >&2
      exit 1
      ;;
    *migrations/*|migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-161: $file" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/contracts/actor_context_resolution.py|\
    services/brain-api/src/aion_brain/contracts/request_identity.py|\
    services/brain-api/src/aion_brain/identity/dev_auth.py|\
    services/brain-api/src/aion_brain/production_auth/*|\
    services/brain-api/src/aion_brain/config.py|\
    services/brain-api/src/aion_brain/kernel/*|\
    services/brain-api/src/aion_brain/api_support/*|\
    services/brain-api/src/aion_brain/api/*|\
    packages/aion-sdk-python/src/*)
      echo "implementation source changes are forbidden for AION-161: $file" >&2
      exit 1
      ;;
  esac

  if [[ -f "$file" ]] && ! aion161_is_scoped_offline_identity_assertion_verification_authorization_path "$file"; then
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

test ! -e services/brain-api/src/aion_brain/api/actor_context.py || {
  echo "new actor-context API router is forbidden" >&2
  exit 1
}

if [[ -s "$scan_file_list" ]]; then
  if rg -n '\b(runtime_implementation_approved|production_auth_runtime_enabled|identity_verification_enabled|identity_verification_runtime_enabled|authenticated_requests_enabled|authenticated_actor_context_enabled|identity_assertion_header_parsing_approved|authorization_header_parsing_approved|cookie_parsing_approved|identity_assertion_middleware_registration_approved|request_identity_verifier_replacement_approved|actor_context_resolver_integration_approved|actor_context_application_approved|request_identity_context_application_approved|runtime_private_key_material_approved|private_key_configuration_approved|private_key_persistence_approved|private_key_serialization_approved|raw_assertion_logging_approved|verified_claims_logging_approved|verified_claims_persistence_approved|jwks_network_fetch_approved|provider_discovery_approved|external_calls_approved|network_client_approved|provider_sdk_approved|replay_cache_approved|replay_protection_runtime_approved|identity_assertion_endpoint_approved|openapi_security_scheme_added|new_package_manifest_added|package_files_added|lockfiles_added|migrations_added|runtime_api_routes_added|api_runtime_execution_route_added|sdk_runtime_resource_added|cli_runtime_command_added|connector_runtime_enabled|operator_write_execution_approved|module_activation_approved|sandbox_execution_approved|v02_tag_created|v02_release_created|v02_release_approved|runtime_effect_approved|runtime_effect)\s*[:=]\s*true\b' $(cat "$scan_file_list"); then
    echo "runtime integration, private-key, provider, replay, route, package, migration, SDK, CLI, execution, tag, or release approval was enabled" >&2
    exit 1
  fi

  if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(production-auth|request-identity|actor-context|identity-assertion|auth/production|login|logout|callback|oauth|oidc|saml|token|session|credential)' $(cat "$scan_file_list"); then
    echo "runtime auth route surface found in changed files" >&2
    exit 1
  fi

  if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' $(cat "$scan_file_list"); then
    echo "network or external provider call path found in changed files" >&2
    exit 1
  fi
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-161" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-161" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 offline identity assertion verification authorization no-go result:
- AION-159-PA-0005: historical, consumed by AION-160 PR 70, expired, non-reusable
- AION-161-PA-0006: only active approved authorization
- approved future dependency: cryptography>=49.0.0,<50.0.0 in services/brain-api/pyproject.toml
- AION-161 dependency changes: absent
- implementation source changes: absent
- runtime authentication, request parsing, ActorContext and RequestIdentityContext application: absent
- runtime private keys, private-key configuration, persistence, and serialization: absent
- provider networking, JWKS fetch, provider discovery, external calls, and replay runtime: absent
- routes, OpenAPI security, SDK/CLI runtime surfaces, packages, lockfiles, migrations, connector runtime, operator writes, module activation, sandbox execution, v0.2 tags, and v0.2 releases: absent
v0.2 offline identity assertion verification authorization no-go PASS
SUMMARY

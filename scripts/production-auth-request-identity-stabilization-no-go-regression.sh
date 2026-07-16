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

base_ref="$(comparison_base || true)"
changed_file_list="$(mktemp)"
scan_file_list="$(mktemp)"
all_changed_text="$(mktemp)"
trap 'rm -f "$changed_file_list" "$scan_file_list" "$all_changed_text"' EXIT

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

test ! -e services/brain-api/src/aion_brain/api/request_identity.py || {
  echo "new request-identity API router is forbidden" >&2
  exit 1
}

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  case "$file" in
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      echo "package files and lockfiles are forbidden for AION-158: $file" >&2
      exit 1
      ;;
    packages/aion-sdk-python/src/*)
      echo "SDK or CLI runtime source is forbidden for AION-158: $file" >&2
      exit 1
      ;;
    *migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-158: $file" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/api/*)
      echo "API route source changes are forbidden for AION-158: $file" >&2
      exit 1
      ;;
  esac

  if [[ -f "$file" ]]; then
    case "$file" in
      services/brain-api/tests/*|docs/*|README.md|AGENTS.md|\
      examples/auth/*|operator-console-static/*|operator-console-static/demo-data/*|\
      scripts/production-auth-request-identity-stabilization-check.sh|\
      scripts/production-auth-request-identity-stabilization-runtime-hold.sh|\
      scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
      scripts/production-auth-request-identity-check.sh|\
      scripts/production-auth-request-identity-runtime-hold.sh|\
      scripts/production-auth-request-identity-no-go-regression.sh|\
      scripts/production-auth-core-no-go-regression.sh|\
      scripts/production-auth-core-stabilization-no-go-regression.sh|\
      scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh|\
      scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh)
        ;;
      *)
        printf '%s\n' "$file" >> "$scan_file_list"
        ;;
    esac
    printf '%s\n' "$file" >> "$all_changed_text"
  fi
done < "$changed_file_list"

request_middleware="services/brain-api/src/aion_brain/production_auth/request_middleware.py"
if [[ -f "$request_middleware" ]]; then
  if rg -n 'BaseHTTPMiddleware|from +fastapi +import +(Request|Response)|Request\(|Response\(' "$request_middleware"; then
    echo "request identity middleware must remain pure ASGI" >&2
    exit 1
  fi
  if rg -n 'request\.(headers|cookies|query_params|body)\b|scope\[("headers"|'\''headers'\'')\]|scope\[("query_string"|'\''query_string'\'')\]|scope\[("client"|'\''client'\'')\]|scope\[("server"|'\''server'\'')\]' "$request_middleware"; then
    echo "request identity middleware must not inspect request identity material" >&2
    exit 1
  fi
  if rg -n 'receive_wrapper|wrapped_receive|send_wrapper|wrapped_send|body_chunks|response_body|buffered_response' "$request_middleware"; then
    echo "request identity middleware must not wrap channels or buffer responses" >&2
    exit 1
  fi
fi

if [[ -s "$scan_file_list" ]]; then
  if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(production-auth|request-identity|auth/production|login|logout|callback|oauth|oidc|saml|token|session|credential)' $(cat "$scan_file_list"); then
    echo "runtime auth route surface found in changed files" >&2
    exit 1
  fi

  if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' $(cat "$scan_file_list"); then
    echo "network or external call path found in changed files" >&2
    exit 1
  fi

  if rg -n '\b(oauth|oidc|saml|authlib|okta|auth0|webauthn|passkey|python-jose|jwt)\b.*\b(enabled|client|provider|runtime|sdk)\b' $(cat "$scan_file_list"); then
    echo "provider runtime or SDK surface found in changed files" >&2
    exit 1
  fi
fi

if [[ -s "$all_changed_text" ]]; then
  if rg -n '\b(runtime_implementation_approved|production_auth_runtime_enabled|identity_verification_enabled|authenticated_requests_enabled|runtime_enablement_guard_release_approved|runtime_enablement_guard_final_lock_release_approved|runtime_enablement_master_lock_release_approved|authorization_header_parsing_enabled|cookie_parsing_enabled|credential_verification_enabled|password_verification_enabled|token_parsing_enabled|token_issuance_enabled|token_storage_enabled|token_refresh_enabled|session_creation_enabled|session_storage_enabled|cookie_issuance_enabled|cookie_session_persistence_enabled|external_identity_provider_enabled|oauth_runtime_enabled|oidc_runtime_enabled|saml_runtime_enabled|external_calls_enabled|network_client_enabled|provider_sdk_enabled|operator_write_execution_enabled|connector_runtime_enabled|module_activation_enabled|sandbox_execution_enabled|package_files_added|lockfiles_added|migrations_added|runtime_api_routes_added|openapi_security_scheme_added|sdk_runtime_resource_added|cli_runtime_command_added|v02_tag_created|v02_release_created)\s*[:=]\s*true\b' $(cat "$all_changed_text"); then
    echo "runtime, endpoint, parsing, storage, provider, package, migration, execution, tag, or release flag was enabled" >&2
    exit 1
  fi
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-158" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-158" >&2
  exit 1
fi

echo "production auth request identity stabilization no-go PASS"

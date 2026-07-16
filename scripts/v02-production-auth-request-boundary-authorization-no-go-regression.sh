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

scan_paths=(
  .env.example
  docs/release
  docs/adr
  docs/platform
  examples/release
  examples/platform
  examples/auth
  examples/connectors
  examples/modules
  operator-console-static/demo-data
  services/brain-api/src
)

scan_files=()
while IFS= read -r file; do
  scan_files+=("$file")
done < <(aion151_scan_files_excluding_scoped_authorization "${scan_paths[@]}")

if ((${#scan_files[@]})) && rg -n '\b(runtime_implementation_approved|production_auth_runtime_enabled|identity_verification_enabled|authenticated_requests_enabled|runtime_enablement_guard_release_approved|runtime_enablement_guard_final_lock_release_approved|runtime_enablement_master_lock_release_approved|login_endpoint_approved|logout_endpoint_approved|callback_endpoint_approved|authorization_header_parsing_approved|cookie_parsing_approved|credential_verification_approved|credential_storage_approved|password_storage_approved|token_parsing_approved|token_issuance_approved|token_storage_approved|token_refresh_approved|session_creation_approved|session_storage_approved|cookie_issuance_approved|cookie_session_persistence_approved|external_identity_provider_approved|oauth_runtime_approved|oidc_runtime_approved|saml_runtime_approved|external_calls_approved|network_client_approved|provider_sdk_approved|operator_write_execution_approved|connector_implementation_approved|connector_runtime_enabled|module_activation_approved|sandbox_execution_approved|package_files_added|lockfiles_added|migrations_added|runtime_api_routes_added|api_runtime_execution_route_added|v02_tag_created|v02_release_created|v02_release_approved)\s*[:=]\s*true\b' "${scan_files[@]}"; then
  echo "AION-155 runtime, endpoint, protected-material, provider, package, migration, route, release, or execution approval was enabled" >&2
  exit 1
fi

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  if aion156_is_scoped_request_identity_path "$file"; then
    continue
  fi
  if aion158_is_scoped_request_identity_stabilization_path "$file"; then
    continue
  fi
  echo "AION-155 must not modify production-auth, kernel, API, SDK, or CLI implementation source: $file" >&2
  exit 1
done < <(
  changed_files \
    services/brain-api/src/aion_brain/production_auth \
    services/brain-api/src/aion_brain/contracts/production_auth.py \
    services/brain-api/src/aion_brain/config.py \
    services/brain-api/src/aion_brain/kernel \
    services/brain-api/src/aion_brain/api \
    packages/aion-sdk-python/src
)

if changed_files | rg -n '(^|/)(migrations|alembic)/|(^|/).*migration.*\.(py|sql)$'; then
  echo "AION-155 must not add or change migrations" >&2
  exit 1
fi

if changed_files | rg -n '(^|/)(package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb)$'; then
  echo "AION-155 must not add package files or lockfiles" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  services/brain-api/src/aion_brain operator-console-static examples/release examples/platform examples/connectors; then
  echo "external call path found" >&2
  exit 1
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-155" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-155" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 production auth request boundary authorization no-go result:
- AION-151 historical: present
- AION-153 historical: present
- AION-155 historical consumed authorization: present
- AION-157 only active authorization: present
- unknown approved authorization: absent
- duplicate active authorization: absent
- historical reactivation: absent
- wrong task, scope, parent, candidate, or workstream: absent
- missing prohibited scope entries: absent
- extra approved scope entries: absent
- runtime authentication, endpoint, header, cookie, protected-material, provider, network, package, migration, SDK, CLI, connector, operator, module, sandbox, tag, and release approval: absent
v0.2 production auth request boundary authorization no-go PASS
SUMMARY

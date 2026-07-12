#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

python3 scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode no-go

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

if rg -n '\b(runtime_implementation_approved|production_auth_runtime_enabled|runtime_enablement_guard_release_approved|runtime_enablement_guard_final_lock_release_approved|runtime_enablement_master_lock_release_approved|login_endpoint_approved|logout_endpoint_approved|callback_endpoint_approved|credential_storage_approved|password_storage_approved|token_storage_approved|session_storage_approved|cookie_session_persistence_approved|external_identity_provider_approved|oauth_runtime_approved|oidc_runtime_approved|saml_runtime_approved|external_calls_approved|network_client_approved|provider_sdk_approved|operator_write_execution_approved|connector_implementation_approved|connector_runtime_enabled|module_activation_approved|sandbox_execution_approved|package_files_added|lockfiles_added|migrations_added|runtime_api_routes_added|api_runtime_execution_route_added|v02_tag_created|v02_release_created|v02_release_approved)\s*[:=]\s*true\b' "${scan_paths[@]}"; then
  echo "AION-151 runtime, storage, provider, package, migration, route, release, or execution approval was enabled" >&2
  exit 1
fi

if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' \
  services/brain-api/src/aion_brain operator-console-static examples/release examples/platform examples/connectors; then
  echo "external call path found" >&2
  exit 1
fi

for file in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb; do
  if find . -path './.git' -prune -o -type f -name "$file" -print | rg -n '.'; then
    echo "package manager file is not allowed for AION-151: $file" >&2
    exit 1
  fi
done

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-151" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-151" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 production auth authorization no-go result:
- exactly one approved authorization tuple: present
- duplicate approved authorization: absent
- scope expansion: absent
- runtime enablement: absent
- endpoint approvals: absent
- credential, password, token, session, and cookie storage approvals: absent
- identity-provider integration: absent
- network calls and provider SDK approval: absent
- package files and lockfiles: absent
- migrations: absent
- runtime API routes: absent
- connector runtime, operator writes, module activation, and sandbox execution: absent
- v0.2 tag or release: absent
v0.2 production auth authorization no-go PASS
SUMMARY

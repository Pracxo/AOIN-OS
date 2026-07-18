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
    services/brain-api/pyproject.toml|\
    services/brain-api/src/aion_brain/contracts/identity_assertion.py|\
    services/brain-api/src/aion_brain/contracts/actor_context_resolution.py|\
    services/brain-api/src/aion_brain/contracts/request_identity.py|\
    services/brain-api/src/aion_brain/production_auth/*|\
    services/brain-api/src/aion_brain/identity/*|\
    services/brain-api/src/aion_brain/idempotency/*|\
    services/brain-api/src/aion_brain/config.py|\
    services/brain-api/src/aion_brain/kernel/*|\
    services/brain-api/src/aion_brain/api_support/*|\
    services/brain-api/src/aion_brain/api/*|\
    packages/aion-sdk-python/src/*)
      echo "protected implementation or dependency path changed in AION-163: $file" >&2
      exit 1
      ;;
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      echo "package files and lockfiles are forbidden for AION-163: $file" >&2
      exit 1
      ;;
    *migrations/*|migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-163: $file" >&2
      exit 1
      ;;
  esac

  if [[ -f "$file" ]] && ! aion163_is_scoped_identity_assertion_replay_protection_authorization_path "$file"; then
    printf '%s\n' "$file" >> "$scan_file_list"
  fi
done < "$changed_file_list"

for path in \
  services/brain-api/src/aion_brain/contracts/identity_assertion_replay.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_evidence.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py; do
  test ! -e "$path" || {
    echo "AION-164 replay implementation source was added prematurely: $path" >&2
    exit 1
  }
done

if [[ -s "$scan_file_list" ]]; then
  if rg -n '\b(dependency_change_approved|new_dependency_approved|database_migration_approved|production_schema_auto_create_approved|request_authentication_approved|request_middleware_integration_approved|actor_context_application_approved|request_identity_context_application_approved|raw_assertion_persistence_approved|signature_persistence_approved|verified_claim_persistence_approved|in_memory_runtime_replay_store_approved|background_cleanup_scheduler_approved|external_identity_provider_approved|jwks_network_fetch_approved|provider_discovery_approved|external_calls_approved|network_client_approved|provider_sdk_approved|identity_assertion_endpoint_approved|openapi_security_scheme_added|sdk_runtime_resource_added|cli_runtime_command_added|connector_runtime_enabled|operator_write_execution_approved|module_activation_approved|sandbox_execution_approved|v02_tag_created|v02_release_created|v02_release_approved)\s*[:=]\s*true\b' $(cat "$scan_file_list"); then
    echo "AION-163 no-go approval was enabled" >&2
    exit 1
  fi
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-163" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-163" >&2
  exit 1
fi

cat <<'SUMMARY'
v0.2 identity assertion replay protection authorization no-go result:
- AION-161-PA-0006: historical, consumed by AION-162 PR 72 and corrective PR 73, expired, non-reusable
- AION-163-PA-0007: only active approved authorization
- replay implementation source changes in AION-163: absent
- production-auth, idempotency, config, kernel, API, SDK, CLI, pyproject, package, lockfile, and migration changes: absent
- dependency changes, migrations, production schema auto-create, runtime integration, request authentication, raw persistence, provider/network, endpoint, tag, and release approvals: false or absent
v0.2 identity assertion replay protection authorization no-go PASS
SUMMARY

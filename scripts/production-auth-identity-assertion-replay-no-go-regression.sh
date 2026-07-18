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
scan_file_list="$(mktemp)"
trap 'rm -f "$changed_file_list" "$scan_file_list"' EXIT
changed_files > "$changed_file_list"

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  if aion164_is_scoped_identity_assertion_replay_protection_path "$file"; then
    if [[ -f "$file" ]]; then
      printf '%s\n' "$file" >> "$scan_file_list"
    fi
    continue
  fi
  case "$file" in
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb|\
    requirements.txt|requirements-dev.txt|poetry.lock|uv.lock|Pipfile|Pipfile.lock)
      echo "package files and lockfiles are forbidden for AION-164: $file" >&2
      exit 1
      ;;
    *migrations/*|migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-164: $file" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/api/*|\
    services/brain-api/src/aion_brain/api_support/*|\
    services/brain-api/src/aion_brain/config.py|\
    services/brain-api/src/aion_brain/kernel/*|\
    packages/aion-sdk-python/src/*)
      echo "runtime integration path is forbidden for AION-164: $file" >&2
      exit 1
      ;;
  esac

  if [[ -f "$file" ]]; then
    echo "unscoped AION-164 file change: $file" >&2
    exit 1
  fi
done < "$changed_file_list"

if [[ -s "$scan_file_list" ]]; then
  if rg -n '\b(request_authenticated|actor_context_applied|request_identity_context_applied|runtime_effect|runtime_integration_allowed|request_integration_enabled|kernel_container_registration_enabled|middleware_integration_enabled|production_schema_auto_create_enabled|replay_protection_core_runtime_enabled|replay_repository_runtime_registered|production_auth_runtime_enabled|identity_verification_enabled|authenticated_requests_enabled|identity_assertion_header_parsing_enabled|authorization_header_parsing_enabled|cookie_parsing_enabled|identity_assertion_middleware_registered|external_identity_provider_enabled|jwks_network_fetch_enabled|provider_discovery_enabled|external_calls_enabled|identity_assertion_endpoint_enabled|runtime_api_routes_added|openapi_security_scheme_added|sdk_runtime_resource_added|cli_runtime_command_added|background_cleanup_scheduler_enabled|in_memory_runtime_replay_store_enabled|new_package_manifest_added|lockfiles_added|migrations_added|connector_runtime_enabled|operator_write_execution_enabled|module_activation_enabled|sandbox_execution_enabled|v02_tag_created|v02_release_created)\s*[:=]\s*true\b' $(cat "$scan_file_list"); then
    echo "AION-164 runtime, route, package, migration, or release flag was enabled" >&2
    exit 1
  fi
fi

for path in \
  services/brain-api/src/aion_brain/api/identity_assertion_replay.py \
  services/brain-api/src/aion_brain/api/identity_assertion.py \
  services/brain-api/src/aion_brain/api/production_auth.py \
  services/brain-api/src/aion_brain/api/request_identity.py \
  services/brain-api/src/aion_brain/api/actor_context.py \
  requirements.txt requirements-dev.txt poetry.lock uv.lock Pipfile Pipfile.lock; do
  test ! -e "$path" || {
    echo "forbidden AION-164 artifact exists: $path" >&2
    exit 1
  }
done

test "$(grep -Fc '"cryptography>=49.0.0,<50.0.0",' services/brain-api/pyproject.toml)" = "1" || {
  echo "cryptography dependency count changed" >&2
  exit 1
}

if rg -n 'os\.environ|APIRouter|FastAPI|KernelContainer|startup|shutdown|create_task|threading\.Thread|requests\.|httpx\.|aiohttp|socket\.|urllib\.request|alembic|from aion_brain\.idempotency|aion_idempotency_records|IdempotencyRepository|idempotency_metadata' \
  services/brain-api/src/aion_brain/contracts/identity_assertion_replay.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_evidence.py \
  services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py; then
  echo "runtime integration, network, migration, or idempotency reuse marker detected" >&2
  exit 1
fi

if rg -n '"issuer\.aion\.local"|"assertion-001"|signature|raw_assertion|subject-001|actor-001|workspace-001|SELECT|INSERT|OperationalError|IntegrityError' \
  examples/auth/identity-assertion-replay-*.json \
  examples/auth/offline-identity-assertion-pipeline-result.json \
  operator-console-static/demo-data/identity-assertion-replay-*.json; then
  echo "raw assertion material or SQL text detected in replay examples" >&2
  exit 1
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2|aion-v0\.2\.0)$'; then
  echo "v0.2 tag must not exist for AION-164" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-164" >&2
  exit 1
fi

echo "production auth identity assertion replay no-go PASS"

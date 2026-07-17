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
  case "$file" in
    package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|\
    */package.json|*/package-lock.json|*/pnpm-lock.yaml|*/yarn.lock|*/bun.lockb)
      echo "package files and lockfiles are forbidden for AION-160: $file" >&2
      exit 1
      ;;
    packages/aion-sdk-python/src/*)
      echo "SDK or CLI runtime source changes are forbidden for AION-160: $file" >&2
      exit 1
      ;;
    *migrations/*|migrations/*|*alembic/*|*migration*.py|*migration*.sql)
      echo "migrations are forbidden for AION-160: $file" >&2
      exit 1
      ;;
    services/brain-api/src/aion_brain/api/production_auth.py|\
    services/brain-api/src/aion_brain/api/request_identity.py|\
    services/brain-api/src/aion_brain/api/actor_context.py)
      echo "auth API routers are forbidden for AION-160: $file" >&2
      exit 1
      ;;
  esac

  case "$file" in
    services/brain-api/src/aion_brain/api/*)
      echo "API route source changes are forbidden for AION-160: $file" >&2
      exit 1
      ;;
  esac

  if [[ -f "$file" ]] && ! aion160_is_scoped_actor_context_trust_boundary_remediation_path "$file"; then
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

dev_auth="services/brain-api/src/aion_brain/identity/dev_auth.py"
grep -F 'return settings.env == "development" and settings.dev_auth_enabled is True' "$dev_auth" >/dev/null || {
  echo "exact development identity simulation gate is missing" >&2
  exit 1
}

if rg -n 'settings\.env\s+in|startswith\(|endswith\(|"dev"\s+in|'\''dev'\''\s+in|"local"|'\''local'\''' "$dev_auth"; then
  echo "loose development environment matching is forbidden" >&2
  exit 1
fi

if rg -n 'if +not +dev_enabled|if +dev_enabled +is +False' "$dev_auth"; then
  echo "non-development identity-header parsing branch is forbidden" >&2
  exit 1
fi

if rg -n 'request_context\.(actor_id|workspace_id|idempotency_key|method|path|metadata)' \
  services/brain-api/src/aion_brain/identity/dev_auth.py \
  services/brain-api/src/aion_brain/production_auth/actor_context.py \
  services/brain-api/src/aion_brain/production_auth/actor_context_evidence.py; then
  echo "RequestContext identity or request metadata projection is forbidden" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
source = root / "services/brain-api/src/aion_brain/identity/dev_auth.py"
tree = ast.parse(source.read_text())

identity_headers = {
    "X-AION-Actor-ID",
    "X-AION-Workspace-ID",
    "X-AION-Roles",
    "X-AION-Permissions",
    "X-AION-Security-Scope",
}


class HeaderVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.dev_stack: list[bool] = []
        self.violations: list[tuple[int, str]] = []

    def visit_If(self, node: ast.If) -> None:
        is_dev_gate = isinstance(node.test, ast.Name) and node.test.id == "dev_enabled"
        self.dev_stack.append(is_dev_gate or any(self.dev_stack))
        for item in node.body:
            self.visit(item)
        self.dev_stack.pop()
        self.dev_stack.append(any(self.dev_stack))
        for item in node.orelse:
            self.visit(item)
        self.dev_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in {"_header", "_csv_header"}:
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                header = node.args[1].value
                if header in identity_headers and not any(self.dev_stack):
                    self.violations.append((node.lineno, str(header)))
        self.generic_visit(node)


visitor = HeaderVisitor()
visitor.visit(tree)
if visitor.violations:
    raise SystemExit(f"identity header read outside dev gate: {visitor.violations}")

runtime_hold = json.loads(
    (root / "operator-console-static/demo-data/actor-context-runtime-hold.json").read_text()
)
required_false = [
    "authenticated_actor_context_enabled",
    "identity_verification_enabled",
    "authenticated_requests_enabled",
    "production_auth_runtime_enabled",
    "production_actor_header_trust_enabled",
    "production_workspace_header_trust_enabled",
    "production_role_header_trust_enabled",
    "production_permission_header_trust_enabled",
    "production_security_scope_header_trust_enabled",
    "authorization_header_parsing_enabled",
    "cookie_parsing_enabled",
    "credential_verification_enabled",
    "password_verification_enabled",
    "token_parsing_enabled",
    "token_issuance_enabled",
    "token_storage_enabled",
    "token_refresh_enabled",
    "session_creation_enabled",
    "session_storage_enabled",
    "cookie_issuance_enabled",
    "cookie_session_persistence_enabled",
    "external_identity_provider_enabled",
    "oauth_runtime_enabled",
    "oidc_runtime_enabled",
    "saml_runtime_enabled",
    "external_calls_enabled",
    "network_client_enabled",
    "provider_sdk_enabled",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "callback_endpoint_enabled",
    "token_endpoint_enabled",
    "session_endpoint_enabled",
    "credential_endpoint_enabled",
    "openapi_security_scheme_added",
    "runtime_api_routes_added",
    "sdk_runtime_resource_added",
    "cli_runtime_command_added",
    "connector_runtime_enabled",
    "operator_write_execution_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "package_files_added",
    "lockfiles_added",
    "migrations_added",
    "v02_tag_created",
    "v02_release_created",
]
for key in required_false:
    if runtime_hold.get(key) is not False:
        raise SystemExit(f"{key} must be false")
if runtime_hold.get("runtime_no_go_status") is not True:
    raise SystemExit("runtime_no_go_status must be true")
if runtime_hold.get("actor_context_trust_boundary_remediated") is not True:
    raise SystemExit("actor_context_trust_boundary_remediated must be true")
PY

if [[ -s "$scan_file_list" ]]; then
  if rg -n '\b(runtime_implementation_approved|runtime_enablement_guard_release_approved|production_auth_runtime_enabled|identity_verification_enabled|authenticated_requests_enabled|authenticated_actor_context_enabled|non_development_identity_header_trust_enabled|production_actor_header_trust_enabled|production_workspace_header_trust_enabled|production_role_header_trust_enabled|production_permission_header_trust_enabled|production_security_scope_header_trust_enabled|authorization_header_parsing_enabled|cookie_parsing_enabled|credential_verification_enabled|password_verification_enabled|credential_storage_enabled|password_storage_enabled|token_parsing_enabled|token_issuance_enabled|token_storage_enabled|token_refresh_enabled|session_creation_enabled|session_storage_enabled|cookie_issuance_enabled|cookie_session_persistence_enabled|external_identity_provider_enabled|oauth_runtime_enabled|oidc_runtime_enabled|saml_runtime_enabled|external_calls_enabled|network_client_enabled|provider_sdk_enabled|login_endpoint_enabled|logout_endpoint_enabled|callback_endpoint_enabled|token_endpoint_enabled|session_endpoint_enabled|credential_endpoint_enabled|openapi_security_scheme_added|package_files_added|lockfiles_added|migrations_added|runtime_api_routes_added|api_runtime_execution_route_added|sdk_runtime_resource_added|cli_runtime_command_added|operator_write_execution_enabled|connector_runtime_enabled|module_activation_enabled|sandbox_execution_enabled|v02_tag_created|v02_release_created)\s*[:=]\s*true\b' $(cat "$scan_file_list"); then
    echo "runtime, parsing, provider, package, migration, route, execution, tag, or release flag was enabled" >&2
    exit 1
  fi

  if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(production-auth|request-identity|actor-context|auth/production|login|logout|callback|oauth|oidc|saml|token|session|credential)' $(cat "$scan_file_list"); then
    echo "runtime auth route surface found in changed files" >&2
    exit 1
  fi

  if rg -n 'requests\.(get|post|put|patch|delete)|httpx\.|aiohttp\.ClientSession|urllib\.request|socket\.|dns\.resolver' $(cat "$scan_file_list"); then
    echo "network or external call path found in changed files" >&2
    exit 1
  fi
fi

if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2\.0|aion-v0\.2)$'; then
  echo "v0.2 tag must not exist for AION-160" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release must not exist for AION-160" >&2
  exit 1
fi

echo "production auth actor context trust boundary no-go PASS"

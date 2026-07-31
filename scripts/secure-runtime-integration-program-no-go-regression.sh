#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

if [[ -f docs/secure-runtime-integration/program-ledger.json ]] && \
  grep -q '"program_state": "sandboxed_capability_runtime_implemented_reference_only_pending_closeout"' docs/secure-runtime-integration/program-ledger.json && \
  grep -q '"active_sri_implementation_authorization": "AION-234-SRI-0003"' docs/secure-runtime-integration/program-ledger.json && \
  grep -q '"active_sri_implementation_task": "AION-235"' docs/secure-runtime-integration/program-ledger.json && \
  grep -q '"formal_closeout_task": "AION-236"' docs/secure-runtime-integration/program-ledger.json; then
  AION235_IMPLEMENTATION_STATE_ACTIVE=1
else
  AION235_IMPLEMENTATION_STATE_ACTIVE=0
fi

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
  if git_ref_exists HEAD^2 && git_ref_exists HEAD^1; then
    echo "HEAD^1"
    return 0
  fi
  if git_ref_exists HEAD~1; then
    echo "HEAD~1"
    return 0
  fi
  return 1
}

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/release/secure-runtime-integration-*|docs/release/secure-runtime-foundation-*|\
    docs/release/model-gateway-*|\
    docs/release/capability-runtime-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0194-secure-runtime-integration-program-charter-and-local-operator-runtime-foundation-authorization.md|\
    docs/adr/0195-controlled-authenticated-local-operator-runtime-foundation.md|\
    docs/adr/0196-secure-runtime-foundation-evaluation-and-controlled-model-gateway-authorization.md|\
	    docs/adr/0197-controlled-provider-neutral-model-gateway-and-deterministic-reference-provider.md|\
	    docs/adr/0198-controlled-model-gateway-evaluation-and-sandboxed-capability-runtime-authorization.md|\
	    docs/adr/0199-sandboxed-deterministic-capability-and-synthetic-connector-runtime.md|\
	    docs/adr/README.md|\
    examples/secure-runtime-integration/*|\
	    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
	    operator-console-static/demo-data/secure-runtime-integration-*.json|\
	    operator-console-static/demo-data/secure-runtime-foundation-operator-evaluation.json|\
	    operator-console-static/demo-data/model-gateway-*.json|\
	    operator-console-static/demo-data/capability-runtime-*.json|\
	    scripts/auth-design-check.sh|\
	    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
	    scripts/operator-console-static-check.sh|\
	    scripts/connector-no-go-regression.sh|\
	    scripts/connector-runtime-no-external-call-regression.sh|\
	    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
	    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
	    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
	    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
	    scripts/lib/cognitive_architecture_governance.py|\
	    scripts/operator-action-write-path-no-go-regression.sh|\
	    scripts/post-v01-release-candidate-no-go-regression.sh|\
	    scripts/production-auth-architecture-check.sh|\
	    scripts/static-console-safety-check.sh|\
	    scripts/secure-runtime-integration-program-authorization-check.sh|\
	    scripts/secure-runtime-integration-program-no-go-regression.sh|\
	    scripts/secure-runtime-integration-runtime-hold.sh|\
	    scripts/secure-runtime-foundation-check.sh|\
	    scripts/secure-runtime-foundation-no-go-regression.sh|\
	    scripts/secure-runtime-foundation-pilot-evidence-check.sh|\
	    scripts/secure-runtime-foundation-runtime-hold.sh|\
	    scripts/secure-runtime-foundation-operator-evaluation-check.sh|\
	    scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh|\
	    scripts/model-gateway-authorization-check.sh|\
	    scripts/model-gateway-authorization-no-go-regression.sh|\
	    scripts/model-gateway-check.sh|\
	    scripts/model-gateway-no-go-regression.sh|\
	    scripts/model-gateway-pilot-evidence-check.sh|\
	    scripts/model-gateway-runtime-hold.sh|\
	    scripts/model-gateway-operator-evaluation-check.sh|\
	    scripts/model-gateway-operator-evaluation-no-go-regression.sh|\
	    scripts/capability-runtime-authorization-check.sh|\
	    scripts/capability-runtime-authorization-no-go-regression.sh|\
	    scripts/capability-runtime-check.sh|\
	    scripts/capability-runtime-no-go-regression.sh|\
	    scripts/capability-runtime-pilot-evidence-check.sh|\
	    scripts/capability-runtime-runtime-hold.sh|\
	    scripts/capability-runtime-local-sandbox-run.py|\
	    scripts/model-gateway-local-simulation-run.py|\
	    scripts/secure-runtime-local-operator-run.py|\
	    scripts/lib/secure_runtime_foundation_operator_evaluation.py|\
	    scripts/lib/model_gateway_operator_evaluation.py|\
	    scripts/lib/v02_production_auth_authorization.py|\
	    scripts/lib/v02-production-auth-scan-exclusions.sh|\
	    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
	    scripts/production-auth-core-no-go-regression.sh|\
	    scripts/production-auth-core-stabilization-no-go-regression.sh|\
	    scripts/production-auth-identity-assertion-replay-no-go-regression.sh|\
	    scripts/production-auth-offline-identity-assertion-check.sh|\
	    scripts/production-auth-offline-identity-assertion-no-go-regression.sh|\
	    scripts/production-auth-request-identity-no-go-regression.sh|\
	    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
	    scripts/v02-actor-context-trust-boundary-authorization-check.sh|\
	    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
	    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
	    scripts/v02-offline-identity-assertion-verification-authorization-check.sh|\
	    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
	    scripts/v02-production-auth-request-boundary-authorization-check.sh|\
	    scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh|\
	    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
	    scripts/governed-learning-memory-program-final-evaluation-no-go-regression.sh|\
    services/brain-api/src/aion_brain/contracts/secure_runtime.py|\
    services/brain-api/src/aion_brain/secure_runtime/__init__.py|\
    services/brain-api/src/aion_brain/secure_runtime/authorization.py|\
    services/brain-api/src/aion_brain/secure_runtime/identity_binding.py|\
    services/brain-api/src/aion_brain/secure_runtime/session_lifecycle.py|\
    services/brain-api/src/aion_brain/secure_runtime/request_pipeline.py|\
    services/brain-api/src/aion_brain/secure_runtime/capability_dispatch.py|\
    services/brain-api/src/aion_brain/secure_runtime/runtime_guard.py|\
    services/brain-api/src/aion_brain/secure_runtime/kill_switch.py|\
    services/brain-api/src/aion_brain/secure_runtime/audit.py|\
    services/brain-api/src/aion_brain/secure_runtime/observability.py|\
    services/brain-api/src/aion_brain/secure_runtime/integrity.py|\
    services/brain-api/src/aion_brain/secure_runtime/evidence.py|\
    services/brain-api/tests/secure_runtime_test_support.py|\
	    services/brain-api/tests/secure_runtime_aion232_test_helpers.py|\
	    services/brain-api/tests/aion234_test_support.py|\
	    services/brain-api/tests/capability_runtime_test_support.py|\
    services/brain-api/tests/model_gateway_aion233_test_support.py|\
    services/brain-api/tests/test_secure_runtime_*.py|\
    services/brain-api/tests/test_capability_runtime_*.py|\
    services/brain-api/tests/test_model_gateway_*.py)
      return 0
      ;;
  esac
  return 1
}

is_aion233_model_gateway_source_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/model_gateway.py|\
    services/brain-api/src/aion_brain/model_gateway/__init__.py|\
    services/brain-api/src/aion_brain/model_gateway/authorization.py|\
    services/brain-api/src/aion_brain/model_gateway/manifests.py|\
    services/brain-api/src/aion_brain/model_gateway/request_envelope.py|\
    services/brain-api/src/aion_brain/model_gateway/context_budget.py|\
    services/brain-api/src/aion_brain/model_gateway/routing.py|\
    services/brain-api/src/aion_brain/model_gateway/circuit_breaker.py|\
    services/brain-api/src/aion_brain/model_gateway/guard.py|\
    services/brain-api/src/aion_brain/model_gateway/response_validation.py|\
    services/brain-api/src/aion_brain/model_gateway/provider_registry.py|\
    services/brain-api/src/aion_brain/model_gateway/provider_adapter.py|\
    services/brain-api/src/aion_brain/model_gateway/reference_provider.py|\
    services/brain-api/src/aion_brain/model_gateway/audit.py|\
    services/brain-api/src/aion_brain/model_gateway/observability.py|\
    services/brain-api/src/aion_brain/model_gateway/integrity.py|\
    services/brain-api/src/aion_brain/model_gateway/evidence.py)
      return 0
      ;;
  esac
  return 1
}

is_aion235_capability_runtime_source_path() {
  [[ "$AION235_IMPLEMENTATION_STATE_ACTIVE" == "1" ]] || return 1
  case "$1" in
    services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py|\
    services/brain-api/src/aion_brain/capability_runtime/__init__.py|\
    services/brain-api/src/aion_brain/capability_runtime/authorization.py|\
    services/brain-api/src/aion_brain/capability_runtime/component_binding.py|\
    services/brain-api/src/aion_brain/capability_runtime/manifests.py|\
    services/brain-api/src/aion_brain/capability_runtime/request_envelope.py|\
    services/brain-api/src/aion_brain/capability_runtime/input_validation.py|\
    services/brain-api/src/aion_brain/capability_runtime/execution_plan.py|\
    services/brain-api/src/aion_brain/capability_runtime/sandbox.py|\
    services/brain-api/src/aion_brain/capability_runtime/guard.py|\
    services/brain-api/src/aion_brain/capability_runtime/dispatcher.py|\
    services/brain-api/src/aion_brain/capability_runtime/reference_capabilities.py|\
    services/brain-api/src/aion_brain/capability_runtime/reference_connector.py|\
    services/brain-api/src/aion_brain/capability_runtime/budget.py|\
    services/brain-api/src/aion_brain/capability_runtime/audit.py|\
    services/brain-api/src/aion_brain/capability_runtime/observability.py|\
    services/brain-api/src/aion_brain/capability_runtime/integrity.py|\
    services/brain-api/src/aion_brain/capability_runtime/evidence.py)
      return 0
      ;;
  esac
  return 1
}

is_aion231_source_path() {
  case "$1" in
    services/brain-api/src/aion_brain/contracts/secure_runtime.py|\
    services/brain-api/src/aion_brain/secure_runtime/__init__.py|\
    services/brain-api/src/aion_brain/secure_runtime/authorization.py|\
    services/brain-api/src/aion_brain/secure_runtime/identity_binding.py|\
    services/brain-api/src/aion_brain/secure_runtime/session_lifecycle.py|\
    services/brain-api/src/aion_brain/secure_runtime/request_pipeline.py|\
    services/brain-api/src/aion_brain/secure_runtime/capability_dispatch.py|\
    services/brain-api/src/aion_brain/secure_runtime/runtime_guard.py|\
    services/brain-api/src/aion_brain/secure_runtime/kill_switch.py|\
    services/brain-api/src/aion_brain/secure_runtime/audit.py|\
    services/brain-api/src/aion_brain/secure_runtime/observability.py|\
    services/brain-api/src/aion_brain/secure_runtime/integrity.py|\
    services/brain-api/src/aion_brain/secure_runtime/evidence.py)
      return 0
      ;;
  esac
  return 1
}

base_ref="$(comparison_base || true)"
changed_file_list="$(mktemp)"
changed_status_list="$(mktemp)"
trap 'rm -f "$changed_file_list" "$changed_status_list"' EXIT

if [[ -n "$base_ref" ]]; then
  {
    git diff --name-only "$base_ref" HEAD --
    git diff --name-only HEAD --
    git diff --cached --name-only --
    git ls-files --others --exclude-standard --
  } | sort -u > "$changed_file_list"
  {
    git diff --name-status "$base_ref" HEAD --
    git diff --name-status HEAD --
    git diff --cached --name-status --
    git ls-files --others --exclude-standard -- | sed 's/^/A\t/'
  } | sort -u > "$changed_status_list"
else
  {
    git diff --name-only HEAD --
    git diff --cached --name-only --
    git ls-files --others --exclude-standard --
  } | sort -u > "$changed_file_list"
  {
    git diff --name-status HEAD --
    git diff --cached --name-status --
    git ls-files --others --exclude-standard -- | sed 's/^/A\t/'
  } | sort -u > "$changed_status_list"
fi

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
	  if ! is_allowed_path "$path"; then
	    if ! is_aion233_model_gateway_source_path "$path" && \
	      ! is_aion235_capability_runtime_source_path "$path"; then
	      echo "ERROR: AION-230 changed disallowed path: $path" >&2
	      exit 1
	    fi
	  fi
  case "$path" in
    services/brain-api/src/*|packages/*|.github/workflows/*|\
    *migrations*|*package.json|*package-lock.json|*pnpm-lock.yaml|*yarn.lock|\
    *poetry.lock|*Pipfile.lock|*requirements*.txt|*pyproject.toml)
	      if ! is_aion231_source_path "$path" && \
	        ! is_aion233_model_gateway_source_path "$path" && \
	        ! is_aion235_capability_runtime_source_path "$path"; then
	        echo "ERROR: prohibited runtime/dependency/migration path changed: $path" >&2
	        exit 1
	      fi
      ;;
  esac
done < "$changed_file_list"

while IFS=$'\t' read -r status path rest; do
  [[ -n "${status:-}" ]] || continue
  if [[ "$status" == D* || "$status" == R* ]]; then
    case "$path" in
      services/brain-api/src/*|packages/*|scripts/*)
        echo "ERROR: prohibited source/script deletion or rename: $status $path ${rest:-}" >&2
        exit 1
      ;;
    esac
  fi
done < "$changed_status_list"

future_source_paths=(
  services/brain-api/src/aion_brain/contracts/secure_runtime.py
  services/brain-api/src/aion_brain/secure_runtime/__init__.py
  services/brain-api/src/aion_brain/secure_runtime/authorization.py
  services/brain-api/src/aion_brain/secure_runtime/identity_binding.py
  services/brain-api/src/aion_brain/secure_runtime/session_lifecycle.py
  services/brain-api/src/aion_brain/secure_runtime/request_pipeline.py
  services/brain-api/src/aion_brain/secure_runtime/capability_dispatch.py
  services/brain-api/src/aion_brain/secure_runtime/runtime_guard.py
  services/brain-api/src/aion_brain/secure_runtime/kill_switch.py
  services/brain-api/src/aion_brain/secure_runtime/audit.py
  services/brain-api/src/aion_brain/secure_runtime/observability.py
  services/brain-api/src/aion_brain/secure_runtime/integrity.py
  services/brain-api/src/aion_brain/secure_runtime/evidence.py
)
for path in "${future_source_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "ERROR: AION-231 source missing after implementation: $path" >&2
    exit 1
  fi
done
if find services/brain-api/src/aion_brain/secure_runtime -type f | while IFS= read -r path; do
  is_aion231_source_path "$path" || echo "$path"
done | grep -q .; then
  echo "ERROR: prohibited secure_runtime source file exists" >&2
  exit 1
fi

if grep -R -n '"implementation_approved"[[:space:]]*:[[:space:]]*true' \
  docs/secure-runtime-integration examples/secure-runtime-integration operator-console-static/demo-data/secure-runtime-integration-*.json; then
  echo "ERROR: future implementation approval flag created" >&2
  exit 1
fi

./scripts/secure-runtime-integration-program-authorization-check.sh
aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "secure runtime integration program no-go PASS"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

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

changed_paths() {
  local base
  base="$(comparison_base || true)"
  if [[ -n "$base" ]]; then
    git diff --name-only --diff-filter=ACMRT "$base" HEAD --
  fi
  git diff --name-only --diff-filter=ACMRT HEAD --
  git diff --cached --name-only --diff-filter=ACMRT --
  git ls-files --others --exclude-standard --
}

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/adr/0202-final-secure-runtime-integration-evaluation-and-v02-release-qualification-program-authorization.md|\
    docs/adr/0203-disabled-v02-production-readiness-qualification-foundation.md|\
    docs/adr/0204-v02-qualification-foundation-evaluation-and-controlled-isolated-staging-qualification-authorization.md|\
    docs/adr/0205-controlled-isolated-local-staging-artifact-build-and-rollback-drill.md|\
    docs/adr/README.md|\
    docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/project-status.md|docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/v02-release-qualification/*|\
    docs/release/secure-runtime-integration-*|\
    docs/release/operator-console-integration-implementation.md|\
    docs/release/operator-console-integrated-local-pilot.md|\
    docs/release/operator-console-integration-runtime-hold.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/release/v02-release-qualification-*|\
    docs/release/v02-qualification-foundation-operator-evaluation-*|\
    docs/release/v02-staging-qualification-*|\
    examples/secure-runtime-integration/*|\
    examples/v02-release-qualification/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/secure-runtime-integration-*.json|\
    operator-console-static/demo-data/v02-release-qualification-*.json|\
    operator-console-static/demo-data/v02-qualification-foundation-operator-evaluation.json|\
    operator-console-static/demo-data/v02-staging-qualification-authorization.json|\
    operator-console-static/demo-data/v02-staging-environment-profile.json|\
    operator-console-static/demo-data/v02-staging-build-plan.json|\
    operator-console-static/demo-data/v02-staging-artifact-boundary.json|\
    operator-console-static/demo-data/v02-staging-rollback-boundary.json|\
    operator-console-static/demo-data/v02-staging-runtime-hold.json|\
    operator-console-static/demo-data/v02-release-qualification-staging-*.json|\
    scripts/auth-design-check.sh|\
    scripts/capability-runtime-authorization-check.sh|\
    scripts/capability-runtime-authorization-no-go-regression.sh|\
    scripts/capability-runtime-check.sh|\
    scripts/capability-runtime-no-go-regression.sh|\
    scripts/capability-runtime-operator-evaluation-no-go-regression.sh|\
    scripts/connector-no-go-regression.sh|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
    scripts/model-gateway-authorization-check.sh|\
    scripts/model-gateway-authorization-no-go-regression.sh|\
    scripts/model-gateway-check.sh|\
    scripts/model-gateway-no-go-regression.sh|\
    scripts/model-gateway-operator-evaluation-no-go-regression.sh|\
    scripts/operator-console-integration-authorization-check.sh|\
    scripts/operator-console-integration-authorization-no-go-regression.sh|\
    scripts/operator-console-integration-check.sh|\
    scripts/operator-console-integration-runtime-hold.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/secure-runtime-integration-final-evaluation-check.sh|\
    scripts/secure-runtime-integration-final-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-authorization-check.sh|\
    scripts/secure-runtime-integration-program-complete-check.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/secure-runtime-integration-runtime-hold.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/lib/v02_release_qualification_foundation_operator_evaluation.py|\
    scripts/secure-runtime-foundation-check.sh|\
    scripts/secure-runtime-foundation-no-go-regression.sh|\
    scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-release-qualification-program-authorization-check.sh|\
    scripts/v02-release-qualification-program-authorization-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-check.sh|\
    scripts/v02-release-qualification-foundation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-check.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-pilot-evidence-check.sh|\
    scripts/v02-release-qualification-foundation-runtime-hold.sh|\
    scripts/v02-release-qualification-local-run.py|\
    scripts/v02-release-qualification-runtime-hold.sh|\
    scripts/v02-staging-qualification-authorization-check.sh|\
    scripts/v02-staging-qualification-authorization-no-go-regression.sh|\
    scripts/v02-staging-qualification-check.sh|\
    scripts/v02-staging-qualification-local-run.py|\
    scripts/v02-staging-qualification-no-go-regression.sh|\
    scripts/v02-staging-qualification-pilot-evidence-check.sh|\
    scripts/v02-staging-qualification-runtime-hold.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/secure_runtime_integration_final_evaluation.py|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/tests/secure_runtime_integration_final_evaluation_test_support.py|\
    services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py|\
    services/brain-api/src/aion_brain/v02_staging_qualification/*.py|\
    services/brain-api/tests/test_governed_learning_memory_no_runtime_source.py|\
    services/brain-api/tests/test_identity_assertion_no_runtime_integration.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_intelligence_program_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_research_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py|\
    services/brain-api/tests/test_v02_staging_qualification_aion241.py|\
    services/brain-api/tests/test_capability_runtime_current_state_after_aion235.py|\
    services/brain-api/tests/test_model_gateway_authorization.py|\
    services/brain-api/tests/test_model_gateway_authorization_scope.py|\
    services/brain-api/tests/test_model_gateway_current_state_consistency.py|\
    services/brain-api/tests/test_secure_runtime_integration_final_closeout_aion238.py|\
    services/brain-api/tests/test_secure_runtime_integration_final_evaluation_aion238.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion232.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion234.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion236.py|\
    services/brain-api/tests/test_secure_runtime_current_state_consistency.py|\
    services/brain-api/tests/test_secure_runtime_integration_authorization.py|\
    services/brain-api/tests/test_secure_runtime_integration_program_charter.py|\
    services/brain-api/tests/test_secure_runtime_integration_project_status.py|\
    services/brain-api/tests/test_operator_console_integration_authorization.py)
      return 0
      ;;
    services/brain-api/tests/test_governed_learning_memory_no_runtime_source.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_intelligence_program_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_research_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py|\
    services/brain-api/src/aion_brain/contracts/v02_release_qualification.py|\
    services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py|\
    services/brain-api/src/aion_brain/v02_release_qualification/*.py|\
    services/brain-api/src/aion_brain/v02_staging_qualification/*.py|\
    services/brain-api/tests/test_v02_release_qualification_*.py)
      return 0
      ;;
  esac
  return 1
}

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if ! is_allowed_path "$path"; then
    echo "AION-238 changed path outside v0.2 qualification authorization boundary: $path" >&2
    exit 1
  fi
done < <(changed_paths | sort -u)

if changed_paths | sort -u | rg -n '^\.github/workflows/' >/dev/null 2>&1; then
  echo "AION-238 must not modify GitHub workflows" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|pyproject\.toml)$' >/dev/null 2>&1; then
  echo "AION-238 must not modify package manifests or lockfiles" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^migrations/|/migrations/)' >/dev/null 2>&1; then
  echo "AION-238 must not add migrations" >&2
  exit 1
fi
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  case "$path" in
    services/brain-api/src/aion_brain/contracts/v02_release_qualification.py|\
    services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py|\
    services/brain-api/src/aion_brain/v02_release_qualification/*.py|\
    services/brain-api/src/aion_brain/v02_staging_qualification/*.py)
      ;;
    services/brain-api/src/aion_brain/*)
      echo "AION-239 must not modify completed runtime source: $path" >&2
      exit 1
      ;;
  esac
done < <(changed_paths | sort -u)
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+' >/dev/null 2>&1; then
  echo "AION-238 must not create a v0.2 tag" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

prohibited_true = (
    "production_auth_runtime_enabled",
    "external_identity_provider_call_enabled",
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "public_listener_enabled",
    "credential_generation_enabled",
    "credential_read_enabled",
    "credential_persistence_enabled",
    "secret_provisioning_enabled",
    "token_generation_enabled",
    "token_read_enabled",
    "token_persistence_enabled",
    "deployment_execution_enabled",
    "rollback_execution_enabled",
    "production_observability_export_enabled",
    "v02_release_candidate_created",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
)
for path in (
    Path("docs/v02-release-qualification/program-ledger.json"),
    Path("docs/v02-release-qualification/authorization-ledger.json"),
):
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in prohibited_true:
            if payload.get(key) is not False:
                raise SystemExit(f"{path} must keep {key}=false")
        limits = payload.get("resource_limits", {})
        if isinstance(limits, dict) and isinstance(limits.get("limits"), dict):
            limits = limits["limits"]
        for key, value in limits.items():
            if key.startswith("maximum_") and key in {
                "maximum_public_network_calls",
                "maximum_dns_resolutions",
                "maximum_external_identity_provider_calls",
                "maximum_credentials_generated",
                "maximum_credentials_read",
                "maximum_credentials_persisted",
                "maximum_secrets_provisioned",
                "maximum_tokens_generated",
                "maximum_tokens_read",
                "maximum_tokens_persisted",
                "maximum_production_deployments",
                "maximum_v02_tags_created",
                "maximum_v02_releases_created",
            } and value != 0:
                raise SystemExit(f"{path} must keep {key}=0")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
echo "v0.2 release qualification program authorization no-go PASS"

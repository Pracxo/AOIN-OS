#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  operator-console-static/README.md
  operator-console-static/index.html
  operator-console-static/styles.css
  operator-console-static/app.js
  operator-console-static/demo-data/overview-view-model.json
  operator-console-static/demo-data/module-lifecycle-view-model.json
  operator-console-static/demo-data/provider-hardening-view-model.json
  operator-console-static/demo-data/release-readiness-view-model.json
  operator-console-static/demo-data/incidents-view-model.json
  operator-console-static/demo-data/settings-safety-view-model.json
  operator-console-static/demo-data/module-lifecycle-dashboard.json
  operator-console-static/demo-data/generic-knowledge-trail.json
  operator-console-static/demo-data/module-activation-blockers.json
  operator-console-static/demo-data/module-mock-runtime-trail.json
  operator-console-static/demo-data/module-review-checklist.json
  operator-console-static/demo-data/operator-action-preview.json
  operator-console-static/demo-data/operator-action-blockers.json
  operator-console-static/demo-data/operator-action-review.json
  operator-console-static/demo-data/action-authorization-preview.json
  operator-console-static/demo-data/action-authorization-deny-matrix.json
  operator-console-static/demo-data/auth-runtime-status.json
  operator-console-static/demo-data/mock-claims-preview.json
  operator-console-static/demo-data/local-auth-status.json
  operator-console-static/demo-data/role-filtered-view-model.json
  docs/operator-console/static-console-prototype.md
  docs/operator-console/static-console-runbook.md
  docs/operator-console/static-console-safety-review.md
  docs/operator-console/static-console-test-plan.md
  docs/operator-console/module-lifecycle-dashboard.md
  docs/operator-console/generic-knowledge-trail-view.md
  docs/operator-console/module-review-panel.md
  docs/operator-console/module-dashboard-safety-review.md
  docs/operator-console/governed-operator-actions.md
  docs/operator-console/action-preview-panel.md
  docs/operator-console/action-review-flow.md
  docs/operator-console/action-boundary-matrix.md
  docs/adr/0080-static-local-operator-console-prototype.md
  docs/adr/0081-read-only-module-lifecycle-dashboard.md
  docs/adr/0083-governed-operator-actions-dry-run-only.md
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing static console artifact: $file" >&2
    exit 1
  }
done

grep -q "AION Operator Console Prototype — local, read-only, no activation" operator-console-static/index.html || {
  echo "static console banner missing" >&2
  exit 1
}

grep -q "isLocalApiOrigin" operator-console-static/app.js || {
  echo "localhost API guard missing" >&2
  exit 1
}

grep -q "127.0.0.1" operator-console-static/app.js || {
  echo "127.0.0.1 API guard missing" >&2
  exit 1
}

grep -q "apiAllowed: false" operator-console-static/app.js || {
  echo "non-local API block missing" >&2
  exit 1
}

grep -q "/brain/operator-console/view-model" operator-console-static/app.js || {
  echo "view-model endpoint missing" >&2
  exit 1
}

if grep -R -n -E "https?://" operator-console-static | grep -v -E "localhost|127\\.0\\.0\\.1"; then
  echo "non-local URL found in static console" >&2
  exit 1
fi

if grep -n -E "method:[[:space:]]*[\"'](PUT|PATCH|DELETE)[\"']" operator-console-static/app.js; then
  echo "write HTTP method found in app.js" >&2
  exit 1
fi

if grep -n -E "\\b(import|require)[[:space:]]*\\(" operator-console-static/app.js; then
  echo "external library loading found in app.js" >&2
  exit 1
fi

if grep -n "localStorage" operator-console-static/app.js; then
  echo "localStorage usage found in app.js" >&2
  exit 1
fi

if grep -n -E "@import|url\\([[:space:]]*[\"']?https?://" operator-console-static/styles.css; then
  echo "external CSS import found" >&2
  exit 1
fi

for key in raw_prompt hidden_reasoning chain_of_thought password token api_key secret private_key credential authorization bearer; do
  grep -q "$key" operator-console-static/app.js || {
    echo "redaction key missing from app.js: $key" >&2
    exit 1
  }
done

grep -q "0080-static-local-operator-console-prototype.md" docs/adr/README.md || {
  echo "ADR 0080 is not indexed" >&2
  exit 1
}

grep -q "0081-read-only-module-lifecycle-dashboard.md" docs/adr/README.md || {
  echo "ADR 0081 is not indexed" >&2
  exit 1
}

grep -q "0083-governed-operator-actions-dry-run-only.md" docs/adr/README.md || {
  echo "ADR 0083 is not indexed" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
demo_dir = root / "operator-console-static" / "demo-data"
required_actions = {
    "activate_module",
    "activate_capability",
    "load_code",
    "execute_tool",
    "enable_external_model_calls",
    "hard_delete",
}


def validate_domain_expert_demo(payload: object, path: Path) -> None:
    forbidden_true_keys = {
        "automatic_action",
        "belief_mutated",
        "claim_accepted",
        "claim_rejected",
        "confidence_amplified",
        "consensus_as_truth",
        "domain_expert_mesh_runtime_enabled",
        "expert_majority_truth_override_enabled",
        "expert_mesh_database_enabled",
        "human_expert_identity_claimed",
        "human_expert_identity_claim_enabled",
        "knowledge_promoted",
        "model_call_enabled",
        "model_provider_integration_enabled",
        "network_access_enabled",
        "persistent_expert_mesh_write_enabled",
        "persistent_mesh_write_authorized",
        "professional_credential_claimed",
        "professional_credential_claim_enabled",
        "runtime_effect",
        "tool_execution_enabled",
        "truth_decision",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if "read_only" in value and value["read_only"] is not True:
                raise SystemExit(f"domain expert demo must be read_only: {path}")
            if "redacted" in value and value["redacted"] is not True:
                raise SystemExit(f"domain expert demo must be redacted: {path}")
            if "redaction_applied" in value and value["redaction_applied"] is not True:
                raise SystemExit(f"domain expert demo redaction flag must be true: {path}")
            for key in forbidden_true_keys:
                if value.get(key) is not False and key in value:
                    raise SystemExit(f"domain expert demo flag must be false: {key}: {path}")
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)


def validate_tool_verification_demo(payload: object, path: Path) -> None:
    allowed_names = {
        "knowledge-intelligence-tool-attestation.json",
        "knowledge-intelligence-tool-manifest.json",
        "knowledge-intelligence-tool-plan.json",
        "knowledge-intelligence-tool-simulation.json",
        "knowledge-intelligence-tool-verification-authorization.json",
        "knowledge-intelligence-tool-verification-runtime-hold.json",
    }
    if path.name not in allowed_names:
        raise SystemExit(f"unknown knowledge intelligence tool demo: {path}")
    if not isinstance(payload, dict):
        raise SystemExit(f"knowledge intelligence tool demo must be an object: {path}")
    if payload.get("read_only") is not True:
        raise SystemExit(f"knowledge intelligence tool demo must be read_only: {path}")
    redaction_applied = payload.get("redaction_applied")
    redacted = payload.get("redacted")
    if redaction_applied is not True and redacted is not True:
        raise SystemExit(f"knowledge intelligence tool demo must be redacted: {path}")
    if payload.get("synthetic") is not True:
        raise SystemExit(f"knowledge intelligence tool demo must be synthetic: {path}")

    forbidden_true_keys = {
        "actual_execution_enabled",
        "actual_tool_executed",
        "actual_tool_execution_enabled",
        "api_route_enabled",
        "application_startup_registration_enabled",
        "approval_creation_enabled",
        "authorization_header_use_enabled",
        "automatic_claim_acceptance_enabled",
        "automatic_claim_rejection_enabled",
        "automatic_memory_ingestion_enabled",
        "automatic_merge_enabled",
        "autonomous_real_world_action_enabled",
        "background_tool_worker_enabled",
        "belief_mutated",
        "browser_automation_enabled",
        "cognitive_belief_creation_enabled",
        "cognitive_belief_mutation_enabled",
        "connector_integration_enabled",
        "cookie_use_enabled",
        "credential_use_enabled",
        "dependency_change_approved",
        "dns_resolution_enabled",
        "external_database_integration_enabled",
        "filesystem_mutation_enabled",
        "financial_action_execution_enabled",
        "git_mutation_enabled",
        "github_workflow_change_approved",
        "high_stakes_action_enabled",
        "installed_cli_command_enabled",
        "kernel_registration_enabled",
        "knowledge_promoted",
        "knowledge_promotion_enabled",
        "legal_action_execution_enabled",
        "medical_action_execution_enabled",
        "migration_approved",
        "model_call_enabled",
        "model_provider_integration_enabled",
        "model_weight_training_enabled",
        "network_access_enabled",
        "network_acquisition_enabled",
        "persistent_tool_state_write_enabled",
        "persistent_write_applied",
        "production_deployment_enabled",
        "raw_source_content_storage_enabled",
        "real_pull_request_creation_enabled",
        "runtime_effect",
        "shell_command_execution_enabled",
        "subprocess_execution_enabled",
        "tool_execution_enabled",
        "tool_state_database_enabled",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key in forbidden_true_keys:
                if key in value and value.get(key) is not False:
                    raise SystemExit(f"knowledge intelligence tool demo flag must be false: {key}: {path}")
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)

    if path.name == "knowledge-intelligence-tool-verification-authorization.json":
        for key in (
            "authorization_transaction_approved",
            "explicit_approval_record_approval",
            "implementation_authorization_approved",
            "implementation_go_status",
            "tool_verification_fabric_authorized",
        ):
            if payload.get(key) is not True:
                raise SystemExit(f"knowledge intelligence tool authorization flag must be true: {key}: {path}")
        if payload.get("implementation_no_go_status") is not False:
            raise SystemExit(f"knowledge intelligence tool authorization no-go flag must be false: {path}")
    elif path.name == "knowledge-intelligence-tool-verification-runtime-hold.json":
        if payload.get("tool_verification_fabric_authorized") is not True:
            raise SystemExit(f"knowledge intelligence tool hold must remain authorized: {path}")
        if payload.get("tool_verification_fabric_runtime_enabled") is not False:
            raise SystemExit(f"knowledge intelligence tool runtime must remain disabled: {path}")


def validate_secure_runtime_integration_demo(payload: object, path: Path) -> None:
    allowed_names = {
        "secure-runtime-integration-actor-context.json",
        "secure-runtime-integration-approval-bundle.json",
        "secure-runtime-integration-audit.json",
        "secure-runtime-integration-authorization.json",
        "secure-runtime-integration-capability-plan.json",
        "secure-runtime-integration-checkpoint.json",
        "secure-runtime-integration-guardrail-binding.json",
        "secure-runtime-integration-health.json",
        "secure-runtime-integration-identity-binding.json",
        "secure-runtime-integration-integrity.json",
        "secure-runtime-integration-kill-switch.json",
        "secure-runtime-integration-observability.json",
        "secure-runtime-integration-pilot-evidence.json",
        "secure-runtime-integration-policy-binding.json",
        "secure-runtime-integration-program.json",
        "secure-runtime-integration-request-identity.json",
        "secure-runtime-integration-risk-binding.json",
        "secure-runtime-integration-runtime-boundary.json",
        "secure-runtime-integration-runtime-guard.json",
        "secure-runtime-integration-runtime-hold.json",
        "secure-runtime-integration-session-state.json",
        "secure-runtime-integration-session.json",
        "secure-runtime-integration-simulated-dispatch.json",
        "secure-runtime-integration-stage-command.json",
        "secure-runtime-integration-stage-receipt.json",
    }
    if path.name not in allowed_names:
        raise SystemExit(f"unknown secure runtime integration demo: {path}")
    if not isinstance(payload, dict):
        raise SystemExit(f"secure runtime integration demo must be an object: {path}")
    if payload.get("program_id") != "AION-SECURE-RUNTIME-INTEGRATION-001":
        raise SystemExit(f"secure runtime integration program id mismatch: {path}")
    if payload.get("read_only") is not True:
        raise SystemExit(f"secure runtime integration demo must be read_only: {path}")
    redaction_applied = payload.get("redaction_applied")
    redacted = payload.get("redacted")
    if redaction_applied is not True and redacted is not True:
        raise SystemExit(f"secure runtime integration demo must be redacted: {path}")
    if payload.get("synthetic") is not True:
        raise SystemExit(f"secure runtime integration demo must be synthetic: {path}")

    false_keys = {
        "actual_execution_allowed",
        "actual_tool_execution_enabled",
        "calls_providers",
        "connector_call_allowed",
        "connector_execution_enabled",
        "credential_persistence_enabled",
        "deploys",
        "executes_tools",
        "external_identity_provider_enabled",
        "general_network_access_enabled",
        "git_mutation_enabled",
        "model_provider_call_enabled",
        "model_weight_training_enabled",
        "module_activation_enabled",
        "mutates_production_policy",
        "production_auth_runtime_enabled",
        "production_deployment_enabled",
        "production_runtime",
        "production_runtime_authorized",
        "production_write_allowed",
        "production_write_execution_enabled",
        "provider_call_allowed",
        "session_token_issuance_enabled",
        "source_rewrite_enabled",
        "token_persistence_enabled",
        "tool_execution_allowed",
        "v02_release_created",
        "v02_release_ready",
        "v02_tag_created",
    }
    for key in false_keys:
        if key in payload and payload.get(key) is not False:
            raise SystemExit(f"secure runtime integration flag must be false: {key}: {path}")

    if path.name == "secure-runtime-integration-authorization.json":
        for key in (
            "authorization_active",
            "sole_active_sri_authorization",
        ):
            if payload.get(key) is not True:
                raise SystemExit(f"secure runtime integration authorization flag must be true: {key}: {path}")
        for key in (
            "authorization_consumed",
            "authorization_expired",
            "authorization_reusable",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"secure runtime integration authorization flag must be false: {key}: {path}")
        if payload.get("implementation_task") != "AION-231":
            raise SystemExit(f"secure runtime integration implementation task mismatch: {path}")
        if payload.get("formal_closeout_task") != "AION-232":
            raise SystemExit(f"secure runtime integration closeout task mismatch: {path}")
    elif path.name == "secure-runtime-integration-program.json":
        if payload.get("active_sri_implementation_authorization_count") != 1:
            raise SystemExit(f"secure runtime integration active authorization count mismatch: {path}")
        if payload.get("active_sri_implementation_authorization") != "AION-230-SRI-0001":
            raise SystemExit(f"secure runtime integration active authorization mismatch: {path}")
        if payload.get("active_sri_implementation_task") != "AION-231":
            raise SystemExit(f"secure runtime integration active task mismatch: {path}")
    elif path.name == "secure-runtime-integration-runtime-guard.json":
        if payload.get("guard_result") != "allow_simulated_dispatch_only":
            raise SystemExit(f"secure runtime integration guard result mismatch: {path}")
    elif path.name == "secure-runtime-integration-runtime-hold.json":
        if payload.get("runtime_hold_active") is not True:
            raise SystemExit(f"secure runtime integration runtime hold must be active: {path}")
    elif path.name == "secure-runtime-integration-session.json":
        if payload.get("implementation_task") != "AION-231":
            raise SystemExit(f"secure runtime integration session task mismatch: {path}")


for path in sorted(demo_dir.glob("*.json")):
    payload = json.loads(path.read_text())
    if path.name.startswith("secure-runtime-integration-"):
        validate_secure_runtime_integration_demo(payload, path)
        continue
    if path.name == "secure-runtime-foundation-operator-evaluation.json":
        if payload.get("read_only") is not True:
            raise SystemExit(f"operator evaluation demo must be read_only: {path}")
        if payload.get("redacted") is not True:
            raise SystemExit(f"operator evaluation demo must be redacted: {path}")
        if payload.get("synthetic") is not True:
            raise SystemExit(f"operator evaluation demo must be synthetic: {path}")
        for key in (
            "network_calls",
            "model_provider_calls",
            "connector_calls",
            "actual_tool_executions",
            "credentials_persisted",
            "tokens_persisted",
            "production_writes",
            "source_mutations",
            "git_operations",
            "deployments",
            "model_weight_changes",
        ):
            if payload.get(key) != 0:
                raise SystemExit(f"operator evaluation demo counter must be zero: {key}: {path}")
        continue
    if path.name.startswith("model-gateway-"):
        allowed_names = {
            "model-gateway-audit.json",
            "model-gateway-authorization.json",
            "model-gateway-budget.json",
            "model-gateway-circuit-breaker.json",
            "model-gateway-component-binding.json",
            "model-gateway-fallback-plan.json",
            "model-gateway-guard.json",
            "model-gateway-health.json",
            "model-gateway-integrity.json",
            "model-gateway-message-normalization.json",
            "model-gateway-model-manifests.json",
            "model-gateway-observability.json",
            "model-gateway-output-provenance.json",
            "model-gateway-output-validation.json",
            "model-gateway-pilot-evidence.json",
            "model-gateway-provider-manifest.json",
            "model-gateway-reference-provider-response.json",
            "model-gateway-retry-plan.json",
            "model-gateway-routing-plan.json",
            "model-gateway-runtime-boundary.json",
            "model-gateway-runtime-hold.json",
            "model-gateway-session-plan.json",
            "model-gateway-static-console-evidence.json",
        }
        if path.name not in allowed_names:
            raise SystemExit(f"unknown model gateway demo: {path}")
        if payload.get("program_id") != "AION-SECURE-RUNTIME-INTEGRATION-001":
            raise SystemExit(f"model gateway demo program id mismatch: {path}")
        if payload.get("read_only") is not True:
            raise SystemExit(f"model gateway demo must be read_only: {path}")
        redaction_applied = payload.get("redaction_applied")
        redacted = payload.get("redacted")
        if redaction_applied is not True and redacted is not True:
            raise SystemExit(f"model gateway demo must be redacted: {path}")
        if payload.get("synthetic") is not True:
            raise SystemExit(f"model gateway demo must be synthetic: {path}")
        for key in (
            "actual_model_provider_call_enabled",
            "actual_tool_execution_enabled",
            "api_key_persistence_enabled",
            "connector_execution_enabled",
            "function_calling_enabled",
            "live_model_session_enabled",
            "model_response_persistence_enabled",
            "production_runtime_authorized",
            "provider_credential_persistence_enabled",
            "provider_credential_read_enabled",
            "provider_network_egress_enabled",
            "provider_sdk_enabled",
            "public_model_api_route_enabled",
            "public_network_access_enabled",
            "runtime_effect",
            "shell_command_execution_enabled",
            "source_rewrite_enabled",
            "subprocess_execution_enabled",
            "token_persistence_enabled",
            "tool_calling_enabled",
            "v02_release_created",
            "v02_release_ready",
            "v02_tag_created",
        ):
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"model gateway demo flag must be false: {key}: {path}")
        continue
    if path.name.startswith("action-authorization-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"action authorization demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"action authorization demo must be redacted: {path}")
        for key in (
            "write_allowed",
            "execution_allowed",
            "activation_allowed",
            "external_calls_allowed",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"action authorization demo flag must be false: {key}: {path}")
        if payload.get("dry_run_only") is not True:
            raise SystemExit(f"action authorization demo must be dry_run_only: {path}")
        continue
    if path.name.startswith("offline-identity-assertion-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"offline identity assertion demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"offline identity assertion demo must be redacted: {path}")
        false_keys = {
            "actor_context_applied",
            "authorization_header_parsing_enabled",
            "cli_runtime_command_added",
            "connector_runtime_enabled",
            "cookie_parsing_enabled",
            "external_calls_enabled",
            "external_identity_provider_enabled",
            "identity_assertion_endpoint_enabled",
            "identity_assertion_header_parsing_enabled",
            "identity_assertion_middleware_registered",
            "lockfiles_added",
            "migrations_added",
            "module_activation_enabled",
            "new_package_manifest_added",
            "openapi_security_scheme_added",
            "operator_write_execution_enabled",
            "replay_check_performed",
            "request_authenticated",
            "request_identity_context_applied",
            "runtime_api_routes_added",
            "runtime_effect",
            "runtime_integration_allowed",
            "runtime_private_key_material_present",
            "sandbox_execution_enabled",
            "sdk_runtime_resource_added",
            "v02_release_created",
            "v02_tag_created",
        }
        for key in false_keys:
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"offline identity assertion demo flag must be false: {key}: {path}")
        continue
    if path.name.startswith("identity-assertion-replay-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"identity assertion replay demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"identity assertion replay demo must be redacted: {path}")
        false_keys = {
            "actor_context_applied",
            "background_cleanup_scheduler_enabled",
            "cli_runtime_command_added",
            "external_calls_enabled",
            "identity_assertion_endpoint_enabled",
            "in_memory_runtime_replay_store_enabled",
            "kernel_container_registration_enabled",
            "migrations_added",
            "middleware_integration_enabled",
            "openapi_security_scheme_added",
            "production_auth_runtime_enabled",
            "replay_protection_core_runtime_enabled",
            "replay_repository_runtime_registered",
            "request_authenticated",
            "request_identity_context_applied",
            "request_integration_enabled",
            "runtime_api_routes_added",
            "runtime_effect",
            "runtime_integration_allowed",
            "sdk_runtime_resource_added",
            "v02_release_created",
            "v02_tag_created",
        }
        for key in false_keys:
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"identity assertion replay demo flag must be false: {key}: {path}")
        continue
    if path.name.startswith("local-session-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"local session demo must be read_only: {path}")
        for key in (
            "production_session",
            "credential_backed",
            "token_issued",
            "cookie_issued",
            "persistent",
            "write_allowed",
            "execute_allowed",
            "activation_allowed",
            "external_calls_allowed",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"local session demo flag must be false: {key}: {path}")
        continue
    if path.name.startswith("auth-runtime-") or path.name.startswith("mock-claims-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"auth runtime demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"auth runtime demo must be redacted: {path}")
        for key in (
            "production_auth_enabled",
            "auth_runtime_enabled",
            "external_identity_provider_enabled",
            "credentials_enabled",
            "token_issuance_enabled",
            "cookie_issuance_enabled",
            "session_persistence_enabled",
            "login_endpoint_enabled",
            "logout_endpoint_enabled",
            "production_identity",
            "credentials_present",
            "token_present",
            "cookie_present",
            "session_persisted",
            "write_allowed",
            "execute_allowed",
            "activation_allowed",
            "external_calls_allowed",
        ):
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"auth runtime demo flag must be false: {key}: {path}")
        continue
    if path.name.startswith("production-auth-request-identity-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"request identity demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"request identity demo must be redacted: {path}")
        for key in (
            "request_identity_boundary_default_enabled",
            "identity_verification_enabled",
            "authenticated_requests_enabled",
            "production_auth_runtime_enabled",
            "runtime_effect",
            "runtime_implementation_approved",
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
            "runtime_api_routes_added",
            "package_files_added",
            "lockfiles_added",
            "migrations_added",
            "v02_tag_created",
            "v02_release_created",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"request identity demo flag must be false: {key}: {path}")
        continue
    if path.name in {
        "v02-actor-context-trust-boundary-authorization.json",
        "v02-identity-assertion-replay-protection-authorization.json",
        "v02-offline-identity-assertion-verification-authorization.json",
        "v02-production-auth-request-identity-stabilization-authorization.json",
    }:
        if payload.get("read_only") is not True:
            raise SystemExit(f"authorization demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"authorization demo must be redacted: {path}")
        false_keys = {
            "authenticated_actor_context_enabled",
            "authenticated_requests_enabled",
            "authorization_header_parsing_approved",
            "callback_endpoint_approved",
            "cli_runtime_command_added",
            "connector_implementation_approved",
            "connector_runtime_enabled",
            "cookie_issuance_approved",
            "cookie_parsing_approved",
            "cookie_session_persistence_approved",
            "credential_endpoint_approved",
            "credential_storage_approved",
            "credential_verification_approved",
            "external_calls_approved",
            "external_identity_provider_approved",
            "identity_verification_enabled",
            "lockfiles_added",
            "login_endpoint_approved",
            "logout_endpoint_approved",
            "migrations_added",
            "module_activation_approved",
            "network_client_approved",
            "non_development_identity_header_trust_enabled",
            "oauth_runtime_approved",
            "oidc_runtime_approved",
            "openapi_security_scheme_added",
            "operator_write_execution_approved",
            "package_files_added",
            "password_storage_approved",
            "password_verification_approved",
            "production_actor_header_trust_enabled",
            "production_auth_runtime_enabled",
            "production_identity_header_trust_approved",
            "production_permission_header_trust_enabled",
            "production_role_header_trust_enabled",
            "production_security_scope_header_trust_enabled",
            "protected_material_handling_approved",
            "provider_runtime_approved",
            "provider_sdk_approved",
            "runtime_api_routes_added",
            "runtime_effect",
            "runtime_implementation_approved",
            "saml_runtime_approved",
            "sandbox_execution_approved",
            "sdk_runtime_resource_added",
            "session_creation_approved",
            "session_endpoint_approved",
            "session_storage_approved",
            "token_endpoint_approved",
            "token_issuance_approved",
            "token_parsing_approved",
            "token_refresh_approved",
            "token_storage_approved",
            "v02_release_created",
            "v02_tag_created",
        }
        for key in false_keys:
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"authorization demo flag must be false: {key}: {path}")
        continue
    if path.name.startswith("self-improvement-shadow-mode-"):
        if path.name not in {
            "self-improvement-shadow-mode-authorization.json",
            "self-improvement-shadow-mode-plane.json",
            "self-improvement-shadow-mode-review-items.json",
            "self-improvement-shadow-mode-runtime-hold.json",
            "self-improvement-shadow-mode-operator-evaluation.json",
            "self-improvement-shadow-mode-activation-review-boundary.json",
        }:
            raise SystemExit(f"unknown self-improvement shadow-mode demo: {path}")
        if payload.get("read_only") is not True:
            raise SystemExit(f"self-improvement shadow-mode demo must be read_only: {path}")
        redaction_applied = payload.get("redaction_applied")
        redacted = payload.get("redacted")
        if redaction_applied is not True and redacted is not True:
            raise SystemExit(f"self-improvement shadow-mode demo must be redacted: {path}")
        if path.name == "self-improvement-shadow-mode-authorization.json":
            if payload.get("shadow_mode_implemented") is not False:
                raise SystemExit(f"shadow_mode_implemented must be false: {path}")
        else:
            if payload.get("shadow_mode_implemented") is not True:
                raise SystemExit(f"shadow_mode_implemented must be true: {path}")
            if payload.get("shadow_mode_implementation_state") != "implemented_operator_invoked_disabled":
                raise SystemExit(f"shadow implementation state mismatch: {path}")
        if payload.get("shadow_mode_runtime_enabled") is not False:
            raise SystemExit(f"shadow_mode_runtime_enabled must be false: {path}")
        allowed_true_keys = {
            "synthetic",
            "read_only",
            "redacted",
            "redaction_applied",
            "shadow_mode_authorized",
            "shadow_mode",
            "shadow_mode_implemented",
            "shadow_only",
            "operator_review_required",
            "operator_invoked_shadow_runs_supported",
            "operator_invoked_batch_runner_available",
            "required_source_files_present",
        }
        blocked_true_markers = (
            "_enabled",
            "_approved",
            "_allowed",
            "_created",
            "_added",
            "_present",
            "_mutated",
            "_mutation",
            "_training",
            "_deployment",
            "_canary",
            "_merge",
            "_push",
            "_execution",
            "_effect",
        )
        for key, value in payload.items():
            normalized = key.lower()
            if (
                isinstance(value, bool)
                and value is True
                and normalized not in allowed_true_keys
                and any(marker in normalized for marker in blocked_true_markers)
            ):
                raise SystemExit(
                    f"self-improvement shadow-mode flag must not be true: {key}: {path}"
                )
        continue
    if path.name.startswith("self-improvement-shadow-activation-"):
        if path.name not in {
            "self-improvement-shadow-activation-authorization.json",
            "self-improvement-shadow-activation-control-plane.json",
            "self-improvement-shadow-activation-control-plane-evaluation.json",
            "self-improvement-shadow-activation-runtime-hold.json",
            "self-improvement-shadow-activation-simulation.json",
        }:
            raise SystemExit(f"unknown self-improvement shadow-activation demo: {path}")
        if payload.get("read_only") is not True:
            raise SystemExit(f"self-improvement shadow-activation demo must be read_only: {path}")
        redaction_applied = payload.get("redaction_applied")
        redacted = payload.get("redacted")
        if redaction_applied is not True and redacted is not True:
            raise SystemExit(f"self-improvement shadow-activation demo must be redacted: {path}")
        if payload.get("shadow_activation_control_plane_authorized") is not True:
            raise SystemExit(f"shadow activation control plane must be authorized: {path}")
        implemented_payloads = {
            "self-improvement-shadow-activation-control-plane.json",
            "self-improvement-shadow-activation-control-plane-evaluation.json",
            "self-improvement-shadow-activation-runtime-hold.json",
            "self-improvement-shadow-activation-simulation.json",
        }
        if path.name in implemented_payloads:
            if payload.get("shadow_activation_control_plane_implemented") is not True:
                raise SystemExit(f"shadow activation control plane must be implemented-disabled: {path}")
            if payload.get("shadow_activation_control_plane_state") != "implemented_disabled_simulation_only":
                raise SystemExit(f"shadow activation control plane state mismatch: {path}")
        elif payload.get("shadow_activation_control_plane_implemented") is not False:
            raise SystemExit(f"shadow activation control plane must remain unimplemented: {path}")
        for key in (
            "shadow_activation_enabled",
            "shadow_mode_runtime_enabled",
            "runtime_effect",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"self-improvement shadow-activation flag must be false: {key}: {path}")
        for key in (
            "network_calls_enabled",
            "connector_calls_enabled",
            "provider_calls_enabled",
            "source_mutation_enabled",
            "git_mutation_enabled",
            "real_pull_request_creation_enabled",
            "approval_creation_enabled",
            "automatic_merge_enabled",
            "production_canary_enabled",
            "production_deployment_enabled",
            "model_weight_training_enabled",
            "v02_tag_created",
            "v02_release_created",
        ):
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"self-improvement shadow-activation flag must be false: {key}: {path}")
        continue
    if path.name == "self-improvement-actual-shadow-activation-review-boundary.json":
        if payload.get("read_only") is not True:
            raise SystemExit(f"actual shadow activation review boundary must be read_only: {path}")
        redaction_applied = payload.get("redaction_applied")
        redacted = payload.get("redacted")
        if redaction_applied is not True and redacted is not True:
            raise SystemExit(f"actual shadow activation review boundary must be redacted: {path}")
        for key in (
            "activation_approval_created",
            "actual_activation_authorized",
            "actual_activation_created",
            "connector_calls_allowed",
            "deployment_allowed",
            "evaluation_reusable",
            "evaluation_used_as_approval",
            "git_write_allowed",
            "merge_allowed",
            "model_training_allowed",
            "new_implementation_authorization_created",
            "provider_calls_allowed",
            "pull_request_creation_allowed",
            "runtime_enablement_allowed",
            "shadow_activation_enabled",
            "shadow_mode_runtime_enabled",
            "source_mutation_allowed",
            "synthetic_approval_evidence_is_real_approval",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"actual shadow activation boundary flag must be false: {key}: {path}")
        if payload.get("next_authorization_required") is not True:
            raise SystemExit(f"actual shadow activation review must require future authorization: {path}")
        if payload.get("next_authorization_must_be_separate") is not True:
            raise SystemExit(f"actual shadow activation review must require separate authorization: {path}")
        continue
    if path.name.startswith("knowledge-intelligence-domain-expert-"):
        validate_domain_expert_demo(payload, path)
        continue
    if path.name.startswith("knowledge-intelligence-tool-"):
        validate_tool_verification_demo(payload, path)
        continue
    if path.name.startswith("knowledge-intelligence-"):
        if path.name not in {
            "knowledge-intelligence-program.json",
            "knowledge-intelligence-program-complete.json",
            "knowledge-intelligence-program-final-capabilities.json",
            "knowledge-intelligence-program-final-evaluation.json",
            "knowledge-intelligence-program-final-runtime-boundary.json",
            "knowledge-intelligence-research-authorization.json",
            "knowledge-intelligence-research-evaluation.json",
            "knowledge-intelligence-research-plane.json",
            "knowledge-intelligence-research-runtime-hold.json",
            "knowledge-intelligence-source-registry-authorization.json",
            "knowledge-intelligence-source-registry.json",
            "knowledge-intelligence-source-registry-index.json",
            "knowledge-intelligence-source-registry-integrity.json",
            "knowledge-intelligence-source-registry-runtime-hold.json",
            "knowledge-intelligence-source-registry-evaluation.json",
            "knowledge-intelligence-claim-graph-authorization.json",
            "knowledge-intelligence-claim-graph.json",
            "knowledge-intelligence-claim-graph-index.json",
            "knowledge-intelligence-claim-graph-integrity.json",
            "knowledge-intelligence-claim-graph-conflict-candidates.json",
            "knowledge-intelligence-claim-graph-evaluation.json",
            "knowledge-intelligence-claim-graph-runtime-hold.json",
            "knowledge-intelligence-epistemic-assessment.json",
            "knowledge-intelligence-epistemic-hard-caps.json",
            "knowledge-intelligence-epistemic-integrity.json",
            "knowledge-intelligence-epistemic-runtime-hold.json",
            "knowledge-intelligence-epistemic-scorecard.json",
            "knowledge-intelligence-epistemic-truth-authorization.json",
            "knowledge-intelligence-epistemic-assessment-evaluation.json",
            "knowledge-intelligence-domain-expert-mesh-authorization.json",
            "knowledge-intelligence-domain-expert-mesh-budget.json",
            "knowledge-intelligence-domain-expert-mesh-disagreement.json",
            "knowledge-intelligence-domain-expert-mesh-panel-policy.json",
            "knowledge-intelligence-domain-expert-mesh-panel.json",
            "knowledge-intelligence-domain-expert-mesh-runtime-hold.json",
            "knowledge-intelligence-engagement-learning-candidate.json",
            "knowledge-intelligence-engagement-learning-candidates.json",
            "knowledge-intelligence-engagement-signals.json",
            "knowledge-intelligence-integrated-lineage.json",
            "knowledge-intelligence-integrated-research-agent-evaluation.json",
            "knowledge-intelligence-verified-candidate-integrity.json",
            "knowledge-intelligence-verified-candidate-refutation.json",
            "knowledge-intelligence-verified-candidate-revalidation.json",
            "knowledge-intelligence-verified-candidate-support.json",
            "knowledge-intelligence-verified-candidate-versioning.json",
            "knowledge-intelligence-source-lineage.json",
            "knowledge-intelligence-source-snapshots.json",
            "knowledge-intelligence-verified-knowledge-authorization.json",
            "knowledge-intelligence-verified-knowledge-candidate.json",
            "knowledge-intelligence-verified-knowledge-runtime-hold.json",
            "knowledge-intelligence-verified-knowledge-versioning.json",
            "knowledge-intelligence-verified-memory-evaluation.json",
            "knowledge-intelligence-verified-memory-runtime-hold.json",
            "knowledge-intelligence-verified-memory.json",
            "knowledge-intelligence-public-research-pilot-authorization.json",
            "knowledge-intelligence-public-research-pilot-dns.json",
            "knowledge-intelligence-public-research-pilot-http.json",
            "knowledge-intelligence-public-research-pilot-implementation.json",
            "knowledge-intelligence-public-research-pilot-integrity.json",
            "knowledge-intelligence-public-research-pilot-lineage.json",
            "knowledge-intelligence-public-research-pilot-live-evidence.json",
            "knowledge-intelligence-public-research-pilot-network-policy.json",
            "knowledge-intelligence-public-research-pilot-resource-budget.json",
            "knowledge-intelligence-public-research-pilot-result.json",
            "knowledge-intelligence-public-research-pilot-runtime-hold.json",
        }:
            raise SystemExit(f"unknown knowledge intelligence demo: {path}")
        if payload.get("read_only") is not True:
            raise SystemExit(f"knowledge intelligence demo must be read_only: {path}")
        redaction_applied = payload.get("redaction_applied")
        redacted = payload.get("redacted")
        if redaction_applied is not True and redacted is not True:
            raise SystemExit(f"knowledge intelligence demo must be redacted: {path}")
        implemented_disabled_plane_present = any(
            payload.get(key) is True
            for key in (
                "research_plane_implemented",
                "source_provenance_registry_implemented",
                "temporal_claim_evidence_graph_implemented",
                "epistemic_truth_engine_implemented",
                "domain_expert_mesh_implemented",
                "tool_verification_fabric_implemented",
                "verified_knowledge_memory_authorized",
                "verified_knowledge_memory_implemented",
                "controlled_public_research_pilot_authorized",
                "controlled_public_research_pilot_passed",
                "engagement_learning_candidate_plane_implemented",
                "knowledge_intelligence_program_complete",
            )
        )
        read_only_evidence_marker_present = (
            payload.get("evaluation_passed") is True
            or payload.get("all_hard_gates_passed") is True
            or payload.get("evaluation_id") == "AION-KIPE-001"
            or payload.get("program_state") == "knowledge_intelligence_program_complete"
            or payload.get("dns_pinning_required") is True
            or payload.get("explicit_allowlist_required") is True
            or payload.get("operator_invoked_public_https_fetch_authorized") is True
            or isinstance(payload.get("resource_limits"), dict)
            or path.name.startswith("knowledge-intelligence-public-research-pilot-")
        )
        if not implemented_disabled_plane_present and not read_only_evidence_marker_present:
            raise SystemExit(f"knowledge intelligence demo marker missing: {path}")
        for key in (
            "research_runtime_enabled",
            "source_registry_runtime_enabled",
            "claim_graph_runtime_enabled",
            "epistemic_truth_engine_runtime_enabled",
            "persistent_assessment_write_enabled",
            "network_access_enabled",
            "runtime_effect",
        ):
            if payload.get(key, False) is not False:
                raise SystemExit(f"knowledge intelligence runtime flag must be false: {key}: {path}")
        runtime_hold = payload.get("runtime_hold", {})
        if isinstance(runtime_hold, dict):
            for key, value in runtime_hold.items():
                if value is not False:
                    raise SystemExit(f"knowledge intelligence hold flag must be false: {key}: {path}")
        continue
    if path.name.startswith("governed-learning-memory-"):
        if path.name not in {
            "governed-learning-memory-authorization.json",
            "governed-learning-memory-boundary.json",
            "governed-learning-memory-approval-evidence.json",
            "governed-learning-memory-conflicts.json",
            "governed-learning-memory-eligibility.json",
            "governed-learning-memory-engagement-application-authorization.json",
            "governed-learning-memory-engagement-evaluation.json",
            "governed-learning-memory-continual-learning-authorization.json",
            "governed-learning-memory-continual-learning-authorization-envelope.json",
            "governed-learning-memory-continual-learning-candidate-binding.json",
            "governed-learning-memory-continual-learning-cross-cycle-context.json",
            "governed-learning-memory-continual-learning-cycle.json",
            "governed-learning-memory-continual-learning-cycle-outcomes.json",
            "governed-learning-memory-continual-learning-cycle-plans.json",
            "governed-learning-memory-continual-learning-evidence-bundle.json",
            "governed-learning-memory-continual-learning-integrity-report.json",
            "governed-learning-memory-continual-learning-live-pilot-evidence.json",
            "governed-learning-memory-continual-learning-outcome.json",
            "governed-learning-memory-continual-learning-persistence-binding.json",
            "governed-learning-memory-continual-learning-persistence.json",
            "governed-learning-memory-continual-learning-promotion-binding.json",
            "governed-learning-memory-continual-learning-research-binding.json",
            "governed-learning-memory-continual-learning-research.json",
            "governed-learning-memory-continual-learning-runtime-boundary.json",
            "governed-learning-memory-continual-learning-runtime-hold.json",
            "governed-learning-memory-continual-learning-session-plan.json",
            "governed-learning-memory-continual-learning-session-result.json",
            "governed-learning-memory-continual-learning-shadow-binding.json",
            "governed-learning-memory-continual-learning-shadow.json",
            "governed-learning-memory-continual-learning-stage-command.json",
            "governed-learning-memory-continual-learning-stage-receipt.json",
            "governed-learning-memory-engagement-adaptation-identity.json",
            "governed-learning-memory-engagement-application-plan.json",
            "governed-learning-memory-engagement-application-result.json",
            "governed-learning-memory-engagement-approval-bundle.json",
            "governed-learning-memory-engagement-authorization.json",
            "governed-learning-memory-engagement-baseline-snapshot.json",
            "governed-learning-memory-engagement-candidate-binding.json",
            "governed-learning-memory-engagement-conflict-report.json",
            "governed-learning-memory-engagement-counterfactual-result.json",
            "governed-learning-memory-engagement-counterfactual.json",
            "governed-learning-memory-engagement-integrity-report.json",
            "governed-learning-memory-engagement-integrity.json",
            "governed-learning-memory-engagement-lifecycle-evidence.json",
            "governed-learning-memory-engagement-metric-delta.json",
            "governed-learning-memory-engagement-overlay-record.json",
            "governed-learning-memory-engagement-overlay-snapshot.json",
            "governed-learning-memory-engagement-overlay.json",
            "governed-learning-memory-engagement-risk-assessment.json",
            "governed-learning-memory-engagement-risk-policy.json",
            "governed-learning-memory-engagement-rollback-plan.json",
            "governed-learning-memory-engagement-runtime-boundary.json",
            "governed-learning-memory-engagement-runtime-hold.json",
            "governed-learning-memory-engagement-synthetic-pilot.json",
            "governed-learning-memory-engagement-target-policy.json",
            "governed-learning-memory-engagement-version-plan.json",
            "governed-learning-memory-integrity.json",
            "governed-learning-memory-knowledge-identity.json",
            "governed-learning-memory-local-persistence-approval.json",
            "governed-learning-memory-local-persistence-authorization.json",
            "governed-learning-memory-local-persistence-evaluation.json",
            "governed-learning-memory-local-persistence-integrity.json",
            "governed-learning-memory-local-persistence-projection.json",
            "governed-learning-memory-local-persistence-runtime-hold.json",
            "governed-learning-memory-local-persistence-schema.json",
            "governed-learning-memory-local-persistence-version.json",
            "governed-learning-memory-projection-plan.json",
            "governed-learning-memory-program.json",
            "governed-learning-memory-program-final-authorization-closeout.json",
            "governed-learning-memory-program-final-capability-matrix.json",
            "governed-learning-memory-program-final-closeout.json",
            "governed-learning-memory-program-final-evaluation.json",
            "governed-learning-memory-program-final-lineage.json",
            "governed-learning-memory-program-final-runtime-boundary.json",
            "governed-learning-memory-promotion-evaluation.json",
            "governed-learning-memory-promotion-request.json",
            "governed-learning-memory-roadmap.json",
            "governed-learning-memory-runtime-hold.json",
            "governed-learning-memory-transaction-result.json",
            "governed-learning-memory-version-plan.json",
        }:
            raise SystemExit(f"unknown governed learning memory demo: {path}")
        if payload.get("read_only") is not True:
            raise SystemExit(f"governed learning memory demo must be read_only: {path}")
        redaction_applied = payload.get("redaction_applied")
        redacted = payload.get("redacted")
        if redaction_applied is not True and redacted is not True:
            raise SystemExit(f"governed learning memory demo must be redacted: {path}")
        if payload.get("synthetic") is not True:
            raise SystemExit(f"governed learning memory demo must be synthetic: {path}")
        if payload.get("program_id") != "AION-GOVERNED-LEARNING-MEMORY-001":
            raise SystemExit(f"governed learning memory program id mismatch: {path}")
        for key in (
            "actual_knowledge_promotion_enabled",
            "actual_tool_execution_enabled",
            "automatic_knowledge_promotion_enabled",
            "automatic_memory_ingestion_enabled",
            "background_learning_enabled",
            "cognitive_belief_creation_enabled",
            "cognitive_belief_mutation_enabled",
            "cognitive_memory_write_enabled",
            "engagement_confidence_effect_enabled",
            "engagement_factual_effect_enabled",
            "episodic_memory_write_enabled",
            "external_calls_enabled",
            "model_provider_integration_enabled",
            "network_calls_enabled",
            "persistent_knowledge_write_enabled",
            "persistent_verified_knowledge_write_enabled",
            "procedural_memory_write_enabled",
            "production_deployment_enabled",
            "production_exposure",
            "public_network_access_enabled",
            "runtime_enabled",
            "runtime_effect",
            "runtime_source_rewrite_enabled",
            "scheduled_learning_enabled",
            "semantic_memory_write_enabled",
            "source_mutation_enabled",
            "v02_release_created",
            "v02_tag_created",
        ):
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"governed learning memory flag must be false: {key}: {path}")
        continue
    if payload.get("read_only") is not True:
        raise SystemExit(f"read_only must be true: {path}")
    if payload.get("redaction_applied") is not True:
        raise SystemExit(f"redaction_applied must be true: {path}")
    for key in ("status", "sections", "blockers", "warnings", "refs"):
        if key not in payload and not any(key in section for section in payload.get("sections", [])):
            raise SystemExit(f"missing {key}: {path}")
    actions = {item.get("action_key") for item in payload.get("forbidden_actions", [])}
    if actions != required_actions:
        raise SystemExit(f"forbidden actions mismatch: {path}")
    serialized = json.dumps(payload, sort_keys=True).lower()
    allowed_authorization_demo_names = {
        "v02-implementation-authorization-preview.json",
        "v02-runtime-enablement-guard-boundary.json",
        "v02-implementation-authorization-stabilization.json",
        "v02-explicit-approval-record-freeze.json",
        "v02-implementation-authorization-final-review.json",
        "v02-runtime-enablement-guard-final-lock.json",
        "v02-authorization-track-closeout.json",
        "v02-runtime-enablement-master-lock.json",
        "v02-production-auth-authorization.json",
        "v02-production-auth-runtime-guard-hold.json",
        "v02-production-auth-core-implementation-closeout.json",
        "v02-production-auth-stabilization-authorization.json",
        "v02-production-auth-request-boundary-authorization.json",
        "v02-production-auth-request-identity-stabilization-authorization.json",
        "v02-actor-context-trust-boundary-authorization.json",
        "self-improvement-shadow-mode-authorization.json",
        "self-improvement-shadow-mode-activation-review-boundary.json",
        "self-improvement-actual-shadow-activation-review-boundary.json",
        "self-improvement-shadow-activation-authorization.json",
        "self-improvement-shadow-activation-control-plane.json",
        "self-improvement-shadow-activation-control-plane-evaluation.json",
        "self-improvement-shadow-activation-runtime-hold.json",
        "self-improvement-shadow-activation-simulation.json",
        "production-auth-core-status.json",
        "production-auth-runtime-hold.json",
        "production-auth-core-stabilization.json",
        "production-auth-core-stabilization-runtime-hold.json",
        "production-auth-request-identity-boundary.json",
        "production-auth-request-identity-runtime-hold.json",
        "actor-context-trust-boundary.json",
        "actor-context-runtime-hold.json",
        "knowledge-intelligence-domain-expert-mesh-authorization.json",
        "governed-learning-memory-local-persistence-approval.json",
        "governed-learning-memory-local-persistence-authorization.json",
        "governed-learning-memory-local-persistence-integrity.json",
        "governed-learning-memory-local-persistence-projection.json",
        "governed-learning-memory-local-persistence-runtime-hold.json",
        "governed-learning-memory-local-persistence-schema.json",
        "governed-learning-memory-local-persistence-version.json",
        "governed-learning-memory-promotion-evaluation.json",
        "governed-learning-memory-engagement-adaptation-identity.json",
        "governed-learning-memory-engagement-application-authorization.json",
        "governed-learning-memory-engagement-evaluation.json",
        "governed-learning-memory-continual-learning-authorization.json",
        "governed-learning-memory-continual-learning-authorization-envelope.json",
        "governed-learning-memory-continual-learning-candidate-binding.json",
        "governed-learning-memory-continual-learning-cross-cycle-context.json",
        "governed-learning-memory-continual-learning-cycle.json",
        "governed-learning-memory-continual-learning-cycle-outcomes.json",
        "governed-learning-memory-continual-learning-cycle-plans.json",
        "governed-learning-memory-continual-learning-evidence-bundle.json",
        "governed-learning-memory-continual-learning-integrity-report.json",
        "governed-learning-memory-continual-learning-live-pilot-evidence.json",
        "governed-learning-memory-continual-learning-outcome.json",
        "governed-learning-memory-continual-learning-persistence-binding.json",
        "governed-learning-memory-continual-learning-persistence.json",
        "governed-learning-memory-continual-learning-promotion-binding.json",
        "governed-learning-memory-continual-learning-research-binding.json",
        "governed-learning-memory-continual-learning-research.json",
        "governed-learning-memory-continual-learning-runtime-boundary.json",
        "governed-learning-memory-continual-learning-runtime-hold.json",
        "governed-learning-memory-continual-learning-session-plan.json",
        "governed-learning-memory-continual-learning-session-result.json",
        "governed-learning-memory-continual-learning-shadow-binding.json",
        "governed-learning-memory-continual-learning-shadow.json",
        "governed-learning-memory-continual-learning-stage-command.json",
        "governed-learning-memory-continual-learning-stage-receipt.json",
        "governed-learning-memory-engagement-application-plan.json",
        "governed-learning-memory-engagement-application-result.json",
        "governed-learning-memory-engagement-approval-bundle.json",
        "governed-learning-memory-engagement-authorization.json",
        "governed-learning-memory-engagement-baseline-snapshot.json",
        "governed-learning-memory-engagement-candidate-binding.json",
        "governed-learning-memory-engagement-conflict-report.json",
        "governed-learning-memory-engagement-counterfactual-result.json",
        "governed-learning-memory-engagement-counterfactual.json",
        "governed-learning-memory-engagement-integrity-report.json",
        "governed-learning-memory-engagement-integrity.json",
        "governed-learning-memory-engagement-lifecycle-evidence.json",
        "governed-learning-memory-engagement-metric-delta.json",
        "governed-learning-memory-engagement-overlay-record.json",
        "governed-learning-memory-engagement-overlay-snapshot.json",
        "governed-learning-memory-engagement-overlay.json",
        "governed-learning-memory-engagement-risk-assessment.json",
        "governed-learning-memory-engagement-risk-policy.json",
        "governed-learning-memory-engagement-rollback-plan.json",
        "governed-learning-memory-engagement-runtime-boundary.json",
        "governed-learning-memory-engagement-runtime-hold.json",
        "governed-learning-memory-engagement-synthetic-pilot.json",
        "governed-learning-memory-engagement-target-policy.json",
        "governed-learning-memory-engagement-version-plan.json",
        "governed-learning-memory-program-final-authorization-closeout.json",
        "governed-learning-memory-program-final-capability-matrix.json",
        "governed-learning-memory-program-final-closeout.json",
        "governed-learning-memory-program-final-evaluation.json",
        "governed-learning-memory-program-final-lineage.json",
        "governed-learning-memory-program-final-runtime-boundary.json",
    }
    blocked = (
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
        "password",
        "api_key",
        "private_key",
        "authorization",
        "bearer ",
        "sk-",
        "ghp_",
        "xoxb-",
    )
    for value in blocked:
        if value == "authorization" and path.name in allowed_authorization_demo_names:
            continue
        if value == "password" and path.name in {
            "v02-production-auth-authorization.json",
            "v02-production-auth-runtime-guard-hold.json",
            "v02-production-auth-core-implementation-closeout.json",
            "v02-production-auth-stabilization-authorization.json",
            "v02-production-auth-request-boundary-authorization.json",
            "v02-production-auth-request-identity-stabilization-authorization.json",
            "v02-actor-context-trust-boundary-authorization.json",
            "production-auth-core-status.json",
            "production-auth-runtime-hold.json",
            "production-auth-core-stabilization.json",
            "production-auth-core-stabilization-runtime-hold.json",
            "production-auth-request-identity-boundary.json",
            "production-auth-request-identity-runtime-hold.json",
            "actor-context-trust-boundary.json",
            "actor-context-runtime-hold.json",
        }:
            continue
        if value in serialized:
            raise SystemExit(f"unsafe demo content: {path}")

changed = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
untracked = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
blocked_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
blocked_prefixes = (
    "vite.config.",
    "next.config.",
    "tailwind.config.",
    "webpack.config.",
)
for name in [*changed, *untracked]:
    basename = Path(name).name
    if basename in blocked_names or any(basename.startswith(prefix) for prefix in blocked_prefixes):
        raise SystemExit(f"frontend package or build file changed: {name}")

print("Static console JSON and artifact checks PASS")
PY

echo "Operator console static check PASS"

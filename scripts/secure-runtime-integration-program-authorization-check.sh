#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

root = Path(os.environ["AION_REPO_ROOT"])

PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
PROGRAM_STATE = "controlled_model_gateway_implemented_reference_simulation_only_pending_closeout"
AUTH_ID = "AION-230-SRI-0001"
IMPLEMENTATION_TASK = "AION-231"
CLOSEOUT_TASK = "AION-232"
ACTIVE_AUTH_ID = "AION-232-SRI-0002"
ACTIVE_IMPLEMENTATION_TASK = "AION-233"
ACTIVE_CLOSEOUT_TASK = "AION-234"
FINAL_TASK = "AION-238"
SCOPE = (
    "local-operator-authenticated-session-offline-identity-request-context-"
    "actor-context-replay-guarded-capability-dispatch-policy-risk-approval-"
    "kill-switch-audit-observability-foundation-core"
)
GLM_DECISION = (
    "CONTROLLED_LOCAL_CONTINUAL_LEARNING_PILOT_FINAL_EVALUATION_PASS_COMPLETE_"
    "GOVERNED_LEARNING_MEMORY_PROGRAM"
)
PARENT_PROGRAMS = [
    "AION-COGNITIVE-ARCHITECTURE-001",
    "AION-KNOWLEDGE-INTELLIGENCE-001",
    "AION-GOVERNED-LEARNING-MEMORY-001",
    "AION-SELF-IMPROVEMENT-001",
]
REQUIRED_CHECKS = {
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
}
AION_229 = {
    146: {
        "state": "MERGED",
        "baseRefName": "main",
        "headRefName": "phase/governed-learning-memory-program-final-evaluation-closeout",
        "headRefOid": "3d718e29f07d260801bbe372c436442e95224d17",
        "mergeCommit": "a6a6d62eb7c04666a206bfadbbcd640e5bdca10a",
        "mergedAt": "2026-07-30T09:12:24Z",
    },
    147: {
        "state": "MERGED",
        "baseRefName": "main",
        "headRefName": (
            "phase/governed-learning-memory-program-final-evidence-reconciliation"
        ),
        "headRefOid": "ef8e7d0387734fc0c5fb12e1d35d38b0761bb342",
        "mergeCommit": "9daca65b0a801988db17906611b00dff882aaacd",
        "mergedAt": "2026-07-30T09:50:43Z",
    },
}
AUTHORIZED = [
    "secure_runtime_contract_approved",
    "local_operator_runtime_authorization_envelope_approved",
    "offline_ed25519_identity_assertion_composition_approved",
    "public_key_registry_read_approved",
    "request_identity_context_projection_approved",
    "actor_context_binding_approved",
    "persistent_replay_protection_validation_approved",
    "ephemeral_operator_session_lifecycle_approved",
    "explicit_session_start_approved",
    "explicit_session_close_approved",
    "deterministic_runtime_state_machine_approved",
    "runtime_request_envelope_approved",
    "capability_invocation_plan_approved",
    "closed_capability_allowlist_approved",
    "policy_decision_binding_approved",
    "risk_assessment_binding_approved",
    "guardrail_decision_binding_approved",
    "existing_approval_evidence_validation_approved",
    "side_effect_budget_enforcement_approved",
    "runtime_guard_approved",
    "operator_kill_switch_approved",
    "request_trace_correlation_approved",
    "runtime_audit_projection_approved",
    "runtime_observability_snapshot_approved",
    "runtime_health_readiness_approved",
    "deterministic_runtime_fixture_replay_approved",
    "local_operator_runtime_pilot_approved",
    "read_only_operator_console_projection_approved",
    "operator_review_item_approved",
    "redacted_runtime_evidence_approved",
    "documentation_and_static_evidence_approved",
]
PROHIBITED = [
    "production_auth_runtime_enabled",
    "public_auth_endpoint_enabled",
    "external_identity_provider_enabled",
    "password_authentication_enabled",
    "credential_persistence_enabled",
    "token_persistence_enabled",
    "session_token_issuance_enabled",
    "refresh_token_enabled",
    "public_key_network_retrieval_enabled",
    "general_network_access_enabled",
    "public_network_access_enabled",
    "model_provider_integration_enabled",
    "model_provider_call_enabled",
    "connector_integration_enabled",
    "connector_execution_enabled",
    "actual_tool_execution_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "browser_automation_enabled",
    "module_activation_enabled",
    "module_code_loading_enabled",
    "package_installation_enabled",
    "dynamic_route_registration_enabled",
    "automatic_capability_execution_enabled",
    "automatic_approval_enabled",
    "runtime_approval_creation_enabled",
    "production_write_execution_enabled",
    "production_memory_write_enabled",
    "production_policy_mutation_enabled",
    "cognitive_memory_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "glm_live_execution_enabled",
    "repeat_continual_learning_pilot_enabled",
    "self_improvement_runtime_enabled",
    "source_rewrite_enabled",
    "git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
]
RESOURCE_LIMITS = {
    "maximum_local_operator_sessions": 1,
    "maximum_session_seconds": 3600,
    "maximum_requests_per_session": 100,
    "maximum_concurrent_requests": 4,
    "maximum_capability_plans_per_request": 10,
    "maximum_capability_invocations_per_session": 100,
    "maximum_policy_decisions_per_request": 20,
    "maximum_risk_assessments_per_request": 20,
    "maximum_guardrail_decisions_per_request": 20,
    "maximum_approval_evidence_records_per_request": 4,
    "maximum_stage_receipts_per_session": 1000,
    "maximum_audit_records_per_session": 10000,
    "maximum_telemetry_events_per_session": 10000,
    "maximum_operator_review_items_per_session": 500,
    "maximum_trace_bytes_per_session": 4194304,
    "maximum_response_bytes_per_request": 1048576,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_session_checkpoints": 20,
    "maximum_replay_validations_per_request": 10,
    "maximum_kill_switch_checks_per_request": 10,
    "maximum_public_network_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_credentials_persisted": 0,
    "maximum_tokens_persisted": 0,
    "maximum_session_tokens_issued": 0,
    "maximum_external_identity_provider_calls": 0,
    "maximum_modules_activated": 0,
    "maximum_packages_installed": 0,
    "maximum_dynamic_routes_registered": 0,
    "maximum_automatic_approvals": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_production_writes": 0,
    "maximum_production_memory_writes": 0,
    "maximum_production_policy_mutations": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_actual_belief_creations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_glm_live_executions": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_automatic_merges": 0,
    "maximum_production_canary_executions": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
FUTURE_SOURCE_SCOPE = [
    "services/brain-api/src/aion_brain/contracts/secure_runtime.py",
    "services/brain-api/src/aion_brain/secure_runtime/__init__.py",
    "services/brain-api/src/aion_brain/secure_runtime/authorization.py",
    "services/brain-api/src/aion_brain/secure_runtime/identity_binding.py",
    "services/brain-api/src/aion_brain/secure_runtime/session_lifecycle.py",
    "services/brain-api/src/aion_brain/secure_runtime/request_pipeline.py",
    "services/brain-api/src/aion_brain/secure_runtime/capability_dispatch.py",
    "services/brain-api/src/aion_brain/secure_runtime/runtime_guard.py",
    "services/brain-api/src/aion_brain/secure_runtime/kill_switch.py",
    "services/brain-api/src/aion_brain/secure_runtime/audit.py",
    "services/brain-api/src/aion_brain/secure_runtime/observability.py",
    "services/brain-api/src/aion_brain/secure_runtime/integrity.py",
    "services/brain-api/src/aion_brain/secure_runtime/evidence.py",
]


def load_json(relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def text(relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def gh_available() -> bool:
    if subprocess.run(
        ["gh", "--version"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode != 0:
        return False
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        return True
    return subprocess.run(
        ["gh", "auth", "status"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def verify_pr(number: int, expected: dict[str, str]) -> None:
    result = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--json",
            "number,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,statusCheckRollup",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    require(result.returncode == 0, f"gh PR #{number} lookup failed")
    payload = json.loads(result.stdout)
    for key in ("state", "baseRefName", "headRefName", "headRefOid", "mergedAt"):
        require(payload.get(key) == expected[key], f"PR #{number} mismatch {key}")
    require(
        (payload.get("mergeCommit") or {}).get("oid") == expected["mergeCommit"],
        f"PR #{number} merge commit mismatch",
    )
    checks: dict[str, str] = {}
    for item in payload.get("statusCheckRollup") or []:
        name = item.get("name") or item.get("context") or item.get("workflowName")
        conclusion = item.get("conclusion") or item.get("state")
        if name in REQUIRED_CHECKS:
            checks[name] = conclusion
    require(REQUIRED_CHECKS <= set(checks), f"PR #{number} missing required checks")
    failed = {
        name: conclusion
        for name, conclusion in checks.items()
        if conclusion not in {"SUCCESS", "COMPLETED", "SUCCESSFUL"}
    }
    require(not failed, f"PR #{number} has non-success checks: {failed}")


program = load_json("docs/secure-runtime-integration/program-ledger.json")
auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")
glm_program = load_json("docs/governed-learning-memory/program-ledger.json")
glm_auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
program_example = load_json("examples/secure-runtime-integration/program-authorization.json")
auth_example = load_json("examples/secure-runtime-integration/local-operator-runtime-authorization.json")


# AION-236_CURRENT_STATE_FAST_PATH
post_aion236_state = (
    "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented"
)
post_aion237_state = (
    "operator_console_integrated_local_runtime_implemented_pending_final_evaluation"
)
final_complete_state = "secure_runtime_integration_program_complete"
if program.get("program_state") == final_complete_state:
    for payload in (program, auth):
        require(payload["program_id"] == PROGRAM_ID, "program id mismatch")
        require(payload["program_state"] == final_complete_state, "program state mismatch")
        require(
            payload["secure_runtime_integration_program_complete"] is True,
            "SRI program completion flag missing",
        )
        require(
            payload["secure_runtime_integration_final_evaluation_id"] == "AION-SRIPE-004",
            "final evaluation id mismatch",
        )
        require(
            payload["active_sri_implementation_authorization_count"] == 0,
            "active SRI count must be zero after AION-238",
        )
        require(
            payload["active_sri_implementation_authorization"] is None,
            "active SRI authorization must be absent after AION-238",
        )
        require(
            payload["active_sri_implementation_task"] is None,
            "active SRI task must be absent after AION-238",
        )
        require(
            payload["formal_closeout_task"] is None,
            "formal closeout task must be absent after AION-238",
        )
        require(
            payload["next_sri_implementation_task"] is None,
            "next SRI implementation task must be absent after AION-238",
        )
        require(
            payload["successor_authorization_id"] == "AION-238-V02RQ-0001",
            "successor v0.2 qualification authorization mismatch",
        )
        require(payload["operator_console_integration_implemented"] is True, "operator console missing")
        require(
            payload["integrated_authenticated_local_pilot_completed"] is True,
            "operator console pilot missing",
        )
        require(payload["sandboxed_capability_runtime_implemented"] is True, "capability runtime missing")
        for key in (
            "active_glm_implementation_authorization_count",
            "active_knowledge_implementation_authorization_count",
            "active_cognitive_implementation_authorization_count",
            "active_self_improvement_implementation_authorization_count",
        ):
            require(payload[key] == 0, f"parent authorization count nonzero: {key}")
        for key in (
            "external_connector_execution_enabled",
            "external_tool_execution_enabled",
            "production_runtime_authorized",
            "production_exposure",
            "v02_release_ready",
            "v02_tag_created",
            "v02_release_created",
        ):
            require(payload[key] is False, f"runtime boundary flag true: {key}")
    require(auth.get("active_authorizations") == [], "SRI active authorization list must be empty")
    closed_aion236 = next(
        item for item in auth["records"] if item.get("authorization_transaction_id") == "AION-236-SRI-0004"
    )
    require(closed_aion236["authorization_active"] is False, "AION-236 still active")
    require(closed_aion236["authorization_consumed"] is True, "AION-236 not consumed")
    require(closed_aion236["authorization_consumed_by_task"] == "AION-237", "AION-236 consumption task mismatch")
    require(closed_aion236["authorization_closed_by_task"] == "AION-238", "AION-236 closeout mismatch")
    require(closed_aion236["authorization_expired"] is True, "AION-236 not expired")
    require(closed_aion236["authorization_reusable"] is False, "AION-236 reusable")
    require(closed_aion236["final_sri_evaluation_id"] == "AION-SRIPE-004", "AION-236 final evaluation mismatch")
    require("AION-238-V02RQ-0001" in text("docs/project-status.md"), "status missing successor authorization")
    readme = text("README.md")
    require("AION-238 Final SRI Status" in readme, "README missing AION-238 final status")
    require("AION-238-V02RQ-0001" in readme, "README missing successor authorization")
elif program.get("program_state") in {post_aion236_state, post_aion237_state}:
    aion237_implemented = program.get("program_state") == post_aion237_state
    for payload in (program, auth):
        require(payload["program_id"] == PROGRAM_ID, "program id mismatch")
        require(payload["active_sri_implementation_authorization_count"] == 1, "active SRI count mismatch")
        require(payload["active_sri_implementation_authorization"] == "AION-236-SRI-0004", "active SRI auth mismatch")
        require(payload["active_sri_implementation_task"] == "AION-237", "active SRI task mismatch")
        require(payload["formal_closeout_task"] == "AION-238", "formal closeout mismatch")
        require(payload["production_runtime_authorized"] is False, "production runtime authorized")
        require(payload["v02_release_ready"] is False, "v0.2 readiness must be false")
        for key in (
            "active_glm_implementation_authorization_count",
            "active_knowledge_implementation_authorization_count",
            "active_cognitive_implementation_authorization_count",
            "active_self_improvement_implementation_authorization_count",
        ):
            require(payload[key] == 0, f"parent authorization count nonzero: {key}")
        for key in (
            "external_connector_execution_enabled",
            "external_tool_execution_enabled",
            "production_runtime_authorized",
            "v02_release_ready",
            "v02_tag_created",
            "v02_release_created",
        ):
            require(payload[key] is False, f"runtime boundary flag true: {key}")
        require(payload["sandboxed_capability_runtime_implemented"] is True, "capability runtime missing")
        require(
            payload["sandboxed_capability_runtime_operator_evaluation_passed"] is True,
            "AION-236 evaluation missing",
        )
        require(payload["operator_console_integration_authorized"] is True, "operator console auth missing")
        require(
            payload["operator_console_integration_implemented"] is aion237_implemented,
            "operator console implementation state mismatch",
        )
        require(
            payload.get("integrated_authenticated_local_pilot_completed") is aion237_implemented,
            "operator console integrated pilot state mismatch",
        )
    closed_aion232 = next(item for item in auth["records"] if item.get("authorization_transaction_id") == "AION-232-SRI-0002")
    require(closed_aion232["authorization_active"] is False, "AION-232 still active")
    require(closed_aion232["authorization_consumed"] is True, "AION-232 not consumed")
    require(closed_aion232["authorization_expired"] is True, "AION-232 not expired")
    require(closed_aion232["authorization_reusable"] is False, "AION-232 reusable")
    closed_aion234 = next(item for item in auth["records"] if item.get("authorization_transaction_id") == "AION-234-SRI-0003")
    require(closed_aion234["authorization_active"] is False, "AION-234 still active")
    require(closed_aion234["authorization_consumed"] is True, "AION-234 not consumed")
    require(closed_aion234["authorization_expired"] is True, "AION-234 not expired")
    require(closed_aion234["authorization_reusable"] is False, "AION-234 reusable")
    require(closed_aion234["authorization_closed_by_task"] == "AION-236", "AION-234 closeout mismatch")
    require("AION-236-SRI-0004" in text("docs/project-status.md"), "status missing AION-236 auth")
    require("AION-237" in text("README.md"), "README missing AION-237")

# AION-234/AION-235_CURRENT_STATE_FAST_PATH
else:
  post_aion234_states = {
      "model_gateway_evaluated_sandboxed_capability_runtime_authorized_not_implemented": False,
      "sandboxed_capability_runtime_implemented_reference_only_pending_closeout": True,
  }
  if program.get("program_state") in post_aion234_states:
    require(program["active_sri_implementation_authorization_count"] == 1, "active SRI count mismatch")
    require(program["active_sri_implementation_authorization"] == "AION-234-SRI-0003", "active SRI auth mismatch")
    require(program["active_sri_implementation_task"] == "AION-235", "active SRI task mismatch")
    require(program["formal_closeout_task"] == "AION-236", "formal closeout mismatch")
    require(program["model_gateway_operator_evaluation_passed"] is True, "AION-234 evaluation missing")
    require(program["sandboxed_capability_runtime_authorized"] is True, "capability runtime auth missing")
    expected_implemented = post_aion234_states[program["program_state"]]
    require(
        program["sandboxed_capability_runtime_implemented"] is expected_implemented,
        "capability runtime implementation state mismatch",
    )
    require(auth["authorization_transaction_id"] == "AION-234-SRI-0003", "auth ledger active id mismatch")
    require(auth["implementation_task"] == "AION-235", "auth implementation task mismatch")
    require(auth["formal_closeout_task"] == "AION-236", "auth closeout mismatch")
    require(auth["authorization_active"] is True, "AION-234 auth inactive")
    require(auth["authorization_consumed"] is False, "AION-234 auth consumed")
    require(auth["authorization_expired"] is False, "AION-234 auth expired")
    require(auth["authorization_reusable"] is False, "AION-234 auth reusable")
    closed_aion232 = next(item for item in auth["records"] if item.get("authorization_transaction_id") == "AION-232-SRI-0002")
    require(closed_aion232["authorization_active"] is False, "AION-232 still active")
    require(closed_aion232["authorization_consumed"] is True, "AION-232 not consumed")
    require(closed_aion232["authorization_expired"] is True, "AION-232 not expired")
    require(closed_aion232["authorization_reusable"] is False, "AION-232 reusable")
    for key in ("active_glm_implementation_authorization_count", "active_knowledge_implementation_authorization_count", "active_cognitive_implementation_authorization_count", "active_self_improvement_implementation_authorization_count"):
        require(program[key] == 0, f"parent authorization count nonzero: {key}")
    for key in ("external_connector_execution_enabled", "external_tool_execution_enabled", "production_runtime_authorized", "v02_release_ready", "v02_tag_created", "v02_release_created"):
        require(program[key] is False, f"runtime boundary flag true: {key}")
    require("AION-234-SRI-0003" in text("docs/project-status.md"), "status missing AION-234 auth")
    require("AION-235" in text("README.md"), "README missing AION-235")
  else:
    for payload in (program, auth):
        require(payload["program_id"] == PROGRAM_ID, "program id mismatch")
        require(payload["program_state"] == PROGRAM_STATE, "program state mismatch")
        require(
            payload["active_sri_implementation_authorization_count"] == 1,
            "active SRI authorization count mismatch",
        )
        require(
            payload["active_sri_implementation_authorization"] == ACTIVE_AUTH_ID,
            "active SRI authorization mismatch",
        )
        require(payload["active_sri_implementation_task"] == ACTIVE_IMPLEMENTATION_TASK, "task mismatch")
        require(payload["formal_closeout_task"] == ACTIVE_CLOSEOUT_TASK, "closeout task mismatch")
        require(payload["production_runtime_authorized"] is False, "production runtime authorized")
        require(payload["v02_release_ready"] is False, "v0.2 readiness must be false")
        require(payload["active_glm_implementation_authorization_count"] == 0, "GLM active auth")
        require(payload["active_knowledge_implementation_authorization_count"] == 0, "KI active auth")
        require(payload["active_cognitive_implementation_authorization_count"] == 0, "CA active auth")
        require(
            payload["active_self_improvement_implementation_authorization_count"] == 0,
            "self-improvement active auth",
        )
        foundation_authorized = payload.get("foundation_authorized_capabilities", payload["authorized_capabilities"])
        foundation_prohibited = payload.get("foundation_prohibited_capabilities", payload["prohibited_capabilities"])
        foundation_limits = payload.get("foundation_resource_limits", payload["resource_limits"])
        require(set(foundation_authorized) == set(AUTHORIZED), "approved keys mismatch")
        require(all(foundation_authorized[key] is True for key in AUTHORIZED), "approved flag")
        require(set(foundation_prohibited) == set(PROHIBITED), "prohibited keys mismatch")
        require(all(foundation_prohibited[key] is False for key in PROHIBITED), "prohibited flag")
        require(foundation_limits == RESOURCE_LIMITS, "resource limit mismatch")

    require(program["parent_completed_programs"] == PARENT_PROGRAMS, "parent lineage mismatch")
    require(program["parent_glm_evaluation_id"] == "AION-GLMPE-004", "GLMPE id mismatch")
    require(program["parent_glm_evaluation_decision"] == GLM_DECISION, "GLMPE decision mismatch")
    require(program["secure_runtime_foundation_authorized"] is True, "SRI foundation not authorized")
    require(program["secure_runtime_foundation_implemented"] is True, "SRI foundation not implemented")
    require(program["secure_runtime_implemented"] is True, "secure runtime implementation flag false")
    require(
        program["secure_runtime_foundation_state"]
        == "secure_runtime_foundation_implemented_local_operator_simulation_only",
        "SRI foundation state mismatch",
    )
    require(program["aion_231_record"]["authorization_transaction"] == AUTH_ID, "AION-231 record auth")
    require(program["aion_231_record"]["next_task"] == CLOSEOUT_TASK, "AION-231 next task")
    require(program["aion_230_delivery"]["authorization_transaction"] == AUTH_ID, "AION-230 delivery auth")
    require(program["future_source_scope"] == FUTURE_SOURCE_SCOPE, "future source scope mismatch")
    for item in program["roadmap"]:
        if item["task_id"] == IMPLEMENTATION_TASK:
            require(item["state"] == "evaluation_complete", "AION-231 roadmap state")
        if item["task_id"] == CLOSEOUT_TASK:
            require(
                item["state"] == "evaluation_complete_model_gateway_authorized",
                "AION-232 roadmap state",
            )
        if item["task_id"] == ACTIVE_IMPLEMENTATION_TASK:
            require(item["state"] == "implemented_pending_AION-234_closeout", "AION-233 roadmap state")
        if item["task_id"] == ACTIVE_CLOSEOUT_TASK:
            require(
                item["state"]
                == "active_formal_evaluation_and_sandboxed_capability_runtime_authorization_decision",
                "AION-234 roadmap state",
            )
        if item["task_id"] in {"AION-235", "AION-236", "AION-237"}:
            require(item["state"] == "planned_not_authorized", f"{item['task_id']} unauthorized")

    require(auth["authorization_transaction_id"] == ACTIVE_AUTH_ID, "auth id mismatch")
    require(auth["approval_record_id"] == ACTIVE_AUTH_ID, "approval id mismatch")
    require(auth["candidate_id"] == "controlled-provider-neutral-model-gateway-core", "candidate")
    require(auth["workstream"] == "secure-runtime-model-gateway", "workstream")
    require(auth["implementation_task"] == ACTIVE_IMPLEMENTATION_TASK, "implementation task")
    require(auth["formal_closeout_task"] == ACTIVE_CLOSEOUT_TASK, "formal closeout")
    require(auth["authorization_transaction_approved"] is True, "transaction not approved")
    require(auth["explicit_approval_record_approval"] is True, "approval record false")
    require(auth["implementation_authorization_approved"] is True, "implementation auth false")
    require(auth["implementation_go_status"] is True, "go false")
    require(auth["implementation_no_go_status"] is False, "no-go true")
    require(auth["authorization_active"] is True, "authorization inactive")
    require(auth["authorization_consumed"] is False, "authorization consumed")
    require(auth["authorization_expired"] is False, "authorization expired")
    require(auth["authorization_reusable"] is False, "authorization reusable")
    require(len(auth["active_authorizations"]) == 1, "more than one active SRI auth")
    closed_aion230 = next(
        item
        for item in auth["records"]
        if item.get("authorization_transaction_id") == AUTH_ID
    )
    require(closed_aion230["authorization_active"] is False, "AION-230 auth still active")
    require(closed_aion230["authorization_consumed"] is True, "AION-230 auth not consumed")
    require(closed_aion230["authorization_expired"] is True, "AION-230 auth not expired")
    require(closed_aion230["authorization_reusable"] is False, "AION-230 auth reusable")
    require(closed_aion230["authorization_closed_by_task"] == CLOSEOUT_TASK, "AION-230 closeout")
    require(closed_aion230["implementation_task"] == IMPLEMENTATION_TASK, "AION-230 implementation")
    require(closed_aion230["formal_closeout_task"] == CLOSEOUT_TASK, "AION-230 formal closeout")
    require(closed_aion230["authorization_scope"] == SCOPE, "AION-230 scope mismatch")

    require(program_example["program_id"] == PROGRAM_ID, "program example mismatch")
    require(auth_example["authorization_transaction_id"] == AUTH_ID, "auth example mismatch")

    require(glm_program["program_state"] == "governed_learning_memory_program_complete", "GLM incomplete")
    require(glm_program["governed_learning_memory_program_complete"] is True, "GLM complete flag")
    require(glm_program["program_final_evidence_reconciled"] is True, "GLM reconciliation flag")
    require(glm_program["governed_learning_memory_program_evaluation_id"] == "AION-GLMPE-004", "GLMPE")
    require(glm_program["governed_learning_memory_program_evaluation_decision"] == GLM_DECISION, "GLM decision")
    require(glm_program["active_glm_implementation_authorization_count"] == 0, "active GLM auth")
    require(glm_auth["active_authorizations"] == [], "GLM active authorizations not empty")
    closed = next(
        item
        for item in glm_auth["records"]
        if item.get("authorization_transaction_id") == "AION-227-GLM-0004"
    )
    require(closed["authorization_active"] is False, "AION-227 still active")
    require(closed["authorization_consumed"] is True, "AION-227 not consumed")
    require(closed["authorization_consumed_by_task"] == "AION-228", "AION-227 consumer")
    require(closed["authorization_consumed_by_prs"] == [145], "AION-227 PRs")
    require(closed["authorization_expired"] is True, "AION-227 not expired")
    require(closed["authorization_reusable"] is False, "AION-227 reusable")
    require(closed["authorization_closed_by_task"] == "AION-229", "AION-227 closeout")

    verification = program["aion_229_verification"]
    require(verification["primary_pr"] == 146, "AION-229 primary PR mismatch")
    require(verification["reconciliation_pr"] == 147, "AION-229 reconciliation PR mismatch")
    require(verification["ci_result"] == "pass", "AION-229 CI mismatch")
    require(verification["evaluation_id"] == "AION-GLMPE-004", "AION-229 eval id")
    require(verification["evaluation_decision"] == GLM_DECISION, "AION-229 eval decision")

    if gh_available():
        for number, expected in AION_229.items():
            verify_pr(number, expected)
    else:
        print("WARN: gh PR evidence unavailable; relying on committed AION-229 evidence")

    for source_path in FUTURE_SOURCE_SCOPE:
        require((root / source_path).exists(), f"AION-231 source missing: {source_path}")
    for prohibited_path in (
        "services/brain-api/src/aion_brain/api/secure_runtime.py",
        "services/brain-api/src/aion_brain/secure_runtime/network.py",
        "services/brain-api/src/aion_brain/secure_runtime/model_gateway.py",
        "services/brain-api/src/aion_brain/secure_runtime/connector_runtime.py",
        "services/brain-api/src/aion_brain/secure_runtime/tool_runtime.py",
        "services/brain-api/src/aion_brain/secure_runtime/shell_runtime.py",
        "services/brain-api/src/aion_brain/secure_runtime/module_loader.py",
        "services/brain-api/src/aion_brain/secure_runtime/credential_store.py",
        "services/brain-api/src/aion_brain/secure_runtime/token_store.py",
        "services/brain-api/src/aion_brain/secure_runtime/background_worker.py",
        "services/brain-api/src/aion_brain/secure_runtime/scheduler.py",
    ):
        require(not (root / prohibited_path).exists(), f"prohibited source exists: {prohibited_path}")

    readme = text("README.md")
    status = text("docs/project-status.md")
    architecture = text("docs/architecture.md")
    release = text("docs/release/v02-release-readiness-delta.md")
    for content, label in ((readme, "README"), (status, "project status")):
        require("Knowledge Intelligence Program" in content, f"{label} missing KI state")
        require("Governed Learning and Memory Program" in content, f"{label} missing GLM state")
        require(AUTH_ID in content, f"{label} missing SRI auth")
        require(ACTIVE_AUTH_ID in content, f"{label} missing active SRI auth")
        require("AION-231" in content and "AION-232" in content, f"{label} missing task flow")
        require("v0.2 remains unreleased" in content or "v02_release_ready=false" in content, f"{label} v0.2")
    require("final Git evidence reconciliation is recorded by PR #147" in architecture, "architecture stale")
    for blocker in (
        "Production-auth runtime integration",
        "Production replay-ledger provisioning",
        "Request-level verified identity integration",
        "Identity-provider integration",
        "Public-key operational provisioning and rotation",
        "Protected-material lifecycle",
        "Credential lifecycle",
        "Token lifecycle",
        "Session lifecycle",
        "Deployment artifact",
        "Rollback operations",
        "Production observability",
        "Threat-model review",
        "Runtime guard release decision",
        "Release-candidate validation",
        "Explicit v0.2 tag and release authorization",
    ):
        require(blocker in release, f"release blocker missing: {blocker}")
    require("AION-230 addresses only the secure local runtime foundation" in release, "release scope")
PY

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

echo "secure runtime integration program authorization PASS"

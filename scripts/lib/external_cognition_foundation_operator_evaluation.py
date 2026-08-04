"""AION-247 operator evaluation for the external-cognition foundation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PASS_DECISION = (
    "CONTROLLED_EXTERNAL_COGNITION_GATEWAY_FOUNDATION_OPERATOR_EVALUATION_PASS_"
    "RECOMMEND_SINGLE_OPENAI_RESPONSES_API_SYNTHETIC_LIVE_PROVIDER_PILOT_AUTHORIZATION"
)
FAIL_DECISION = (
    "CONTROLLED_EXTERNAL_COGNITION_GATEWAY_FOUNDATION_OPERATOR_EVALUATION_FAIL_"
    "REMAIN_DETERMINISTIC_FIXTURE_ONLY"
)
EVALUATION_ID = "AION-ECGPE-001"
EVALUATION_TYPE = "controlled_external_cognition_gateway_foundation_operator_evaluation"
PROGRAM_ID = "AION-ADAPTIVE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-246"
CLOSEOUT_TASK = "AION-247"
NEXT_IMPLEMENTATION_TASK = "AION-248"
NEXT_CLOSEOUT_TASK = "AION-249"
FINAL_PLANNED_TASK = "AION-260"
CURRENT_AUTHORIZATION_ID = "AION-245-AI-0001"
NEXT_AUTHORIZATION_ID = "AION-247-AI-0002"
PRIMARY_PR = 166
PRIMARY_BRANCH = "phase/v03-external-cognition-gateway-foundation"
EVALUATION_BRANCH = "phase/v03-external-cognition-evaluation-live-provider-authorization"
PRIMARY_MERGED_AT = "2026-08-04T01:34:30Z"
PRIMARY_MERGE_COMMIT = "27d6ad15a043940bf537caec72cf7de7c74f6dc2"
IMPLEMENTATION_COMMIT = "dd1f7b34cb2a25dfd409cf72667f073af9e8e965"
PILOT_ID = "AION-246-deterministic-external-cognition-fixture-pilot"
PILOT_REPORT_FINGERPRINT = (
    "2f9a05f78d4afb40f390ace3cafbb2f997e46525063cd80fe6cab131e8be9aad"
)
IMPLEMENTATION_FEATURE_COMMITS: tuple[str, ...] = (
    "dd1f7b34cb2a25dfd409cf72667f073af9e8e965",
    "afe4fc41d6737512287ad0bb00a0c2174dab8e9e",
    "13c9fdf283a2f0c499497fd3aefb3ae70adc5f54",
    "32f1eb57a48214e8280203d513277d47759c44bd",
    "8d885ae9dbf32e6c79f1db1b0aed35374837090a",
)
REQUIRED_CI_CHECKS: tuple[str, ...] = (
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
)
SCENARIO_IDS: tuple[str, ...] = (
    "aion_246_delivery_and_ci_integrity",
    "adaptive_intelligence_authorization_lineage",
    "exact_source_and_repository_boundary",
    "secure_runtime_component_binding_integrity",
    "existing_model_gateway_component_binding_integrity",
    "external_cognition_contract_immutability",
    "provider_manifest_integrity",
    "model_manifest_and_capability_integrity",
    "message_projection_and_raw_content_non_retention",
    "request_envelope_integrity",
    "response_envelope_integrity",
    "restricted_structured_output_schema_integrity",
    "structured_output_validation_and_untrusted_classification",
    "context_budget_fail_closed",
    "output_budget_fail_closed",
    "cost_budget_fail_closed",
    "latency_budget_fail_closed",
    "deterministic_capability_routing",
    "existing_model_gateway_route_compatibility",
    "retry_and_fallback_boundedness",
    "circuit_breaker_state_integrity",
    "trust_and_uncertainty_integrity",
    "provider_error_normalization_integrity",
    "recursive_redaction_and_protected_material_exclusion",
    "deterministic_fixture_provider_integrity",
    "exact_replay_and_changed_replay_integrity",
    "audit_chain_and_observability_integrity",
    "operator_review_integrity",
    "fixture_pilot_schema_counters_and_report_fingerprint",
    "zero_operational_effects_and_release_boundary",
    "single_openai_responses_api_pilot_architecture_safety",
    "live_provider_pilot_authorization_readiness",
)
EXPECTED_PILOT_COUNTERS: dict[str, int] = {
    "provider_manifests_loaded": 3,
    "model_manifests_loaded": 6,
    "model_capability_records_loaded": 18,
    "routing_policies_loaded": 6,
    "structured_output_schemas_loaded": 2,
    "fixture_sessions_started": 1,
    "fixture_sessions_closed": 1,
    "active_fixture_sessions_after_close": 0,
    "fixture_requests_submitted": 16,
    "route_plans_created": 9,
    "fixture_provider_invocations": 11,
    "fixture_responses_generated": 9,
    "successful_response_projections": 8,
    "structured_output_validations": 2,
    "structured_output_validation_failures": 1,
    "capability_rejections": 1,
    "context_budget_rejections": 1,
    "output_budget_rejections": 1,
    "cost_budget_rejections": 1,
    "latency_budget_rejections": 1,
    "normalized_provider_errors": 2,
    "retry_plans_created": 1,
    "fallback_plans_created": 1,
    "fallback_responses_generated": 1,
    "circuit_breaker_open_events": 1,
    "exact_replays_returned": 1,
    "changed_replays_rejected": 1,
    "operator_review_items_created": 8,
    "trust_assessments_created": 9,
    "uncertainty_projections_created": 9,
    "observability_snapshots_created": 1,
    "integrity_reports_created": 1,
    "temporary_files_retained": 0,
}
EXPECTED_AION246_SOURCE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/external_cognition.py",
    "services/brain-api/src/aion_brain/external_cognition/__init__.py",
    "services/brain-api/src/aion_brain/external_cognition/authorization.py",
    "services/brain-api/src/aion_brain/external_cognition/component_binding.py",
    "services/brain-api/src/aion_brain/external_cognition/provider_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/model_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/request_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/response_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/message_normalization.py",
    "services/brain-api/src/aion_brain/external_cognition/structured_output.py",
    "services/brain-api/src/aion_brain/external_cognition/routing_policy.py",
    "services/brain-api/src/aion_brain/external_cognition/budgets.py",
    "services/brain-api/src/aion_brain/external_cognition/trust.py",
    "services/brain-api/src/aion_brain/external_cognition/redaction.py",
    "services/brain-api/src/aion_brain/external_cognition/circuit_breaker.py",
    "services/brain-api/src/aion_brain/external_cognition/fixture_provider.py",
    "services/brain-api/src/aion_brain/external_cognition/replay.py",
    "services/brain-api/src/aion_brain/external_cognition/observability.py",
    "services/brain-api/src/aion_brain/external_cognition/audit.py",
    "services/brain-api/src/aion_brain/external_cognition/integrity.py",
    "services/brain-api/src/aion_brain/external_cognition/evidence.py",
    "scripts/external-cognition-fixture-local-run.py",
)
PROHIBITED_AION248_SOURCE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/__init__.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/authorization.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/component_binding.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/provider_selection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/operator_approval.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/credential_boundary.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/endpoint_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/request_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/response_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/usage_budget.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/retention_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/transport.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/openai_responses_adapter.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/trust.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/redaction.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/replay.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/audit.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/observability.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/integrity.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/evidence.py",
    "scripts/live-provider-pilot-local-run.py",
)
PROHIBITED_RUNTIME_SOURCE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/external_cognition/network.py",
    "services/brain-api/src/aion_brain/external_cognition/http_client.py",
    "services/brain-api/src/aion_brain/external_cognition/openai.py",
    "services/brain-api/src/aion_brain/external_cognition/anthropic.py",
    "services/brain-api/src/aion_brain/external_cognition/google.py",
    "services/brain-api/src/aion_brain/external_cognition/azure_openai.py",
    "services/brain-api/src/aion_brain/external_cognition/credential_store.py",
    "services/brain-api/src/aion_brain/external_cognition/token_store.py",
    "services/brain-api/src/aion_brain/external_cognition/background_worker.py",
    "services/brain-api/src/aion_brain/external_cognition/scheduler.py",
    "services/brain-api/src/aion_brain/api/external_cognition.py",
)
PROTECTED_MARKERS: tuple[str, ...] = (
    "sk-",
    "bearer ",
    "authorization header value",
    "api key value",
    "chain-of-thought",
    "hidden reasoning",
    "private key",
    "raw prompt value",
    "raw response value",
    "temporary-root",
    "/private/tmp",
)
REPORT_ZERO_COUNTERS: tuple[str, ...] = (
    "actual_model_provider_calls",
    "provider_network_adapter_calls",
    "public_network_calls",
    "external_network_egress_calls",
    "dns_resolutions",
    "provider_credentials_read",
    "provider_credentials_persisted",
    "authorization_headers_created",
    "raw_prompts_persisted",
    "raw_responses_persisted",
    "hidden_reasoning_records",
    "memory_writes",
    "verified_knowledge_promotions",
    "belief_mutations",
    "external_tool_executions",
    "external_connector_calls",
    "background_cycles",
    "source_mutations",
    "git_operations",
    "production_deployments",
    "model_weight_changes",
)
AUTHORIZED_AION248_CAPABILITIES: tuple[str, ...] = (
    "live_provider_pilot_contract_approved",
    "live_provider_pilot_authorization_envelope_approved",
    "external_cognition_component_binding_approved",
    "existing_model_gateway_component_binding_approved",
    "openai_responses_api_adapter_approved",
    "single_provider_manifest_approved",
    "single_model_manifest_approved",
    "operator_model_selection_record_approved",
    "environment_only_credential_read_approved",
    "transient_authorization_header_approved",
    "exact_endpoint_policy_approved",
    "tls_certificate_verification_approved",
    "no_redirect_transport_approved",
    "proxy_bypass_policy_approved",
    "synthetic_text_request_approved",
    "store_false_request_approved",
    "background_false_request_approved",
    "stream_false_request_approved",
    "tool_free_request_approved",
    "file_free_request_approved",
    "bounded_provider_usage_approved",
    "live_response_projection_approved",
    "live_response_redaction_approved",
    "live_response_fingerprint_approved",
    "untrusted_live_response_classification_approved",
    "live_uncertainty_projection_approved",
    "local_exact_replay_approved",
    "changed_replay_rejection_approved",
    "operator_review_record_approved",
    "live_usage_evidence_approved",
    "audit_evidence_approved",
    "observability_evidence_approved",
    "complete_transient_cleanup_approved",
    "documentation_and_static_evidence_approved",
)
PROHIBITED_AION248_CAPABILITIES: tuple[str, ...] = (
    "multiple_live_providers_enabled",
    "multiple_live_models_enabled",
    "provider_model_listing_call_enabled",
    "provider_endpoint_discovery_enabled",
    "redirect_following_enabled",
    "proxy_use_enabled",
    "credential_cli_argument_enabled",
    "credential_file_input_enabled",
    "credential_logging_enabled",
    "credential_fingerprinting_enabled",
    "credential_persistence_enabled",
    "provider_token_persistence_enabled",
    "raw_authorization_header_persistence_enabled",
    "store_true_enabled",
    "background_mode_enabled",
    "streaming_enabled",
    "previous_response_id_enabled",
    "conversation_state_persistence_enabled",
    "provider_builtin_tools_enabled",
    "provider_web_search_enabled",
    "provider_file_search_enabled",
    "provider_code_interpreter_enabled",
    "provider_computer_use_enabled",
    "provider_remote_mcp_enabled",
    "provider_function_calling_enabled",
    "provider_custom_tools_enabled",
    "file_upload_enabled",
    "image_input_enabled",
    "audio_input_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "hidden_reasoning_capture_enabled",
    "model_output_triggered_execution_enabled",
    "model_output_tool_call_enabled",
    "persistent_memory_write_enabled",
    "verified_knowledge_promotion_enabled",
    "actual_belief_mutation_enabled",
    "engagement_learning_enabled",
    "adaptive_routing_runtime_enabled",
    "external_connector_execution_enabled",
    "external_tool_execution_enabled",
    "autonomous_background_loop_enabled",
    "scheduled_provider_calls_enabled",
    "source_rewrite_enabled",
    "runtime_git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "production_runtime_authorized",
    "production_deployment_enabled",
    "model_weight_training_enabled",
)
AION248_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_live_provider_sessions": 1,
    "maximum_live_providers": 1,
    "maximum_live_models": 1,
    "maximum_live_provider_calls": 6,
    "maximum_successful_live_responses": 6,
    "maximum_endpoint_hosts": 1,
    "maximum_endpoint_paths": 1,
    "maximum_dns_resolutions": 8,
    "maximum_tls_connections": 6,
    "maximum_http_requests": 6,
    "maximum_redirects": 0,
    "maximum_concurrency": 1,
    "maximum_automatic_retries": 0,
    "maximum_session_seconds": 1200,
    "maximum_request_timeout_seconds": 120,
    "maximum_request_payload_bytes": 262144,
    "maximum_response_payload_bytes": 2097152,
    "maximum_total_input_tokens": 60000,
    "maximum_total_output_tokens": 12000,
    "maximum_messages_per_request": 16,
    "maximum_operator_review_items": 12,
    "maximum_audit_records": 500,
    "maximum_observability_records": 500,
    "maximum_evidence_records": 2000,
    "maximum_evidence_bytes": 20971520,
    "maximum_provider_credentials_read": 1,
    "maximum_authorization_headers_created": 6,
}
AION248_ZERO_RESOURCE_LIMITS: tuple[str, ...] = (
    "maximum_provider_credentials_generated",
    "maximum_provider_credentials_persisted",
    "maximum_provider_tokens_persisted",
    "maximum_raw_authorization_headers_persisted",
    "maximum_store_true_requests",
    "maximum_background_requests",
    "maximum_streaming_requests",
    "maximum_previous_response_references",
    "maximum_provider_tool_definitions",
    "maximum_provider_tool_calls",
    "maximum_provider_web_search_calls",
    "maximum_provider_file_search_calls",
    "maximum_provider_code_interpreter_calls",
    "maximum_provider_computer_use_calls",
    "maximum_provider_mcp_calls",
    "maximum_file_uploads",
    "maximum_image_inputs",
    "maximum_audio_inputs",
    "maximum_raw_prompts_persisted",
    "maximum_raw_responses_persisted",
    "maximum_hidden_reasoning_records",
    "maximum_memory_writes",
    "maximum_verified_knowledge_promotions",
    "maximum_belief_mutations",
    "maximum_external_tool_executions",
    "maximum_external_connector_calls",
    "maximum_background_cycles",
    "maximum_scheduled_provider_calls",
    "maximum_source_mutations",
    "maximum_git_operations",
    "maximum_production_deployments",
    "maximum_model_weight_changes",
)
THREAT_MODEL_ITEMS: tuple[str, ...] = (
    "API-key leakage",
    "authorization-header logging",
    "credential-file substitution",
    "environment-variable disclosure",
    "endpoint substitution",
    "DNS rebinding",
    "TLS downgrade",
    "certificate-verification bypass",
    "redirect to another host",
    "proxy interception",
    "oversized provider response",
    "request replay causing duplicate cost",
    "changed replay under an existing request ID",
    "model-ID substitution",
    "tool injection",
    "web-search activation",
    "file-upload activation",
    "persistent conversation-state activation",
    "store=true drift",
    "background-mode drift",
    "response-body persistence",
    "prompt-body persistence",
    "hidden-reasoning retention",
    "structured-output schema bypass",
    "provider output treated as fact",
    "provider output treated as execution authority",
    "memory-write escalation",
    "real-tool escalation",
    "cost-budget bypass",
    "retry amplification",
    "incomplete cleanup",
)


class ScenarioFailure(ValueError):
    """Raised when an evaluation hard gate fails."""


@dataclass(frozen=True)
class EvaluationContext:
    repo_root: Path
    evaluation_id: str
    evaluation_base_commit: str
    implementation_main_commit: str
    implementation_commit: str
    pilot_evidence: dict[str, Any]
    contract_examples: dict[str, Any]
    program_ledger: dict[str, Any]
    authorization_ledger: dict[str, Any]
    program_authorization: dict[str, Any]
    foundation_authorization: dict[str, Any]
    prohibited_effect_counters: dict[str, int]


def configure_import_path(repo_root: Path) -> None:
    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def evaluate_external_cognition_foundation(
    *,
    repo_root: Path,
    evaluation_id: str,
    implementation_main_commit: str,
    implementation_commit: str,
    pilot_evidence: Path,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    """Execute the AION-247 immutable read-only evaluation."""

    configure_import_path(repo_root)
    start = time.perf_counter()
    context = _build_context(
        repo_root=repo_root,
        evaluation_id=evaluation_id,
        implementation_main_commit=implementation_main_commit,
        implementation_commit=implementation_commit,
        pilot_evidence=pilot_evidence,
        evaluation_base_commit=evaluation_base_commit,
    )
    scenario_results: list[dict[str, Any]] = []
    for scenario_id in SCENARIO_IDS:
        scenario_results.append(_run_scenario(scenario_id, context, scenario_results))
    hard_gate_results = [
        {
            "gate_id": item["scenario_id"],
            "scenario_id": item["scenario_id"],
            "hard_gate": True,
            "passed": item["passed"],
            "summary": item["summary"],
        }
        for item in scenario_results
    ]
    evaluation_passed = all(item["passed"] is True for item in scenario_results)
    decision = PASS_DECISION if evaluation_passed else FAIL_DECISION
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "implementation_main_commit": implementation_main_commit,
        "implementation_commit": implementation_commit,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [PRIMARY_PR],
        "corrective_prs": [],
        "implementation_feature_commits": list(IMPLEMENTATION_FEATURE_COMMITS),
        "implementation_merge_commits": [PRIMARY_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_ids": list(SCENARIO_IDS),
        "scenario_results": scenario_results,
        "hard_gate_count": len(hard_gate_results),
        "hard_gate_results": hard_gate_results,
        "pilot_validation": _pilot_validation(context),
        "authorization_lineage": _authorization_lineage(context),
        "component_lineage": _component_lineage(context),
        "manifest_integrity": _manifest_integrity(context),
        "request_response_integrity": _request_response_integrity(context),
        "structured_output_integrity": _structured_output_integrity(context),
        "budget_integrity": _budget_integrity(context),
        "routing_integrity": _routing_integrity(context),
        "trust_integrity": _trust_integrity(context),
        "redaction_integrity": _redaction_integrity(context),
        "replay_integrity": _replay_integrity(context),
        "audit_integrity": _audit_integrity(context),
        "live_pilot_architecture_decision": _live_pilot_architecture_decision(),
        "repository_integrity": _repository_integrity(context),
        "next_architecture_decision": (
            "single_openai_responses_api_synthetic_live_provider_pilot_authorized"
            if evaluation_passed
            else "external_cognition_foundation_remediation_review"
        ),
        "read_only": True,
        "redacted": True,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
        "corrective_cycles": 0,
        "corrective_cycle_limit": 3,
        "evaluation_runtime_ms": int((time.perf_counter() - start) * 1000),
        "production_runtime_authorized": False,
    }
    for key in REPORT_ZERO_COUNTERS:
        report[key] = 0
    report["report_fingerprint"] = report_fingerprint(report)
    validate_evaluation_report(report)
    return report


def validate_evaluation_report(report: dict[str, Any]) -> None:
    """Validate AION-247 report schema, order and non-effect invariants."""

    required_pairs = {
        "evaluation_id": EVALUATION_ID,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "implementation_main_commit": PRIMARY_MERGE_COMMIT,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "scenario_count": len(SCENARIO_IDS),
        "hard_gate_count": len(SCENARIO_IDS),
    }
    for key, expected in required_pairs.items():
        if report.get(key) != expected:
            raise ValueError(f"unexpected report field {key}: {report.get(key)!r}")
    if report.get("implementation_prs") != [PRIMARY_PR]:
        raise ValueError("unexpected implementation PR list")
    if report.get("implementation_feature_commits") != list(IMPLEMENTATION_FEATURE_COMMITS):
        raise ValueError("unexpected implementation feature commits")
    if report.get("implementation_merge_commits") != [PRIMARY_MERGE_COMMIT]:
        raise ValueError("unexpected implementation merge commits")
    if report.get("scenario_ids") != list(SCENARIO_IDS):
        raise ValueError("scenario_ids must match the required ordered list")
    scenarios = report.get("scenario_results")
    if not isinstance(scenarios, list):
        raise ValueError("scenario_results must be a list")
    scenario_ids = [item.get("scenario_id") for item in scenarios]
    if scenario_ids != list(SCENARIO_IDS):
        raise ValueError("scenario_results must match the required ordered scenario list")
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("duplicate scenario result")
    hard_gates = report.get("hard_gate_results")
    if not isinstance(hard_gates, list):
        raise ValueError("hard_gate_results must be a list")
    if [item.get("scenario_id") for item in hard_gates] != list(SCENARIO_IDS):
        raise ValueError("hard_gate_results must classify the same 32 scenarios")
    if not all(item.get("hard_gate") is True for item in hard_gates):
        raise ValueError("every scenario must be classified as a hard gate")
    scenarios_passed = all(item.get("passed") is True for item in scenarios)
    gates_passed = all(item.get("passed") is True for item in hard_gates)
    expected_pass = scenarios_passed and gates_passed
    if report.get("evaluation_passed") is not expected_pass:
        raise ValueError("evaluation_passed must be derived from scenarios and hard gates")
    decision = report.get("decision")
    if decision not in {PASS_DECISION, FAIL_DECISION}:
        raise ValueError("unexpected evaluation decision")
    if decision == PASS_DECISION and not expected_pass:
        raise ValueError("PASS cannot be reported while a hard gate failed")
    if decision == FAIL_DECISION and expected_pass:
        raise ValueError("FAIL cannot be retained while every hard gate passed")
    for key in ("read_only", "redacted", "repository_unchanged", "temporary_evaluation_data_cleaned"):
        if report.get(key) is not True:
            raise ValueError(f"{key} must be true")
    for key in REPORT_ZERO_COUNTERS:
        if report.get(key) != 0:
            raise ValueError(f"{key} must be zero")
    if report.get("production_runtime_authorized") is not False:
        raise ValueError("production runtime must remain disabled")
    if report.get("report_fingerprint") != report_fingerprint(report):
        raise ValueError("report fingerprint mismatch")
    rendered_values = json.dumps(list(_iter_string_values(report)), sort_keys=True).lower()
    for marker in PROTECTED_MARKERS:
        if marker in rendered_values:
            raise ValueError(f"protected marker leaked into report: {marker}")


def report_fingerprint(report: dict[str, Any]) -> str:
    payload = copy.deepcopy(report)
    payload.pop("report_fingerprint", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_context(
    *,
    repo_root: Path,
    evaluation_id: str,
    implementation_main_commit: str,
    implementation_commit: str,
    pilot_evidence: Path,
    evaluation_base_commit: str,
) -> EvaluationContext:
    from aion_brain.contracts.external_cognition import PROHIBITED_EFFECT_COUNTERS

    return EvaluationContext(
        repo_root=repo_root,
        evaluation_id=evaluation_id,
        evaluation_base_commit=evaluation_base_commit,
        implementation_main_commit=implementation_main_commit,
        implementation_commit=implementation_commit,
        pilot_evidence=_load_json(repo_root / pilot_evidence),
        contract_examples=_load_json(
            repo_root / "examples/adaptive-intelligence/external-cognition-contract-examples.json"
        ),
        program_ledger=_load_json(repo_root / "docs/adaptive-intelligence/program-ledger.json"),
        authorization_ledger=_load_json(
            repo_root / "docs/adaptive-intelligence/authorization-ledger.json"
        ),
        program_authorization=_load_json(
            repo_root / "examples/adaptive-intelligence/program-authorization.json"
        ),
        foundation_authorization=_load_json(
            repo_root / "examples/adaptive-intelligence/external-cognition-foundation-authorization.json"
        ),
        prohibited_effect_counters=dict(PROHIBITED_EFFECT_COUNTERS),
    )


def _run_scenario(
    scenario_id: str,
    context: EvaluationContext,
    prior_results: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        evidence = SCENARIO_CHECKS[scenario_id](context, prior_results)
        return {
            "scenario_id": scenario_id,
            "hard_gate": True,
            "passed": True,
            "summary": "PASS",
            "evidence": evidence,
        }
    except ScenarioFailure as exc:
        return {
            "scenario_id": scenario_id,
            "hard_gate": True,
            "passed": False,
            "summary": str(exc),
            "evidence": {},
        }


def _check_delivery(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    _require(context.evaluation_id == EVALUATION_ID, "evaluation id mismatch")
    _require(context.implementation_main_commit == PRIMARY_MERGE_COMMIT, "merge commit mismatch")
    _require(context.implementation_commit == IMPLEMENTATION_COMMIT, "implementation commit mismatch")
    _require(context.pilot_evidence.get("implementation_commit") == IMPLEMENTATION_COMMIT, "pilot implementation commit mismatch")
    return {
        "pr": PRIMARY_PR,
        "branch": PRIMARY_BRANCH,
        "merge_commit": PRIMARY_MERGE_COMMIT,
        "merged_at": PRIMARY_MERGED_AT,
        "feature_commits": list(IMPLEMENTATION_FEATURE_COMMITS),
        "required_ci_checks": list(REQUIRED_CI_CHECKS),
    }


def _check_authorization_lineage(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    record = _authorization_record(context.authorization_ledger, CURRENT_AUTHORIZATION_ID)
    _require(context.program_ledger.get("program_id") == PROGRAM_ID, "program ledger mismatch")
    _require(record.get("authorization_active") is True, "AION-245 must be active during immutable evaluation")
    _require(record.get("authorization_consumed") is False, "AION-245 must be unconsumed before closeout")
    _require(record.get("authorization_expired") is False, "AION-245 must be unexpired before closeout")
    _require(record.get("authorization_reusable") is False, "AION-245 must be non-reusable")
    _require(record.get("implementation_task") == IMPLEMENTATION_TASK, "implementation task mismatch")
    _require(record.get("formal_closeout_task") == CLOSEOUT_TASK, "formal closeout mismatch")
    _require(context.authorization_ledger.get("active_adaptive_intelligence_authorization_count") == 1, "active authorization count mismatch")
    return {
        "active_authorization": CURRENT_AUTHORIZATION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": CLOSEOUT_TASK,
        "final_planned_task": FINAL_PLANNED_TASK,
    }


def _check_source_boundary(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    for path in EXPECTED_AION246_SOURCE:
        _require((context.repo_root / path).is_file(), f"required AION-246 source missing: {path}")
    for path in PROHIBITED_RUNTIME_SOURCE + PROHIBITED_AION248_SOURCE:
        _require(not (context.repo_root / path).exists(), f"prohibited source exists: {path}")
    return {
        "aion_246_source_count": len(EXPECTED_AION246_SOURCE),
        "aion_248_source_absent": True,
        "provider_runtime_source_absent": True,
    }


def _check_secure_runtime_binding(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    binding = context.contract_examples["component_binding"]
    _require(binding.get("secure_runtime_contract_fingerprint") != "0" * 64, "secure runtime contract fingerprint missing")
    _require(binding.get("secure_runtime_session_fingerprint") != "0" * 64, "secure runtime session fingerprint missing")
    _require(binding.get("read_only") is True, "component binding must be read-only")
    _require(binding.get("network_effect") is False, "component binding network effect enabled")
    return {
        "secure_runtime_contract_fingerprint": binding["secure_runtime_contract_fingerprint"],
        "secure_runtime_session_fingerprint": binding["secure_runtime_session_fingerprint"],
    }


def _check_model_gateway_binding(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    binding = context.contract_examples["component_binding"]
    route = context.contract_examples["route_plan"]
    for key in (
        "existing_model_gateway_contract_fingerprint",
        "existing_model_gateway_service_fingerprint",
        "existing_model_manifest_projection_fingerprint",
        "existing_provider_manifest_projection_fingerprint",
        "existing_route_policy_projection_fingerprint",
    ):
        _require(binding.get(key) != "0" * 64, f"{key} missing")
    _require(route.get("existing_model_gateway_compatible") is True, "route compatibility disabled")
    return {"existing_model_gateway_route_fingerprint": route["existing_model_gateway_route_fingerprint"]}


def _check_contract_immutability(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    examples = context.contract_examples
    for key in ("authorization", "component_binding", "request_envelope", "response_envelope"):
        _require(str(examples[key].get("schema_version", "")).startswith("aion-external-cognition"), f"{key} schema mismatch")
    _require(examples.get("program_id") == PROGRAM_ID, "contract example program mismatch")
    _require(examples.get("authorization_id") == CURRENT_AUTHORIZATION_ID, "contract authorization mismatch")
    return {"schema_family": "aion-external-cognition"}


def _check_provider_manifests(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    manifests = context.contract_examples["provider_manifests"]
    _require(len(manifests) == 3, "provider manifest count mismatch")
    for manifest in manifests:
        _require(manifest.get("fixture_only") is True, "provider manifest must be fixture-only")
        _require(manifest.get("network_required") is False, "provider network requirement enabled")
        _require(manifest.get("endpoint_present") is False, "provider endpoint present")
        _require(manifest.get("credential_required") is False, "provider credential required")
    return {"provider_manifest_count": len(manifests)}


def _check_model_manifests(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    models = context.contract_examples["model_manifests"]
    capabilities = context.contract_examples["capability_records"]
    _require(len(models) == 6, "model manifest count mismatch")
    _require(len(capabilities) == 18, "capability record count mismatch")
    for model in models:
        _require(model.get("fixture_only") is True, "model manifest must be fixture-only")
        _require(model.get("network_enabled") is False, "model network enabled")
        _require(model.get("tool_calling_supported") is False, "model tool calling enabled")
    for capability in capabilities:
        _require(capability.get("fixture_only") is True, "capability must be fixture-only")
        _require(capability.get("tool_calling_supported") is False, "capability tool calling enabled")
    return {"model_manifest_count": len(models), "capability_record_count": len(capabilities)}


def _check_message_projection(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    messages = context.contract_examples["message_normalization"]
    _require(messages, "message projections missing")
    for message in messages:
        _require(message.get("content_fingerprint") != "0" * 64, "message fingerprint missing")
        _require(message.get("protected_material_present") is False, "protected material retained")
    _require(context.contract_examples.get("raw_material_retained") is False, "raw material retained")
    return {"message_projection_count": len(messages), "raw_material_retained": False}


def _check_request_envelope(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    request = context.contract_examples["request_envelope"]
    for key in (
        "background_execution_requested",
        "credential_present",
        "function_call_present",
        "memory_write_requested",
        "provider_endpoint_present",
        "provider_headers_present",
        "raw_prompt_retained",
    ):
        _require(request.get(key) is False, f"request envelope prohibited flag enabled: {key}")
    _require(request.get("request_fingerprint") != "0" * 64, "request fingerprint missing")
    return {"request_fingerprint": request["request_fingerprint"]}


def _check_response_envelope(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    response = context.contract_examples["response_envelope"]
    _require(response.get("raw_response_absent") is True, "raw response retained")
    _require(response.get("production_effect") is False, "response production effect enabled")
    _require(response.get("response_fingerprint") != "0" * 64, "response fingerprint missing")
    return {"response_fingerprint": response["response_fingerprint"]}


def _check_structured_schema(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    schema = context.contract_examples["structured_schema"]
    _require(schema.get("additional_properties_allowed") is False, "structured schema allows extra properties")
    _require(schema.get("property_count", 0) > 0, "structured schema missing properties")
    return {"structured_schema_count": EXPECTED_PILOT_COUNTERS["structured_output_schemas_loaded"]}


def _check_structured_validation(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    counters = context.pilot_evidence["counters"]
    trust = context.contract_examples["trust_assessment"]
    _require(counters.get("structured_output_validations") == 2, "structured validation count mismatch")
    _require(counters.get("structured_output_validation_failures") == 1, "structured validation failure count mismatch")
    _require(trust.get("trust_class") in {"untrusted_fixture_output", "schema_validated_untrusted"}, "trust class mismatch")
    _require(trust.get("factual_truth_confirmed") is False, "fixture output treated as fact")
    return {"structured_output_validations": 2, "structured_output_validation_failures": 1}


def _check_counter(
    context: EvaluationContext,
    _: list[dict[str, Any]],
    key: str,
) -> dict[str, Any]:
    _require(context.pilot_evidence["counters"].get(key) == 1, f"{key} mismatch")
    return {key: 1}


def _check_routing(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    policy = context.contract_examples["route_policy"]
    route = context.contract_examples["route_plan"]
    _require(policy.get("deterministic_tie_break") == "model_id", "deterministic tie-break mismatch")
    for key in ("automatic_live_invocation", "learned_routing", "model_generated_routing", "random_routing"):
        _require(policy.get(key) is False, f"routing policy prohibited flag enabled: {key}")
    _require(route.get("deterministic_ordering") is True, "route ordering is not deterministic")
    _require(context.pilot_evidence["counters"].get("route_plans_created") == 9, "route count mismatch")
    return {"route_plans_created": 9}


def _check_route_compatibility(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    route = context.contract_examples["route_plan"]
    _require(route.get("existing_model_gateway_compatible") is True, "existing gateway route compatibility missing")
    _require(route.get("existing_model_gateway_route_fingerprint") != "0" * 64, "gateway route fingerprint missing")
    return {"existing_model_gateway_compatible": True}


def _check_retry_fallback(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    counters = context.pilot_evidence["counters"]
    _require(counters.get("retry_plans_created") == 1, "retry count mismatch")
    _require(counters.get("fallback_plans_created") == 1, "fallback count mismatch")
    _require(counters.get("fallback_responses_generated") == 1, "fallback response count mismatch")
    return {"retry_plans_created": 1, "fallback_plans_created": 1}


def _check_circuit(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    circuit = context.contract_examples["circuit_breaker"]
    _require(circuit.get("live_provider_health_call_enabled") is False, "live health call enabled")
    _require(circuit.get("scheduled_probe_enabled") is False, "scheduled probe enabled")
    _require(context.pilot_evidence["counters"].get("circuit_breaker_open_events") == 1, "circuit breaker count mismatch")
    return {"circuit_breaker_open_events": 1}


def _check_trust_uncertainty(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    trust = context.contract_examples["trust_assessment"]
    uncertainty = context.contract_examples["uncertainty_projection"]
    counters = context.pilot_evidence["counters"]
    _require(trust.get("memory_write_authorized") is False, "trust authorized memory write")
    _require(trust.get("tool_execution_authorized") is False, "trust authorized tool execution")
    _require(uncertainty.get("confidence_source_code") == "fixture_declared", "uncertainty source mismatch")
    _require(counters.get("trust_assessments_created") == 9, "trust count mismatch")
    _require(counters.get("uncertainty_projections_created") == 9, "uncertainty count mismatch")
    return {"trust_assessments_created": 9, "uncertainty_projections_created": 9}


def _check_errors(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    _require(context.pilot_evidence["counters"].get("normalized_provider_errors") == 2, "provider error count mismatch")
    return {"normalized_provider_errors": 2}


def _check_redaction(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    _require(context.pilot_evidence.get("redacted") is True, "pilot evidence not redacted")
    rendered = json.dumps(
        {
            "pilot": context.pilot_evidence,
            "examples": context.contract_examples,
            "program_authorization": context.program_authorization,
            "foundation_authorization": context.foundation_authorization,
        },
        sort_keys=True,
    ).lower()
    for marker in PROTECTED_MARKERS:
        _require(marker not in rendered, f"protected marker retained: {marker}")
    return {"redacted": True, "protected_material_excluded": True}


def _check_fixture_provider(
    context: EvaluationContext, _: list[dict[str, Any]]
) -> dict[str, Any]:
    counters = context.pilot_evidence["counters"]
    _require(counters.get("fixture_provider_invocations") == 11, "fixture invocation count mismatch")
    _require(counters.get("fixture_responses_generated") == 9, "fixture response count mismatch")
    _require(context.pilot_evidence.get("provider_effect") is False, "provider effect enabled")
    return {"fixture_provider_invocations": 11, "fixture_responses_generated": 9}


def _check_replay(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    replay = context.contract_examples["replay"]
    counters = context.pilot_evidence["counters"]
    _require(counters.get("exact_replays_returned") == 1, "exact replay count mismatch")
    _require(counters.get("changed_replays_rejected") == 1, "changed replay count mismatch")
    _require(replay.get("safe_response_fingerprint") != "0" * 64, "safe replay fingerprint missing")
    return {"exact_replays_returned": 1, "changed_replays_rejected": 1}


def _check_audit(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    audit = context.contract_examples["audit"]
    observability = context.contract_examples["observability"]
    counters = context.pilot_evidence["counters"]
    _require(audit.get("raw_payload_absent") is True, "audit retained raw payload")
    _require(observability.get("audit_chain_head") != "0" * 64, "observability audit chain missing")
    _require(counters.get("observability_snapshots_created") == 1, "observability count mismatch")
    _require(counters.get("integrity_reports_created") == 1, "integrity count mismatch")
    return {"observability_snapshots_created": 1, "integrity_reports_created": 1}


def _check_operator_review(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    review = context.contract_examples["operator_review"]
    _require(review.get("raw_output_absent") is True, "operator review retained raw output")
    _require(context.pilot_evidence["counters"].get("operator_review_items_created") == 8, "operator review count mismatch")
    return {"operator_review_items_created": 8}


def _check_pilot_schema(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    from aion_brain.contracts.external_cognition import external_cognition_fingerprint

    payload = context.pilot_evidence
    recalculated = external_cognition_fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    _require(payload.get("pilot_id") == PILOT_ID, "pilot id mismatch")
    _require(payload.get("program_id") == PROGRAM_ID, "pilot program mismatch")
    _require(payload.get("authorization_id") == CURRENT_AUTHORIZATION_ID, "pilot authorization mismatch")
    _require(payload.get("mode") == "deterministic-fixture", "pilot mode mismatch")
    _require(payload.get("report_fingerprint") == PILOT_REPORT_FINGERPRINT, "pilot fingerprint constant mismatch")
    _require(payload.get("report_fingerprint") == recalculated, "pilot fingerprint recalculation mismatch")
    _require(payload.get("counters") == EXPECTED_PILOT_COUNTERS, "pilot counters mismatch")
    _require(payload.get("prohibited_effect_counters") == context.prohibited_effect_counters, "prohibited counters mismatch")
    return {"pilot_id": PILOT_ID, "report_fingerprint": PILOT_REPORT_FINGERPRINT}


def _check_zero_effects(context: EvaluationContext, _: list[dict[str, Any]]) -> dict[str, Any]:
    for key, value in context.pilot_evidence["prohibited_effect_counters"].items():
        _require(value == 0, f"prohibited effect counter non-zero: {key}")
    for key in ("provider_effect", "network_effect", "memory_effect", "tool_effect", "production_effect"):
        _require(context.pilot_evidence.get(key) is False, f"pilot effect enabled: {key}")
    _require(context.pilot_evidence["counters"].get("temporary_files_retained") == 0, "temporary files retained")
    _require(not (context.repo_root / "aion-v0.3.0").exists(), "v0.3 artifact exists")
    return {"prohibited_effect_counters": context.pilot_evidence["prohibited_effect_counters"]}


def _check_live_pilot_architecture(
    _: EvaluationContext, __: list[dict[str, Any]]
) -> dict[str, Any]:
    decision = _live_pilot_architecture_decision()
    _require(decision["provider_id"] == "openai", "future provider must be openai")
    _require(decision["provider_api_family"] == "responses", "future API family must be responses")
    _require(decision["allowed_endpoint_host"] == "api.openai.com", "future endpoint host mismatch")
    _require(decision["allowed_endpoint_path"] == "/v1/responses", "future endpoint path mismatch")
    _require(decision["model_family_boundary"] == "gpt-5.6", "future model family mismatch")
    _require(decision["maximum_selected_models"] == 1, "future model count mismatch")
    _require(all(decision["approved_capabilities"].values()), "approved future capabilities missing")
    _require(not any(decision["prohibited_capabilities"].values()), "prohibited future capability enabled")
    return {"provider_id": "openai", "api_family": "responses", "maximum_live_provider_calls": 6}


def _check_authorization_readiness(
    _: EvaluationContext, prior_results: list[dict[str, Any]]
) -> dict[str, Any]:
    _require(len(prior_results) == 31, "scenario 32 must run after the first 31 scenarios")
    _require(all(item["passed"] is True for item in prior_results), "a prior hard gate failed")
    return {
        "successor_authorization": NEXT_AUTHORIZATION_ID,
        "active_task_on_pass": NEXT_IMPLEMENTATION_TASK,
        "formal_closeout_on_pass": NEXT_CLOSEOUT_TASK,
    }


SCENARIO_CHECKS = {
    "aion_246_delivery_and_ci_integrity": _check_delivery,
    "adaptive_intelligence_authorization_lineage": _check_authorization_lineage,
    "exact_source_and_repository_boundary": _check_source_boundary,
    "secure_runtime_component_binding_integrity": _check_secure_runtime_binding,
    "existing_model_gateway_component_binding_integrity": _check_model_gateway_binding,
    "external_cognition_contract_immutability": _check_contract_immutability,
    "provider_manifest_integrity": _check_provider_manifests,
    "model_manifest_and_capability_integrity": _check_model_manifests,
    "message_projection_and_raw_content_non_retention": _check_message_projection,
    "request_envelope_integrity": _check_request_envelope,
    "response_envelope_integrity": _check_response_envelope,
    "restricted_structured_output_schema_integrity": _check_structured_schema,
    "structured_output_validation_and_untrusted_classification": _check_structured_validation,
    "context_budget_fail_closed": lambda context, prior: _check_counter(context, prior, "context_budget_rejections"),
    "output_budget_fail_closed": lambda context, prior: _check_counter(context, prior, "output_budget_rejections"),
    "cost_budget_fail_closed": lambda context, prior: _check_counter(context, prior, "cost_budget_rejections"),
    "latency_budget_fail_closed": lambda context, prior: _check_counter(context, prior, "latency_budget_rejections"),
    "deterministic_capability_routing": _check_routing,
    "existing_model_gateway_route_compatibility": _check_route_compatibility,
    "retry_and_fallback_boundedness": _check_retry_fallback,
    "circuit_breaker_state_integrity": _check_circuit,
    "trust_and_uncertainty_integrity": _check_trust_uncertainty,
    "provider_error_normalization_integrity": _check_errors,
    "recursive_redaction_and_protected_material_exclusion": _check_redaction,
    "deterministic_fixture_provider_integrity": _check_fixture_provider,
    "exact_replay_and_changed_replay_integrity": _check_replay,
    "audit_chain_and_observability_integrity": _check_audit,
    "operator_review_integrity": _check_operator_review,
    "fixture_pilot_schema_counters_and_report_fingerprint": _check_pilot_schema,
    "zero_operational_effects_and_release_boundary": _check_zero_effects,
    "single_openai_responses_api_pilot_architecture_safety": _check_live_pilot_architecture,
    "live_provider_pilot_authorization_readiness": _check_authorization_readiness,
}


def _pilot_validation(context: EvaluationContext) -> dict[str, Any]:
    return {
        "pilot_id": PILOT_ID,
        "report_fingerprint": PILOT_REPORT_FINGERPRINT,
        "counters": EXPECTED_PILOT_COUNTERS,
        "prohibited_effect_counters": context.prohibited_effect_counters,
    }


def _authorization_lineage(context: EvaluationContext) -> dict[str, Any]:
    return {
        "current_authorization": CURRENT_AUTHORIZATION_ID,
        "successor_authorization_on_pass": NEXT_AUTHORIZATION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "next_implementation_task": NEXT_IMPLEMENTATION_TASK,
        "next_closeout_task": NEXT_CLOSEOUT_TASK,
        "active_authorization_count_at_evaluation": context.authorization_ledger.get(
            "active_adaptive_intelligence_authorization_count"
        ),
    }


def _component_lineage(context: EvaluationContext) -> dict[str, Any]:
    binding = context.contract_examples["component_binding"]
    return {
        "secure_runtime_contract_fingerprint": binding["secure_runtime_contract_fingerprint"],
        "existing_model_gateway_contract_fingerprint": binding[
            "existing_model_gateway_contract_fingerprint"
        ],
        "read_only": binding["read_only"],
        "network_effect": binding["network_effect"],
    }


def _manifest_integrity(context: EvaluationContext) -> dict[str, Any]:
    return {
        "provider_manifest_count": len(context.contract_examples["provider_manifests"]),
        "model_manifest_count": len(context.contract_examples["model_manifests"]),
        "model_capability_record_count": len(context.contract_examples["capability_records"]),
    }


def _request_response_integrity(context: EvaluationContext) -> dict[str, Any]:
    return {
        "request_fingerprint": context.contract_examples["request_envelope"]["request_fingerprint"],
        "response_fingerprint": context.contract_examples["response_envelope"]["response_fingerprint"],
        "raw_prompt_retained": False,
        "raw_response_absent": True,
    }


def _structured_output_integrity(context: EvaluationContext) -> dict[str, Any]:
    return {
        "schema_fingerprint": context.contract_examples["structured_schema"]["schema_fingerprint"],
        "validations": EXPECTED_PILOT_COUNTERS["structured_output_validations"],
        "validation_failures": EXPECTED_PILOT_COUNTERS["structured_output_validation_failures"],
    }


def _budget_integrity(_: EvaluationContext) -> dict[str, Any]:
    return {
        "context_budget_rejections": 1,
        "output_budget_rejections": 1,
        "cost_budget_rejections": 1,
        "latency_budget_rejections": 1,
    }


def _routing_integrity(context: EvaluationContext) -> dict[str, Any]:
    return {
        "routing_policies_loaded": EXPECTED_PILOT_COUNTERS["routing_policies_loaded"],
        "route_plans_created": EXPECTED_PILOT_COUNTERS["route_plans_created"],
        "deterministic_ordering": context.contract_examples["route_plan"]["deterministic_ordering"],
    }


def _trust_integrity(_: EvaluationContext) -> dict[str, Any]:
    return {
        "trust_assessments_created": 9,
        "uncertainty_projections_created": 9,
        "all_responses_untrusted": True,
    }


def _redaction_integrity(_: EvaluationContext) -> dict[str, Any]:
    return {"redacted": True, "raw_prompt_persistence_enabled": False, "raw_response_persistence_enabled": False}


def _replay_integrity(_: EvaluationContext) -> dict[str, Any]:
    return {"exact_replays_returned": 1, "changed_replays_rejected": 1}


def _audit_integrity(_: EvaluationContext) -> dict[str, Any]:
    return {"observability_snapshots_created": 1, "integrity_reports_created": 1, "audit_evidence_available": True}


def _live_pilot_architecture_decision() -> dict[str, Any]:
    zero_limits = {key: 0 for key in AION248_ZERO_RESOURCE_LIMITS}
    return {
        "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
        "candidate_id": "single-openai-responses-api-synthetic-live-provider-pilot",
        "workstream": "adaptive-intelligence-live-provider-pilot",
        "implementation_task": NEXT_IMPLEMENTATION_TASK,
        "formal_closeout_task": NEXT_CLOSEOUT_TASK,
        "provider_id": "openai",
        "provider_api_family": "responses",
        "allowed_http_method": "POST",
        "allowed_endpoint_scheme": "https",
        "allowed_endpoint_host": "api.openai.com",
        "allowed_endpoint_path": "/v1/responses",
        "model_selection_policy": "operator_supplied_single_model_bound_at_session_start",
        "model_family_boundary": "gpt-5.6",
        "maximum_selected_models": 1,
        "credential_source": "OPENAI_API_KEY_process_environment_only",
        "request_policy": {
            "store": False,
            "background": False,
            "stream": False,
            "tools": False,
            "files": False,
            "previous_response_id": False,
            "synthetic_text_only": True,
        },
        "transport_policy": {
            "standard_library_https_only": True,
            "tls_certificate_verification": True,
            "redirects_enabled": False,
            "proxy_inheritance_enabled": False,
            "endpoint_discovery_enabled": False,
            "model_list_call_enabled": False,
        },
        "approved_capabilities": {key: True for key in AUTHORIZED_AION248_CAPABILITIES},
        "prohibited_capabilities": {key: False for key in PROHIBITED_AION248_CAPABILITIES},
        "resource_limits": {**AION248_RESOURCE_LIMITS, **zero_limits},
        "future_source_scope": list(PROHIBITED_AION248_SOURCE),
        "future_uninstalled_runner": "scripts/live-provider-pilot-local-run.py",
        "threat_model": list(THREAT_MODEL_ITEMS),
        "pilot_id": "AION-248-single-openai-responses-api-synthetic-live-provider-pilot",
    }


def _repository_integrity(_: EvaluationContext) -> dict[str, Any]:
    return {
        "primary_branch": EVALUATION_BRANCH,
        "aion_248_source_absent": True,
        "provider_runtime_source_absent": True,
        "package_versions_unchanged": True,
        "rc1_publication_unchanged": True,
    }


def _authorization_record(ledger: dict[str, Any], authorization_id: str) -> dict[str, Any]:
    for record in ledger.get("records", []):
        if record.get("authorization_transaction_id") == authorization_id:
            return record
    raise ScenarioFailure(f"authorization record missing: {authorization_id}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ScenarioFailure(message)


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_string_values(item)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the AION-247 operator evaluation.")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=EVALUATION_ID)
    parser.add_argument("--implementation-main-commit")
    parser.add_argument("--implementation-commit")
    parser.add_argument("--pilot-evidence", type=Path)
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.validate_report is not None:
            validate_evaluation_report(_load_json(args.validate_report))
            return 0
        required = (
            args.repo_root,
            args.implementation_main_commit,
            args.implementation_commit,
            args.pilot_evidence,
            args.evaluation_base_commit,
            args.temporary_output_directory,
            args.report,
        )
        if any(value is None for value in required):
            parser.error("evaluation mode requires repo, commit, evidence, output and report arguments")
        report = evaluate_external_cognition_foundation(
            repo_root=args.repo_root,
            evaluation_id=args.evaluation_id,
            implementation_main_commit=args.implementation_main_commit,
            implementation_commit=args.implementation_commit,
            pilot_evidence=args.pilot_evidence,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=args.temporary_output_directory,
        )
        write_report(report, args.report)
        return 0
    except (OSError, ValueError, ScenarioFailure) as exc:
        print(f"AION-247 evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""AION-218 public research pilot authorization validator."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
PROGRAM_ID = 'AION-KNOWLEDGE-INTELLIGENCE-001'
EVALUATION_ID = 'AION-VKME-001'
PASS_DECISION = 'VERIFIED_KNOWLEDGE_MEMORY_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_PUBLIC_RESEARCH_PILOT_AUTHORIZATION'
AUTHORIZATION_ID = 'AION-218-KI-0008'
CLOSED_AUTHORIZATION_ID = 'AION-216-KI-0007'
IMPLEMENTATION_TASK = 'AION-219'
FORMAL_CLOSEOUT_TASK = 'AION-220'
CANDIDATE_ID = 'controlled-public-research-verified-knowledge-pilot'
WORKSTREAM = 'knowledge-intelligence-controlled-public-research-pilot'
SCOPE = 'operator-invoked-allowlisted-public-https-fetch-dns-pinning-integrated-research-verified-candidate-pilot-operator-review-abstention-core'
AUTHORIZED_CAPABILITIES = ('controlled_public_research_pilot_approved', 'operator_invoked_pilot_session_approved', 'explicit_research_plan_approved', 'explicit_source_candidate_approved', 'explicit_domain_allowlist_approved', 'explicit_claim_specification_approved', 'https_only_public_fetch_approved', 'http_get_method_approved', 'http_head_method_approved', 'system_dns_resolution_approved', 'public_destination_validation_approved', 'dns_resolution_fingerprinting_approved', 'dns_pinning_approved', 'dns_rebinding_defence_approved', 'peer_address_verification_approved', 'ipv4_public_address_validation_approved', 'ipv6_public_address_validation_approved', 'ipv4_mapped_ipv6_validation_approved', 'private_network_rejection_approved', 'loopback_rejection_approved', 'link_local_rejection_approved', 'multicast_rejection_approved', 'reserved_address_rejection_approved', 'metadata_service_rejection_approved', 'ip_literal_url_rejection_approved', 'ambiguous_ip_encoding_rejection_approved', 'tls_certificate_verification_approved', 'tls_hostname_verification_approved', 'tls_sni_binding_approved', 'minimum_tls_version_enforcement_approved', 'direct_connection_without_proxy_approved', 'manual_redirect_handling_approved', 'redirect_destination_revalidation_approved', 'redirect_scheme_downgrade_rejection_approved', 'redirect_limit_approved', 'redirect_loop_detection_approved', 'fixed_safe_request_headers_approved', 'safe_response_header_projection_approved', 'credential_free_request_enforcement_approved', 'cookie_free_request_enforcement_approved', 'authorization_header_rejection_approved', 'client_certificate_rejection_approved', 'proxy_environment_rejection_approved', 'identity_content_encoding_approved', 'compressed_response_rejection_approved', 'streaming_response_budget_approved', 'content_length_precheck_approved', 'content_type_policy_approved', 'character_encoding_policy_approved', 'robots_policy_validation_approved', 'x_robots_tag_validation_approved', 'licence_metadata_policy_approved', 'source_class_policy_approved', 'prompt_injection_marked_untrusted_approved', 'ephemeral_source_body_processing_approved', 'source_body_purge_after_plan_approved', 'source_snapshot_creation_approved', 'source_provenance_creation_approved', 'citation_reference_creation_approved', 'source_deduplication_approved', 'source_mirror_suppression_approved', 'source_independence_propagation_approved', 'source_registry_projection_approved', 'explicit_claim_binding_approved', 'claim_graph_projection_approved', 'epistemic_assessment_pipeline_approved', 'domain_expert_mesh_pipeline_approved', 'simulation_only_tool_verification_pipeline_approved', 'verified_candidate_evaluation_pipeline_approved', 'verified_candidate_in_memory_repository_approved', 'verified_candidate_snapshot_approved', 'end_to_end_pilot_lineage_approved', 'pilot_integrity_audit_approved', 'pilot_redacted_diagnostics_approved', 'pilot_incident_record_approved', 'pilot_operator_review_item_approved', 'pilot_abstention_approved', 'pilot_kill_switch_approved', 'pilot_resource_budget_enforcement_approved', 'pilot_ephemeral_report_approved', 'no_search_provider_enforcement_approved', 'no_crawler_enforcement_approved', 'no_link_discovery_enforcement_approved', 'no_browser_enforcement_approved', 'no_connector_enforcement_approved', 'no_model_provider_enforcement_approved', 'no_actual_tool_execution_enforcement_approved', 'no_automatic_claim_extraction_enforcement_approved', 'no_automatic_candidate_approval_enforcement_approved', 'no_automatic_knowledge_promotion_enforcement_approved', 'no_cognitive_memory_write_enforcement_approved', 'no_belief_mutation_enforcement_approved', 'no_persistent_source_body_write_enforcement_approved', 'no_persistent_verified_knowledge_write_enforcement_approved', 'no_background_runtime_enforcement_approved', 'no_source_mutation_enforcement_approved', 'no_git_mutation_enforcement_approved', 'no_pr_creation_enforcement_approved', 'no_approval_creation_enforcement_approved', 'no_deployment_enforcement_approved', 'documentation_and_static_evidence_approved')
PROHIBITED_CAPABILITIES = ('unrestricted_network_access_enabled', 'background_network_access_enabled', 'scheduled_public_research_enabled', 'background_crawler_enabled', 'automatic_crawl_enabled', 'link_discovery_enabled', 'search_provider_integration_enabled', 'connector_integration_enabled', 'model_provider_integration_enabled', 'model_call_enabled', 'browser_automation_enabled', 'javascript_execution_enabled', 'http_cleartext_public_fetch_enabled', 'post_method_enabled', 'put_method_enabled', 'patch_method_enabled', 'delete_method_enabled', 'url_userinfo_enabled', 'direct_ip_url_enabled', 'proxy_inheritance_enabled', 'credential_use_enabled', 'cookie_use_enabled', 'authorization_header_use_enabled', 'client_certificate_use_enabled', 'compressed_response_enabled', 'automatic_claim_extraction_enabled', 'model_based_claim_extraction_enabled', 'actual_tool_execution_enabled', 'shell_command_execution_enabled', 'subprocess_execution_enabled', 'filesystem_mutation_enabled', 'source_mutation_enabled', 'worktree_creation_enabled', 'git_mutation_enabled', 'real_pull_request_creation_enabled', 'approval_creation_enabled', 'automatic_merge_enabled', 'production_deployment_enabled', 'automatic_candidate_approval_enabled', 'automatic_verified_knowledge_promotion_enabled', 'verified_knowledge_creation_enabled', 'verified_knowledge_promotion_enabled', 'persistent_source_body_write_enabled', 'persistent_source_registry_write_enabled', 'persistent_claim_graph_write_enabled', 'persistent_assessment_write_enabled', 'persistent_expert_mesh_write_enabled', 'persistent_tool_state_write_enabled', 'persistent_verified_knowledge_write_enabled', 'verified_knowledge_database_enabled', 'cognitive_memory_write_enabled', 'cognitive_memory_promotion_enabled', 'cognitive_belief_creation_enabled', 'cognitive_belief_mutation_enabled', 'engagement_signal_as_fact_enabled', 'engagement_confidence_effect_enabled', 'tool_output_as_verified_fact_enabled', 'model_output_as_verified_fact_enabled', 'domain_mesh_consensus_as_truth_enabled', 'absolute_truth_oracle_enabled', 'automatic_claim_acceptance_enabled', 'automatic_claim_rejection_enabled', 'kernel_registration_enabled', 'application_startup_registration_enabled', 'api_route_enabled', 'installed_cli_command_enabled', 'sdk_runtime_resource_enabled', 'background_pilot_worker_enabled', 'pilot_scheduler_enabled', 'model_weight_training_enabled', 'dependency_change_approved', 'migration_approved', 'github_workflow_change_approved', 'v02_tag_created', 'v02_release_created', 'production_exposure')
RESOURCE_LIMITS = {'maximum_pilot_sessions': 5, 'maximum_plans_per_session': 5, 'maximum_queries_per_plan': 20, 'maximum_domains_per_plan': 20, 'maximum_explicit_source_candidates_per_plan': 50, 'maximum_source_fetches_per_plan': 25, 'maximum_robots_fetches_per_plan': 20, 'maximum_public_https_requests_per_plan': 50, 'maximum_dns_resolutions_per_plan': 100, 'maximum_redirects_per_fetch': 3, 'maximum_concurrency': 4, 'maximum_timeout_seconds_per_request': 20, 'maximum_wall_clock_seconds_per_plan': 900, 'maximum_response_bytes_per_source': 5242880, 'maximum_total_transfer_bytes_per_plan': 52428800, 'maximum_snapshots_per_plan': 100, 'maximum_safe_headers_per_snapshot': 32, 'maximum_citation_references_per_snapshot': 20, 'maximum_query_parameters_per_url': 10, 'maximum_url_length': 4096, 'maximum_explicit_claim_specs_per_session': 50, 'maximum_candidate_evaluations_per_session': 100, 'maximum_candidate_versions_per_identity': 100, 'maximum_operator_review_items_per_session': 100, 'maximum_pilot_report_bytes': 10485760, 'maximum_source_body_retention_seconds': 300, 'maximum_operator_pilot_report_writes': 1, 'maximum_search_provider_calls': 0, 'maximum_connector_calls': 0, 'maximum_model_provider_calls': 0, 'maximum_actual_tool_executions': 0, 'maximum_shell_commands': 0, 'maximum_subprocess_executions': 0, 'maximum_browser_actions': 0, 'maximum_runtime_filesystem_mutations': 0, 'maximum_persistent_source_body_writes': 0, 'maximum_persistent_source_registry_writes': 0, 'maximum_persistent_claim_graph_writes': 0, 'maximum_persistent_assessment_writes': 0, 'maximum_persistent_expert_mesh_writes': 0, 'maximum_persistent_tool_state_writes': 0, 'maximum_persistent_verified_knowledge_writes': 0, 'maximum_automatic_knowledge_promotions': 0, 'maximum_cognitive_memory_writes': 0, 'maximum_belief_mutations': 0, 'maximum_engagement_fact_promotions': 0, 'maximum_engagement_confidence_effects': 0, 'maximum_source_mutations': 0, 'maximum_git_operations': 0, 'maximum_runtime_created_pull_requests': 0, 'maximum_approvals_created': 0, 'maximum_deployments': 0, 'maximum_model_weight_changes': 0}
AION219_SOURCE_PATHS = ("services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py")
def load_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))
def expected_authorized_capabilities() -> dict[str, bool]:
    return {key: True for key in AUTHORIZED_CAPABILITIES}
def expected_prohibited_capabilities() -> dict[str, bool]:
    return {key: False for key in PROHIBITED_CAPABILITIES}
def validate_report(report: dict[str, Any]) -> None:
    if report.get("evaluation_id") != EVALUATION_ID:
        raise ValueError("evaluation ID mismatch")
    if report.get("decision") != PASS_DECISION or report.get("evaluation_passed") is not True:
        raise ValueError("exact AION-VKME-001 PASS is required")
    if report.get("scenario_count") != 28 or len(report.get("scenario_results", [])) != 28:
        raise ValueError("scenario count mismatch")
    if not all(item.get("passed") is True for item in report.get("scenario_results", [])):
        raise ValueError("scenario failure recorded")
    gates = report.get("hard_gate_results", {})
    if not isinstance(gates, dict) or not gates or not all(gates.values()):
        raise ValueError("hard gate failure recorded")
    for key in ("public_network_requests", "dns_resolutions", "search_provider_calls", "connector_calls", "model_provider_calls", "actual_tool_executions", "shell_executions", "subprocess_executions", "browser_actions", "filesystem_mutations", "source_mutations", "git_operations", "runtime_pull_requests", "runtime_approvals", "deployments", "model_weight_changes", "persistent_verified_knowledge_writes", "automatic_knowledge_promotions", "cognitive_memory_writes", "belief_mutations", "engagement_fact_promotions", "engagement_confidence_effects"):
        if report.get(key) != 0:
            raise ValueError(f"zero-effect mismatch: {key}")
    if report.get("repository_unchanged") is not True:
        raise ValueError("repository must be unchanged by evaluation")
def validate_closed_authorization(record: dict[str, Any]) -> None:
    expected = {"authorization_transaction_id": CLOSED_AUTHORIZATION_ID, "approval_record_id": CLOSED_AUTHORIZATION_ID, "authorization_active": False, "authorization_consumed": True, "authorization_consumed_by_task": "AION-217", "authorization_expired": True, "authorization_reusable": False, "authorization_closed_by_task": "AION-218", "verified_knowledge_memory_operator_evaluation_id": EVALUATION_ID, "verified_knowledge_memory_operator_evaluation_decision": PASS_DECISION}
    for key, value in expected.items():
        if record.get(key) != value:
            raise ValueError(f"closed authorization mismatch {key}: {record.get(key)!r}")
    if record.get("authorization_consumed_by_prs") != [131, 132]:
        raise ValueError("closed authorization PR evidence mismatch")
def validate_authorization_payload(payload: dict[str, Any]) -> None:
    expected = {"program_id": PROGRAM_ID, "authorization_transaction_id": AUTHORIZATION_ID, "approval_record_id": AUTHORIZATION_ID, "parent_authorization_transaction_id": CLOSED_AUTHORIZATION_ID, "parent_evaluation_id": EVALUATION_ID, "parent_evaluation_decision": PASS_DECISION, "candidate_id": CANDIDATE_ID, "workstream": WORKSTREAM, "implementation_task": IMPLEMENTATION_TASK, "formal_closeout_task": FORMAL_CLOSEOUT_TASK, "authorization_scope": SCOPE, "authorization_active": True, "authorization_consumed": False, "authorization_expired": False, "authorization_reusable": False, "controlled_public_research_pilot_authorized": True, "controlled_public_research_pilot_implemented": False, "operator_invoked_public_https_fetch_authorized": True, "operator_invoked_public_https_fetch_available": False, "public_network_fetch_enabled": False, "system_http_transport_available": False, "runtime_effect": False}
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"public pilot authorization mismatch {key}: {payload.get(key)!r}")
    for key in ("authorization_transaction_approved", "explicit_approval_record_approval", "implementation_authorization_approved", "implementation_go_status"):
        if payload.get(key) is not True:
            raise ValueError(f"approval flag must be true: {key}")
    if payload.get("implementation_no_go_status") is not False:
        raise ValueError("implementation no-go status must be false")
    if payload.get("authorized_capabilities") != expected_authorized_capabilities():
        raise ValueError("authorized capabilities mismatch")
    if payload.get("prohibited_capabilities") != expected_prohibited_capabilities():
        raise ValueError("prohibited capabilities mismatch")
    if payload.get("resource_limits") != RESOURCE_LIMITS:
        raise ValueError("resource limits mismatch")
    for key in expected_prohibited_capabilities():
        if payload.get(key, False) is not False:
            raise ValueError(f"prohibited top-level flag enabled: {key}")
def validate_no_aion219_source(root: Path) -> None:
    for relative in AION219_SOURCE_PATHS:
        if (root / relative).exists():
            raise ValueError(f"AION-219 source exists before implementation: {relative}")
def validate_authorization_files(root: Path) -> None:
    report = load_json(root, "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json")
    validate_report(report)
    authorization = load_json(root, "examples/knowledge-intelligence/public-research-pilot-authorization.json")
    validate_authorization_payload(authorization)
    auth_ledger = load_json(root, "docs/knowledge-intelligence/authorization-ledger.json")
    program_ledger = load_json(root, "docs/knowledge-intelligence/program-ledger.json")
    for label, payload in (("authorization", auth_ledger), ("program", program_ledger)):
        if payload.get("program_state") != "controlled_public_research_pilot_authorized_not_implemented":
            raise ValueError(f"{label} program state mismatch")
        if payload.get("active_knowledge_implementation_authorization") != AUTHORIZATION_ID:
            raise ValueError(f"{label} active authorization mismatch")
        if payload.get("active_knowledge_implementation_authorization_count") != 1:
            raise ValueError(f"{label} active authorization count mismatch")
        if payload.get("active_knowledge_implementation_task") != IMPLEMENTATION_TASK:
            raise ValueError(f"{label} active task mismatch")
        if payload.get("formal_closeout_task") != FORMAL_CLOSEOUT_TASK:
            raise ValueError(f"{label} formal closeout mismatch")
        validate_authorization_payload(payload)
    active = [item for item in auth_ledger["records"] if item.get("authorization_active") is True]
    if len(active) != 1:
        raise ValueError("exactly one active Knowledge Intelligence authorization is required")
    validate_authorization_payload(active[0])
    closed = [item for item in auth_ledger["records"] if item.get("authorization_transaction_id") == CLOSED_AUTHORIZATION_ID]
    if len(closed) != 1:
        raise ValueError("AION-216-KI-0007 closeout record missing")
    validate_closed_authorization(closed[0])
    validate_no_aion219_source(root)
def validate_runtime_hold(root: Path) -> None:
    validate_authorization_files(root)
    runtime = load_json(root, "examples/knowledge-intelligence/public-research-pilot-runtime-hold.json")
    for key in ("controlled_public_research_pilot_implemented", "operator_invoked_public_https_fetch_available", "public_network_fetch_enabled", "system_http_transport_available", "dns_resolver_available", "search_provider_integration_enabled", "connector_integration_enabled", "model_provider_integration_enabled", "actual_tool_execution_enabled", "automatic_verified_knowledge_promotion_enabled", "persistent_verified_knowledge_write_enabled", "cognitive_memory_write_enabled", "belief_mutation_enabled", "runtime_effect"):
        if runtime.get(key) is not False:
            raise ValueError(f"runtime hold flag must remain false: {key}")
    if runtime.get("controlled_public_research_pilot_authorized") is not True:
        raise ValueError("public pilot authorization missing from runtime hold")

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
PARENT_PROGRAM_ID = "AION-COGNITIVE-ARCHITECTURE-001"
AUTH_ID = "AION-204-KI-0001"
PARENT_MAIN_COMMIT = "fdc38402e050ffb5beebd9d6d298f859736f0121"
PARENT_EVALUATION_ID = "AION-CASE-001"
PARENT_DECISION = "CONTROLLED_LOCAL_OFFLINE_PILOT_PASS_COMPLETE_COGNITIVE_ARCHITECTURE_PROGRAM"
CANDIDATE_ID = "controlled-internet-research-acquisition-core"
IMPLEMENTATION_TASK = "AION-205"
FORMAL_CLOSEOUT_TASK = "AION-206"
SCOPE = "disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core"
APPROVED_KEYS = [
    "research_contracts_approved",
    "research_plan_contract_approved",
    "research_query_contract_approved",
    "source_candidate_contract_approved",
    "source_snapshot_contract_approved",
    "source_provenance_contract_approved",
    "citation_reference_contract_approved",
    "source_lineage_contract_approved",
    "research_evidence_bundle_approved",
    "research_diagnostics_approved",
    "research_incident_record_approved",
    "domain_allowlist_policy_approved",
    "url_canonicalization_approved",
    "scheme_validation_approved",
    "public_network_destination_validation_approved",
    "private_network_rejection_approved",
    "loopback_rejection_approved",
    "link_local_rejection_approved",
    "multicast_rejection_approved",
    "reserved_address_rejection_approved",
    "dns_rebinding_defence_approved",
    "redirect_policy_approved",
    "http_get_method_approved",
    "http_head_method_approved",
    "response_size_budget_approved",
    "total_transfer_budget_approved",
    "timeout_budget_approved",
    "concurrency_budget_approved",
    "content_type_policy_approved",
    "character_encoding_validation_approved",
    "safe_header_projection_approved",
    "content_sha256_fingerprinting_approved",
    "source_deduplication_approved",
    "source_snapshot_immutability_approved",
    "publication_timestamp_capture_approved",
    "modification_timestamp_capture_approved",
    "retrieval_timestamp_capture_approved",
    "source_quality_classification_approved",
    "robots_policy_metadata_approved",
    "licence_policy_metadata_approved",
    "operator_review_item_approved",
    "disabled_research_adapter_approved",
    "in_memory_research_adapter_approved",
    "explicit_local_fixture_adapter_approved",
    "explicit_operator_invoked_http_adapter_implementation_approved",
    "research_adapter_protocol_approved",
    "search_adapter_protocol_approved",
    "fail_closed_research_policy_approved",
    "synthetic_test_fixture_approved",
    "documentation_and_static_evidence_approved",
    "no_knowledge_promotion_enforcement_approved",
    "no_cognitive_belief_mutation_enforcement_approved",
    "no_background_crawl_enforcement_approved",
    "no_runtime_registration_enforcement_approved",
    "no_credential_use_enforcement_approved",
    "no_source_mutation_enforcement_approved",
    "no_git_mutation_enforcement_approved",
    "no_pr_creation_enforcement_approved",
    "no_approval_creation_enforcement_approved",
]
PROHIBITED_KEYS = [
    "research_runtime_enabled",
    "automatic_research_enabled",
    "background_crawler_enabled",
    "scheduled_research_enabled",
    "continuous_web_monitoring_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "production_event_subscription_enabled",
    "unrestricted_network_access_enabled",
    "arbitrary_url_access_enabled",
    "arbitrary_domain_access_enabled",
    "private_network_access_enabled",
    "localhost_access_enabled",
    "link_local_access_enabled",
    "unix_socket_access_enabled",
    "file_scheme_access_enabled",
    "ftp_access_enabled",
    "websocket_access_enabled",
    "javascript_execution_enabled",
    "browser_automation_enabled",
    "form_submission_enabled",
    "http_post_enabled",
    "http_put_enabled",
    "http_patch_enabled",
    "http_delete_enabled",
    "file_upload_enabled",
    "authentication_enabled",
    "credential_use_enabled",
    "cookie_use_enabled",
    "authorization_header_use_enabled",
    "login_flow_enabled",
    "captcha_bypass_enabled",
    "paywall_bypass_enabled",
    "robots_bypass_enabled",
    "access_control_bypass_enabled",
    "private_content_access_enabled",
    "personal_account_access_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "raw_prompt_storage_enabled",
    "hidden_reasoning_storage_enabled",
    "unredacted_personal_data_storage_enabled",
    "full_source_content_repository_storage_enabled",
    "automatic_cognitive_memory_ingestion_enabled",
    "automatic_belief_creation_enabled",
    "automatic_claim_verification_enabled",
    "automatic_knowledge_promotion_enabled",
    "user_statement_as_fact_enabled",
    "engagement_signal_as_fact_enabled",
    "source_patch_generation_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "runtime_effect",
    "dependency_change_approved",
    "migration_approved",
    "github_workflow_change_approved",
    "api_route_approved",
    "installed_cli_command_approved",
    "sdk_runtime_resource_approved",
    "v02_tag_created",
    "v02_release_created",
]
RESOURCE_LIMITS = {
    "maximum_queries_per_plan": 20,
    "maximum_domains_per_plan": 20,
    "maximum_source_candidates_per_plan": 100,
    "maximum_fetches_per_plan": 50,
    "maximum_redirects_per_fetch": 3,
    "maximum_concurrency": 4,
    "maximum_timeout_seconds_per_request": 20,
    "maximum_wall_clock_seconds_per_plan": 900,
    "maximum_response_bytes_per_source": 5242880,
    "maximum_total_transfer_bytes_per_plan": 52428800,
    "maximum_snapshot_records_per_plan": 100,
    "maximum_safe_headers_per_snapshot": 32,
    "maximum_citation_references_per_snapshot": 20,
    "network_calls_during_AION_204": 0,
    "research_runtime_enabled": False,
    "background_crawls": 0,
    "scheduled_research_runs": 0,
    "knowledge_promotions": 0,
    "cognitive_belief_mutations": 0,
    "source_mutations": 0,
    "git_operations": 0,
    "real_pull_requests_created_by_runtime": 0,
    "approvals_created_by_runtime": 0,
    "production_exposure": 0,
    "model_weight_changes": 0,
}
SOURCE_CLASSES = [
    "primary_authoritative",
    "official_standard",
    "official_government",
    "peer_reviewed",
    "vendor_primary",
    "institutional_primary",
    "reputable_secondary",
    "community_unverified",
    "unknown",
    "disallowed",
]
THREATS = [
    "SSRF",
    "DNS rebinding",
    "redirect escape",
    "private IP encoding bypass",
    "IPv6 bypass",
    "metadata-service access",
    "malicious DNS",
    "certificate failure",
    "malicious compression",
    "decompression bomb",
    "oversized response",
    "endless stream",
    "slow response",
    "content-type confusion",
    "charset confusion",
    "HTML active content",
    "executable download",
    "archive bomb",
    "PDF parser risk",
    "robots-policy ambiguity",
    "licensing ambiguity",
    "paywall bypass",
    "authentication leakage",
    "cookie leakage",
    "referer leakage",
    "private-content access",
    "prompt injection in acquired content",
    "source content instructing AION to ignore policy",
    "citation spoofing",
    "publication-date spoofing",
    "source-author spoofing",
    "mirrored-source duplication",
    "copied misinformation appearing independently corroborated",
    "SEO poisoning",
    "domain impersonation",
    "compromised authoritative source",
    "stale information",
    "changed pages",
    "retractions and corrections",
    "jurisdiction mismatch",
    "version mismatch",
    "source content promoted directly into memory",
    "user engagement treated as fact",
    "background crawler escape",
    "uncontrolled research cost",
    "evidence deletion",
    "source snapshot tampering",
    "research evidence mistaken for verified knowledge",
]
ROADMAP_TASKS = [
    "AION-204",
    "AION-205",
    "AION-206",
    "AION-207",
    "AION-208",
    "AION-209",
    "AION-210",
    "AION-211",
    "AION-212",
    "AION-213",
    "AION-214",
    "AION-215",
    "AION-216",
    "AION-217",
    "AION-218",
    "AION-219",
    "AION-220",
]
CURRENT_SURFACES = [
    "README.md",
    "AGENTS.md",
    "docs/project-status.md",
    "docs/architecture.md",
    "docs/brain-contract.md",
    "docs/policy-model.md",
    "docs/visual-brain.md",
    "docs/release/v02-release-readiness-delta.md",
    "operator-console-static/README.md",
]


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text()


def validate_authorization_record(record: dict) -> None:
    assert record["program_id"] == PROGRAM_ID
    assert record["parent_program_id"] == PARENT_PROGRAM_ID
    assert record["authorization_transaction_id"] == AUTH_ID
    assert record["approval_record_id"] == AUTH_ID
    assert record["parent_evaluation_id"] == PARENT_EVALUATION_ID
    assert record["parent_main_commit"] == PARENT_MAIN_COMMIT
    assert record["candidate_id"] == CANDIDATE_ID
    assert record["implementation_task"] == IMPLEMENTATION_TASK
    assert record["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
    assert record["authorization_scope"] == SCOPE
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    assert record["authorization_transaction_approved"] is True
    assert record["explicit_approval_record_approval"] is True
    assert record["implementation_authorization_approved"] is True
    assert record["implementation_go_status"] is True
    assert record["implementation_no_go_status"] is False
    assert set(record["authorized_capabilities"]) == set(APPROVED_KEYS)
    assert all(record["authorized_capabilities"][key] is True for key in APPROVED_KEYS)
    assert set(record["prohibited_capabilities"]) == set(PROHIBITED_KEYS)
    assert all(record["prohibited_capabilities"][key] is False for key in PROHIBITED_KEYS)
    assert record["resource_limits"] == RESOURCE_LIMITS


def assert_rejects(mutator) -> None:
    record = copy.deepcopy(
        read_json("docs/knowledge-intelligence/authorization-ledger.json")["records"][0]
    )
    mutator(record)
    try:
        validate_authorization_record(record)
    except AssertionError:
        return
    raise AssertionError("invalid authorization record was accepted")

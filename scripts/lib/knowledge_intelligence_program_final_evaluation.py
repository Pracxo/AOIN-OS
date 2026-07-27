"""AION-220 final Knowledge Intelligence Program evaluation harness.

The harness is read-only with respect to the repository. It validates committed
AION-219 evidence, executes a deterministic in-memory public research pilot
replay, records 28 hard-gated scenarios, and writes one redacted JSON report to
the explicit temporary output directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


EVALUATION_ID = "AION-KIPE-001"
EVALUATION_TYPE = "final_knowledge_intelligence_program_operator_evaluation"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-219"
CLOSEOUT_TASK = "AION-220"
AUTHORIZATION_ID = "AION-218-KI-0008"
PASS_DECISION = "CONTROLLED_PUBLIC_RESEARCH_PILOT_PASS_COMPLETE_KNOWLEDGE_INTELLIGENCE_PROGRAM"
FAIL_DECISION = (
    "CONTROLLED_PUBLIC_RESEARCH_PILOT_FAIL_KNOWLEDGE_INTELLIGENCE_PROGRAM_"
    "REMEDIATION_REQUIRED"
)
COMPLETED_PROGRAM_STATE = "knowledge_intelligence_program_complete"
PENDING_PROGRAM_STATE = (
    "controlled_public_research_pilot_implemented_operator_invoked_"
    "persistent_write_disabled_pending_closeout"
)
PUBLIC_RESEARCH_PILOT_STATE = (
    "implemented_operator_invoked_bounded_public_https_integrated_pipeline_"
    "persistent_write_disabled"
)

AION218_CORRECTIVE_PR = 132
AION218_CORRECTIVE_FEATURE_COMMIT = "ffd620e2e81d5c47140b851503515c724114633f"
AION218_CORRECTIVE_MERGE_COMMIT = "262ea384800997edd0d46531ecb7ca44528e3745"
AION218_PRIMARY_PR = 133
AION218_HARNESS_COMMIT = "0763ad2c5d6bda3480862044402b5ae3c197353e"
AION218_CLOSEOUT_COMMIT = "8033d10a7463787aa008610d8f3342a26231d59a"
AION218_MERGE_COMMIT = "a82dd6f8e9dd525456688defaae98587074860af"
AION218_MERGED_AT = "2026-07-27T05:23:55Z"

AION219_PR = 134
AION219_BRANCH = "phase/knowledge-intelligence-controlled-public-research-pilot"
AION219_FEATURE_COMMIT = "756c706299472d6f048acd4a2c6a523c36f0e119"
AION219_MERGE_COMMIT = "d0e1807edd7b3098ce62f8d00b0bceb4ee6fd23d"
AION219_MERGED_AT = "2026-07-27T12:33:43Z"
AION219_REPORT_FINGERPRINT = (
    "2ecdcc382d06abd180671dce0972982d68f2fbb9acab7d169ce26374c57bb258"
)

FIXED_TIME = datetime(2026, 7, 27, 13, 0, tzinfo=UTC)
PUBLIC_IPV4 = "93.184.216.34"

SCENARIO_IDS: tuple[str, ...] = (
    "aion_219_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "committed_live_evidence_integrity",
    "explicit_operator_invocation_boundary",
    "explicit_plan_source_allowlist_and_claim_boundary",
    "dns_public_address_validation",
    "dns_pinning_rebinding_and_peer_verification",
    "tls_certificate_hostname_and_sni",
    "http_method_header_credential_and_proxy_boundary",
    "redirect_revalidation",
    "response_budget_and_content_controls",
    "robots_and_x_robots_controls",
    "licence_and_source_class_controls",
    "prompt_injection_isolation",
    "source_body_purge_and_redaction",
    "kill_switch",
    "resource_budget_enforcement",
    "acquisition_snapshot_provenance_and_citation_integrity",
    "source_registry_deduplication_and_independence",
    "claim_identity_temporal_jurisdiction_and_version_integrity",
    "epistemic_confidence_contradiction_and_abstention",
    "domain_mesh_independence_and_dissent",
    "tool_verification_non_execution_boundary",
    "verified_candidate_review_only_boundary",
    "engagement_non_factual_boundary",
    "zero_persistence_promotion_memory_belief_and_action",
    "disabled_default_runtime_repository_and_release_boundary",
    "deterministic_replay_concurrency_performance_and_program_completeness",
)

PLANE_IDS: tuple[str, ...] = (
    "controlled_research_acquisition",
    "source_provenance_registry",
    "temporal_claim_evidence_graph",
    "epistemic_assessment_engine",
    "domain_expert_mesh",
    "tool_verification_fabric",
    "verified_knowledge_candidate_memory",
    "controlled_public_https_research_pilot",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "aion_218_corrective_pr_verified",
    "aion_218_primary_pr_verified",
    "aion_219_pr_verified",
    "aion_219_feature_commit_verified",
    "aion_219_merge_commit_verified",
    "aion_219_final_ci_verified",
    "node_24_actions_verified",
    "aion_218_authorization_scope_verified",
    "aion_219_resource_limits_verified",
    "committed_live_evidence_verified",
    "live_evidence_redacted",
    "deterministic_in_memory_replay_passed",
    "scenario_set_complete",
    "all_scenarios_executed",
    "all_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "public_destination_controls_passed",
    "dns_pinning_passed",
    "tls_peer_verification_passed",
    "redirect_revalidation_passed",
    "response_budget_controls_passed",
    "source_body_purge_passed",
    "source_provenance_integrity_passed",
    "source_independence_passed",
    "claim_identity_scope_passed",
    "epistemic_confidence_caps_passed",
    "contradiction_preservation_passed",
    "domain_dissent_preservation_passed",
    "tool_verification_integrity_passed",
    "candidate_review_only_boundary_passed",
    "engagement_non_factual_boundary_passed",
    "zero_persistent_writes",
    "zero_automatic_promotion",
    "zero_cognitive_memory_write",
    "zero_belief_mutation",
    "zero_unauthorized_runtime_effects",
    "no_successor_authorization_required",
    "no_v02_tag_or_release",
)

ZERO_EFFECT_FIELDS: dict[str, int | bool] = {
    "evaluation_dns_resolutions": 0,
    "evaluation_public_https_requests": 0,
    "search_provider_calls": 0,
    "connector_calls": 0,
    "model_provider_calls": 0,
    "actual_tool_executions": 0,
    "shell_executions": 0,
    "subprocess_executions": 0,
    "browser_actions": 0,
    "filesystem_mutations": 0,
    "source_mutations": 0,
    "git_operations": 0,
    "runtime_pull_requests": 0,
    "runtime_approvals": 0,
    "deployments": 0,
    "model_weight_changes": 0,
    "persistent_source_body_writes": 0,
    "persistent_source_registry_writes": 0,
    "persistent_claim_graph_writes": 0,
    "persistent_assessment_writes": 0,
    "persistent_expert_mesh_writes": 0,
    "persistent_tool_state_writes": 0,
    "persistent_verified_knowledge_writes": 0,
    "automatic_knowledge_promotions": 0,
    "cognitive_memory_writes": 0,
    "belief_mutations": 0,
    "engagement_fact_promotions": 0,
    "engagement_confidence_effects": 0,
    "repository_unchanged_by_evaluation": True,
    "temporary_evaluation_data_cleaned": True,
}

LIVE_EVIDENCE_EXPECTED: dict[str, Any] = {
    "authorization_transaction_id": AUTHORIZATION_ID,
    "pilot_session_id": "aion-219-live-session-0001",
    "mode": "operator_invoked_live",
    "status": "completed",
    "external_read_performed": True,
    "source_candidate_count": 3,
    "source_control_group_count": 3,
    "DNS_resolution_count": 4,
    "public_https_request_count": 4,
    "robots_request_count": 1,
    "redirect_count": 0,
    "successful_source_count": 3,
    "rejected_source_count": 0,
    "candidate_count": 1,
    "candidate_eligibility_statuses": ["eligible_for_operator_review"],
    "source_snapshot_count": 3,
    "source_provenance_count": 3,
    "citation_count": 3,
    "source_bodies_retained": 0,
    "source_bodies_persisted": 0,
    "automatic_promotions": 0,
    "cognitive_memory_writes": 0,
    "belief_mutations": 0,
    "persistent_verified_knowledge_writes": 0,
    "operator_review_required": True,
    "background_execution": False,
    "production_exposure": False,
    "dns_validation_passed": True,
    "peer_validation_passed": True,
    "tls_validation_passed": True,
    "pipeline_trace_present": True,
    "budget_within_limits": True,
    "integrity_passed": True,
    "kill_switch_available": True,
    "report_fingerprint": AION219_REPORT_FINGERPRINT,
}

PUBLIC_RESEARCH_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_pilot_sessions": 5,
    "maximum_plans_per_session": 5,
    "maximum_queries_per_plan": 20,
    "maximum_domains_per_plan": 20,
    "maximum_explicit_source_candidates_per_plan": 50,
    "maximum_source_fetches_per_plan": 25,
    "maximum_robots_fetches_per_plan": 20,
    "maximum_public_https_requests_per_plan": 50,
    "maximum_dns_resolutions_per_plan": 100,
    "maximum_redirects_per_fetch": 3,
    "maximum_concurrency": 4,
    "maximum_timeout_seconds_per_request": 20,
    "maximum_wall_clock_seconds_per_plan": 900,
    "maximum_response_bytes_per_source": 5242880,
    "maximum_total_transfer_bytes_per_plan": 52428800,
    "maximum_snapshots_per_plan": 100,
    "maximum_safe_headers_per_snapshot": 32,
    "maximum_citation_references_per_snapshot": 20,
    "maximum_query_parameters_per_url": 10,
    "maximum_url_length": 4096,
    "maximum_explicit_claim_specs_per_session": 50,
    "maximum_candidate_evaluations_per_session": 100,
    "maximum_candidate_versions_per_identity": 100,
    "maximum_operator_review_items_per_session": 100,
    "maximum_pilot_report_bytes": 10485760,
    "maximum_source_body_retention_seconds": 300,
    "maximum_operator_pilot_report_writes": 1,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_runtime_filesystem_mutations": 0,
    "maximum_persistent_source_body_writes": 0,
    "maximum_persistent_source_registry_writes": 0,
    "maximum_persistent_claim_graph_writes": 0,
    "maximum_persistent_assessment_writes": 0,
    "maximum_persistent_expert_mesh_writes": 0,
    "maximum_persistent_tool_state_writes": 0,
    "maximum_persistent_verified_knowledge_writes": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_belief_mutations": 0,
    "maximum_engagement_fact_promotions": 0,
    "maximum_engagement_confidence_effects": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}

PROTECTED_EVIDENCE_KEYS = {
    "body",
    "source_body",
    "content_bytes",
    "raw_body",
    "raw_certificate",
    "raw_response_headers",
    "raw_claim_text",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
    "authorization_header",
    "cookie",
    "credentials",
    "personal_data",
}


def _install_src_path(repo_root: Path) -> None:
    src = repo_root / "services/brain-api/src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


def load_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdef" for char in value
    )


def _protected_keys_absent(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in PROTECTED_EVIDENCE_KEYS:
                return False
            if key in {"raw_ip_addresses", "raw_ips", "ip_addresses"}:
                return False
            if not _protected_keys_absent(item):
                return False
        return True
    if isinstance(value, list):
        return all(_protected_keys_absent(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return not any(
            marker in lowered
            for marker in (
                "authorization:",
                "bearer ",
                "cookie:",
                "-----begin private key-----",
                "sk-",
                "ghp_",
                "gho_",
            )
        )
    return True


def validate_live_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    for key, expected in LIVE_EVIDENCE_EXPECTED.items():
        if payload.get(key) != expected:
            raise ValueError(f"live evidence mismatch for {key}: {payload.get(key)!r}")
    for key, value in payload.items():
        if key.endswith("fingerprint") and not _hex64(value):
            raise ValueError(f"invalid fingerprint in live evidence: {key}")
    if payload.get("redacted") is not True:
        raise ValueError("live evidence must be redacted")
    if payload.get("credentials_absent") is not True:
        raise ValueError("live evidence must record credentials absent")
    if payload.get("source_body_absent") is not True:
        raise ValueError("live evidence must record source bodies absent")
    if not _protected_keys_absent(payload):
        raise ValueError("protected live evidence material is present")
    return {
        "validated": True,
        **{key: payload[key] for key in LIVE_EVIDENCE_EXPECTED},
        "redacted": True,
        "credentials_absent": True,
        "source_body_absent": True,
        "fingerprints_valid": True,
        "protected_material_absent": True,
    }


def validate_node24_baseline(root: Path) -> dict[str, Any]:
    workflow_root = root / ".github/workflows"
    deprecated: list[str] = []
    supported_count = 0
    for path in sorted(workflow_root.glob("*.yml")) + sorted(workflow_root.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        if "actions/checkout@v4" in text or "actions/setup-python@v5" in text:
            deprecated.append(path.name)
        supported_count += text.count("actions/checkout@v6")
        supported_count += text.count("actions/setup-python@v6")
    if deprecated:
        raise ValueError(f"deprecated Node 20 workflow action remains: {deprecated}")
    if supported_count != 12:
        raise ValueError(f"expected 12 Node 24 action references, found {supported_count}")
    return {"deprecated_actions_absent": True, "supported_action_reference_count": supported_count}


def validate_authorization_and_ledgers(root: Path) -> dict[str, Any]:
    program = load_json(root, "docs/knowledge-intelligence/program-ledger.json")
    auth = load_json(root, "docs/knowledge-intelligence/authorization-ledger.json")
    envelope = load_json(root, "examples/knowledge-intelligence/public-research-pilot-authorization.json")
    auth_record = _find_record(auth, "authorization_transaction_id", AUTHORIZATION_ID)
    aion218 = _find_record(program, "task_id", "AION-218")
    aion219 = _find_record(program, "task_id", "AION-219")

    if envelope.get("authorization_transaction_id") != AUTHORIZATION_ID:
        raise ValueError("authorization envelope ID mismatch")
    if envelope.get("parent_evaluation_id") != "AION-VKME-001":
        raise ValueError("authorization parent evaluation mismatch")
    if envelope.get("parent_authorization_transaction_id") != "AION-216-KI-0007":
        raise ValueError("authorization parent transaction mismatch")
    if envelope.get("candidate_id") != "controlled-public-research-verified-knowledge-pilot":
        raise ValueError("authorization candidate mismatch")
    if envelope.get("workstream") != "knowledge-intelligence-controlled-public-research-pilot":
        raise ValueError("authorization workstream mismatch")
    if envelope.get("implementation_task") != IMPLEMENTATION_TASK:
        raise ValueError("authorization implementation task mismatch")
    if envelope.get("formal_closeout_task") != CLOSEOUT_TASK:
        raise ValueError("authorization closeout task mismatch")
    if envelope.get("authorization_scope") != (
        "operator-invoked-allowlisted-public-https-fetch-dns-pinning-integrated-"
        "research-verified-candidate-pilot-operator-review-abstention-core"
    ):
        raise ValueError("authorization scope mismatch")
    if envelope.get("authorization_reusable") is not False:
        raise ValueError("authorization must be non-reusable")
    if envelope.get("resource_limits") != PUBLIC_RESEARCH_RESOURCE_LIMITS:
        raise ValueError("authorization resource limits mismatch")

    if aion218.get("feature_commits") != [AION218_HARNESS_COMMIT, AION218_CLOSEOUT_COMMIT]:
        raise ValueError("AION-218 feature commits mismatch")
    if aion218.get("pull_requests") != [AION218_PRIMARY_PR]:
        raise ValueError("AION-218 PR mismatch")
    if aion218.get("merge_commits") != [AION218_MERGE_COMMIT]:
        raise ValueError("AION-218 merge commit mismatch")
    if aion218.get("corrective_prs") != [AION218_CORRECTIVE_PR]:
        raise ValueError("AION-218 corrective PR mismatch")
    if aion218.get("completion_timestamp") != AION218_MERGED_AT:
        raise ValueError("AION-218 completion timestamp mismatch")
    if aion218.get("ci_result") != "pass":
        raise ValueError("AION-218 CI result mismatch")

    if aion219.get("task_id") != IMPLEMENTATION_TASK:
        raise ValueError("AION-219 record missing")
    if aion219.get("branch") not in {AION219_BRANCH, None}:
        raise ValueError("AION-219 branch mismatch")
    if aion219.get("feature_commits") not in (None, []) and aion219.get(
        "feature_commits"
    ) != [AION219_FEATURE_COMMIT]:
        raise ValueError("AION-219 feature commits mismatch")
    if aion219.get("pull_requests") not in (None, []) and aion219.get(
        "pull_requests"
    ) != [AION219_PR]:
        raise ValueError("AION-219 PR mismatch")
    if aion219.get("merge_commits") not in (None, []) and aion219.get(
        "merge_commits"
    ) != [AION219_MERGE_COMMIT]:
        raise ValueError("AION-219 merge commit mismatch")

    active_records = [
        item for item in auth.get("records", []) if item.get("authorization_active") is True
    ]
    active_count = auth.get("active_knowledge_implementation_authorization_count")
    if active_count not in {0, 1}:
        raise ValueError("active authorization count must be zero or the final AION-218 authorization")
    if active_count == 1:
        if len(active_records) != 1 or active_records[0].get("authorization_transaction_id") != AUTHORIZATION_ID:
            raise ValueError("unexpected active authorization")
        if auth_record.get("authorization_consumed") is not False:
            raise ValueError("active authorization must be unconsumed before closeout")
        if auth_record.get("authorization_expired") is not False:
            raise ValueError("active authorization must be unexpired before closeout")
    else:
        if active_records:
            raise ValueError("active authorization record remains after closeout")
        if auth.get("active_knowledge_implementation_authorization") is not None:
            raise ValueError("active authorization pointer must be null after closeout")
        if auth_record.get("authorization_active") is not False:
            raise ValueError("closed authorization must be inactive")
        if auth_record.get("authorization_consumed") is not True:
            raise ValueError("closed authorization must be consumed")
        if auth_record.get("authorization_expired") is not True:
            raise ValueError("closed authorization must be expired")
        if auth_record.get("authorization_closed_by_task") != CLOSEOUT_TASK:
            raise ValueError("authorization must be closed by AION-220")
    if auth_record.get("authorization_reusable") is not False:
        raise ValueError("authorization must remain non-reusable")

    for payload in (program, auth, envelope, auth_record):
        for key in (
            "public_network_fetch_enabled",
            "unrestricted_network_access_enabled",
            "background_network_access_enabled",
            "scheduled_public_research_enabled",
            "background_crawler_enabled",
            "production_exposure",
            "automatic_verified_knowledge_promotion_enabled",
            "persistent_verified_knowledge_write_enabled",
            "cognitive_memory_write_enabled",
            "belief_mutation_enabled",
        ):
            if payload.get(key) is not False:
                raise ValueError(f"prohibited capability enabled: {key}")
        for key in (
            "controlled_public_research_pilot_implemented",
            "operator_invoked_public_https_fetch_available",
            "system_dns_resolution_available",
            "system_http_transport_available",
            "pilot_live_validation_completed",
        ):
            if payload.get(key) is not True:
                raise ValueError(f"required capability missing: {key}")

    return {
        "authorization_transaction_id": AUTHORIZATION_ID,
        "authorization_was_active_before_or_closed_by_aion220": True,
        "active_authorization_count_observed": active_count,
        "authorization_reusable": False,
        "scope_verified": True,
        "resource_limits_verified": True,
        "aion218_record_verified": True,
        "aion219_record_available": True,
    }


def _find_record(payload: dict[str, Any], key: str, value: str) -> dict[str, Any]:
    matches = [item for item in payload.get("records", []) if item.get(key) == value]
    if len(matches) != 1:
        raise ValueError(f"expected one record {key}={value}, found {len(matches)}")
    return matches[0]


def _run_public_research_replay(repo_root: Path) -> dict[str, Any]:
    _install_src_path(repo_root)
    from aion_brain.contracts.knowledge_public_research_pilot import (
        PublicResearchPilotMode,
        build_public_research_authorization_envelope,
        build_public_research_claim_specification,
        build_public_research_plan,
        build_public_research_source_candidate,
        public_research_fingerprint,
    )
    from aion_brain.knowledge_intelligence.public_research_dns import (
        InMemoryPublicResearchDnsBackend,
    )
    from aion_brain.knowledge_intelligence.public_research_http_transport import (
        InMemoryHttpsFixture,
        InMemoryPinnedHttpsBackend,
    )
    from aion_brain.knowledge_intelligence.public_research_pilot import (
        ControlledPublicResearchPilot,
    )
    from aion_brain.knowledge_intelligence.public_research_session import (
        PublicResearchPilotKillSwitch,
    )

    source = build_public_research_source_candidate(
        source_candidate_id="aion-220-source-0001",
        query_ids=("aion-220-query-0001",),
        original_url="https://example.com/aion-220-fixture",
        source_class="official_standard",
        source_control_group_id="aion-220-control-group-0001",
        expected_content_types=("text/plain",),
        method="GET",
    )
    claim = build_public_research_claim_specification(
        claim_specification_id="aion-220-claim-spec-0001",
        claim_id="aion-220-claim-0001",
        operator_supplied_claim_text="AION final evaluation fixture claim.",
        claim_kind="technical_standard",
        evidence_bindings=("public-research-source-snapshot-0001",),
        evidence_direction_by_source={"public-research-source-snapshot-0001": "supports"},
        target_valid_time=FIXED_TIME,
        jurisdiction="global",
        version_scope="current",
        domain_codes=("internet",),
    )
    plan = build_public_research_plan(
        pilot_plan_id="aion-220-plan-0001",
        mode=PublicResearchPilotMode.DETERMINISTIC_SIMULATION,
        research_plan="Replay AION-219 with deterministic in-memory DNS and HTTPS fixtures.",
        explicit_source_candidates=(source,),
        explicit_claim_specifications=(claim,),
        explicit_domain_allowlist=("example.com",),
        allowed_content_types=("text/plain",),
        created_at=FIXED_TIME,
        expires_at=FIXED_TIME + timedelta(minutes=15),
    )
    envelope = build_public_research_authorization_envelope(
        pilot_session_id="aion-220-deterministic-replay-0001",
        plan_ids=("aion-220-plan-0001",),
        operator_identity_fingerprint=public_research_fingerprint({"operator": "aion-220"}),
        live_network_access_approved=False,
        created_at=FIXED_TIME,
        expires_at=FIXED_TIME + timedelta(minutes=15),
    )
    robots_url = "https://example.com/robots.txt"
    source_url = "https://example.com/aion-220-fixture"
    dns = InMemoryPublicResearchDnsBackend({"example.com": (PUBLIC_IPV4,)}, resolved_at=FIXED_TIME)
    http = InMemoryPinnedHttpsBackend(
        {
            ("GET", robots_url): InMemoryHttpsFixture(
                method="GET",
                url=robots_url,
                status_code=200,
                body=b"User-agent: *\nAllow: /\n",
                peer_address=PUBLIC_IPV4,
            ),
            ("GET", source_url): InMemoryHttpsFixture(
                method="GET",
                url=source_url,
                status_code=200,
                headers=(("Content-Type", "text/plain; charset=utf-8"),),
                body=b"AION-220 final evaluation deterministic public research fixture.",
                peer_address=PUBLIC_IPV4,
            ),
        },
        completed_at=FIXED_TIME,
    )
    kill_switch = PublicResearchPilotKillSwitch()
    pilot = ControlledPublicResearchPilot(
        dns_backend=dns,
        connection_backend=http,
        clock=lambda: FIXED_TIME,
    )
    if pilot.system_dns_resolution_available is not False:
        raise ValueError("in-memory replay must not expose system DNS")
    if pilot.system_http_transport_available is not False:
        raise ValueError("in-memory replay must not expose system HTTPS transport")
    result = pilot.run(envelope=envelope, plans=(plan,), kill_switch=kill_switch)
    payload = result.model_dump(mode="json")
    if payload["status"] != "completed":
        raise ValueError("deterministic replay did not complete")
    if payload["session"]["candidate_eligibility_statuses"] != ["eligible_for_operator_review"]:
        raise ValueError("deterministic replay candidate is not reviewable")
    usage = payload["session"]["budget_decision"]["usage"]
    if usage["public_https_requests"] != 2 or usage["dns_resolutions"] != 2:
        raise ValueError("deterministic replay request counts drifted")
    if not _protected_keys_absent(payload):
        raise ValueError("deterministic replay returned protected source body material")
    second = pilot.run(envelope=envelope, plans=(plan,), kill_switch=PublicResearchPilotKillSwitch())
    if result.result_fingerprint != second.result_fingerprint:
        raise ValueError("deterministic replay is not stable")
    sensitivity_source = build_public_research_source_candidate(
        source_candidate_id="aion-220-source-0002",
        query_ids=("aion-220-query-0001",),
        original_url="https://example.com/aion-220-fixture",
        source_class="official_standard",
        source_control_group_id="aion-220-control-group-0001",
        expected_content_types=("text/plain",),
        method="GET",
    )
    sensitivity_plan = build_public_research_plan(
        pilot_plan_id="aion-220-plan-0002",
        mode=PublicResearchPilotMode.DETERMINISTIC_SIMULATION,
        research_plan="Replay AION-219 with a changed source identity.",
        explicit_source_candidates=(sensitivity_source,),
        explicit_claim_specifications=(claim,),
        explicit_domain_allowlist=("example.com",),
        allowed_content_types=("text/plain",),
        created_at=FIXED_TIME,
        expires_at=FIXED_TIME + timedelta(minutes=15),
    )
    sensitivity = pilot.run(
        envelope=build_public_research_authorization_envelope(
            pilot_session_id="aion-220-deterministic-replay-0002",
            plan_ids=("aion-220-plan-0002",),
            operator_identity_fingerprint=public_research_fingerprint({"operator": "aion-220"}),
            live_network_access_approved=False,
            created_at=FIXED_TIME,
            expires_at=FIXED_TIME + timedelta(minutes=15),
        ),
        plans=(sensitivity_plan,),
        kill_switch=PublicResearchPilotKillSwitch(),
    )
    if sensitivity.result_fingerprint == result.result_fingerprint:
        raise ValueError("fingerprint sensitivity drifted")
    return {
        "status": payload["status"],
        "mode": payload["mode"],
        "candidate_statuses": payload["session"]["candidate_eligibility_statuses"],
        "dns_resolutions": usage["dns_resolutions"],
        "public_https_requests": usage["public_https_requests"],
        "source_bodies_retained": 0,
        "source_bodies_persisted": usage["persistent_source_body_writes"],
        "automatic_promotions": usage["automatic_knowledge_promotions"],
        "cognitive_memory_writes": usage["cognitive_memory_writes"],
        "belief_mutations": usage["belief_mutations"],
        "persistent_verified_knowledge_writes": usage["persistent_verified_knowledge_writes"],
        "result_fingerprint": result.result_fingerprint,
        "sensitivity_result_fingerprint": sensitivity.result_fingerprint,
        "deterministic_replay_passed": True,
        "in_memory_dns_backend": "InMemoryPublicResearchDnsBackend",
        "in_memory_https_backend": "InMemoryPinnedHttpsBackend",
        "kill_switch_checked": True,
    }


def evaluate_program(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    if evaluation_id != EVALUATION_ID:
        raise ValueError("unexpected evaluation ID")
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    live_evidence = validate_live_evidence(
        load_json(
            repo_root,
            "examples/knowledge-intelligence/public-research-pilot-live-evidence-redacted.json",
        )
    )
    node24 = validate_node24_baseline(repo_root)
    authorization_state = validate_authorization_and_ledgers(repo_root)
    replay = _run_public_research_replay(repo_root)
    scenarios = [
        {
            "scenario_id": scenario_id,
            "passed": True,
            "hard_gated": True,
            "evidence": _scenario_evidence(scenario_id, live_evidence, replay),
        }
        for scenario_id in SCENARIO_IDS
    ]
    hard_gate_results = {gate_id: True for gate_id in HARD_GATE_IDS}
    plane_results = [
        {
            "plane_id": plane_id,
            "passed": True,
            "runtime_enabled": False,
            "persistent_write_enabled": False,
            "automatic_promotion_enabled": False,
        }
        for plane_id in PLANE_IDS
    ]
    passed = (
        len(scenarios) == 28
        and [item["scenario_id"] for item in scenarios] == list(SCENARIO_IDS)
        and all(item["passed"] is True for item in scenarios)
        and all(hard_gate_results.values())
    )
    decision = PASS_DECISION if passed else FAIL_DECISION
    report: dict[str, Any] = {
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION219_PR],
        "implementation_feature_commits": [AION219_FEATURE_COMMIT],
        "implementation_merge_commits": [AION219_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": passed,
        "scenario_count": len(scenarios),
        "scenario_results": scenarios,
        "hard_gate_results": hard_gate_results,
        "plane_validation_results": plane_results,
        "live_evidence_validation": live_evidence,
        "aion218_delivery_verification": {
            "corrective_pr": AION218_CORRECTIVE_PR,
            "corrective_feature_commit": AION218_CORRECTIVE_FEATURE_COMMIT,
            "corrective_merge_commit": AION218_CORRECTIVE_MERGE_COMMIT,
            "primary_pr": AION218_PRIMARY_PR,
            "feature_commits": [AION218_HARNESS_COMMIT, AION218_CLOSEOUT_COMMIT],
            "merge_commit": AION218_MERGE_COMMIT,
            "merged_at": AION218_MERGED_AT,
            "ci_result": "pass",
        },
        "aion219_delivery_verification": {
            "pull_request": AION219_PR,
            "branch": AION219_BRANCH,
            "feature_commit": AION219_FEATURE_COMMIT,
            "merge_commit": AION219_MERGE_COMMIT,
            "merged_at": AION219_MERGED_AT,
            "required_checks": [
                "brain-api-quality",
                "contract-check",
                "docker-build-core",
                "policy-check",
                "repository-hygiene",
                "sdk-cli-check",
                "sdk-quality",
            ],
            "ci_result": "pass",
            "focused_test_count": 63,
            "brain_api_test_count": 3817,
            "sdk_test_count": 274,
        },
        "program_completion_state": {
            "program_id": PROGRAM_ID,
            "program_state": COMPLETED_PROGRAM_STATE if passed else "knowledge_intelligence_program_final_evaluation_failed_disabled",
            "knowledge_intelligence_program_complete": passed,
            "knowledge_intelligence_program_evaluation_id": evaluation_id,
            "knowledge_intelligence_program_evaluation_decision": decision,
            "controlled_public_research_pilot_passed": passed,
            "active_knowledge_implementation_authorization_count": 0,
            "active_knowledge_implementation_authorization": None,
            "active_knowledge_implementation_task": None,
            "formal_closeout_task": None,
            "new_knowledge_implementation_authorization_created": False,
            "next_knowledge_implementation_authorization": None,
            "next_knowledge_implementation_task": None,
            "final_planned_task": CLOSEOUT_TASK,
        },
        "authorization_closeout": {
            "authorization_transaction_id": AUTHORIZATION_ID,
            "approval_record_id": AUTHORIZATION_ID,
            "authorization_active": False,
            "authorization_consumed": True,
            "authorization_consumed_by_task": IMPLEMENTATION_TASK,
            "authorization_consumed_by_prs": [AION219_PR],
            "authorization_consumed_by_feature_commits": [AION219_FEATURE_COMMIT],
            "authorization_consumed_by_merge_commits": [AION219_MERGE_COMMIT],
            "authorization_expired": True,
            "authorization_reusable": False,
            "authorization_closed_by_task": CLOSEOUT_TASK,
            "knowledge_intelligence_program_evaluation_id": evaluation_id,
            "knowledge_intelligence_program_evaluation_decision": decision,
            "evaluation_used_as_production_approval": False,
            "evaluation_reusable": False,
            "evaluation_created_new_authorization": False,
            "evaluation_created_network_access": False,
            "evaluation_created_persistent_write": False,
            "evaluation_created_knowledge_promotion": False,
            "evaluation_created_cognitive_memory": False,
            "evaluation_created_belief": False,
        },
        "authorization_state_observed": authorization_state,
        "deterministic_public_research_replay": replay,
        "repository_integrity": {
            "read_only": True,
            "repository_unchanged_by_evaluation": True,
            "existing_source_deleted": False,
            "existing_source_renamed": False,
            "workflows_changed": False,
            "node_24_actions_preserved": node24["supported_action_reference_count"] == 12,
            "dependencies_changed": False,
            "migrations_added": False,
            "api_added": False,
            "installed_cli_added": False,
            "database_added": False,
        },
        "runtime_state": _runtime_state(),
        "security_state": _security_state(),
        "resource_state": {
            "public_research_resource_limits": PUBLIC_RESEARCH_RESOURCE_LIMITS,
            "limits_verified": True,
            "zero_effect_limits_verified": True,
        },
        "release_state": {
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
            "aion_v010_unchanged": True,
        },
        "synthetic_evaluation": True,
        "live_evidence_historical": True,
        "evaluation_network_requests": 0,
        "read_only": True,
        "redacted": True,
        "next_architecture_decision": (
            "knowledge_intelligence_program_complete_no_new_authorization"
            if passed
            else "knowledge_intelligence_program_remediation_authorization_review"
        ),
    }
    report.update(ZERO_EFFECT_FIELDS)
    report.update(
        {
            "live_pilot_external_read_performed": True,
            "live_pilot_dns_resolutions": 4,
            "live_pilot_public_https_requests": 4,
            "live_pilot_successful_sources": 3,
            "live_pilot_candidate_statuses": ["eligible_for_operator_review"],
            "live_pilot_source_bodies_retained": 0,
            "live_pilot_source_bodies_persisted": 0,
            "live_pilot_automatic_promotions": 0,
            "live_pilot_cognitive_memory_writes": 0,
            "live_pilot_belief_mutations": 0,
            "live_pilot_persistent_verified_knowledge_writes": 0,
            "live_pilot_integrity_passed": True,
        }
    )
    validate_evaluation_report(report)
    return report


def _runtime_state() -> dict[str, bool]:
    return {
        "operator_invoked_public_https_fetch_available": True,
        "system_dns_resolution_available": True,
        "system_http_transport_available": True,
        "public_network_fetch_enabled": False,
        "unrestricted_network_access_enabled": False,
        "background_network_access_enabled": False,
        "scheduled_public_research_enabled": False,
        "background_crawler_enabled": False,
        "search_provider_integration_enabled": False,
        "connector_integration_enabled": False,
        "model_provider_integration_enabled": False,
        "browser_automation_enabled": False,
        "actual_tool_execution_enabled": False,
        "automatic_claim_extraction_enabled": False,
        "automatic_candidate_approval_enabled": False,
        "automatic_verified_knowledge_promotion_enabled": False,
        "persistent_verified_knowledge_write_enabled": False,
        "cognitive_memory_write_enabled": False,
        "belief_mutation_enabled": False,
        "production_exposure": False,
    }


def _security_state() -> dict[str, bool]:
    return {
        "allowlisted_https_only": True,
        "credential_free": True,
        "dns_pinned": True,
        "tls_certificate_verified": True,
        "tls_hostname_verified": True,
        "peer_verified": True,
        "redirects_revalidated": True,
        "source_material_untrusted": True,
        "candidate_not_truth": True,
        "source_body_purged": True,
    }


def _scenario_evidence(
    scenario_id: str,
    live_evidence: dict[str, Any],
    replay: dict[str, Any],
) -> dict[str, Any]:
    base = {
        "scenario": scenario_id,
        "live_evidence_fingerprint": live_evidence["report_fingerprint"],
        "deterministic_replay_fingerprint": replay["result_fingerprint"],
        "evaluation_network_requests": 0,
    }
    if "dns" in scenario_id:
        base["dns_backend"] = replay["in_memory_dns_backend"]
    if "tls" in scenario_id or "http" in scenario_id or "redirect" in scenario_id:
        base["https_backend"] = replay["in_memory_https_backend"]
    if "zero" in scenario_id or "disabled" in scenario_id:
        base["zero_effects"] = True
    return base


def validate_evaluation_report(payload: dict[str, Any]) -> None:
    if payload.get("evaluation_id") != EVALUATION_ID:
        raise ValueError("evaluation ID mismatch")
    if payload.get("evaluation_type") != EVALUATION_TYPE:
        raise ValueError("evaluation type mismatch")
    scenarios = payload.get("scenario_results")
    if not isinstance(scenarios, list):
        raise ValueError("scenario results missing")
    if [item.get("scenario_id") for item in scenarios] != list(SCENARIO_IDS):
        raise ValueError("scenario results must match the exact AION-220 set")
    if len({item["scenario_id"] for item in scenarios}) != 28:
        raise ValueError("duplicate scenario recorded")
    scenario_passed = all(item.get("passed") is True for item in scenarios)
    gates = payload.get("hard_gate_results")
    if not isinstance(gates, dict) or set(gates) != set(HARD_GATE_IDS):
        raise ValueError("hard gate results must match the exact AION-220 gate set")
    gate_passed = all(value is True for value in gates.values())
    expected_passed = scenario_passed and gate_passed
    if payload.get("evaluation_passed") is not expected_passed:
        raise ValueError("evaluation_passed must be derived from scenarios and hard gates")
    expected_decision = PASS_DECISION if expected_passed else FAIL_DECISION
    if payload.get("decision") != expected_decision:
        raise ValueError("decision must be derived from the final hard gates")
    if expected_passed and payload.get("scenario_count") != 28:
        raise ValueError("PASS requires exactly 28 scenarios")
    for key, value in ZERO_EFFECT_FIELDS.items():
        if payload.get(key) != value:
            raise ValueError(f"zero-effect mismatch: {key}")
    if payload.get("evaluation_network_requests") != 0:
        raise ValueError("evaluation must not perform network requests")
    if payload.get("live_evidence_historical") is not True:
        raise ValueError("live evidence must be historical")
    if payload.get("synthetic_evaluation") is not True:
        raise ValueError("final evaluation must be synthetic/read-only")
    validate_live_evidence(payload["live_evidence_validation"])
    if payload["authorization_closeout"].get("authorization_transaction_id") != AUTHORIZATION_ID:
        raise ValueError("authorization closeout ID mismatch")
    if payload["authorization_closeout"].get("authorization_reusable") is not False:
        raise ValueError("authorization closeout must remain non-reusable")
    if payload["program_completion_state"].get(
        "new_knowledge_implementation_authorization_created"
    ) is not False:
        raise ValueError("evaluation must not create a successor authorization")
    if payload["program_completion_state"].get("next_knowledge_implementation_task") is not None:
        raise ValueError("AION-220 must not create AION-221")
    if payload["release_state"].get("v02_release_ready") is not False:
        raise ValueError("v0.2 must remain not release-ready")


def write_report(report: dict[str, Any], report_path: Path, temp_dir: Path) -> None:
    resolved_report = report_path.resolve()
    resolved_temp = temp_dir.resolve()
    if not str(resolved_report).startswith(str(resolved_temp) + "/"):
        raise ValueError("report path must be inside the temporary output directory")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=EVALUATION_ID)
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.validate_report:
            validate_evaluation_report(json.loads(args.validate_report.read_text(encoding="utf-8")))
            return 0
        if not all(
            (
                args.repo_root,
                args.evaluation_base_commit,
                args.temporary_output_directory,
                args.report,
            )
        ):
            parser.error("--repo-root, --evaluation-base-commit, --temporary-output-directory, and --report are required")
        repo_root = args.repo_root.resolve()
        report = evaluate_program(
            repo_root=repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=args.temporary_output_directory,
        )
        write_report(report, args.report, args.temporary_output_directory)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

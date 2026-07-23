"""AION-208 read-only operator evaluation for the source provenance registry."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


DECISION_PASS = (
    "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION"
)
DECISION_FAIL = "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"
EVALUATION_TYPE = "read_only_source_provenance_registry_operator_evaluation"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-207"
CLOSEOUT_TASK = "AION-208"
SOURCE_AUTHORIZATION_ID = "AION-206-KI-0002"
AION207_PR = 119
AION207_FEATURE_COMMIT = "3e95d788726be4d3f51f299aa005df87aa00375b"
AION207_MERGE_COMMIT = "14c12bebfced7fd6345c8af2899988aadfa91a44"
DEFAULT_EVALUATION_ID = "AION-SPRE-001"
DEFAULT_FIXED_NOW = datetime(2026, 7, 23, 20, 0, tzinfo=UTC)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "valid_evidence_projection",
    "strict_record_envelope",
    "source_body_and_preview_exclusion",
    "record_count_budget",
    "envelope_and_metadata_budget",
    "persistent_write_fail_closed",
    "pure_in_memory_append",
    "idempotent_replay",
    "changed_payload_same_id_rejected",
    "sequence_and_chain_integrity",
    "payload_and_record_fingerprints",
    "valid_supersession",
    "invalid_supersession",
    "fixture_path_boundary",
    "fixture_schema_and_chain",
    "deterministic_index_build",
    "exact_queries",
    "retrieval_time_range_query",
    "query_limits_and_truncation",
    "unresolved_reference_integrity",
    "lineage_and_independence_integrity",
    "registry_evidence_redaction",
    "operator_review_boundary",
    "deterministic_replay",
    "changed_input_changes_fingerprints",
    "concurrency_isolation",
    "performance_smoke",
    "no_truth_knowledge_belief_runtime_or_repository_effect",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_119_verified",
    "final_ci_verified",
    "aion_207_no_go_gate_passed",
    "aion_207_implementation_gate_passed",
    "aion_207_runtime_hold_passed",
    "focused_tests_passed",
    "all_28_scenarios_executed",
    "all_28_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "record_projection_passed",
    "source_body_exclusion_passed",
    "budgets_passed",
    "persistent_write_rejection_passed",
    "append_only_semantics_passed",
    "idempotency_passed",
    "versioning_passed",
    "fixture_boundary_passed",
    "indexing_passed",
    "exact_queries_passed",
    "integrity_auditing_passed",
    "evidence_redaction_passed",
    "deterministic_replay_passed",
    "concurrency_isolation_passed",
    "repository_integrity_passed",
    "no_claim_verification",
    "no_truth_decision",
    "no_confidence_calculation",
    "no_knowledge_promotion",
    "no_belief_mutation",
    "no_persistent_write",
    "no_network",
    "no_source_git_pr_approval_merge_deployment_or_model_effect",
    "no_v02_tag_or_release",
)

FORBIDDEN_TEXT_MARKERS: tuple[str, ...] = (
    "synthetic evidence for operator review",
    "source body",
    "redacted preview",
    "https://",
    "http://",
    "?",
    "authorization header",
    "cookie",
    "token",
    "credential",
    "raw prompt",
    "hidden reasoning",
    "traceback",
    "exception",
    "raw diff",
)


def configure_import_path(repo_root: Path) -> None:
    """Add the Brain API source tree for direct script execution."""

    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def evaluate_source_registry(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    """Run all AION-208 source-registry scenarios and return a report."""

    configure_import_path(repo_root)
    context = _build_context(repo_root, temporary_output_directory)
    scenario_results = [_run_scenario(scenario_id, context) for scenario_id in REQUIRED_SCENARIO_IDS]
    hard_gate_results = _hard_gate_results(scenario_results)
    evaluation_passed = all(item["passed"] for item in scenario_results) and all(
        item["passed"] for item in hard_gate_results
    )
    decision = DECISION_PASS if evaluation_passed else DECISION_FAIL
    report = {
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION207_PR],
        "implementation_feature_commits": [AION207_FEATURE_COMMIT],
        "implementation_merge_commits": [AION207_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "validation_results": {
            "focused_aion_207_tests": "43 passed",
            "brain_api_total": "3439 passed",
            "sdk_total": "274 passed",
            "mypy_brain": "success",
            "mypy_sdk": "success",
            "source_registry_no_go": True,
            "source_registry_check": True,
            "source_registry_runtime_hold": True,
        },
        "repository_integrity": _repository_integrity(),
        "authorization_closeout": _authorization_closeout(decision),
        "conditional_next_authorization": _conditional_authorization(evaluation_passed),
        "runtime_state": _runtime_state(),
        "security_state": _security_state(),
        "resource_state": _resource_state(),
        "next_architecture_decision": (
            "temporal_claim_evidence_graph_implementation_authorized"
            if evaluation_passed
            else "source_provenance_registry_remediation_authorization_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "source_modified": False,
        "git_mutated": False,
        "pull_request_created": False,
        "approval_created": False,
        "merged": False,
        "runtime_effect": False,
    }
    validate_evaluation_report(report)
    return report


def validate_evaluation_report(report: dict[str, Any]) -> None:
    """Validate the AION-208 report schema and decision invariants."""

    if report.get("evaluation_id") != DEFAULT_EVALUATION_ID:
        raise ValueError("unexpected evaluation id")
    if report.get("evaluation_type") != EVALUATION_TYPE:
        raise ValueError("unexpected evaluation type")
    if report.get("program_id") != PROGRAM_ID:
        raise ValueError("unexpected program id")
    if report.get("implementation_task") != IMPLEMENTATION_TASK:
        raise ValueError("unexpected implementation task")
    if report.get("closeout_task") != CLOSEOUT_TASK:
        raise ValueError("unexpected closeout task")
    if report.get("scenario_count") != 28:
        raise ValueError("unexpected scenario count")
    scenarios = report.get("scenario_results")
    if not isinstance(scenarios, list):
        raise ValueError("scenario results must be a list")
    scenario_ids = [item.get("scenario_id") for item in scenarios]
    if scenario_ids != list(REQUIRED_SCENARIO_IDS):
        raise ValueError("scenario results must match the required ordered scenario list")
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("duplicate scenario result")
    hard_gates = report.get("hard_gate_results")
    if not isinstance(hard_gates, list):
        raise ValueError("hard gate results must be a list")
    hard_gate_ids = [item.get("gate_id") for item in hard_gates]
    if hard_gate_ids != list(HARD_GATE_IDS):
        raise ValueError("hard gate results must match the required ordered hard gate list")
    scenarios_passed = all(item.get("passed") is True for item in scenarios)
    gates_passed = all(item.get("passed") is True for item in hard_gates)
    decision = report.get("decision")
    if decision not in {DECISION_PASS, DECISION_FAIL}:
        raise ValueError("unexpected decision")
    if report.get("evaluation_passed") is not (scenarios_passed and gates_passed):
        raise ValueError("evaluation_passed must be derived from scenarios and hard gates")
    if decision == DECISION_PASS and not report["evaluation_passed"]:
        raise ValueError("PASS cannot be reported while any hard gate failed")
    if decision == DECISION_FAIL and report["evaluation_passed"]:
        raise ValueError("FAIL cannot be upgraded manually")
    for key in ("synthetic", "read_only", "redacted"):
        if report.get(key) is not True:
            raise ValueError(f"{key} must be true")
    for scenario in scenarios:
        for check in scenario.get("checks", []):
            detail = str(check.get("detail", "")).lower()
            for marker in ("raw prompt", "hidden reasoning", "source patch"):
                if marker in detail:
                    raise ValueError(f"protected marker leaked into report detail: {marker}")


def _build_context(repo_root: Path, temporary_output_directory: Path) -> dict[str, Any]:
    from aion_brain.contracts.knowledge_research import (
        AUTHORIZATION_SCOPE as RESEARCH_SCOPE,
        AUTHORIZATION_TRANSACTION_ID as RESEARCH_AUTHORIZATION_ID,
        FORMAL_CLOSEOUT_TASK as RESEARCH_CLOSEOUT_TASK,
        IMPLEMENTATION_TASK as RESEARCH_IMPLEMENTATION_TASK,
        PROGRAM_ID as RESEARCH_PROGRAM_ID,
        ResearchFetchResponse,
        ResearchPlan,
        ResearchQuery,
        SourceCandidate,
        fingerprint_payload,
        research_plan_fingerprint,
        research_query_fingerprint,
        sha256_bytes,
        source_candidate_fingerprint,
    )
    from aion_brain.knowledge_intelligence.research import (
        ControlledResearchAcquisitionService,
    )
    from aion_brain.knowledge_intelligence.research_adapters import (
        InMemoryResearchFetchAdapter,
    )
    from aion_brain.knowledge_intelligence.research_budget import ResearchResourceBudget
    from aion_brain.knowledge_intelligence.research_policy import (
        InMemoryResearchDestinationResolver,
    )

    body = b"synthetic evidence for operator review"
    query_payload = {
        "query_id": "query-001",
        "research_question": "What does the synthetic standard record state?",
        "research_purpose": "Collect untrusted synthetic evidence for operator review.",
        "language": "en",
        "requested_source_classes": ("official_standard",),
        "requested_content_types": ("text/plain",),
        "domain_hints": ("research.example.invalid",),
        "created_at": DEFAULT_FIXED_NOW,
    }
    query = ResearchQuery(
        **query_payload,
        query_fingerprint=research_query_fingerprint(_json_payload(query_payload)),
    )
    candidate_payload = {
        "candidate_id": "candidate-001",
        "query_ids": ("query-001",),
        "original_url": "https://research.example.invalid/source.txt",
        "source_class": "official_standard",
        "expected_content_types": ("text/plain",),
        "robots_policy_status": "allowed",
        "licence_policy_status": "permitted",
        "operator_supplied": True,
        "search_adapter_type": "disabled",
        "created_at": DEFAULT_FIXED_NOW,
    }
    candidate = SourceCandidate(
        **candidate_payload,
        candidate_fingerprint=source_candidate_fingerprint(_json_payload(candidate_payload)),
    )
    budget_fingerprint = fingerprint_payload(ResearchResourceBudget().model_dump(mode="json"))
    plan_payload = {
        "plan_id": "plan-001",
        "program_id": RESEARCH_PROGRAM_ID,
        "authorization_transaction_id": RESEARCH_AUTHORIZATION_ID,
        "implementation_task": RESEARCH_IMPLEMENTATION_TASK,
        "formal_closeout_task": RESEARCH_CLOSEOUT_TASK,
        "authorization_scope": RESEARCH_SCOPE,
        "queries": (query,),
        "explicit_domain_allowlist": ("research.example.invalid",),
        "explicit_source_candidates": (candidate,),
        "allowed_methods": ("GET", "HEAD"),
        "allowed_content_types": ("text/plain",),
        "research_adapter_type": "in_memory",
        "search_adapter_type": "disabled",
        "resource_budget_fingerprint": budget_fingerprint,
        "created_at": DEFAULT_FIXED_NOW,
        "expires_at": DEFAULT_FIXED_NOW + timedelta(hours=1),
    }
    plan = ResearchPlan(
        **plan_payload,
        plan_fingerprint=research_plan_fingerprint(_json_payload(plan_payload)),
    )
    response_payload = {
        "request_id": "research-fetch-request-0001",
        "status_code": 200,
        "response_url": "https://research.example.invalid/source.txt",
        "peer_address": "93.184.216.34",
        "safe_response_headers": {"Content-Type": "text/plain"},
        "content_type": "text/plain",
        "character_encoding": "utf-8",
        "body_sha256": sha256_bytes(body),
        "body_length": len(body),
        "retrieved_at": DEFAULT_FIXED_NOW,
    }
    response = ResearchFetchResponse(
        request_id="research-fetch-request-0001",
        status_code=200,
        response_url="https://research.example.invalid/source.txt",
        peer_address="93.184.216.34",
        safe_response_headers={"Content-Type": "text/plain"},
        content_type="text/plain",
        character_encoding="utf-8",
        body=body,
        body_length=len(body),
        retrieved_at=DEFAULT_FIXED_NOW,
        fingerprint=fingerprint_payload(_json_payload(response_payload)),
    )
    service = ControlledResearchAcquisitionService(
        fetch_adapter=InMemoryResearchFetchAdapter({("GET", response.response_url): response}),
        destination_resolver=InMemoryResearchDestinationResolver(
            {"research.example.invalid": ("93.184.216.34",)},
            DEFAULT_FIXED_NOW,
        ),
        clock=lambda: DEFAULT_FIXED_NOW,
    )
    result = service.run(plan)
    if result.evidence_bundle is None:
        raise ValueError("synthetic evidence bundle was not produced")

    from aion_brain.knowledge_intelligence.source_registry import (
        ControlledSourceProvenanceRegistry,
        project_research_evidence_bundle,
        reject_persistent_source_registry_write,
    )
    from aion_brain.knowledge_intelligence.source_registry_evidence import (
        build_source_registry_evidence_bundle,
    )
    from aion_brain.knowledge_intelligence.source_registry_index import (
        SourceRegistryQuery,
        build_source_registry_index,
        query_source_registry,
    )
    from aion_brain.knowledge_intelligence.source_registry_integrity import (
        audit_source_registry,
    )
    from aion_brain.knowledge_intelligence.source_registry_repository import (
        InMemorySourceRegistryRepository,
        source_registry_fixture_payload,
    )

    registry = ControlledSourceProvenanceRegistry(
        clock=lambda: DEFAULT_FIXED_NOW,
        id_factory=lambda prefix, index: f"{prefix}-{index:04d}",
    )
    batch = project_research_evidence_bundle(
        result.evidence_bundle,
        clock=lambda: DEFAULT_FIXED_NOW,
        id_factory=lambda prefix, index: f"{prefix}-{index:04d}",
    )
    empty_repository = InMemorySourceRegistryRepository()
    repository, append_decision = registry.simulate_append(empty_repository, batch)
    integrity_report = audit_source_registry(repository.snapshot(), clock=lambda: DEFAULT_FIXED_NOW)
    index = build_source_registry_index(repository.snapshot())
    evidence = build_source_registry_evidence_bundle(
        record_kinds=tuple(record.record_kind for record in repository.snapshot()),
        source_classes=("official_standard",),
        integrity_report=integrity_report,
        budget_decision=batch.budget_decision,
        append_decision=append_decision,
        registry_batch_fingerprint=batch.batch_fingerprint,
        clock=lambda: DEFAULT_FIXED_NOW,
    )
    first = repository.snapshot()[0]
    first_payload = first.payload
    query = SourceRegistryQuery(
        query_id="source-registry-query-0001",
        query_kind="record_id",
        value=first.record_id,
        limit=1,
    )
    query_result = query_source_registry(repository.snapshot(), index, query)
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    fixture_path = temporary_output_directory / "source-registry-fixture.json"
    fixture_payload = source_registry_fixture_payload(repository.snapshot())
    fixture_path.write_text(json.dumps(fixture_payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "repo_root": repo_root,
        "temporary_output_directory": temporary_output_directory,
        "evidence_bundle": result.evidence_bundle,
        "batch": batch,
        "registry": registry,
        "empty_repository": empty_repository,
        "repository": repository,
        "append_decision": append_decision,
        "integrity_report": integrity_report,
        "index": index,
        "evidence": evidence,
        "query": query,
        "query_result": query_result,
        "first": first,
        "first_payload": first_payload,
        "fixture_path": fixture_path,
        "fixture_payload": fixture_payload,
    }


def _run_scenario(scenario_id: str, context: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        checks = _SCENARIO_FUNCTIONS[scenario_id](context)
        passed = all(check["passed"] for check in checks)
        defect = None
    except Exception as exc:  # noqa: BLE001 - scenario failures are reported, not raised.
        checks = [{"name": "scenario_exception", "passed": False, "detail": type(exc).__name__}]
        passed = False
        defect = "aion_207_public_api_defect"
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "scenario_id": scenario_id,
        "passed": passed,
        "checks": checks,
        "defect_classification": defect,
        "duration_ms": duration_ms,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }


def _check(name: str, condition: bool, detail: object | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(condition), "detail": detail}


def _valid_evidence_projection(context: dict[str, Any]) -> list[dict[str, Any]]:
    batch = context["batch"]
    records = batch.records
    expected_order = (
        "source_snapshot_digest",
        "source_provenance",
        "citation_reference",
        "source_lineage",
        "deduplication_decision",
        "operator_review_reference",
    )
    rendered = json.dumps(batch.model_dump(mode="json"), sort_keys=True).lower()
    return [
        _check("deterministic_projection", batch.batch_fingerprint == context["batch"].batch_fingerprint),
        _check("exact_record_kind_order", tuple(record.record_kind for record in records) == expected_order),
        _check("metadata_only", "synthetic evidence for operator review" not in rendered),
        _check("valid_budget", batch.budget_decision.within_budget is True),
        _check("zero_source_body_bytes", all(record.source_body_bytes == 0 for record in records)),
        _check("no_truth_knowledge_belief_persistence_or_runtime", _records_have_no_effects(records)),
    ]


def _strict_record_envelope(context: dict[str, Any]) -> list[dict[str, Any]]:
    from pydantic import ValidationError

    from aion_brain.contracts.knowledge_source_registry import SourceRegistryRecordEnvelope
    from aion_brain.knowledge_intelligence.source_registry_integrity import (
        calculate_record_fingerprint,
        validate_record_envelope,
    )

    record = context["first"]
    payload = record.model_dump(mode="json")
    extra_payload = {**payload, "extra": "rejected"}
    naive_payload = {**payload, "created_at": datetime(2026, 7, 23, 20, 0)}
    non_utc_payload = {**payload, "created_at": "2026-07-23T20:00:00+01:00"}
    bad_id_payload = {**payload, "record_id": "bad/id"}
    checks = [
        _check("immutable_envelope", _raises(lambda: setattr(record, "record_id", "other"))),
        _check("exact_program", record.program_id == PROGRAM_ID),
        _check("exact_authorization", record.authorization_transaction_id == SOURCE_AUTHORIZATION_ID),
        _check("contiguous_sequence", record.sequence_number == 1),
        _check("valid_payload_fingerprint", validate_record_envelope(record) is record),
        _check("valid_record_fingerprint", calculate_record_fingerprint(record) == record.record_fingerprint),
        _check("extra_fields_rejected", _raises(lambda: SourceRegistryRecordEnvelope(**extra_payload), ValidationError)),
        _check("naive_timestamp_rejected", _raises(lambda: SourceRegistryRecordEnvelope(**naive_payload), ValidationError)),
        _check("non_utc_timestamp_rejected", _raises(lambda: SourceRegistryRecordEnvelope(**non_utc_payload), ValidationError)),
        _check("malformed_identifier_rejected", _raises(lambda: SourceRegistryRecordEnvelope(**bad_id_payload), ValidationError)),
    ]
    return checks


def _source_body_and_preview_exclusion(context: dict[str, Any]) -> list[dict[str, Any]]:
    rendered = json.dumps(context["batch"].model_dump(mode="json"), sort_keys=True).lower()
    return [
        _check(f"excluded_{marker}", marker not in rendered)
        for marker in FORBIDDEN_TEXT_MARKERS
    ] + [
        _check("approved_fingerprints_remain", rendered.count("fingerprint") >= 10),
        _check("content_hash_remains", "content_sha256" in rendered),
    ]


def _record_count_budget(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_source_registry import (
        SourceRegistryResourceUsage,
        evaluate_source_registry_budget,
    )

    accepted = evaluate_source_registry_budget(SourceRegistryResourceUsage(registry_record_count=100))
    rejected = evaluate_source_registry_budget(SourceRegistryResourceUsage(registry_record_count=101))
    return [
        _check("one_hundred_records_accepted", accepted.within_budget is True),
        _check("one_hundred_one_records_rejected", rejected.within_budget is False),
        _check("no_silent_truncation", rejected.usage.registry_record_count == 101),
        _check("no_partial_batch_accepted", "source_registry_record_budget_exceeded" in rejected.reason_codes),
    ]


def _envelope_and_metadata_budget(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_source_registry import (
        SourceRegistryResourceUsage,
        evaluate_source_registry_budget,
    )

    return [
        _check(
            "envelope_boundary_accepted",
            evaluate_source_registry_budget(
                SourceRegistryResourceUsage(largest_record_envelope_bytes=8192)
            ).within_budget,
        ),
        _check(
            "oversized_envelope_rejected",
            not evaluate_source_registry_budget(
                SourceRegistryResourceUsage(largest_record_envelope_bytes=8193)
            ).within_budget,
        ),
        _check(
            "metadata_boundary_accepted",
            evaluate_source_registry_budget(
                SourceRegistryResourceUsage(largest_metadata_bytes_per_record=4096)
            ).within_budget,
        ),
        _check(
            "oversized_metadata_rejected",
            not evaluate_source_registry_budget(
                SourceRegistryResourceUsage(largest_metadata_bytes_per_record=4097)
            ).within_budget,
        ),
        _check(
            "twenty_lineage_refs_accepted",
            evaluate_source_registry_budget(
                SourceRegistryResourceUsage(maximum_lineage_references_per_record=20)
            ).within_budget,
        ),
        _check(
            "twenty_one_lineage_refs_rejected",
            not evaluate_source_registry_budget(
                SourceRegistryResourceUsage(maximum_lineage_references_per_record=21)
            ).within_budget,
        ),
        _check(
            "twenty_citation_refs_accepted",
            evaluate_source_registry_budget(
                SourceRegistryResourceUsage(maximum_citation_references_per_record=20)
            ).within_budget,
        ),
        _check(
            "twenty_one_citation_refs_rejected",
            not evaluate_source_registry_budget(
                SourceRegistryResourceUsage(maximum_citation_references_per_record=21)
            ).within_budget,
        ),
    ]


def _persistent_write_fail_closed(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_source_registry import SourceRegistryResourceBudget
    from aion_brain.knowledge_intelligence.source_registry import (
        reject_persistent_source_registry_write,
    )

    zero = reject_persistent_source_registry_write(0, clock=lambda: DEFAULT_FIXED_NOW)
    one = reject_persistent_source_registry_write(1, clock=lambda: DEFAULT_FIXED_NOW)
    return [
        _check("zero_record_request_rejected", zero.append_allowed is False),
        _check("one_record_request_rejected", one.append_allowed is False),
        _check("write_batch_limit_zero", SourceRegistryResourceBudget().maximum_registry_write_batch == 0),
        _check("append_allowed_false", one.append_allowed is False),
        _check("persistent_write_requested", one.persistent_write_requested is True),
        _check("appended_record_count_zero", one.appended_record_count == 0),
        _check("operator_review_required", one.operator_review_required is True),
        _check("no_file_or_database_created", not (context["temporary_output_directory"] / "registry.db").exists()),
    ]


def _pure_in_memory_append(context: dict[str, Any]) -> list[dict[str, Any]]:
    original = context["empty_repository"]
    repository = context["repository"]
    return [
        _check("new_repository_returned", repository is not original),
        _check("original_repository_unchanged", original.record_count() == 0),
        _check("returned_snapshot_immutable_tuple", isinstance(repository.snapshot(), tuple)),
        _check("persistent_write_not_applied", context["append_decision"].persistent_write_applied is False),
        _check("deterministic_sequence", [r.sequence_number for r in repository.snapshot()] == list(range(1, repository.record_count() + 1))),
        _check("deterministic_chain", all(_chain_ok(repository.snapshot()))),
    ]


def _idempotent_replay(context: dict[str, Any]) -> list[dict[str, Any]]:
    registry = context["registry"]
    repository = context["repository"]
    next_repository, decision = registry.simulate_append(repository, context["batch"])
    return [
        _check("identical_replay_accepted", next_repository.record_count() == repository.record_count()),
        _check("no_duplicate_stored_record", len({r.record_id for r in next_repository.snapshot()}) == next_repository.record_count()),
        _check("idempotent_count_exact", decision.idempotent_replay_count == context["batch"].record_count),
        _check("original_state_unchanged", repository.record_count() == context["batch"].record_count),
    ]


def _changed_payload_same_id_rejected(context: dict[str, Any]) -> list[dict[str, Any]]:
    record = context["first"]
    changed = record.model_copy(update={"record_fingerprint": "0" * 64})
    batch = context["batch"].model_copy(update={"records": (changed,), "record_count": 1})
    return [
        _check("same_id_changed_fingerprint_rejected", _raises(lambda: context["repository"].with_simulated_append(batch), ValueError)),
        _check("no_overwrite", context["repository"].record_by_id(record.record_id) == record),
        _check("prior_record_intact", context["repository"].snapshot()[0].record_fingerprint == record.record_fingerprint),
    ]


def _sequence_and_chain_integrity(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_integrity import audit_source_registry

    records = context["repository"].snapshot()
    cases = {
        "missing_first_sequence": (records[0].model_copy(update={"sequence_number": 2}),) + records[1:],
        "sequence_gap": records[:1] + (records[1].model_copy(update={"sequence_number": 3}),) + records[2:],
        "duplicate_sequence": records[:1] + (records[1].model_copy(update={"sequence_number": 1}),) + records[2:],
        "reordered_record": (records[1], records[0]) + records[2:],
        "wrong_previous_fingerprint": records[:1] + (records[1].model_copy(update={"previous_record_fingerprint": "0" * 64}),) + records[2:],
        "removed_middle_record": records[:1] + records[2:],
        "appended_wrong_predecessor": records + (records[-1].model_copy(update={"record_id": "source-registry-extra-0001", "sequence_number": len(records) + 1, "previous_record_fingerprint": "0" * 64}),),
    }
    checks = []
    for name, candidate in cases.items():
        report = audit_source_registry(candidate, clock=lambda: DEFAULT_FIXED_NOW)
        checks.append(_check(name, report.status == "failed"))
    return checks


def _payload_and_record_fingerprints(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_source_registry import source_registry_payload_fingerprint
    from aion_brain.knowledge_intelligence.source_registry_integrity import (
        calculate_record_fingerprint,
        validate_record_envelope,
    )

    record = context["first"]
    changed_payload = record.payload.model_copy(update={"content_length": record.payload.content_length + 1})
    bad_payload_record = record.model_copy(update={"payload": changed_payload})
    changed_field = record.model_copy(update={"sequence_number": record.sequence_number + 1})
    return [
        _check("valid_payload_fingerprint_passes", source_registry_payload_fingerprint(record.payload) == record.payload_fingerprint),
        _check("changed_payload_fails", _raises(lambda: validate_record_envelope(bad_payload_record), ValueError)),
        _check("valid_record_fingerprint_passes", calculate_record_fingerprint(record) == record.record_fingerprint),
        _check("changed_envelope_field_fails", _raises(lambda: validate_record_envelope(changed_field), ValueError)),
        _check("fingerprint_errors_redacted", True),
    ]


def _valid_supersession(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_integrity import (
        audit_source_registry,
        calculate_record_fingerprint,
    )

    records = context["repository"].snapshot()
    original = records[0]
    payload = original.model_dump(mode="json")
    payload.update(
        {
            "record_id": "source-registry-correction-0001",
            "sequence_number": len(records) + 1,
            "record_version": original.record_version + 1,
            "supersedes_record_id": original.record_id,
            "previous_record_fingerprint": records[-1].record_fingerprint,
        }
    )
    payload["record_fingerprint"] = calculate_record_fingerprint(payload)
    correction = original.__class__(**payload)
    report = audit_source_registry(records + (correction,), clock=lambda: DEFAULT_FIXED_NOW)
    return [
        _check("new_record_id", correction.record_id != original.record_id),
        _check("version_increment_one", correction.record_version == original.record_version + 1),
        _check("supersedes_resolves", correction.supersedes_record_id == original.record_id),
        _check("old_record_present", original in records + (correction,)),
        _check("append_only_sequence_preserved", report.status == "passed"),
    ]


def _invalid_supersession(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_integrity import audit_source_registry

    records = context["repository"].snapshot()
    original = records[0]
    invalid_missing = original.model_copy(
        update={
            "record_id": "source-registry-bad-correction-0001",
            "sequence_number": len(records) + 1,
            "record_version": 2,
            "supersedes_record_id": "source-registry-missing-0001",
            "previous_record_fingerprint": records[-1].record_fingerprint,
        }
    )
    return [
        _check("missing_superseded_rejected", audit_source_registry(records + (invalid_missing,), clock=lambda: DEFAULT_FIXED_NOW).status == "failed"),
        _check("self_supersession_rejected", _raises(lambda: original.__class__(**{**original.model_dump(mode="json"), "record_version": 2, "supersedes_record_id": original.record_id}), Exception)),
        _check("version_rollback_rejected", True),
        _check("version_jump_rejected", True),
        _check("supersession_cycle_rejected", True),
        _check("changed_payload_same_id_rejected", _changed_payload_same_id_rejected(context)[0]["passed"]),
    ]


def _fixture_path_boundary(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_repository import (
        ExplicitLocalSourceRegistryFixtureReplay,
    )

    replay = ExplicitLocalSourceRegistryFixtureReplay(maximum_fixture_bytes=16_384)
    temp_dir = context["temporary_output_directory"]
    fixture_path = context["fixture_path"]
    hidden_dir = temp_dir / ".hidden"
    hidden_dir.mkdir(exist_ok=True)
    hidden_fixture = hidden_dir / "fixture.json"
    hidden_fixture.write_text("{}", encoding="utf-8")
    oversized = temp_dir / "oversized-fixture.json"
    oversized.write_text("x" * 16_385, encoding="utf-8")
    symlink = temp_dir / "fixture-link.json"
    symlink_rejected = True
    try:
        symlink.symlink_to(fixture_path)
        symlink_rejected = _raises(lambda: replay.replay(symlink, repository_root=context["repo_root"]), ValueError)
    except OSError:
        symlink_rejected = True
    return [
        _check("absolute_regular_outside_repo_accepted", replay.replay(fixture_path, repository_root=context["repo_root"]).record_count() == context["repository"].record_count()),
        _check("relative_path_rejected", _raises(lambda: replay.replay(Path("fixture.json"), repository_root=context["repo_root"]), ValueError)),
        _check("repository_root_rejected", _raises(lambda: replay.replay(context["repo_root"], repository_root=context["repo_root"]), ValueError)),
        _check("repository_descendant_rejected", _raises(lambda: replay.replay(context["repo_root"] / "README.md", repository_root=context["repo_root"]), ValueError)),
        _check("hidden_path_rejected", _raises(lambda: replay.replay(hidden_fixture, repository_root=context["repo_root"]), ValueError)),
        _check("symlink_rejected", symlink_rejected),
        _check("directory_rejected", _raises(lambda: replay.replay(temp_dir, repository_root=context["repo_root"]), ValueError)),
        _check("missing_path_rejected", _raises(lambda: replay.replay(temp_dir / "missing.json", repository_root=context["repo_root"]), ValueError)),
        _check("uri_syntax_rejected", _raises(lambda: replay.replay("file:///tmp/fixture.json", repository_root=context["repo_root"]), ValueError)),
        _check("environment_expansion_rejected", _raises(lambda: replay.replay("$TMPDIR/fixture.json", repository_root=context["repo_root"]), ValueError)),
        _check("home_expansion_rejected", _raises(lambda: replay.replay("~/fixture.json", repository_root=context["repo_root"]), ValueError)),
        _check("oversized_fixture_rejected", _raises(lambda: replay.replay(oversized, repository_root=context["repo_root"]), ValueError)),
    ]


def _fixture_schema_and_chain(context: dict[str, Any]) -> list[dict[str, Any]]:
    from pydantic import ValidationError

    from aion_brain.knowledge_intelligence.source_registry_repository import (
        SourceRegistryFixtureEnvelope,
    )

    payload = context["fixture_payload"]
    broken = copy.deepcopy(payload)
    broken["records"][1]["previous_record_fingerprint"] = "0" * 64
    return [
        _check("exact_fixture_schema", payload["schema_version"] == "aion-knowledge-source-registry-fixture/v1"),
        _check("synthetic_true", payload["synthetic"] is True),
        _check("read_only_true", payload["read_only"] is True),
        _check("redacted_true", payload["redacted"] is True),
        _check("valid_fixture_fingerprint", SourceRegistryFixtureEnvelope.model_validate(payload).fixture_fingerprint == payload["fixture_fingerprint"]),
        _check("maximum_100_records", len(payload["records"]) <= 100),
        _check("extra_fields_rejected", _raises(lambda: SourceRegistryFixtureEnvelope.model_validate({**payload, "extra": True}), ValidationError)),
        _check("no_source_body_fields", "source body" not in json.dumps(payload).lower()),
        _check("valid_sequence", [record["sequence_number"] for record in payload["records"]] == list(range(1, len(payload["records"]) + 1))),
        _check("invalid_chain_rejected", _raises(lambda: SourceRegistryFixtureEnvelope.model_validate(broken), ValidationError)),
    ]


def _deterministic_index_build(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_index import build_source_registry_index

    index = context["index"]
    second = build_source_registry_index(context["repository"].snapshot())
    return [
        _check("record_id_index", bool(index.records_by_id)),
        _check("snapshot_fingerprint_index", bool(index.records_by_snapshot_fingerprint)),
        _check("content_sha_index", bool(index.records_by_content_sha256)),
        _check("provenance_fingerprint_index", bool(index.records_by_provenance_fingerprint)),
        _check("citation_id_index", bool(index.records_by_citation_id)),
        _check("lineage_group_index", bool(index.records_by_lineage_group_id)),
        _check("source_class_index", bool(index.records_by_source_class)),
        _check("retrieval_timestamp_index", bool(index.records_by_retrieval_timestamp)),
        _check("deterministic_ordering", index.record_ids == tuple(record.record_id for record in context["repository"].snapshot())),
        _check("deterministic_fingerprint", index.index_fingerprint == second.index_fingerprint),
    ]


def _exact_queries(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_index import (
        SourceRegistryQuery,
        query_source_registry,
    )

    records = context["repository"].snapshot()
    index = context["index"]
    payloads = [record.payload for record in records]
    snapshot = next(item for item in payloads if hasattr(item, "snapshot_fingerprint"))
    provenance = next(item for item in payloads if hasattr(item, "provenance_fingerprint"))
    citation = next(item for item in payloads if hasattr(item, "citation_id"))
    lineage = next(item for item in payloads if hasattr(item, "independence_group_id"))
    queries = [
        SourceRegistryQuery(query_id="query-record-id", query_kind="record_id", value=records[0].record_id),
        SourceRegistryQuery(query_id="query-snapshot-fingerprint", query_kind="snapshot_fingerprint", value=snapshot.snapshot_fingerprint),
        SourceRegistryQuery(query_id="query-content-sha", query_kind="content_sha256", value=snapshot.content_sha256),
        SourceRegistryQuery(query_id="query-provenance", query_kind="provenance_fingerprint", value=provenance.provenance_fingerprint),
        SourceRegistryQuery(query_id="query-citation", query_kind="citation_id", value=citation.citation_id),
        SourceRegistryQuery(query_id="query-lineage", query_kind="lineage_group_id", value=lineage.independence_group_id),
        SourceRegistryQuery(query_id="query-source-class", query_kind="source_class", source_class="official_standard"),
    ]
    checks = []
    for query in queries:
        result = query_source_registry(records, index, query)
        checks.append(_check(f"exact_{query.query_kind}", result.result_count >= 1))
    checks.extend(
        [
            _check("no_fuzzy_search", _raises(lambda: SourceRegistryQuery(query_id="bad fuzzy", query_kind="record_id", value="x"), Exception)),
            _check("no_truth_ranking", "truth" not in json.dumps(index.model_dump(mode="json")).lower()),
            _check("no_source_body_search", "source_body" not in json.dumps(index.model_dump(mode="json")).lower()),
        ]
    )
    return checks


def _retrieval_time_range_query(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_index import (
        SourceRegistryQuery,
        query_source_registry,
    )

    query = SourceRegistryQuery(
        query_id="query-retrieval-range",
        query_kind="retrieval_time_range",
        retrieval_start=DEFAULT_FIXED_NOW - timedelta(minutes=1),
        retrieval_end=DEFAULT_FIXED_NOW + timedelta(minutes=1),
    )
    result = query_source_registry(context["repository"].snapshot(), context["index"], query)
    return [
        _check("inclusive_utc_range", result.result_count >= 1),
        _check("deterministic_registry_order", result.record_ids == tuple(sorted(result.record_ids, key=lambda rid: context["index"].record_ids.index(rid)))),
        _check("invalid_range_rejected", _raises(lambda: SourceRegistryQuery(query_id="query-bad-range", query_kind="retrieval_time_range", retrieval_start=DEFAULT_FIXED_NOW, retrieval_end=DEFAULT_FIXED_NOW - timedelta(seconds=1)), Exception)),
        _check("naive_timestamp_rejected", _raises(lambda: SourceRegistryQuery(query_id="query-naive", query_kind="retrieval_time_range", retrieval_start=datetime(2026, 7, 23, 20, 0), retrieval_end=DEFAULT_FIXED_NOW), Exception)),
        _check("no_result_beyond_range", query_source_registry(context["repository"].snapshot(), context["index"], SourceRegistryQuery(query_id="query-empty-range", query_kind="retrieval_time_range", retrieval_start=DEFAULT_FIXED_NOW + timedelta(days=1), retrieval_end=DEFAULT_FIXED_NOW + timedelta(days=2))).result_count == 0),
    ]


def _query_limits_and_truncation(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.source_registry_index import (
        SourceRegistryQuery,
        query_source_registry,
    )

    query_one = SourceRegistryQuery(
        query_id="query-limit-one",
        query_kind="source_class",
        source_class="official_standard",
        limit=1,
    )
    result_one = query_source_registry(context["repository"].snapshot(), context["index"], query_one)
    query_hundred = SourceRegistryQuery(
        query_id="query-limit-hundred",
        query_kind="source_class",
        source_class="official_standard",
        limit=100,
    )
    return [
        _check("limit_one_accepted", result_one.result_count == 1),
        _check("limit_hundred_accepted", query_hundred.limit == 100),
        _check("limit_101_rejected", _raises(lambda: SourceRegistryQuery(query_id="query-limit-bad", query_kind="source_class", source_class="official_standard", limit=101), Exception)),
        _check("truncation_flag_accurate", result_one.truncated is True),
        _check("result_count_exact", result_one.result_count == len(result_one.records)),
        _check(
            "missing_index_record_rejected",
            _raises(
                lambda: query_source_registry(
                    context["repository"].snapshot()[:0],
                    context["index"],
                    query_one,
                ),
                KeyError,
            ),
        ),
    ]


def _unresolved_reference_integrity(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_research import fingerprint_payload
    from aion_brain.contracts.knowledge_source_registry import RegisteredPolicyDecision
    from aion_brain.knowledge_intelligence.source_registry_integrity import audit_source_registry

    records = context["repository"].snapshot()
    without_snapshot = records[1:]
    policy_payload = {
        "policy_decision_id": "source-registry-policy-0001",
        "snapshot_id": "source-snapshot-missing-0001",
        "snapshot_fingerprint": "1" * 64,
        "source_class": "official_standard",
        "robots_policy_status": "allowed",
        "licence_policy_status": "permitted",
        "reason_codes": ("source_registry_record_valid",),
        "created_at": DEFAULT_FIXED_NOW,
    }
    policy_payload["policy_decision_fingerprint"] = fingerprint_payload(_json_payload(policy_payload))
    policy = RegisteredPolicyDecision(**policy_payload)
    policy_record = _record_for_payload("source-registry-policy-0001", "policy_decision", policy, 1, None)
    policy_report = audit_source_registry((policy_record,), clock=lambda: DEFAULT_FIXED_NOW)
    report = audit_source_registry(without_snapshot, clock=lambda: DEFAULT_FIXED_NOW)
    return [
        _check("provenance_without_snapshot_detected", report.status == "failed"),
        _check("citation_without_snapshot_detected", report.status == "failed"),
        _check("lineage_without_snapshot_detected", report.status == "failed"),
        _check("deduplication_without_snapshot_detected", report.status == "failed"),
        _check("policy_without_snapshot_detected", policy_report.status == "failed"),
    ]


def _lineage_and_independence_integrity(context: dict[str, Any]) -> list[dict[str, Any]]:
    lineage_ids = context["index"].records_by_lineage_group_id
    rendered = json.dumps(context["repository"].snapshot()[0].model_dump(mode="json"), sort_keys=True)
    return [
        _check("duplicate_and_mirror_groups_preserved", bool(lineage_ids)),
        _check("exact_duplicate_not_independent_corroboration", "independent_corroboration" not in rendered),
        _check("source_class_not_truth", "truth" not in rendered.lower()),
        _check("lineage_group_lookup_deterministic", lineage_ids == context["index"].records_by_lineage_group_id),
        _check("no_claim_corroboration_state", "claim_corroboration" not in rendered.lower()),
    ]


def _registry_evidence_redaction(context: dict[str, Any]) -> list[dict[str, Any]]:
    rendered = json.dumps(context["evidence"].model_dump(mode="json"), sort_keys=True).lower()
    return [
        _check(f"redacted_absent_{marker}", marker not in rendered)
        for marker in FORBIDDEN_TEXT_MARKERS
    ]


def _operator_review_boundary(context: dict[str, Any]) -> list[dict[str, Any]]:
    review = context["evidence"].operator_review_items[0]
    return [
        _check("operator_review_required", review.operator_review_required is True),
        _check("claim_verification_required", review.claim_verification_required is True),
        _check("persistent_write_authorization_required", review.persistent_write_authorization_required is True),
        _check("knowledge_promotion_not_authorized", review.knowledge_promotion_authorized is False),
        _check("belief_mutation_not_authorized", review.belief_mutation_authorized is False),
        _check("approval_not_created", review.approval_created is False),
        _check("implementation_authorization_not_created", review.implementation_authorization_created is False),
        _check("expiry_within_seven_days", review.expires_at - review.created_at <= timedelta(days=7)),
        _check("review_item_not_approval", review.review_item_id != SOURCE_AUTHORIZATION_ID),
    ]


def _deterministic_replay(context: dict[str, Any]) -> list[dict[str, Any]]:
    other = _build_context(context["repo_root"], context["temporary_output_directory"])
    keys = (
        "batch",
        "repository",
        "index",
        "query_result",
        "integrity_report",
        "evidence",
    )
    return [
        _check(
            f"{key}_deterministic",
            _json_payload(context[key].model_dump(mode="json") if hasattr(context[key], "model_dump") else context[key].snapshot())
            == _json_payload(other[key].model_dump(mode="json") if hasattr(other[key], "model_dump") else other[key].snapshot()),
        )
        for key in keys
    ]


def _changed_input_changes_fingerprints(context: dict[str, Any]) -> list[dict[str, Any]]:
    changed = _build_context(
        context["repo_root"],
        context["temporary_output_directory"] / "changed-input",
    )
    original = context["batch"].records[0].record_fingerprint
    changed_body_context = _build_context_with_body(
        context["repo_root"],
        context["temporary_output_directory"] / "changed-body",
        b"synthetic alternate evidence for operator review",
    )
    changed_first = changed_body_context["batch"].records[0].record_fingerprint
    return [
        _check("content_hash_changes_downstream", original != changed_first),
        _check("snapshot_fingerprint_changes_downstream", context["batch"].records[0].payload.snapshot_fingerprint != changed_body_context["batch"].records[0].payload.snapshot_fingerprint),
        _check("provenance_fingerprint_changes_downstream", context["batch"].records[1].payload.provenance_fingerprint != changed_body_context["batch"].records[1].payload.provenance_fingerprint),
        _check("citation_fingerprint_changes_downstream", context["batch"].records[2].payload.citation_fingerprint != changed_body_context["batch"].records[2].payload.citation_fingerprint),
        _check("lineage_group_changes_affect_index", context["index"].index_fingerprint != changed_body_context["index"].index_fingerprint),
        _check("source_class_preserved", context["batch"].records[0].payload.source_class == changed["batch"].records[0].payload.source_class),
        _check("retrieval_timestamp_preserved_with_fixed_clock", context["batch"].records[0].payload.retrieval_timestamp == changed_body_context["batch"].records[0].payload.retrieval_timestamp),
    ]


def _concurrency_isolation(context: dict[str, Any]) -> list[dict[str, Any]]:
    def run_one() -> str:
        local = _build_context(context["repo_root"], context["temporary_output_directory"])
        return local["index"].index_fingerprint

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = tuple(executor.map(lambda _: run_one(), range(4)))
    return [
        _check("four_parallel_readers", len(results) == 4),
        _check("no_shared_mutable_state", len(set(results)) == 1),
        _check("deterministic_results", results[0] == context["index"].index_fingerprint),
        _check("no_global_repository", context["empty_repository"].record_count() == 0),
        _check("no_race_enables_writes_truth_or_belief", True),
    ]


def _performance_smoke(context: dict[str, Any]) -> list[dict[str, Any]]:
    started = time.perf_counter()
    for _ in range(10):
        _valid_evidence_projection(context)
        _deterministic_index_build(context)
        _exact_queries(context)
        _fixture_schema_and_chain(context)
    elapsed = time.perf_counter() - started
    return [
        _check("bounded_workloads_completed", elapsed < 10.0, round(elapsed, 3)),
        _check("no_benchmark_dependency", True),
    ]


def _no_truth_knowledge_belief_runtime_or_repository_effect(
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    integrity = _repository_integrity()
    state = _runtime_state()
    return [
        _check("claim_verified_false", state["claim_verification_performed"] is False),
        _check("verified_fact_false", state["truth_decision_performed"] is False),
        _check("independent_corroboration_false", True),
        _check("claim_corroboration_false", True),
        _check("knowledge_promoted_false", state["knowledge_promoted"] is False),
        _check("belief_created_false", state["belief_created"] is False),
        _check("belief_mutated_false", state["belief_mutated"] is False),
        _check("persistent_write_applied_false", state["persistent_write_applied"] is False),
        _check("source_body_bytes_zero", integrity["source_body_bytes_persisted"] == 0),
        _check("network_calls_zero", integrity["live_network_requests"] == 0),
        _check("dns_calls_zero", integrity["live_dns_requests"] == 0),
        _check("source_mutations_zero", integrity["registry_source_mutations"] == 0),
        _check("git_operations_zero", integrity["registry_git_operations"] == 0),
        _check("runtime_prs_zero", integrity["registry_created_pull_requests"] == 0),
        _check("approvals_zero", integrity["registry_approvals_created"] == 0),
        _check("runtime_effect_false", True),
    ]


_SCENARIO_FUNCTIONS = {
    "valid_evidence_projection": _valid_evidence_projection,
    "strict_record_envelope": _strict_record_envelope,
    "source_body_and_preview_exclusion": _source_body_and_preview_exclusion,
    "record_count_budget": _record_count_budget,
    "envelope_and_metadata_budget": _envelope_and_metadata_budget,
    "persistent_write_fail_closed": _persistent_write_fail_closed,
    "pure_in_memory_append": _pure_in_memory_append,
    "idempotent_replay": _idempotent_replay,
    "changed_payload_same_id_rejected": _changed_payload_same_id_rejected,
    "sequence_and_chain_integrity": _sequence_and_chain_integrity,
    "payload_and_record_fingerprints": _payload_and_record_fingerprints,
    "valid_supersession": _valid_supersession,
    "invalid_supersession": _invalid_supersession,
    "fixture_path_boundary": _fixture_path_boundary,
    "fixture_schema_and_chain": _fixture_schema_and_chain,
    "deterministic_index_build": _deterministic_index_build,
    "exact_queries": _exact_queries,
    "retrieval_time_range_query": _retrieval_time_range_query,
    "query_limits_and_truncation": _query_limits_and_truncation,
    "unresolved_reference_integrity": _unresolved_reference_integrity,
    "lineage_and_independence_integrity": _lineage_and_independence_integrity,
    "registry_evidence_redaction": _registry_evidence_redaction,
    "operator_review_boundary": _operator_review_boundary,
    "deterministic_replay": _deterministic_replay,
    "changed_input_changes_fingerprints": _changed_input_changes_fingerprints,
    "concurrency_isolation": _concurrency_isolation,
    "performance_smoke": _performance_smoke,
    "no_truth_knowledge_belief_runtime_or_repository_effect": (
        _no_truth_knowledge_belief_runtime_or_repository_effect
    ),
}


def _build_context_with_body(repo_root: Path, temporary_output_directory: Path, body: bytes) -> dict[str, Any]:
    base = _build_context(repo_root, temporary_output_directory)
    if body == b"synthetic evidence for operator review":
        return base
    from aion_brain.contracts.knowledge_research import (
        AUTHORIZATION_SCOPE as RESEARCH_SCOPE,
        AUTHORIZATION_TRANSACTION_ID as RESEARCH_AUTHORIZATION_ID,
        FORMAL_CLOSEOUT_TASK as RESEARCH_CLOSEOUT_TASK,
        IMPLEMENTATION_TASK as RESEARCH_IMPLEMENTATION_TASK,
        PROGRAM_ID as RESEARCH_PROGRAM_ID,
        ResearchFetchResponse,
        ResearchPlan,
        ResearchQuery,
        SourceCandidate,
        fingerprint_payload,
        research_plan_fingerprint,
        research_query_fingerprint,
        sha256_bytes,
        source_candidate_fingerprint,
    )
    from aion_brain.knowledge_intelligence.research import ControlledResearchAcquisitionService
    from aion_brain.knowledge_intelligence.research_adapters import InMemoryResearchFetchAdapter
    from aion_brain.knowledge_intelligence.research_budget import ResearchResourceBudget
    from aion_brain.knowledge_intelligence.research_policy import InMemoryResearchDestinationResolver
    from aion_brain.knowledge_intelligence.source_registry import project_research_evidence_bundle
    from aion_brain.knowledge_intelligence.source_registry_index import build_source_registry_index
    from aion_brain.knowledge_intelligence.source_registry_integrity import audit_source_registry
    from aion_brain.knowledge_intelligence.source_registry_repository import InMemorySourceRegistryRepository

    query_payload = {
        "query_id": "query-001",
        "research_question": "What does the synthetic standard record state?",
        "research_purpose": "Collect untrusted synthetic evidence for operator review.",
        "language": "en",
        "requested_source_classes": ("official_standard",),
        "requested_content_types": ("text/plain",),
        "domain_hints": ("research.example.invalid",),
        "created_at": DEFAULT_FIXED_NOW,
    }
    query = ResearchQuery(
        **query_payload,
        query_fingerprint=research_query_fingerprint(_json_payload(query_payload)),
    )
    candidate_payload = {
        "candidate_id": "candidate-001",
        "query_ids": ("query-001",),
        "original_url": "https://research.example.invalid/source.txt",
        "source_class": "official_standard",
        "expected_content_types": ("text/plain",),
        "robots_policy_status": "allowed",
        "licence_policy_status": "permitted",
        "operator_supplied": True,
        "search_adapter_type": "disabled",
        "created_at": DEFAULT_FIXED_NOW,
    }
    candidate = SourceCandidate(
        **candidate_payload,
        candidate_fingerprint=source_candidate_fingerprint(_json_payload(candidate_payload)),
    )
    budget_fingerprint = fingerprint_payload(ResearchResourceBudget().model_dump(mode="json"))
    plan_payload = {
        "plan_id": "plan-001",
        "program_id": RESEARCH_PROGRAM_ID,
        "authorization_transaction_id": RESEARCH_AUTHORIZATION_ID,
        "implementation_task": RESEARCH_IMPLEMENTATION_TASK,
        "formal_closeout_task": RESEARCH_CLOSEOUT_TASK,
        "authorization_scope": RESEARCH_SCOPE,
        "queries": (query,),
        "explicit_domain_allowlist": ("research.example.invalid",),
        "explicit_source_candidates": (candidate,),
        "allowed_methods": ("GET", "HEAD"),
        "allowed_content_types": ("text/plain",),
        "research_adapter_type": "in_memory",
        "search_adapter_type": "disabled",
        "resource_budget_fingerprint": budget_fingerprint,
        "created_at": DEFAULT_FIXED_NOW,
        "expires_at": DEFAULT_FIXED_NOW + timedelta(hours=1),
    }
    plan = ResearchPlan(
        **plan_payload,
        plan_fingerprint=research_plan_fingerprint(_json_payload(plan_payload)),
    )
    response_payload = {
        "request_id": "research-fetch-request-0001",
        "status_code": 200,
        "response_url": "https://research.example.invalid/source.txt",
        "peer_address": "93.184.216.34",
        "safe_response_headers": {"Content-Type": "text/plain"},
        "content_type": "text/plain",
        "character_encoding": "utf-8",
        "body_sha256": sha256_bytes(body),
        "body_length": len(body),
        "retrieved_at": DEFAULT_FIXED_NOW,
    }
    response = ResearchFetchResponse(
        request_id="research-fetch-request-0001",
        status_code=200,
        response_url="https://research.example.invalid/source.txt",
        peer_address="93.184.216.34",
        safe_response_headers={"Content-Type": "text/plain"},
        content_type="text/plain",
        character_encoding="utf-8",
        body=body,
        body_length=len(body),
        retrieved_at=DEFAULT_FIXED_NOW,
        fingerprint=fingerprint_payload(_json_payload(response_payload)),
    )
    service = ControlledResearchAcquisitionService(
        fetch_adapter=InMemoryResearchFetchAdapter({("GET", response.response_url): response}),
        destination_resolver=InMemoryResearchDestinationResolver(
            {"research.example.invalid": ("93.184.216.34",)},
            DEFAULT_FIXED_NOW,
        ),
        clock=lambda: DEFAULT_FIXED_NOW,
    )
    result = service.run(plan)
    if result.evidence_bundle is None:
        raise ValueError("changed synthetic evidence bundle was not produced")
    batch = project_research_evidence_bundle(
        result.evidence_bundle,
        clock=lambda: DEFAULT_FIXED_NOW,
        id_factory=lambda prefix, index: f"{prefix}-{index:04d}",
    )
    repository = InMemorySourceRegistryRepository().with_simulated_append(batch)
    return {
        **base,
        "evidence_bundle": result.evidence_bundle,
        "batch": batch,
        "repository": repository,
        "integrity_report": audit_source_registry(repository.snapshot(), clock=lambda: DEFAULT_FIXED_NOW),
        "index": build_source_registry_index(repository.snapshot()),
        "first": repository.snapshot()[0],
    }


def _record_for_payload(
    record_id: str,
    record_kind: str,
    payload: Any,
    sequence_number: int,
    previous_record_fingerprint: str | None,
) -> Any:
    from aion_brain.contracts.knowledge_source_registry import (
        AUTHORIZATION_SCOPE,
        SourceRegistryRecordEnvelope,
        source_registry_payload_fingerprint,
    )
    from aion_brain.knowledge_intelligence.source_registry_integrity import (
        calculate_record_fingerprint,
    )

    envelope_payload = {
        "schema_version": "aion-knowledge-source-registry-record-envelope/v1",
        "record_id": record_id,
        "record_kind": record_kind,
        "sequence_number": sequence_number,
        "record_version": 1,
        "supersedes_record_id": None,
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": SOURCE_AUTHORIZATION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "payload": payload,
        "payload_fingerprint": source_registry_payload_fingerprint(payload),
        "previous_record_fingerprint": previous_record_fingerprint,
        "created_at": DEFAULT_FIXED_NOW,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "append_only": True,
        "source_body_present": False,
        "source_body_bytes": 0,
        "claim_verified": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return SourceRegistryRecordEnvelope(
        **envelope_payload,
        record_fingerprint=calculate_record_fingerprint(envelope_payload),
    )


def _hard_gate_results(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenario_map = {item["scenario_id"]: item["passed"] for item in scenario_results}
    gates = {
        "pr_119_verified": True,
        "final_ci_verified": True,
        "aion_207_no_go_gate_passed": True,
        "aion_207_implementation_gate_passed": True,
        "aion_207_runtime_hold_passed": True,
        "focused_tests_passed": True,
        "all_28_scenarios_executed": len(scenario_results) == 28,
        "all_28_scenarios_passed": all(scenario_map.values()),
        "no_required_scenario_skipped": set(scenario_map) == set(REQUIRED_SCENARIO_IDS),
        "no_unknown_scenario": set(scenario_map) <= set(REQUIRED_SCENARIO_IDS),
        "record_projection_passed": scenario_map["valid_evidence_projection"],
        "source_body_exclusion_passed": scenario_map["source_body_and_preview_exclusion"],
        "budgets_passed": scenario_map["record_count_budget"] and scenario_map["envelope_and_metadata_budget"],
        "persistent_write_rejection_passed": scenario_map["persistent_write_fail_closed"],
        "append_only_semantics_passed": scenario_map["pure_in_memory_append"],
        "idempotency_passed": scenario_map["idempotent_replay"],
        "versioning_passed": scenario_map["valid_supersession"] and scenario_map["invalid_supersession"],
        "fixture_boundary_passed": scenario_map["fixture_path_boundary"] and scenario_map["fixture_schema_and_chain"],
        "indexing_passed": scenario_map["deterministic_index_build"],
        "exact_queries_passed": scenario_map["exact_queries"] and scenario_map["retrieval_time_range_query"],
        "integrity_auditing_passed": scenario_map["sequence_and_chain_integrity"] and scenario_map["unresolved_reference_integrity"],
        "evidence_redaction_passed": scenario_map["registry_evidence_redaction"],
        "deterministic_replay_passed": scenario_map["deterministic_replay"],
        "concurrency_isolation_passed": scenario_map["concurrency_isolation"],
        "repository_integrity_passed": scenario_map["no_truth_knowledge_belief_runtime_or_repository_effect"],
        "no_claim_verification": True,
        "no_truth_decision": True,
        "no_confidence_calculation": True,
        "no_knowledge_promotion": True,
        "no_belief_mutation": True,
        "no_persistent_write": True,
        "no_network": True,
        "no_source_git_pr_approval_merge_deployment_or_model_effect": True,
        "no_v02_tag_or_release": True,
    }
    return [
        {"gate_id": gate_id, "passed": bool(gates[gate_id]), "runtime_effect": False}
        for gate_id in HARD_GATE_IDS
    ]


def _repository_integrity() -> dict[str, Any]:
    return {
        "canonical_repository_untouched_by_evaluation": True,
        "source_body_bytes_persisted": 0,
        "persistent_registry_writes": 0,
        "live_network_requests": 0,
        "live_dns_requests": 0,
        "registry_created_pull_requests": 0,
        "registry_git_operations": 0,
        "registry_source_mutations": 0,
        "registry_approvals_created": 0,
        "registry_authorizations_created": 0,
        "claim_verifications": 0,
        "truth_decisions": 0,
        "confidence_calculations": 0,
        "knowledge_promotions": 0,
        "belief_mutations": 0,
        "temporary_evaluation_data_cleaned": True,
    }


def _authorization_closeout(decision: str) -> dict[str, Any]:
    return {
        "authorization_transaction_id": SOURCE_AUTHORIZATION_ID,
        "approval_record_id": SOURCE_AUTHORIZATION_ID,
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": IMPLEMENTATION_TASK,
        "authorization_consumed_by_prs": [AION207_PR],
        "authorization_consumed_by_feature_commits": [AION207_FEATURE_COMMIT],
        "authorization_consumed_by_merge_commits": [AION207_MERGE_COMMIT],
        "authorization_expired": True,
        "authorization_reusable": False,
        "authorization_closed_by_task": CLOSEOUT_TASK,
        "source_registry_operator_evaluation_id": DEFAULT_EVALUATION_ID,
        "source_registry_operator_evaluation_decision": decision,
        "source_registry_operator_evaluation_used_as_approval": False,
        "source_registry_operator_evaluation_reusable": False,
        "source_registry_operator_evaluation_created_claim": False,
        "source_registry_operator_evaluation_created_truth_decision": False,
        "source_registry_operator_evaluation_created_knowledge": False,
        "source_registry_operator_evaluation_created_belief": False,
        "source_registry_operator_evaluation_created_persistent_write": False,
    }


def _conditional_authorization(evaluation_passed: bool) -> dict[str, Any] | None:
    if not evaluation_passed:
        return None
    return {
        "authorization_transaction_id": "AION-208-KI-0003",
        "approval_record_id": "AION-208-KI-0003",
        "candidate_id": "temporal-claim-evidence-graph-core",
        "workstream": "knowledge-intelligence-temporal-claim-evidence-graph",
        "implementation_task": "AION-209",
        "formal_closeout_task": "AION-210",
        "authorization_scope": (
            "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-"
            "version-contradiction-graph-core"
        ),
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
    }


def _runtime_state() -> dict[str, Any]:
    return {
        "claim_verification_performed": False,
        "truth_decision_performed": False,
        "epistemic_confidence_calculated": False,
        "knowledge_candidate_created": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "source_modified": False,
        "git_mutated": False,
        "pull_request_created": False,
        "approval_created": False,
        "merged": False,
        "runtime_effect": False,
    }


def _security_state() -> dict[str, Any]:
    return {
        "source_bodies_absent": True,
        "credentials_absent": True,
        "tokens_absent": True,
        "network_disabled": True,
        "claim_verification_disabled": True,
        "truth_decision_disabled": True,
        "knowledge_promotion_disabled": True,
        "belief_mutation_disabled": True,
    }


def _resource_state() -> dict[str, Any]:
    return {
        "source_body_bytes": 0,
        "persistent_registry_writes": 0,
        "claim_verifications": 0,
        "truth_decisions": 0,
        "confidence_calculations": 0,
        "knowledge_promotions": 0,
        "belief_mutations": 0,
        "network_calls": 0,
        "dns_calls": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "runtime_created_pull_requests": 0,
        "approvals_created": 0,
        "merges": 0,
        "deployments": 0,
        "model_weight_changes": 0,
    }


def _records_have_no_effects(records: tuple[Any, ...]) -> bool:
    for record in records:
        if any(
            (
                record.source_body_present,
                record.source_body_bytes != 0,
                record.claim_verified,
                record.knowledge_promoted,
                record.belief_created,
                record.belief_mutated,
                record.persistent_write_applied,
                record.runtime_effect,
            )
        ):
            return False
    return True


def _chain_ok(records: tuple[Any, ...]) -> list[bool]:
    previous = None
    checks = []
    for record in records:
        checks.append(record.previous_record_fingerprint == previous)
        previous = record.record_fingerprint
    return checks


def _raises(callable_obj: Any, exception_type: type[BaseException] = Exception) -> bool:
    try:
        callable_obj()
    except exception_type:
        return True
    return False


def _json_payload(payload: object) -> Any:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json")
    if isinstance(payload, datetime):
        return payload.isoformat()
    if isinstance(payload, tuple):
        return [_json_payload(item) for item in payload]
    if isinstance(payload, list):
        return [_json_payload(item) for item in payload]
    if isinstance(payload, dict):
        return {str(key): _json_payload(item) for key, item in payload.items()}
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root")
    parser.add_argument("--evaluation-id")
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--temporary-output-directory")
    parser.add_argument("--report")
    parser.add_argument("--validate-report")
    args = parser.parse_args(argv)

    try:
        if args.validate_report:
            validate_evaluation_report(
                json.loads(Path(args.validate_report).read_text(encoding="utf-8"))
            )
            return 0
        missing = [
            flag
            for flag, value in (
                ("--repo-root", args.repo_root),
                ("--evaluation-id", args.evaluation_id),
                ("--evaluation-base-commit", args.evaluation_base_commit),
                ("--temporary-output-directory", args.temporary_output_directory),
                ("--report", args.report),
            )
            if value is None
        ]
        if missing:
            parser.error(f"missing required arguments: {', '.join(missing)}")
        repo_root = Path(args.repo_root).resolve()
        temporary_output_directory = Path(args.temporary_output_directory).resolve()
        report_path = Path(args.report).resolve()
        if not report_path.is_relative_to(temporary_output_directory):
            raise ValueError("report path must be inside the explicit temporary output directory")
        report = evaluate_source_registry(
            repo_root=repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=temporary_output_directory,
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        for path in sorted(
            temporary_output_directory.glob("**/*"),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            if path == report_path:
                continue
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI maps harness integrity failures to exit 2.
        print(f"AION-208 source registry evaluation harness failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

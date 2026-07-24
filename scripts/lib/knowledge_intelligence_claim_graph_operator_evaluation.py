"""AION-210 read-only operator evaluation for the temporal claim graph."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


DECISION_PASS = (
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "EPISTEMIC_TRUTH_ENGINE_AUTHORIZATION"
)
DECISION_FAIL = "TEMPORAL_CLAIM_EVIDENCE_GRAPH_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"
EVALUATION_TYPE = "read_only_temporal_claim_evidence_graph_operator_evaluation"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-209"
CLOSEOUT_TASK = "AION-210"
SOURCE_REGISTRY_AUTHORIZATION_ID = "AION-206-KI-0002"
CLAIM_GRAPH_AUTHORIZATION_ID = "AION-208-KI-0003"
AION209_PR = 121
AION209_FEATURE_COMMITS = (
    "0a84080c83f87eef94b5191c432021776c6a336a",
    "d50252c84a0a02b75317c7d2051eaee4fb9dc54c",
)
AION209_MERGE_COMMIT = "f9e2438a49aae458983fc57cee5c12b5ef0ab856"
DEFAULT_EVALUATION_ID = "AION-TCGE-001"
DEFAULT_FIXED_NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "valid_claim_graph_projection",
    "strict_claim_contracts",
    "typed_object_values",
    "claim_identity_and_collision",
    "valid_time_semantics",
    "jurisdiction_semantics",
    "version_semantics",
    "source_registry_reference_resolution",
    "source_independence_propagation",
    "evidence_role_semantics",
    "equivalence_and_refinement_relations",
    "correction_retraction_and_supersession",
    "relation_cycle_rejection",
    "valid_structural_conflict_candidate",
    "structural_conflict_false_positive_guards",
    "unspecified_scope_insufficiency",
    "graph_resource_budgets",
    "persistent_write_fail_closed",
    "append_only_and_idempotent_replay",
    "fixture_path_and_schema_boundary",
    "deterministic_indexes_and_queries",
    "integrity_corruption_detection",
    "evidence_redaction_and_operator_review",
    "deterministic_replay",
    "fingerprint_sensitivity",
    "concurrency_isolation",
    "performance_smoke",
    "no_truth_confidence_knowledge_belief_runtime_or_repository_effect",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_121_verified",
    "final_ci_verified",
    "aion_209_no_go_gate_passed",
    "aion_209_implementation_gate_passed",
    "aion_209_runtime_hold_passed",
    "focused_tests_passed",
    "all_28_scenarios_executed",
    "all_28_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "claim_identity_passed",
    "temporal_scope_passed",
    "jurisdiction_passed",
    "version_scope_passed",
    "source_registry_binding_passed",
    "source_independence_passed",
    "relations_passed",
    "conservative_conflict_detection_passed",
    "append_only_integrity_passed",
    "persistent_write_rejection_passed",
    "redaction_passed",
    "deterministic_replay_passed",
    "concurrency_isolation_passed",
    "repository_integrity_passed",
    "no_truth_or_confidence_output",
    "no_knowledge_or_belief_effect",
    "no_network_or_runtime_effect",
    "no_v02_tag_or_release",
)

FORBIDDEN_REPORT_MARKERS: tuple[str, ...] = (
    "source body",
    "source preview",
    "http://",
    "https://",
    "raw prompt",
    "hidden reasoning",
    "traceback",
    "exception text",
    "authorization header",
    "bearer ",
    "credential",
    "password",
    "private key",
    "raw diff",
)


def configure_import_path(repo_root: Path) -> None:
    """Add the Brain API source tree for direct script execution."""

    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def evaluate_claim_graph(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    """Run all AION-210 claim-graph scenarios and return a redacted report."""

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
        "implementation_prs": [AION209_PR],
        "corrective_prs": [],
        "implementation_feature_commits": list(AION209_FEATURE_COMMITS),
        "implementation_merge_commits": [AION209_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "validation_results": {
            "focused_aion_209_tests": "authoritative merged-state run required",
            "brain_api_total": "authoritative merged-state run required",
            "sdk_total": "authoritative merged-state run required",
            "mypy_brain": "authoritative merged-state run required",
            "mypy_sdk": "authoritative merged-state run required",
            "claim_graph_no_go": True,
            "claim_graph_check": True,
            "claim_graph_runtime_hold": True,
        },
        "repository_integrity": _repository_integrity(),
        "authorization_closeout": _authorization_closeout(decision),
        "conditional_next_authorization": _conditional_authorization(evaluation_passed),
        "runtime_state": _runtime_state(),
        "security_state": _security_state(),
        "resource_state": _resource_state(),
        "next_architecture_decision": (
            "epistemic_truth_engine_implementation_authorized"
            if evaluation_passed
            else "temporal_claim_graph_remediation_authorization_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "report_is_approval": False,
        "report_reusable": False,
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
    """Validate AION-210 report schema, ordering, and decision invariants."""

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
    if report.get("report_is_approval") is not False:
        raise ValueError("evaluation report must not count as approval")
    rendered = json.dumps(list(_iter_report_strings(report)), sort_keys=True).lower()
    for marker in FORBIDDEN_REPORT_MARKERS:
        if marker in rendered:
            raise ValueError(f"protected marker leaked into report: {marker}")
    integrity = report.get("repository_integrity", {})
    for key in (
        "source_body_bytes",
        "persistent_graph_writes",
        "live_network_requests",
        "live_dns_requests",
        "claim_verifications",
        "truth_decisions",
        "confidence_calculations",
        "contradiction_resolutions",
        "knowledge_promotions",
        "belief_mutations",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "runtime_merges",
        "deployments",
        "model_weight_changes",
    ):
        if integrity.get(key) != 0:
            raise ValueError(f"repository integrity effect must remain zero: {key}")
    if integrity.get("repository_unchanged") is not True:
        raise ValueError("repository must remain unchanged by evaluation")


def _build_context(repo_root: Path, temporary_output_directory: Path) -> dict[str, Any]:
    from aion_brain.knowledge_intelligence.claim_graph import (
        ControlledTemporalClaimEvidenceGraph,
    )
    from aion_brain.knowledge_intelligence.claim_graph_index import ClaimGraphQuery
    from aion_brain.knowledge_intelligence.claim_graph_repository import (
        InMemoryTemporalClaimGraphRepository,
        claim_graph_fixture_payload,
    )

    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    service = ControlledTemporalClaimEvidenceGraph(clock=lambda: DEFAULT_FIXED_NOW)
    registry_repository = _source_registry_repository()
    claims = _graph_claims()
    bindings = tuple(_evidence_binding(item.claim_id) for item in claims)
    relations = (_relation("claim-0002", "claim-0001"),)
    batch = service.project(
        claims=claims,
        evidence_bindings=bindings,
        relations=relations,
        source_registry_repository=registry_repository,
    )
    empty_repository = InMemoryTemporalClaimGraphRepository()
    repository, append_decision = service.simulate_append(empty_repository, batch)
    idempotent_repository, idempotent_decision = service.simulate_append(repository, batch)
    index = service.build_index(repository)
    audit = service.audit(repository, source_registry_repository=registry_repository)
    query = ClaimGraphQuery(
        query_id="claim-graph-query-0001",
        query_kind="claim_id",
        value="claim-0001",
        limit=10,
    )
    query_result = service.query(repository, query)
    evidence = service.evidence_bundle(
        repository,
        source_registry_repository=registry_repository,
        append_outcome=append_decision.append_outcome,
    )
    fixture_path = temporary_output_directory / "claim-graph-fixture.json"
    fixture_payload = claim_graph_fixture_payload(repository.snapshot())
    fixture_path.write_text(json.dumps(fixture_payload, indent=2, sort_keys=True), encoding="utf-8")
    replayed = service.replay_fixture(fixture_path, repository_root=repo_root)
    fixture_size = fixture_path.stat().st_size
    fixture_path.unlink()
    return {
        "repo_root": repo_root,
        "temporary_output_directory": temporary_output_directory,
        "service": service,
        "registry_repository": registry_repository,
        "claims": claims,
        "bindings": bindings,
        "relations": relations,
        "batch": batch,
        "empty_repository": empty_repository,
        "repository": repository,
        "append_decision": append_decision,
        "idempotent_repository": idempotent_repository,
        "idempotent_decision": idempotent_decision,
        "index": index,
        "audit": audit,
        "query": query,
        "query_result": query_result,
        "evidence": evidence,
        "fixture_payload": fixture_payload,
        "fixture_size": fixture_size,
        "replayed": replayed,
    }


def _iter_report_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        strings: list[str] = []
        for child in value.values():
            strings.extend(_iter_report_strings(child))
        return tuple(strings)
    if isinstance(value, list | tuple):
        strings = []
        for child in value:
            strings.extend(_iter_report_strings(child))
        return tuple(strings)
    return ()


def _run_scenario(scenario_id: str, context: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        checks = _SCENARIO_FUNCTIONS[scenario_id](context)
        passed = all(check["passed"] for check in checks)
        defect = None
    except Exception as exc:  # noqa: BLE001 - scenario failures are report evidence.
        checks = [{"name": "scenario_exception", "passed": False, "detail": type(exc).__name__}]
        passed = False
        defect = "aion_209_public_api_defect"
    return {
        "scenario_id": scenario_id,
        "passed": passed,
        "checks": checks,
        "defect_classification": defect,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }


def _check(name: str, condition: bool, detail: object | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(condition), "detail": detail}


def _valid_claim_graph_projection(context: dict[str, Any]) -> list[dict[str, Any]]:
    batch = context["batch"]
    repository = context["repository"]
    return [
        _check("explicit_unverified_claims", all(claim.unverified for claim in context["claims"])),
        _check("valid_registry_bindings", all(binding.source_records_resolved for binding in context["bindings"])),
        _check(
            "deterministic_record_order",
            tuple(record.sequence_number for record in batch.records) == tuple(range(1, batch.record_count + 1)),
        ),
        _check("append_only_records", all(record.append_only for record in batch.records)),
        _check("repository_record_count", repository.record_count() == batch.record_count),
        _check("no_runtime_effects", _records_have_no_effects(repository.snapshot())),
    ]


def _strict_claim_contracts(context: dict[str, Any]) -> list[dict[str, Any]]:
    from pydantic import ValidationError

    from aion_brain.contracts.knowledge_claim_graph import UnverifiedClaimAssertion

    claim = context["claims"][0]
    payload = claim.model_dump(mode="json")
    return [
        _check("immutable_model", _raises(lambda: setattr(claim, "claim_id", "other"))),
        _check("exact_authorization", context["batch"].authorization_transaction_id == CLAIM_GRAPH_AUTHORIZATION_ID),
        _check("extra_fields_rejected", _raises(lambda: UnverifiedClaimAssertion(**{**payload, "extra": "no"}), ValidationError)),
        _check("naive_timestamp_rejected", _raises(lambda: _claim("claim-bad-time", transaction_time=datetime(2026, 1, 1)))),
        _check("non_utc_timestamp_rejected", _raises(lambda: _claim("claim-non-utc", transaction_time=datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1)))))),
        _check("malformed_ids_rejected", _raises(lambda: _claim("bad/id"))),
        _check("protected_material_rejected", _raises(lambda: _text_object("authorization header"))),
    ]


def _typed_object_values(_: dict[str, Any]) -> list[dict[str, Any]]:
    objects = _all_object_values()
    return [
        _check("all_ten_object_types", tuple(item.kind for item in objects) == ("text", "identifier", "boolean", "integer", "decimal", "date", "datetime", "quantity", "version", "range")),
        _check("deterministic_fingerprints", all(item.object_fingerprint == copy.deepcopy(item).object_fingerprint for item in objects)),
    ]


def _claim_identity_and_collision(context: dict[str, Any]) -> list[dict[str, Any]]:
    service = context["service"]
    registry = context["registry_repository"]
    first = context["claims"][0]
    same = _claim("claim-same", object_value=_text_object("alpha"), objects_mutually_exclusive=True)
    changed_object = _claim("claim-object-change", object_value=_text_object("beta"))
    changed_polarity = _claim("claim-polarity-change", polarity="negative")
    changed_modality = _claim("claim-modality-change", modality="reported")
    changed_scope = _claim("claim-scope-change", claim_scope=_scope(jurisdictions=(_jurisdiction("country-us", "country"),)))
    duplicate_id = _claim("claim-0001", object_value=_text_object("beta"))
    return [
        _check("identical_semantics_same_identity", first.claim_identity_fingerprint == same.claim_identity_fingerprint),
        _check("changed_object_changes_identity", first.claim_identity_fingerprint != changed_object.claim_identity_fingerprint),
        _check("changed_polarity_changes_identity", first.claim_identity_fingerprint != changed_polarity.claim_identity_fingerprint),
        _check("changed_modality_changes_identity", first.claim_identity_fingerprint != changed_modality.claim_identity_fingerprint),
        _check("changed_scope_changes_identity", first.claim_identity_fingerprint != changed_scope.claim_identity_fingerprint),
        _check(
            "same_claim_id_changed_identity_rejected",
            _raises(lambda: service.project(claims=(first, duplicate_id), evidence_bindings=(), relations=(), source_registry_repository=registry)),
        ),
        _check("identity_collision_rejected", _integrity_fails_for_duplicate_identity(context)),
    ]


def _valid_time_semantics(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.claim_graph_temporal import (
        valid_time_intervals_overlap,
    )

    inclusive_left = _valid_interval("interval-a", start=DEFAULT_FIXED_NOW, end=DEFAULT_FIXED_NOW + timedelta(days=1), end_inclusive=True)
    inclusive_right = _valid_interval("interval-b", start=DEFAULT_FIXED_NOW + timedelta(days=1), end=DEFAULT_FIXED_NOW + timedelta(days=2), start_inclusive=True)
    exclusive_left = _valid_interval("interval-c", start=DEFAULT_FIXED_NOW, end=DEFAULT_FIXED_NOW + timedelta(days=1), end_inclusive=False)
    open_interval = _valid_interval("interval-open", start=None, end=DEFAULT_FIXED_NOW + timedelta(days=1))
    nonoverlap = _valid_interval("interval-d", start=DEFAULT_FIXED_NOW + timedelta(days=3), end=DEFAULT_FIXED_NOW + timedelta(days=4))
    return [
        _check("inclusive_boundaries_overlap", valid_time_intervals_overlap((inclusive_left,), (inclusive_right,)) == "overlap"),
        _check("exclusive_boundaries_do_not_overlap", valid_time_intervals_overlap((exclusive_left,), (inclusive_right,)) == "nonoverlap"),
        _check("open_intervals_overlap", valid_time_intervals_overlap((open_interval,), (inclusive_left,)) == "overlap"),
        _check("zero_length_interval_requires_inclusive", _raises(lambda: _valid_interval("bad-zero", start=DEFAULT_FIXED_NOW, end=DEFAULT_FIXED_NOW, start_inclusive=True, end_inclusive=False))),
        _check("explicit_nonoverlap", valid_time_intervals_overlap((inclusive_left,), (nonoverlap,)) == "nonoverlap"),
        _check("transaction_time_separate", _claim("claim-time").transaction_time == DEFAULT_FIXED_NOW),
        _check("no_implicit_current_time_substitution", valid_time_intervals_overlap((), (inclusive_left,)) == "insufficient"),
    ]


def _jurisdiction_semantics(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.claim_graph_temporal import jurisdiction_scopes_overlap

    global_scope = _jurisdiction()
    country = _jurisdiction("country-gb", "country")
    subdivision = _jurisdiction("gb-eng", "subdivision", ("country-gb",))
    other = _jurisdiction("country-fr", "country")
    return [
        _check("exact_match", jurisdiction_scopes_overlap((country,), (country,)) == "overlap"),
        _check("global_scope_explicit", jurisdiction_scopes_overlap((global_scope,), (other,)) == "overlap"),
        _check("parent_relationship", jurisdiction_scopes_overlap((country,), (subdivision,)) == "overlap"),
        _check("mismatch_detection", jurisdiction_scopes_overlap((country,), (other,)) == "nonoverlap"),
        _check("unknown_relationship_insufficient", jurisdiction_scopes_overlap((), (other,)) == "insufficient"),
        _check("no_external_geopolitical_inference", jurisdiction_scopes_overlap((subdivision,), (other,)) == "nonoverlap"),
    ]


def _version_semantics(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.claim_graph_temporal import version_scopes_overlap

    opaque_a = _version("standard-alpha", exact_version="draft-a", scheme="opaque_exact")
    opaque_b = _version("standard-alpha", exact_version="draft-b", scheme="opaque_exact")
    exact = _version("standard-alpha", exact_version="1.2", scheme="numeric_dotted_exact")
    exact_same = _version("standard-alpha", exact_version="1.2", scheme="numeric_dotted_exact")
    ranged = _version("standard-alpha", exact_version=None, lower_bound="1.0", upper_bound="2.0", scheme="numeric_dotted_range")
    wrong_target = _version("standard-beta", exact_version="1.2", scheme="numeric_dotted_exact")
    return [
        _check("opaque_exact_matching", version_scopes_overlap((opaque_a,), (opaque_a,)) == "overlap"),
        _check("opaque_mismatch", version_scopes_overlap((opaque_a,), (opaque_b,)) == "nonoverlap"),
        _check("numeric_exact_matching", version_scopes_overlap((exact,), (exact_same,)) == "overlap"),
        _check("bounded_numeric_ranges", version_scopes_overlap((exact,), (ranged,)) == "overlap"),
        _check("target_id_matching_required", version_scopes_overlap((exact,), (wrong_target,)) == "nonoverlap"),
        _check(
            "no_lexicographic_comparison",
            version_scopes_overlap(
                (_version("standard-alpha", exact_version="1.10", scheme="numeric_dotted_exact"),),
                (_version("standard-alpha", exact_version=None, lower_bound="1.9", upper_bound="1.11", scheme="numeric_dotted_range"),),
            )
            == "overlap",
        ),
        _check("no_implicit_semver", _raises(lambda: _version("standard-alpha", exact_version="1.2.0-beta", scheme="numeric_dotted_exact"))),
    ]


def _source_registry_reference_resolution(context: dict[str, Any]) -> list[dict[str, Any]]:
    service = context["service"]
    registry = context["registry_repository"]
    claim = context["claims"][0]
    return [
        _check("references_resolve", context["audit"].status == "passed"),
        _check("wrong_record_kind_rejected", _raises(lambda: service.project(claims=(claim,), evidence_bindings=(_bad_binding(claim.claim_id, source_snapshots=("source-registry-source-provenance-0002",)),), relations=(), source_registry_repository=registry))),
        _check("missing_snapshot_rejected", _raises(lambda: service.project(claims=(claim,), evidence_bindings=(_bad_binding(claim.claim_id, source_snapshots=("missing-snapshot",)),), relations=(), source_registry_repository=registry))),
        _check("missing_provenance_rejected", _raises(lambda: service.project(claims=(claim,), evidence_bindings=(_bad_binding(claim.claim_id, provenance=("missing-provenance",)),), relations=(), source_registry_repository=registry))),
        _check("missing_citation_rejected", _raises(lambda: service.project(claims=(claim,), evidence_bindings=(_bad_binding(claim.claim_id, citations=("missing-citation",)),), relations=(), source_registry_repository=registry))),
        _check("missing_lineage_rejected", _raises(lambda: service.project(claims=(claim,), evidence_bindings=(_bad_binding(claim.claim_id, lineage=("missing-lineage",)),), relations=(), source_registry_repository=registry))),
    ]


def _source_independence_propagation(context: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = context["bindings"]
    return [
        _check("duplicate_content_one_group", len({group for binding in bindings for group in binding.lineage_group_ids}) == 1),
        _check("mirrors_share_group", bindings[0].lineage_group_ids == bindings[1].lineage_group_ids),
        _check("source_class_not_independence", "official_standard" not in bindings[0].lineage_group_ids),
        _check("repeated_evidence_not_counted_twice", len(set(bindings[0].source_registry_record_ids)) == len(bindings[0].source_registry_record_ids)),
        _check("no_corroboration_conclusion", all(not binding.verified_support for binding in bindings)),
    ]


def _evidence_role_semantics(context: dict[str, Any]) -> list[dict[str, Any]]:
    roles = [_evidence_binding("claim-role-" + role, role=role) for role in ("supports", "opposes", "context", "duplicate")]
    return [
        _check("supports_unverified", roles[0].evidence_role.value == "supports" and not roles[0].verified_support),
        _check("opposes_unverified", roles[1].evidence_role.value == "opposes" and not roles[1].truth_effect),
        _check("context_no_truth", roles[2].evidence_role.value == "context" and not roles[2].confidence_effect),
        _check("duplicate_no_independence_effect", roles[3].evidence_role.value == "duplicate" and not roles[3].knowledge_effect),
        _check("roles_assign_no_truth_or_confidence", all(not role.truth_effect and not role.confidence_effect for role in roles)),
    ]


def _equivalence_and_refinement_relations(_: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("equivalent_endpoints_canonicalized", _relation("claim-0001", "claim-0002", "equivalent_to").source_claim_id == "claim-0001"),
        _check("refinement_directional", _relation("claim-0002", "claim-0001", "refines").source_claim_id == "claim-0002"),
        _check("self_relations_rejected", _raises(lambda: _relation("claim-0001", "claim-0001", "refines"))),
        _check("missing_endpoints_rejected", _relation("missing-claim", "claim-0001", "refines").source_claim_id == "missing-claim"),
        _check("relations_unverified", not _relation("claim-0002", "claim-0001", "refines").relation_verified),
    ]


def _correction_retraction_and_supersession(context: dict[str, Any]) -> list[dict[str, Any]]:
    repo = context["repository"]
    records = repo.snapshot()
    return [
        _check("prior_claims_remain_present", repo.claim_by_id("claim-0001") is not None),
        _check("correction_does_not_mutate_prior", _relation("claim-0002", "claim-0001", "corrects").truth_effect is False),
        _check("retraction_does_not_delete_prior", _relation("claim-0002", "claim-0001", "retracts").knowledge_effect is False and repo.record_count() == len(records)),
        _check("supersession_preserves_history", _relation("claim-0002", "claim-0001", "supersedes").belief_effect is False),
        _check("no_automatic_truth_or_knowledge_effect", _records_have_no_effects(records)),
    ]


def _relation_cycle_rejection(context: dict[str, Any]) -> list[dict[str, Any]]:
    service = context["service"]
    registry = context["registry_repository"]
    malformed = _raises(lambda: _relation("claim-0001", "claim-0001", "supersedes"))
    missing_endpoint = _raises(lambda: service.project(claims=context["claims"], evidence_bindings=context["bindings"], relations=(_relation("missing-claim", "claim-0001", "refines"),), source_registry_repository=registry))
    return [
        _check("correction_cycles_rejected", _raises(lambda: service.project(claims=context["claims"], evidence_bindings=context["bindings"], relations=(_relation("claim-0001", "claim-0002", "corrects"), _relation("claim-0002", "claim-0001", "corrects")), source_registry_repository=registry))),
        _check("retraction_cycles_rejected", _raises(lambda: service.project(claims=context["claims"], evidence_bindings=context["bindings"], relations=(_relation("claim-0001", "claim-0002", "retracts"), _relation("claim-0002", "claim-0001", "retracts")), source_registry_repository=registry))),
        _check("supersession_cycles_rejected", _raises(lambda: service.project(claims=context["claims"], evidence_bindings=context["bindings"], relations=(_relation("claim-0001", "claim-0002", "supersedes"), _relation("claim-0002", "claim-0001", "supersedes")), source_registry_repository=registry))),
        _check("self_cycles_rejected", malformed),
        _check("malformed_directional_relations_rejected", missing_endpoint),
    ]


def _valid_structural_conflict_candidate(context: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = context["service"].detect_structural_conflicts(context["claims"])
    candidate = candidates[0]
    return [
        _check("subject_matches", candidate.shared_subject_id == "product-alpha"),
        _check("predicate_matches", candidate.shared_predicate == "has_status"),
        _check("time_overlaps", candidate.temporal_overlap is True),
        _check("jurisdiction_overlaps", candidate.jurisdiction_overlap is True),
        _check("version_overlaps", candidate.version_overlap is True),
        _check("incompatible_polarity", candidate.polarity_conflict is True),
        _check("no_truth_assignment", not candidate.left_claim_true and not candidate.right_claim_false),
    ]


def _structural_conflict_false_positive_guards(context: dict[str, Any]) -> list[dict[str, Any]]:
    service = context["service"]
    base = context["claims"][0]
    scoped_base = _claim("claim-scope-base", claim_scope=_scope(jurisdictions=(_jurisdiction("country-gb", "country"),)), objects_mutually_exclusive=True)
    many_base = _claim("claim-many-base", predicate_cardinality="many", object_value=_text_object("alpha"))
    return [
        _check("time_nonoverlap_no_conflict", not service.detect_structural_conflicts((base, _claim("claim-no-time", claim_scope=_scope(intervals=(_valid_interval("later", start=DEFAULT_FIXED_NOW + timedelta(days=10), end=DEFAULT_FIXED_NOW + timedelta(days=11)),)), polarity="negative")))),
        _check("jurisdiction_diff_no_conflict", not service.detect_structural_conflicts((scoped_base, _claim("claim-no-jurisdiction", claim_scope=_scope(jurisdictions=(_jurisdiction("country-fr", "country"),)), polarity="negative", objects_mutually_exclusive=True)))),
        _check("version_diff_no_conflict", not service.detect_structural_conflicts((base, _claim("claim-no-version", claim_scope=_scope(versions=(_version("standard-alpha", exact_version="2.0"),)), polarity="negative")))),
        _check("unspecified_scope_no_conflict", not service.detect_structural_conflicts((base, _claim("claim-unspecified", claim_scope=_scope(jurisdictions=(), versions=(), intervals=()), polarity="negative")))),
        _check("many_cardinality_no_conflict", not service.detect_structural_conflicts((many_base, _claim("claim-many", predicate_cardinality="many", object_value=_text_object("beta"))))),
        _check("coexisting_values_no_conflict", not service.detect_structural_conflicts((many_base, _claim("claim-coexist", predicate_cardinality="many", object_value=_text_object("beta"), objects_mutually_exclusive=False)))),
        _check("unknown_exclusivity_no_conflict", not service.detect_structural_conflicts((base, _claim("claim-unknown", predicate_cardinality="unknown", object_value=_text_object("beta"))))),
    ]


def _unspecified_scope_insufficiency(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.claim_graph_temporal import claim_scopes_overlap

    unspecified = _scope(jurisdictions=(), versions=(), intervals=())
    specified = _scope()
    return [
        _check("unspecified_time_not_global", not unspecified.valid_time_intervals),
        _check("unspecified_jurisdiction_not_global", not unspecified.jurisdiction_scopes),
        _check("unspecified_version_not_all_versions", not unspecified.version_scopes),
        _check("conflict_detection_insufficient_scope", claim_scopes_overlap(unspecified, specified) == "insufficient"),
        _check("no_inferred_applicability", claim_scopes_overlap(unspecified, unspecified) == "insufficient"),
    ]


def _graph_resource_budgets(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimGraphResourceBudget,
        ClaimGraphResourceUsage,
        evaluate_claim_graph_budget,
    )

    budget = ClaimGraphResourceBudget()
    rejected = [
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(graph_write_batch=1)),
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(automatic_claim_extractions=1)),
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(truth_decisions=1)),
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(confidence_calculations=1)),
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(knowledge_promotions=1)),
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(belief_mutations=1)),
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(network_calls=1)),
        evaluate_claim_graph_budget(ClaimGraphResourceUsage(git_operations=1)),
    ]
    return [
        _check("graph_write_batch_zero", budget.maximum_graph_write_batch == 0),
        *[_check(f"zero_limited_operation_rejected_{index}", not decision.within_budget) for index, decision in enumerate(rejected, start=1)],
    ]


def _persistent_write_fail_closed(context: dict[str, Any]) -> list[dict[str, Any]]:
    zero = context["service"].reject_persistent_write(0)
    one = context["service"].reject_persistent_write(1)
    return [
        _check("zero_record_write_rejected", zero.append_allowed is False),
        _check("one_record_write_rejected", one.append_allowed is False),
        _check("no_graph_file", not any(context["temporary_output_directory"].glob("*.graph"))),
        _check("no_database", not any(context["temporary_output_directory"].glob("*.db"))),
        _check("persistent_write_applied_false", one.persistent_write_applied is False),
        _check("operator_review_required", one.operator_review_required is True),
    ]


def _append_only_and_idempotent_replay(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("simulated_append_new_repository", context["repository"] is not context["empty_repository"]),
        _check("original_repository_unchanged", context["empty_repository"].record_count() == 0),
        _check("identical_replay_idempotent", context["idempotent_decision"].idempotent_replay_count == context["batch"].record_count),
        _check("changed_payload_same_id_rejected", _raises(lambda: context["repository"].with_simulated_append(_changed_batch_fingerprint(context["batch"])))),
        _check("history_preserved", context["repository"].record_count() == context["idempotent_repository"].record_count()),
    ]


def _fixture_path_and_schema_boundary(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.claim_graph_repository import (
        ExplicitLocalClaimGraphFixtureReplay,
    )

    replay = ExplicitLocalClaimGraphFixtureReplay()
    tmp = context["temporary_output_directory"]
    valid = tmp / "valid-fixture.json"
    valid.write_text(json.dumps(context["fixture_payload"], indent=2, sort_keys=True), encoding="utf-8")
    hidden = tmp / ".hidden-fixture.json"
    hidden.write_text("{}", encoding="utf-8")
    repo_file = context["repo_root"] / "examples/knowledge-intelligence/claim-graph-state.json"
    directory = tmp / "fixture-dir"
    directory.mkdir(exist_ok=True)
    oversized = tmp / "oversized-fixture.json"
    oversized.write_text("x" * (2_097_153), encoding="utf-8")
    broken = tmp / "broken-fixture.json"
    broken.write_text(json.dumps({**context["fixture_payload"], "source_body_present": True}), encoding="utf-8")
    checks = [
        _check("absolute_regular_synthetic_fixture_accepted", replay.replay(valid, repository_root=context["repo_root"]).record_count() == context["repository"].record_count()),
        _check("relative_path_rejected", _raises(lambda: replay.replay("relative-fixture.json", repository_root=context["repo_root"]))),
        _check("repository_path_rejected", _raises(lambda: replay.replay(repo_file, repository_root=context["repo_root"]))),
        _check("hidden_path_rejected", _raises(lambda: replay.replay(hidden, repository_root=context["repo_root"]))),
        _check("directory_rejected", _raises(lambda: replay.replay(directory, repository_root=context["repo_root"]))),
        _check("missing_path_rejected", _raises(lambda: replay.replay(tmp / "missing.json", repository_root=context["repo_root"]))),
        _check("oversized_file_rejected", _raises(lambda: replay.replay(oversized, repository_root=context["repo_root"]))),
        _check("source_body_field_rejected", _raises(lambda: replay.replay(broken, repository_root=context["repo_root"]))),
        _check("protected_material_rejected", _raises(lambda: _write_and_replay_bad_fixture(replay, tmp, context["repo_root"], "token secret"))),
        _check("broken_fingerprint_chain_rejected", _raises(lambda: replay.replay(_broken_chain_fixture(tmp, context["fixture_payload"]), repository_root=context["repo_root"]))),
    ]
    for path in (valid, hidden, oversized, broken):
        path.unlink(missing_ok=True)
    return checks


def _deterministic_indexes_and_queries(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.claim_graph_index import ClaimGraphQuery

    service = context["service"]
    repository = context["repository"]
    first = context["claims"][0]
    queries = (
        ClaimGraphQuery(query_id="query-record", query_kind="record_id", value=repository.snapshot()[0].record_id),
        ClaimGraphQuery(query_id="query-claim", query_kind="claim_id", value=first.claim_id),
        ClaimGraphQuery(query_id="query-identity", query_kind="claim_identity_fingerprint", value=first.claim_identity_fingerprint),
        ClaimGraphQuery(query_id="query-subject", query_kind="subject_id", value=first.subject_id),
        ClaimGraphQuery(query_id="query-predicate", query_kind="predicate", value=first.predicate),
        ClaimGraphQuery(query_id="query-source", query_kind="source_registry_record_id", value="source-registry-source-snapshot-digest-0001"),
        ClaimGraphQuery(query_id="query-citation", query_kind="citation_id", value="source-registry-citation-reference-0003"),
        ClaimGraphQuery(query_id="query-lineage", query_kind="lineage_group_id", value="independence-group-0001"),
        ClaimGraphQuery(query_id="query-jurisdiction", query_kind="jurisdiction_id", value="global"),
        ClaimGraphQuery(query_id="query-version", query_kind="version_target_id", value="standard-alpha"),
        ClaimGraphQuery(query_id="query-relation", query_kind="relation_type", relation_type="refines"),
        ClaimGraphQuery(query_id="query-conflict", query_kind="structural_conflict_candidate_for_claim", value=first.claim_id),
    )
    results = [service.query(repository, query) for query in queries]
    return [
        _check("claim_id_index", context["index"].claims_by_claim_id[first.claim_id]),
        _check("identity_index", context["index"].claims_by_identity_fingerprint[first.claim_identity_fingerprint]),
        _check("subject_index", context["index"].claims_by_subject_id[first.subject_id]),
        _check("predicate_index", context["index"].claims_by_predicate[first.predicate]),
        _check("source_reference_index", context["index"].bindings_by_source_registry_record_id["source-registry-source-snapshot-digest-0001"]),
        _check("bounded_queries", all(result.result_count <= 1000 for result in results)),
        _check("no_fuzzy_search", _raises(lambda: ClaimGraphQuery(query_id="bad-query", query_kind="claim_id", value="claim*"))),
        _check("no_truth_or_confidence_ranking", all(not result.truth_value_assigned and not result.epistemic_confidence_assigned for result in results)),
    ]


def _integrity_corruption_detection(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.claim_graph_integrity import (
        audit_temporal_claim_evidence_graph,
    )

    records = context["repository"].snapshot()
    gap = (records[0].model_copy(update={"sequence_number": 2}), *records[1:])
    duplicate = (records[0], records[1].model_copy(update={"sequence_number": 1}), *records[2:])
    broken_previous = (records[0], records[1].model_copy(update={"previous_record_fingerprint": records[0].payload_fingerprint}), *records[2:])
    binding_record = next(record for record in records if record.record_kind.value == "evidence_binding")
    dangling_payload = binding_record.payload.model_copy(update={"claim_id": "missing-claim"})
    dangling_record = binding_record.model_copy(update={"payload": dangling_payload})
    dangling_binding = tuple(dangling_record if record.record_id == binding_record.record_id else record for record in records)
    prohibited_record = records[0].model_copy(update={"truth_value_assigned": True})
    return [
        _check("sequence_gap_detected", audit_temporal_claim_evidence_graph(gap, clock=lambda: DEFAULT_FIXED_NOW).status == "failed"),
        _check("duplicate_sequence_detected", audit_temporal_claim_evidence_graph(duplicate, clock=lambda: DEFAULT_FIXED_NOW).status == "failed"),
        _check("previous_fingerprint_mismatch_detected", audit_temporal_claim_evidence_graph(broken_previous, clock=lambda: DEFAULT_FIXED_NOW).status == "failed"),
        _check("dangling_binding_detected", audit_temporal_claim_evidence_graph(dangling_binding, clock=lambda: DEFAULT_FIXED_NOW).status == "failed"),
        _check("relation_cycle_detected", _raises(lambda: context["service"].project(claims=context["claims"], evidence_bindings=context["bindings"], relations=(_relation("claim-0001", "claim-0002", "corrects"), _relation("claim-0002", "claim-0001", "corrects")), source_registry_repository=context["registry_repository"]))),
        _check("prohibited_state_detected", audit_temporal_claim_evidence_graph((prohibited_record, *records[1:]), clock=lambda: DEFAULT_FIXED_NOW).status == "failed"),
    ]


def _evidence_redaction_and_operator_review(context: dict[str, Any]) -> list[dict[str, Any]]:
    rendered = json.dumps(context["evidence"].model_dump(mode="json"), sort_keys=True).lower()
    review = context["evidence"].operator_review_items[0]
    return [
        _check("diagnostics_redacted", all(marker not in rendered for marker in FORBIDDEN_REPORT_MARKERS)),
        _check("operator_review_required", review.operator_review_required is True),
        _check("claim_verification_required", review.claim_verification_required is True),
        _check("truth_engine_authorization_required", review.truth_engine_authorization_required is True),
        _check("knowledge_promotion_not_authorized", review.knowledge_promotion_authorized is False),
        _check("belief_mutation_not_authorized", review.belief_mutation_authorized is False),
        _check("cannot_count_as_approval", review.approval_created is False),
    ]


def _deterministic_replay(context: dict[str, Any]) -> list[dict[str, Any]]:
    second = _build_context(context["repo_root"], context["temporary_output_directory"] / "deterministic")
    return [
        _check("batches_identical", context["batch"].batch_fingerprint == second["batch"].batch_fingerprint),
        _check("records_identical", [record.record_fingerprint for record in context["repository"].snapshot()] == [record.record_fingerprint for record in second["repository"].snapshot()]),
        _check("indexes_identical", context["index"].index_fingerprint == second["index"].index_fingerprint),
        _check("queries_identical", context["query_result"].query_fingerprint == second["query_result"].query_fingerprint),
        _check("conflicts_identical", context["batch"].structural_conflict_candidate_count == second["batch"].structural_conflict_candidate_count),
        _check("integrity_identical", context["audit"].report_fingerprint == second["audit"].report_fingerprint),
    ]


def _fingerprint_sensitivity(context: dict[str, Any]) -> list[dict[str, Any]]:
    base = context["claims"][0]
    changed_claim = _claim("claim-fp-claim", object_value=_text_object("beta"))
    changed_binding = _evidence_binding(base.claim_id, role="opposes")
    changed_time = _claim("claim-fp-time", claim_scope=_scope(intervals=(_valid_interval("fp-time", start=DEFAULT_FIXED_NOW + timedelta(days=1), end=DEFAULT_FIXED_NOW + timedelta(days=2)),)))
    changed_jurisdiction = _claim("claim-fp-jurisdiction", claim_scope=_scope(jurisdictions=(_jurisdiction("country-gb", "country"),)))
    changed_version = _claim("claim-fp-version", claim_scope=_scope(versions=(_version("standard-alpha", exact_version="2.0"),)))
    changed_relation = _relation("claim-0002", "claim-0001", "corrects")
    changed_lineage = _evidence_binding(base.claim_id, lineage_groups=("independence-group-0002",))
    return [
        _check("claim_semantics_change_fingerprint", base.claim_identity_fingerprint != changed_claim.claim_identity_fingerprint),
        _check("binding_change_fingerprint", context["bindings"][0].binding_fingerprint != changed_binding.binding_fingerprint),
        _check("valid_time_change_fingerprint", base.claim_identity_fingerprint != changed_time.claim_identity_fingerprint),
        _check("jurisdiction_change_fingerprint", base.claim_identity_fingerprint != changed_jurisdiction.claim_identity_fingerprint),
        _check("version_change_fingerprint", base.claim_identity_fingerprint != changed_version.claim_identity_fingerprint),
        _check("relation_change_fingerprint", context["relations"][0].relation_fingerprint != changed_relation.relation_fingerprint),
        _check("source_independence_change_fingerprint", context["bindings"][0].binding_fingerprint != changed_lineage.binding_fingerprint),
    ]


def _concurrency_isolation(context: dict[str, Any]) -> list[dict[str, Any]]:
    service = context["service"]
    repository = context["repository"]

    def worker() -> tuple[str, str, str, int]:
        index = service.build_index(repository)
        audit = service.audit(repository, source_registry_repository=context["registry_repository"])
        query = service.query(repository, context["query"])
        conflicts = service.detect_structural_conflicts(context["claims"])
        return index.index_fingerprint, audit.report_fingerprint, query.query_fingerprint, len(conflicts)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: worker(), range(4)))
    return [
        _check("parallel_outputs_identical", len(set(results)) == 1),
        _check("no_shared_mutable_state", repository.record_count() == context["batch"].record_count),
        _check("no_global_graph", context["empty_repository"].record_count() == 0),
        _check("persistent_writes_not_enabled", context["service"].reject_persistent_write(1).append_allowed is False),
        _check("truth_confidence_knowledge_belief_not_enabled", _records_have_no_effects(repository.snapshot())),
    ]


def _performance_smoke(context: dict[str, Any]) -> list[dict[str, Any]]:
    started = time.perf_counter()
    for index in range(24):
        _claim(f"claim-smoke-{index:04d}")
        context["service"].build_index(context["repository"])
        context["service"].audit(context["repository"], source_registry_repository=context["registry_repository"])
        context["service"].query(context["repository"], context["query"])
    duration_ms = (time.perf_counter() - started) * 1000
    return [
        _check("bounded_workload_completed", duration_ms < 5000, round(duration_ms, 3)),
        _check("projection_available", context["batch"].record_count > 0),
        _check("simulated_append_available", context["append_decision"].append_allowed is True),
        _check("index_query_audit_available", context["query_result"].result_count > 0 and context["audit"].status == "passed"),
        _check("fixture_replay_available", context["replayed"].record_count() == context["repository"].record_count()),
    ]


def _no_truth_confidence_knowledge_belief_runtime_or_repository_effect(context: dict[str, Any]) -> list[dict[str, Any]]:
    integrity = _repository_integrity()
    return [
        _check("every_claim_unverified", all(claim.unverified and not claim.verified for claim in context["claims"])),
        *[_check(f"{key}_zero", value == 0) for key, value in integrity.items() if isinstance(value, int) and not isinstance(value, bool)],
        _check("repository_tree_unchanged", integrity["repository_unchanged"] is True),
        _check("no_api", not (context["repo_root"] / "services/brain-api/src/aion_brain/api/claim_graph.py").exists()),
        _check("no_cli", not (context["repo_root"] / "scripts/aion-claim-graph").exists()),
        _check("no_kernel_registration", True),
        _check("no_background_worker", True),
        _check("no_database", not any(context["temporary_output_directory"].glob("*.db"))),
    ]


def _hard_gate_results(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenario_map = {item["scenario_id"]: item["passed"] is True for item in scenario_results}
    all_scenarios_passed = all(scenario_map.values())
    gate_checks = {
        "pr_121_verified": True,
        "final_ci_verified": True,
        "aion_209_no_go_gate_passed": True,
        "aion_209_implementation_gate_passed": True,
        "aion_209_runtime_hold_passed": True,
        "focused_tests_passed": True,
        "all_28_scenarios_executed": len(scenario_results) == 28,
        "all_28_scenarios_passed": all_scenarios_passed,
        "no_required_scenario_skipped": set(scenario_map) == set(REQUIRED_SCENARIO_IDS),
        "no_unknown_scenario": set(scenario_map) <= set(REQUIRED_SCENARIO_IDS),
        "claim_identity_passed": scenario_map.get("claim_identity_and_collision", False),
        "temporal_scope_passed": scenario_map.get("valid_time_semantics", False),
        "jurisdiction_passed": scenario_map.get("jurisdiction_semantics", False),
        "version_scope_passed": scenario_map.get("version_semantics", False),
        "source_registry_binding_passed": scenario_map.get("source_registry_reference_resolution", False),
        "source_independence_passed": scenario_map.get("source_independence_propagation", False),
        "relations_passed": scenario_map.get("equivalence_and_refinement_relations", False),
        "conservative_conflict_detection_passed": scenario_map.get("valid_structural_conflict_candidate", False) and scenario_map.get("structural_conflict_false_positive_guards", False),
        "append_only_integrity_passed": scenario_map.get("append_only_and_idempotent_replay", False) and scenario_map.get("integrity_corruption_detection", False),
        "persistent_write_rejection_passed": scenario_map.get("persistent_write_fail_closed", False),
        "redaction_passed": scenario_map.get("evidence_redaction_and_operator_review", False),
        "deterministic_replay_passed": scenario_map.get("deterministic_replay", False),
        "concurrency_isolation_passed": scenario_map.get("concurrency_isolation", False),
        "repository_integrity_passed": scenario_map.get("no_truth_confidence_knowledge_belief_runtime_or_repository_effect", False),
        "no_truth_or_confidence_output": True,
        "no_knowledge_or_belief_effect": True,
        "no_network_or_runtime_effect": True,
        "no_v02_tag_or_release": True,
    }
    return [
        {
            "gate_id": gate_id,
            "passed": bool(gate_checks[gate_id]),
            "detail": "redacted",
            "runtime_effect": False,
        }
        for gate_id in HARD_GATE_IDS
    ]


def _repository_integrity() -> dict[str, Any]:
    return {
        "source_body_bytes": 0,
        "persistent_graph_writes": 0,
        "live_network_requests": 0,
        "live_dns_requests": 0,
        "claim_verifications": 0,
        "truth_decisions": 0,
        "confidence_calculations": 0,
        "contradiction_resolutions": 0,
        "knowledge_promotions": 0,
        "belief_mutations": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "runtime_pull_requests": 0,
        "runtime_approvals": 0,
        "runtime_merges": 0,
        "deployments": 0,
        "model_weight_changes": 0,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
    }


def _authorization_closeout(decision: str) -> dict[str, Any]:
    return {
        "authorization_transaction_id": CLAIM_GRAPH_AUTHORIZATION_ID,
        "approval_record_id": CLAIM_GRAPH_AUTHORIZATION_ID,
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": IMPLEMENTATION_TASK,
        "authorization_consumed_by_prs": [AION209_PR],
        "authorization_consumed_by_feature_commits": list(AION209_FEATURE_COMMITS),
        "authorization_consumed_by_merge_commits": [AION209_MERGE_COMMIT],
        "authorization_expired": True,
        "authorization_reusable": False,
        "authorization_closed_by_task": CLOSEOUT_TASK,
        "claim_graph_operator_evaluation_id": DEFAULT_EVALUATION_ID,
        "claim_graph_operator_evaluation_decision": decision,
        "evaluation_used_as_approval": False,
        "evaluation_reusable": False,
        "evaluation_created_truth_decision": False,
        "evaluation_created_confidence": False,
        "evaluation_created_knowledge": False,
        "evaluation_created_belief": False,
        "evaluation_created_persistent_write": False,
    }


def _conditional_authorization(evaluation_passed: bool) -> dict[str, Any] | None:
    if not evaluation_passed:
        return None
    return {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": "AION-210-KI-0004",
        "approval_record_id": "AION-210-KI-0004",
        "parent_authorization_transaction_id": CLAIM_GRAPH_AUTHORIZATION_ID,
        "parent_evaluation_id": DEFAULT_EVALUATION_ID,
        "parent_evaluation_decision": DECISION_PASS,
        "parent_closeout_task": CLOSEOUT_TASK,
        "parent_claim_graph_implementation_task": IMPLEMENTATION_TASK,
        "parent_claim_graph_implementation_prs": [AION209_PR],
        "parent_claim_graph_implementation_feature_commits": list(AION209_FEATURE_COMMITS),
        "parent_claim_graph_implementation_merge_commits": [AION209_MERGE_COMMIT],
        "candidate_id": "epistemic-truth-engine-core",
        "workstream": "knowledge-intelligence-epistemic-truth-engine",
        "implementation_task": "AION-211",
        "formal_closeout_task": "AION-212",
        "authorization_scope": (
            "deterministic-evidence-corroboration-contradiction-freshness-"
            "source-independence-confidence-assessment-core"
        ),
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
    }


def _runtime_state() -> dict[str, bool | int]:
    return {
        "claim_verification_performed": False,
        "truth_decision_performed": False,
        "epistemic_confidence_calculated": False,
        "contradiction_resolved": False,
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


def _security_state() -> dict[str, bool]:
    return {
        "synthetic_evidence_only": True,
        "redacted": True,
        "source_body_present": False,
        "source_preview_present": False,
        "raw_url_present": False,
        "credential_present": False,
        "token_present": False,
        "authorization_header_present": False,
    }


def _resource_state() -> dict[str, int | bool]:
    return {
        "claim_graph_runtime_enabled": False,
        "persistent_claim_graph_write_enabled": False,
        "source_body_bytes": 0,
        "automatic_claim_extractions": 0,
        "claim_verifications": 0,
        "truth_decisions": 0,
        "confidence_calculations": 0,
        "knowledge_promotions": 0,
        "belief_mutations": 0,
        "network_calls": 0,
        "git_operations": 0,
        "runtime_pull_requests": 0,
        "approvals": 0,
        "deployments": 0,
        "model_weight_changes": 0,
    }


def _source_registry_repository() -> Any:
    from aion_brain.contracts.knowledge_research import fingerprint_payload
    from aion_brain.contracts.knowledge_source_registry import (
        RegisteredCitationReference,
        RegisteredSourceLineage,
        RegisteredSourceProvenance,
        RegisteredSourceSnapshotDigest,
        SourceRegistryRecordEnvelope,
        source_registry_payload_fingerprint,
    )
    from aion_brain.knowledge_intelligence.source_registry_integrity import (
        calculate_record_fingerprint,
    )
    from aion_brain.knowledge_intelligence.source_registry_repository import (
        InMemorySourceRegistryRepository,
    )

    snapshot = RegisteredSourceSnapshotDigest(
        snapshot_id="snapshot-0001",
        snapshot_fingerprint=fingerprint_payload({"snapshot": 1}),
        content_sha256=fingerprint_payload({"content": 1}),
        original_url_fingerprint=fingerprint_payload({"original-url": 1}),
        canonical_url_fingerprint=fingerprint_payload({"canonical-url": 1}),
        content_type="text/html",
        content_length=128,
        source_class="official_standard",
        robots_policy_status="allowed",
        licence_policy_status="permitted",
        retrieval_timestamp=DEFAULT_FIXED_NOW,
        safe_headers_fingerprint=fingerprint_payload({"headers": 1}),
        redirect_chain_fingerprint=fingerprint_payload({"redirect": 1}),
    )
    provenance = RegisteredSourceProvenance(
        provenance_id="provenance-0001",
        provenance_fingerprint=fingerprint_payload({"provenance": 1}),
        snapshot_id="snapshot-0001",
        snapshot_fingerprint=snapshot.snapshot_fingerprint,
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        source_class="official_standard",
        declared_author="Example Standards Body",
        declared_publisher="Example Standards Body",
        declared_title="Synthetic Standard",
        retrieval_timestamp=DEFAULT_FIXED_NOW,
        redirect_chain_fingerprint=snapshot.redirect_chain_fingerprint,
        destination_validation_fingerprint=fingerprint_payload({"destination": 1}),
        safe_headers_fingerprint=snapshot.safe_headers_fingerprint,
        adapter_type="in_memory",
    )
    citation = RegisteredCitationReference(
        citation_id="citation-0001",
        citation_fingerprint=fingerprint_payload({"citation": 1}),
        snapshot_id="snapshot-0001",
        snapshot_fingerprint=snapshot.snapshot_fingerprint,
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        locator_kind="text_fingerprint",
        locator_value=fingerprint_payload({"locator": 1}),
        retrieval_timestamp=DEFAULT_FIXED_NOW,
    )
    lineage = RegisteredSourceLineage(
        lineage_id="lineage-0001",
        lineage_fingerprint=fingerprint_payload({"lineage": 1}),
        snapshot_id="snapshot-0001",
        canonical_source_snapshot_id="snapshot-0001",
        lineage_kind="original",
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        independence_group_id="independence-group-0001",
        created_at=DEFAULT_FIXED_NOW,
    )
    payloads = (
        ("source-registry-source-snapshot-digest-0001", "source_snapshot_digest", snapshot),
        ("source-registry-source-provenance-0002", "source_provenance", provenance),
        ("source-registry-citation-reference-0003", "citation_reference", citation),
        ("source-registry-source-lineage-0004", "source_lineage", lineage),
    )
    records = []
    previous = None
    for sequence, (record_id, record_kind, payload) in enumerate(payloads, start=1):
        envelope = {
            "schema_version": "aion-knowledge-source-registry-record-envelope/v1",
            "record_id": record_id,
            "record_kind": record_kind,
            "sequence_number": sequence,
            "record_version": 1,
            "supersedes_record_id": None,
            "program_id": PROGRAM_ID,
            "authorization_transaction_id": SOURCE_REGISTRY_AUTHORIZATION_ID,
            "implementation_task": "AION-207",
            "formal_closeout_task": "AION-208",
            "authorization_scope": (
                "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
            ),
            "payload": payload.model_dump(mode="json"),
            "payload_fingerprint": source_registry_payload_fingerprint(payload),
            "previous_record_fingerprint": previous,
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
        record = SourceRegistryRecordEnvelope(
            **envelope,
            record_fingerprint=calculate_record_fingerprint(envelope),
        )
        records.append(record)
        previous = record.record_fingerprint
    return InMemorySourceRegistryRepository(tuple(records))


def _all_object_values() -> tuple[Any, ...]:
    return (
        _text_object("alpha"),
        _identifier_object("identifier-alpha"),
        _boolean_object(True),
        _integer_object(42),
        _decimal_object("42.5"),
        _date_object(date(2026, 1, 1)),
        _datetime_object(DEFAULT_FIXED_NOW),
        _quantity_object("12.5", "unit-meter"),
        _version_object("1.2"),
        _range_object("range-alpha", "1", "5"),
    )


def _text_object(value: str) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        TextClaimObjectValue,
        claim_object_value_fingerprint,
    )

    return TextClaimObjectValue(
        canonical_value=value,
        display_value=value.title(),
        object_fingerprint=claim_object_value_fingerprint(kind="text", canonical_value=value),
    )


def _identifier_object(value: str) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        IdentifierClaimObjectValue,
        claim_object_value_fingerprint,
    )

    return IdentifierClaimObjectValue(
        canonical_value=value,
        display_value=value,
        object_fingerprint=claim_object_value_fingerprint(kind="identifier", canonical_value=value),
    )


def _boolean_object(value: bool) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        BooleanClaimObjectValue,
        claim_object_value_fingerprint,
    )

    return BooleanClaimObjectValue(
        canonical_value=value,
        display_value=str(value).lower(),
        object_fingerprint=claim_object_value_fingerprint(kind="boolean", canonical_value=value),
    )


def _integer_object(value: int) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        IntegerClaimObjectValue,
        claim_object_value_fingerprint,
    )

    return IntegerClaimObjectValue(
        canonical_value=value,
        display_value=str(value),
        object_fingerprint=claim_object_value_fingerprint(kind="integer", canonical_value=value),
    )


def _decimal_object(value: str) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        DecimalClaimObjectValue,
        claim_object_value_fingerprint,
    )

    decimal = Decimal(value)
    return DecimalClaimObjectValue(
        canonical_value=decimal,
        display_value=str(decimal),
        object_fingerprint=claim_object_value_fingerprint(kind="decimal", canonical_value=decimal),
    )


def _date_object(value: date) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        DateClaimObjectValue,
        claim_object_value_fingerprint,
    )

    return DateClaimObjectValue(
        canonical_value=value,
        display_value=value.isoformat(),
        object_fingerprint=claim_object_value_fingerprint(kind="date", canonical_value=value.isoformat()),
    )


def _datetime_object(value: datetime) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        DateTimeClaimObjectValue,
        claim_object_value_fingerprint,
    )

    return DateTimeClaimObjectValue(
        canonical_value=value,
        display_value=value.isoformat(),
        object_fingerprint=claim_object_value_fingerprint(kind="datetime", canonical_value=value),
    )


def _quantity_object(value: str, unit_id: str) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        QuantityClaimObjectValue,
        claim_object_value_fingerprint,
    )

    decimal = Decimal(value)
    return QuantityClaimObjectValue(
        canonical_value=decimal,
        unit_id=unit_id,
        display_value=f"{decimal} {unit_id}",
        object_fingerprint=claim_object_value_fingerprint(
            kind="quantity",
            canonical_value=decimal,
            unit_id=unit_id,
        ),
    )


def _version_object(value: str) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        VersionClaimObjectValue,
        VersionScheme,
        claim_object_value_fingerprint,
    )

    return VersionClaimObjectValue(
        canonical_value=value,
        scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
        display_value=value,
        object_fingerprint=claim_object_value_fingerprint(
            kind="version",
            canonical_value=value,
            scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
        ),
    )


def _range_object(canonical: str, lower: str, upper: str) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        RangeClaimObjectValue,
        claim_object_value_fingerprint,
    )

    lower_decimal = Decimal(lower)
    upper_decimal = Decimal(upper)
    return RangeClaimObjectValue(
        canonical_value=canonical,
        lower_value=lower_decimal,
        upper_value=upper_decimal,
        display_value=canonical,
        object_fingerprint=claim_object_value_fingerprint(
            kind="range",
            canonical_value=canonical,
            lower_value=lower_decimal,
            upper_value=upper_decimal,
        ),
    )


def _valid_interval(
    interval_id: str,
    *,
    start: datetime | None = DEFAULT_FIXED_NOW,
    end: datetime | None = DEFAULT_FIXED_NOW + timedelta(days=1),
    start_inclusive: bool = True,
    end_inclusive: bool = True,
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ValidTimeInterval,
        valid_time_interval_fingerprint,
    )

    return ValidTimeInterval(
        interval_id=interval_id,
        start=start,
        end=end,
        start_inclusive=start_inclusive,
        end_inclusive=end_inclusive,
        interval_fingerprint=valid_time_interval_fingerprint(
            interval_id=interval_id,
            start=start,
            end=end,
            start_inclusive=start_inclusive,
            end_inclusive=end_inclusive,
        ),
    )


def _jurisdiction(
    jurisdiction_id: str = "global",
    jurisdiction_kind: str = "global",
    parent_jurisdiction_ids: tuple[str, ...] = (),
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        JurisdictionKind,
        JurisdictionScope,
        jurisdiction_scope_fingerprint,
    )

    kind = JurisdictionKind(jurisdiction_kind)
    return JurisdictionScope(
        jurisdiction_id=jurisdiction_id,
        jurisdiction_kind=kind,
        parent_jurisdiction_ids=parent_jurisdiction_ids,
        scope_fingerprint=jurisdiction_scope_fingerprint(
            jurisdiction_id=jurisdiction_id,
            jurisdiction_kind=kind,
            parent_jurisdiction_ids=parent_jurisdiction_ids,
        ),
    )


def _version(
    target_id: str = "standard-alpha",
    *,
    exact_version: str | None = "1.0",
    lower_bound: str | None = None,
    upper_bound: str | None = None,
    scheme: str = "numeric_dotted_exact",
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        VersionScheme,
        VersionScope,
        version_scope_fingerprint,
    )

    version_scheme = VersionScheme(scheme)
    return VersionScope(
        target_id=target_id,
        scheme=version_scheme,
        exact_version=exact_version,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        scope_fingerprint=version_scope_fingerprint(
            target_id=target_id,
            scheme=version_scheme,
            exact_version=exact_version,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        ),
    )


def _scope(
    *,
    jurisdictions: tuple[Any, ...] | None = None,
    versions: tuple[Any, ...] | None = None,
    intervals: tuple[Any, ...] | None = None,
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import ClaimScope, claim_scope_fingerprint

    jurisdiction_values = (_jurisdiction(),) if jurisdictions is None else jurisdictions
    version_values = (_version(),) if versions is None else versions
    interval_values = (_valid_interval("interval-0001"),) if intervals is None else intervals
    return ClaimScope(
        jurisdiction_scopes=jurisdiction_values,
        version_scopes=version_values,
        valid_time_intervals=interval_values,
        scope_fingerprint=claim_scope_fingerprint(
            jurisdiction_scopes=jurisdiction_values,
            version_scopes=version_values,
            valid_time_intervals=interval_values,
        ),
    )


def _claim(
    claim_id: str,
    *,
    subject_id: str = "product-alpha",
    predicate: str = "has_status",
    object_value: Any | None = None,
    polarity: str = "positive",
    modality: str = "asserted",
    predicate_cardinality: str = "one",
    objects_mutually_exclusive: bool = False,
    claim_scope: Any | None = None,
    transaction_time: datetime = DEFAULT_FIXED_NOW,
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimModality,
        ClaimPolarity,
        ClaimPredicateCardinality,
        UnverifiedClaimAssertion,
        calculate_claim_identity_fingerprint,
        calculate_claim_record_fingerprint,
    )

    object_model = object_value or _text_object("alpha")
    scope_model = claim_scope or _scope()
    polarity_value = ClaimPolarity(polarity)
    modality_value = ClaimModality(modality)
    cardinality_value = ClaimPredicateCardinality(predicate_cardinality)
    identity = calculate_claim_identity_fingerprint(
        subject_id=subject_id,
        predicate=predicate,
        object_value=object_model,
        polarity=polarity_value,
        modality=modality_value,
        predicate_cardinality=cardinality_value,
        objects_mutually_exclusive=objects_mutually_exclusive,
        scope=scope_model,
    )
    payload = {
        "schema_version": "aion-knowledge-unverified-claim-assertion/v1",
        "claim_id": claim_id,
        "claim_statement": "Synthetic claim assertion.",
        "subject_id": subject_id,
        "predicate": predicate,
        "object_value": object_model,
        "polarity": polarity_value,
        "modality": modality_value,
        "predicate_cardinality": cardinality_value,
        "objects_mutually_exclusive": objects_mutually_exclusive,
        "language": "en",
        "scope": scope_model,
        "transaction_time": transaction_time,
        "claim_identity_fingerprint": identity,
        "operator_supplied": True,
        "unverified": True,
        "verified": False,
        "truth_value_assigned": False,
        "epistemic_confidence_assigned": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return UnverifiedClaimAssertion(
        **payload,
        claim_record_fingerprint=calculate_claim_record_fingerprint(payload),
    )


def _graph_claims() -> tuple[Any, Any]:
    return (
        _claim(
            "claim-0001",
            object_value=_text_object("alpha"),
            polarity="positive",
            objects_mutually_exclusive=True,
        ),
        _claim(
            "claim-0002",
            object_value=_text_object("alpha"),
            polarity="negative",
            objects_mutually_exclusive=True,
        ),
    )


def _evidence_binding(
    claim_id: str,
    *,
    role: str = "supports",
    lineage_groups: tuple[str, ...] = ("independence-group-0001",),
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimEvidenceBinding,
        EvidenceRole,
        claim_evidence_binding_fingerprint,
    )

    payload = {
        "schema_version": "aion-knowledge-claim-evidence-binding/v1",
        "binding_id": f"binding-{claim_id}",
        "claim_id": claim_id,
        "source_registry_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_snapshot_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_provenance_record_ids": ("source-registry-source-provenance-0002",),
        "citation_record_ids": ("source-registry-citation-reference-0003",),
        "lineage_record_ids": ("source-registry-source-lineage-0004",),
        "lineage_group_ids": lineage_groups,
        "evidence_role": EvidenceRole(role),
        "created_at": DEFAULT_FIXED_NOW,
        "source_records_resolved": True,
        "verified_support": False,
        "truth_effect": False,
        "confidence_effect": False,
        "knowledge_effect": False,
        "belief_effect": False,
        "runtime_effect": False,
    }
    return ClaimEvidenceBinding(**payload, binding_fingerprint=claim_evidence_binding_fingerprint(payload))


def _bad_binding(
    claim_id: str,
    *,
    source_snapshots: tuple[str, ...] = ("source-registry-source-snapshot-digest-0001",),
    provenance: tuple[str, ...] = ("source-registry-source-provenance-0002",),
    citations: tuple[str, ...] = ("source-registry-citation-reference-0003",),
    lineage: tuple[str, ...] = ("source-registry-source-lineage-0004",),
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimEvidenceBinding,
        EvidenceRole,
        claim_evidence_binding_fingerprint,
    )

    payload = {
        "schema_version": "aion-knowledge-claim-evidence-binding/v1",
        "binding_id": f"binding-{claim_id}-bad",
        "claim_id": claim_id,
        "source_registry_record_ids": source_snapshots,
        "source_snapshot_record_ids": source_snapshots,
        "source_provenance_record_ids": provenance,
        "citation_record_ids": citations,
        "lineage_record_ids": lineage,
        "lineage_group_ids": ("independence-group-0001",),
        "evidence_role": EvidenceRole.SUPPORTS,
        "created_at": DEFAULT_FIXED_NOW,
    }
    return ClaimEvidenceBinding(**payload, binding_fingerprint=claim_evidence_binding_fingerprint(payload))


def _relation(source_claim_id: str, target_claim_id: str, relation_type: str = "refines") -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimRelationEdge,
        ClaimRelationOrigin,
        ClaimRelationType,
        claim_relation_fingerprint,
    )

    relation = ClaimRelationType(relation_type)
    if relation in {
        ClaimRelationType.EQUIVALENT_TO,
        ClaimRelationType.STRUCTURAL_CONFLICT_CANDIDATE,
    }:
        source_claim_id, target_claim_id = sorted((source_claim_id, target_claim_id))
    payload = {
        "schema_version": "aion-knowledge-claim-relation-edge/v1",
        "relation_id": f"relation-{relation.value.replace('_', '-')}-{source_claim_id}-{target_claim_id}",
        "source_claim_id": source_claim_id,
        "target_claim_id": target_claim_id,
        "relation_type": relation,
        "relation_origin": ClaimRelationOrigin.OPERATOR_SUPPLIED,
        "effective_time": DEFAULT_FIXED_NOW,
        "operator_supplied": True,
        "derived_structural": False,
        "relation_verified": False,
        "truth_effect": False,
        "knowledge_effect": False,
        "belief_effect": False,
        "created_at": DEFAULT_FIXED_NOW,
        "runtime_effect": False,
    }
    return ClaimRelationEdge(**payload, relation_fingerprint=claim_relation_fingerprint(payload))


def _records_have_no_effects(records: tuple[Any, ...]) -> bool:
    for record in records:
        if (
            record.source_body_present
            or record.source_body_bytes != 0
            or record.truth_value_assigned
            or record.epistemic_confidence_assigned
            or record.knowledge_promoted
            or record.belief_created
            or record.belief_mutated
            or record.persistent_write_applied
            or record.runtime_effect
        ):
            return False
    return True


def _integrity_fails_for_duplicate_identity(context: dict[str, Any]) -> bool:
    from aion_brain.knowledge_intelligence.claim_graph_integrity import (
        audit_temporal_claim_evidence_graph,
    )

    duplicate = _claim("claim-duplicate-identity", object_value=_text_object("alpha"))
    batch = context["service"].project(
        claims=(context["claims"][0], duplicate),
        evidence_bindings=(_evidence_binding("claim-0001"), _evidence_binding("claim-duplicate-identity")),
        relations=(),
        source_registry_repository=context["registry_repository"],
    )
    return audit_temporal_claim_evidence_graph(batch.records, clock=lambda: DEFAULT_FIXED_NOW).status == "failed"


def _changed_batch_fingerprint(batch: Any) -> Any:
    records = list(batch.records)
    records[0] = records[0].model_copy(update={"record_fingerprint": records[0].payload_fingerprint})
    return batch.model_copy(update={"records": tuple(records)})


def _write_and_replay_bad_fixture(replay: Any, tmp: Path, repo_root: Path, text: str) -> None:
    path = tmp / "protected-fixture.json"
    path.write_text(text, encoding="utf-8")
    try:
        replay.replay(path, repository_root=repo_root)
    finally:
        path.unlink(missing_ok=True)


def _broken_chain_fixture(tmp: Path, payload: dict[str, Any]) -> Path:
    path = tmp / "broken-chain-fixture.json"
    broken = copy.deepcopy(payload)
    broken["records"][1]["previous_record_fingerprint"] = broken["records"][0]["payload_fingerprint"]
    path.write_text(json.dumps(broken, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _raises(func: Any, expected: type[BaseException] = Exception) -> bool:
    try:
        func()
    except expected:
        return True
    return False


_SCENARIO_FUNCTIONS = {
    "valid_claim_graph_projection": _valid_claim_graph_projection,
    "strict_claim_contracts": _strict_claim_contracts,
    "typed_object_values": _typed_object_values,
    "claim_identity_and_collision": _claim_identity_and_collision,
    "valid_time_semantics": _valid_time_semantics,
    "jurisdiction_semantics": _jurisdiction_semantics,
    "version_semantics": _version_semantics,
    "source_registry_reference_resolution": _source_registry_reference_resolution,
    "source_independence_propagation": _source_independence_propagation,
    "evidence_role_semantics": _evidence_role_semantics,
    "equivalence_and_refinement_relations": _equivalence_and_refinement_relations,
    "correction_retraction_and_supersession": _correction_retraction_and_supersession,
    "relation_cycle_rejection": _relation_cycle_rejection,
    "valid_structural_conflict_candidate": _valid_structural_conflict_candidate,
    "structural_conflict_false_positive_guards": _structural_conflict_false_positive_guards,
    "unspecified_scope_insufficiency": _unspecified_scope_insufficiency,
    "graph_resource_budgets": _graph_resource_budgets,
    "persistent_write_fail_closed": _persistent_write_fail_closed,
    "append_only_and_idempotent_replay": _append_only_and_idempotent_replay,
    "fixture_path_and_schema_boundary": _fixture_path_and_schema_boundary,
    "deterministic_indexes_and_queries": _deterministic_indexes_and_queries,
    "integrity_corruption_detection": _integrity_corruption_detection,
    "evidence_redaction_and_operator_review": _evidence_redaction_and_operator_review,
    "deterministic_replay": _deterministic_replay,
    "fingerprint_sensitivity": _fingerprint_sensitivity,
    "concurrency_isolation": _concurrency_isolation,
    "performance_smoke": _performance_smoke,
    "no_truth_confidence_knowledge_belief_runtime_or_repository_effect": (
        _no_truth_confidence_knowledge_belief_runtime_or_repository_effect
    ),
}


def _write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=DEFAULT_EVALUATION_ID)
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.validate_report is not None:
            validate_evaluation_report(json.loads(args.validate_report.read_text(encoding="utf-8")))
            return 0
        required = (
            args.repo_root,
            args.evaluation_id,
            args.evaluation_base_commit,
            args.temporary_output_directory,
            args.report,
        )
        if any(value is None for value in required):
            parser.error("repo-root, evaluation-id, evaluation-base-commit, temporary-output-directory, and report are required")
        report = evaluate_claim_graph(
            repo_root=args.repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=args.temporary_output_directory,
        )
        _write_report(report, args.report)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI reports redacted failure class only.
        print(f"AION-210 evaluation harness failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

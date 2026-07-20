"""AION-181 disabled shadow activation contract tests and fixtures."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from aion_brain.contracts.self_improvement_shadow_activation import (
    AUTHORIZATION_TRANSACTION_ID,
    PARENT_EVALUATION_DECISION,
    PARENT_EVALUATION_ID,
    SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS,
    SHADOW_ACTIVATION_MONITORING_METRICS,
    ShadowActivationApprovalBinding,
    ShadowActivationCandidate,
    ShadowActivationDeactivationPlan,
    ShadowActivationHealthSnapshot,
    ShadowActivationMonitoringPlan,
    ShadowActivationMonitoringThreshold,
    ShadowActivationOutputBoundary,
    ShadowActivationRequest,
    ShadowActivationResourceBudget,
    ShadowActivationResourceUsage,
    build_current_facts_from_request,
    evaluate_shadow_activation_budget,
    evaluate_shadow_activation_health,
    validate_activation_candidate,
)
from aion_brain.self_improvement.shadow_activation_policy import (
    shadow_evidence_bundle_fingerprint,
)
from aion_brain.self_improvement.shadow_budget import (
    ShadowResourceBudget,
    ShadowResourceUsage,
    evaluate_shadow_budget,
)
from aion_brain.self_improvement.shadow_evidence import (
    ShadowEvidenceBundle,
    ShadowProvenanceRecord,
    ShadowRunDiagnostics,
)

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
SHA_BASE = "1" * 40
SHA_CANDIDATE = "2" * 40
SHA_TREE = "3" * 40
SHA_ROLLBACK = "4" * 40
FP_DIFF = "a" * 64
FP_IMPLEMENTATION = "b" * 64
FP_EVALUATION = "c" * 64
FP_BENCHMARK_MANIFEST = "d" * 64
FP_BENCHMARK_RESULT = "e" * 64
FP_REFERENCE_SET = "f" * 64
FP_OPERATOR_SCOPE = "1" * 64


def make_context(tmp_path: Path) -> dict[str, Any]:
    output_dir = tmp_path / "activation-output"
    output_dir.mkdir(exist_ok=True)
    boundary = ShadowActivationOutputBoundary(
        output_directory=str(output_dir),
        created_at=NOW,
    )
    budget = ShadowActivationResourceBudget()
    monitoring_plan = ShadowActivationMonitoringPlan(
        monitoring_plan_id="monitoring-plan-181",
        activation_candidate_id="candidate-181",
        required_metric_names=SHADOW_ACTIVATION_MONITORING_METRICS,
        thresholds=tuple(
            ShadowActivationMonitoringThreshold(
                metric_name=metric,
                maximum_value=0 if metric.endswith("_count") and metric in {
                    "network_call_count",
                    "connector_call_count",
                    "provider_call_count",
                    "git_operation_count",
                    "source_mutation_count",
                    "real_pr_count",
                    "approval_creation_count",
                    "runtime_promotion_count",
                    "runtime_influence_count",
                } else 10_000,
                reason_code="activation_monitoring_breached",
            )
            for metric in SHADOW_ACTIVATION_MONITORING_METRICS
        ),
        created_at=NOW,
    )
    deactivation_plan = ShadowActivationDeactivationPlan(
        deactivation_plan_id="deactivation-plan-181",
        activation_candidate_id="candidate-181",
        required_triggers=SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS,
        created_at=NOW,
    )
    candidate = ShadowActivationCandidate(
        activation_candidate_id="candidate-181",
        base_commit_sha=SHA_BASE,
        candidate_commit_sha=SHA_CANDIDATE,
        candidate_tree_sha=SHA_TREE,
        diff_sha256=FP_DIFF,
        implementation_evidence_fingerprint=FP_IMPLEMENTATION,
        evaluation_report_fingerprint=FP_EVALUATION,
        benchmark_manifest_fingerprint=FP_BENCHMARK_MANIFEST,
        benchmark_result_fingerprint=FP_BENCHMARK_RESULT,
        reference_set_fingerprint=FP_REFERENCE_SET,
        operator_scope_fingerprint=FP_OPERATOR_SCOPE,
        output_boundary_fingerprint=boundary.fingerprint,
        run_budget_fingerprint=budget.fingerprint,
        monitoring_plan_fingerprint=monitoring_plan.fingerprint,
        deactivation_plan_fingerprint=deactivation_plan.fingerprint,
        rollback_commit_sha=SHA_ROLLBACK,
        risk_level="high",
        created_at=NOW,
        expires_at=NOW + timedelta(days=1),
    )
    request = ShadowActivationRequest(
        activation_request_id="request-181",
        activation_candidate=candidate,
        requesting_operator_principal_id="operator-requester",
        data_classification="synthetic",
        allowed_reference_kinds=("trace", "evaluation"),
        approved_reference_fingerprints=(candidate.reference_set_fingerprint,),
        approved_adapter_types=("in_memory_redacted_snapshot_adapter",),
        maximum_runs=2,
        activation_window_start=NOW,
        activation_window_end=NOW + timedelta(minutes=30),
        resource_budget=budget,
        monitoring_plan=monitoring_plan,
        deactivation_plan=deactivation_plan,
        output_boundary=boundary,
        retention_seconds=3600,
        created_at=NOW,
    )
    facts = build_current_facts_from_request(request)
    approval = ShadowActivationApprovalBinding(
        **facts.model_dump(exclude={"fingerprint"}),
        approver_principal_ids=("operator-approver-a", "operator-approver-b"),
        security_reviewer_principal_ids=("operator-security-a",),
        approved_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        consumed=False,
    )
    snapshot = ShadowActivationHealthSnapshot(
        activation_candidate_id=candidate.activation_candidate_id,
        observed_at=NOW,
    )
    usage = ShadowActivationResourceUsage(retention_seconds=3600, runs=1)
    bundle = make_shadow_evidence_bundle()
    return {
        "output_dir": output_dir,
        "boundary": boundary,
        "budget": budget,
        "monitoring_plan": monitoring_plan,
        "deactivation_plan": deactivation_plan,
        "candidate": candidate,
        "request": request,
        "facts": facts,
        "approval": approval,
        "snapshot": snapshot,
        "usage": usage,
        "bundle": bundle,
        "bundle_fingerprint": shadow_evidence_bundle_fingerprint(bundle),
    }


def make_shadow_evidence_bundle() -> ShadowEvidenceBundle:
    budget = ShadowResourceBudget()
    usage = ShadowResourceUsage(evaluation_records=1)
    diagnostics = ShadowRunDiagnostics(
        run_id="shadow-run-181",
        reference_count=1,
        observation_count=1,
        evaluation_count=1,
        pattern_count=0,
        hypothesis_count=0,
        regression_proposal_count=0,
        shadow_proposal_count=0,
        operator_review_item_count=0,
        wall_clock_seconds=1.0,
        benchmark_cost_units=0,
        output_bytes=0,
        output_files=0,
        created_at=NOW,
    )
    provenance = ShadowProvenanceRecord(
        provenance_record_id="shadow-provenance-181",
        run_id="shadow-run-181",
        manifest_fingerprint="5" * 64,
        reference_fingerprints=("6" * 64,),
        created_at=NOW,
    )
    return ShadowEvidenceBundle(
        run_id="shadow-run-181",
        manifest_id="manifest-181",
        manifest_fingerprint="5" * 64,
        outcome="completed",
        evaluation_summary={"status": "redacted synthetic pass"},
        provenance=provenance,
        diagnostics=diagnostics,
        resource_budget=budget,
        resource_usage=usage,
        budget_decision=evaluate_shadow_budget(usage, budget),
        reason_codes=("shadow_run_completed", "shadow_budget_satisfied"),
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


def test_valid_contracts_are_accepted(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    assert ctx["candidate"].implementation_authorization_id == AUTHORIZATION_TRANSACTION_ID
    assert ctx["candidate"].parent_evaluation_id == PARENT_EVALUATION_ID
    assert ctx["candidate"].parent_evaluation_decision == PARENT_EVALUATION_DECISION
    assert validate_activation_candidate(ctx["candidate"], now=NOW).valid is True
    assert evaluate_shadow_activation_budget(ctx["usage"], ctx["budget"]).within_budget is True
    assert (
        evaluate_shadow_activation_health(
            ctx["snapshot"],
            ctx["monitoring_plan"],
            activation_window_end=ctx["request"].activation_window_end,
            maximum_runs=ctx["request"].maximum_runs,
            now=NOW,
        ).monitoring_passed
        is True
    )


def test_extra_fields_are_rejected(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload["extra"] = "blocked"
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)


def test_malformed_sha_fingerprint_and_timestamps_are_rejected(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload["candidate_commit_sha"] = "ABC"
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)

    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload["diff_sha256"] = "z" * 64
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)

    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload["created_at"] = datetime(2026, 1, 1, 12, 0)
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)


def test_protected_material_is_rejected(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload["activation_candidate_id"] = "raw-prompt"
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)

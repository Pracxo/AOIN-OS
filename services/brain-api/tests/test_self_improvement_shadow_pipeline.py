"""AION-178 controlled shadow pipeline tests."""

from __future__ import annotations

from test_self_improvement_shadow_contracts import (
    NOW,
    fixed_id_factory,
    make_bundle,
    make_manifest,
    make_metric,
    make_reference,
    make_snapshot,
)

from aion_brain.self_improvement.shadow_budget import ShadowResourceBudget
from aion_brain.self_improvement.shadow_observation import DisabledShadowReferenceAdapter
from aion_brain.self_improvement.shadow_pipeline import ControlledShadowPipeline


def test_complete_pipeline_returns_evidence_bundle() -> None:
    bundle = make_bundle()

    assert bundle.outcome == "completed"
    assert len(bundle.observations) == 1
    assert bundle.evaluation_summary is not None
    assert len(bundle.failure_patterns) == 1
    assert len(bundle.hypotheses) == 1
    assert len(bundle.regression_test_proposals) == 1
    assert len(bundle.shadow_proposals) == 1
    assert len(bundle.operator_review_items) == 1
    assert bundle.diagnostics.shadow_mode_runtime_enabled is False


def test_pipeline_without_repeated_pattern_returns_no_candidates() -> None:
    reference = make_reference(repeated_count=1)
    metric = make_metric(reference_id=reference.reference_id)
    manifest = make_manifest(references=(reference,), redacted_metrics=(metric,))
    snapshot = make_snapshot(reference=reference, metrics=(metric,))

    bundle = make_bundle(manifest=manifest, snapshots=(snapshot,))

    assert bundle.outcome == "completed_without_pattern"
    assert bundle.failure_patterns == ()
    assert bundle.hypotheses == ()
    assert bundle.shadow_proposals == ()
    assert bundle.approval_created is False


def test_pipeline_reference_failure_fails_closed() -> None:
    pipeline = ControlledShadowPipeline(
        reference_adapter=DisabledShadowReferenceAdapter(),
        resource_budget=ShadowResourceBudget(),
        clock=lambda: NOW,
        monotonic_clock=lambda: 0.0,
        id_factory=fixed_id_factory,
    )

    bundle = pipeline.run(make_manifest())

    assert bundle.outcome == "reference_unavailable"
    assert bundle.shadow_proposals == ()
    assert bundle.runtime_effect is False
    assert "shadow_run_stopped_fail_closed" in bundle.reason_codes


def test_pipeline_budget_failure_fails_closed_before_candidates() -> None:
    bundle = make_bundle(budget=ShadowResourceBudget(maximum_observation_references=0))

    assert bundle.outcome == "budget_blocked"
    assert bundle.budget_failure is not None
    assert bundle.failure_patterns == ()
    assert bundle.operator_review_items == ()

"""AION-178 deterministic shadow replay tests."""

from __future__ import annotations

from test_self_improvement_shadow_contracts import (
    NOW,
    fixed_id_factory,
    make_manifest,
    make_metric,
    make_reference,
    make_snapshot,
)

from aion_brain.self_improvement.shadow_budget import ShadowResourceBudget
from aion_brain.self_improvement.shadow_runner import replay_shadow_run


def test_fixed_replay_produces_identical_content_and_fingerprints() -> None:
    manifest = make_manifest()
    snapshot = make_snapshot()

    first = replay_shadow_run(
        manifest=manifest,
        resolved_snapshots=(snapshot,),
        resource_budget=ShadowResourceBudget(),
        fixed_clock=lambda: NOW,
        fixed_id_factory=fixed_id_factory,
    )
    second = replay_shadow_run(
        manifest=manifest,
        resolved_snapshots=(snapshot,),
        resource_budget=ShadowResourceBudget(),
        fixed_clock=lambda: NOW,
        fixed_id_factory=fixed_id_factory,
    )

    assert first == second
    assert first.fingerprint == second.fingerprint


def test_changed_reference_or_metric_changes_output_fingerprint() -> None:
    manifest = make_manifest()
    first = replay_shadow_run(
        manifest=manifest,
        resolved_snapshots=(make_snapshot(),),
        resource_budget=ShadowResourceBudget(),
        fixed_clock=lambda: NOW,
        fixed_id_factory=fixed_id_factory,
    )
    changed_reference = make_reference("shadow-ref-1", reference_fingerprint="1" * 64)
    changed_metric = make_metric(current_value=0.2, reference_id=changed_reference.reference_id)
    changed_manifest = make_manifest(
        references=(changed_reference,),
        redacted_metrics=(changed_metric,),
    )
    second = replay_shadow_run(
        manifest=changed_manifest,
        resolved_snapshots=(make_snapshot(reference=changed_reference, metrics=(changed_metric,)),),
        resource_budget=ShadowResourceBudget(),
        fixed_clock=lambda: NOW,
        fixed_id_factory=fixed_id_factory,
    )

    assert first.fingerprint != second.fingerprint


def test_default_ids_remain_unique() -> None:
    from aion_brain.self_improvement.shadow_pipeline import ControlledShadowPipeline

    first = ControlledShadowPipeline(
        reference_adapter=__import__(
            "aion_brain.self_improvement.shadow_observation",
            fromlist=["InMemoryShadowReferenceAdapter"],
        ).InMemoryShadowReferenceAdapter((make_snapshot(),)),
        clock=lambda: NOW,
        monotonic_clock=lambda: 0.0,
    ).run(make_manifest())
    second = ControlledShadowPipeline(
        reference_adapter=__import__(
            "aion_brain.self_improvement.shadow_observation",
            fromlist=["InMemoryShadowReferenceAdapter"],
        ).InMemoryShadowReferenceAdapter((make_snapshot(),)),
        clock=lambda: NOW,
        monotonic_clock=lambda: 0.0,
    ).run(make_manifest())

    assert first.run_id != second.run_id

"""AION-178 controlled shadow-mode contract tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.self_improvement_shadow import (
    ACTIVATION_PHASE_ID,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    DEFAULT_MAXIMUM_CONCURRENCY,
    DEFAULT_RETENTION_SECONDS,
    FORBIDDEN_SHADOW_REVIEW_STATES,
    IMPLEMENTATION_TASK,
    MAXIMUM_RETENTION_SECONDS,
    PROGRAM_ID,
    SHADOW_METRIC_NAMES,
    SHADOW_REASON_CODES,
    ShadowObservationManifest,
    ShadowRedactedMetric,
    ShadowReference,
    fingerprint_model,
    require_reason_codes,
    sha256_fingerprint,
)
from aion_brain.self_improvement.shadow_budget import ShadowResourceBudget
from aion_brain.self_improvement.shadow_evidence import ShadowEvidenceBundle
from aion_brain.self_improvement.shadow_observation import (
    InMemoryShadowReferenceAdapter,
    ShadowObservationRecord,
    ShadowReferenceSnapshot,
    observation_from_shadow_snapshot,
)
from aion_brain.self_improvement.shadow_pipeline import ControlledShadowPipeline

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def safe_fingerprint(label: str) -> str:
    return sha256_fingerprint({"synthetic": True, "label": label})


def fixed_id_factory(prefix: str, index: int) -> str:
    return f"{prefix}-{index}"


def make_reference(
    reference_id: str = "shadow-ref-1",
    *,
    reference_kind: str = "evaluation",
    repeated_count: int = 2,
    reference_fingerprint: str | None = None,
    observed_at: datetime = NOW,
) -> ShadowReference:
    return ShadowReference(
        reference_kind=reference_kind,
        reference_id=reference_id,
        reference_fingerprint=reference_fingerprint or safe_fingerprint(reference_id),
        observed_at=observed_at,
        repeated_count=repeated_count,
        source_version="source-v1",
    )


def make_metric(
    metric_name: str = "retrieval_precision",
    *,
    reference_id: str | None = "shadow-ref-1",
    current_value: float = 0.4,
    baseline_value: float = 0.7,
    target_value: float = 0.8,
    higher_is_better: bool = True,
    weight: float = 1.0,
    recorded_at: datetime = NOW,
) -> ShadowRedactedMetric:
    return ShadowRedactedMetric(
        metric_name=metric_name,
        current_value=current_value,
        baseline_value=baseline_value,
        target_value=target_value,
        higher_is_better=higher_is_better,
        weight=weight,
        recorded_at=recorded_at,
        reference_id=reference_id,
    )


def make_manifest(
    *,
    references: tuple[ShadowReference, ...] | None = None,
    redacted_metrics: tuple[ShadowRedactedMetric, ...] | None = None,
    manifest_id: str = "shadow-manifest-1",
    maximum_concurrency: int = 1,
    retention_seconds: int = DEFAULT_RETENTION_SECONDS,
    benchmark_cost_units: int = 0,
) -> ShadowObservationManifest:
    refs = references or (make_reference(),)
    metrics = redacted_metrics or (
        make_metric(reference_id=refs[0].reference_id),
    )
    return ShadowObservationManifest(
        manifest_id=manifest_id,
        references=refs,
        redacted_metrics=metrics,
        operator_scope_labels=("retrieval-ranking",),
        requested_review_outputs=("operator-review-items",),
        maximum_concurrency=maximum_concurrency,
        retention_seconds=retention_seconds,
        benchmark_cost_units=benchmark_cost_units,
        input_classification="redacted",
        created_at=NOW,
    )


def make_snapshot(
    reference: ShadowReference | None = None,
    *,
    metrics: tuple[ShadowRedactedMetric, ...] | None = None,
    summary: str = "Retrieval precision trailed the redacted target.",
) -> ShadowReferenceSnapshot:
    ref = reference or make_reference()
    return ShadowReferenceSnapshot(
        reference=ref,
        summary=summary,
        metrics=metrics or (make_metric(reference_id=ref.reference_id),),
        evidence_reference_fingerprints=(ref.reference_fingerprint,),
        source_record_version="source-v1",
        resolved_at=NOW,
    )


def make_pipeline(
    *,
    snapshots: tuple[ShadowReferenceSnapshot, ...] | None = None,
    budget: ShadowResourceBudget | None = None,
) -> ControlledShadowPipeline:
    adapter = InMemoryShadowReferenceAdapter(snapshots or (make_snapshot(),))
    return ControlledShadowPipeline(
        reference_adapter=adapter,
        resource_budget=budget or ShadowResourceBudget(),
        clock=lambda: NOW,
        monotonic_clock=lambda: 0.0,
        id_factory=fixed_id_factory,
    )


def make_bundle(
    *,
    manifest: ShadowObservationManifest | None = None,
    snapshots: tuple[ShadowReferenceSnapshot, ...] | None = None,
    budget: ShadowResourceBudget | None = None,
) -> ShadowEvidenceBundle:
    chosen_manifest = manifest or make_manifest()
    chosen_snapshots = snapshots or tuple(
        make_snapshot(reference=reference) for reference in chosen_manifest.references
    )
    return make_pipeline(snapshots=chosen_snapshots, budget=budget).run(chosen_manifest)


def make_observation(
    observation_id: str = "shadow-observation-1",
    *,
    reference: ShadowReference | None = None,
    metric: ShadowRedactedMetric | None = None,
    repeated_count: int = 2,
) -> ShadowObservationRecord:
    ref = reference or make_reference(repeated_count=repeated_count)
    chosen_metric = metric or make_metric(reference_id=ref.reference_id)
    snapshot = make_snapshot(reference=ref, metrics=(chosen_metric,))
    return observation_from_shadow_snapshot(
        snapshot,
        observation_id=observation_id,
        created_at=NOW,
    )


def test_valid_manifest_contract_is_accepted() -> None:
    manifest = make_manifest(maximum_concurrency=DEFAULT_MAXIMUM_CONCURRENCY)

    assert manifest.program_id == PROGRAM_ID
    assert manifest.activation_phase_id == ACTIVATION_PHASE_ID
    assert manifest.authorization_transaction_id == AUTHORIZATION_TRANSACTION_ID
    assert manifest.maximum_concurrency == DEFAULT_MAXIMUM_CONCURRENCY
    assert manifest.retention_seconds == DEFAULT_RETENTION_SECONDS
    assert manifest.shadow_only is True
    assert manifest.read_only is True
    assert manifest.redacted is True
    assert manifest.runtime_effect is False


def test_contract_constants_are_exact() -> None:
    assert IMPLEMENTATION_TASK == "AION-178"
    assert AUTHORIZATION_SCOPE == (
        "read-only-shadow-observation-evaluation-pattern-mining-proposal-generation"
    )
    assert MAXIMUM_RETENTION_SECONDS == 604800
    assert DEFAULT_MAXIMUM_CONCURRENCY == 4
    assert "retrieval_precision" in SHADOW_METRIC_NAMES
    assert "shadow_mode_runtime_disabled" in SHADOW_REASON_CODES


def test_extra_manifest_fields_are_rejected() -> None:
    payload = make_manifest().model_dump(mode="python")
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        ShadowObservationManifest(**payload)


def test_invalid_authorization_is_rejected() -> None:
    payload = make_manifest().model_dump(mode="python")
    payload["authorization_transaction_id"] = "AION-000-SI-0000"

    with pytest.raises(ValidationError):
        ShadowObservationManifest(**payload)


def test_invalid_reference_and_malformed_fingerprint_are_rejected() -> None:
    with pytest.raises(ValidationError):
        make_reference(reference_id="../bad")
    with pytest.raises(ValidationError):
        make_reference(reference_fingerprint="abc")


def test_naive_and_non_utc_timestamps_are_rejected() -> None:
    with pytest.raises(ValidationError):
        make_reference(observed_at=datetime(2026, 7, 20))
    with pytest.raises(ValidationError):
        make_reference(observed_at=datetime(2026, 7, 20, tzinfo=timezone(timedelta(hours=1))))


def test_duplicate_references_metrics_and_forbidden_review_states_are_rejected() -> None:
    ref = make_reference()
    with pytest.raises(ValidationError):
        make_manifest(references=(ref, ref))
    metric = make_metric()
    with pytest.raises(ValidationError):
        make_manifest(redacted_metrics=(metric, metric))
    with pytest.raises(ValidationError):
        ShadowObservationManifest(
            **{
                **make_manifest().model_dump(mode="python"),
                "requested_review_outputs": tuple(FORBIDDEN_SHADOW_REVIEW_STATES),
            }
        )


def test_evidence_is_immutable_and_reason_codes_are_strict() -> None:
    bundle = make_bundle()

    with pytest.raises(ValidationError):
        bundle.runtime_effect = True  # type: ignore[misc]
    with pytest.raises(ValueError):
        require_reason_codes(("shadow_run_completed", "shadow_run_completed"))
    with pytest.raises(ValueError):
        require_reason_codes(("shadow_unknown",))
    assert fingerprint_model(bundle) == bundle.fingerprint

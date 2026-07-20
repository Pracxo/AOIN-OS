"""AION-178 shadow observation manifest tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_contracts import (
    NOW,
    make_manifest,
    make_metric,
    make_reference,
)

from aion_brain.contracts.self_improvement_shadow import ShadowObservationManifest


def test_manifest_bounds_and_flags_are_enforced() -> None:
    manifest = make_manifest(maximum_concurrency=4, retention_seconds=604800)

    assert manifest.operator_invoked is True
    assert manifest.shadow_only is True
    assert manifest.read_only is True
    assert manifest.redacted is True
    assert manifest.source_modified is False
    assert manifest.git_mutated is False
    assert manifest.pull_request_created is False
    assert manifest.approval_created is False
    assert manifest.runtime_effect is False


def test_manifest_rejects_over_limit_concurrency_retention_and_cost() -> None:
    with pytest.raises(ValidationError):
        make_manifest(maximum_concurrency=5)
    with pytest.raises(ValidationError):
        make_manifest(retention_seconds=604801)
    with pytest.raises(ValidationError):
        make_manifest(benchmark_cost_units=51)


def test_manifest_rejects_side_effect_flags() -> None:
    payload = make_manifest().model_dump(mode="python")
    payload["source_modified"] = True

    with pytest.raises(ValidationError):
        ShadowObservationManifest(**payload)


def test_manifest_rejects_duplicate_reference_metric_pairs() -> None:
    ref_a = make_reference("shadow-ref-1")
    ref_b = make_reference("shadow-ref-2")
    metrics = (
        make_metric(reference_id=ref_a.reference_id),
        make_metric(reference_id=ref_b.reference_id),
    )
    assert make_manifest(references=(ref_a, ref_b), redacted_metrics=metrics)

    with pytest.raises(ValidationError):
        make_manifest(
            references=(ref_a, ref_b),
            redacted_metrics=(metrics[0], make_metric(reference_id=ref_a.reference_id)),
        )


def test_manifest_timestamp_must_be_utc() -> None:
    payload = make_manifest().model_dump(mode="python")
    payload["created_at"] = datetime(2026, 7, 20)

    with pytest.raises(ValidationError):
        ShadowObservationManifest(**payload)

    payload["created_at"] = NOW.astimezone(UTC)
    assert ShadowObservationManifest(**payload)

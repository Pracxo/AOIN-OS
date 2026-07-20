"""AION-178 bounded shadow concurrency tests."""

from __future__ import annotations

from threading import Lock

from test_self_improvement_shadow_contracts import (
    NOW,
    fixed_id_factory,
    make_manifest,
    make_metric,
    make_reference,
    make_snapshot,
)

from aion_brain.self_improvement.shadow_observation import (
    ShadowReferenceResolutionError,
    ShadowReferenceSnapshot,
)
from aion_brain.self_improvement.shadow_pipeline import ControlledShadowPipeline


class CountingAdapter:
    def __init__(
        self,
        snapshots: tuple[ShadowReferenceSnapshot, ...],
        fail_id: str | None = None,
    ) -> None:
        self._snapshots = {item.reference.reference_id: item for item in snapshots}
        self._fail_id = fail_id
        self.seen: list[str] = []
        self.maximum_active = 0
        self._active = 0
        self._lock = Lock()

    def resolve(self, reference):
        with self._lock:
            self.seen.append(reference.reference_id)
            self._active += 1
            self.maximum_active = max(self.maximum_active, self._active)
        try:
            if reference.reference_id == self._fail_id:
                raise ShadowReferenceResolutionError("shadow_reference_unavailable")
            return self._snapshots[reference.reference_id]
        finally:
            with self._lock:
                self._active -= 1


def test_reference_resolution_is_bounded_and_ordered() -> None:
    references = tuple(make_reference(f"shadow-ref-{index}") for index in range(6))
    metrics = tuple(make_metric(reference_id=reference.reference_id) for reference in references)
    snapshots = tuple(
        make_snapshot(reference=reference, metrics=(metric,))
        for reference, metric in zip(references, metrics, strict=True)
    )
    adapter = CountingAdapter(snapshots)
    pipeline = ControlledShadowPipeline(
        reference_adapter=adapter,
        clock=lambda: NOW,
        monotonic_clock=lambda: 0.0,
        id_factory=fixed_id_factory,
    )

    bundle = pipeline.run(
        make_manifest(references=references, redacted_metrics=metrics, maximum_concurrency=4)
    )

    assert adapter.maximum_active <= 4
    assert tuple(item.source_reference.reference_id for item in bundle.observations) == tuple(
        reference.reference_id for reference in references
    )


def test_one_failed_reference_fails_closed_without_retry_storm() -> None:
    good = make_reference("shadow-ref-1")
    bad = make_reference("shadow-ref-2")
    adapter = CountingAdapter((make_snapshot(reference=good),), fail_id=bad.reference_id)
    pipeline = ControlledShadowPipeline(
        reference_adapter=adapter,
        clock=lambda: NOW,
        monotonic_clock=lambda: 0.0,
        id_factory=fixed_id_factory,
    )

    bundle = pipeline.run(make_manifest(references=(good, bad)))

    assert bundle.outcome == "reference_unavailable"
    assert adapter.seen.count(bad.reference_id) == 1

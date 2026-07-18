"""Read-only benchmark manifest registry helpers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from aion_brain.self_improvement.benchmark_contracts import (
    BenchmarkCaseReference,
    BenchmarkManifest,
    BenchmarkMetric,
)


class BenchmarkRegistry:
    """In-memory registry for immutable benchmark manifests."""

    def __init__(self, manifests: Iterable[BenchmarkManifest] = ()) -> None:
        self._manifests: dict[str, BenchmarkManifest] = {}
        for manifest in manifests:
            self.register(manifest)

    def register(self, manifest: BenchmarkManifest) -> BenchmarkManifest:
        """Register a manifest if its ID is new or identical to the existing version."""

        existing = self._manifests.get(manifest.manifest_id)
        if existing is not None and existing.manifest_fingerprint != manifest.manifest_fingerprint:
            raise ValueError("benchmark manifest IDs are immutable once registered")
        self._manifests[manifest.manifest_id] = manifest
        return manifest

    def get(self, manifest_id: str) -> BenchmarkManifest:
        """Return a manifest by ID."""

        try:
            return self._manifests[manifest_id]
        except KeyError as exc:
            raise KeyError(f"unknown benchmark manifest: {manifest_id}") from exc

    def manifest_ids(self) -> tuple[str, ...]:
        """Return registered manifest IDs in deterministic order."""

        return tuple(sorted(self._manifests))

    def manifests(self) -> tuple[BenchmarkManifest, ...]:
        """Return registered manifests in deterministic order."""

        return tuple(self._manifests[manifest_id] for manifest_id in self.manifest_ids())


def build_benchmark_manifest(
    *,
    manifest_id: str,
    benchmark_version: str,
    case_references: tuple[BenchmarkCaseReference, ...],
    metric_definitions: tuple[BenchmarkMetric, ...],
    created_at: datetime,
) -> BenchmarkManifest:
    """Build a manifest and let its contract assign the canonical fingerprint."""

    return BenchmarkManifest(
        manifest_id=manifest_id,
        benchmark_version=benchmark_version,
        case_references=case_references,
        metric_definitions=metric_definitions,
        created_at=created_at,
    )


__all__ = ["BenchmarkRegistry", "build_benchmark_manifest"]

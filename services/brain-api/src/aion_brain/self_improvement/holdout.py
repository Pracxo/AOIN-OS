"""Holdout benchmark protections for self-improvement evaluation."""

from __future__ import annotations

from collections.abc import Iterable

from aion_brain.self_improvement.benchmark_contracts import (
    PROTECTED_HOLDOUT_PREFIX,
    BenchmarkManifest,
    sha256_json,
)
from aion_brain.self_improvement.protected_paths import (
    matched_protected_pattern,
    normalize_repo_path,
)


def opaque_case_id(*, manifest_id: str, raw_case_id: str) -> str:
    """Return a deterministic opaque case ID for patch-generation boundaries."""

    return sha256_json({"manifest_id": manifest_id, "raw_case_id": raw_case_id})[:32]


def patch_generator_case_ids(manifest: BenchmarkManifest) -> tuple[str, ...]:
    """Return only opaque case IDs, never holdout paths or content fingerprints."""

    return tuple(case.opaque_case_id for case in manifest.case_references)


def hidden_holdout_path_is_protected(path: str) -> bool:
    """Return whether a hidden holdout path is under the protected-core boundary."""

    normalized = normalize_repo_path(path)
    return (
        normalized.startswith(PROTECTED_HOLDOUT_PREFIX)
        and matched_protected_pattern(normalized) is not None
    )


def assert_holdout_controls(
    manifest: BenchmarkManifest,
    *,
    candidate_changed_paths: Iterable[str],
    candidate_modified_baseline: bool = False,
    candidate_modified_holdout: bool = False,
) -> None:
    """Fail closed if a candidate touches its baseline or protected holdout."""

    if candidate_modified_baseline:
        raise ValueError("candidate code cannot update its own baseline")
    if candidate_modified_holdout:
        raise ValueError("candidate code cannot modify the holdout in the same proposal")

    for case in manifest.case_references:
        if case.hidden and not hidden_holdout_path_is_protected(case.holdout_path):
            raise ValueError("hidden holdout path must be protected")

    for path in candidate_changed_paths:
        normalized = normalize_repo_path(path)
        if normalized.startswith(PROTECTED_HOLDOUT_PREFIX):
            raise ValueError("candidate code cannot modify the holdout in the same proposal")


__all__ = [
    "assert_holdout_controls",
    "hidden_holdout_path_is_protected",
    "opaque_case_id",
    "patch_generator_case_ids",
]

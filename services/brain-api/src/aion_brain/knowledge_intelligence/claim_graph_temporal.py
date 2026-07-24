"""Pure temporal, jurisdiction, and version-scope overlap functions."""

from __future__ import annotations

from typing import Literal

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimScope,
    JurisdictionKind,
    JurisdictionScope,
    ValidTimeInterval,
    VersionScheme,
    VersionScope,
)

ScopeOverlap = Literal["overlap", "nonoverlap", "insufficient"]


def valid_time_intervals_overlap(
    left: tuple[ValidTimeInterval, ...],
    right: tuple[ValidTimeInterval, ...],
) -> ScopeOverlap:
    """Return explicit valid-time overlap without substituting current time."""

    if not left or not right:
        return "insufficient"
    for left_interval in left:
        for right_interval in right:
            if _intervals_overlap(left_interval, right_interval):
                return "overlap"
    return "nonoverlap"


def jurisdiction_scopes_overlap(
    left: tuple[JurisdictionScope, ...],
    right: tuple[JurisdictionScope, ...],
) -> ScopeOverlap:
    """Return explicit jurisdiction overlap without external hierarchy lookup."""

    if not left or not right:
        return "insufficient"
    for left_scope in left:
        for right_scope in right:
            if _jurisdiction_pair_overlaps(left_scope, right_scope):
                return "overlap"
    return "nonoverlap"


def version_scopes_overlap(
    left: tuple[VersionScope, ...],
    right: tuple[VersionScope, ...],
) -> ScopeOverlap:
    """Return explicit version overlap without semantic-version inference."""

    if not left or not right:
        return "insufficient"
    for left_scope in left:
        for right_scope in right:
            if _version_pair_overlaps(left_scope, right_scope):
                return "overlap"
    return "nonoverlap"


def claim_scopes_overlap(left: ClaimScope, right: ClaimScope) -> ScopeOverlap:
    """Return overlap only when every scope dimension is explicitly overlapping."""

    decisions = (
        valid_time_intervals_overlap(left.valid_time_intervals, right.valid_time_intervals),
        jurisdiction_scopes_overlap(left.jurisdiction_scopes, right.jurisdiction_scopes),
        version_scopes_overlap(left.version_scopes, right.version_scopes),
    )
    if any(decision == "nonoverlap" for decision in decisions):
        return "nonoverlap"
    if any(decision == "insufficient" for decision in decisions):
        return "insufficient"
    return "overlap"


def _intervals_overlap(left: ValidTimeInterval, right: ValidTimeInterval) -> bool:
    if left.end is not None and right.start is not None:
        if left.end < right.start:
            return False
        if left.end == right.start and not (left.end_inclusive and right.start_inclusive):
            return False
    if right.end is not None and left.start is not None:
        if right.end < left.start:
            return False
        if right.end == left.start and not (right.end_inclusive and left.start_inclusive):
            return False
    return True


def _jurisdiction_pair_overlaps(left: JurisdictionScope, right: JurisdictionScope) -> bool:
    if left.jurisdiction_id == right.jurisdiction_id:
        return True
    if left.jurisdiction_kind == JurisdictionKind.GLOBAL:
        return True
    if right.jurisdiction_kind == JurisdictionKind.GLOBAL:
        return True
    if left.jurisdiction_id in right.parent_jurisdiction_ids:
        return True
    return right.jurisdiction_id in left.parent_jurisdiction_ids


def _version_pair_overlaps(left: VersionScope, right: VersionScope) -> bool:
    if left.target_id != right.target_id:
        return False
    if left.scheme == VersionScheme.OPAQUE_EXACT or right.scheme == VersionScheme.OPAQUE_EXACT:
        return (
            left.scheme == right.scheme == VersionScheme.OPAQUE_EXACT
            and left.exact_version == right.exact_version
        )
    left_range = _version_range(left)
    right_range = _version_range(right)
    left_lower, left_upper, left_lower_inclusive, left_upper_inclusive = left_range
    right_lower, right_upper, right_lower_inclusive, right_upper_inclusive = right_range
    if left_upper is not None and right_lower is not None:
        comparison = _compare_versions(left_upper, right_lower)
        if comparison < 0:
            return False
        if comparison == 0 and not (left_upper_inclusive and right_lower_inclusive):
            return False
    if right_upper is not None and left_lower is not None:
        comparison = _compare_versions(right_upper, left_lower)
        if comparison < 0:
            return False
        if comparison == 0 and not (right_upper_inclusive and left_lower_inclusive):
            return False
    return True


def _version_range(
    scope: VersionScope,
) -> tuple[tuple[int, ...] | None, tuple[int, ...] | None, bool, bool]:
    if scope.exact_version is not None:
        parsed = _parse_version(scope.exact_version)
        return parsed, parsed, True, True
    lower = _parse_version(scope.lower_bound) if scope.lower_bound is not None else None
    upper = _parse_version(scope.upper_bound) if scope.upper_bound is not None else None
    return lower, upper, scope.lower_inclusive, scope.upper_inclusive


def _parse_version(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    width = max(len(left), len(right))
    padded_left = left + (0,) * (width - len(left))
    padded_right = right + (0,) * (width - len(right))
    return (padded_left > padded_right) - (padded_left < padded_right)


__all__ = [
    "ScopeOverlap",
    "claim_scopes_overlap",
    "jurisdiction_scopes_overlap",
    "valid_time_intervals_overlap",
    "version_scopes_overlap",
]

"""Deterministic learning pattern helpers."""

from __future__ import annotations

import re

from aion_brain.contracts.experience import ExperienceRecord
from aion_brain.contracts.learning_synthesis import LearningPatternType, LearningSeverity

_TOKEN_RE = re.compile(r"[^a-z0-9]+")


def normalized_summary_key(summary: str) -> str:
    """Return a compact deterministic grouping key."""
    cleaned = _TOKEN_RE.sub(" ", summary.lower()).strip()
    tokens = [token for token in cleaned.split() if token]
    return " ".join(tokens[:10]) or "generic"


def source_key(experience: ExperienceRecord) -> str:
    """Return a deterministic source grouping key."""
    return f"{experience.source_type}:{experience.source_id}"


def pattern_type_for(experience_type: str) -> LearningPatternType:
    """Map experience type to generic pattern type."""
    if experience_type == "success":
        return "repeated_success"
    if experience_type == "failure":
        return "repeated_failure"
    if experience_type == "blocked_action":
        return "recurring_block"
    if experience_type == "approval_required":
        return "approval_bottleneck"
    if experience_type == "missing_effect":
        return "missing_effect"
    if experience_type == "unexpected_effect":
        return "unexpected_effect"
    if experience_type == "regression_drift":
        return "regression_drift"
    if experience_type == "replay_drift":
        return "replay_drift"
    if experience_type == "contradiction":
        return "contradiction"
    if experience_type == "recovery":
        return "recovery_pattern"
    return "generic"


def severity_for_pattern(pattern_type: str, confidence: float) -> LearningSeverity:
    """Map generic pattern type and confidence to severity."""
    if pattern_type in {"repeated_failure", "contradiction", "regression_drift"}:
        return "high" if confidence >= 0.7 else "medium"
    if pattern_type in {"missing_effect", "unexpected_effect", "recurring_block"}:
        return "medium"
    if pattern_type == "approval_bottleneck":
        return "medium"
    return "low"


def recommendation_for(pattern_type: str) -> str:
    """Return a generic recommendation for one pattern type."""
    if pattern_type == "repeated_success":
        return "Preserve the generic conditions that produced repeated success."
    if pattern_type == "repeated_failure":
        return "Review planning, context, policy, and verification before repeating."
    if pattern_type == "approval_bottleneck":
        return "Review risk level, approval scope, and autonomy constraints."
    if pattern_type == "missing_effect":
        return "Clarify success criteria and verification before repeating."
    if pattern_type == "unexpected_effect":
        return "Review assumptions and counterfactuals before repeating."
    if pattern_type == "regression_drift":
        return "Add or update regression coverage before changing this path."
    if pattern_type == "replay_drift":
        return "Review deterministic replay inputs and expected snapshots."
    if pattern_type == "contradiction":
        return "Review belief, evidence, and memory governance state."
    if pattern_type == "recovery_pattern":
        return "Preserve recovery conditions and review repeatability."
    return "Review linked experiences and outcomes."


__all__ = [
    "normalized_summary_key",
    "pattern_type_for",
    "recommendation_for",
    "severity_for_pattern",
    "source_key",
]

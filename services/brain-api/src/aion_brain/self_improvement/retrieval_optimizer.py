"""Bounded data-only retrieval ranking optimization."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.self_improvement.canary_contracts import safe_text
from aion_brain.self_improvement.outcome_ledger import LearningLedgerRecord

RetrievalRankingStatus = Literal["candidate", "active", "archived"]


class RetrievalRankingVersion(BaseModel):
    """Versioned retrieval feature weights with bounded data-only updates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version_id: str = Field(min_length=1)
    feature_weights: dict[str, float] = Field(min_length=1)
    status: RetrievalRankingStatus
    source_rewrite_enabled: bool = False
    approval_required_for_promotion: bool = True

    @field_validator("version_id")
    @classmethod
    def version_id_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "retrieval ranking version id")

    @field_validator("feature_weights")
    @classmethod
    def weights_must_be_bounded(cls, value: dict[str, float]) -> dict[str, float]:
        cleaned: dict[str, float] = {}
        for feature, weight in value.items():
            cleaned[safe_text(feature, "retrieval ranking feature")] = _bounded(weight)
        return cleaned

    @model_validator(mode="after")
    def update_must_remain_data_only(self) -> RetrievalRankingVersion:
        if self.source_rewrite_enabled:
            raise ValueError("retrieval optimization cannot rewrite source")
        if not self.approval_required_for_promotion:
            raise ValueError("retrieval ranking promotion requires approval")
        return self


class RetrievalRankingOptimizer:
    """Create reversible candidate ranking versions from outcome records."""

    def propose_candidate(
        self,
        active: RetrievalRankingVersion,
        outcomes: tuple[LearningLedgerRecord, ...],
        *,
        candidate_version_id: str,
    ) -> RetrievalRankingVersion:
        """Return a bounded candidate version without changing the active version."""

        if active.status != "active":
            raise ValueError("retrieval optimizer requires an active baseline version")
        direction = _outcome_direction(outcomes)
        updated = {
            feature: _bounded(weight + direction * 0.05)
            for feature, weight in active.feature_weights.items()
        }
        return RetrievalRankingVersion(
            version_id=candidate_version_id,
            feature_weights=updated,
            status="candidate",
        )

    def promote(
        self,
        candidate: RetrievalRankingVersion,
        *,
        approval_granted: bool,
    ) -> RetrievalRankingVersion:
        """Promote a candidate version only after explicit approval."""

        if candidate.status != "candidate":
            raise ValueError("only candidate retrieval versions can be promoted")
        if not approval_granted:
            raise ValueError("approval is required to promote retrieval ranking updates")
        return candidate.model_copy(update={"status": "active"})


def _outcome_direction(outcomes: tuple[LearningLedgerRecord, ...]) -> float:
    successes = sum(1 for outcome in outcomes if outcome.outcome_value == "improvement_success")
    failures = sum(
        1
        for outcome in outcomes
        if outcome.outcome_value in {"improvement_failed", "improvement_rolled_back"}
    )
    if successes > failures:
        return 1.0
    if failures > successes:
        return -1.0
    return 0.0


def _bounded(value: float) -> float:
    return max(-1.0, min(1.0, value))


__all__ = [
    "RetrievalRankingOptimizer",
    "RetrievalRankingStatus",
    "RetrievalRankingVersion",
]

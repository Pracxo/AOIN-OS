"""Bounded context-bucketed strategy selection."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.self_improvement.canary_contracts import safe_text


class StrategyStats(BaseModel):
    """Beta-Bernoulli statistics for one allowlisted strategy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_id: str = Field(min_length=1)
    alpha: float = Field(default=1.0, gt=0.0)
    beta: float = Field(default=1.0, gt=0.0)

    @field_validator("strategy_id")
    @classmethod
    def strategy_id_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "strategy id")

    @property
    def expected_success(self) -> float:
        """Return the posterior mean."""

        return self.alpha / (self.alpha + self.beta)

    def update(self, *, success: bool) -> StrategyStats:
        """Return updated bounded statistics."""

        return self.model_copy(
            update={
                "alpha": self.alpha + (1.0 if success else 0.0),
                "beta": self.beta + (0.0 if success else 1.0),
            }
        )


class StrategySelectionPolicy(BaseModel):
    """Allowlisted strategy-selection policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    allowlisted_strategy_ids: tuple[str, ...] = Field(min_length=1)
    shadow_mode: bool = True
    exploration_cap: float = Field(default=0.05, ge=0.0, le=0.2)
    strategy_creation_at_runtime_enabled: bool = False
    safety_gate_bypass_enabled: bool = False

    @field_validator("allowlisted_strategy_ids")
    @classmethod
    def allowlist_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(safe_text(item, "strategy allowlist id") for item in value)

    @model_validator(mode="after")
    def policy_must_remain_bounded(self) -> StrategySelectionPolicy:
        if not self.shadow_mode:
            raise ValueError("strategy selection defaults to shadow mode")
        if self.strategy_creation_at_runtime_enabled:
            raise ValueError("runtime strategy creation is prohibited")
        if self.safety_gate_bypass_enabled:
            raise ValueError("strategy selection cannot bypass safety gates")
        return self


class StrategySelection(BaseModel):
    """One shadow-mode strategy selection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    context_bucket_id: str
    selected_strategy_id: str
    shadow_mode: bool
    expected_success: float = Field(ge=0.0, le=1.0)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)


class ContextBucketStrategySelector:
    """Select the best allowlisted strategy for a context bucket."""

    def select(
        self,
        policy: StrategySelectionPolicy,
        context_bucket_id: str,
        stats: tuple[StrategyStats, ...],
    ) -> StrategySelection:
        """Return the highest-posterior strategy without direct execution."""

        allowed = set(policy.allowlisted_strategy_ids)
        ranked = [item for item in stats if item.strategy_id in allowed]
        if not ranked:
            raise ValueError("at least one allowlisted strategy statistic is required")
        selected = max(ranked, key=lambda item: item.expected_success)
        return StrategySelection(
            context_bucket_id=safe_text(context_bucket_id, "context bucket id"),
            selected_strategy_id=selected.strategy_id,
            shadow_mode=policy.shadow_mode,
            expected_success=selected.expected_success,
            reason_codes=("shadow_mode_selection_only",),
        )


__all__ = [
    "ContextBucketStrategySelector",
    "StrategySelection",
    "StrategySelectionPolicy",
    "StrategyStats",
]

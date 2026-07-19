"""User-scoped reversible preference learning for AION-174."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.self_improvement.canary_contracts import safe_text

PreferenceImpact = Literal["low", "medium", "high"]
PROTECTED_ATTRIBUTE_NAMES = frozenset(
    {
        "age",
        "race",
        "ethnicity",
        "religion",
        "sex",
        "gender",
        "sexual_orientation",
        "disability",
        "pregnancy",
        "marital_status",
    }
)


class UserPreferenceSignal(BaseModel):
    """One user-scoped preference signal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_id: str = Field(min_length=1)
    user_scope_id: str = Field(min_length=1)
    preference_key: str = Field(min_length=1)
    positive: bool
    confidence: float = Field(ge=0.0, le=1.0)
    impact: PreferenceImpact = "low"

    @field_validator("signal_id", "user_scope_id", "preference_key")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "preference signal text")

    @model_validator(mode="after")
    def signal_must_not_infer_protected_attributes(self) -> UserPreferenceSignal:
        if self.preference_key.lower() in PROTECTED_ATTRIBUTE_NAMES:
            raise ValueError("protected attribute preference inference is prohibited")
        return self


class PreferenceDistribution(BaseModel):
    """Reversible user-scoped preference confidence distribution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    distribution_id: str = Field(min_length=1)
    user_scope_id: str = Field(min_length=1)
    preference_key: str = Field(min_length=1)
    alpha: float = Field(default=1.0, gt=0.0)
    beta: float = Field(default=1.0, gt=0.0)
    version: int = Field(default=1, ge=1)
    reversible: bool = True
    high_impact_approval_required: bool = True

    @field_validator("distribution_id", "user_scope_id", "preference_key")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "preference distribution text")

    @model_validator(mode="after")
    def distribution_must_remain_reversible(self) -> PreferenceDistribution:
        if self.preference_key.lower() in PROTECTED_ATTRIBUTE_NAMES:
            raise ValueError("protected attribute preference inference is prohibited")
        if not self.reversible:
            raise ValueError("preference learning must be reversible")
        if not self.high_impact_approval_required:
            raise ValueError("high-impact preference changes require approval")
        return self

    @property
    def mean_confidence(self) -> float:
        """Return the Beta posterior mean."""

        return self.alpha / (self.alpha + self.beta)


class PreferenceLearner:
    """Apply bounded preference signals to user-scoped distributions."""

    def update(
        self,
        distribution: PreferenceDistribution,
        signal: UserPreferenceSignal,
        *,
        approval_granted: bool = False,
    ) -> PreferenceDistribution:
        """Return an updated distribution, requiring approval for high-impact signals."""

        if distribution.user_scope_id != signal.user_scope_id:
            raise ValueError("preference signal must match the user scope")
        if distribution.preference_key != signal.preference_key:
            raise ValueError("preference signal must match the preference key")
        if signal.impact == "high" and not approval_granted:
            raise ValueError("approval is required for high-impact preference changes")
        return distribution.model_copy(
            update={
                "alpha": distribution.alpha + (signal.confidence if signal.positive else 0.0),
                "beta": distribution.beta + (0.0 if signal.positive else signal.confidence),
                "version": distribution.version + 1,
            }
        )

    def revert(self, distribution: PreferenceDistribution) -> PreferenceDistribution:
        """Return a reversible prior version marker."""

        return distribution.model_copy(
            update={
                "alpha": 1.0,
                "beta": 1.0,
                "version": distribution.version + 1,
            }
        )


__all__ = [
    "PROTECTED_ATTRIBUTE_NAMES",
    "PreferenceDistribution",
    "PreferenceImpact",
    "PreferenceLearner",
    "UserPreferenceSignal",
]

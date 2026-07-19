"""Case-based planning for governed self-improvement."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.self_improvement.canary_contracts import safe_text


class PlanningCase(BaseModel):
    """Successful historical planning case used as data-only guidance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1)
    context_tags: tuple[str, ...] = Field(min_length=1)
    plan_template: tuple[str, ...] = Field(min_length=1)
    success_score: float = Field(ge=0.0, le=1.0)
    policy_validated: bool
    direct_execution_allowed: bool = False

    @field_validator("case_id")
    @classmethod
    def case_id_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "planning case id")

    @field_validator("context_tags", "plan_template")
    @classmethod
    def tuple_text_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(safe_text(item, "planning case text") for item in value)

    @model_validator(mode="after")
    def case_must_preserve_policy_gate(self) -> PlanningCase:
        if self.direct_execution_allowed:
            raise ValueError("case-based planning cannot bypass execution approval")
        if not self.policy_validated:
            raise ValueError("planning cases must preserve policy validation")
        return self


class AdaptedPlan(BaseModel):
    """Policy-preserving adapted plan template."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    adapted_plan_id: str = Field(min_length=1)
    source_case_id: str = Field(min_length=1)
    context_tags: tuple[str, ...] = Field(min_length=1)
    steps: tuple[str, ...] = Field(min_length=1)
    policy_validation_preserved: bool
    direct_execution_allowed: bool = False

    @model_validator(mode="after")
    def adapted_plan_must_remain_non_executing(self) -> AdaptedPlan:
        if self.direct_execution_allowed:
            raise ValueError("adapted plans cannot directly execute")
        if not self.policy_validation_preserved:
            raise ValueError("adapted plans must preserve policy validation")
        return self


class CaseBasedPlanner:
    """Retrieve similar successful cases and adapt their plan templates."""

    def retrieve(
        self,
        cases: tuple[PlanningCase, ...],
        context_tags: tuple[str, ...],
    ) -> PlanningCase:
        """Return the most similar policy-valid case."""

        requested = set(context_tags)
        ranked = sorted(
            cases,
            key=lambda case: (len(requested & set(case.context_tags)), case.success_score),
            reverse=True,
        )
        if not ranked:
            raise ValueError("at least one planning case is required")
        return ranked[0]

    def adapt(
        self,
        case: PlanningCase,
        context_tags: tuple[str, ...],
        *,
        adapted_plan_id: str,
    ) -> AdaptedPlan:
        """Return a policy-preserving data-only plan adaptation."""

        return AdaptedPlan(
            adapted_plan_id=adapted_plan_id,
            source_case_id=case.case_id,
            context_tags=context_tags,
            steps=case.plan_template,
            policy_validation_preserved=case.policy_validated,
        )


__all__ = ["AdaptedPlan", "CaseBasedPlanner", "PlanningCase"]

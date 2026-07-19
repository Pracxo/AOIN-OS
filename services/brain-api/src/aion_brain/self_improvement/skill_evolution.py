"""Data-only procedural skill evolution for AION-174."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.self_improvement.canary_contracts import safe_text

SkillApprovalStatus = Literal["pending", "approved", "rejected"]
SkillRecordStatus = Literal["candidate", "active", "archived"]


class ProceduralSkillRecord(BaseModel):
    """Versioned data-only procedural skill record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    skill_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    status: SkillRecordStatus
    procedure_steps: tuple[str, ...] = Field(min_length=1)
    policy_gate_passed: bool
    approval_status: SkillApprovalStatus = "pending"
    executable_source_generated: bool = False
    direct_runtime_activation_enabled: bool = False

    @field_validator("skill_id")
    @classmethod
    def skill_id_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "procedural skill id")

    @field_validator("procedure_steps")
    @classmethod
    def steps_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(safe_text(step, "procedural skill step") for step in value)

    @model_validator(mode="after")
    def skill_record_must_be_data_only(self) -> ProceduralSkillRecord:
        if self.executable_source_generated:
            raise ValueError("procedural skill evolution cannot generate executable source")
        if self.direct_runtime_activation_enabled:
            raise ValueError("procedural skills cannot directly activate runtime behavior")
        if self.status == "active" and self.approval_status != "approved":
            raise ValueError("active procedural skills require approval")
        if self.status == "active" and not self.policy_gate_passed:
            raise ValueError("active procedural skills require a passed policy gate")
        return self


class ProceduralSkillEvolution:
    """Create and promote data-only skill records."""

    def propose(
        self,
        current: ProceduralSkillRecord,
        *,
        candidate_steps: tuple[str, ...],
    ) -> ProceduralSkillRecord:
        """Return a new candidate skill version."""

        return ProceduralSkillRecord(
            skill_id=current.skill_id,
            version=current.version + 1,
            status="candidate",
            procedure_steps=candidate_steps,
            policy_gate_passed=False,
            approval_status="pending",
        )

    def promote(
        self,
        candidate: ProceduralSkillRecord,
        *,
        policy_gate_passed: bool,
        approval_granted: bool,
    ) -> ProceduralSkillRecord:
        """Promote only when policy and approval gates pass."""

        if candidate.status != "candidate":
            raise ValueError("only candidate skill records can be promoted")
        if not policy_gate_passed:
            raise ValueError("policy gate is required before skill promotion")
        if not approval_granted:
            raise ValueError("approval is required before skill promotion")
        return candidate.model_copy(
            update={
                "status": "active",
                "policy_gate_passed": True,
                "approval_status": "approved",
            }
        )


__all__ = [
    "ProceduralSkillEvolution",
    "ProceduralSkillRecord",
    "SkillApprovalStatus",
    "SkillRecordStatus",
]

"""Reflection contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.execution import ExecutionRun
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.tasks import CognitiveTask, TaskRunRecord
from aion_brain.contracts.traces import DecisionTrace

ReflectionType = Literal[
    "trace_review",
    "task_run_review",
    "execution_review",
    "retrieval_review",
    "planning_review",
    "policy_review",
    "failure_review",
    "success_pattern_review",
]
ReflectionStatus = Literal["recorded", "candidate_created", "dismissed"]


class ReflectionRecord(BaseModel):
    """Persistent deterministic reflection record."""

    model_config = ConfigDict(extra="forbid")

    reflection_id: str = Field(min_length=1)
    trace_id: str | None = None
    task_id: str | None = None
    task_run_id: str | None = None
    execution_id: str | None = None
    evaluation_id: str | None = None
    learning_signal_ids: list[str] = Field(default_factory=list)
    reflection_type: ReflectionType
    observations: list[str] = Field(default_factory=list)
    proposed_changes: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    status: ReflectionStatus
    created_at: datetime | None = None

    @model_validator(mode="after")
    def observations_required_unless_dismissed(self) -> "ReflectionRecord":
        """Require observations for active reflection records."""
        if self.status != "dismissed" and not self.observations:
            raise ValueError("observations can be empty only when status=dismissed")
        return self


class ReflectionRequest(BaseModel):
    """Request to reflect on Brain-owned artifacts."""

    model_config = ConfigDict(extra="forbid")

    reflection_id: str | None = None
    event: AIONEvent | None = None
    trace: DecisionTrace | None = None
    evaluation: EvaluationRecord | None = None
    learning_signals: list[LearningSignal] = Field(default_factory=list)
    task: CognitiveTask | None = None
    task_run: TaskRunRecord | None = None
    execution: ExecutionRun | None = None
    reflection_type: ReflectionType = "trace_review"
    metadata: dict[str, Any] = Field(default_factory=dict)

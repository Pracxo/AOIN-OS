"""Learning contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

LearningType = Literal[
    "retrieval_improvement_candidate",
    "planning_pattern_candidate",
    "policy_feedback_candidate",
    "capability_selection_candidate",
    "user_preference_candidate",
    "failure_pattern_candidate",
]


class LearningSignal(BaseModel):
    """Candidate learning signal that requires evaluation before promotion."""

    model_config = ConfigDict(extra="forbid")

    learning_id: str
    trace_id: str
    learning_type: LearningType
    signal: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    promotion_status: Literal["candidate"]
    created_at: datetime

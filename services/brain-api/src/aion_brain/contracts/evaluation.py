"""Evaluation contracts owned by AION Brain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationRecord(BaseModel):
    """Deterministic evaluation of a Brain decision trace."""

    model_config = ConfigDict(extra="forbid")

    evaluation_id: str
    trace_id: str
    scores: dict[str, float]
    lessons: list[str]
    created_at: datetime

    @field_validator("scores")
    @classmethod
    def scores_are_bounded(cls, value: dict[str, float]) -> dict[str, float]:
        """Ensure every deterministic score is between 0 and 1."""
        for score in value.values():
            if score < 0.0 or score > 1.0:
                raise ValueError("evaluation scores must be between 0 and 1")
        return value


class EvaluationRequest(BaseModel):
    """Request wrapper for future evaluation extension."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(min_length=1)

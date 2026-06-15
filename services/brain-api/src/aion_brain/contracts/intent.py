"""Intent contracts owned by AION Brain."""

from pydantic import BaseModel, ConfigDict, Field


class IntentFrame(BaseModel):
    """The Brain's interpretation of an event goal."""

    model_config = ConfigDict(extra="forbid")

    intent_id: str
    event_id: str
    intent_type: str
    goal: str
    urgency: str
    risk_level: str
    requires_memory: bool
    requires_capability: bool
    requires_approval: bool | None
    confidence: float = Field(ge=0.0, le=1.0)

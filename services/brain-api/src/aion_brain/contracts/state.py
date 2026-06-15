"""Brain runtime state contract owned by AION Brain."""

from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.planning import PlanGraph
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.reasoning import ReasoningResult
from aion_brain.contracts.traces import DecisionTrace


class BrainState(BaseModel):
    """Public state shape for deterministic Brain runtime transitions."""

    model_config = ConfigDict(extra="forbid")

    event: AIONEvent
    intent: IntentFrame | None = None
    context: ContextPacket | None = None
    reasoning: ReasoningResult | None = None
    plan: PlanGraph | None = None
    policy_decisions: list[PolicyDecision] = Field(default_factory=list)
    trace: DecisionTrace | None = None
    errors: list[str] = Field(default_factory=list)
    status: str

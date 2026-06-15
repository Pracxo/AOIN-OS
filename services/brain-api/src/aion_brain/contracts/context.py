"""Context contracts owned by AION Brain."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from aion_brain.contracts.attention import ContextBudget, ContextBudgetRequest


class ContextPacket(BaseModel):
    """Context gathered for an intent before planning."""

    model_config = ConfigDict(extra="forbid")

    context_id: str
    intent_id: str
    goal: str
    known_context: list[dict[str, Any]]
    retrieved_memory_ids: list[str]
    graph_node_ids: list[str] = []
    graph_edge_ids: list[str] = []
    available_capability_ids: list[str]
    constraints: list[str]
    open_questions: list[str]
    execution_limits: dict[str, Any]


__all__ = ["ContextBudget", "ContextBudgetRequest", "ContextPacket"]

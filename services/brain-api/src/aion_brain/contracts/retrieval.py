"""Retrieval and context fusion contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RetrievalSource = Literal[
    "lexical_memory",
    "semantic_memory",
    "graph_memory",
    "capability_registry",
    "skill_registry",
    "recent_trace",
    "evidence_vault",
    "working_memory",
    "belief_state",
    "entity_registry",
    "concept_registry",
    "situation_model",
    "temporal_state",
    "decision_journal",
    "learning_signal",
    "policy_constraint",
]


class RetrievalRequest(BaseModel):
    """Request for policy-gated multi-source retrieval."""

    model_config = ConfigDict(extra="forbid")

    retrieval_id: str = Field(min_length=1)
    trace_id: str | None
    intent_id: str | None
    query: str = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    requested_sources: list[RetrievalSource] = Field(min_length=1)
    memory_types: list[str] = Field(default_factory=list)
    capability_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    include_graph: bool = True
    include_capabilities: bool = True
    include_recent_traces: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedContextItem(BaseModel):
    """A normalized retrieval candidate selected for context."""

    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1)
    source: RetrievalSource
    source_id: str = Field(min_length=1)
    title: str | None
    content: str
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    sensitivity: str
    owner_scope: list[str] = Field(min_length=1)
    memory_type: str | None
    capability_id: str | None
    graph_node_ids: list[str]
    graph_edge_ids: list[str]
    trace_refs: list[str]
    evidence_ref: str | None
    metadata: dict[str, Any]


class RetrievalResult(BaseModel):
    """Result of RetrievalRouter candidate selection."""

    model_config = ConfigDict(extra="forbid")

    retrieval_id: str
    query: str
    items: list[RetrievedContextItem]
    source_counts: dict[str, int]
    constraints: list[str]
    created_at: datetime


class ContextFusionRequest(BaseModel):
    """Request for deterministic context fusion."""

    model_config = ConfigDict(extra="forbid")

    retrieval_result: RetrievalResult
    goal: str
    max_items: int = Field(default=10, ge=1, le=50)
    max_chars: int = Field(default=12000, ge=100, le=50000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextBundle(BaseModel):
    """Reasoning-ready bundle produced from retrieval results."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    retrieval_id: str
    goal: str
    items: list[RetrievedContextItem]
    fused_summary: str
    memory_refs: list[str]
    capability_refs: list[str]
    graph_node_refs: list[str]
    graph_edge_refs: list[str]
    trace_refs: list[str]
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str]
    token_budget_hint: int | None
    created_at: datetime

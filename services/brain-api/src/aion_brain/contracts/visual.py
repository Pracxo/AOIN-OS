"""Frontend-agnostic Visual Brain Projection contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BrainVisualNodeType = Literal[
    "event",
    "intent",
    "context",
    "memory",
    "graph",
    "evidence",
    "chunk",
    "claim",
    "retrieval",
    "reasoning",
    "model",
    "plan",
    "policy",
    "risk",
    "guardrail",
    "governance",
    "conflict",
    "compaction",
    "retention",
    "autonomy",
    "focus",
    "working_memory",
    "attention",
    "interrupt",
    "execution",
    "step",
    "approval",
    "capability",
    "module",
    "mcp",
    "server",
    "tool",
    "runtime",
    "goal",
    "task",
    "schedule",
    "due_item",
    "reminder",
    "scheduler_tick",
    "schedule_policy",
    "scheduler_report",
    "reflection",
    "candidate",
    "skill",
    "actor",
    "workspace",
    "permission",
    "scope",
    "evaluation",
    "learning",
    "trace",
    "telemetry",
    "snapshot",
    "replay",
    "regression",
    "eval",
    "kernel",
    "service",
    "adapter",
    "index",
    "episode",
    "diagnostic",
    "contract",
    "interface",
    "contract_snapshot",
    "compatibility_rule",
    "compatibility_scan",
    "interface_drift",
    "migration_note",
    "contract_report",
    "extension",
    "extension_package",
    "extension_manifest",
    "extension_capability",
    "extension_dependency",
    "extension_compatibility",
    "extension_review",
    "extension_install_plan",
    "module_slot",
    "capability_binding",
    "binding_conflict",
    "binding_validation",
    "module_mount_plan",
    "route_binding_preview",
    "conformance_profile",
    "test_vector",
    "mock_invocation",
    "conformance_run",
    "conformance_finding",
    "readiness_assessment",
    "provider",
    "profile",
    "delegation",
    "run_level",
    "cycle",
    "cycle_step",
    "consolidation",
    "maintenance",
    "budget",
    "prompt",
    "prompt_template",
    "prompt_fragment",
    "prompt_packet",
    "prompt_boundary",
    "prompt_injection",
    "model_input",
    "model_output",
    "output_segment",
    "structured_validation",
    "response_candidate",
    "tool_intent",
    "output_governance",
    "action_proposal",
    "action_blocker",
    "action_review",
    "execution_handoff",
    "tool_intent_review",
    "run_supervision",
    "run_status_sample",
    "run_control",
    "timeout_policy",
    "compensation_plan",
    "compensation_step",
    "supervision_report",
    "notification",
    "notification_topic",
    "notification_subscription",
    "alert",
    "escalation",
    "digest",
    "workflow",
    "workflow_run",
    "workflow_step",
    "worker",
    "scheduler",
    "temporal",
    "event_router",
    "subscription",
    "dispatch",
    "reaction",
    "dead_letter",
    "command",
    "idempotency",
    "outbox",
    "inbox",
    "lease",
    "consistency",
    "api",
    "request",
    "error",
    "scenario",
    "scenario_step",
    "fixture",
    "release_baseline",
    "version",
    "feature",
    "compatibility",
    "migration",
    "release_artifact",
    "freeze",
    "sdk",
    "release_package",
    "backup",
    "backup_file",
    "restore",
    "restore_preview",
    "performance",
    "benchmark",
    "baseline",
    "budget",
    "regression",
    "checksum",
    "sbom",
    "handoff",
    "source_manifest",
    "instruction",
    "preference",
    "constraint",
    "style_profile",
    "instruction_conflict",
    "instruction_resolution",
    "security",
    "threat",
    "control",
    "finding",
    "hardening",
    "config",
    "feature_flag",
    "config_snapshot",
    "config_validation",
    "dependency",
    "retry_policy",
    "circuit_breaker",
    "degraded_mode",
    "fault_rule",
    "resilience",
    "config_drift",
    "dialogue",
    "message",
    "clarification",
    "response",
    "feedback",
    "explanation",
    "trace_narrative",
    "why_not",
    "explanation_feedback",
    "belief",
    "contradiction",
    "truth_maintenance",
    "concept",
    "entity",
    "mention",
    "reference",
    "resolution",
    "merge",
    "split",
    "unknown",
]

BrainVisualStatus = Literal[
    "active",
    "dormant",
    "blocked",
    "completed",
    "failed",
    "unknown",
]

BrainVisualEdgeType = Literal[
    "triggered",
    "classified_as",
    "compiled_into",
    "retrieved",
    "grounded_by",
    "reasoned_over",
    "planned",
    "authorized_by",
    "blocked_by",
    "executed_as",
    "evaluated_by",
    "learned_from",
    "reflected_into",
    "promoted_to",
    "linked_to",
    "activated",
    "related_to",
    "emitted",
]

BrainVisualClusterType = Literal[
    "trace",
    "memory",
    "reasoning",
    "execution",
    "evidence",
    "learning",
    "identity",
    "capability",
    "lifecycle",
    "mixed",
]


class BrainVisualNode(BaseModel):
    """A frontend-independent node in a projected Brain Map."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    node_type: BrainVisualNodeType
    label: str = Field(min_length=1)
    status: BrainVisualStatus
    intensity: float = Field(ge=0.0, le=1.0)
    owner_scope: list[str] = Field(min_length=1)
    trace_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class BrainVisualEdge(BaseModel):
    """A typed relation in a projected Brain Map."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1)
    edge_type: BrainVisualEdgeType
    from_node_id: str = Field(min_length=1)
    to_node_id: str = Field(min_length=1)
    weight: float = Field(ge=0.0, le=1.0)
    status: BrainVisualStatus
    trace_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None

    @model_validator(mode="after")
    def reject_self_edge(self) -> "BrainVisualEdge":
        """Reject relations that point back to the same node."""
        if self.from_node_id == self.to_node_id:
            raise ValueError("from_node_id cannot equal to_node_id")
        return self


class BrainPulse(BaseModel):
    """A short-lived visual activity signal."""

    model_config = ConfigDict(extra="forbid")

    pulse_id: str = Field(min_length=1)
    trace_id: str | None = None
    event_type: str = Field(min_length=1)
    node_id: str | None = None
    edge_id: str | None = None
    intensity: float = Field(ge=0.0, le=1.0)
    duration_ms: int = Field(ge=100, le=10000)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @model_validator(mode="after")
    def require_target(self) -> "BrainPulse":
        """Require a node or edge target."""
        if self.node_id is None and self.edge_id is None:
            raise ValueError("node_id or edge_id must be present")
        return self


class BrainVisualCluster(BaseModel):
    """A deterministic family grouping of visual nodes."""

    model_config = ConfigDict(extra="forbid")

    cluster_id: str = Field(min_length=1)
    cluster_type: BrainVisualClusterType
    label: str = Field(min_length=1)
    node_ids: list[str]
    intensity: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrainMapRequest(BaseModel):
    """Request to project telemetry into a Brain Map."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    workspace_id: str | None = None
    scope: list[str] = Field(min_length=1)
    node_types: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    since: datetime | None = None
    until: datetime | None = None
    limit: int = Field(default=500, ge=1, le=5000)
    include_edges: bool = True
    include_pulses: bool = True
    include_clusters: bool = True
    decay: bool = True

    @model_validator(mode="after")
    def validate_time_range(self) -> "BrainMapRequest":
        """Require a chronological time range."""
        if self.since is not None and self.until is not None and self.since >= self.until:
            raise ValueError("since must be before until")
        return self


class BrainMap(BaseModel):
    """Projected visual form of Brain telemetry."""

    model_config = ConfigDict(extra="forbid")

    map_id: str
    trace_id: str | None
    workspace_id: str | None
    nodes: list[BrainVisualNode]
    edges: list[BrainVisualEdge]
    pulses: list[BrainPulse]
    clusters: list[BrainVisualCluster]
    stats: dict[str, Any]
    created_at: datetime


class BrainMapSnapshot(BaseModel):
    """Persisted Brain Map snapshot."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    trace_id: str | None
    workspace_id: str | None
    owner_scope: list[str] = Field(min_length=1)
    map: BrainMap
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    pulse_count: int = Field(ge=0)
    created_at: datetime | None = None


class VisualTelemetryQuery(BaseModel):
    """Query for canonical visual telemetry events."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    workspace_id: str | None = None
    scope: list[str] = Field(min_length=1)
    event_types: list[str] = Field(default_factory=list)
    node_types: list[str] = Field(default_factory=list)
    since: datetime | None = None
    until: datetime | None = None
    limit: int = Field(default=250, ge=1, le=1000)

    @model_validator(mode="after")
    def validate_time_range(self) -> "VisualTelemetryQuery":
        """Require a chronological time range."""
        if self.since is not None and self.until is not None and self.since >= self.until:
            raise ValueError("since must be before until")
        return self


class TraceTimelineRequest(BaseModel):
    """Request for a trace timeline projection."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    include_telemetry: bool = True
    include_policy: bool = True
    include_reasoning: bool = True
    include_execution: bool = True
    include_evaluation: bool = True
    include_learning: bool = True


class TraceTimelineEvent(BaseModel):
    """A normalized event in a trace timeline."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    trace_id: str
    event_type: str
    component: str
    title: str
    timestamp: datetime
    status: BrainVisualStatus
    payload: dict[str, Any]


class TraceTimeline(BaseModel):
    """Ordered projection of a Brain trace."""

    model_config = ConfigDict(extra="forbid")

    timeline_id: str
    trace_id: str
    owner_scope: list[str] = Field(min_length=1)
    events: list[TraceTimelineEvent]
    duration_ms: int | None
    status: BrainVisualStatus
    created_at: datetime

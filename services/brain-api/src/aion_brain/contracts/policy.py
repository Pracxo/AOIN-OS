"""Policy contracts owned by AION Brain."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class PolicyRequest(BaseModel):
    """Generic authorization request for a Brain action."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    trace_id: str | None
    actor_id: str | None
    workspace_id: str | None
    action_type: str
    resource_type: str
    resource_id: str | None
    risk_level: str
    approval_present: bool
    requested_permissions: list[str]
    security_scope: list[str]
    context: dict[str, Any]


class PolicyDecision(BaseModel):
    """Authorization result for a plan or action."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str
    trace_id: str
    allow: bool
    approval_required: bool
    reason: str
    constraints: list[str]
    audit_level: str

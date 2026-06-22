"""Shared fakes for autonomy tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.autonomy.repository import AutonomyRepository
from aion_brain.config import Settings
from aion_brain.contracts.autonomy import AutonomyDecision, AutonomyDecisionRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest


class AllowPolicy:
    """Always-allow fake policy adapter."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        """Record and allow or deny one policy request."""
        self.requests.append(request)
        allow = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["blocked"],
            audit_level="standard" if allow else "high",
        )


class FakeAutonomyGovernor:
    """Autonomy governor fake returning a fixed decision."""

    def __init__(self, *, allow: bool = True, resolved_mode: str = "dry_run") -> None:
        self.allow = allow
        self.resolved_mode = resolved_mode
        self.requests: list[AutonomyDecisionRequest] = []

    def decide(self, request: AutonomyDecisionRequest) -> AutonomyDecision:
        """Record and return one autonomy decision."""
        self.requests.append(request)
        return autonomy_decision(
            request,
            allow=self.allow,
            resolved_mode=self.resolved_mode,
        )


def autonomy_decision(
    request: AutonomyDecisionRequest,
    *,
    allow: bool = True,
    resolved_mode: str = "dry_run",
) -> AutonomyDecision:
    """Create a persisted autonomy decision contract."""
    return AutonomyDecision(
        autonomy_decision_id=request.autonomy_decision_id or "autonomy-decision-1",
        trace_id=request.trace_id,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        requested_mode=request.requested_mode,
        resolved_mode=resolved_mode,  # type: ignore[arg-type]
        action_type=request.action_type,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        risk_level=request.risk_level,
        allow=allow,
        approval_required=not allow,
        delegation_id=request.delegation_id,
        autonomy_profile_id=None,
        run_level_id=None,
        reason="autonomy_allowed" if allow else "autonomy_denied",
        constraints=[] if allow else ["blocked_by_autonomy"],
        metadata=request.metadata,
        created_at=datetime.now(UTC),
    )


def autonomy_repository() -> AutonomyRepository:
    """Create an in-memory autonomy repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return AutonomyRepository(engine=engine)


def make_test_settings(**overrides: object) -> Settings:
    """Return Settings configured for local tests."""
    values = {
        "_env_file": None,
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "AION_DEFAULT_SEMANTIC_ADAPTER": "in_memory",
        "AION_GRAPH_MEMORY_ADAPTER": "in_memory",
        **overrides,
    }
    return Settings(**values)

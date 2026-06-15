"""Visual telemetry query service tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import VisualTelemetryQuery
from aion_brain.visual.service import VisualPolicyDenied, VisualTelemetryQueryService


class FakePolicy:
    """Policy fake that records requests."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeRepository:
    """Telemetry repository fake."""

    def query_telemetry(self, query: VisualTelemetryQuery) -> list[VisualTelemetryEvent]:
        return [telemetry()]


def test_visual_telemetry_query_service_calls_policy() -> None:
    """Telemetry reads pass through the generic policy boundary."""
    policy = FakePolicy()
    service = VisualTelemetryQueryService(FakeRepository(), policy, actor_context())

    assert service.query(VisualTelemetryQuery(scope=["workspace:main"]))
    assert policy.requests[0].action_type == "visual.telemetry.read"


def test_policy_deny_blocks_visual_telemetry_query() -> None:
    """Telemetry reads fail closed."""
    service = VisualTelemetryQueryService(FakeRepository(), FakePolicy(False), actor_context())
    with pytest.raises(VisualPolicyDenied):
        service.query(VisualTelemetryQuery(scope=["workspace:main"]))


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["telemetry.read"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )


def telemetry() -> VisualTelemetryEvent:
    return VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        trace_id="trace-1",
        event_type="brain_loop_started",
        node_type="event",
        node_id="event-1",
        edge_from=None,
        edge_to=None,
        intensity=0.5,
        payload={},
        created_at=datetime.now(UTC),
    )

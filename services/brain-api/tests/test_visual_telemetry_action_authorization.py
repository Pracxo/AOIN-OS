from __future__ import annotations

from aion_brain.action_authorization import (
    ActionAuthorizationAuditService,
    DryRunActionAuthorizationService,
)
from aion_brain.contracts.action_authorization import (
    ActionAuthorizationAuditRequest,
    DryRunActionAuthorizationRequest,
)
from tests.operator_action_fakes import AllowPolicy, FakeTelemetry


def test_visual_telemetry_emits_action_authorization_events() -> None:
    telemetry = FakeTelemetry()
    service = DryRunActionAuthorizationService(
        policy_adapter=AllowPolicy(),
        telemetry_service=telemetry,
    )
    audit = ActionAuthorizationAuditService(telemetry_service=telemetry)

    service.authorize(
        DryRunActionAuthorizationRequest(
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
            action_key="operator.review",
            action_type="generic",
            target_type="generic",
        )
    )
    audit.audit(ActionAuthorizationAuditRequest(owner_scope=["workspace:main"]))

    event_types = {getattr(event, "event_type", None) for event in telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in telemetry.events}
    assert "dry_run_action_authorization_decided" in event_types
    assert "action_authorization_audit_completed" in event_types
    assert "action_authorization_decision" in node_types
    assert "action_authorization_audit" in node_types

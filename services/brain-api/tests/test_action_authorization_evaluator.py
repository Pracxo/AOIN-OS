from __future__ import annotations

from aion_brain.action_authorization import DryRunActionAuthorizationService
from aion_brain.contracts.action_authorization import DryRunActionAuthorizationRequest
from tests.operator_action_fakes import AllowPolicy, DenyPolicy


def _request(**overrides: object) -> DryRunActionAuthorizationRequest:
    payload: dict[str, object] = {
        "actor_id": "local.operator",
        "workspace_id": "local",
        "roles": ["operator"],
        "owner_scope": ["workspace:main"],
        "action_key": "operator.review",
        "action_type": "generic",
        "target_type": "generic",
        "requested_operation": "preview",
    }
    payload.update(overrides)
    return DryRunActionAuthorizationRequest(**payload)


def test_operator_can_request_allowed_dry_run_preview() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())

    decision = service.authorize(_request())

    assert decision.status == "allowed"
    assert decision.decision == "allow_dry_run_preview"
    assert decision.role_allowed is True


def test_reviewer_can_create_review_authorization() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())

    decision = service.authorize(_request(roles=["reviewer"], requested_operation="review"))

    assert decision.status == "allowed"
    assert decision.decision == "allow_review_record"


def test_restricted_roles_and_unknown_roles_are_denied() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())

    viewer = service.authorize(_request(roles=["viewer"]))
    auditor = service.authorize(_request(roles=["auditor"]))
    unknown = service.authorize(_request(roles=["mystery"]))

    assert viewer.role_allowed is False
    assert auditor.role_allowed is False
    assert unknown.role_allowed is False
    assert {viewer.status, auditor.status, unknown.status} == {"blocked"}


def test_unknown_action_type_is_denied() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())

    decision = service.authorize(_request(action_type="unknown_type"))

    assert decision.status == "blocked"
    assert decision.decision == "unsupported"


def test_policy_denial_blocks_decision() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=DenyPolicy())

    decision = service.authorize(_request())

    assert decision.policy_allowed is False
    assert decision.status == "blocked"
    assert any(item["blocker_type"] == "policy_denied" for item in decision.blockers)


def test_session_boundary_denial_blocks_decision() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())

    decision = service.authorize(_request(metadata={"session_allowed": False}))

    assert decision.session_allowed is False
    assert any(item["blocker_type"] == "session_denied" for item in decision.blockers)

from __future__ import annotations

from aion_brain.action_authorization import DryRunActionAuthorizationService
from aion_brain.contracts.action_authorization import DryRunActionAuthorizationRequest
from tests.operator_action_fakes import AllowPolicy


def _decision_for_metadata(metadata: dict[str, object]) -> list[str]:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())
    request = DryRunActionAuthorizationRequest(
        actor_id="local.operator",
        workspace_id="local",
        roles=["operator"],
        owner_scope=["workspace:main"],
        action_key="operator.review",
        action_type="generic",
        target_type="generic",
        metadata=metadata,
    )
    return [str(item["blocker_type"]) for item in service.authorize(request).blockers]


def test_unsafe_payload_creates_blocker() -> None:
    blocker_types = _decision_for_metadata({"request_payload_findings": [{"code": "unsafe"}]})

    assert "unsafe_payload" in blocker_types


def test_raw_prompt_creates_blocker() -> None:
    blocker_types = _decision_for_metadata({"notes": "raw prompt: protected"})

    assert "raw_prompt_detected" in blocker_types


def test_hidden_reasoning_creates_blocker() -> None:
    blocker_types = _decision_for_metadata({"notes": "hidden reasoning: protected"})

    assert "hidden_reasoning_detected" in blocker_types

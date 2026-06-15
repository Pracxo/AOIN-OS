"""Outbox retry policy integration tests."""

from __future__ import annotations

from aion_brain.contracts.outbox import OutboxProcessRequest
from tests.test_outbox_service import make_service, publish_request


def test_outbox_uses_retry_policy_delay_for_failed_delivery() -> None:
    service = make_service(outbox_process_enabled=True)
    service.set_retry_policy_service(FakeRetryPolicyService())
    service.enqueue(publish_request(destination="webhook_placeholder"))

    result = service.process_once(OutboxProcessRequest(dry_run=False))

    assert result.failed == 1
    assert result.messages[0].next_attempt_at is not None
    assert result.messages[0].last_error["reason"] == "webhook_placeholder_disabled"


class FakePolicy:
    name = "outbox"


class FakeRetryPolicyService:
    def policy_for_target(self, target_type: str) -> object | None:
        return FakePolicy() if target_type == "outbox" else None

    def compute_delay_ms(self, policy: object, attempt: int) -> int:
        return 250

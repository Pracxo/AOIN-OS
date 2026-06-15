"""Command bus retry policy integration tests."""

from __future__ import annotations

from tests.test_command_bus import make_bus


def test_command_bus_exposes_retry_metadata_without_auto_retry() -> None:
    bus, *_ = make_bus()
    bus.set_retry_policy_service(FakeRetryPolicyService())

    metadata = bus.retry_metadata(1, "failed")

    assert metadata == {
        "retry_configured": True,
        "policy": "command",
        "should_retry": True,
        "delay_ms": 123,
    }


class FakePolicy:
    name = "command"


class FakeRetryPolicyService:
    def policy_for_target(self, target_type: str) -> object | None:
        return FakePolicy() if target_type == "command" else None

    def compute_delay_ms(self, policy: object, attempt: int) -> int:
        return 123

    def should_retry(self, policy: object, status: str, attempt: int) -> bool:
        return status == "failed" and attempt < 3

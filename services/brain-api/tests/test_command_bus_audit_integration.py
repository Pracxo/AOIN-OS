"""Command Bus audit integration tests."""

from __future__ import annotations

from tests.test_command_bus import make_bus, request


class FakeAuditSink:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def record(self, audit_request: object) -> object:
        self.requests.append(audit_request)
        return audit_request


def test_command_bus_records_audit_entry() -> None:
    sink = FakeAuditSink()
    bus, _policy, _autonomy, _approval = make_bus()
    bus.set_audit_sink(sink)

    bus.dispatch(request())

    assert any(item.event_type == "command_created" for item in sink.requests)
    assert any(item.event_type == "command_completed" for item in sink.requests)

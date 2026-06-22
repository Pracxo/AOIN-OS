"""Action proposal audit and provenance integration tests."""

from __future__ import annotations

from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, proposal_request


class FakeAuditSink:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record_event(self, event: dict[str, object]) -> None:
        self.events.append(event)


class FakeProvenance:
    def __init__(self) -> None:
        self.links: list[tuple[str, str, str]] = []

    def record_link(self, source_id: str, target_id: str, relation_type: str) -> None:
        self.links.append((source_id, target_id, relation_type))


def test_audit_and_provenance_record_proposal_and_handoff() -> None:
    fixture = ActionFixture()
    audit = FakeAuditSink()
    provenance = FakeProvenance()
    fixture.proposals._audit_sink = audit  # type: ignore[attr-defined]
    fixture.proposals._provenance_service = provenance  # type: ignore[attr-defined]
    fixture.handoffs._audit_sink = audit  # type: ignore[attr-defined]
    fixture.handoffs._provenance_service = provenance  # type: ignore[attr-defined]

    proposal = fixture.proposals.create_proposal(proposal_request())
    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="dry_run",
            target_system="noop",
        )
    )

    assert {event["event_type"] for event in audit.events} >= {
        "action_proposal_created",
        "execution_handoff_created",
    }
    assert (proposal.action_proposal_id, handoff.execution_handoff_id, "handed_off_as") in (
        provenance.links
    )

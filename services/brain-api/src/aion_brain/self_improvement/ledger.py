"""Thread-safe in-memory ledger for governed self-improvement evidence."""

from __future__ import annotations

from threading import RLock

from aion_brain.contracts.self_improvement import (
    ImprovementAuditEvent,
    ImprovementGovernanceDecision,
    ImprovementProposalRef,
    ImprovementProvenanceRecord,
)


class SelfImprovementLedger:
    """In-memory ledger used by the governance plane and tests.

    This object deliberately does not write files, mutate Git state, open PRs, or call
    production services.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._proposals: dict[str, ImprovementProposalRef] = {}
        self._decisions: dict[str, ImprovementGovernanceDecision] = {}
        self._events: list[ImprovementAuditEvent] = []
        self._provenance: list[ImprovementProvenanceRecord] = []

    def record_proposal(self, proposal: ImprovementProposalRef) -> ImprovementProposalRef:
        """Record or replace a proposal reference."""

        with self._lock:
            self._proposals[proposal.proposal_id] = proposal
            return proposal

    def record_decision(
        self,
        decision: ImprovementGovernanceDecision,
    ) -> ImprovementGovernanceDecision:
        """Record the latest governance decision for a proposal."""

        with self._lock:
            self._decisions[decision.proposal.proposal_id] = decision
            return decision

    def append_event(self, event: ImprovementAuditEvent) -> ImprovementAuditEvent:
        """Append an immutable audit event."""

        with self._lock:
            self._events.append(event)
            return event

    def append_provenance(
        self,
        record: ImprovementProvenanceRecord,
    ) -> ImprovementProvenanceRecord:
        """Append an immutable provenance record."""

        with self._lock:
            self._provenance.append(record)
            return record

    def get_proposal(self, proposal_id: str) -> ImprovementProposalRef | None:
        """Return a proposal reference by ID."""

        with self._lock:
            return self._proposals.get(proposal_id)

    def get_decision(self, proposal_id: str) -> ImprovementGovernanceDecision | None:
        """Return the latest governance decision for a proposal."""

        with self._lock:
            return self._decisions.get(proposal_id)

    def list_events(self, proposal_id: str | None = None) -> tuple[ImprovementAuditEvent, ...]:
        """Return an immutable audit-event snapshot."""

        with self._lock:
            events = tuple(self._events)
        if proposal_id is None:
            return events
        return tuple(event for event in events if event.proposal_id == proposal_id)

    def list_provenance(
        self,
        proposal_id: str | None = None,
    ) -> tuple[ImprovementProvenanceRecord, ...]:
        """Return an immutable provenance snapshot."""

        with self._lock:
            records = tuple(self._provenance)
        if proposal_id is None:
            return records
        return tuple(record for record in records if record.proposal_id == proposal_id)


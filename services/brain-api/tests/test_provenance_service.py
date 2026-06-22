"""Provenance service tests."""

from __future__ import annotations

import pytest

from aion_brain.audit_integrity.provenance import ProvenanceService
from aion_brain.contracts.audit_integrity import ProvenanceLink
from tests.audit_integrity_fakes import AllowPolicy, DenyPolicy, repository


def test_provenance_service_creates_link_through_policy() -> None:
    repo = repository()
    policy = AllowPolicy()
    service = ProvenanceService(repo, policy)

    link = service.create_link(_link())

    assert link.provenance_link_id == "prov-1"
    assert policy.requests[0].action_type == "audit.provenance.write"


def test_policy_deny_blocks_provenance_write() -> None:
    service = ProvenanceService(repository(), DenyPolicy())

    with pytest.raises(PermissionError):
        service.create_link(_link())


def test_provenance_service_soft_deletes_link() -> None:
    repo = repository()
    service = ProvenanceService(repo, AllowPolicy())
    service.create_link(_link())

    assert service.soft_delete_link("prov-1", "actor-1", "correction") is True
    assert service.list_links() == []


def _link() -> ProvenanceLink:
    return ProvenanceLink(
        provenance_link_id="prov-1",
        trace_id="trace-1",
        source_type="event",
        source_id="event-1",
        target_type="command",
        target_id="command-1",
        relation_type="caused",
        confidence=0.9,
    )

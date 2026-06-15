"""Evidence link tests."""

from tests.test_evidence_service import make_ingest_request, make_link, make_service


def test_evidence_link_stores_relation_to_target() -> None:
    """Evidence links connect source material to Brain targets."""
    service = make_service()
    service.ingest(make_ingest_request())

    link = service.link(make_link())

    assert link.evidence_id == "evidence-1"
    assert service.list_links("evidence-1", ["workspace:main"])[0].target_id == "memory-1"

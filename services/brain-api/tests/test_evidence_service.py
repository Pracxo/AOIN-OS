"""Evidence service tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.evidence import (
    EvidenceChunk,
    EvidenceIngestRequest,
    EvidenceLink,
    EvidenceRecord,
    GroundingClaim,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.evidence.service import EvidencePolicyDenied, EvidenceService


class FakePolicyAdapter:
    """Policy fake."""

    def __init__(self, *, deny: bool = False) -> None:
        self.deny = deny
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=not self.deny,
            approval_required=False,
            reason="allowed" if not self.deny else "denied",
            constraints=[] if not self.deny else ["blocked"],
            audit_level="standard",
        )


class FakeTelemetryService:
    """Visual telemetry fake."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


class FakeEvidenceRepository:
    """In-memory evidence repository fake."""

    def __init__(self) -> None:
        self.records: dict[str, EvidenceRecord] = {}
        self.chunks: dict[str, list[EvidenceChunk]] = {}
        self.links: dict[str, EvidenceLink] = {}
        self.claims: dict[str, GroundingClaim] = {}

    def save_evidence(self, evidence: EvidenceRecord) -> EvidenceRecord:
        self.records[evidence.evidence_id] = evidence
        return evidence

    def save_chunks(self, chunks: list[EvidenceChunk]) -> list[EvidenceChunk]:
        for chunk in chunks:
            self.chunks.setdefault(chunk.evidence_id, []).append(chunk)
        return chunks

    def get_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        record = self.records.get(evidence_id)
        if record is None or record.deleted_at is not None:
            return None
        return record

    def list_evidence(
        self,
        scope: list[str],
        *,
        source_types: list[str] | None = None,
        limit: int = 500,
    ) -> list[EvidenceRecord]:
        allowed = set(source_types or [])
        return [
            record
            for record in self.records.values()
            if record.deleted_at is None
            and set(record.owner_scope).intersection(scope)
            and (not allowed or record.source_type in allowed)
        ][:limit]

    def get_chunks(self, evidence_id: str) -> list[EvidenceChunk]:
        return [
            chunk
            for chunk in self.chunks.get(evidence_id, [])
            if chunk.deleted_at is None
        ]

    def save_link(self, link: EvidenceLink) -> EvidenceLink:
        self.links[link.link_id] = link
        return link

    def list_links(self, evidence_id: str) -> list[EvidenceLink]:
        return [
            link
            for link in self.links.values()
            if link.evidence_id == evidence_id and link.deleted_at is None
        ]

    def list_links_for_evidence_ids(
        self,
        evidence_ids: list[str],
        *,
        relation_type: str | None = None,
    ) -> list[EvidenceLink]:
        return [
            link
            for link in self.links.values()
            if link.evidence_id in evidence_ids
            and link.deleted_at is None
            and (relation_type is None or link.relation_type == relation_type)
        ]

    def save_grounding_claim(self, claim: GroundingClaim) -> GroundingClaim:
        self.claims[claim.claim_id] = claim
        return claim

    def soft_delete_evidence(self, evidence_id: str) -> bool:
        record = self.records.get(evidence_id)
        if record is None or record.deleted_at is not None:
            return False
        self.records[evidence_id] = record.model_copy(update={"deleted_at": datetime.now(UTC)})
        return True


def test_evidence_service_calls_policy_before_ingest() -> None:
    """Evidence ingestion is policy-gated."""
    policy = FakePolicyAdapter()
    service = make_service(policy=policy)

    service.ingest(make_ingest_request())

    assert policy.requests[0].action_type == "evidence.create"


def test_policy_deny_blocks_evidence_ingest() -> None:
    """Policy denial blocks ingestion."""
    service = make_service(policy=FakePolicyAdapter(deny=True))

    with pytest.raises(EvidencePolicyDenied):
        service.ingest(make_ingest_request())


def test_evidence_service_ingests_text_and_creates_chunks() -> None:
    """Text ingestion creates evidence and chunks."""
    repository = FakeEvidenceRepository()
    telemetry = FakeTelemetryService()
    service = make_service(repository=repository, telemetry=telemetry)

    response = service.ingest(make_ingest_request(content_text="alpha beta " * 120))

    assert response.ingested is True
    assert response.chunk_count >= 1
    assert response.evidence.content_ref == "evidence://evidence-1"
    assert repository.chunks["evidence-1"]
    assert "evidence_created" in [event.event_type for event in telemetry.events]


def test_evidence_service_stores_metadata_only_content_ref_without_fetching() -> None:
    """Metadata-only refs are stored without fetching content."""
    repository = FakeEvidenceRepository()
    service = make_service(repository=repository)

    response = service.ingest(
        make_ingest_request(content_text=None, content_ref="url-metadata://example")
    )

    assert response.chunk_count == 0
    assert response.evidence.content_ref == "url-metadata://example"
    assert repository.chunks == {}


def test_evidence_soft_delete_excludes_record_from_access() -> None:
    """Soft-deleted evidence is hidden from subsequent reads."""
    service = make_service()
    service.ingest(make_ingest_request())

    deleted = service.soft_delete("evidence-1", ["workspace:main"])

    assert deleted is True
    assert service.get_evidence("evidence-1", ["workspace:main"]) is None


def make_service(
    *,
    repository: FakeEvidenceRepository | None = None,
    policy: FakePolicyAdapter | None = None,
    telemetry: FakeTelemetryService | None = None,
) -> EvidenceService:
    """Create an evidence service fake."""
    return EvidenceService(
        evidence_repository=repository or FakeEvidenceRepository(),
        policy_adapter=policy or FakePolicyAdapter(),
        telemetry_service=telemetry,
        actor_context=make_actor_context(),
    )


def make_actor_context() -> ActorContext:
    """Create a dev actor context."""
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["evidence.restricted.read"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )


def make_ingest_request(
    *,
    content_text: str | None = "alpha beta gamma",
    content_ref: str | None = None,
    source_type: str = "text",
    owner_scope: list[str] | None = None,
) -> EvidenceIngestRequest:
    """Create an evidence ingest request."""
    return EvidenceIngestRequest(
        evidence_id="evidence-1",
        trace_id="trace-1",
        source_type=source_type,  # type: ignore[arg-type]
        source_ref=None,
        owner_scope=owner_scope or ["workspace:main"],
        title="Alpha Evidence",
        content_text=content_text,
        summary=None,
        content_ref=content_ref,
        media_type="text/plain",
        sensitivity="internal",
        confidence=0.9,
        metadata={},
        chunk_size_chars=500,
        chunk_overlap_chars=50,
    )


def make_link(
    *,
    evidence_id: str = "evidence-1",
    relation_type: str = "supports",
) -> EvidenceLink:
    """Create an evidence link."""
    return EvidenceLink(
        link_id="link-1",
        evidence_id=evidence_id,
        target_type="memory",
        target_id="memory-1",
        relation_type=relation_type,  # type: ignore[arg-type]
        trace_id="trace-1",
        confidence=0.8,
        metadata={},
        created_at=datetime.now(UTC),
        deleted_at=None,
    )


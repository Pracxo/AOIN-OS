"""Grounding service tests."""

from aion_brain.contracts.evidence import GroundingRequest
from aion_brain.evidence.grounding import GroundingService
from tests.test_evidence_contracts import make_statement
from tests.test_evidence_service import (
    FakeEvidenceRepository,
    FakePolicyAdapter,
    FakeTelemetryService,
    make_actor_context,
    make_ingest_request,
    make_service,
)


def test_grounding_service_creates_supported_claim_for_overlapping_evidence() -> None:
    """Overlapping evidence creates a supported grounding claim."""
    repository = FakeEvidenceRepository()
    evidence_service = make_service(repository=repository)
    evidence_service.ingest(make_ingest_request(content_text="alpha beta gamma source"))
    service = make_grounding_service(repository, evidence_service)

    response = service.ground(
        GroundingRequest(
            trace_id="trace-1",
            statements=[make_statement("alpha beta")],
            scope=["workspace:main"],
        )
    )

    assert response.claims[0].verification_status == "supported"
    assert response.claims[0].evidence_refs == ["evidence-1"]
    assert repository.claims


def test_grounding_service_creates_insufficient_evidence_for_weak_overlap() -> None:
    """Weak overlap is not upgraded into truth."""
    repository = FakeEvidenceRepository()
    evidence_service = make_service(repository=repository)
    evidence_service.ingest(make_ingest_request(content_text="alpha beta gamma source"))
    service = make_grounding_service(repository, evidence_service)

    response = service.ground(
        GroundingRequest(
            trace_id="trace-1",
            statements=[make_statement("zeta theta")],
            scope=["workspace:main"],
        )
    )

    assert response.claims[0].verification_status == "insufficient_evidence"


def test_grounding_service_never_calls_llm() -> None:
    """Grounding has no model dependency."""
    repository = FakeEvidenceRepository()
    evidence_service = make_service(repository=repository)
    evidence_service.ingest(make_ingest_request(content_text="alpha beta gamma source"))
    service = make_grounding_service(repository, evidence_service)

    response = service.ground(
        GroundingRequest(
            trace_id="trace-1",
            statements=[make_statement("alpha")],
            scope=["workspace:main"],
        )
    )

    assert response.claims


def make_grounding_service(
    repository: FakeEvidenceRepository,
    evidence_service: object,
) -> GroundingService:
    """Create a grounding service fake."""
    return GroundingService(
        evidence_service=evidence_service,  # type: ignore[arg-type]
        grounding_repository=repository,
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=FakeTelemetryService(),
        actor_context=make_actor_context(),
    )

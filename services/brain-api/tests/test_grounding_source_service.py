from __future__ import annotations

from types import SimpleNamespace

from aion_brain.contracts.grounding import GroundingSourceCreateRequest
from tests.grounding_helpers import service_bundle


class FakeEvidenceService:
    def get_evidence(self, evidence_id: str, scope: list[str]) -> object:
        return SimpleNamespace(
            evidence_id=evidence_id,
            trace_id="trace-1",
            title="Evidence",
            summary="AION records deterministic source support.",
            content_hash="hash-1",
            sensitivity="internal",
            source_type="text",
            source_ref=None,
        )


class FakeMemoryService:
    def get(self, memory_id: str) -> object:
        return SimpleNamespace(
            memory_id=memory_id,
            memory_type="semantic",
            summary="AION recalls deterministic source support.",
            sensitivity="internal",
            source_event_id="event-1",
        )


class FakeBeliefService:
    def __init__(self, status: str = "supported") -> None:
        self.status = status

    def get_claim(self, claim_id: str, scope: list[str]) -> object:
        return SimpleNamespace(
            claim_id=claim_id,
            trace_id="trace-1",
            claim_text="AION records deterministic source support.",
            claim_hash="hash-claim",
            sensitivity="internal",
            status=self.status,
            evidence_refs=["evidence-1"],
            memory_refs=[],
        )


def test_grounding_source_service_create_and_builders() -> None:
    bundle = service_bundle()
    bundle.source_service._evidence_service = FakeEvidenceService()
    bundle.source_service._memory_service = FakeMemoryService()
    bundle.source_service._belief_service = FakeBeliefService()

    created = bundle.source_service.create_source(
        GroundingSourceCreateRequest(
            source_type="generic",
            source_id="generic-1",
            title="Generic",
            summary="AION records deterministic source support.",
            owner_scope=["workspace:main"],
        )
    )
    evidence = bundle.source_service.build_from_evidence("evidence-1", ["workspace:main"])
    memory = bundle.source_service.build_from_memory("memory-1", ["workspace:main"])
    belief = bundle.source_service.build_from_belief("claim-1", ["workspace:main"])

    assert created.grounding_source_id
    assert evidence.trust_level == "primary"
    assert memory.trust_level == "memory_recall"
    assert belief.trust_level == "belief_supported"
    assert any(
        getattr(event, "event_type", "") == "grounding_source_created"
        for event in bundle.telemetry.events
    )

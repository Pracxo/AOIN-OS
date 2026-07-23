from __future__ import annotations

from datetime import timedelta

from knowledge_research_test_helpers import NOW, valid_plan, valid_response

from aion_brain.contracts.knowledge_research import fingerprint_payload
from aion_brain.contracts.knowledge_source_registry import (
    SourceRegistryProposedBatch,
    SourceRegistryRecordEnvelope,
    source_registry_payload_fingerprint,
)
from aion_brain.knowledge_intelligence.research import ControlledResearchAcquisitionService
from aion_brain.knowledge_intelligence.research_adapters import InMemoryResearchFetchAdapter
from aion_brain.knowledge_intelligence.research_evidence import ResearchEvidenceBundle
from aion_brain.knowledge_intelligence.research_policy import (
    InMemoryResearchDestinationResolver,
)
from aion_brain.knowledge_intelligence.source_registry import project_research_evidence_bundle
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    calculate_record_fingerprint,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
    source_registry_fixture_payload,
)


def fixed_id(prefix: str, index: int) -> str:
    return f"{prefix}-{index:04d}"


def valid_evidence_bundle(
    body: bytes = b"synthetic evidence for operator review",
) -> ResearchEvidenceBundle:
    plan = valid_plan()
    response = valid_response(request_id="research-fetch-request-0001", body=body)
    service = ControlledResearchAcquisitionService(
        fetch_adapter=InMemoryResearchFetchAdapter({("GET", response.response_url): response}),
        destination_resolver=InMemoryResearchDestinationResolver(
            {"research.example.invalid": ("93.184.216.34",)},
            NOW,
        ),
        clock=lambda: NOW,
    )
    result = service.run(plan)
    assert result.evidence_bundle is not None
    return result.evidence_bundle


def valid_batch(
    body: bytes = b"synthetic evidence for operator review",
) -> SourceRegistryProposedBatch:
    return project_research_evidence_bundle(
        valid_evidence_bundle(body),
        clock=lambda: NOW,
        id_factory=fixed_id,
    )


def valid_repository() -> InMemorySourceRegistryRepository:
    return InMemorySourceRegistryRepository().with_simulated_append(valid_batch())


def correction_record(
    original: SourceRegistryRecordEnvelope,
    *,
    sequence_number: int,
    previous_record_fingerprint: str,
) -> SourceRegistryRecordEnvelope:
    payload = original.payload
    envelope_payload = {
        "schema_version": "aion-knowledge-source-registry-record-envelope/v1",
        "record_id": f"{original.record_id}-correction",
        "record_kind": original.record_kind,
        "sequence_number": sequence_number,
        "record_version": original.record_version + 1,
        "supersedes_record_id": original.record_id,
        "program_id": original.program_id,
        "authorization_transaction_id": original.authorization_transaction_id,
        "implementation_task": original.implementation_task,
        "formal_closeout_task": original.formal_closeout_task,
        "authorization_scope": original.authorization_scope,
        "payload": payload,
        "payload_fingerprint": source_registry_payload_fingerprint(payload),
        "previous_record_fingerprint": previous_record_fingerprint,
        "created_at": NOW + timedelta(minutes=1),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "append_only": True,
        "source_body_present": False,
        "source_body_bytes": 0,
        "claim_verified": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return SourceRegistryRecordEnvelope(
        **envelope_payload,
        record_fingerprint=calculate_record_fingerprint(envelope_payload),
    )


def fixture_payload(records: tuple[SourceRegistryRecordEnvelope, ...]) -> dict[str, object]:
    return source_registry_fixture_payload(records)


def batch_fingerprint(records: tuple[SourceRegistryRecordEnvelope, ...]) -> str:
    return fingerprint_payload([record.record_fingerprint for record in records])

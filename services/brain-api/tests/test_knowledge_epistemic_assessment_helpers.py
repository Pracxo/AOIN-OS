"""Shared fixtures for AION-211 epistemic assessment tests."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimEvidenceBinding,
    ClaimRelationEdge,
    EvidenceRole,
    UnverifiedClaimAssertion,
    claim_evidence_binding_fingerprint,
)
from aion_brain.contracts.knowledge_epistemic_assessment import (
    EpistemicAssessmentFixtureEnvelope,
    EpistemicAssessmentRequest,
    EpistemicFreshnessPolicy,
    EpistemicTargetScope,
    epistemic_freshness_policy_fingerprint,
    epistemic_target_scope_fingerprint,
)
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredSourceLineage,
    RegisteredSourceSnapshotDigest,
    SourceRegistryRecordEnvelope,
    source_registry_payload_fingerprint,
)
from aion_brain.knowledge_intelligence.claim_graph import (
    ControlledTemporalClaimEvidenceGraph,
)
from aion_brain.knowledge_intelligence.claim_graph_repository import (
    InMemoryTemporalClaimGraphRepository,
)
from aion_brain.knowledge_intelligence.epistemic_assessment import (
    ControlledEpistemicAssessmentEngine,
    fixture_payload,
)
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    calculate_record_fingerprint,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)
from tests.test_knowledge_claim_graph_helpers import (
    NOW,
    claim,
    graph_claims,
    registry_records,
    valid_interval,
    version,
)


def freshness_policy(
    *,
    current_max_age_seconds: int = 86_400,
    stale_after_seconds: int = 604_800,
) -> EpistemicFreshnessPolicy:
    payload = {
        "policy_id": "freshness-policy-0001",
        "current_max_age_seconds": current_max_age_seconds,
        "stale_after_seconds": stale_after_seconds,
        "future_timestamp_tolerance_seconds": 60,
    }
    return EpistemicFreshnessPolicy(
        **payload,
        policy_fingerprint=epistemic_freshness_policy_fingerprint(payload),
    )


def target_scope(
    *,
    jurisdictions: tuple[str, ...] = ("global",),
) -> EpistemicTargetScope:
    payload = {
        "target_valid_time": valid_interval(),
        "target_jurisdiction_ids": jurisdictions,
        "target_version_scopes": (version(),),
    }
    return EpistemicTargetScope(
        **payload,
        scope_fingerprint=epistemic_target_scope_fingerprint(payload),
    )


def assessment_request(
    *,
    claim_ids: tuple[str, ...] = ("claim-0001",),
    assessment_time: datetime = NOW,
    target: EpistemicTargetScope | None = None,
    policy: EpistemicFreshnessPolicy | None = None,
) -> EpistemicAssessmentRequest:
    return EpistemicAssessmentRequest(
        request_id="request-0001",
        claim_ids=claim_ids,
        target_scope=target or target_scope(),
        freshness_policy=policy or freshness_policy(),
        assessment_time=assessment_time,
    )


def evidence_binding(
    *,
    claim_id: str = "claim-0001",
    binding_id: str = "binding-claim-0001",
    evidence_role: EvidenceRole = EvidenceRole.SUPPORTS,
    group_id: str = "independence-group-0001",
    lineage_record_id: str = "source-registry-source-lineage-0004",
    citation_record_ids: tuple[str, ...] = ("source-registry-citation-reference-0003",),
    provenance_record_ids: tuple[str, ...] = ("source-registry-source-provenance-0002",),
) -> ClaimEvidenceBinding:
    payload = {
        "schema_version": "aion-knowledge-claim-evidence-binding/v1",
        "binding_id": binding_id,
        "claim_id": claim_id,
        "source_registry_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_snapshot_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_provenance_record_ids": provenance_record_ids,
        "citation_record_ids": citation_record_ids,
        "lineage_record_ids": (lineage_record_id,),
        "lineage_group_ids": (group_id,),
        "evidence_role": evidence_role,
        "created_at": NOW,
        "source_records_resolved": True,
        "verified_support": False,
        "truth_effect": False,
        "confidence_effect": False,
        "knowledge_effect": False,
        "belief_effect": False,
        "runtime_effect": False,
    }
    return ClaimEvidenceBinding(
        **payload,
        binding_fingerprint=claim_evidence_binding_fingerprint(payload),
    )


def source_registry_repository(
    *,
    additional_group_ids: tuple[str, ...] = (),
) -> InMemorySourceRegistryRepository:
    records = list(registry_records())
    previous = records[-1].record_fingerprint
    snapshot = records[0].payload
    assert isinstance(snapshot, RegisteredSourceSnapshotDigest)
    for offset, group_id in enumerate(additional_group_ids, start=5):
        lineage = RegisteredSourceLineage(
            lineage_id=f"lineage-{offset:04d}",
            lineage_fingerprint=records[3].payload.lineage_fingerprint,
            snapshot_id=snapshot.snapshot_id,
            canonical_source_snapshot_id=snapshot.snapshot_id,
            lineage_kind="canonical_alias",
            content_sha256=snapshot.content_sha256,
            canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
            independence_group_id=group_id,
            created_at=NOW,
        )
        envelope = {
            "schema_version": "aion-knowledge-source-registry-record-envelope/v1",
            "record_id": f"source-registry-source-lineage-{offset:04d}",
            "record_kind": "source_lineage",
            "sequence_number": offset,
            "record_version": 1,
            "supersedes_record_id": None,
            "program_id": "AION-KNOWLEDGE-INTELLIGENCE-001",
            "authorization_transaction_id": "AION-206-KI-0002",
            "implementation_task": "AION-207",
            "formal_closeout_task": "AION-208",
            "authorization_scope": (
                "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
            ),
            "payload": lineage.model_dump(mode="json"),
            "payload_fingerprint": source_registry_payload_fingerprint(lineage),
            "previous_record_fingerprint": previous,
            "created_at": NOW,
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
        record = SourceRegistryRecordEnvelope(
            **envelope,
            record_fingerprint=calculate_record_fingerprint(envelope),
        )
        records.append(record)
        previous = record.record_fingerprint
    return InMemorySourceRegistryRepository(tuple(records))


def graph_repository(
    *,
    claims: Iterable[UnverifiedClaimAssertion] | None = None,
    bindings: Iterable[ClaimEvidenceBinding] | None = None,
    relations: Iterable[ClaimRelationEdge] = (),
    registry: InMemorySourceRegistryRepository | None = None,
) -> InMemoryTemporalClaimGraphRepository:
    registry_repository = registry or source_registry_repository()
    claim_values = tuple(claims or graph_claims())
    binding_values = tuple(
        bindings
        or tuple(
            evidence_binding(claim_id=item.claim_id, binding_id=f"binding-{item.claim_id}")
            for item in claim_values
        )
    )
    service = ControlledTemporalClaimEvidenceGraph(clock=lambda: NOW)
    batch = service.project(
        claims=claim_values,
        evidence_bindings=binding_values,
        relations=tuple(relations),
        source_registry_repository=registry_repository,
    )
    repository, _decision = service.simulate_append(InMemoryTemporalClaimGraphRepository(), batch)
    return repository


def assessment_batch():
    engine = ControlledEpistemicAssessmentEngine(clock=lambda: NOW)
    registry = source_registry_repository()
    graph = graph_repository(registry=registry)
    return engine.assess(
        request=assessment_request(),
        source_registry_repository=registry,
        claim_graph_repository=graph,
    )


def fixture_json(path: Path) -> Path:
    registry = source_registry_repository()
    graph = graph_repository(registry=registry)
    payload = fixture_payload(
        request=assessment_request(),
        source_registry_records=registry.records(),
        claim_graph_records=graph.records(),
    )
    fixture = EpistemicAssessmentFixtureEnvelope.model_validate(payload)
    path.write_text(fixture.model_dump_json(indent=2), encoding="utf-8")
    return path


def single_claim(claim_id: str = "claim-0001") -> UnverifiedClaimAssertion:
    return claim(claim_id)

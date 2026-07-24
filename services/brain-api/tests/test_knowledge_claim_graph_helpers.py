"""Shared synthetic fixtures for AION-209 claim-graph tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aion_brain.contracts.knowledge_claim_graph import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    BooleanClaimObjectValue,
    ClaimEvidenceBinding,
    ClaimGraphRecordEnvelope,
    ClaimModality,
    ClaimPolarity,
    ClaimPredicateCardinality,
    ClaimRelationEdge,
    ClaimRelationOrigin,
    ClaimRelationType,
    ClaimScope,
    EvidenceRole,
    IdentifierClaimObjectValue,
    IntegerClaimObjectValue,
    JurisdictionKind,
    JurisdictionScope,
    TextClaimObjectValue,
    UnverifiedClaimAssertion,
    ValidTimeInterval,
    VersionScheme,
    VersionScope,
    calculate_claim_identity_fingerprint,
    calculate_claim_record_fingerprint,
    claim_evidence_binding_fingerprint,
    claim_object_value_fingerprint,
    claim_relation_fingerprint,
    claim_scope_fingerprint,
    jurisdiction_scope_fingerprint,
    valid_time_interval_fingerprint,
    version_scope_fingerprint,
)
from aion_brain.contracts.knowledge_research import fingerprint_payload
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredCitationReference,
    RegisteredSourceLineage,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryRecordEnvelope,
    source_registry_payload_fingerprint,
)
from aion_brain.knowledge_intelligence.claim_graph import (
    ControlledTemporalClaimEvidenceGraph,
)
from aion_brain.knowledge_intelligence.claim_graph_repository import (
    InMemoryTemporalClaimGraphRepository,
    claim_graph_fixture_payload,
)
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    calculate_record_fingerprint,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)

NOW = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
LATER = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
MUCH_LATER = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)


def hex_for(value: object) -> str:
    return fingerprint_payload(value)


def text_object(value: str = "alpha") -> TextClaimObjectValue:
    return TextClaimObjectValue(
        canonical_value=value,
        display_value=value.title(),
        object_fingerprint=claim_object_value_fingerprint(kind="text", canonical_value=value),
    )


def identifier_object(value: str = "identifier-alpha") -> IdentifierClaimObjectValue:
    return IdentifierClaimObjectValue(
        canonical_value=value,
        display_value=value,
        object_fingerprint=claim_object_value_fingerprint(
            kind="identifier",
            canonical_value=value,
        ),
    )


def boolean_object(value: bool = True) -> BooleanClaimObjectValue:
    return BooleanClaimObjectValue(
        canonical_value=value,
        display_value=str(value).lower(),
        object_fingerprint=claim_object_value_fingerprint(
            kind="boolean",
            canonical_value=value,
        ),
    )


def integer_object(value: int = 42) -> IntegerClaimObjectValue:
    return IntegerClaimObjectValue(
        canonical_value=value,
        display_value=str(value),
        object_fingerprint=claim_object_value_fingerprint(
            kind="integer",
            canonical_value=value,
        ),
    )


def valid_interval(
    interval_id: str = "interval-0001",
    *,
    start: datetime | None = NOW,
    end: datetime | None = LATER,
    start_inclusive: bool = True,
    end_inclusive: bool = True,
) -> ValidTimeInterval:
    return ValidTimeInterval(
        interval_id=interval_id,
        start=start,
        end=end,
        start_inclusive=start_inclusive,
        end_inclusive=end_inclusive,
        interval_fingerprint=valid_time_interval_fingerprint(
            interval_id=interval_id,
            start=start,
            end=end,
            start_inclusive=start_inclusive,
            end_inclusive=end_inclusive,
        ),
    )


def jurisdiction(
    jurisdiction_id: str = "global",
    jurisdiction_kind: JurisdictionKind = JurisdictionKind.GLOBAL,
    parent_jurisdiction_ids: tuple[str, ...] = (),
) -> JurisdictionScope:
    return JurisdictionScope(
        jurisdiction_id=jurisdiction_id,
        jurisdiction_kind=jurisdiction_kind,
        parent_jurisdiction_ids=parent_jurisdiction_ids,
        scope_fingerprint=jurisdiction_scope_fingerprint(
            jurisdiction_id=jurisdiction_id,
            jurisdiction_kind=jurisdiction_kind,
            parent_jurisdiction_ids=parent_jurisdiction_ids,
        ),
    )


def version(
    target_id: str = "standard-alpha",
    exact_version: str = "1.0",
) -> VersionScope:
    return VersionScope(
        target_id=target_id,
        scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
        exact_version=exact_version,
        scope_fingerprint=version_scope_fingerprint(
            target_id=target_id,
            scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
            exact_version=exact_version,
        ),
    )


def scope(
    *,
    jurisdictions: tuple[JurisdictionScope, ...] | None = None,
    versions: tuple[VersionScope, ...] | None = None,
    intervals: tuple[ValidTimeInterval, ...] | None = None,
) -> ClaimScope:
    jurisdiction_values = jurisdictions if jurisdictions is not None else (jurisdiction(),)
    version_values = versions if versions is not None else (version(),)
    interval_values = intervals if intervals is not None else (valid_interval(),)
    return ClaimScope(
        jurisdiction_scopes=jurisdiction_values,
        version_scopes=version_values,
        valid_time_intervals=interval_values,
        scope_fingerprint=claim_scope_fingerprint(
            jurisdiction_scopes=jurisdiction_values,
            version_scopes=version_values,
            valid_time_intervals=interval_values,
        ),
    )


def claim(
    claim_id: str = "claim-0001",
    *,
    subject_id: str = "product-alpha",
    predicate: str = "has_status",
    object_value: object | None = None,
    polarity: ClaimPolarity = ClaimPolarity.POSITIVE,
    modality: ClaimModality = ClaimModality.ASSERTED,
    predicate_cardinality: ClaimPredicateCardinality = ClaimPredicateCardinality.ONE,
    objects_mutually_exclusive: bool = False,
    claim_scope: ClaimScope | None = None,
    transaction_time: datetime = NOW,
) -> UnverifiedClaimAssertion:
    object_model = object_value or text_object("alpha")
    scope_model = claim_scope or scope()
    identity = calculate_claim_identity_fingerprint(
        subject_id=subject_id,
        predicate=predicate,
        object_value=object_model,
        polarity=polarity,
        modality=modality,
        predicate_cardinality=predicate_cardinality,
        objects_mutually_exclusive=objects_mutually_exclusive,
        scope=scope_model,
    )
    payload = {
        "schema_version": "aion-knowledge-unverified-claim-assertion/v1",
        "claim_id": claim_id,
        "claim_statement": "Product alpha has status alpha.",
        "subject_id": subject_id,
        "predicate": predicate,
        "object_value": object_model,
        "polarity": polarity,
        "modality": modality,
        "predicate_cardinality": predicate_cardinality,
        "objects_mutually_exclusive": objects_mutually_exclusive,
        "language": "en",
        "scope": scope_model,
        "transaction_time": transaction_time,
        "claim_identity_fingerprint": identity,
        "operator_supplied": True,
        "unverified": True,
        "verified": False,
        "truth_value_assigned": False,
        "epistemic_confidence_assigned": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return UnverifiedClaimAssertion(
        **payload,
        claim_record_fingerprint=calculate_claim_record_fingerprint(payload),
    )


def registry_records() -> tuple[SourceRegistryRecordEnvelope, ...]:
    snapshot = RegisteredSourceSnapshotDigest(
        snapshot_id="snapshot-0001",
        snapshot_fingerprint=hex_for({"snapshot": 1}),
        content_sha256=hex_for({"content": 1}),
        original_url_fingerprint=hex_for({"original-url": 1}),
        canonical_url_fingerprint=hex_for({"canonical-url": 1}),
        content_type="text/html",
        content_length=128,
        source_class="official_standard",
        robots_policy_status="allowed",
        licence_policy_status="permitted",
        retrieval_timestamp=NOW,
        safe_headers_fingerprint=hex_for({"headers": 1}),
        redirect_chain_fingerprint=hex_for({"redirect": 1}),
    )
    provenance = RegisteredSourceProvenance(
        provenance_id="provenance-0001",
        provenance_fingerprint=hex_for({"provenance": 1}),
        snapshot_id="snapshot-0001",
        snapshot_fingerprint=snapshot.snapshot_fingerprint,
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        source_class="official_standard",
        declared_author="Example Standards Body",
        declared_publisher="Example Standards Body",
        declared_title="Synthetic Standard",
        retrieval_timestamp=NOW,
        redirect_chain_fingerprint=snapshot.redirect_chain_fingerprint,
        destination_validation_fingerprint=hex_for({"destination": 1}),
        safe_headers_fingerprint=snapshot.safe_headers_fingerprint,
        adapter_type="in_memory",
    )
    citation = RegisteredCitationReference(
        citation_id="citation-0001",
        citation_fingerprint=hex_for({"citation": 1}),
        snapshot_id="snapshot-0001",
        snapshot_fingerprint=snapshot.snapshot_fingerprint,
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        locator_kind="text_fingerprint",
        locator_value=hex_for({"locator": 1}),
        retrieval_timestamp=NOW,
    )
    lineage = RegisteredSourceLineage(
        lineage_id="lineage-0001",
        lineage_fingerprint=hex_for({"lineage": 1}),
        snapshot_id="snapshot-0001",
        canonical_source_snapshot_id="snapshot-0001",
        lineage_kind="original",
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        independence_group_id="independence-group-0001",
        created_at=NOW,
    )
    payloads = (
        ("source-registry-source-snapshot-digest-0001", "source_snapshot_digest", snapshot),
        ("source-registry-source-provenance-0002", "source_provenance", provenance),
        ("source-registry-citation-reference-0003", "citation_reference", citation),
        ("source-registry-source-lineage-0004", "source_lineage", lineage),
    )
    records: list[SourceRegistryRecordEnvelope] = []
    previous: str | None = None
    for sequence, (record_id, record_kind, payload) in enumerate(payloads, start=1):
        envelope = {
            "schema_version": "aion-knowledge-source-registry-record-envelope/v1",
            "record_id": record_id,
            "record_kind": record_kind,
            "sequence_number": sequence,
            "record_version": 1,
            "supersedes_record_id": None,
            "program_id": "AION-KNOWLEDGE-INTELLIGENCE-001",
            "authorization_transaction_id": "AION-206-KI-0002",
            "implementation_task": "AION-207",
            "formal_closeout_task": "AION-208",
            "authorization_scope": (
                "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
            ),
            "payload": payload.model_dump(mode="json"),
            "payload_fingerprint": source_registry_payload_fingerprint(payload),
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
    return tuple(records)


def source_registry_repository() -> InMemorySourceRegistryRepository:
    return InMemorySourceRegistryRepository(registry_records())


def evidence_binding(claim_id: str = "claim-0001") -> ClaimEvidenceBinding:
    payload = {
        "schema_version": "aion-knowledge-claim-evidence-binding/v1",
        "binding_id": f"binding-{claim_id}",
        "claim_id": claim_id,
        "source_registry_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_snapshot_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_provenance_record_ids": ("source-registry-source-provenance-0002",),
        "citation_record_ids": ("source-registry-citation-reference-0003",),
        "lineage_record_ids": ("source-registry-source-lineage-0004",),
        "lineage_group_ids": ("independence-group-0001",),
        "evidence_role": EvidenceRole.SUPPORTS,
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


def relation(
    source_claim_id: str = "claim-0002",
    target_claim_id: str = "claim-0001",
    relation_type: ClaimRelationType = ClaimRelationType.REFINES,
) -> ClaimRelationEdge:
    if relation_type in {
        ClaimRelationType.EQUIVALENT_TO,
        ClaimRelationType.STRUCTURAL_CONFLICT_CANDIDATE,
    }:
        source_claim_id, target_claim_id = sorted((source_claim_id, target_claim_id))
    payload = {
        "schema_version": "aion-knowledge-claim-relation-edge/v1",
        "relation_id": "relation-0001",
        "source_claim_id": source_claim_id,
        "target_claim_id": target_claim_id,
        "relation_type": relation_type,
        "relation_origin": ClaimRelationOrigin.OPERATOR_SUPPLIED,
        "effective_time": NOW,
        "operator_supplied": True,
        "derived_structural": False,
        "relation_verified": False,
        "truth_effect": False,
        "knowledge_effect": False,
        "belief_effect": False,
        "created_at": NOW,
        "runtime_effect": False,
    }
    return ClaimRelationEdge(
        **payload,
        relation_fingerprint=claim_relation_fingerprint(payload),
    )


def graph_claims() -> tuple[UnverifiedClaimAssertion, UnverifiedClaimAssertion]:
    left = claim("claim-0001", object_value=text_object("alpha"), polarity=ClaimPolarity.POSITIVE)
    right = claim("claim-0002", object_value=text_object("alpha"), polarity=ClaimPolarity.NEGATIVE)
    return left, right


def graph_batch():
    service = ControlledTemporalClaimEvidenceGraph(clock=lambda: NOW)
    registry = source_registry_repository()
    claims = graph_claims()
    batch = service.project(
        claims=claims,
        evidence_bindings=tuple(evidence_binding(item.claim_id) for item in claims),
        relations=(relation(),),
        source_registry_repository=registry,
    )
    return service, registry, claims, batch


def graph_repository() -> InMemoryTemporalClaimGraphRepository:
    service, _registry, _claims, batch = graph_batch()
    repository, _decision = service.simulate_append(InMemoryTemporalClaimGraphRepository(), batch)
    return repository


def write_fixture(path: Path, records: tuple[ClaimGraphRecordEnvelope, ...]) -> Path:
    payload = claim_graph_fixture_payload(records)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def common_json_state() -> dict[str, object]:
    return {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "temporal_claim_evidence_graph_authorized": True,
        "temporal_claim_evidence_graph_implemented": True,
        "claim_graph_runtime_enabled": False,
        "persistent_claim_graph_write_enabled": False,
        "automatic_claim_extraction_enabled": False,
        "claim_verification_enabled": False,
        "truth_decision_enabled": False,
        "epistemic_confidence_enabled": False,
        "knowledge_promotion_enabled": False,
        "belief_mutation_enabled": False,
        "runtime_effect": False,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
    }

"""Integrity validation for immutable temporal claim-evidence graph records."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimEvidenceBinding,
    ClaimGraphIntegrityStatus,
    ClaimGraphRecordEnvelope,
    ClaimRelationEdge,
    StructuralConflictCandidate,
    UnverifiedClaimAssertion,
    claim_graph_payload_fingerprint,
    claim_graph_record_fingerprint,
    json_size,
    validate_claim_graph_reason_codes,
)
from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    utc_now,
    validate_hex64,
    validate_safe_identifier,
)


class ClaimGraphIntegrityFinding(BaseModel):
    """Redacted claim-graph integrity finding."""

    model_config = FROZEN_MODEL_CONFIG

    finding_id: str
    severity: Literal["low", "medium", "high", "critical"]
    reason_codes: tuple[str, ...]
    record_id: str | None = None
    claim_id: str | None = None
    redacted_summary: str = Field(max_length=240)
    runtime_effect: Literal[False] = False

    @field_validator("finding_id", "record_id", "claim_id")
    @classmethod
    def identifiers_are_safe(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_safe_identifier(value, "claim graph integrity identifier")
        return value

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_claim_graph_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        reject_protected_material(value, "claim graph integrity summary")
        lowered = value.lower()
        for marker in ("http://", "https://", "traceback", "exception", "/", "claim text"):
            if marker in lowered:
                raise ValueError("claim graph integrity summary must remain redacted")
        return value


class ClaimGraphIntegrityReport(BaseModel):
    """Integrity audit report without claim text, source metadata, or object leakage."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-integrity/v1"] = (
        "aion-knowledge-claim-graph-integrity/v1"
    )
    status: ClaimGraphIntegrityStatus
    record_count: int = Field(ge=0)
    validated_record_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    evidence_binding_count: int = Field(ge=0)
    relation_count: int = Field(ge=0)
    structural_conflict_candidate_count: int = Field(ge=0)
    findings: tuple[ClaimGraphIntegrityFinding, ...]
    chain_head_fingerprint: str | None
    index_fingerprint: str
    audit_timestamp: datetime
    report_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("chain_head_fingerprint", "index_fingerprint", "report_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_hex64(value, "claim graph integrity fingerprint")
        return value

    @field_validator("audit_timestamp")
    @classmethod
    def audit_timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim graph integrity timestamp")


def calculate_claim_graph_record_fingerprint(
    envelope: ClaimGraphRecordEnvelope | dict[str, object],
) -> str:
    """Calculate an envelope fingerprint over all fields except itself."""

    return claim_graph_record_fingerprint(envelope)


def validate_claim_graph_record(
    envelope: ClaimGraphRecordEnvelope,
) -> ClaimGraphRecordEnvelope:
    """Validate one claim-graph envelope and return it unchanged."""

    if envelope.payload_fingerprint != claim_graph_payload_fingerprint(envelope.payload):
        raise ValueError("payload fingerprint mismatch")
    if envelope.record_fingerprint != calculate_claim_graph_record_fingerprint(envelope):
        raise ValueError("record fingerprint mismatch")
    if json_size(envelope.model_dump(mode="json")) > 32_768:
        raise ValueError("record envelope exceeds size budget")
    _assert_no_prohibited_state(envelope)
    return envelope


def audit_temporal_claim_evidence_graph(
    graph_snapshot: Iterable[ClaimGraphRecordEnvelope],
    *,
    source_registry_record_ids: Iterable[str] = (),
    source_snapshot_record_ids: Iterable[str] = (),
    source_provenance_record_ids: Iterable[str] = (),
    citation_record_ids: Iterable[str] = (),
    lineage_record_ids: Iterable[str] = (),
    lineage_group_ids: Iterable[str] = (),
    clock: object = utc_now,
) -> ClaimGraphIntegrityReport:
    """Audit graph records without mutating repository state."""

    now = clock() if callable(clock) else utc_now()
    records = tuple(sorted(graph_snapshot, key=lambda record: record.sequence_number))
    source_records = set(source_registry_record_ids)
    snapshot_records = set(source_snapshot_record_ids)
    provenance_records = set(source_provenance_record_ids)
    citations = set(citation_record_ids)
    lineage_records = set(lineage_record_ids)
    lineage_groups = set(lineage_group_ids)
    findings: list[ClaimGraphIntegrityFinding] = []
    expected_previous: str | None = None
    seen_record_ids: set[str] = set()
    seen_sequences: set[int] = set()
    supersedes: dict[str, str] = {}
    claims_by_id: dict[str, UnverifiedClaimAssertion] = {}
    identity_by_claim_id: dict[str, str] = {}
    identity_to_claim_id: dict[str, str] = {}
    relation_counts: Counter[str] = Counter()
    revision_edges: dict[str, set[str]] = defaultdict(set)
    validated_count = 0

    for expected_sequence, record in enumerate(records, start=1):
        if record.record_id in seen_record_ids:
            findings.append(_finding(expected_sequence, "claim_graph_duplicate_identifier", record))
        seen_record_ids.add(record.record_id)
        if record.sequence_number in seen_sequences:
            findings.append(_finding(expected_sequence, "claim_graph_sequence_duplicate", record))
        seen_sequences.add(record.sequence_number)
        if record.sequence_number != expected_sequence:
            findings.append(_finding(expected_sequence, "claim_graph_sequence_gap", record))
        if record.previous_record_fingerprint != expected_previous:
            findings.append(_finding(expected_sequence, "claim_graph_chain_broken", record))
        try:
            validate_claim_graph_record(record)
            validated_count += 1
        except ValueError as exc:
            findings.append(_finding(expected_sequence, _reason_for_error(str(exc)), record))
        expected_previous = record.record_fingerprint
        if record.supersedes_record_id is not None:
            supersedes[record.record_id] = record.supersedes_record_id
        payload = record.payload
        if isinstance(payload, UnverifiedClaimAssertion):
            existing_identity = identity_by_claim_id.get(payload.claim_id)
            if (
                existing_identity is not None
                and existing_identity != payload.claim_identity_fingerprint
            ):
                findings.append(
                    _finding(expected_sequence, "claim_graph_identity_collision", record)
                )
            if (
                payload.claim_identity_fingerprint in identity_to_claim_id
                and identity_to_claim_id[payload.claim_identity_fingerprint] != payload.claim_id
            ):
                findings.append(
                    _finding(expected_sequence, "claim_graph_identity_collision", record)
                )
            claims_by_id[payload.claim_id] = payload
            identity_by_claim_id[payload.claim_id] = payload.claim_identity_fingerprint
            identity_to_claim_id[payload.claim_identity_fingerprint] = payload.claim_id

    record_ids = {record.record_id for record in records}
    for record_id, superseded_id in supersedes.items():
        if superseded_id not in record_ids:
            findings.append(
                _finding_by_id(
                    len(findings) + 1,
                    "claim_graph_supersession_missing",
                    record_id,
                    None,
                )
            )
    if _has_cycle({record_id: {target} for record_id, target in supersedes.items()}):
        findings.append(
            _finding_by_id(len(findings) + 1, "claim_graph_supersession_cycle", None, None)
        )

    for index, record in enumerate(records, start=1):
        payload = record.payload
        if isinstance(payload, ClaimEvidenceBinding):
            if payload.claim_id not in claims_by_id:
                findings.append(_finding(index, "claim_graph_evidence_binding_invalid", record))
            if set(payload.source_registry_record_ids) - source_records:
                findings.append(_finding(index, "claim_graph_source_reference_unresolved", record))
            if set(payload.source_snapshot_record_ids) - snapshot_records:
                findings.append(_finding(index, "claim_graph_source_reference_unresolved", record))
            if set(payload.source_provenance_record_ids) - provenance_records:
                findings.append(_finding(index, "claim_graph_source_reference_unresolved", record))
            if set(payload.citation_record_ids) - citations:
                findings.append(
                    _finding(index, "claim_graph_citation_reference_unresolved", record)
                )
            if set(payload.lineage_record_ids) - lineage_records:
                findings.append(_finding(index, "claim_graph_source_reference_unresolved", record))
            if set(payload.lineage_group_ids) - lineage_groups:
                findings.append(_finding(index, "claim_graph_source_reference_unresolved", record))
        elif isinstance(payload, ClaimRelationEdge):
            relation_counts[payload.source_claim_id] += 1
            relation_counts[payload.target_claim_id] += 1
            if (
                payload.source_claim_id not in claims_by_id
                or payload.target_claim_id not in claims_by_id
            ):
                findings.append(_finding(index, "claim_graph_relation_invalid", record))
            if payload.source_claim_id == payload.target_claim_id:
                findings.append(_finding(index, "claim_graph_relation_invalid", record))
            if payload.relation_type.value in {"supersedes", "corrects", "retracts"}:
                revision_edges[payload.source_claim_id].add(payload.target_claim_id)
        elif isinstance(payload, StructuralConflictCandidate):
            if (
                payload.left_claim_id not in claims_by_id
                or payload.right_claim_id not in claims_by_id
            ):
                findings.append(_finding(index, "claim_graph_relation_invalid", record))
            if payload.contradiction_resolved:
                findings.append(
                    _finding(index, "claim_graph_contradiction_resolution_blocked", record)
                )

    if any(count > 100 for count in relation_counts.values()):
        findings.append(
            _finding_by_id(len(findings) + 1, "claim_graph_relation_invalid", None, None)
        )
    if _has_cycle(revision_edges):
        findings.append(_finding_by_id(len(findings) + 1, "claim_graph_relation_cycle", None, None))

    status = ClaimGraphIntegrityStatus.PASSED if not findings else ClaimGraphIntegrityStatus.FAILED
    chain_head = records[-1].record_fingerprint if records else None
    index_fingerprint = _index_fingerprint(records)
    counts = _record_counts(records)
    report_payload = {
        "status": status,
        "record_count": len(records),
        "validated_record_count": validated_count,
        "counts": counts,
        "finding_codes": [finding.reason_codes for finding in findings],
        "chain_head": chain_head,
        "index": index_fingerprint,
        "audit_timestamp": now.isoformat(),
    }
    return ClaimGraphIntegrityReport(
        status=status,
        record_count=len(records),
        validated_record_count=validated_count,
        claim_count=counts["claims"],
        evidence_binding_count=counts["bindings"],
        relation_count=counts["relations"],
        structural_conflict_candidate_count=counts["conflicts"],
        findings=tuple(findings),
        chain_head_fingerprint=chain_head,
        index_fingerprint=index_fingerprint,
        audit_timestamp=now,
        report_fingerprint=fingerprint_payload(report_payload),
    )


def _assert_no_prohibited_state(envelope: ClaimGraphRecordEnvelope) -> None:
    if envelope.source_body_present or envelope.source_body_bytes != 0:
        raise ValueError("source body blocked")
    if envelope.truth_value_assigned or envelope.epistemic_confidence_assigned:
        raise ValueError("truth or confidence state blocked")
    if envelope.knowledge_promoted or envelope.belief_created or envelope.belief_mutated:
        raise ValueError("knowledge or belief state blocked")
    if envelope.persistent_write_applied or envelope.runtime_effect:
        raise ValueError("runtime state blocked")
    data = envelope.payload.model_dump(mode="json")
    for key in (
        "verified",
        "truth_value_assigned",
        "epistemic_confidence_assigned",
        "knowledge_promoted",
        "belief_created",
        "belief_mutated",
        "truth_effect",
        "confidence_effect",
        "knowledge_effect",
        "belief_effect",
        "relation_verified",
        "contradiction_resolved",
        "left_claim_true",
        "right_claim_true",
        "left_claim_false",
        "right_claim_false",
        "persistent_write_applied",
        "runtime_effect",
    ):
        if data.get(key) is True:
            raise ValueError("prohibited graph state blocked")
    if data.get("source_body_present") is True or data.get("source_body_bytes", 0) != 0:
        raise ValueError("source body blocked")


def _record_counts(records: tuple[ClaimGraphRecordEnvelope, ...]) -> dict[str, int]:
    return {
        "claims": sum(isinstance(record.payload, UnverifiedClaimAssertion) for record in records),
        "bindings": sum(isinstance(record.payload, ClaimEvidenceBinding) for record in records),
        "relations": sum(isinstance(record.payload, ClaimRelationEdge) for record in records),
        "conflicts": sum(
            isinstance(record.payload, StructuralConflictCandidate) for record in records
        ),
    }


def _has_cycle(edges: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for target in edges.get(node, set()):
            if visit(target):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in edges)


def _finding(
    index: int,
    reason_code: str,
    record: ClaimGraphRecordEnvelope,
) -> ClaimGraphIntegrityFinding:
    claim_id = None
    payload = record.payload
    if isinstance(payload, UnverifiedClaimAssertion):
        claim_id = payload.claim_id
    elif isinstance(payload, (ClaimEvidenceBinding, ClaimRelationEdge)):
        claim_id = getattr(payload, "claim_id", None) or getattr(payload, "source_claim_id", None)
    return _finding_by_id(index, reason_code, record.record_id, claim_id)


def _finding_by_id(
    index: int,
    reason_code: str,
    record_id: str | None,
    claim_id: str | None,
) -> ClaimGraphIntegrityFinding:
    return ClaimGraphIntegrityFinding(
        finding_id=f"claim-graph-finding-{index:04d}",
        severity="high",
        reason_codes=(reason_code,),
        record_id=record_id,
        claim_id=claim_id,
        redacted_summary="Claim graph integrity invariant failed.",
    )


def _reason_for_error(message: str) -> str:
    lowered = message.lower()
    if "payload fingerprint" in lowered:
        return "claim_graph_payload_fingerprint_mismatch"
    if "record fingerprint" in lowered:
        return "claim_graph_record_fingerprint_mismatch"
    if "source body" in lowered:
        return "claim_graph_source_body_blocked"
    if "truth" in lowered:
        return "claim_graph_truth_decision_blocked"
    if "confidence" in lowered:
        return "claim_graph_confidence_calculation_blocked"
    if "knowledge" in lowered:
        return "claim_graph_knowledge_promotion_blocked"
    if "belief" in lowered:
        return "claim_graph_belief_mutation_blocked"
    if "runtime" in lowered:
        return "claim_graph_runtime_disabled"
    return "claim_graph_record_fingerprint_mismatch"


def _index_fingerprint(records: tuple[ClaimGraphRecordEnvelope, ...]) -> str:
    return fingerprint_payload(
        {
            "record_ids": [record.record_id for record in records],
            "sequence": [record.sequence_number for record in records],
            "fingerprints": [record.record_fingerprint for record in records],
        }
    )


__all__ = [
    "ClaimGraphIntegrityFinding",
    "ClaimGraphIntegrityReport",
    "audit_temporal_claim_evidence_graph",
    "calculate_claim_graph_record_fingerprint",
    "validate_claim_graph_record",
]

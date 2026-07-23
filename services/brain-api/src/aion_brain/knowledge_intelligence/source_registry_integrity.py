"""Integrity validation for append-only source-registry records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    stable_json,
    utc_now,
    validate_hex64,
    validate_safe_identifier,
)
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredCitationReference,
    RegisteredDeduplicationDecision,
    RegisteredPolicyDecision,
    RegisteredSourceLineage,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryRecordEnvelope,
    source_registry_payload_fingerprint,
    validate_source_registry_reason_codes,
)


class SourceRegistryIntegrityFinding(BaseModel):
    """Redacted source-registry integrity finding."""

    model_config = FROZEN_MODEL_CONFIG

    finding_id: str
    severity: Literal["low", "medium", "high", "critical"]
    reason_codes: tuple[str, ...]
    record_id: str | None = None
    redacted_summary: str = Field(max_length=240)
    runtime_effect: Literal[False] = False

    @field_validator("finding_id", "record_id")
    @classmethod
    def identifiers_are_safe(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_safe_identifier(value, "integrity finding identifier")
        return value

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_source_registry_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        reject_protected_material(value, "integrity finding summary")
        if "://" in value or "/" in value:
            raise ValueError("integrity finding summary must not include URLs or paths")
        return value


class SourceRegistryIntegrityReport(BaseModel):
    """Integrity audit report without source metadata leakage."""

    model_config = FROZEN_MODEL_CONFIG

    status: Literal["passed", "failed"]
    record_count: int = Field(ge=0)
    validated_record_count: int = Field(ge=0)
    findings: tuple[SourceRegistryIntegrityFinding, ...]
    chain_head_fingerprint: str | None
    index_fingerprint: str
    audit_timestamp: datetime
    report_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("chain_head_fingerprint")
    @classmethod
    def chain_head_is_hex(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_hex64(value, "chain head fingerprint")
        return value

    @field_validator("index_fingerprint", "report_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry integrity fingerprint")

    @field_validator("audit_timestamp")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry integrity audit timestamp")


def calculate_record_fingerprint(
    envelope: SourceRegistryRecordEnvelope | Mapping[str, Any],
) -> str:
    """Calculate a record fingerprint over all envelope fields except itself."""

    if isinstance(envelope, SourceRegistryRecordEnvelope):
        payload = envelope.model_dump(mode="json")
    else:
        payload = _json_ready(dict(envelope))
    payload.pop("record_fingerprint", None)
    return fingerprint_payload(payload)


def validate_record_envelope(
    envelope: SourceRegistryRecordEnvelope,
) -> SourceRegistryRecordEnvelope:
    """Validate one source-registry envelope and return it unchanged."""

    if envelope.payload_fingerprint != source_registry_payload_fingerprint(envelope.payload):
        raise ValueError("payload fingerprint mismatch")
    if envelope.record_fingerprint != calculate_record_fingerprint(envelope):
        raise ValueError("record fingerprint mismatch")
    if _json_size(envelope.model_dump(mode="json")) > 8192:
        raise ValueError("record envelope exceeds size budget")
    if _json_size(envelope.payload.model_dump(mode="json")) > 4096:
        raise ValueError("record payload exceeds metadata budget")
    _assert_no_prohibited_state(envelope)
    return envelope


def audit_source_registry(
    registry_snapshot: Iterable[SourceRegistryRecordEnvelope],
    *,
    clock: object = utc_now,
) -> SourceRegistryIntegrityReport:
    """Audit a registry snapshot without mutating it."""

    now = clock() if callable(clock) else utc_now()
    records = tuple(registry_snapshot)
    findings: list[SourceRegistryIntegrityFinding] = []
    validated_count = 0
    seen_ids: set[str] = set()
    seen_sequences: set[int] = set()
    expected_previous: str | None = None
    snapshot_ids: set[str] = set()
    record_ids = {record.record_id for record in records}
    supersedes: dict[str, str] = {}

    for index, record in enumerate(records, start=1):
        if record.record_id in seen_ids:
            findings.append(
                _finding(index, "source_registry_duplicate_identifier", record.record_id)
            )
        seen_ids.add(record.record_id)
        if record.sequence_number in seen_sequences:
            findings.append(_finding(index, "source_registry_sequence_duplicate", record.record_id))
        seen_sequences.add(record.sequence_number)
        if record.sequence_number != index:
            findings.append(_finding(index, "source_registry_sequence_gap", record.record_id))
        if record.previous_record_fingerprint != expected_previous:
            findings.append(_finding(index, "source_registry_chain_broken", record.record_id))
        try:
            validate_record_envelope(record)
            validated_count += 1
        except ValueError as exc:
            reason = _reason_for_validation_error(str(exc))
            findings.append(_finding(index, reason, record.record_id))
        expected_previous = record.record_fingerprint
        if isinstance(record.payload, RegisteredSourceSnapshotDigest):
            snapshot_ids.add(record.payload.snapshot_id)
        if record.supersedes_record_id is not None:
            supersedes[record.record_id] = record.supersedes_record_id
            if record.supersedes_record_id not in record_ids:
                findings.append(
                    _finding(index, "source_registry_supersession_missing", record.record_id)
                )

    for index, record in enumerate(records, start=1):
        if _references_unresolved(record, snapshot_ids):
            findings.append(_finding(index, "source_registry_chain_broken", record.record_id))
    if _has_supersession_cycle(supersedes):
        findings.append(
            _finding(
                len(findings) + 1,
                "source_registry_supersession_cycle",
                None,
            )
        )

    status: Literal["passed", "failed"] = "passed" if not findings else "failed"
    chain_head = records[-1].record_fingerprint if records else None
    index_fingerprint = _index_fingerprint(records)
    report_payload = {
        "status": status,
        "record_count": len(records),
        "validated_record_count": validated_count,
        "finding_codes": [finding.reason_codes for finding in findings],
        "chain_head": chain_head,
        "index": index_fingerprint,
        "audit_timestamp": now.isoformat(),
    }
    reason = (
        "source_registry_integrity_passed"
        if status == "passed"
        else "source_registry_integrity_failed"
    )
    if not findings:
        findings_tuple: tuple[SourceRegistryIntegrityFinding, ...] = ()
    else:
        findings_tuple = tuple(findings)
    return SourceRegistryIntegrityReport(
        status=status,
        record_count=len(records),
        validated_record_count=validated_count,
        findings=findings_tuple,
        chain_head_fingerprint=chain_head,
        index_fingerprint=index_fingerprint,
        audit_timestamp=now,
        report_fingerprint=fingerprint_payload({**report_payload, "reason": reason}),
    )


def _assert_no_prohibited_state(envelope: SourceRegistryRecordEnvelope) -> None:
    if envelope.source_body_present or envelope.source_body_bytes != 0:
        raise ValueError("source body blocked")
    if envelope.claim_verified or envelope.knowledge_promoted:
        raise ValueError("truth or knowledge state blocked")
    if envelope.belief_created or envelope.belief_mutated:
        raise ValueError("belief state blocked")
    if envelope.persistent_write_applied or envelope.runtime_effect:
        raise ValueError("runtime state blocked")
    payload = envelope.payload
    payload_data = payload.model_dump(mode="json")
    if (
        payload_data.get("source_body_present") is True
        or payload_data.get("source_body_bytes", 0) != 0
    ):
        raise ValueError("source body blocked")
    for key in (
        "verified_fact",
        "source_claims_verified",
        "claim_verified",
        "independent_corroboration_established",
        "claim_corroboration_established",
        "knowledge_promoted",
        "knowledge_promotion_authorized",
        "belief_created",
        "belief_mutated",
        "belief_mutation_authorized",
        "approval_created",
        "implementation_authorization_created",
        "runtime_effect",
    ):
        if payload_data.get(key) is True:
            raise ValueError("prohibited state blocked")


def _references_unresolved(record: SourceRegistryRecordEnvelope, snapshot_ids: set[str]) -> bool:
    payload = record.payload
    if isinstance(
        payload,
        (
            RegisteredSourceProvenance,
            RegisteredCitationReference,
            RegisteredSourceLineage,
            RegisteredDeduplicationDecision,
            RegisteredPolicyDecision,
        ),
    ):
        return payload.snapshot_id not in snapshot_ids
    return False


def _reason_for_validation_error(message: str) -> str:
    lowered = message.lower()
    if "payload fingerprint" in lowered:
        return "source_registry_payload_fingerprint_mismatch"
    if "record fingerprint" in lowered:
        return "source_registry_record_fingerprint_mismatch"
    if "source body" in lowered:
        return "source_registry_source_body_blocked"
    if "metadata" in lowered:
        return "source_registry_metadata_budget_exceeded"
    return "source_registry_record_invalid"


def _has_supersession_cycle(supersedes: dict[str, str]) -> bool:
    for record_id in supersedes:
        visited: set[str] = set()
        cursor: str | None = record_id
        while cursor is not None:
            if cursor in visited:
                return True
            visited.add(cursor)
            cursor = supersedes.get(cursor)
    return False


def _finding(
    index: int,
    reason_code: str,
    record_id: str | None,
) -> SourceRegistryIntegrityFinding:
    return SourceRegistryIntegrityFinding(
        finding_id=f"source-registry-finding-{index:04d}",
        severity="high",
        reason_codes=(reason_code,),
        record_id=record_id,
        redacted_summary="Source registry integrity invariant failed.",
    )


def _index_fingerprint(records: tuple[SourceRegistryRecordEnvelope, ...]) -> str:
    payload = {
        "record_ids": [record.record_id for record in records],
        "sequence": [record.sequence_number for record in records],
        "fingerprints": [record.record_fingerprint for record in records],
    }
    return fingerprint_payload(payload)


def _json_size(payload: object) -> int:
    return len(stable_json(payload).encode("utf-8"))


def _json_ready(value: object) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        text = value.isoformat()
        if text.endswith("+00:00"):
            return f"{text[:-6]}Z"
        return text
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = [
    "SourceRegistryIntegrityFinding",
    "SourceRegistryIntegrityReport",
    "audit_source_registry",
    "calculate_record_fingerprint",
    "validate_record_envelope",
]

"""Audit integrity verifier."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from aion_brain.audit_integrity.canonical import canonical_json
from aion_brain.audit_integrity.hashing import (
    hash_checkpoint,
    hash_entry,
    hash_payload,
    sha256_text,
)
from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.contracts.audit_integrity import AuditVerificationRequest, AuditVerificationRun
from aion_brain.contracts.telemetry import VisualTelemetryEvent


class AuditVerifier:
    """Verify audit hash-chain and checkpoint integrity."""

    def __init__(
        self,
        repository: AuditIntegrityRepository,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._telemetry_service = telemetry_service

    def verify(self, request: AuditVerificationRequest) -> AuditVerificationRun:
        """Run deterministic local verification."""
        verification_id = request.audit_verification_id or f"audit-verification-{uuid4().hex}"
        self._emit("audit_verification_started", verification_id, request.trace_id, 0.7, {})
        entries = self._repository.list_entries(
            trace_id=request.trace_id,
            from_sequence=request.from_sequence,
            to_sequence=request.to_sequence,
            limit=100_000,
            ascending=True,
        )
        violations: list[dict[str, object]] = []
        valid_count = 0
        missing_count = 0
        previous_entry = None
        if request.from_sequence and request.from_sequence > 1:
            previous_entry = self._repository.get_by_sequence(request.from_sequence - 1)
        expected_previous_hash = previous_entry.entry_hash if previous_entry else None
        expected_sequence = request.from_sequence or (entries[0].sequence_number if entries else 1)
        for entry in entries:
            entry_valid = True
            if request.verify_hash_chain and entry.sequence_number != expected_sequence:
                missing_count += max(0, entry.sequence_number - expected_sequence)
                violations.append(
                    {
                        "type": "sequence_gap",
                        "expected_sequence": expected_sequence,
                        "actual_sequence": entry.sequence_number,
                    }
                )
                entry_valid = False
            if request.verify_hash_chain and entry.previous_hash != expected_previous_hash:
                violations.append(
                    {
                        "type": "previous_hash_mismatch",
                        "sequence_number": entry.sequence_number,
                    }
                )
                entry_valid = False
            if request.verify_payload_hashes:
                expected_payload_hash = hash_payload(entry.canonical_payload)
                if entry.payload_hash != expected_payload_hash:
                    violations.append(
                        {
                            "type": "payload_hash_mismatch",
                            "sequence_number": entry.sequence_number,
                        }
                    )
                    entry_valid = False
            if request.verify_hash_chain:
                expected_entry_hash = hash_entry(
                    entry.previous_hash,
                    entry.payload_hash,
                    entry.sequence_number,
                    entry.metadata,
                )
                if entry.entry_hash != expected_entry_hash:
                    violations.append(
                        {
                            "type": "entry_hash_mismatch",
                            "sequence_number": entry.sequence_number,
                        }
                    )
                    entry_valid = False
            if entry_valid:
                valid_count += 1
            expected_previous_hash = entry.entry_hash
            expected_sequence = entry.sequence_number + 1
        if request.verify_checkpoints:
            self._verify_checkpoints(violations)
        invalid_count = len(violations)
        status: Literal["passed", "failed"] = (
            "passed" if invalid_count == 0 and missing_count == 0 else "failed"
        )
        run = AuditVerificationRun(
            audit_verification_id=verification_id,
            trace_id=request.trace_id,
            status=status,
            from_sequence=request.from_sequence,
            to_sequence=request.to_sequence,
            checked_count=len(entries),
            valid_count=valid_count,
            invalid_count=invalid_count,
            missing_count=missing_count,
            violations=violations,
            report={
                "verify_checkpoints": request.verify_checkpoints,
                "verify_hash_chain": request.verify_hash_chain,
                "verify_payload_hashes": request.verify_payload_hashes,
            },
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        stored = self._repository.save_verification_run(run)
        self._emit(
            "audit_verification_completed",
            stored.audit_verification_id,
            stored.trace_id,
            0.8 if stored.status == "passed" else 1.0,
            {"status": stored.status, "invalid_count": stored.invalid_count},
        )
        if stored.status != "passed":
            self._emit(
                "audit_integrity_violation_detected",
                stored.audit_verification_id,
                stored.trace_id,
                1.0,
                {"violations": stored.invalid_count},
            )
        return stored

    def _verify_checkpoints(self, violations: list[dict[str, object]]) -> None:
        checkpoints = list(reversed(self._repository.list_checkpoints(limit=100_000)))
        previous_hash = None
        for checkpoint in checkpoints:
            entries = self._repository.list_entries(
                from_sequence=checkpoint.from_sequence,
                to_sequence=checkpoint.to_sequence,
                limit=max(1, checkpoint.to_sequence - checkpoint.from_sequence + 1),
                ascending=True,
            )
            entry_hashes = [entry.entry_hash for entry in entries]
            expected_root = sha256_text(canonical_json({"entry_hashes": entry_hashes}))
            expected_checkpoint = hash_checkpoint(entry_hashes, previous_hash)
            if checkpoint.root_hash != expected_root:
                violations.append(
                    {
                        "type": "checkpoint_root_mismatch",
                        "checkpoint_id": checkpoint.checkpoint_id,
                    }
                )
            if checkpoint.previous_checkpoint_hash != previous_hash:
                violations.append(
                    {
                        "type": "checkpoint_chain_mismatch",
                        "checkpoint_id": checkpoint.checkpoint_id,
                    }
                )
            if checkpoint.checkpoint_hash != expected_checkpoint:
                violations.append(
                    {
                        "type": "checkpoint_hash_mismatch",
                        "checkpoint_id": checkpoint.checkpoint_id,
                    }
                )
            previous_hash = checkpoint.checkpoint_hash

    def _emit(
        self,
        event_type: str,
        node_id: str,
        trace_id: str | None,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{node_id}",
                    trace_id=trace_id or node_id,
                    event_type=event_type,  # type: ignore[arg-type]
                    node_type="audit_verification",
                    node_id=node_id,
                    edge_from=trace_id,
                    edge_to=node_id,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return

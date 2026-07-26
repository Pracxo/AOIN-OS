"""Hash-chained attestations for AION-215 verification findings."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.knowledge_research import utc_now
from aion_brain.contracts.knowledge_tool_verification import (
    ToolAttestation,
    ToolVerificationFinding,
    tool_attestation_fingerprint,
)


def _now(clock: object) -> datetime:
    value = clock() if callable(clock) else utc_now()
    return value if isinstance(value, datetime) else utc_now()


def build_attestation_chain(
    findings: tuple[ToolVerificationFinding, ...],
    *,
    clock: object = utc_now,
) -> tuple[ToolAttestation, ...]:
    """Build deterministic hash-chained attestations for sorted findings."""

    attestations: list[ToolAttestation] = []
    previous: str | None = None
    for index, finding in enumerate(sorted(findings, key=lambda item: item.finding_id), start=1):
        payload = {
            "schema_version": "aion-knowledge-tool-attestation/v1",
            "attestation_id": f"attestation-{finding.finding_id}",
            "sequence_number": index,
            "previous_attestation_fingerprint": previous,
            "finding_id": finding.finding_id,
            "finding_fingerprint": finding.finding_fingerprint,
            "attested_at": _now(clock),
            "synthetic": True,
            "read_only": True,
            "redacted": True,
            "runtime_effect": False,
        }
        attestation = ToolAttestation.model_validate(
            {**payload, "attestation_fingerprint": tool_attestation_fingerprint(payload)}
        )
        attestations.append(attestation)
        previous = attestation.attestation_fingerprint
    return tuple(attestations)


def attestation_chain_is_valid(attestations: tuple[ToolAttestation, ...]) -> bool:
    """Verify sequence order and previous-fingerprint links."""

    previous: str | None = None
    for expected_sequence, attestation in enumerate(attestations, start=1):
        if attestation.sequence_number != expected_sequence:
            return False
        if attestation.previous_attestation_fingerprint != previous:
            return False
        if attestation.attestation_fingerprint != tool_attestation_fingerprint(attestation):
            return False
        previous = attestation.attestation_fingerprint
    return True


__all__ = ["attestation_chain_is_valid", "build_attestation_chain"]

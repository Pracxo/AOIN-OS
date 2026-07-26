"""Redacted diagnostics, incidents, and operator evidence for AION-215."""

from __future__ import annotations

from aion_brain.contracts.knowledge_tool_verification import (
    ToolAttestation,
    ToolFindingSeverity,
    ToolSimulationResult,
    ToolVerificationDiagnostics,
    ToolVerificationEvidenceBundle,
    ToolVerificationFinding,
    ToolVerificationIncident,
    ToolVerificationOperatorReviewItem,
    tool_diagnostics_fingerprint,
    tool_evidence_bundle_fingerprint,
    tool_incident_fingerprint,
    tool_operator_review_fingerprint,
)


def build_tool_diagnostics(
    *,
    diagnostic_id: str,
    reason_codes: tuple[str, ...],
    summary: str,
) -> ToolVerificationDiagnostics:
    """Build redacted deterministic diagnostics."""

    payload = {
        "schema_version": "aion-knowledge-tool-verification-diagnostics/v1",
        "diagnostic_id": diagnostic_id,
        "reason_codes": reason_codes,
        "summary": summary,
        "redacted": True,
    }
    return ToolVerificationDiagnostics.model_validate(
        {**payload, "diagnostic_fingerprint": tool_diagnostics_fingerprint(payload)}
    )


def build_tool_incident(
    *,
    incident_id: str,
    severity: ToolFindingSeverity,
    reason_codes: tuple[str, ...],
    redacted_detail: str,
) -> ToolVerificationIncident:
    """Build a redacted incident record."""

    payload = {
        "schema_version": "aion-knowledge-tool-verification-incident/v1",
        "incident_id": incident_id,
        "severity": severity,
        "reason_codes": reason_codes,
        "redacted_detail": redacted_detail,
        "actual_tool_executed": False,
        "runtime_effect": False,
    }
    return ToolVerificationIncident.model_validate(
        {**payload, "incident_fingerprint": tool_incident_fingerprint(payload)}
    )


def build_operator_review_item(
    *,
    review_item_id: str,
    session_id: str,
) -> ToolVerificationOperatorReviewItem:
    """Build operator evidence that simulation is not execution or approval."""

    payload = {
        "schema_version": "aion-knowledge-tool-verification-operator-review/v1",
        "review_item_id": review_item_id,
        "session_id": session_id,
        "required": True,
        "summary": "Synthetic tool simulation requires operator review before any future action.",
        "simulation_pass_not_execution": True,
        "verification_pass_not_approval": True,
        "tool_output_not_knowledge": True,
        "actual_tool_executed": False,
        "runtime_effect": False,
    }
    return ToolVerificationOperatorReviewItem.model_validate(
        {**payload, "review_fingerprint": tool_operator_review_fingerprint(payload)}
    )


def build_evidence_bundle(
    *,
    evidence_id: str,
    session_id: str,
    simulation: ToolSimulationResult,
    findings: tuple[ToolVerificationFinding, ...],
    attestations: tuple[ToolAttestation, ...],
) -> ToolVerificationEvidenceBundle:
    """Build a redacted evidence bundle from artifacts, findings, and attestations."""

    payload = {
        "schema_version": "aion-knowledge-tool-verification-evidence/v1",
        "evidence_id": evidence_id,
        "session_id": session_id,
        "artifact_fingerprints": tuple(
            artifact.artifact_fingerprint for artifact in simulation.artifacts
        ),
        "finding_fingerprints": tuple(finding.finding_fingerprint for finding in findings),
        "attestation_fingerprints": tuple(
            attestation.attestation_fingerprint for attestation in attestations
        ),
        "provenance_fingerprints": (
            simulation.simulation_fingerprint,
            simulation.output_fingerprint,
        ),
        "redacted": True,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ToolVerificationEvidenceBundle.model_validate(
        {**payload, "evidence_fingerprint": tool_evidence_bundle_fingerprint(payload)}
    )


__all__ = [
    "build_evidence_bundle",
    "build_operator_review_item",
    "build_tool_diagnostics",
    "build_tool_incident",
]

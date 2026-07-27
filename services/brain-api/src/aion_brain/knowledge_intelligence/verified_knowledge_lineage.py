"""Integrated verified-knowledge lineage helpers."""

from __future__ import annotations

from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import EpistemicAssessmentStatus
from aion_brain.contracts.knowledge_verified_memory import (
    AUTHORIZATION_TRANSACTION_ID,
    INTEGRATED_KNOWLEDGE_LINEAGE_SCHEMA_VERSION,
    PROGRAM_ID,
    VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
    IntegratedKnowledgeLineage,
    VerifiedKnowledgeIntegrityFinding,
    VerifiedKnowledgeIntegrityReport,
    VerifiedKnowledgeIntegrityStatus,
    quantize_confidence,
    verified_knowledge_fingerprint,
)


def _sort_pairs(
    ids: tuple[str, ...],
    fingerprints: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if len(ids) != len(fingerprints):
        raise ValueError("lineage reference fingerprint mismatch")
    pairs = tuple(sorted(zip(ids, fingerprints, strict=True), key=lambda item: item[0]))
    return tuple(item[0] for item in pairs), tuple(item[1] for item in pairs)


def build_integrated_knowledge_lineage(
    *,
    lineage_id: str,
    research_plan_id: str,
    research_plan_fingerprint: str,
    acquisition_result_fingerprint: str,
    source_snapshot_ids: tuple[str, ...],
    source_snapshot_fingerprints: tuple[str, ...],
    source_provenance_ids: tuple[str, ...],
    source_provenance_fingerprints: tuple[str, ...],
    citation_reference_ids: tuple[str, ...],
    citation_reference_fingerprints: tuple[str, ...],
    source_registry_integrity_fingerprint: str,
    claim_id: str,
    claim_identity_fingerprint: str,
    claim_version_id: str,
    claim_graph_integrity_fingerprint: str,
    assessment_id: str,
    assessment_fingerprint: str,
    assessment_status: EpistemicAssessmentStatus,
    assessment_confidence: Decimal | int | str | float,
    assessment_hard_cap: Decimal | int | str | float,
    domain_mesh_session_id: str,
    domain_mesh_session_fingerprint: str,
    synthesis_id: str,
    synthesis_fingerprint: str,
    synthesis_confidence_cap: Decimal | int | str | float,
    tool_verification_session_ids: tuple[str, ...] = (),
    tool_verification_session_fingerprints: tuple[str, ...] = (),
    attestation_chain_head_fingerprints: tuple[str, ...] = (),
    tool_evidence_confidence_caps: tuple[Decimal | int | str | float, ...] = (),
    source_independence_group_ids: tuple[str, ...] = (),
    target_valid_time_fingerprint: str,
    jurisdiction_scope_fingerprint: str,
    version_scope_fingerprint: str,
    synthetic: bool = True,
) -> IntegratedKnowledgeLineage:
    """Build complete deterministic upstream lineage for one candidate."""

    snapshot_ids, snapshot_fps = _sort_pairs(source_snapshot_ids, source_snapshot_fingerprints)
    provenance_ids, provenance_fps = _sort_pairs(
        source_provenance_ids, source_provenance_fingerprints
    )
    citation_ids, citation_fps = _sort_pairs(
        citation_reference_ids, citation_reference_fingerprints
    )
    tool_ids, tool_fps = _sort_pairs(
        tool_verification_session_ids,
        tool_verification_session_fingerprints,
    )
    attestations = tuple(sorted(attestation_chain_head_fingerprints))
    independence = tuple(sorted(source_independence_group_ids))
    reference_count = (
        len(snapshot_ids)
        + len(provenance_ids)
        + len(citation_ids)
        + 1
        + 1
        + 1
        + len(tool_ids)
        + len(attestations)
        + len(independence)
    )
    payload = {
        "schema_version": INTEGRATED_KNOWLEDGE_LINEAGE_SCHEMA_VERSION,
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "lineage_id": lineage_id,
        "research_plan_id": research_plan_id,
        "research_plan_fingerprint": research_plan_fingerprint,
        "acquisition_result_fingerprint": acquisition_result_fingerprint,
        "source_snapshot_ids": snapshot_ids,
        "source_snapshot_fingerprints": snapshot_fps,
        "source_provenance_ids": provenance_ids,
        "source_provenance_fingerprints": provenance_fps,
        "citation_reference_ids": citation_ids,
        "citation_reference_fingerprints": citation_fps,
        "source_registry_integrity_fingerprint": source_registry_integrity_fingerprint,
        "claim_id": claim_id,
        "claim_identity_fingerprint": claim_identity_fingerprint,
        "claim_version_id": claim_version_id,
        "claim_graph_integrity_fingerprint": claim_graph_integrity_fingerprint,
        "assessment_id": assessment_id,
        "assessment_fingerprint": assessment_fingerprint,
        "assessment_status": assessment_status,
        "assessment_confidence": quantize_confidence(assessment_confidence),
        "assessment_hard_cap": quantize_confidence(assessment_hard_cap),
        "domain_mesh_session_id": domain_mesh_session_id,
        "domain_mesh_session_fingerprint": domain_mesh_session_fingerprint,
        "synthesis_id": synthesis_id,
        "synthesis_fingerprint": synthesis_fingerprint,
        "synthesis_confidence_cap": quantize_confidence(synthesis_confidence_cap),
        "tool_verification_session_ids": tool_ids,
        "tool_verification_session_fingerprints": tool_fps,
        "attestation_chain_head_fingerprints": attestations,
        "tool_evidence_confidence_caps": tuple(
            quantize_confidence(item) for item in tool_evidence_confidence_caps
        ),
        "source_independence_group_ids": independence,
        "target_valid_time_fingerprint": target_valid_time_fingerprint,
        "jurisdiction_scope_fingerprint": jurisdiction_scope_fingerprint,
        "version_scope_fingerprint": version_scope_fingerprint,
        "lineage_reference_count": reference_count,
        "synthetic": synthetic,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return IntegratedKnowledgeLineage.model_validate(
        {**payload, "lineage_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def validate_integrated_knowledge_lineage(
    lineage: IntegratedKnowledgeLineage,
) -> IntegratedKnowledgeLineage:
    """Validate lineage by reloading the immutable model."""

    return IntegratedKnowledgeLineage.model_validate(lineage.model_dump(mode="python"))


def audit_integrated_knowledge_lineage(
    lineage: IntegratedKnowledgeLineage,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit lineage integrity with redacted finding content."""

    status = VerifiedKnowledgeIntegrityStatus.PASSED
    reason = "verified_lineage_valid"
    try:
        validate_integrated_knowledge_lineage(lineage)
    except ValueError:
        status = VerifiedKnowledgeIntegrityStatus.FAILED
        reason = "verified_lineage_invalid"
    finding_payload = {
        "finding_id": f"finding-{lineage.lineage_id}",
        "status": status,
        "reason_codes": (reason,),
        "safe_ids": (lineage.lineage_id,),
        "fingerprints": (lineage.lineage_fingerprint,),
        "bounded_count": lineage.lineage_reference_count,
        "redacted_summary": "integrated verified knowledge lineage audit",
        "runtime_effect": False,
    }
    finding = VerifiedKnowledgeIntegrityFinding.model_validate(finding_payload)
    report_payload = {
        "schema_version": VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
        "report_id": f"integrity-{lineage.lineage_id}",
        "status": status,
        "findings": (finding,),
        "finding_count": 1,
        "read_only": True,
        "redacted": True,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeIntegrityReport.model_validate(
        {**report_payload, "report_fingerprint": verified_knowledge_fingerprint(report_payload)}
    )

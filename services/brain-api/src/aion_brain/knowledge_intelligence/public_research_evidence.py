"""Redacted evidence builders for AION-219 public research pilots."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchCandidateOutcome,
    PublicResearchPilotDiagnostics,
    PublicResearchPilotEvidenceBundle,
    PublicResearchPilotIncident,
    PublicResearchPilotOperatorReviewItem,
    public_research_fingerprint,
)


def build_public_research_incident(
    *,
    incident_id: str,
    reason_code: str,
    redacted_summary: str,
    created_at: datetime,
) -> PublicResearchPilotIncident:
    """Build one redacted incident without source content."""

    payload = {
        "incident_id": incident_id,
        "reason_code": reason_code,
        "redacted_summary": redacted_summary,
        "created_at": created_at.isoformat(),
    }
    return PublicResearchPilotIncident(
        incident_id=incident_id,
        reason_code=reason_code,
        redacted_summary=redacted_summary,
        created_at=created_at,
        fingerprint=public_research_fingerprint(payload),
    )


def build_public_research_diagnostics(
    *,
    diagnostics_id: str,
    reason_codes: tuple[str, ...],
    bounded_counts: dict[str, int],
    incident_ids: tuple[str, ...],
    created_at: datetime,
) -> PublicResearchPilotDiagnostics:
    """Build bounded redacted diagnostics for one pilot."""

    payload = {
        "diagnostics_id": diagnostics_id,
        "reason_codes": tuple(sorted(reason_codes)),
        "bounded_counts": dict(sorted(bounded_counts.items())),
        "incident_ids": tuple(sorted(incident_ids)),
        "created_at": created_at.isoformat(),
    }
    return PublicResearchPilotDiagnostics(
        diagnostics_id=diagnostics_id,
        reason_codes=tuple(sorted(reason_codes)),
        bounded_counts=dict(sorted(bounded_counts.items())),
        incident_ids=tuple(sorted(incident_ids)),
        created_at=created_at,
        fingerprint=public_research_fingerprint(payload),
    )


def build_public_research_operator_review_item(
    *,
    review_item_id: str,
    candidate_ids: tuple[str, ...],
    candidate_eligibility_statuses: tuple[PublicResearchCandidateOutcome, ...],
) -> PublicResearchPilotOperatorReviewItem:
    """Build one operator-review item that grants no approval."""

    payload = {
        "review_item_id": review_item_id,
        "candidate_ids": tuple(sorted(candidate_ids)),
        "candidate_eligibility_statuses": tuple(
            status.value for status in candidate_eligibility_statuses
        ),
    }
    return PublicResearchPilotOperatorReviewItem(
        review_item_id=review_item_id,
        candidate_ids=tuple(sorted(candidate_ids)),
        candidate_eligibility_statuses=tuple(
            sorted(candidate_eligibility_statuses, key=lambda status: status.value)
        ),
        fingerprint=public_research_fingerprint(payload),
    )


def build_public_research_evidence_bundle(
    *,
    evidence_bundle_id: str,
    dns_resolution_fingerprints: tuple[str, ...],
    http_exchange_fingerprints: tuple[str, ...],
    redirect_hop_fingerprints: tuple[str, ...],
    robots_policy_fingerprints: tuple[str, ...],
    source_snapshot_fingerprints: tuple[str, ...],
    source_provenance_fingerprints: tuple[str, ...],
    citation_fingerprints: tuple[str, ...],
    verified_candidate_fingerprints: tuple[str, ...],
    incidents: tuple[PublicResearchPilotIncident, ...],
    operator_review_items: tuple[PublicResearchPilotOperatorReviewItem, ...],
) -> PublicResearchPilotEvidenceBundle:
    """Build a final source-body-free evidence bundle."""

    payload = {
        "evidence_bundle_id": evidence_bundle_id,
        "dns_resolution_fingerprints": tuple(sorted(dns_resolution_fingerprints)),
        "http_exchange_fingerprints": tuple(sorted(http_exchange_fingerprints)),
        "redirect_hop_fingerprints": tuple(sorted(redirect_hop_fingerprints)),
        "robots_policy_fingerprints": tuple(sorted(robots_policy_fingerprints)),
        "source_snapshot_fingerprints": tuple(sorted(source_snapshot_fingerprints)),
        "source_provenance_fingerprints": tuple(sorted(source_provenance_fingerprints)),
        "citation_fingerprints": tuple(sorted(citation_fingerprints)),
        "verified_candidate_fingerprints": tuple(sorted(verified_candidate_fingerprints)),
        "incidents": tuple(incident.fingerprint for incident in incidents),
        "operator_review_items": tuple(item.fingerprint for item in operator_review_items),
    }
    return PublicResearchPilotEvidenceBundle(
        evidence_bundle_id=evidence_bundle_id,
        dns_resolution_fingerprints=tuple(sorted(dns_resolution_fingerprints)),
        http_exchange_fingerprints=tuple(sorted(http_exchange_fingerprints)),
        redirect_hop_fingerprints=tuple(sorted(redirect_hop_fingerprints)),
        robots_policy_fingerprints=tuple(sorted(robots_policy_fingerprints)),
        source_snapshot_fingerprints=tuple(sorted(source_snapshot_fingerprints)),
        source_provenance_fingerprints=tuple(sorted(source_provenance_fingerprints)),
        citation_fingerprints=tuple(sorted(citation_fingerprints)),
        verified_candidate_fingerprints=tuple(sorted(verified_candidate_fingerprints)),
        incidents=incidents,
        operator_review_items=operator_review_items,
        bundle_fingerprint=public_research_fingerprint(payload),
    )


__all__ = [
    "build_public_research_diagnostics",
    "build_public_research_evidence_bundle",
    "build_public_research_incident",
    "build_public_research_operator_review_item",
]

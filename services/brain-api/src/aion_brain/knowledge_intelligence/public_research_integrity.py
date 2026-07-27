"""Integrity audit for AION-219 public research pilot results."""

from __future__ import annotations

from collections.abc import Mapping

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchPilotIntegrityFinding,
    PublicResearchPilotIntegrityReport,
    public_research_fingerprint,
    validate_safe_identifier,
)

REQUIRED_INTEGRITY_CHECKS: tuple[str, ...] = (
    "authorization_exact",
    "invocation_envelope_valid",
    "plan_valid",
    "source_candidates_explicit",
    "allowlist_exact",
    "claim_specifications_explicit",
    "dns_resolutions_valid",
    "every_address_public",
    "dns_pinning_used",
    "peer_address_verified",
    "tls_certificate_verified",
    "hostname_verified",
    "tls_minimum_enforced",
    "proxy_inheritance_absent",
    "methods_read_only",
    "redirects_revalidated",
    "request_headers_fixed",
    "response_limits_enforced",
    "compression_absent",
    "content_type_allowed",
    "character_encoding_allowed",
    "robots_policy_passed",
    "licence_policy_passed",
    "source_bodies_purged",
    "source_snapshots_resolve",
    "provenance_resolves",
    "citations_resolve",
    "source_independence_preserved",
    "claim_references_resolve",
    "assessment_references_resolve",
    "domain_mesh_references_resolve",
    "tool_verification_references_resolve",
    "candidate_lineage_complete",
    "candidate_confidence_non_amplified",
    "operator_review_required",
    "automatic_promotion_false",
    "persistent_write_false",
    "cognitive_memory_write_false",
    "belief_mutation_false",
    "background_execution_false",
    "production_exposure_false",
)


def audit_public_research_pilot_integrity(
    *,
    report_id: str,
    checks: Mapping[str, bool],
) -> PublicResearchPilotIntegrityReport:
    """Build a redacted integrity report from explicit invariant checks."""

    findings = tuple(
        _finding(index=index, reason_code=reason_code, passed=bool(checks.get(reason_code)))
        for index, reason_code in enumerate(REQUIRED_INTEGRITY_CHECKS, start=1)
    )
    payload = {
        "report_id": report_id,
        "findings": tuple(finding.fingerprint for finding in findings),
        "passed": all(finding.passed for finding in findings),
    }
    return PublicResearchPilotIntegrityReport(
        report_id=report_id,
        passed=all(finding.passed for finding in findings),
        findings=findings,
        finding_count=len(findings),
        report_fingerprint=public_research_fingerprint(payload),
    )


def passing_public_research_integrity_checks() -> dict[str, bool]:
    """Return the all-pass baseline used by successful deterministic pilots."""

    return {reason_code: True for reason_code in REQUIRED_INTEGRITY_CHECKS}


def _finding(
    *,
    index: int,
    reason_code: str,
    passed: bool,
) -> PublicResearchPilotIntegrityFinding:
    safe_reason = validate_safe_identifier(reason_code, "integrity reason")
    payload = {"reason_code": safe_reason, "passed": passed}
    return PublicResearchPilotIntegrityFinding(
        finding_id=f"public-research-integrity-{index:04d}",
        passed=passed,
        reason_code=safe_reason,
        redacted_summary=f"{safe_reason}={'passed' if passed else 'failed'}",
        fingerprint=public_research_fingerprint(payload),
    )


__all__ = [
    "REQUIRED_INTEGRITY_CHECKS",
    "audit_public_research_pilot_integrity",
    "passing_public_research_integrity_checks",
]

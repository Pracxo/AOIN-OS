"""Integrity audits for simulation-only tool verification sessions."""

from __future__ import annotations

from aion_brain.contracts.knowledge_tool_verification import (
    ToolIntegrityStatus,
    ToolVerificationIntegrityFinding,
    ToolVerificationIntegrityReport,
    ToolVerificationResourceUsage,
    ToolVerificationSession,
    tool_integrity_finding_fingerprint,
    tool_integrity_report_fingerprint,
)
from aion_brain.knowledge_intelligence.tool_attestation import attestation_chain_is_valid


def runtime_counters_zero(usage: ToolVerificationResourceUsage) -> bool:
    """Return true when every prohibited execution/write counter is zero."""

    return all(
        value == 0
        for value in (
            usage.persistent_tool_state_write_batch,
            usage.actual_tool_executions,
            usage.shell_commands,
            usage.subprocess_executions,
            usage.network_calls,
            usage.dns_resolutions,
            usage.browser_actions,
            usage.connector_calls,
            usage.model_provider_calls,
            usage.filesystem_mutations,
            usage.source_mutations,
            usage.git_operations,
            usage.runtime_created_pull_requests,
            usage.approvals_created,
            usage.autonomous_actions,
            usage.high_stakes_actions,
            usage.deployments,
            usage.knowledge_promotions,
            usage.belief_mutations,
            usage.model_weight_changes,
        )
    )


def _integrity_finding(
    *,
    finding_id: str,
    status: ToolIntegrityStatus,
    reason_codes: tuple[str, ...],
) -> ToolVerificationIntegrityFinding:
    payload = {
        "finding_id": finding_id,
        "status": status,
        "reason_codes": reason_codes,
    }
    return ToolVerificationIntegrityFinding.model_validate(
        {**payload, "finding_fingerprint": tool_integrity_finding_fingerprint(payload)}
    )


def audit_tool_verification_session(
    session: ToolVerificationSession,
) -> ToolVerificationIntegrityReport:
    """Audit fingerprints, attestation chain, and zero runtime counters."""

    chain_valid = attestation_chain_is_valid(session.attestations)
    counters_zero = runtime_counters_zero(session.resource_usage)
    findings = (
        _integrity_finding(
            finding_id=f"integrity-{session.session_id}-attestation-chain",
            status=ToolIntegrityStatus.PASS_ if chain_valid else ToolIntegrityStatus.FAIL,
            reason_codes=("tool_attestation_chained",)
            if chain_valid
            else ("tool_attestation_invalid",),
        ),
        _integrity_finding(
            finding_id=f"integrity-{session.session_id}-runtime-counters",
            status=ToolIntegrityStatus.PASS_ if counters_zero else ToolIntegrityStatus.FAIL,
            reason_codes=("tool_actual_execution_blocked",)
            if counters_zero
            else ("tool_integrity_failed",),
        ),
    )
    status = (
        ToolIntegrityStatus.PASS_ if chain_valid and counters_zero else ToolIntegrityStatus.FAIL
    )
    payload = {
        "schema_version": "aion-knowledge-tool-verification-integrity/v1",
        "report_id": f"integrity-report-{session.session_id}",
        "session_id": session.session_id,
        "status": status,
        "findings": findings,
        "resource_usage": session.resource_usage,
        "attestation_chain_valid": chain_valid,
        "runtime_counters_zero": counters_zero,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ToolVerificationIntegrityReport.model_validate(
        {**payload, "report_fingerprint": tool_integrity_report_fingerprint(payload)}
    )


__all__ = ["audit_tool_verification_session", "runtime_counters_zero"]

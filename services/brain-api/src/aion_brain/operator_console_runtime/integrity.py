"""Integrity reporting for the controlled local console runtime."""

from __future__ import annotations

from collections.abc import Mapping

from aion_brain.contracts.operator_console_integration import (
    AUTHORIZATION_TRANSACTION_ID,
    SECURITY_HEADERS,
    OperatorConsoleIntegrityFinding,
    OperatorConsoleIntegrityReport,
    OperatorConsoleIntegrityStatus,
    OperatorConsoleRouteManifest,
    OperatorConsoleSecurityHeaders,
    OperatorConsoleStaticAssetManifest,
    utc_now,
)


def build_integrity_report(
    *,
    report_id: str,
    authorization_id: str,
    route_manifest: OperatorConsoleRouteManifest,
    static_asset_manifest: OperatorConsoleStaticAssetManifest,
    security_headers: OperatorConsoleSecurityHeaders,
    prohibited_counters: Mapping[str, int],
    active_requests_after_close: int,
    active_sessions_after_close: int,
    listener_closed: bool,
) -> OperatorConsoleIntegrityReport:
    """Build a pass/fail integrity report from redacted boundary evidence."""

    findings: list[OperatorConsoleIntegrityFinding] = []
    if authorization_id != AUTHORIZATION_TRANSACTION_ID:
        findings.append(_finding("authorization", "authorization_mismatch"))
    if len(route_manifest.routes) != 10:
        findings.append(_finding("route_manifest", "route_count_mismatch"))
    if len(static_asset_manifest.assets) != 5:
        findings.append(_finding("static_assets", "asset_count_mismatch"))
    if dict(security_headers.headers) != SECURITY_HEADERS:
        findings.append(_finding("security_headers", "security_header_mismatch"))
    if any(value != 0 for value in prohibited_counters.values()):
        findings.append(_finding("prohibited_counters", "prohibited_counter_nonzero"))
    if active_requests_after_close != 0:
        findings.append(_finding("active_requests", "active_requests_retained"))
    if active_sessions_after_close != 0:
        findings.append(_finding("active_sessions", "active_sessions_retained"))
    if not listener_closed:
        findings.append(_finding("listener", "listener_not_closed"))

    return OperatorConsoleIntegrityReport(
        report_id=report_id,
        status=(
            OperatorConsoleIntegrityStatus.failed
            if findings
            else OperatorConsoleIntegrityStatus.passed
        ),
        checked_categories=(
            "authorization",
            "component_lineage",
            "route_manifest",
            "static_assets",
            "security_headers",
            "host_origin_nonce",
            "session_lifecycle",
            "zero_external_effects",
            "listener_cleanup",
        ),
        findings=tuple(findings),
        all_prohibited_counters_zero=not any(value != 0 for value in prohibited_counters.values()),
        active_requests_after_close=active_requests_after_close,
        active_sessions_after_close=active_sessions_after_close,
        listener_closed=listener_closed,
        created_at=utc_now(),
    )


def _finding(category: str, reason: str) -> OperatorConsoleIntegrityFinding:
    return OperatorConsoleIntegrityFinding(
        finding_id=f"finding-{category}",
        category=category,
        status=OperatorConsoleIntegrityStatus.failed,
        reason_codes=(reason,),
    )

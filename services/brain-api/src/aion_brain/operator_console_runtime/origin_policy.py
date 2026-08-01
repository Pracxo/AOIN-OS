"""Same-origin and numeric loopback policy for AION-237."""

from __future__ import annotations

from collections.abc import Sequence

from aion_brain.contracts.operator_console_integration import (
    LOOPBACK_BIND_HOST,
    OperatorConsoleOriginDecision,
    OperatorConsoleOriginDecisionRecord,
    OperatorConsoleOriginPolicy,
    fingerprint_text,
    utc_now,
)

FORWARDED_HEADER_NAMES = (
    "Forwarded",
    "X-Forwarded-For",
    "X-Forwarded-Host",
    "X-Forwarded-Proto",
    "Via",
)


def validate_loopback_bind_address(host: str) -> None:
    if host != LOOPBACK_BIND_HOST:
        raise ValueError("bind host rejected")


def bound_origin(port: int) -> str:
    if port < 1 or port > 65535:
        raise ValueError("port is outside TCP range")
    return f"http://{LOOPBACK_BIND_HOST}:{port}"


def create_origin_policy(port: int) -> OperatorConsoleOriginPolicy:
    return OperatorConsoleOriginPolicy(bound_port=port, bound_origin=bound_origin(port))


def validate_request_target(target: str, *, method: str) -> None:
    if not target or "\x00" in target or "\\" in target:
        raise ValueError("request target rejected")
    lowered = target.lower()
    if target.startswith("//") or "://" in target or method.upper() == "CONNECT":
        raise ValueError("request target rejected")
    if not target.startswith("/"):
        raise ValueError("request target rejected")
    if any(marker in lowered for marker in ("%2f", "%5c", "%00", "%2e")):
        raise ValueError("request target rejected")
    path, _, query = target.partition("?")
    if ";" in path:
        raise ValueError("request target rejected")
    parts = [part for part in path.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise ValueError("request target rejected")
    if method.upper() == "POST" and query:
        raise ValueError("action route query strings are rejected")


def validate_host_header(values: Sequence[str], *, port: int) -> str:
    if len(values) != 1:
        raise ValueError("Host header rejected")
    expected = f"{LOOPBACK_BIND_HOST}:{port}"
    if values[0] != expected:
        raise ValueError("Host header rejected")
    return values[0]


def validate_origin_header(values: Sequence[str], *, method: str, port: int) -> str:
    if method.upper() != "POST":
        if len(values) > 1:
            raise ValueError("Origin header rejected")
        if values and values[0] != bound_origin(port):
            raise ValueError("Origin header rejected")
        return values[0] if values else ""
    if len(values) != 1 or values[0] != bound_origin(port):
        raise ValueError("Origin header rejected")
    return values[0]


def validate_forwarded_headers(header_names: Sequence[str]) -> None:
    lowered = {name.lower() for name in header_names}
    if any(name.lower() in lowered for name in FORWARDED_HEADER_NAMES):
        raise ValueError("forwarded request rejected")


def validate_fetch_metadata(value: str | None, *, method: str) -> None:
    if value is None or value == "":
        return
    normalized = value.strip().lower()
    if normalized == "cross-site":
        raise ValueError("cross-site request rejected")
    if method.upper() == "POST" and normalized == "same-site":
        raise ValueError("same-site state-changing request rejected")
    if normalized not in {"same-origin", "none"}:
        raise ValueError("fetch metadata rejected")


def decision_record(
    *,
    request_id: str,
    method: str,
    route_path: str,
    decision: OperatorConsoleOriginDecision,
    host_value: str,
    origin_value: str,
    reason_codes: tuple[str, ...],
) -> OperatorConsoleOriginDecisionRecord:
    return OperatorConsoleOriginDecisionRecord(
        request_id=request_id,
        method=method,
        route_path=route_path,
        decision=decision,
        host_fingerprint=fingerprint_text("host", host_value),
        origin_fingerprint=fingerprint_text("origin", origin_value),
        reason_codes=reason_codes,
        created_at=utc_now(),
    )

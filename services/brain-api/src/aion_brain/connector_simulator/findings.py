"""Connector simulator finding helpers."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.connector_simulator.redaction import payload_findings
from aion_brain.contracts.connector_simulator import ConnectorSimulatorFinding, utc_now

_FINDING_META = {
    "secret_detected": ("critical", "Secret-like simulator material detected."),
    "raw_prompt_detected": ("high", "Raw prompt material detected."),
    "hidden_reasoning_detected": ("high", "Private reasoning material detected."),
    "external_url_detected": ("critical", "External endpoint material detected."),
    "credential_field_detected": ("critical", "Credential field detected."),
    "token_field_detected": ("critical", "Token field detected."),
    "unsafe_request_shape": ("high", "Unsafe request shape detected."),
    "unsafe_response_shape": ("high", "Unsafe response shape detected."),
    "untrusted_ingress": ("medium", "Connector ingress remains untrusted."),
    "missing_policy_action": ("high", "Required connector policy action missing."),
    "sandbox_required": ("high", "Connector sandbox proof is required."),
}


class ConnectorSimulatorFindingService:
    """Create safe simulator findings from synthetic payloads."""

    def findings_for_payload(
        self,
        connector_key: str,
        payload: Any,
        *,
        source: str,
    ) -> list[ConnectorSimulatorFinding]:
        """Return findings for unsafe synthetic payload content."""

        findings: list[ConnectorSimulatorFinding] = []
        for raw in payload_findings(payload):
            finding_type = str(raw.get("finding_type") or "generic")
            findings.append(self.create(connector_key, finding_type, source=source, metadata=raw))
        return findings

    def create(
        self,
        connector_key: str,
        finding_type: str,
        *,
        source: str,
        metadata: dict[str, object] | None = None,
    ) -> ConnectorSimulatorFinding:
        """Create one simulator finding."""

        severity, title = _FINDING_META.get(finding_type, ("medium", "Connector finding."))
        return ConnectorSimulatorFinding(
            connector_simulator_finding_id=f"connector-simulator-finding-{uuid4().hex}",
            connector_key=connector_key,
            finding_type=finding_type,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            status="open",
            title=title,
            description=f"{title} Source: {source}.",
            recommended_action="Keep connector simulation synthetic and remove unsafe material.",
            refs=["docs/connectors/connector-simulation-safety.md"],
            metadata={"source": source, **(metadata or {})},
            created_at=utc_now(),
        )


def findings_to_dicts(findings: list[ConnectorSimulatorFinding]) -> list[dict[str, Any]]:
    """Serialize simulator findings for result payloads."""

    return [finding.model_dump(mode="json") for finding in findings]


__all__ = ["ConnectorSimulatorFindingService", "findings_to_dicts"]

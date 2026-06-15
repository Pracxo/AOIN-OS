"""Default local security baseline catalog entries."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.security_baseline import (
    RiskLevel,
    SecurityControlRecord,
    ThreatCategory,
    ThreatModelRecord,
)

DEFAULT_THREAT_KEYS = (
    "api_error_leakage",
    "raw_secret_storage",
    "external_model_exfiltration",
    "mcp_uncontrolled_tool_execution",
    "sandbox_escape_future_risk",
    "backup_sensitive_data_leakage",
    "release_package_secret_leakage",
    "autonomy_unintended_execution",
    "policy_fail_open",
    "provider_object_leakage",
    "connector_uncontrolled_egress",
    "memory_ungoverned_recall",
    "evidence_grounding_bypass",
    "command_replay_duplicate_effect",
    "outbox_duplicate_delivery",
    "restore_overwrite_risk",
)

DEFAULT_CONTROL_KEYS = (
    "api.error_contracts.no_stacktrace",
    "api.request_audit.no_body_storage",
    "policy.fail_closed",
    "autonomy.no_full_default",
    "sandbox.execution_disabled_default",
    "secrets.metadata_only",
    "connectors.metadata_only",
    "backups.redaction_default",
    "release.no_env_files",
    "adapters.optional_default",
    "mcp.disabled_default",
    "model_gateway.external_disabled_default",
    "restore.apply_disabled_default",
    "command.idempotency_supported",
    "outbox.manual_processing_default",
)


def default_threat_model_records(owner_scope: list[str]) -> list[ThreatModelRecord]:
    """Return generic default threat model records."""
    now = datetime.now(UTC)
    return [
        ThreatModelRecord(
            threat_model_id=f"threat-{key}",
            name=key.replace("_", " ").title(),
            description=f"Generic local risk for {key.replace('_', ' ')}.",
            status="open",
            category=_threat_category(key),
            asset_type=_asset_type(key),
            threat_type=key,
            severity=_severity(key),
            likelihood="medium",
            impact="high" if _severity(key) in {"high", "critical"} else "medium",
            controls=_controls_for_threat(key),
            residual_risk="medium",
            owner_scope=owner_scope,
            metadata={"source": "aion_security_baseline_defaults"},
            created_at=now,
            updated_at=now,
        )
        for key in DEFAULT_THREAT_KEYS
    ]


def default_security_controls() -> list[SecurityControlRecord]:
    """Return generic default security controls."""
    now = datetime.now(UTC)
    return [
        SecurityControlRecord(
            security_control_id=f"control-{key.replace('.', '-')}",
            control_key=key,
            name=key.replace(".", " ").replace("_", " ").title(),
            description=f"Local deterministic control for {key}.",
            category=_control_category(key),
            status="implemented" if _implemented_by_default(key) else "partial",
            required=True,
            evidence_refs=[],
            implementation_refs=_implementation_refs(key),
            metadata={"source": "aion_security_baseline_defaults"},
            created_at=now,
            updated_at=now,
        )
        for key in DEFAULT_CONTROL_KEYS
    ]


def _threat_category(key: str) -> ThreatCategory:
    if key.startswith("api"):
        return "api"
    if key.startswith("raw_secret"):
        return "configuration"
    if key.startswith("external_model") or key.startswith("provider"):
        return "model_gateway"
    if key.startswith("mcp"):
        return "mcp"
    if key.startswith("sandbox"):
        return "sandbox"
    if key.startswith("backup"):
        return "backup"
    if key.startswith("release"):
        return "release"
    if key.startswith("autonomy"):
        return "autonomy"
    if key.startswith("policy"):
        return "policy"
    if key.startswith("connector"):
        return "connector"
    if key.startswith("memory"):
        return "memory"
    if key.startswith("evidence"):
        return "evidence"
    return "configuration"


def _asset_type(key: str) -> str:
    return key.split("_", maxsplit=1)[0]


def _severity(key: str) -> RiskLevel:
    if key in {"raw_secret_storage", "policy_fail_open", "sandbox_escape_future_risk"}:
        return "high"
    return "medium"


def _controls_for_threat(key: str) -> list[str]:
    if "secret" in key:
        return ["secrets.metadata_only", "release.no_env_files"]
    if "policy" in key:
        return ["policy.fail_closed"]
    if "autonomy" in key:
        return ["autonomy.no_full_default"]
    if "sandbox" in key:
        return ["sandbox.execution_disabled_default"]
    if "backup" in key:
        return ["backups.redaction_default"]
    if "model" in key or "provider" in key:
        return ["model_gateway.external_disabled_default", "adapters.optional_default"]
    if "mcp" in key:
        return ["mcp.disabled_default"]
    return ["api.error_contracts.no_stacktrace"]


def _control_category(key: str) -> ThreatCategory:
    head = key.split(".", maxsplit=1)[0]
    mapping: dict[str, ThreatCategory] = {
        "api": "api",
        "policy": "policy",
        "autonomy": "autonomy",
        "sandbox": "sandbox",
        "secrets": "configuration",
        "connectors": "connector",
        "backups": "backup",
        "release": "release",
        "adapters": "configuration",
        "mcp": "mcp",
        "model_gateway": "model_gateway",
        "restore": "backup",
        "command": "api",
        "outbox": "api",
    }
    return mapping.get(head, "configuration")


def _implementation_refs(key: str) -> list[str]:
    refs = {
        "api.error_contracts.no_stacktrace": ["aion_brain.api_support.exception_handlers"],
        "api.request_audit.no_body_storage": ["aion_brain.api_support.request_audit"],
        "policy.fail_closed": ["aion_brain.policy.opa_adapter"],
        "sandbox.execution_disabled_default": ["aion_brain.config.Settings"],
        "release.no_env_files": ["aion_brain.release_package.validator"],
    }
    return refs.get(key, ["aion_brain.config.Settings"])


def _implemented_by_default(key: str) -> bool:
    return key not in {"command.idempotency_supported", "outbox.manual_processing_default"}

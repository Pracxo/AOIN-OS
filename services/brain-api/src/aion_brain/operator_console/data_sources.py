"""Read-only data source map for future Operator Console views."""

# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from aion_brain.contracts.operator_console import ConsoleDataSource, ConsoleView


@dataclass(frozen=True)
class ConsoleSourceSpec:
    """Static data-source mapping for one console section."""

    source_key: str
    source_type: str
    service_name: str
    endpoint_hint: str | None = None
    cli_hint: str | None = None


DATA_SOURCE_MAP: Final[dict[ConsoleView, tuple[ConsoleSourceSpec, ...]]] = {
    "overview": (
        ConsoleSourceSpec("operator_overview", "operator", "operator_control_tower_service", "/brain/operator/overview", "aionctl operator overview"),
        ConsoleSourceSpec("health", "health", "health", "/health", "aionctl health"),
        ConsoleSourceSpec("readiness", "health", "health", "/health/ready", "aionctl ready"),
        ConsoleSourceSpec("notifications", "notifications", "notification_query_service", "/brain/notifications/query", "aionctl notifications alerts"),
        ConsoleSourceSpec("incidents", "incidents", "incident_service", "/brain/incidents", "aionctl incidents list"),
    ),
    "readiness": (
        ConsoleSourceSpec("bootstrap", "bootstrap", "bootstrap_query_service", "/brain/bootstrap/reports", "aionctl bootstrap doctor"),
        ConsoleSourceSpec("setup_doctor", "bootstrap", "setup_doctor", "/brain/bootstrap/doctor", "./scripts/setup-doctor.sh --fast --offline-ok"),
        ConsoleSourceSpec("golden_path", "golden_path", "golden_path_repository", "/brain/golden-path/runs", "./scripts/golden-path.sh --offline-ok"),
        ConsoleSourceSpec("release_smoke", "golden_path", "golden_path_release_smoke", None, "./scripts/release-smoke.sh --offline-ok"),
    ),
    "release_candidate": (
        ConsoleSourceSpec("rc_gate", "release", "release_candidate_gate", "/brain/rc/gate/run", "./scripts/rc-check.sh --offline-ok"),
        ConsoleSourceSpec("rc_reports", "release", "release_candidate_report_service", "/brain/rc/reports", "aionctl rc reports"),
        ConsoleSourceSpec("rc_findings", "release", "release_candidate_repository", "/brain/rc/findings", "aionctl rc findings"),
        ConsoleSourceSpec("rc_evidence", "release", "release_candidate_repository", "/brain/rc/evidence-packs", "aionctl rc evidence"),
    ),
    "freeze_release": (
        ConsoleSourceSpec("freeze_gate", "release", "freeze_gate_service", "/brain/freeze/run", "aionctl freeze run"),
        ConsoleSourceSpec("release_package", "release", "release_package_service", "/brain/release/packages", "./scripts/package-release.sh --dry-run"),
        ConsoleSourceSpec("release_baseline", "release", "release_baseline_service", "/brain/release/baseline", "aionctl release baseline"),
    ),
    "golden_path": (
        ConsoleSourceSpec("golden_path", "golden_path", "golden_path_repository", "/brain/golden-path/runs", "./scripts/golden-path.sh --offline-ok"),
        ConsoleSourceSpec("golden_path_reports", "golden_path", "golden_path_report_service", "/brain/golden-path/reports", "aionctl golden-path reports"),
    ),
    "module_lifecycle": (
        ConsoleSourceSpec("extensions", "module", "extension_registry_repository", "/brain/extensions", "aionctl extensions validate"),
        ConsoleSourceSpec("module_bindings", "module", "module_binding_repository", "/brain/module-bindings", "aionctl module-bindings validate --dry-run"),
        ConsoleSourceSpec("conformance", "module", "conformance_repository", "/brain/conformance/runs", "aionctl conformance run"),
        ConsoleSourceSpec("readiness", "module", "readiness_assessment_service", "/brain/conformance/readiness", "aionctl readiness assess"),
        ConsoleSourceSpec("module_activation", "module", "module_activation_repository", "/brain/module-activation/gates", "aionctl module-activation gate"),
        ConsoleSourceSpec("module_mock_runtime", "module", "module_mock_repository", "/brain/module-mock/runs", "aionctl module-mock runs"),
    ),
    "module_activation": (
        ConsoleSourceSpec("module_activation", "module", "module_activation_repository", "/brain/module-activation/gates", "aionctl module-activation gate"),
        ConsoleSourceSpec("activation_blockers", "module", "module_activation_repository", "/brain/module-activation/blockers", "aionctl module-activation blockers"),
    ),
    "module_mock_runtime": (
        ConsoleSourceSpec("module_mock_runtime", "module", "module_mock_repository", "/brain/module-mock/runs", "aionctl module-mock runs"),
        ConsoleSourceSpec("module_mock_findings", "module", "module_mock_repository", "/brain/module-mock/findings", "aionctl module-mock findings"),
    ),
    "model_provider_hardening": (
        ConsoleSourceSpec("model_provider_profiles", "provider", "model_provider_profile_service", "/brain/model-providers/profiles", "aionctl model-providers profiles list"),
        ConsoleSourceSpec("prompt_egress", "provider", "prompt_egress_guard", "/brain/model-providers/egress-preview", "aionctl model-providers egress-preview"),
        ConsoleSourceSpec("provider_simulation", "provider", "model_provider_simulator", "/brain/model-providers/simulate", "aionctl model-providers simulate"),
        ConsoleSourceSpec("provider_readiness", "provider", "model_provider_readiness_service", "/brain/model-providers/readiness", "aionctl model-providers readiness"),
        ConsoleSourceSpec("provider_blockers", "provider", "model_provider_blocker_service", "/brain/model-providers/blockers", "aionctl model-providers blockers"),
    ),
    "notifications": (
        ConsoleSourceSpec("notifications", "notifications", "notification_query_service", "/brain/notifications/query", "aionctl notifications alerts"),
        ConsoleSourceSpec("alerts", "notifications", "alert_service", "/brain/alerts/query", "aionctl notifications alerts"),
        ConsoleSourceSpec("escalations", "notifications", "escalation_service", "/brain/escalations", "aionctl notifications escalations"),
        ConsoleSourceSpec("digests", "notifications", "notification_digest_service", "/brain/notifications/digests", "aionctl notifications digests"),
    ),
    "incidents": (
        ConsoleSourceSpec("incident_signals", "incidents", "incident_signal_service", "/brain/incidents/signals", "aionctl incidents list"),
        ConsoleSourceSpec("incident_records", "incidents", "incident_service", "/brain/incidents", "aionctl incidents list"),
        ConsoleSourceSpec("root_cause_candidates", "incidents", "root_cause_candidate_service", "/brain/incidents/root-causes", "aionctl incidents root-causes"),
        ConsoleSourceSpec("recovery_reviews", "incidents", "recovery_review_service", "/brain/incidents/recovery-reviews", "aionctl incidents recovery-reviews"),
    ),
    "registry_integrity": (
        ConsoleSourceSpec("resource_registry", "registry", "registry_query_service", "/brain/resources/query", "aionctl resources validate"),
        ConsoleSourceSpec("link_validation", "registry", "reference_validator", "/brain/resources/validate", "aionctl resources validate"),
        ConsoleSourceSpec("snapshots", "registry", "registry_snapshot_service", "/brain/resources/snapshots", "aionctl resources snapshots"),
    ),
    "lifecycle_review": (
        ConsoleSourceSpec("lifecycle_policies", "lifecycle", "lifecycle_policy_service", "/brain/lifecycle/policies", "aionctl lifecycle evaluate"),
        ConsoleSourceSpec("classifications", "lifecycle", "retention_classifier", "/brain/lifecycle/classify", "aionctl lifecycle evaluate"),
        ConsoleSourceSpec("archive_candidates", "lifecycle", "archive_planner", "/brain/lifecycle/archive-candidates", "aionctl lifecycle evaluate"),
        ConsoleSourceSpec("redaction_candidates", "lifecycle", "redaction_planner", "/brain/lifecycle/redaction-candidates", "aionctl lifecycle evaluate"),
        ConsoleSourceSpec("purge_previews", "lifecycle", "purge_preview_service", "/brain/lifecycle/purge-preview", "aionctl lifecycle purge-preview"),
    ),
    "audit_provenance": (
        ConsoleSourceSpec("audit_entries", "audit", "audit_integrity_ledger", "/brain/audit-integrity/entries", "./scripts/audit-verify.sh"),
        ConsoleSourceSpec("provenance_links", "audit", "provenance_service", "/brain/audit-integrity/provenance", "./scripts/audit-verify.sh"),
    ),
    "settings_safety": (
        ConsoleSourceSpec("runtime_config", "settings", "runtime_config_status_service", "/brain/runtime-config/status", "./scripts/config-validate.sh"),
        ConsoleSourceSpec("security_baseline", "settings", "security_baseline_service", "/brain/security-baseline/reports", "./scripts/security-scan.sh"),
        ConsoleSourceSpec("feature_flags", "settings", "feature_registry", "/brain/runtime-config/features", "./scripts/config-validate.sh"),
    ),
    "generic": (
        ConsoleSourceSpec("generic", "generic", "operator_control_tower_service", None, None),
    ),
}


def view_data_sources(
    view: ConsoleView,
    *,
    owner_scope: list[str],
    container: object | None = None,
) -> list[ConsoleDataSource]:
    """Return data source contracts for a view."""
    result: list[ConsoleDataSource] = []
    for spec in DATA_SOURCE_MAP.get(view, DATA_SOURCE_MAP["generic"]):
        available = container is None or getattr(container, spec.service_name, None) is not None
        result.append(
            ConsoleDataSource(
                data_source_id=f"{view}.{spec.source_key}",
                source_key=spec.source_key,
                source_type=spec.source_type,
                service_name=spec.service_name,
                endpoint_hint=spec.endpoint_hint,
                cli_hint=spec.cli_hint,
                status="available" if available else "unavailable",
                available=available,
                read_only=True,
                owner_scope=owner_scope,
                metadata={"view": view},
            )
        )
    return result


def list_console_views() -> list[ConsoleView]:
    """Return all defined console views."""
    return [view for view in DATA_SOURCE_MAP if view != "generic"]


__all__ = ["DATA_SOURCE_MAP", "ConsoleSourceSpec", "list_console_views", "view_data_sources"]

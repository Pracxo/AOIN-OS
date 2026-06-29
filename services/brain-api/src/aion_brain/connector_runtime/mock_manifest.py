"""Mock connector manifest validation service."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.connector_runtime.blockers import blocker
from aion_brain.contracts.connector_runtime import (
    MockConnectorManifest,
    MockConnectorManifestValidationResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class MockConnectorManifestService:
    """Validate mock connector declarations without enabling connectors."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def validate(
        self,
        manifest: MockConnectorManifest,
    ) -> MockConnectorManifestValidationResult:
        """Validate one synthetic manifest and return normalized preview evidence."""

        validation_id = f"connector-manifest-validation-{uuid4().hex}"
        blockers = []
        if manifest.external_calls_required:
            blockers.append(
                blocker(
                    "manifest_external_calls_required",
                    "external_calls_required_not_allowed",
                    source_type="mock_connector_manifest",
                    source_id=validation_id,
                    severity="critical",
                )
            )
        if manifest.credentials_required:
            blockers.append(
                blocker(
                    "manifest_credentials_required",
                    "credentials_required_not_allowed",
                    source_type="mock_connector_manifest",
                    source_id=validation_id,
                    severity="critical",
                )
            )
        if manifest.routes_declared:
            blockers.append(
                blocker(
                    "manifest_routes_declared",
                    "routes_declared_not_allowed",
                    source_type="mock_connector_manifest",
                    source_id=validation_id,
                    severity="critical",
                )
            )
        if not manifest.dry_run_supported:
            blockers.append(
                blocker(
                    "generic",
                    "dry_run_required",
                    source_type="mock_connector_manifest",
                    source_id=validation_id,
                    severity="high",
                )
            )
        result = MockConnectorManifestValidationResult(
            connector_manifest_validation_id=validation_id,
            connector_key=manifest.connector_key,
            status="blocked" if blockers else "preview",
            valid=not blockers,
            external_calls_required=manifest.external_calls_required,
            credentials_required=manifest.credentials_required,
            routes_declared_count=len(manifest.routes_declared),
            blockers=blockers,
            warnings=[{"code": "mock_manifest_not_activation", "status": "open"}],
            normalized_manifest={
                "connector_key": manifest.connector_key,
                "name": manifest.name,
                "version": manifest.version,
                "owner_scope": manifest.owner_scope,
                "connector_type": manifest.connector_type,
                "supported_modes": manifest.supported_modes,
                "declared_capabilities": manifest.declared_capabilities,
                "required_policy_actions": manifest.required_policy_actions,
                "required_scopes": manifest.required_scopes,
                "sandbox_required": manifest.sandbox_required,
                "dry_run_supported": manifest.dry_run_supported,
                "external_calls_required": False,
                "credentials_required": False,
                "routes_declared": [],
            },
            metadata={"mock_only": True, "activation_allowed": False},
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_manifest_validated",
            node_type="connector_manifest",
            node_id=result.connector_manifest_validation_id,
            intensity=0.85 if blockers else 0.6,
            trace_id=result.connector_manifest_validation_id,
            payload={"status": result.status, "mock_only": True},
        )
        return result


__all__ = ["MockConnectorManifestService"]

"""Connector sandbox design boundary."""

from __future__ import annotations

from aion_brain.contracts.connector_sandbox import ConnectorSandboxBoundary, utc_now


class ConnectorSandboxDesignService:
    """Return a local-only sandbox design boundary without sandbox execution."""

    def boundary(self) -> ConnectorSandboxBoundary:
        """Return the current connector sandbox design boundary."""

        return ConnectorSandboxBoundary(
            sandbox_boundary_id="connector-sandbox-boundary-aion-112",
            name="Connector Sandbox Design Boundary",
            description="Design-only sandbox boundary; no real sandbox runtime exists.",
            filesystem_access_allowed=False,
            network_access_allowed=False,
            credential_access_allowed=False,
            token_access_allowed=False,
            process_spawn_allowed=False,
            dynamic_import_allowed=False,
            package_install_allowed=False,
            runtime_execution_allowed=False,
            connector_activation_allowed=False,
            audit_required=True,
            provenance_required=True,
            blockers=[
                {"blocker_key": "real_sandbox_runtime_absent", "bypassable": False},
                {"blocker_key": "connector_runtime_disabled", "bypassable": False},
                {"blocker_key": "filesystem_access_disabled", "bypassable": False},
                {"blocker_key": "network_access_disabled", "bypassable": False},
                {"blocker_key": "credentials_tokens_disabled", "bypassable": False},
                {"blocker_key": "activation_disabled", "bypassable": False},
            ],
            metadata={
                "design_only": True,
                "readiness_preview_only": True,
                "runtime_execution_allowed": False,
                "filesystem_access_allowed": False,
                "network_access_allowed": False,
                "credential_access_allowed": False,
                "token_access_allowed": False,
                "process_spawn_allowed": False,
                "dynamic_import_allowed": False,
                "package_install_allowed": False,
                "connector_activation_allowed": False,
            },
            created_at=utc_now(),
        )


__all__ = ["ConnectorSandboxDesignService"]

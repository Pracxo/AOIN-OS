"""Local auth status query service."""

from __future__ import annotations

from aion_brain.config import Settings, get_settings


class LocalAuthQueryService:
    """Read-only local auth status queries."""

    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def status(self, scope: list[str]) -> dict[str, object]:
        """Return local auth runtime status and no-go flags."""
        return {
            "scope": scope,
            "local_auth_enabled": self._settings.local_auth_enabled,
            "dev_identity_simulation_enabled": (
                self._settings.local_auth_dev_identity_simulation_enabled
            ),
            "role_filtering_enabled": self._settings.local_auth_role_filtering_enabled,
            "local_auth_audit_enabled": self._settings.local_auth_audit_enabled,
            "role_permission_matrix_enabled": self._settings.local_auth_role_matrix_enabled,
            "role_access_audit_enabled": (
                self._settings.local_auth_role_access_audit_enabled
            ),
            "production_auth_enabled": False,
            "credentials_enabled": False,
            "sessions_enabled": False,
            "external_identity_provider_enabled": False,
            "write_actions_enabled": False,
            "no_go_warnings": [
                "no_login_endpoint",
                "no_credentials",
                "no_sessions",
                "no_external_identity_provider",
                "no_execution_grant",
                "no_activation_grant",
            ],
        }


__all__ = ["LocalAuthQueryService"]

"""Local session status query service."""

from __future__ import annotations

from aion_brain.config import Settings, get_settings


class LocalSessionQueryService:
    """Read-only local session status queries."""

    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def status(self, scope: list[str]) -> dict[str, object]:
        """Return local session status and no-go warnings."""
        return {
            "scope": scope,
            "local_session_preview_enabled": self._settings.local_session_preview_enabled,
            "local_session_context_enabled": self._settings.local_session_context_enabled,
            "local_session_audit_enabled": self._settings.local_session_audit_enabled,
            "dev_only": self._settings.local_session_dev_only,
            "read_only": self._settings.local_session_read_only,
            "production_session": False,
            "credential_backed": False,
            "token_issued": False,
            "cookie_issued": False,
            "persistent": False,
            "write_allowed": False,
            "execute_allowed": False,
            "activation_allowed": False,
            "external_calls_allowed": False,
            "credentials_enabled": self._settings.local_session_credentials_enabled,
            "tokens_enabled": self._settings.local_session_tokens_enabled,
            "cookies_enabled": self._settings.local_session_cookies_enabled,
            "persistence_enabled": self._settings.local_session_persistence_enabled,
            "production_auth_enabled": False,
            "no_go_warnings": [
                "no_login_endpoint",
                "no_logout_endpoint",
                "no_credentials",
                "no_tokens",
                "no_cookies",
                "no_persistence",
                "no_execution_grant",
                "no_activation_grant",
                "no_external_calls",
            ],
        }


__all__ = ["LocalSessionQueryService"]

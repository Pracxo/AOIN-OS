"""Disabled production auth runtime gate service."""

from __future__ import annotations

from aion_brain.auth_runtime.blockers import blocker
from aion_brain.contracts.auth_runtime import AuthRuntimeBlocker, AuthRuntimeStatus, utc_now
from aion_brain.dialogue._shared import emit_telemetry


class AuthRuntimeGateService:
    """Expose disabled auth-runtime status without enabling auth behavior."""

    def __init__(
        self,
        *,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._settings = settings
        self._telemetry_service = telemetry_service

    def status(self, scope: list[str]) -> AuthRuntimeStatus:
        """Return disabled production auth runtime status for one scope."""

        status = AuthRuntimeStatus(
            status_id="auth-runtime-status-local",
            production_auth_enabled=bool(
                getattr(self._settings, "production_auth_enabled", False)
            ),
            auth_runtime_enabled=bool(getattr(self._settings, "auth_runtime_enabled", False)),
            mock_claims_preview_enabled=bool(
                getattr(self._settings, "auth_runtime_mock_claims_preview_enabled", True)
            ),
            external_identity_provider_enabled=bool(
                getattr(self._settings, "auth_runtime_external_identity_enabled", False)
                or getattr(self._settings, "external_identity_provider_enabled", False)
            ),
            credentials_enabled=bool(
                getattr(self._settings, "auth_runtime_credentials_enabled", False)
                or getattr(self._settings, "auth_credentials_enabled", False)
            ),
            token_issuance_enabled=bool(
                getattr(self._settings, "auth_runtime_token_issuance_enabled", False)
            ),
            cookie_issuance_enabled=bool(
                getattr(self._settings, "auth_runtime_cookie_issuance_enabled", False)
            ),
            session_persistence_enabled=bool(
                getattr(self._settings, "auth_runtime_session_persistence_enabled", False)
                or getattr(self._settings, "auth_sessions_enabled", False)
            ),
            login_endpoint_enabled=bool(
                getattr(self._settings, "auth_runtime_login_endpoint_enabled", False)
            ),
            logout_endpoint_enabled=bool(
                getattr(self._settings, "auth_runtime_logout_endpoint_enabled", False)
            ),
            actor_mapping_preview_enabled=bool(
                getattr(self._settings, "auth_runtime_actor_mapping_preview_enabled", True)
            ),
            blockers=_disabled_blockers(),
            warnings=[{"code": "prototype_disabled", "status": "open"}],
            metadata={
                "disabled_by_default": True,
                "owner_scope": scope,
                "mock_only": True,
                "runtime_activation_allowed": False,
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="auth_runtime_status_checked",
            node_type="auth_runtime_status",
            node_id=status.status_id,
            intensity=0.65,
            trace_id=status.status_id,
            payload={
                "production_auth_enabled": False,
                "auth_runtime_enabled": False,
                "mock_claims_preview_enabled": status.mock_claims_preview_enabled,
            },
        )
        return status


def _disabled_blockers() -> list[AuthRuntimeBlocker]:
    return [
        blocker(
            "production_auth_disabled",
            "production_auth_disabled_by_default",
            source_type="settings",
            severity="critical",
            recommended_action="Complete production auth release gates before enabling.",
        ),
        blocker(
            "external_identity_disabled",
            "external_identity_provider_disabled",
            source_type="settings",
        ),
        blocker(
            "credentials_disabled",
            "credential_handling_disabled",
            source_type="settings",
        ),
        blocker(
            "token_issuance_disabled",
            "token_issuance_disabled",
            source_type="settings",
        ),
        blocker(
            "cookie_issuance_disabled",
            "cookie_issuance_disabled",
            source_type="settings",
        ),
        blocker(
            "session_persistence_disabled",
            "session_persistence_disabled",
            source_type="settings",
        ),
        blocker(
            "login_endpoint_disabled",
            "login_endpoint_disabled",
            source_type="api",
        ),
        blocker(
            "logout_endpoint_disabled",
            "logout_endpoint_disabled",
            source_type="api",
        ),
    ]


__all__ = ["AuthRuntimeGateService"]

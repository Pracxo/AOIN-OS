"""Status query helpers for dry-run action authorization."""

from __future__ import annotations


class ActionAuthorizationQueryService:
    """Expose action authorization status without mutating state."""

    def __init__(self, *, settings: object | None = None) -> None:
        self._settings = settings

    def status(self, scope: list[str]) -> dict[str, object]:
        """Return current dry-run authorization boundary flags."""

        return {
            "scope": scope,
            "action_authorization_enabled": bool(
                getattr(self._settings, "action_authorization_enabled", True)
            ),
            "dry_run_action_authorization_enabled": bool(
                getattr(self._settings, "dry_run_action_authorization_enabled", True)
            ),
            "action_authorization_audit_enabled": bool(
                getattr(self._settings, "action_authorization_audit_enabled", True)
            ),
            "write_allowed": False,
            "execution_allowed": False,
            "activation_allowed": False,
            "external_calls_allowed": False,
            "authorization_scope": "dry_run_preview_and_review_only",
        }


__all__ = ["ActionAuthorizationQueryService"]

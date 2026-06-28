"""Synthetic local session preview service."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from aion_brain.contracts.local_session import (
    LocalSessionPreview,
    LocalSessionPreviewRequest,
    utc_now,
)
from aion_brain.telemetry.visual import build_operator_console_telemetry_event


class LocalSessionPreviewService:
    """Create read-only, dev-only session previews without persistence."""

    def __init__(
        self,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._telemetry_service = telemetry_service

    def create_preview(self, request: LocalSessionPreviewRequest) -> LocalSessionPreview:
        """Create a synthetic local session preview."""
        now = utc_now()
        preview = LocalSessionPreview(
            local_session_preview_id=f"local-session-preview-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            roles=request.roles,
            owner_scope=request.owner_scope,
            status="active_local_preview",
            session_type=request.session_type,
            read_only=True,
            dev_only=True,
            production_session=False,
            credential_backed=False,
            token_issued=False,
            cookie_issued=False,
            persistent=False,
            write_allowed=False,
            execute_allowed=False,
            activation_allowed=False,
            external_calls_allowed=False,
            expires_at=now + timedelta(seconds=request.ttl_seconds),
            warnings=[
                {"code": "synthetic_preview", "message": "local session preview only"},
                {"code": "no_login_runtime", "message": "no production login was created"},
            ],
            blockers=[],
            metadata={
                **request.metadata,
                "synthetic": True,
                "source": "local_session_preview_service",
                "ttl_seconds": request.ttl_seconds,
            },
            created_at=now,
        )
        _emit(
            self._telemetry_service,
            "local_session_preview_created",
            "local_session_preview",
            preview.local_session_preview_id,
            preview.owner_scope,
            {"roles": preview.roles, "production_session": False},
        )
        return preview

    def status(self, scope: list[str]) -> dict[str, object]:
        """Return local session runtime status and disabled privilege flags."""
        return {
            "scope": scope,
            "local_session_preview_enabled": True,
            "local_session_context_enabled": True,
            "local_session_audit_enabled": True,
            "dev_only": True,
            "read_only": True,
            "production_session": False,
            "credential_backed": False,
            "token_issued": False,
            "cookie_issued": False,
            "persistent": False,
            "write_allowed": False,
            "execute_allowed": False,
            "activation_allowed": False,
            "external_calls_allowed": False,
            "no_go_warnings": [
                "no_login_endpoint",
                "no_credentials",
                "no_tokens",
                "no_cookies",
                "no_session_persistence",
                "no_execution_grant",
                "no_activation_grant",
                "no_external_calls",
            ],
        }


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    scope: list[str],
    payload: dict[str, object] | None = None,
) -> None:
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    emit(
        build_operator_console_telemetry_event(
            telemetry_id=f"telemetry-{node_id}",
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            payload=payload,
        )
    )


__all__ = ["LocalSessionPreviewService"]

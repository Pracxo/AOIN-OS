"""Local session boundary validation."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.contracts.local_session import (
    LocalSessionBoundaryCheck,
    LocalSessionPreview,
    utc_now,
)
from aion_brain.telemetry.visual import build_operator_console_telemetry_event


class LocalSessionBoundaryService:
    """Validate local session previews against AION-095 safety boundaries."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def check(self, preview: LocalSessionPreview | None = None) -> LocalSessionBoundaryCheck:
        """Return boundary status for a preview or the default safe configuration."""
        read_only = preview.read_only if preview else True
        dev_only = preview.dev_only if preview else True
        no_credentials = not preview.credential_backed if preview else True
        no_tokens = not preview.token_issued if preview else True
        no_cookies = not preview.cookie_issued if preview else True
        no_persistence = not preview.persistent if preview else True
        no_execution = not preview.execute_allowed if preview else True
        no_activation = not preview.activation_allowed if preview else True
        no_external = not preview.external_calls_allowed if preview else True
        blockers = [
            {"code": code, "message": message}
            for ok, code, message in (
                (read_only, "write_path_enabled", "session preview was not read-only"),
                (dev_only, "production_path_enabled", "session preview was not dev-only"),
                (no_credentials, "auth_material_present", "credential-like backing found"),
                (no_tokens, "bearer_material_present", "token issuance found"),
                (no_cookies, "browser_state_present", "cookie issuance found"),
                (no_persistence, "state_storage_present", "session persistence found"),
                (no_execution, "execution_enabled", "execution grant found"),
                (no_activation, "activation_enabled", "activation grant found"),
                (no_external, "external_calls_enabled", "external call grant found"),
            )
            if not ok
        ]
        passed = not blockers
        result = LocalSessionBoundaryCheck(
            boundary_check_id=f"local-session-boundary-{uuid4().hex}",
            trace_id=preview.trace_id if preview else None,
            status="passed" if passed else "failed",
            checks_run=[
                "read_only",
                "dev_only",
                "no_credentials",
                "no_tokens",
                "no_cookies",
                "no_persistence",
                "no_execution",
                "no_activation",
                "no_external_calls",
            ],
            read_only_passed=read_only,
            dev_only_passed=dev_only,
            no_credentials_passed=no_credentials,
            no_tokens_passed=no_tokens,
            no_cookies_passed=no_cookies,
            no_persistence_passed=no_persistence,
            no_execution_passed=no_execution,
            no_activation_passed=no_activation,
            no_external_calls_passed=no_external,
            blockers=blockers,
            warnings=[],
            metadata={"local_only": True, "stateless": True},
            created_at=utc_now(),
        )
        _emit(
            self._telemetry_service,
            "local_session_boundary_checked",
            "local_session_preview",
            result.boundary_check_id,
            preview.owner_scope if preview else ["workspace:main"],
            {"status": result.status},
        )
        return result


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


__all__ = ["LocalSessionBoundaryService"]

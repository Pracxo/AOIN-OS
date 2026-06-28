"""Local session safety audit service."""

from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_local_session_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.local_session import (
    LocalSessionAuditRequest,
    LocalSessionAuditResult,
    utc_now,
)
from aion_brain.local_session.redaction import local_session_payload_has_unsafe_content
from aion_brain.telemetry.visual import build_operator_console_telemetry_event

_FRONTEND_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
_FRONTEND_PREFIXES = ("vite.config.", "next.config.", "tailwind.config.", "webpack.config.")


class LocalSessionAuditService:
    """Run local-only session boundary checks without external calls."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repo_root = repo_root or Path(__file__).parents[5]
        self._settings = settings or get_settings()
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def audit(self, request: LocalSessionAuditRequest) -> LocalSessionAuditResult:
        """Audit AION-095 local session safety constraints."""
        findings: list[dict[str, object]] = []
        checks_run = [
            "no_login_endpoint",
            "no_logout_endpoint",
            "no_credential_storage",
            "no_token_issuance",
            "no_cookie_issuance",
            "no_session_persistence",
            "no_production_auth",
            "write_actions_disabled",
            "execution_disabled",
            "activation_disabled",
            "external_calls_disabled",
            "examples_safe",
            "no_aion_095_migration",
            "no_frontend_dependency_files",
            "static_console_has_no_login_form",
        ]
        no_login = self._no_route_with("login", findings)
        no_logout = self._no_route_with("logout", findings)
        examples_safe = self._examples_safe(findings) if request.include_examples else True
        no_migration = self._no_aion_095_migration(findings)
        no_frontend = self._no_frontend_dependency_files(findings)
        static_console_safe = self._static_console_has_no_login_form(findings)
        sessions_are_dev_only = bool(self._settings.local_session_dev_only)
        sessions_are_read_only = bool(self._settings.local_session_read_only)
        credentials_absent = not self._settings.local_session_credentials_enabled
        tokens_absent = not self._settings.local_session_tokens_enabled
        cookies_absent = not self._settings.local_session_cookies_enabled
        persistence_absent = not self._settings.local_session_persistence_enabled
        production_auth_absent = not self._settings.production_auth_enabled
        write_actions_disabled = not self._settings.local_session_write_actions_enabled
        execution_disabled = not self._settings.local_session_execution_enabled
        activation_disabled = not self._settings.local_session_activation_enabled
        external_calls_disabled = not self._settings.local_session_external_calls_enabled
        for ok, finding in (
            (no_login, "login_endpoint_absent"),
            (no_logout, "logout_endpoint_absent"),
            (examples_safe, "examples_safe"),
            (no_migration, "migration_absent"),
            (no_frontend, "frontend_dependencies_absent"),
            (static_console_safe, "static_console_form_absent"),
            (sessions_are_dev_only, "dev_only_enabled"),
            (sessions_are_read_only, "read_only_enabled"),
            (credentials_absent, "auth_material_disabled"),
            (tokens_absent, "bearer_material_disabled"),
            (cookies_absent, "browser_state_disabled"),
            (persistence_absent, "state_storage_disabled"),
            (production_auth_absent, "production_auth_disabled"),
            (write_actions_disabled, "write_actions_disabled"),
            (execution_disabled, "execution_disabled"),
            (activation_disabled, "activation_disabled"),
            (external_calls_disabled, "external_calls_disabled"),
        ):
            if not ok:
                findings.append({"finding": finding, "status": "failed"})
        passed = all(
            (
                no_login,
                no_logout,
                examples_safe,
                no_migration,
                no_frontend,
                static_console_safe,
                sessions_are_dev_only,
                sessions_are_read_only,
                credentials_absent,
                tokens_absent,
                cookies_absent,
                persistence_absent,
                production_auth_absent,
                write_actions_disabled,
                execution_disabled,
                activation_disabled,
                external_calls_disabled,
            )
        )
        result = LocalSessionAuditResult(
            local_session_audit_id=f"local-session-audit-{uuid4().hex}",
            trace_id=request.trace_id,
            status="passed" if passed else "failed",
            owner_scope=request.owner_scope,
            checks_run=checks_run,
            findings=findings,
            sessions_are_dev_only=sessions_are_dev_only,
            sessions_are_read_only=sessions_are_read_only,
            credentials_absent=credentials_absent,
            tokens_absent=tokens_absent,
            cookies_absent=cookies_absent,
            persistence_absent=persistence_absent,
            production_auth_absent=production_auth_absent,
            write_actions_disabled=write_actions_disabled,
            execution_disabled=execution_disabled,
            activation_disabled=activation_disabled,
            external_calls_disabled=external_calls_disabled,
            recommendations=[] if passed else ["review_local_session_findings"],
            metadata={"dev_only": True, "no_privileged_bypass": True},
            created_at=utc_now(),
        )
        _emit(
            self._telemetry_service,
            "local_session_audit_completed",
            "local_session_audit",
            result.local_session_audit_id,
            request.owner_scope,
            {"status": result.status},
        )
        record_local_session_audit_event(
            self._audit_sink,
            audit_id=result.local_session_audit_id,
            trace_id=result.trace_id,
            actor_id=request.created_by,
            owner_scope=result.owner_scope,
            status=result.status,
        )
        return result

    def _no_route_with(self, route_text: str, findings: list[dict[str, object]]) -> bool:
        pattern = re.compile(r"@\w+\.((get)|(post)|(put)|(patch)|(delete))\([^)]*" + route_text)
        ok = True
        api_dir = self._repo_root / "services/brain-api/src/aion_brain/api"
        for path in api_dir.glob("*.py"):
            text = path.read_text()
            if pattern.search(text):
                findings.append({"finding": f"{route_text}_route_found", "path": str(path)})
                ok = False
        return ok

    def _examples_safe(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        for path in sorted((self._repo_root / "examples/auth").glob("*session*.json")):
            try:
                payload = json.loads(path.read_text())
            except json.JSONDecodeError:
                findings.append({"finding": "invalid_json", "path": str(path)})
                ok = False
                continue
            if local_session_payload_has_unsafe_content(payload):
                findings.append({"finding": "unsafe_example", "path": str(path)})
                ok = False
        return ok

    def _no_aion_095_migration(self, findings: list[dict[str, object]]) -> bool:
        migration_dir = self._repo_root / "infra/postgres/migrations"
        added = [path for path in migration_dir.glob("*095*") if path.is_file()]
        for path in added:
            findings.append({"finding": "unexpected_migration", "path": str(path)})
        return not added

    def _no_frontend_dependency_files(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        for path in self._repo_root.iterdir():
            if path.name in _FRONTEND_FILES or any(
                path.name.startswith(prefix) for prefix in _FRONTEND_PREFIXES
            ):
                findings.append({"finding": "frontend_dependency_file_found", "path": path.name})
                ok = False
        return ok

    def _static_console_has_no_login_form(self, findings: list[dict[str, object]]) -> bool:
        html = self._repo_root / "operator-console-static/index.html"
        text = html.read_text().lower() if html.exists() else ""
        unsafe = "<form" in text or 'type="password"' in text
        if unsafe:
            findings.append({"finding": "static_console_login_form_found", "path": str(html)})
        return not unsafe


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


__all__ = ["LocalSessionAuditService"]

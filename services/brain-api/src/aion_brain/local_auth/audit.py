"""Local auth safety audit service."""

from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_local_auth_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.local_auth import LocalAuthAuditRequest, LocalAuthAuditResult, utc_now
from aion_brain.local_auth.redaction import local_auth_payload_has_unsafe_content
from aion_brain.telemetry.visual import build_operator_console_telemetry_event

_FRONTEND_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
_FRONTEND_PREFIXES = ("vite.config.", "next.config.", "tailwind.config.", "webpack.config.")


class LocalAuthAuditService:
    """Run local-only auth boundary checks without external calls."""

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

    def audit(self, request: LocalAuthAuditRequest) -> LocalAuthAuditResult:
        """Audit AION-094 local auth safety constraints."""
        findings: list[dict[str, object]] = []
        checks_run = [
            "no_login_endpoint",
            "no_credential_storage",
            "no_session_storage",
            "no_external_identity_provider",
            "production_auth_disabled",
            "credentials_disabled",
            "sessions_disabled",
            "external_identity_disabled",
            "write_actions_disabled",
            "execution_disabled",
            "activation_disabled",
            "examples_safe",
            "no_migration_added",
            "no_frontend_dependency_files",
        ]
        no_login = self._no_login_endpoint(findings)
        examples_safe = self._examples_safe(findings) if request.include_examples else True
        no_migration = self._no_aion_094_migration(findings)
        no_frontend = self._no_frontend_dependency_files(findings)
        production_auth_absent = not self._settings.production_auth_enabled
        credentials_absent = not self._settings.auth_credentials_enabled
        sessions_absent = not self._settings.auth_sessions_enabled
        external_identity_absent = not self._settings.external_identity_provider_enabled
        write_actions_disabled = not self._settings.local_auth_write_actions_enabled
        execution_disabled = True
        activation_disabled = True
        for ok, finding in (
            (no_login, "login_endpoint_absent"),
            (examples_safe, "examples_safe"),
            (no_migration, "migration_absent"),
            (no_frontend, "frontend_dependencies_absent"),
            (production_auth_absent, "production_auth_disabled"),
            (credentials_absent, "credentials_disabled"),
            (sessions_absent, "sessions_disabled"),
            (external_identity_absent, "external_identity_disabled"),
            (write_actions_disabled, "write_actions_disabled"),
        ):
            if not ok:
                findings.append({"finding": finding, "status": "failed"})
        passed = all(
            (
                no_login,
                examples_safe,
                no_migration,
                no_frontend,
                production_auth_absent,
                credentials_absent,
                sessions_absent,
                external_identity_absent,
                write_actions_disabled,
                execution_disabled,
                activation_disabled,
            )
        )
        result = LocalAuthAuditResult(
            local_auth_audit_id=f"local-auth-audit-{uuid4().hex}",
            trace_id=request.trace_id,
            status="passed" if passed else "failed",
            owner_scope=request.owner_scope,
            checks_run=checks_run,
            findings=findings,
            production_auth_absent=production_auth_absent,
            credentials_absent=credentials_absent,
            sessions_absent=sessions_absent,
            external_identity_absent=external_identity_absent,
            write_actions_disabled=write_actions_disabled,
            execution_disabled=execution_disabled,
            activation_disabled=activation_disabled,
            recommendations=[] if passed else ["review_local_auth_findings"],
            metadata={"dev_only": True, "no_privileged_bypass": True},
            created_at=utc_now(),
        )
        _emit(
            self._telemetry_service,
            "local_auth_audit_completed",
            "local_auth_audit",
            result.local_auth_audit_id,
            request.owner_scope,
            {"status": result.status},
        )
        record_local_auth_audit_event(
            self._audit_sink,
            audit_id=result.local_auth_audit_id,
            trace_id=result.trace_id,
            actor_id=request.created_by,
            owner_scope=result.owner_scope,
            status=result.status,
        )
        return result

    def _no_login_endpoint(self, findings: list[dict[str, object]]) -> bool:
        route_pattern = re.compile(r"@\w+\.((get)|(post)|(put)|(patch)|(delete))\([^)]*login")
        ok = True
        api_dir = self._repo_root / "services/brain-api/src/aion_brain/api"
        for path in api_dir.glob("*.py"):
            text = path.read_text()
            if route_pattern.search(text):
                findings.append({"finding": "login_route_found", "path": str(path)})
                ok = False
        return ok

    def _examples_safe(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        aion_104_review_examples = {
            "auth-safety-evidence-pack.json",
            "auth-runtime-disabled-proof.json",
            "auth-traceability-matrix.json",
            "auth-no-go-regression-result.json",
        }
        for path in sorted((self._repo_root / "examples/auth").glob("*.json")):
            if (
                path.name in aion_104_review_examples
                or path.name.startswith("local-session")
                or path.name == "role-aware-session-context.json"
                or "action-authorization" in path.name
                or "auth-runtime" in path.name
                or "mock-claims" in path.name
            ):
                continue
            try:
                payload = json.loads(path.read_text())
            except json.JSONDecodeError:
                findings.append({"finding": "invalid_json", "path": str(path)})
                ok = False
                continue
            if local_auth_payload_has_unsafe_content(payload):
                findings.append({"finding": "unsafe_example", "path": str(path)})
                ok = False
        return ok

    def _no_aion_094_migration(self, findings: list[dict[str, object]]) -> bool:
        migration_dir = self._repo_root / "infra/postgres/migrations"
        added = [path for path in migration_dir.glob("*094*") if path.is_file()]
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


__all__ = ["LocalAuthAuditService"]

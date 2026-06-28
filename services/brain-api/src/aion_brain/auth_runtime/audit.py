"""Audit service for the disabled production auth runtime prototype."""

from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

from aion_brain.contracts.auth_runtime import (
    AuthRuntimeAuditRequest,
    AuthRuntimeAuditResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry

_PROVIDER_DEPENDENCY_PATTERN = re.compile(
    r"authlib|oauth|oidc|saml|ldap|webauthn|passkey|python-jose|jwt|okta|auth0",
    re.IGNORECASE,
)
_FORBIDDEN_AUTH_RUNTIME_ROUTES = (
    "login",
    "logout",
    "callback",
    "token",
    "session",
    "authorize",
    "oauth",
    "saml",
    "oidc",
)
_FRONTEND_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}


class AuthRuntimeAuditService:
    """Run local-only disabled-auth runtime boundary checks."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repo_root = repo_root or Path(__file__).parents[5]
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def audit(self, request: AuthRuntimeAuditRequest) -> AuthRuntimeAuditResult:
        """Return deterministic audit proof for AION-099."""

        findings: list[dict[str, object]] = []
        checks_run = [
            "production_auth_disabled",
            "external_identity_disabled",
            "credentials_disabled",
            "token_issuance_disabled",
            "cookie_issuance_disabled",
            "session_persistence_disabled",
            "login_logout_absent",
            "auth_runtime_router_has_no_forbidden_routes",
            "provider_sdk_absent",
            "examples_safe",
            "static_console_has_no_login_password_or_auth_material_inputs",
            "no_frontend_dependency_files",
        ]
        production_auth_disabled = not bool(
            getattr(self._settings, "production_auth_enabled", False)
        )
        external_identity_disabled = not bool(
            getattr(self._settings, "auth_runtime_external_identity_enabled", False)
            or getattr(self._settings, "external_identity_provider_enabled", False)
        )
        credentials_disabled = not bool(
            getattr(self._settings, "auth_runtime_credentials_enabled", False)
            or getattr(self._settings, "auth_credentials_enabled", False)
        )
        token_issuance_disabled = not bool(
            getattr(self._settings, "auth_runtime_token_issuance_enabled", False)
        )
        cookie_issuance_disabled = not bool(
            getattr(self._settings, "auth_runtime_cookie_issuance_enabled", False)
        )
        session_persistence_disabled = not bool(
            getattr(self._settings, "auth_runtime_session_persistence_enabled", False)
            or getattr(self._settings, "auth_sessions_enabled", False)
        )
        login_logout_absent = self._no_login_logout_routes(findings)
        auth_runtime_routes_safe = self._auth_runtime_router_has_no_forbidden_routes(findings)
        provider_sdk_absent = self._provider_sdk_absent(findings)
        examples_safe = self._examples_safe(findings) if request.include_examples else True
        static_console_safe = self._static_console_safe(findings)
        no_frontend = self._no_frontend_dependency_files(findings)
        for ok, code in (
            (production_auth_disabled, "production_auth_disabled"),
            (external_identity_disabled, "external_identity_disabled"),
            (credentials_disabled, "credentials_disabled"),
            (token_issuance_disabled, "token_issuance_disabled"),
            (cookie_issuance_disabled, "cookie_issuance_disabled"),
            (session_persistence_disabled, "session_persistence_disabled"),
            (login_logout_absent, "login_logout_absent"),
            (auth_runtime_routes_safe, "auth_runtime_routes_safe"),
            (provider_sdk_absent, "provider_sdk_absent"),
            (examples_safe, "examples_safe"),
            (static_console_safe, "static_console_safe"),
            (no_frontend, "frontend_dependencies_absent"),
        ):
            if not ok:
                findings.append({"code": code, "status": "failed"})
        passed = all(
            (
                production_auth_disabled,
                external_identity_disabled,
                credentials_disabled,
                token_issuance_disabled,
                cookie_issuance_disabled,
                session_persistence_disabled,
                login_logout_absent,
                auth_runtime_routes_safe,
                provider_sdk_absent,
                examples_safe,
                static_console_safe,
                no_frontend,
            )
        )
        result = AuthRuntimeAuditResult(
            auth_runtime_audit_id=f"auth-runtime-audit-{uuid4().hex}",
            trace_id=request.trace_id,
            status="passed" if passed else "failed",
            owner_scope=request.owner_scope,
            checks_run=checks_run,
            findings=findings,
            production_auth_disabled=production_auth_disabled,
            external_identity_disabled=external_identity_disabled,
            credentials_disabled=credentials_disabled,
            token_issuance_disabled=token_issuance_disabled,
            cookie_issuance_disabled=cookie_issuance_disabled,
            session_persistence_disabled=session_persistence_disabled,
            login_logout_absent=login_logout_absent,
            mock_only=True,
            recommendations=[] if passed else ["review_auth_runtime_findings"],
            metadata={
                "mock_only": True,
                "include_examples": request.include_examples,
                "auth_runtime_enabled": False,
            },
            created_at=utc_now(),
        )
        self._record_audit(result.auth_runtime_audit_id)
        emit_telemetry(
            self._telemetry_service,
            event_type="auth_runtime_audit_completed",
            node_type="auth_runtime_audit",
            node_id=result.auth_runtime_audit_id,
            intensity=0.9 if result.status != "passed" else 0.65,
            trace_id=result.trace_id,
            payload={"status": result.status, "mock_only": True},
        )
        return result

    def _no_login_logout_routes(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        pattern = re.compile(r"@\w+\.(get|post|put|patch|delete)\([^)]*(login|logout)")
        api_dir = self._repo_root / "services/brain-api/src/aion_brain/api"
        for path in api_dir.glob("*.py"):
            text = path.read_text()
            if pattern.search(text):
                findings.append({"code": "login_logout_route_found", "path": str(path)})
                ok = False
        return ok

    def _auth_runtime_router_has_no_forbidden_routes(
        self,
        findings: list[dict[str, object]],
    ) -> bool:
        path = self._repo_root / "services/brain-api/src/aion_brain/api/auth_runtime.py"
        if not path.exists():
            findings.append({"code": "auth_runtime_router_missing", "path": str(path)})
            return False
        text = path.read_text().lower()
        ok = True
        for route_text in _FORBIDDEN_AUTH_RUNTIME_ROUTES:
            if re.search(rf"@\w+\.(get|post|put|patch|delete)\([^)]*{route_text}", text):
                findings.append(
                    {
                        "code": "forbidden_auth_runtime_route",
                        "route": route_text,
                        "path": str(path),
                    }
                )
                ok = False
        return ok

    def _provider_sdk_absent(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        paths = [
            self._repo_root / "pyproject.toml",
            self._repo_root / "requirements.txt",
            self._repo_root / "services/brain-api/pyproject.toml",
            self._repo_root / "packages/aion-sdk-python/pyproject.toml",
        ]
        for path in paths:
            if path.exists() and _PROVIDER_DEPENDENCY_PATTERN.search(path.read_text()):
                findings.append({"code": "provider_sdk_dependency_found", "path": str(path)})
                ok = False
        return ok

    def _examples_safe(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        paths = [
            *sorted((self._repo_root / "examples/auth").glob("*auth-runtime*.json")),
            *sorted((self._repo_root / "examples/auth").glob("*mock-claims*.json")),
            *sorted(
                (self._repo_root / "operator-console-static/demo-data").glob(
                    "*auth-runtime*.json"
                )
            ),
            *sorted(
                (self._repo_root / "operator-console-static/demo-data").glob(
                    "*mock-claims*.json"
                )
            ),
        ]
        for path in paths:
            try:
                payload = json.loads(path.read_text())
            except json.JSONDecodeError:
                findings.append({"code": "invalid_json", "path": str(path)})
                ok = False
                continue
            if _example_has_unsafe_auth_material(payload):
                findings.append({"code": "unsafe_example", "path": str(path)})
                ok = False
        return ok

    def _static_console_safe(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        html = self._repo_root / "operator-console-static/index.html"
        text = html.read_text().lower() if html.exists() else ""
        if "<form" in text or "<input" in text or 'type="password"' in text:
            findings.append({"code": "static_console_auth_input_found", "path": str(html)})
            ok = False
        return ok

    def _no_frontend_dependency_files(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        for path in self._repo_root.iterdir():
            if path.name in _FRONTEND_FILES:
                findings.append({"code": "frontend_dependency_file_found", "path": path.name})
                ok = False
        return ok

    def _record_audit(self, audit_id: str) -> None:
        for name in ("record_event", "record_audit_event"):
            record = getattr(self._audit_sink, name, None)
            if callable(record):
                try:
                    record({"event_type": "auth_runtime_audit_completed", "audit_id": audit_id})
                except Exception:
                    return


def _example_has_unsafe_auth_material(value: object) -> bool:
    allowed_keys = {
        "credentials_enabled",
        "credentials_present",
        "token_issuance_enabled",
        "token_present",
        "cookie_issuance_enabled",
        "cookie_present",
        "session_persistence_enabled",
        "session_persisted",
        "login_endpoint_enabled",
        "logout_endpoint_enabled",
        "external_identity_provider_enabled",
    }
    blocked_key_parts = {
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "credential",
        "password",
        "private_key",
        "secret",
        "token",
    }
    blocked_value_markers = {
        "sk-",
        "xoxb-",
        "ghp_",
        "-----begin private key-----",
        "bearer ",
        "basic ",
        "raw prompt",
        "raw_prompt",
        "hidden reasoning",
        "hidden_reasoning",
        "chain-of-thought",
        "chain_of_thought",
    }
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized not in allowed_keys and any(
                part in normalized for part in blocked_key_parts
            ):
                return True
            if _example_has_unsafe_auth_material(nested):
                return True
    elif isinstance(value, list):
        return any(_example_has_unsafe_auth_material(item) for item in value)
    elif isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in blocked_value_markers)
    return False


__all__ = ["AuthRuntimeAuditService"]

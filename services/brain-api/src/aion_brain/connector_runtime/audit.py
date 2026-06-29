"""Audit service for the disabled external connector runtime prototype."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_connector_runtime_audit
from aion_brain.contracts.connector_runtime import (
    ConnectorRuntimeAuditRequest,
    ConnectorRuntimeAuditResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry

_NETWORK_DEPENDENCY_PATTERN = re.compile(
    r"connector[-_ ]?sdk|provider[-_ ]?sdk|requests\s*==|httpx\s*==|aiohttp\s*==",
    re.IGNORECASE,
)
_CONNECTOR_CALL_PATTERN = re.compile(
    r"requests\.(get|post|put|patch|delete)|httpx\.(get|post|put|patch|delete)|aiohttp\.ClientSession|urllib\.request",
    re.IGNORECASE,
)


class ConnectorRuntimeAuditService:
    """Run local-only disabled connector runtime boundary checks."""

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

    def audit(self, request: ConnectorRuntimeAuditRequest) -> ConnectorRuntimeAuditResult:
        """Return deterministic audit proof for AION-108."""

        findings: list[dict[str, object]] = []
        checks_run = [
            "connector_runtime_disabled",
            "connector_external_calls_disabled",
            "connector_credentials_disabled",
            "connector_token_storage_disabled",
            "connector_activation_disabled",
            "connector_route_registration_disabled",
            "network_clients_absent",
            "provider_sdks_absent",
            "examples_safe",
            "static_console_has_no_connector_inputs_or_call_buttons",
        ]
        runtime_disabled = not bool(getattr(self._settings, "connector_runtime_enabled", False))
        external_calls_disabled = not bool(
            getattr(self._settings, "connector_external_calls_enabled", False)
        )
        credentials_disabled = not bool(
            getattr(self._settings, "connector_credentials_enabled", False)
        )
        token_storage_disabled = not bool(
            getattr(self._settings, "connector_token_storage_enabled", False)
        )
        activation_disabled = not bool(
            getattr(self._settings, "connector_activation_enabled", False)
        )
        route_registration_disabled = not bool(
            getattr(self._settings, "connector_route_registration_enabled", False)
        )
        network_clients_absent = self._network_clients_absent(findings)
        provider_sdks_absent = self._provider_sdks_absent(findings)
        examples_safe = self._examples_safe(findings) if request.include_examples else True
        static_console_safe = self._static_console_safe(findings)
        for ok, code in (
            (runtime_disabled, "connector_runtime_disabled"),
            (external_calls_disabled, "connector_external_calls_disabled"),
            (credentials_disabled, "connector_credentials_disabled"),
            (token_storage_disabled, "connector_token_storage_disabled"),
            (activation_disabled, "connector_activation_disabled"),
            (route_registration_disabled, "connector_route_registration_disabled"),
            (network_clients_absent, "network_clients_absent"),
            (provider_sdks_absent, "provider_sdks_absent"),
            (examples_safe, "examples_safe"),
            (static_console_safe, "static_console_safe"),
        ):
            if not ok:
                findings.append({"code": code, "status": "failed"})
        passed = all(
            (
                runtime_disabled,
                external_calls_disabled,
                credentials_disabled,
                token_storage_disabled,
                activation_disabled,
                route_registration_disabled,
                network_clients_absent,
                provider_sdks_absent,
                examples_safe,
                static_console_safe,
            )
        )
        result = ConnectorRuntimeAuditResult(
            connector_runtime_audit_id=f"connector-runtime-audit-{uuid4().hex}",
            trace_id=request.trace_id,
            status="passed" if passed else "failed",
            owner_scope=request.owner_scope,
            checks_run=checks_run,
            findings=findings,
            runtime_disabled=runtime_disabled,
            external_calls_disabled=external_calls_disabled,
            credentials_disabled=credentials_disabled,
            token_storage_disabled=token_storage_disabled,
            activation_disabled=activation_disabled,
            route_registration_disabled=route_registration_disabled,
            network_clients_absent=network_clients_absent,
            provider_sdks_absent=provider_sdks_absent,
            recommendations=[] if passed else ["review_connector_runtime_findings"],
            metadata={
                "mock_only": True,
                "include_examples": request.include_examples,
                "connector_runtime_enabled": False,
            },
            created_at=utc_now(),
        )
        record_connector_runtime_audit(
            self._audit_sink,
            audit_id=result.connector_runtime_audit_id,
            trace_id=result.trace_id,
            actor_id=request.created_by,
            owner_scope=result.owner_scope,
            status=result.status,
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_runtime_audit_completed",
            node_type="connector_runtime_audit",
            node_id=result.connector_runtime_audit_id,
            intensity=0.9 if result.status != "passed" else 0.65,
            trace_id=result.trace_id,
            payload={"status": result.status, "mock_only": True},
        )
        return result

    def _network_clients_absent(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        for path in self._runtime_files():
            text = path.read_text(errors="ignore")
            if _CONNECTOR_CALL_PATTERN.search(text):
                findings.append({"code": "connector_network_call_pattern_found", "path": str(path)})
                ok = False
        return ok

    def _provider_sdks_absent(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        paths = [
            self._repo_root / "pyproject.toml",
            self._repo_root / "requirements.txt",
            self._repo_root / "services/brain-api/pyproject.toml",
            self._repo_root / "packages/aion-sdk-python/pyproject.toml",
        ]
        for path in paths:
            if path.exists() and _NETWORK_DEPENDENCY_PATTERN.search(path.read_text()):
                findings.append(
                    {"code": "connector_or_provider_sdk_dependency_found", "path": str(path)}
                )
                ok = False
        return ok

    def _examples_safe(self, findings: list[dict[str, object]]) -> bool:
        ok = True
        for path in sorted((self._repo_root / "examples/connectors").glob("*connector*.json")):
            text = path.read_text().lower()
            for marker in (
                "sk-",
                "ghp_",
                "xoxb-",
                "-----begin private key-----",
                "bearer ",
                "http://",
                "https://",
                "raw_prompt",
                "hidden_reasoning",
                "chain_of_thought",
            ):
                if marker in text:
                    findings.append({"code": "unsafe_connector_example_marker", "path": str(path)})
                    ok = False
        return ok

    def _static_console_safe(self, findings: list[dict[str, object]]) -> bool:
        static_dir = self._repo_root / "operator-console-static"
        text = "\n".join(
            path.read_text(errors="ignore").lower()
            for path in (static_dir / "demo-data").glob("connector*.json")
        )
        html = (static_dir / "index.html").read_text(errors="ignore").lower()
        app = (static_dir / "app.js").read_text(errors="ignore").lower()
        combined = "\n".join([text, html, app])
        forbidden = [
            "connector credential input",
            "connect connector",
            "call connector",
            "connector token input",
            "type=\"password\"",
            "name=\"credential\"",
            "name=\"token\"",
        ]
        hits = [item for item in forbidden if item in combined]
        if hits:
            findings.append({"code": "unsafe_static_connector_surface", "hits": hits})
        return not hits

    def _runtime_files(self) -> list[Path]:
        base = self._repo_root / "services/brain-api/src/aion_brain/connector_runtime"
        api_file = self._repo_root / "services/brain-api/src/aion_brain/api/connector_runtime.py"
        return (
            [*sorted(base.glob("*.py")), api_file]
            if api_file.exists()
            else sorted(base.glob("*.py"))
        )


__all__ = ["ConnectorRuntimeAuditService"]

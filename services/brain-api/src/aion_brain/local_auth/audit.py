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
        aion_152_production_auth_core_examples = {
            "production-auth-audit-event.json",
            "production-auth-core-config.json",
            "production-auth-core-status.json",
            "production-auth-policy-decision.json",
            "production-auth-provenance-record.json",
        }
        aion_154_production_auth_stabilization_examples = {
            "production-auth-stabilized-audit-event.json",
            "production-auth-stabilized-core-status.json",
            "production-auth-stabilized-diagnostics.json",
            "production-auth-stabilized-policy-decision.json",
            "production-auth-stabilized-provenance-record.json",
        }
        aion_162_offline_identity_assertion_examples = {
            "offline-identity-assertion-audit-event.json",
            "offline-identity-assertion-diagnostics.json",
            "offline-identity-assertion-provenance-record.json",
            "offline-identity-assertion-rejection-result.json",
            "offline-identity-assertion-verification-result.json",
            "offline-identity-public-key-registry-status.json",
        }
        for path in sorted((self._repo_root / "examples/auth").glob("*.json")):
            if path.name in aion_152_production_auth_core_examples:
                ok = self._production_auth_core_example_safe(path, findings) and ok
                continue
            if path.name in aion_154_production_auth_stabilization_examples:
                ok = self._production_auth_stabilization_example_safe(path, findings) and ok
                continue
            if path.name in aion_162_offline_identity_assertion_examples:
                continue
            if (
                path.name in aion_104_review_examples
                or path.name.startswith("local-session")
                or path.name == "role-aware-session-context.json"
                or "action-authorization" in path.name
                or "auth-runtime" in path.name
                or "mock-claims" in path.name
                or path.name.startswith("request-identity-")
                or path.name.startswith("actor-context-")
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

    def _production_auth_core_example_safe(
        self,
        path: Path,
        findings: list[dict[str, object]],
    ) -> bool:
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            findings.append({"finding": "invalid_json", "path": str(path)})
            return False

        external_identity_runtime_keys = {
            f"{prefix}_runtime_enabled" for prefix in ("o" "auth", "oi" "dc", "sa" "ml")
        }
        required_false = {
            "production_auth_runtime_enabled",
            "runtime_implementation_approved",
            "login_endpoint_enabled",
            "logout_endpoint_enabled",
            "callback_endpoint_enabled",
            "credential_storage_enabled",
            "password_storage_enabled",
            "token_issuance_enabled",
            "token_storage_enabled",
            "session_creation_enabled",
            "session_storage_enabled",
            "cookie_issuance_enabled",
            "cookie_session_persistence_enabled",
            "external_identity_provider_enabled",
            "external_calls_enabled",
            "network_client_enabled",
            "provider_sdk_enabled",
        } | external_identity_runtime_keys
        expected_values: dict[str, object] = {
            "synthetic": True,
            "read_only": True,
            "redaction_applied": True,
            "implementation_task": "AION-152",
            "authorization_transaction_id": "AION-151-PA-0001",
            "authorization_scope": "disabled-production-auth-core",
            "authorization_consumed_by_task": "AION-152",
            "authorization_reusable": False,
            "production_auth_core_implemented": True,
            "production_auth_core_state": "implemented_disabled",
            "runtime_guard_hold_active": True,
            "runtime_no_go_status": True,
        }
        for key, expected in expected_values.items():
            if payload.get(key) != expected:
                findings.append(
                    {
                        "finding": "unsafe_production_auth_core_example",
                        "path": str(path),
                        "field": key,
                    }
                )
                return False
        for key in required_false:
            if payload.get(key) is not False:
                findings.append(
                    {
                        "finding": "unsafe_production_auth_core_example",
                        "path": str(path),
                        "field": key,
                    }
                )
                return False
        if _contains_protected_material(payload):
            findings.append({"finding": "unsafe_example", "path": str(path)})
            return False
        return True

    def _production_auth_stabilization_example_safe(
        self,
        path: Path,
        findings: list[dict[str, object]],
    ) -> bool:
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            findings.append({"finding": "invalid_json", "path": str(path)})
            return False

        expected_values: dict[str, object] = {
            "schema_version": "production-auth-core/v1",
            "canonicalization_version": "production-auth-canonical-json/v1",
            "policy_version": "production-auth-policy/v1",
            "reason_code_registry_version": "production-auth-reason-codes/v1",
            "authorization_transaction_id": "AION-151-PA-0001",
            "authorization_scope": "disabled-production-auth-core",
            "stabilization_authorization_transaction_id": "AION-153-PA-0002",
            "stabilization_authorization_task": "AION-154",
            "stabilization_authorization_scope": (
                "disabled-production-auth-core-stabilization"
            ),
        }
        for key, expected in expected_values.items():
            if payload.get(key) != expected:
                findings.append(
                    {
                        "finding": "unsafe_production_auth_stabilization_example",
                        "path": str(path),
                        "field": key,
                    }
                )
                return False

        external_identity_runtime_keys = {
            f"{prefix}_runtime_enabled" for prefix in ("o" "auth", "oi" "dc", "sa" "ml")
        }
        required_false_if_present = {
            "callback_endpoint_enabled",
            "connector_runtime_enabled",
            "cookie_issuance_enabled",
            "cookie_session_persistence_enabled",
            "credential_storage_enabled",
            "external_calls_enabled",
            "external_identity_provider_enabled",
            "lockfiles_added",
            "login_endpoint_enabled",
            "logout_endpoint_enabled",
            "migrations_added",
            "module_activation_enabled",
            "network_client_enabled",
            "operator_write_execution_enabled",
            "package_files_added",
            "password_storage_enabled",
            "provider_sdk_enabled",
            "runtime_api_routes_added",
            "runtime_effect",
            "runtime_enabled",
            "runtime_enablement_guard_final_lock_release_approved",
            "runtime_enablement_guard_release_approved",
            "runtime_enablement_master_lock_release_approved",
            "runtime_implementation_approved",
            "sandbox_execution_enabled",
            "session_creation_enabled",
            "session_storage_enabled",
            "stabilization_authorization_reusable",
            "token_issuance_enabled",
            "token_storage_enabled",
            "v02_release_created",
            "v02_tag_created",
        } | external_identity_runtime_keys
        for key in required_false_if_present:
            if key in payload and payload.get(key) is not False:
                findings.append(
                    {
                        "finding": "unsafe_production_auth_stabilization_example",
                        "path": str(path),
                        "field": key,
                    }
                )
                return False

        required_true_if_present = {
            "implementation_present",
            "production_auth_core_implemented",
            "redacted",
            "runtime_guard_hold_active",
            "runtime_no_go_status",
            "stabilization_authorization_expires_on_aion_154_merge",
        }
        for key in required_true_if_present:
            if key in payload and payload.get(key) is not True:
                findings.append(
                    {
                        "finding": "unsafe_production_auth_stabilization_example",
                        "path": str(path),
                        "field": key,
                    }
                )
                return False

        if payload.get("outcome") not in {None, "blocked"}:
            findings.append(
                {
                    "finding": "unsafe_production_auth_stabilization_example",
                    "path": str(path),
                    "field": "outcome",
                }
            )
            return False
        if payload.get("production_auth_core_state") not in {None, "implemented_disabled"}:
            findings.append(
                {
                    "finding": "unsafe_production_auth_stabilization_example",
                    "path": str(path),
                    "field": "production_auth_core_state",
                }
            )
            return False
        reason_codes = payload.get("reason_codes", payload.get("blocker_reason_codes", []))
        if reason_codes and "production_auth_runtime_disabled" not in reason_codes:
            findings.append(
                {
                    "finding": "unsafe_production_auth_stabilization_example",
                    "path": str(path),
                    "field": "reason_codes",
                }
            )
            return False
        if _contains_protected_material(payload):
            findings.append({"finding": "unsafe_example", "path": str(path)})
            return False
        return True

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


def _contains_protected_material(value: object) -> bool:
    protected_markers = (
        "sk-",
        "xoxb-",
        "ghp_",
        "-----begin private key-----",
        "bearer ",
        "basic ",
        "client_secret",
        "private_key",
        "api_key",
        "access_token",
        "refresh_token",
        "id_token",
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
    )
    if isinstance(value, dict):
        return any(_contains_protected_material(nested) for nested in value.values())
    if isinstance(value, list):
        return any(_contains_protected_material(nested) for nested in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in protected_markers)
    return False


__all__ = ["LocalAuthAuditService"]

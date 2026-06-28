"""Local Operator Console contract audit."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from aion_brain.contracts.operator_console import (
    ConsoleAuditRequest,
    ConsoleAuditResult,
    utc_now,
)
from aion_brain.operator_console.action_boundaries import forbidden_action_descriptors
from aion_brain.operator_console.data_sources import list_console_views
from aion_brain.operator_console.redaction import payload_has_sensitive_content

_FRONTEND_FILES = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
}
_FRONTEND_PREFIXES = ("vite.config.", "next.config.", "tailwind.config.")
_UI_RELEASE_GATE_EXAMPLES = {
    "static-console-artifact-manifest.json",
    "ui-release-gate-result.json",
    "ui-safety-matrix.json",
    "operator-platform-checkpoint.json",
    "operator-platform-evidence-pack.json",
    "operator-platform-risk-register.json",
}


class ConsoleContractAuditService:
    """Run local read-only console contract checks."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repo_root = repo_root or Path(__file__).parents[5]
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def audit(self, request: ConsoleAuditRequest) -> ConsoleAuditResult:
        """Audit local console contracts without external calls."""
        _authorize(
            self._policy_adapter,
            "operator_console.audit.run",
            request.owner_scope,
            actor_id=request.created_by,
            trace_id=request.trace_id,
        )
        views = request.views or list_console_views()
        findings: list[dict[str, object]] = []
        docs_present = self._required_docs_present(findings)
        examples_passed = self._examples_safe(findings) if request.include_examples else True
        frontend_absent = self._frontend_absent(findings)
        if not frontend_absent:
            raise ValueError("frontend files are forbidden in AION-088 operator console contracts")
        forbidden_passed = all(item.reason for item in forbidden_action_descriptors())
        data_source_passed = "module_lifecycle" in list_console_views()
        redaction_passed = docs_present and examples_passed
        status = (
            "passed"
            if all((redaction_passed, forbidden_passed, data_source_passed, frontend_absent))
            else "failed"
        )
        result = ConsoleAuditResult(
            console_audit_id=f"console-audit-{uuid4().hex}",
            trace_id=request.trace_id,
            status=status,
            owner_scope=request.owner_scope,
            views_checked=views,
            findings=findings,
            redaction_passed=redaction_passed,
            forbidden_action_passed=forbidden_passed,
            data_source_passed=data_source_passed,
            frontend_absent=frontend_absent,
            recommendations=[] if status == "passed" else ["review_console_contract_findings"],
            metadata={"read_only": True, "write_actions_enabled": False},
            created_at=utc_now(),
        )
        _emit(
            self._telemetry_service,
            "operator_console_contract_audit_completed",
            "operator_console_audit",
            result.console_audit_id,
            request.owner_scope,
            {"status": result.status},
        )
        return result

    def _required_docs_present(self, findings: list[dict[str, object]]) -> bool:
        required = [
            "docs/operator-console/view-model-contract.md",
            "docs/operator-console/data-source-map.md",
            "docs/operator-console/api-contract-audit.md",
            "docs/operator-console/read-only-action-model.md",
            "docs/operator-console/view-redaction-rules.md",
            "docs/operator-console/console-api-examples.md",
            "docs/adr/0079-operator-console-read-only-view-models.md",
        ]
        missing = [path for path in required if not (self._repo_root / path).is_file()]
        for path in missing:
            findings.append({"finding": "missing_doc", "path": path})
        return not missing

    def _examples_safe(self, findings: list[dict[str, object]]) -> bool:
        example_dir = self._repo_root / "examples/operator-console"
        ok = True
        for path in sorted(example_dir.glob("*.json")):
            if path.name in _UI_RELEASE_GATE_EXAMPLES:
                continue
            try:
                payload = json.loads(path.read_text())
            except json.JSONDecodeError:
                findings.append({"finding": "invalid_json", "path": str(path)})
                ok = False
                continue
            if payload_has_sensitive_content(payload):
                findings.append({"finding": "unsafe_example", "path": str(path)})
                ok = False
        return ok

    def _frontend_absent(self, findings: list[dict[str, object]]) -> bool:
        found: list[str] = []
        scan_roots = [
            self._repo_root,
            self._repo_root / "services",
            self._repo_root / "packages",
            self._repo_root / "docs",
        ]
        for root in scan_roots:
            if not root.exists():
                continue
            paths = root.iterdir() if root == self._repo_root else root.rglob("*")
            for path in paths:
                if not path.is_file():
                    continue
                name = path.name
                if name in _FRONTEND_FILES or any(
                    name.startswith(prefix) for prefix in _FRONTEND_PREFIXES
                ):
                    found.append(str(path.relative_to(self._repo_root)))
        for found_path in found:
            findings.append({"finding": "frontend_file_present", "path": found_path})
        return not found


def _authorize(
    policy_adapter: object | None,
    action_type: str,
    scope: list[str],
    *,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> None:
    from uuid import uuid4

    from aion_brain.contracts.policy import PolicyRequest

    authorize = getattr(policy_adapter, "authorize", None)
    if not callable(authorize):
        return
    decision = authorize(
        PolicyRequest(
            request_id=f"operator-console-{uuid4().hex}",
            trace_id=trace_id,
            actor_id=actor_id,
            workspace_id=None,
            action_type=action_type,
            resource_type="operator_console",
            resource_id=None,
            risk_level="low",
            approval_present=False,
            requested_permissions=[action_type],
            security_scope=scope,
            context={"read_only": True},
        )
    )
    if not decision.allow:
        raise PermissionError(decision.reason)


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    scope: list[str],
    payload: dict[str, object],
) -> None:
    from aion_brain.versioning.compatibility import emit_versioning_telemetry

    emit_versioning_telemetry(
        telemetry_service,
        event_type=event_type,
        node_type=node_type,
        node_id=node_id,
        intensity=0.5,
        scope=scope,
        payload=payload,
    )


__all__ = ["ConsoleContractAuditService"]

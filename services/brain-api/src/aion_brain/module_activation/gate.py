"""Deterministic activation gate for metadata-only module activation requests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.audit_integrity.ledger import AuditSink
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.audit_integrity import AuditRecordRequest
from aion_brain.contracts.module_activation import (
    ActivationBlocker,
    ActivationGateRun,
    ActivationGateStatus,
)
from aion_brain.module_activation.blockers import ActivationBlockerService
from aion_brain.module_activation.policy import authorize_module_activation_action
from aion_brain.module_activation.redaction import redact_activation_payload
from aion_brain.module_activation.repository import ModuleActivationRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry

_CHECKS = [
    "module_slot_exists",
    "capability_bindings_exist",
    "readiness_assessment_present",
    "conformance_runs_present",
    "policy_actions_present",
    "runtime_settings_safe",
    "sandbox_profiles_present",
    "module_mock_runtime_evidence_present",
    "activation_disabled",
    "runtime_registration_disabled",
]


class ActivationGateService:
    """Run the AION-083 activation gate without activating or registering anything."""

    def __init__(
        self,
        repository: ModuleActivationRepository,
        policy_adapter: object,
        *,
        module_binding_repository: object | None = None,
        conformance_repository: object | None = None,
        module_mock_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: AuditSink | None = None,
        settings: Settings | None = None,
        blocker_service: ActivationBlockerService | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._module_binding_repository = module_binding_repository
        self._conformance_repository = conformance_repository
        self._module_mock_repository = module_mock_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()
        self._blocker_service = blocker_service or ActivationBlockerService(
            repository,
            policy_adapter,
            telemetry_service=telemetry_service,
        )

    def set_module_mock_repository(self, repository: object | None) -> None:
        """Attach module mock runtime evidence after kernel assembly."""

        self._module_mock_repository = repository

    def run_gate(
        self,
        activation_request_id: str,
        scope: list[str],
        *,
        mode: str = "dry_run",
        created_by: str | None = None,
    ) -> ActivationGateRun:
        """Run deterministic readiness checks and persist a blocked/dry-run result."""
        if not self._settings.module_activation_gate_enabled:
            raise RuntimeError("module_activation_gate_disabled")
        request = self._repository.get_request(activation_request_id)
        if request is None or not _in_scope(request.owner_scope, scope):
            raise AIONNotFoundException("module_activation_request_not_found")
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.gate.run",
            scope,
            actor_id=created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="module_activation_request",
            resource_id=activation_request_id,
            risk_level=request.risk_level,
            context={"mode": mode, "activation_allowed": False},
        )
        self._emit(
            "module_activation_gate_started",
            "module_activation_gate",
            activation_request_id,
            scope,
            {"mode": mode},
        )
        blockers = self._build_blockers(activation_request_id, scope)
        open_blockers = [blocker for blocker in blockers if blocker.status == "open"]
        status: ActivationGateStatus = "blocked" if open_blockers else "dry_run"
        score = 0.0 if any(blocker.severity == "critical" for blocker in open_blockers) else 0.5
        now = datetime.now(UTC)
        run = ActivationGateRun(
            activation_gate_run_id=f"activation-gate-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=created_by or request.actor_id,
            workspace_id=request.workspace_id,
            activation_request_id=request.activation_request_id,
            status=status,
            mode=mode,
            owner_scope=request.owner_scope,
            checks_run=list(_CHECKS),
            blockers=open_blockers,
            warnings=_warnings_for(open_blockers),
            score=score,
            activation_allowed=False,
            result={
                "metadata_only": True,
                "activation_allowed": False,
                "execution_allowed": False,
                "runtime_registration_allowed": False,
                "module_mock_run_count": _module_mock_run_count(
                    self._module_mock_repository,
                    request.capability_binding_ids,
                ),
                "open_blocker_count": len(open_blockers),
            },
            metadata={"activation_gate_version": "0.1", "no_runtime_mutation": True},
            created_by=created_by,
            created_at=now,
            completed_at=now,
        )
        saved = self._repository.save_gate_run(run)
        self._repository.save_request(
            request.model_copy(
                update={
                    "status": "blocked" if open_blockers else request.status,
                    "blocker_refs": [blocker.activation_blocker_id for blocker in open_blockers],
                    "activation_allowed": False,
                    "execution_allowed": False,
                }
            )
        )
        self._record_audit(saved)
        self._emit(
            "module_activation_gate_completed",
            "module_activation_gate",
            saved.activation_gate_run_id,
            scope,
            {
                "status": saved.status,
                "score": saved.score,
                "activation_allowed": False,
            },
        )
        return saved

    def list_gate_runs(
        self,
        scope: list[str],
        *,
        activation_request_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ActivationGateRun]:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.gate.read",
            scope,
            resource_type="module_activation_gate",
        )
        return [
            item
            for item in self._repository.list_gate_runs(
                activation_request_id=activation_request_id,
                status=status,
                limit=limit,
            )
            if _in_scope(item.owner_scope, scope)
        ]

    def _build_blockers(
        self,
        activation_request_id: str,
        scope: list[str],
    ) -> list[ActivationBlocker]:
        request = self._repository.get_request(activation_request_id)
        if request is None:
            raise AIONNotFoundException("module_activation_request_not_found")
        blockers: list[ActivationBlocker] = []

        if not _module_slot_exists(self._module_binding_repository, request.module_slot_id):
            blockers.append(
                self._create_blocker(
                    scope,
                    activation_request_id,
                    "missing_contract",
                    "Module slot metadata was not found.",
                    "Create or validate module slot metadata before activation review.",
                    severity="high",
                    source_type="module_slot",
                    source_id=request.module_slot_id,
                )
            )

        for binding_id in request.capability_binding_ids:
            if not _binding_exists(self._module_binding_repository, binding_id):
                blockers.append(
                    self._create_blocker(
                        scope,
                        activation_request_id,
                        "binding_validation_failed",
                        "Capability binding metadata was not found.",
                        "Create or validate capability binding metadata before activation review.",
                        severity="high",
                        capability_binding_id=binding_id,
                        source_type="capability_binding",
                        source_id=binding_id,
                    )
                )

        if not request.readiness_assessment_ids:
            blockers.append(
                self._create_blocker(
                    scope,
                    activation_request_id,
                    "missing_readiness_assessment",
                    "No readiness assessment is attached to this request.",
                    "Run readiness assessment before future activation review.",
                    severity="high",
                )
            )
        elif not _readiness_ready(self._conformance_repository, request.readiness_assessment_ids):
            blockers.append(
                self._create_blocker(
                    scope,
                    activation_request_id,
                    "readiness_not_ready",
                    "Attached readiness assessment is missing or not ready.",
                    "Resolve readiness blockers before future activation review.",
                    severity="high",
                )
            )

        if not request.conformance_run_ids:
            blockers.append(
                self._create_blocker(
                    scope,
                    activation_request_id,
                    "conformance_failed",
                    "No conformance run is attached to this request.",
                    "Run deterministic conformance checks before future activation review.",
                    severity="medium",
                )
            )

        for action in request.required_policy_actions:
            if not action.strip():
                blockers.append(
                    self._create_blocker(
                        scope,
                        activation_request_id,
                        "missing_policy_action",
                        "A required policy action is empty.",
                        "Declare generic policy actions before future activation review.",
                        severity="high",
                    )
                )

        for setting in request.required_settings:
            if not setting.strip():
                blockers.append(
                    self._create_blocker(
                        scope,
                        activation_request_id,
                        "missing_setting",
                        "A required setting is empty.",
                        "Declare runtime settings before future activation review.",
                        severity="medium",
                    )
                )

        for profile in request.required_sandbox_profiles:
            if not profile.strip():
                blockers.append(
                    self._create_blocker(
                        scope,
                        activation_request_id,
                        "missing_sandbox_profile",
                        "A required sandbox profile is empty.",
                        "Declare sandbox profile metadata before future activation review.",
                        severity="high",
                    )
                )

        for binding_id in request.capability_binding_ids:
            if not _module_mock_evidence_ready(self._module_mock_repository, binding_id):
                blockers.append(
                    self._create_blocker(
                        scope,
                        activation_request_id,
                        "generic",
                        "No passing module mock runtime dry-run exists for this binding.",
                        (
                            "Run a deterministic module mock invocation before future "
                            "activation review."
                        ),
                        severity="medium",
                        capability_binding_id=binding_id,
                        source_type="module_mock_runtime",
                        source_id=binding_id,
                    )
                )

        if request.risk_level in {"high", "critical"}:
            blockers.append(
                self._create_blocker(
                    scope,
                    activation_request_id,
                    "high_risk_requires_review",
                    "High-risk and critical requests require human review.",
                    "Record an operator review before future activation can be reconsidered.",
                    severity="critical" if request.risk_level == "critical" else "high",
                )
            )

        blockers.append(
            self._create_blocker(
                scope,
                activation_request_id,
                "activation_disabled",
                "Module activation execution is disabled in AION-083.",
                "Keep this request metadata-only until a later activation task enables execution.",
                severity="critical",
                metadata={"module_activation_execution_enabled": False},
            )
        )

        blockers.append(
            self._create_blocker(
                scope,
                activation_request_id,
                "dynamic_route_registration_disabled",
                "Runtime registration is disabled in AION-083.",
                "Use runtime registration preview only; do not register live routes.",
                severity="critical",
                metadata={"runtime_registration_enabled": False},
            )
        )

        if _contains_unsafe_metadata(request.metadata):
            blockers.append(
                self._create_blocker(
                    scope,
                    activation_request_id,
                    "unsafe_metadata",
                    "Activation metadata contains unsafe activation markers.",
                    "Remove activation or execution markers from metadata.",
                    severity="critical",
                )
            )
        return blockers

    def _create_blocker(
        self,
        scope: list[str],
        activation_request_id: str,
        blocker_type: str,
        reason: str,
        recommended_action: str,
        *,
        severity: str,
        capability_binding_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ActivationBlocker:
        request = self._repository.get_request(activation_request_id)
        return self._blocker_service.create_blocker(
            scope=scope,
            blocker_type=blocker_type,
            reason=reason,
            recommended_action=recommended_action,
            activation_request_id=activation_request_id,
            module_slot_id=request.module_slot_id if request else None,
            capability_binding_id=capability_binding_id,
            trace_id=request.trace_id if request else None,
            severity=severity,
            source_type=source_type,
            source_id=source_id,
            metadata=metadata,
        )

    def _record_audit(self, run: ActivationGateRun) -> None:
        if self._audit_sink is None:
            return
        try:
            self._audit_sink.record(
                AuditRecordRequest(
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    action_type="module_activation.gate.run",
                    resource_type="module_activation_gate",
                    resource_id=run.activation_gate_run_id,
                    event_type="module_activation_gate_completed",
                    outcome="blocked" if run.status == "blocked" else "dry_run",
                    risk_level="medium",
                    source_component="module_activation",
                    payload=redact_activation_payload(run.model_dump(mode="json")),
                    metadata={"activation_allowed": False, "runtime_mutated": False},
                )
            )
        except Exception:
            return

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        scope: list[str],
        payload: dict[str, object],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=0.7,
            scope=scope,
            payload=payload,
        )


def _module_slot_exists(repository: object | None, module_slot_id: str) -> bool:
    get_slot = getattr(repository, "get_slot", None)
    if not callable(get_slot):
        return False
    try:
        return get_slot(module_slot_id) is not None
    except Exception:
        return False


def _binding_exists(repository: object | None, capability_binding_id: str) -> bool:
    get_binding = getattr(repository, "get_binding", None)
    if not callable(get_binding):
        return False
    try:
        return get_binding(capability_binding_id) is not None
    except Exception:
        return False


def _readiness_ready(repository: object | None, readiness_ids: list[str]) -> bool:
    get_readiness = getattr(repository, "get_readiness", None)
    if not callable(get_readiness):
        return False
    for readiness_id in readiness_ids:
        try:
            item = get_readiness(readiness_id)
        except Exception:
            return False
        if item is None or not bool(getattr(item, "activation_ready", False)):
            return False
    return True


def _module_mock_run_count(repository: object | None, binding_ids: list[str]) -> int:
    list_runs = getattr(repository, "list_runs", None)
    if not callable(list_runs):
        return 0
    count = 0
    for binding_id in binding_ids:
        try:
            count += len(list_runs(capability_binding_id=binding_id, limit=100))
        except Exception:
            return count
    return count


def _module_mock_evidence_ready(repository: object | None, capability_binding_id: str) -> bool:
    list_runs = getattr(repository, "list_runs", None)
    if not callable(list_runs):
        return False
    try:
        runs = list_runs(capability_binding_id=capability_binding_id, limit=100)
    except Exception:
        return False
    return any(
        getattr(run, "status", None) in {"passed", "warning", "dry_run"}
        and getattr(run, "execution_allowed", True) is False
        and getattr(run, "activation_allowed", True) is False
        for run in runs
    )


def _warnings_for(blockers: list[ActivationBlocker]) -> list[dict[str, Any]]:
    return [
        {
            "blocker_id": blocker.activation_blocker_id,
            "blocker_type": blocker.blocker_type,
            "severity": blocker.severity,
            "activation_allowed": False,
        }
        for blocker in blockers
        if blocker.severity in {"low", "medium"}
    ]


def _contains_unsafe_metadata(metadata: dict[str, Any]) -> bool:
    markers = {
        "activate",
        "activated",
        "activation_performed",
        "execution_allowed",
        "registration_allowed",
        "runtime_mutated",
    }
    return any(str(key).lower() in markers and value for key, value in metadata.items())


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(requested_scope))


__all__ = ["ActivationGateService"]

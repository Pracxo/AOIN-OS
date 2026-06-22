"""Module binding validation gate."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.capability_bindings import (
    BindingValidationRequest,
    BindingValidationRun,
)
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.module_bindings.conflicts import BindingConflictService
from aion_brain.module_bindings.policy import authorize_module_binding_action
from aion_brain.module_bindings.repository import ModuleBindingRepository
from aion_brain.module_bindings.telemetry import emit_module_binding_telemetry


class BindingValidator:
    """Validate module slots and capability bindings without activation."""

    def __init__(
        self,
        repository: ModuleBindingRepository,
        policy_adapter: object,
        *,
        conflict_service: BindingConflictService,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        notification_router: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._conflict_service = conflict_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._notification_router = notification_router
        self._settings = settings or get_settings()

    def validate(self, request: BindingValidationRequest) -> BindingValidationRun:
        """Run deterministic validation and persist the validation run."""

        if not self._settings.binding_validation_enabled:
            raise RuntimeError("binding_validation_disabled")
        authorize_module_binding_action(
            self._policy_adapter,
            "module_binding.validate",
            request.owner_scope,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="binding_validation",
            risk_level="medium",
            context={"mode": request.mode, "metadata_only": True},
        )
        validation_id = request.binding_validation_id or f"binding-validation-{uuid4().hex}"
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="binding_validation_started",
            node_type="binding_validation",
            node_id=validation_id,
            scope=request.owner_scope,
            intensity=0.4,
            payload={"mode": request.mode},
        )
        checks = self._checks(request)
        conflicts = self._conflict_service.detect_conflicts(
            request.owner_scope,
            module_slot_id=request.module_slot_id,
            capability_binding_ids=request.capability_binding_ids,
            trace_id=request.trace_id,
        )
        if request.mode == "controlled":
            self._conflict_service.save_conflicts(conflicts)
        blockers = [
            *[finding for check in checks for finding in check.get("blockers", [])],
            *[
                _conflict_finding(conflict)
                for conflict in conflicts
                if conflict.severity in {"high", "critical"}
            ],
        ]
        warnings = [
            *[finding for check in checks for finding in check.get("warnings", [])],
            *[
                _conflict_finding(conflict)
                for conflict in conflicts
                if conflict.severity in {"low", "medium"}
            ],
        ]
        status = _status(request.mode, blockers, warnings)
        score = max(0.0, min(1.0, 1.0 - (0.2 * len(blockers)) - (0.05 * len(warnings))))
        run = BindingValidationRun(
            binding_validation_id=validation_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            module_slot_id=request.module_slot_id,
            extension_package_id=request.extension_package_id,
            capability_binding_ids=request.capability_binding_ids,
            checks=checks,
            findings=[
                *[finding for check in checks for finding in check.get("findings", [])],
                *[_conflict_finding(conflict) for conflict in conflicts],
            ],
            blockers=blockers,
            warnings=warnings,
            score=score,
            result={
                "metadata_only": True,
                "source_records_mutated": False,
                "conflict_records_persisted": request.mode == "controlled",
                "activation_allowed": False,
                "dynamic_route_registration_allowed": False,
            },
            metadata={**request.metadata, "source_mutated": False},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_validation_run(run)
        self._record_audit(saved)
        self._maybe_notify(request, saved)
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="binding_validation_completed",
            node_type="binding_validation",
            node_id=saved.binding_validation_id,
            scope=saved.owner_scope,
            intensity=0.8 if blockers else 0.5,
            payload={"status": saved.status, "score": saved.score},
        )
        return saved

    def get_validation_run(
        self,
        binding_validation_id: str,
        scope: list[str],
    ) -> BindingValidationRun | None:
        """Return one validation run through policy."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_binding.validate",
            scope,
            resource_type="binding_validation",
            resource_id=binding_validation_id,
            risk_level="low",
        )
        return self._repository.get_validation_run(binding_validation_id)

    def _checks(self, request: BindingValidationRequest) -> list[dict[str, Any]]:
        return [
            self._slot_check(request),
            self._binding_check(request),
            self._settings_check(request),
            self._security_check(request),
        ]

    def _slot_check(self, request: BindingValidationRequest) -> dict[str, Any]:
        blockers: list[dict[str, Any]] = []
        slot = (
            self._repository.get_slot(request.module_slot_id)
            if request.module_slot_id is not None
            else None
        )
        if request.module_slot_id and slot is None:
            blockers.append(_finding("module_slot_missing", "Requested module slot was not found."))
        if slot and slot.status in {"deleted", "archived"}:
            blockers.append(
                _finding("module_slot_inactive", "Archived or deleted slots cannot be mounted.")
            )
        return _check("module_slot", blockers=blockers)

    def _binding_check(self, request: BindingValidationRequest) -> dict[str, Any]:
        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        bindings = [
            binding
            for binding_id in request.capability_binding_ids
            if (binding := self._repository.get_binding(binding_id)) is not None
        ]
        if request.capability_binding_ids and len(bindings) != len(request.capability_binding_ids):
            blockers.append(
                _finding(
                    "capability_binding_missing",
                    "One or more requested capability bindings were not found.",
                )
            )
        if not bindings and request.module_slot_id:
            bindings = self._repository.list_bindings(module_slot_id=request.module_slot_id)
        for binding in bindings:
            if binding.status in {"disabled", "archived"}:
                warnings.append(
                    _finding(
                        "capability_binding_inactive",
                        "Inactive capability binding was included in validation.",
                        severity="medium",
                    )
                )
            if binding.risk_level in {"high", "critical"} and not binding.requires_approval:
                blockers.append(
                    _finding(
                        "high_risk_requires_review",
                        "High-risk bindings require approval metadata.",
                    )
                )
        return _check("capability_bindings", blockers=blockers, warnings=warnings)

    def _settings_check(self, request: BindingValidationRequest) -> dict[str, Any]:
        blockers: list[dict[str, Any]] = []
        if not bool(getattr(self._settings, "module_slots_enabled", True)):
            blockers.append(_finding("module_slots_disabled", "Module slots are disabled."))
        if not bool(getattr(self._settings, "capability_bindings_enabled", True)):
            blockers.append(
                _finding("capability_bindings_disabled", "Capability bindings are disabled.")
            )
        if bool(getattr(self._settings, "module_slot_activation_enabled", False)):
            blockers.append(
                _finding("module_slot_activation_enabled", "Module slot activation must be off.")
            )
        if bool(getattr(self._settings, "capability_binding_activation_enabled", False)):
            blockers.append(
                _finding(
                    "capability_binding_activation_enabled",
                    "Capability binding activation must be off.",
                )
            )
        if bool(getattr(self._settings, "dynamic_route_registration_enabled", False)):
            blockers.append(
                _finding(
                    "dynamic_route_registration_enabled",
                    "Dynamic route registration must be off.",
                )
            )
        return _check("runtime_settings", blockers=blockers, details={"mode": request.mode})

    def _security_check(self, request: BindingValidationRequest) -> dict[str, Any]:
        warnings: list[dict[str, Any]] = []
        if request.mode == "dry_run":
            warnings.append(
                _finding(
                    "dry_run_only",
                    "Dry-run validation does not persist conflict records.",
                    severity="low",
                )
            )
        return _check("security", warnings=warnings)

    def _record_audit(self, run: BindingValidationRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="module_binding.validate",
            resource_type="binding_validation",
            resource_id=run.binding_validation_id,
            event_type="binding_validation_completed",
            outcome="completed" if run.status != "failed" else "failed",
            source_component="module_binding_registry",
            trace_id=run.trace_id,
            actor_id=run.actor_id,
            workspace_id=run.workspace_id,
            risk_level="medium",
            payload={"status": run.status, "score": run.score},
        )

    def _maybe_notify(self, request: BindingValidationRequest, run: BindingValidationRun) -> None:
        if not (
            request.create_notifications
            or bool(getattr(self._settings, "module_binding_create_notifications_default", False))
        ):
            return
        publish = getattr(self._notification_router, "publish", None)
        if not callable(publish):
            return
        try:
            publish(
                NotificationPublishRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    topic_key="generic.info",
                    severity="high" if run.blockers else "info",
                    title="Module binding validation completed",
                    message=f"Module binding validation {run.binding_validation_id} completed.",
                    source_type="generic",
                    source_id=run.binding_validation_id,
                    target_type="operator",
                    target_id="operator",
                    owner_scope=run.owner_scope,
                    refs=[run.binding_validation_id],
                    metadata={"status": run.status, "metadata_only": True},
                    created_by=request.created_by,
                )
            )
        except Exception:
            return


def _check(
    name: str,
    *,
    blockers: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers = blockers or []
    warnings = warnings or []
    return {
        "name": name,
        "status": "failed" if blockers else "warning" if warnings else "passed",
        "findings": [*blockers, *warnings],
        "blockers": blockers,
        "warnings": warnings,
        "details": details or {},
    }


def _finding(code: str, message: str, *, severity: str = "high") -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message}


def _conflict_finding(conflict: object) -> dict[str, Any]:
    return {
        "code": getattr(conflict, "conflict_type", "binding_conflict"),
        "severity": getattr(conflict, "severity", "medium"),
        "message": getattr(conflict, "reason", "Binding conflict detected."),
        "binding_conflict_id": getattr(conflict, "binding_conflict_id", None),
    }


def _status(
    mode: str,
    blockers: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    if blockers:
        return (
            "blocked" if any(item.get("severity") == "critical" for item in blockers) else "failed"
        )
    if mode == "dry_run":
        return "dry_run"
    if warnings:
        return "warning"
    return "passed"


__all__ = ["BindingValidator"]

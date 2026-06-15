"""Sandbox control-plane service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.approvals import ApprovalCreateRequest
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessmentRequest
from aion_brain.contracts.sandbox import (
    RuntimePermissionGrant,
    RuntimePermissionGrantRequest,
    SandboxProfile,
    SandboxProfileCreateRequest,
    SandboxRunRequest,
    SandboxRunResult,
    SandboxValidationResult,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.sandbox.adapters import SandboxAdapter
from aion_brain.sandbox.repository import SandboxRepository
from aion_brain.sandbox.validator import SandboxValidator


class SandboxService:
    """Govern sandbox metadata, validation, dry-runs, and permission grants."""

    def __init__(
        self,
        *,
        sandbox_repository: SandboxRepository,
        sandbox_validator: SandboxValidator,
        risk_engine: object | None,
        approval_service: object | None,
        autonomy_governor: object | None,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        settings: Settings,
        adapters: dict[str, SandboxAdapter],
    ) -> None:
        self._repository = sandbox_repository
        self._validator = sandbox_validator
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._adapters = adapters

    def create_profile(self, request: SandboxProfileCreateRequest) -> SandboxProfile:
        """Create and persist a sandbox profile after policy and validation."""
        self._authorize(
            "sandbox.profile.create",
            "sandbox_profile",
            request.sandbox_profile_id,
            "medium",
            request.owner_scope,
            actor_id=request.created_by,
            context={"sandbox_type": request.sandbox_type, "activate": request.activate},
            approval_present=True,
        )
        now = datetime.now(UTC)
        profile = SandboxProfile(
            sandbox_profile_id=request.sandbox_profile_id or f"sandbox-profile-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active" if request.activate else "disabled",
            sandbox_type=request.sandbox_type,
            owner_scope=request.owner_scope,
            resource_limits=request.resource_limits,
            egress_rules=request.egress_rules,
            filesystem_rules=request.filesystem_rules,
            allowed_runtime_permissions=request.allowed_runtime_permissions,
            secret_refs_allowed=request.secret_refs_allowed,
            connector_refs_allowed=request.connector_refs_allowed,
            network_enabled=request.network_enabled,
            filesystem_write_enabled=request.filesystem_write_enabled,
            process_spawn_enabled=request.process_spawn_enabled,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None if request.activate else now,
        )
        validation = self._validator.validate_profile(profile)
        self._repository.save_validation(validation)
        if validation.status == "failed":
            raise ValueError("sandbox_profile_validation_failed")
        saved = self._repository.save_profile(profile)
        self._emit(
            "sandbox_profile_created",
            "sandbox",
            saved.sandbox_profile_id,
            0.5,
            {"sandbox_type": saved.sandbox_type, "status": saved.status},
        )
        return saved

    def get_profile(self, sandbox_profile_id: str, scope: list[str]) -> SandboxProfile | None:
        """Return one profile after read policy."""
        self._authorize(
            "sandbox.profile.read",
            "sandbox_profile",
            sandbox_profile_id,
            "low",
            scope,
            context={},
        )
        profile = self._repository.get_profile(sandbox_profile_id)
        if profile is None or not _scope_matches(profile.owner_scope, scope):
            return None
        return profile

    def list_profiles(
        self,
        scope: list[str],
        status: str | None = None,
    ) -> list[SandboxProfile]:
        """List profiles visible to a scope."""
        self._authorize("sandbox.profile.read", "sandbox_profile", None, "low", scope, context={})
        return [
            profile
            for profile in self._repository.list_profiles(status)
            if _scope_matches(profile.owner_scope, scope)
        ]

    def disable_profile(
        self,
        sandbox_profile_id: str,
        actor_id: str | None,
        reason: str,
    ) -> SandboxProfile:
        """Disable a profile."""
        profile = self._repository.get_profile(sandbox_profile_id)
        if profile is None:
            raise ValueError("sandbox_profile_not_found")
        self._authorize(
            "sandbox.profile.disable",
            "sandbox_profile",
            sandbox_profile_id,
            "medium",
            profile.owner_scope,
            actor_id=actor_id,
            context={"reason": reason},
            approval_present=True,
        )
        now = datetime.now(UTC)
        saved = self._repository.save_profile(
            profile.model_copy(
                update={
                    "status": "disabled",
                    "updated_at": now,
                    "disabled_at": now,
                    "metadata": {**profile.metadata, "disabled_reason": reason},
                }
            )
        )
        self._emit(
            "sandbox_profile_disabled",
            "sandbox",
            saved.sandbox_profile_id,
            0.7,
            {"reason": reason},
        )
        return saved

    def validate_profile(
        self,
        sandbox_profile_id: str,
        scope: list[str],
    ) -> SandboxValidationResult:
        """Validate a profile and persist the result."""
        self._authorize(
            "sandbox.profile.validate",
            "sandbox_profile",
            sandbox_profile_id,
            "low",
            scope,
            context={},
        )
        profile = self.get_profile(sandbox_profile_id, scope)
        if profile is None:
            raise ValueError("sandbox_profile_not_found")
        result = self._repository.save_validation(self._validator.validate_profile(profile))
        self._emit(
            "sandbox_profile_validated",
            "sandbox",
            result.validation_id,
            0.8 if result.status == "passed" else 1.0,
            {"status": result.status, "sandbox_profile_id": sandbox_profile_id},
            edge_from=sandbox_profile_id,
        )
        return result

    def run(self, request: SandboxRunRequest) -> SandboxRunResult:
        """Validate and dry-run a sandbox request without executing code."""
        profile = self._repository.get_profile(request.sandbox_profile_id)
        if profile is None:
            result = _run_result(request, "failed", error={"reason": "sandbox_profile_not_found"})
            return self._repository.save_run(request, result)
        decision = self._authorize_decision(
            "sandbox.run",
            request.target_type,
            request.target_id,
            "medium" if request.mode == "controlled" else "low",
            profile.owner_scope,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            context={
                "mode": request.mode,
                "sandbox_execution_enabled": self._settings.sandbox_execution_enabled,
                **request.metadata,
            },
            approval_present=request.approval_present,
        )
        if not decision.allow:
            result = _run_result(
                request,
                "blocked_by_policy",
                error={"reason": decision.reason, "constraints": decision.constraints},
            )
            self._emit_run("sandbox_run_blocked", result, 1.0)
            return self._repository.save_run(request, result)
        started = _run_result(request, "dry_run", output={"started": True})
        self._emit_run("sandbox_run_started", started, 0.5)

        autonomy = self._autonomy_decision(request, profile)
        if autonomy is not None and not bool(getattr(autonomy, "allow", True)):
            result = _run_result(
                request,
                "blocked_by_autonomy",
                error={"reason": str(getattr(autonomy, "reason", "autonomy_denied"))},
                autonomy_decision_id=getattr(autonomy, "autonomy_decision_id", None),
            )
            self._emit_run("sandbox_run_blocked", result, 1.0)
            return self._repository.save_run(request, result)

        risk = self._risk_assessment(request, profile)
        risk_assessment_id = getattr(risk, "risk_assessment_id", None)
        if getattr(risk, "decision", "allow") == "block":
            result = _run_result(
                request,
                "blocked_by_policy",
                error={"reason": "risk_blocked"},
                risk_assessment_id=risk_assessment_id,
            )
            self._emit_run("sandbox_run_blocked", result, 1.0)
            return self._repository.save_run(request, result)
        approval_required = (
            decision.approval_required or getattr(risk, "decision", "allow") == "require_approval"
        )
        if approval_required and not request.approval_present:
            approval_id = self._create_approval(request, profile, risk_assessment_id)
            result = _run_result(
                request,
                "waiting_for_approval",
                output={"approval_required": True},
                risk_assessment_id=risk_assessment_id,
                approval_request_id=approval_id,
            )
            self._emit_run("sandbox_run_blocked", result, 1.0)
            return self._repository.save_run(request, result)

        validation = self._repository.save_validation(
            self._validator.validate_run(request, profile)
        )
        if validation.status == "failed":
            result = _run_result(
                request,
                "failed",
                error={
                    "reason": "sandbox_validation_failed",
                    "validation_id": validation.validation_id,
                },
                risk_assessment_id=risk_assessment_id,
            )
            self._emit_run("sandbox_run_blocked", result, 1.0)
            return self._repository.save_run(request, result)

        if request.mode == "controlled" and not self._settings.sandbox_execution_enabled:
            result = _run_result(
                request,
                "unsupported",
                error={"reason": "sandbox_execution_disabled"},
                risk_assessment_id=risk_assessment_id,
            )
            self._emit_run("sandbox_run_completed", result, 0.8)
            return self._repository.save_run(request, result)

        adapter = self._adapters.get(profile.sandbox_type)
        if adapter is None:
            result = _run_result(
                request,
                "unsupported",
                error={"reason": "sandbox_adapter_unavailable"},
                risk_assessment_id=risk_assessment_id,
            )
        else:
            result = adapter.run(request, profile).model_copy(
                update={"risk_assessment_id": risk_assessment_id}
            )
        completed_statuses = {"dry_run", "completed", "unsupported"}
        self._emit_run(
            "sandbox_run_completed"
            if result.status in completed_statuses
            else "sandbox_run_blocked",
            result,
            0.8 if result.status in completed_statuses else 1.0,
        )
        return self._repository.save_run(request, result)

    def grant_runtime_permission(
        self,
        request: RuntimePermissionGrantRequest,
    ) -> RuntimePermissionGrant:
        """Create an explicit runtime permission grant."""
        self._authorize(
            "runtime_permission.grant",
            "runtime_permission",
            request.runtime_permission_id,
            "medium",
            request.owner_scope,
            actor_id=request.granted_by,
            context={"target_type": request.target_type, "target_id": request.target_id},
            approval_present=True,
        )
        now = datetime.now(UTC)
        grant = RuntimePermissionGrant(
            runtime_permission_id=request.runtime_permission_id
            or f"runtime-permission-{uuid4().hex}",
            target_type=request.target_type,
            target_id=request.target_id,
            sandbox_profile_id=request.sandbox_profile_id,
            owner_scope=request.owner_scope,
            permissions=request.permissions,
            secret_refs=request.secret_refs,
            connector_refs=request.connector_refs,
            status="active",
            granted_by=request.granted_by,
            expires_at=request.expires_at,
            metadata=request.metadata,
            created_at=now,
            revoked_at=None,
        )
        validation = self._repository.save_validation(
            self._validator.validate_runtime_permissions(grant)
        )
        if validation.status == "failed":
            raise ValueError("runtime_permission_validation_failed")
        saved = self._repository.save_runtime_permission(grant)
        self._emit(
            "runtime_permission_granted",
            "runtime_permission",
            saved.runtime_permission_id,
            0.5,
            {"target_type": saved.target_type, "target_id": saved.target_id},
        )
        return saved

    def list_runtime_permissions(
        self,
        target_type: str | None = None,
        target_id: str | None = None,
        status: str | None = None,
    ) -> list[RuntimePermissionGrant]:
        """List runtime permissions after policy."""
        self._authorize(
            "runtime_permission.read",
            "runtime_permission",
            None,
            "low",
            ["workspace:main"],
            context={"target_type": target_type, "target_id": target_id},
        )
        return self._repository.list_runtime_permissions(
            target_type=target_type,
            target_id=target_id,
            status=status,
        )

    def revoke_runtime_permission(
        self,
        runtime_permission_id: str,
        actor_id: str | None,
        reason: str,
    ) -> RuntimePermissionGrant:
        """Revoke one runtime permission grant."""
        grant = self._repository.get_runtime_permission(runtime_permission_id)
        if grant is None:
            raise ValueError("runtime_permission_not_found")
        self._authorize(
            "runtime_permission.revoke",
            "runtime_permission",
            runtime_permission_id,
            "medium",
            grant.owner_scope,
            actor_id=actor_id,
            context={"reason": reason},
            approval_present=True,
        )
        saved = self._repository.save_runtime_permission(
            grant.model_copy(
                update={
                    "status": "revoked",
                    "revoked_at": datetime.now(UTC),
                    "metadata": {**grant.metadata, "revoked_reason": reason},
                }
            )
        )
        self._emit(
            "runtime_permission_revoked",
            "runtime_permission",
            saved.runtime_permission_id,
            0.7,
            {"reason": reason},
        )
        return saved

    def has_active_grant(
        self,
        *,
        target_type: str,
        target_id: str,
        sandbox_profile_id: str | None = None,
    ) -> bool:
        """Return whether a target has an active grant."""
        grants = self._repository.list_runtime_permissions(
            target_type=target_type,
            target_id=target_id,
            status="active",
        )
        if sandbox_profile_id is None:
            return bool(grants)
        return any(grant.sandbox_profile_id == sandbox_profile_id for grant in grants)

    def _authorize(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        trace_id: str | None = None,
        context: dict[str, Any],
        approval_present: bool = False,
    ) -> PolicyDecision:
        decision = self._authorize_decision(
            action_type,
            resource_type,
            resource_id,
            risk_level,
            scope,
            actor_id=actor_id,
            workspace_id=workspace_id,
            trace_id=trace_id,
            context=context,
            approval_present=approval_present,
        )
        if not decision.allow:
            raise PermissionError(f"policy_denied:{decision.reason}")
        return decision

    def _authorize_decision(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        trace_id: str | None = None,
        context: dict[str, Any],
        approval_present: bool = False,
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context,
            )
        )

    def _autonomy_decision(
        self,
        request: SandboxRunRequest,
        profile: SandboxProfile,
    ) -> object | None:
        if self._autonomy_governor is None:
            return None
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode=(
                        "dry_run" if request.mode == "dry_run" else "supervised_controlled"
                    ),
                    action_type="sandbox.run",
                    resource_type=request.target_type,
                    resource_id=request.target_id,
                    risk_level=cast(Any, "medium" if request.mode == "controlled" else "low"),
                    approval_present=request.approval_present,
                    context={"security_scope": profile.owner_scope, "mode": request.mode},
                    metadata={},
                )
            ),
        )

    def _risk_assessment(
        self,
        request: SandboxRunRequest,
        profile: SandboxProfile,
    ) -> object | None:
        if self._risk_engine is None:
            return None
        assess = getattr(self._risk_engine, "assess", None)
        if not callable(assess):
            return None
        return cast(
            object,
            assess(
                RiskAssessmentRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    action_type="sandbox.run",
                    resource_type=request.target_type,
                    resource_id=request.target_id,
                    requested_risk_level=cast(
                        Any,
                        "medium" if request.mode == "controlled" else "low",
                    ),
                    payload=request.input,
                    context={
                        "security_scope": profile.owner_scope,
                        "controlled_execution": request.mode == "controlled",
                        "approval_present": request.approval_present,
                        "dry_run": request.mode == "dry_run",
                    },
                    metadata={},
                )
            ),
        )

    def _create_approval(
        self,
        request: SandboxRunRequest,
        profile: SandboxProfile,
        risk_assessment_id: str | None,
    ) -> str | None:
        if self._approval_service is None:
            return None
        create = getattr(self._approval_service, "create_request", None)
        if not callable(create):
            return None
        approval = create(
            ApprovalCreateRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                requested_by=request.actor_id,
                action_type="sandbox.run",
                resource_type=request.target_type,
                resource_id=request.target_id,
                title="Approve sandbox run",
                description="AION Sandbox Control Plane requires approval.",
                risk_assessment_id=risk_assessment_id,
                priority="normal",
                approval_scope=profile.owner_scope,
                payload={"sandbox_profile_id": profile.sandbox_profile_id},
                constraints=[],
            )
        )
        return str(getattr(approval, "approval_request_id", "")) or None

    def _emit_run(self, event_type: str, result: SandboxRunResult, intensity: float) -> None:
        self._emit(
            event_type,
            "sandbox",
            result.sandbox_run_id,
            intensity,
            {"status": result.status, "mode": result.mode},
            edge_from=result.sandbox_profile_id,
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
        *,
        edge_from: str | None = None,
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=node_id,
                    event_type=cast(Any, event_type),
                    node_type=cast(Any, node_type),
                    node_id=node_id,
                    edge_from=edge_from,
                    edge_to=node_id,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _run_result(
    request: SandboxRunRequest,
    status: str,
    *,
    output: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    risk_assessment_id: str | None = None,
    approval_request_id: str | None = None,
    autonomy_decision_id: str | None = None,
) -> SandboxRunResult:
    now = datetime.now(UTC)
    return SandboxRunResult(
        sandbox_run_id=request.sandbox_run_id or f"sandbox-run-{uuid4().hex}",
        trace_id=request.trace_id,
        sandbox_profile_id=request.sandbox_profile_id,
        target_type=request.target_type,
        target_id=request.target_id,
        mode=request.mode,
        status=cast(Any, status),
        output=output or {},
        error=error or {},
        risk_assessment_id=risk_assessment_id,
        approval_request_id=approval_request_id,
        autonomy_decision_id=autonomy_decision_id,
        created_at=now,
        started_at=now,
        completed_at=now,
    )


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(set(requested_scope)))

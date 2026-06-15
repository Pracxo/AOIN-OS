"""AION Autonomy Governor."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.autonomy.defaults import default_dev_profile
from aion_brain.autonomy.delegation import DelegationService
from aion_brain.autonomy.modes import min_mode, min_risk, mode_allows, risk_allows
from aion_brain.autonomy.repository import AutonomyRepository
from aion_brain.autonomy.run_level import RunLevelService
from aion_brain.config import Settings
from aion_brain.contracts.autonomy import (
    AutonomyDecision,
    AutonomyDecisionRequest,
    AutonomyLifecycleEvent,
    AutonomyProfile,
    AutonomyProfileCreateRequest,
    AutonomyStatus,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter


class AutonomyGovernor:
    """Resolve the maximum operating mode AION may use."""

    def __init__(
        self,
        repository: AutonomyRepository,
        policy_adapter: PolicyAdapter,
        *,
        delegation_service: DelegationService | None = None,
        run_level_service: RunLevelService | None = None,
        risk_engine: object | None = None,
        approval_service: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._delegation_service = delegation_service
        self._run_level_service = run_level_service
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._audit_sink = audit_sink

    def create_profile(self, request: AutonomyProfileCreateRequest) -> AutonomyProfile:
        """Create an autonomy profile."""
        self._authorize(
            "autonomy.profile.create",
            actor_id=request.created_by or request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope or ["workspace:main"],
            context={"name": request.name, "activate": request.activate},
        )
        now = datetime.now(UTC)
        profile = AutonomyProfile(
            autonomy_profile_id=request.autonomy_profile_id or f"autonomy-profile-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active" if request.activate else "disabled",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope or ["workspace:main"],
            default_mode=request.default_mode,
            max_mode=request.max_mode,
            max_risk_level=request.max_risk_level,
            allowed_action_types=request.allowed_action_types,
            denied_action_types=request.denied_action_types,
            external_models_allowed=request.external_models_allowed,
            external_tools_allowed=request.external_tools_allowed,
            background_workflows_allowed=request.background_workflows_allowed,
            scheduler_allowed=request.scheduler_allowed,
            skill_promotion_allowed=request.skill_promotion_allowed,
            memory_forgetting_allowed=request.memory_forgetting_allowed,
            approval_required_modes=request.approval_required_modes,
            constraints=request.constraints,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None if request.activate else now,
        )
        saved = self._repository.save_profile(profile)
        self._record_event("autonomy_profile_created", profile=saved)
        return saved

    def list_profiles(
        self,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[AutonomyProfile]:
        """List autonomy profiles."""
        self._authorize(
            "autonomy.profile.read",
            actor_id=actor_id,
            workspace_id=workspace_id,
            scope=["workspace:main"],
            context={"status": status},
            risk_level="low",
        )
        return self._repository.list_profiles(
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
        )

    def get_profile(self, autonomy_profile_id: str) -> AutonomyProfile | None:
        """Return one autonomy profile."""
        self._authorize(
            "autonomy.profile.read",
            actor_id=None,
            workspace_id=None,
            scope=["workspace:main"],
            context={"autonomy_profile_id": autonomy_profile_id},
            risk_level="low",
        )
        return self._repository.get_profile(autonomy_profile_id)

    def disable_profile(
        self,
        autonomy_profile_id: str,
        actor_id: str | None,
        reason: str,
    ) -> AutonomyProfile:
        """Disable one profile."""
        profile = self._repository.get_profile(autonomy_profile_id)
        if profile is None:
            raise ValueError("autonomy_profile_not_found")
        self._authorize(
            "autonomy.profile.disable",
            actor_id=actor_id,
            workspace_id=profile.workspace_id,
            scope=profile.owner_scope,
            context={"reason": reason},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_profile(
            profile.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": now,
                    "updated_at": now,
                    "constraints": [*profile.constraints, f"disabled:{reason}"],
                }
            )
        )
        self._record_event("autonomy_profile_disabled", profile=saved)
        return saved

    def decide(self, request: AutonomyDecisionRequest) -> AutonomyDecision:
        """Resolve and persist one autonomy decision."""
        if not self._settings.autonomy_enabled:
            return self._save_decision(
                request,
                resolved_mode="disabled",
                allow=False,
                approval_required=False,
                reason="autonomy_disabled",
                constraints=["autonomy_disabled"],
                profile=None,
                run_level=None,
            )
        policy = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"autonomy.decide-{uuid4().hex}",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="autonomy.decide",
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                risk_level=request.risk_level,
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=_scope(request),
                context=request.context,
            )
        )
        if not policy.allow:
            return self._save_decision(
                request,
                resolved_mode="disabled",
                allow=False,
                approval_required=False,
                reason=policy.reason,
                constraints=policy.constraints,
                profile=None,
                run_level=None,
            )

        scope = _scope(request)
        profile = self._active_profile(request, scope)
        run_level = self._active_run_level(request)
        max_mode = min_mode(profile.max_mode, self._settings.autonomy_default_max_mode)
        if run_level is not None:
            max_mode = min_mode(max_mode, run_level.run_level)
        max_risk = min_risk(profile.max_risk_level, self._settings.autonomy_default_max_risk_level)
        constraints = list(profile.constraints)
        if run_level is not None:
            constraints.extend(run_level.constraints)

        decision_error = _first_decision_error(request, profile, max_mode, max_risk)
        delegation = None
        if decision_error is None and request.requested_mode == "delegated_controlled":
            delegation = self._resolve_delegation(request, scope)
            if delegation is None:
                decision_error = ("delegation_required", ["active_delegation_required"])
        if decision_error is None and request.requested_mode == "supervised_controlled":
            if not request.approval_present:
                decision_error = (
                    "approval_required_for_mode",
                    ["approval_required:supervised_controlled"],
                )
        if decision_error is None:
            decision_error = _first_gate_error(request, profile)

        if decision_error is not None:
            reason, gate_constraints = decision_error
            approval_required = reason == "approval_required_for_mode"
            return self._save_decision(
                request,
                resolved_mode=max_mode,
                allow=False,
                approval_required=approval_required,
                reason=reason,
                constraints=[*constraints, *gate_constraints],
                profile=profile,
                run_level=run_level,
                delegation_id=delegation.delegation_id if delegation is not None else None,
            )

        resolved_delegation_id = (
            delegation.delegation_id if delegation is not None else request.delegation_id
        )
        return self._save_decision(
            request,
            resolved_mode=request.requested_mode,
            allow=True,
            approval_required=False,
            reason="autonomy_allowed",
            constraints=constraints,
            profile=profile,
            run_level=run_level,
            delegation_id=resolved_delegation_id,
        )

    def status(
        self,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
    ) -> AutonomyStatus:
        """Return current autonomy status."""
        self._authorize(
            "autonomy.status.read",
            actor_id=actor_id,
            workspace_id=workspace_id,
            scope=scope,
            context={},
            risk_level="low",
        )
        request = AutonomyDecisionRequest(
            actor_id=actor_id,
            workspace_id=workspace_id,
            requested_mode="assist",
            action_type="autonomy.status.read",
            resource_type="autonomy",
            risk_level="low",
            context={"security_scope": scope},
        )
        profile = self._active_profile(request, scope)
        run_level = self._active_run_level(request)
        effective_mode = profile.default_mode
        if run_level is not None:
            effective_mode = min_mode(effective_mode, run_level.run_level)  # type: ignore[assignment]
        max_risk = min_risk(profile.max_risk_level, self._settings.autonomy_default_max_risk_level)
        delegations = (
            self._delegation_service.list_grants(actor_id, workspace_id, "active")
            if self._delegation_service is not None
            else self._repository.list_delegations(
                actor_id=actor_id,
                workspace_id=workspace_id,
                status="active",
            )
        )
        return AutonomyStatus(
            actor_id=actor_id,
            workspace_id=workspace_id,
            active_profile=profile,
            active_run_level=run_level,
            active_delegations=delegations,
            effective_mode=effective_mode,
            max_risk_level=max_risk,  # type: ignore[arg-type]
            constraints=profile.constraints + (run_level.constraints if run_level else []),
            generated_at=datetime.now(UTC),
        )

    def _active_profile(
        self,
        request: AutonomyDecisionRequest,
        scope: list[str],
    ) -> AutonomyProfile:
        profile = self._repository.get_active_profile(
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
        )
        if profile is not None:
            return profile
        return default_dev_profile(
            self._settings,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=scope,
        )

    def _active_run_level(self, request: AutonomyDecisionRequest) -> Any | None:
        if self._run_level_service is not None:
            try:
                return self._run_level_service.get_active_run_level(
                    request.actor_id,
                    request.workspace_id,
                )
            except PermissionError:
                return None
        return self._repository.get_active_run_level(
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
        )

    def _resolve_delegation(
        self,
        request: AutonomyDecisionRequest,
        scope: list[str],
    ) -> Any | None:
        if request.delegation_id:
            grant = self._repository.get_delegation(request.delegation_id)
            if grant is None:
                return None
            if _delegation_covers(grant, request, scope):
                return grant
            return None
        if self._delegation_service is None:
            return None
        return self._delegation_service.find_active_grant(
            request.actor_id,
            request.workspace_id,
            request.action_type,
            request.resource_type,
            request.risk_level,
            scope,
        )

    def _authorize(
        self,
        action_type: str,
        *,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        context: dict[str, object],
        risk_level: str = "medium",
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="autonomy",
                resource_id=None,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _save_decision(
        self,
        request: AutonomyDecisionRequest,
        *,
        resolved_mode: str,
        allow: bool,
        approval_required: bool,
        reason: str,
        constraints: list[str],
        profile: AutonomyProfile | None,
        run_level: Any | None,
        delegation_id: str | None = None,
    ) -> AutonomyDecision:
        decision = AutonomyDecision(
            autonomy_decision_id=request.autonomy_decision_id
            or f"autonomy-decision-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            requested_mode=request.requested_mode,
            resolved_mode=resolved_mode,  # type: ignore[arg-type]
            action_type=request.action_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            risk_level=request.risk_level,
            allow=allow,
            approval_required=approval_required,
            delegation_id=delegation_id,
            autonomy_profile_id=profile.autonomy_profile_id if profile is not None else None,
            run_level_id=getattr(run_level, "run_level_id", None),
            reason=reason,
            constraints=constraints,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_decision(decision)
        self._record_event("autonomy_decision_recorded", decision=saved)
        if not saved.allow:
            self._record_event("autonomy_blocked", decision=saved)
        if saved.approval_required:
            self._record_event("autonomy_escalation_required", decision=saved)
        record_audit_event(
            self._audit_sink,
            action_type="autonomy.decide",
            resource_type=saved.resource_type,
            resource_id=saved.resource_id or saved.autonomy_decision_id,
            event_type="autonomy_decision_recorded",
            outcome="allowed" if saved.allow else "blocked",
            source_component="autonomy_governor",
            trace_id=saved.trace_id,
            actor_id=saved.actor_id,
            workspace_id=saved.workspace_id,
            risk_level=saved.risk_level,
            autonomy_decision_id=saved.autonomy_decision_id,
            payload={
                "requested_mode": saved.requested_mode,
                "resolved_mode": saved.resolved_mode,
                "approval_required": saved.approval_required,
                "reason": saved.reason,
            },
        )
        return saved

    def _record_event(
        self,
        event_type: str,
        *,
        profile: AutonomyProfile | None = None,
        decision: AutonomyDecision | None = None,
    ) -> None:
        event = AutonomyLifecycleEvent(
            autonomy_event_id=f"autonomy-event-{uuid4().hex}",
            autonomy_profile_id=profile.autonomy_profile_id if profile else None,
            autonomy_decision_id=decision.autonomy_decision_id if decision else None,
            trace_id=decision.trace_id if decision else None,
            event_type=event_type,  # type: ignore[arg-type]
            actor_id=(profile.actor_id if profile else decision.actor_id if decision else None),
            workspace_id=(
                profile.workspace_id if profile else decision.workspace_id if decision else None
            ),
            payload=_event_payload(profile, decision),
            created_at=datetime.now(UTC),
        )
        self._repository.save_lifecycle_event(event)
        node_type = "profile" if profile is not None else "autonomy"
        node_id = (
            profile.autonomy_profile_id
            if profile is not None
            else decision.autonomy_decision_id
            if decision is not None
            else event.autonomy_event_id
        )
        intensity = _event_intensity(event_type, decision)
        _emit(self._telemetry_service, event_type, node_type, node_id, intensity, event.payload)


def _first_decision_error(
    request: AutonomyDecisionRequest,
    profile: AutonomyProfile,
    max_mode: str,
    max_risk: str,
) -> tuple[str, list[str]] | None:
    if request.action_type in profile.denied_action_types:
        return "action_denied_by_profile", ["denied_action_type"]
    if profile.allowed_action_types and request.action_type not in profile.allowed_action_types:
        return "action_not_allowed_by_profile", ["allowed_action_types_restricted"]
    if not risk_allows(request.risk_level, max_risk):
        return "risk_exceeds_autonomy_limit", [f"max_risk:{max_risk}"]
    if not mode_allows(request.requested_mode, max_mode):
        return "mode_exceeds_autonomy_limit", [f"max_mode:{max_mode}"]
    if request.requested_mode == "disabled":
        return "autonomy_mode_disabled", ["mode:disabled"]
    return None


def _first_gate_error(
    request: AutonomyDecisionRequest,
    profile: AutonomyProfile,
) -> tuple[str, list[str]] | None:
    if _requires_external_model_gate(request) and not profile.external_models_allowed:
        return "external_models_not_allowed", ["external_models_allowed:false"]
    if _requires_external_tool_gate(request) and not profile.external_tools_allowed:
        return "external_tools_not_allowed", ["external_tools_allowed:false"]
    if _requires_scheduler_gate(request) and not profile.scheduler_allowed:
        return "scheduler_not_allowed", ["scheduler_allowed:false"]
    if _requires_background_workflow_gate(request) and not profile.background_workflows_allowed:
        return "background_workflows_not_allowed", ["background_workflows_allowed:false"]
    if request.action_type in {"skill.promote", "skill.activate"}:
        if not profile.skill_promotion_allowed:
            return "skill_promotion_not_allowed", ["skill_promotion_allowed:false"]
    if request.action_type == "memory.forget.execute":
        if not profile.memory_forgetting_allowed:
            return "memory_forgetting_not_allowed", ["memory_forgetting_allowed:false"]
    return None


def _requires_external_model_gate(request: AutonomyDecisionRequest) -> bool:
    return request.action_type.startswith("model.") and any(
        bool(request.context.get(key))
        for key in ("allow_external", "uses_external_model", "external_model")
    )


def _requires_external_tool_gate(request: AutonomyDecisionRequest) -> bool:
    if request.requested_mode == "dry_run":
        return False
    if request.action_type.startswith("mcp."):
        return True
    if request.action_type in {"capability.invoke", "module.runtime.invoke"}:
        return request.requested_mode in {"supervised_controlled", "delegated_controlled"}
    return bool(request.context.get("uses_external_tool"))


def _requires_scheduler_gate(request: AutonomyDecisionRequest) -> bool:
    return request.action_type in {"scheduler.tick", "workflow.scheduler.tick"}


def _requires_background_workflow_gate(request: AutonomyDecisionRequest) -> bool:
    return request.action_type in {"workflow.worker.start", "workflow.run"} and bool(
        request.context.get("background_workflow")
    )


def _delegation_covers(grant: Any, request: AutonomyDecisionRequest, scope: list[str]) -> bool:
    if getattr(grant, "status", None) != "active":
        return False
    expires_at = getattr(grant, "expires_at", None)
    if isinstance(expires_at, datetime):
        expires_at = expires_at if expires_at.tzinfo is not None else expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            return False
    owner_scope = getattr(grant, "owner_scope", [])
    if not set(owner_scope).intersection(set(scope)):
        return False
    allowed_action_types = getattr(grant, "allowed_action_types", [])
    if allowed_action_types and request.action_type not in allowed_action_types:
        return False
    resource_types = getattr(grant, "resource_types", [])
    if resource_types and request.resource_type not in resource_types:
        return False
    return risk_allows(request.risk_level, getattr(grant, "max_risk_level", "low"))


def _scope(request: AutonomyDecisionRequest) -> list[str]:
    value = request.context.get("security_scope") or request.metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return ["workspace:main"]


def _event_payload(
    profile: AutonomyProfile | None,
    decision: AutonomyDecision | None,
) -> dict[str, Any]:
    if profile is not None:
        return {
            "status": profile.status,
            "default_mode": profile.default_mode,
            "max_mode": profile.max_mode,
        }
    if decision is not None:
        return {
            "allow": decision.allow,
            "requested_mode": decision.requested_mode,
            "resolved_mode": decision.resolved_mode,
            "reason": decision.reason,
        }
    return {}


def _event_intensity(event_type: str, decision: AutonomyDecision | None) -> float:
    if event_type == "autonomy_blocked":
        return 1.0
    if event_type == "autonomy_escalation_required":
        return 0.8
    if event_type == "autonomy_decision_recorded":
        return 0.6 if decision is not None and decision.allow else 0.9
    if event_type == "autonomy_profile_created":
        return 0.5
    return 0.6


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, Any],
) -> None:
    if telemetry_service is None:
        return
    event = VisualTelemetryEvent(
        telemetry_id=f"telemetry-{node_id}-{event_type}",
        trace_id=str(payload.get("trace_id") or node_id),
        event_type=event_type,  # type: ignore[arg-type]
        node_type=node_type,  # type: ignore[arg-type]
        node_id=node_id,
        edge_from=None,
        edge_to=node_id,
        intensity=intensity,
        payload=payload,
        created_at=datetime.now(UTC),
    )
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
            return
        save = getattr(telemetry_service, "save_visual_telemetry", None)
        if callable(save):
            save(event.trace_id, [event])
    except Exception:
        return

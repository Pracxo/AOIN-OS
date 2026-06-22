"""Skill Registry service."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.approvals.integration import ApprovalGateResult, evaluate_approval_gate
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reflection import ReflectionRecord
from aion_brain.contracts.skills import (
    SkillActivationEvent,
    SkillActivationEventType,
    SkillActivationRequest,
    SkillCandidate,
    SkillMatchRequest,
    SkillMatchResult,
    SkillPromotionRequest,
    SkillPromotionResponse,
    SkillRecord,
    SkillStatus,
    SkillVersion,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.skills.matcher import SkillMatcher
from aion_brain.skills.promotion import ACTION_POLICY, SkillCandidateBuilder
from aion_brain.skills.repository import SkillRepository

ALLOWED_SKILL_TRANSITIONS = {
    "draft": {"active", "archived"},
    "active": {"disabled", "archived"},
    "disabled": {"active", "archived"},
    "archived": set(),
}


class SkillService:
    """Policy-gated procedural memory registry."""

    def __init__(
        self,
        *,
        skill_repository: SkillRepository | object,
        reflection_repository: object,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
        candidate_builder: SkillCandidateBuilder | None = None,
        matcher: SkillMatcher | None = None,
        approval_service: object | None = None,
        autonomy_governor: object | None = None,
    ) -> None:
        self._repository = skill_repository
        self._reflection_repository = reflection_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._candidate_builder = candidate_builder or SkillCandidateBuilder()
        self._matcher = matcher or SkillMatcher(skill_repository)
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor

    def create_candidate_from_reflection(self, reflection_id: str) -> SkillCandidate | None:
        """Create a skill candidate from a reflection when evidence is strong enough."""
        decision = self._authorize(
            action_type="skill.candidate.create",
            resource_type="skill_candidate",
            resource_id=None,
            risk_level="medium",
            scope=["workspace:main"],
            context={"reflection_id": reflection_id},
            approval_present=False,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        reflection = _get_reflection(self._reflection_repository, reflection_id)
        if reflection is None:
            raise ValueError("reflection_not_found")
        candidate = self._candidate_builder.build(reflection)
        if candidate is None:
            return None
        saved = _save_candidate(self._repository, candidate)
        self._emit_candidate(saved, "skill_candidate_created", saved.confidence)
        return saved

    def get_candidate(self, candidate_id: str) -> SkillCandidate | None:
        """Return a skill candidate after policy checks."""
        decision = self._authorize(
            action_type="skill.candidate.read",
            resource_type="skill_candidate",
            resource_id=candidate_id,
            risk_level="low",
            scope=["workspace:main"],
            context={},
            approval_present=False,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        return _get_candidate(self._repository, candidate_id)

    def list_candidates(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillCandidate]:
        """List skill candidates."""
        decision = self._authorize(
            action_type="skill.candidate.read",
            resource_type="skill_candidate",
            resource_id=None,
            risk_level="low",
            scope=["workspace:main"],
            context={"status": status},
            approval_present=False,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        list_candidates = getattr(self._repository, "list_candidates", None)
        if callable(list_candidates):
            result = list_candidates(status=status, limit=limit)
            if isinstance(result, list):
                return [item for item in result if isinstance(item, SkillCandidate)]
        return []

    def update_candidate_status(
        self,
        candidate_id: str,
        status: str,
        reason: str,
    ) -> SkillCandidate:
        """Update candidate review status."""
        candidate = _get_candidate(self._repository, candidate_id)
        if candidate is None:
            raise ValueError("candidate_not_found")
        decision = self._authorize(
            action_type="skill.candidate.update",
            resource_type="skill_candidate",
            resource_id=candidate_id,
            risk_level="medium",
            scope=["workspace:main"],
            context={"status": status, "reason": reason},
            approval_present=False,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        updated = candidate.model_copy(update={"status": status, "updated_at": datetime.now(UTC)})
        saved = _save_candidate(self._repository, updated)
        self._emit_candidate(saved, "skill_candidate_updated", saved.confidence)
        return saved

    def promote_candidate(self, request: SkillPromotionRequest) -> SkillPromotionResponse:
        """Promote a reviewed candidate into a data-only skill record."""
        candidate = _get_candidate(self._repository, request.candidate_id)
        if candidate is None:
            return _promotion_response(request, False, "candidate_not_found")
        validation_reason = _promotion_validation_reason(candidate)
        if validation_reason is not None:
            return _promotion_response(request, False, validation_reason)
        autonomy = self._autonomy_decision(
            action_type="skill.promote",
            resource_type="skill_candidate",
            resource_id=request.candidate_id,
            risk_level=candidate.risk_level,
            actor_id=request.actor_id,
            scope=request.owner_scope,
            metadata=request.metadata,
        )
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return _promotion_response(
                request,
                False,
                f"autonomy_denied:{getattr(autonomy, 'reason', 'autonomy_denied')}",
            )
        decision = self._authorize(
            action_type="skill.promote",
            resource_type="skill_candidate",
            resource_id=request.candidate_id,
            risk_level=candidate.risk_level,
            scope=request.owner_scope,
            context=request.model_dump(mode="json"),
            approval_present=False,
            actor_id=request.actor_id,
        )
        if not decision.allow:
            return _promotion_response(request, False, f"policy_denied:{decision.reason}")
        if _skill_requires_approval(candidate.risk_level, request.metadata):
            gate = self._approval_gate_for_promotion(request, candidate)
            return _promotion_response(
                request,
                False,
                _approval_reason(gate),
            )

        now = datetime.now(UTC)
        skill_id = f"skill-{uuid4().hex}"
        version_id = f"skill-version-{uuid4().hex}"
        status: SkillStatus = "draft"
        if request.activate:
            autonomy = self._autonomy_decision(
                action_type="skill.activate",
                resource_type="skill",
                resource_id=skill_id,
                risk_level=candidate.risk_level,
                actor_id=request.actor_id,
                scope=request.owner_scope,
                metadata=request.metadata,
            )
            if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
                return _promotion_response(
                    request,
                    False,
                    f"autonomy_denied:{getattr(autonomy, 'reason', 'autonomy_denied')}",
                )
            activate_decision = self._authorize(
                action_type="skill.activate",
                resource_type="skill",
                resource_id=skill_id,
                risk_level=candidate.risk_level,
                scope=request.owner_scope,
                context={"candidate_id": candidate.candidate_id, "reason": request.reason},
                approval_present=False,
                actor_id=request.actor_id,
            )
            if activate_decision.allow:
                if _skill_requires_approval(candidate.risk_level, request.metadata):
                    return _promotion_response(
                        request,
                        False,
                        _approval_reason(self._approval_gate_for_promotion(request, candidate)),
                    )
                status = "active"
        skill = SkillRecord(
            skill_id=skill_id,
            candidate_id=candidate.candidate_id,
            name=candidate.name,
            description=candidate.description,
            status=status,
            risk_level=candidate.risk_level,
            current_version=1,
            trigger_patterns=candidate.trigger_patterns,
            preconditions=candidate.preconditions,
            procedure_steps=candidate.procedure_steps,
            expected_outcomes=candidate.expected_outcomes,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
            activated_at=now if status == "active" else None,
            disabled_at=None,
        )
        version = SkillVersion(
            skill_version_id=version_id,
            skill_id=skill_id,
            version=1,
            name=skill.name,
            description=skill.description,
            trigger_patterns=skill.trigger_patterns,
            preconditions=skill.preconditions,
            procedure_steps=skill.procedure_steps,
            expected_outcomes=skill.expected_outcomes,
            change_reason=request.reason,
            source_candidate_id=candidate.candidate_id,
            created_at=now,
        )
        _save_skill(self._repository, skill)
        _save_version(self._repository, version)
        _save_candidate(
            self._repository,
            candidate.model_copy(update={"status": "promoted", "updated_at": now}),
        )
        self._record_event(
            SkillActivationEvent(
                activation_event_id=f"activation-{uuid4().hex}",
                skill_id=skill_id,
                skill_version_id=version_id,
                trace_id=candidate.source_trace_ids[0] if candidate.source_trace_ids else None,
                event_type="skill_promoted",
                from_status=None,
                to_status=status,
                reason=request.reason,
                actor_id=request.actor_id,
                payload={"candidate_id": candidate.candidate_id},
                created_at=now,
            )
        )
        self._emit_skill(skill, "skill_promoted", 0.8)
        if status == "active":
            self._record_event(
                SkillActivationEvent(
                    activation_event_id=f"activation-{uuid4().hex}",
                    skill_id=skill_id,
                    skill_version_id=version_id,
                    trace_id=candidate.source_trace_ids[0] if candidate.source_trace_ids else None,
                    event_type="skill_activated",
                    from_status="draft",
                    to_status="active",
                    reason=request.reason,
                    actor_id=request.actor_id,
                    payload={"candidate_id": candidate.candidate_id},
                    created_at=now,
                )
            )
            self._emit_skill(skill, "skill_activated", 1.0)
        return SkillPromotionResponse(
            promoted=True,
            skill_id=skill_id,
            skill_version_id=version_id,
            candidate_id=candidate.candidate_id,
            status=status,
            reason=None,
        )

    def get_skill(self, skill_id: str, scope: list[str]) -> SkillRecord | None:
        """Return a skill by ID after policy and scope checks."""
        decision = self._authorize(
            action_type="skill.read",
            resource_type="skill",
            resource_id=skill_id,
            risk_level="low",
            scope=scope,
            context={},
            approval_present=False,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        skill = _get_skill(self._repository, skill_id)
        if skill is None or not _within_scope(skill.owner_scope, scope):
            return None
        return skill

    def list_skills(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillRecord]:
        """List skills by scope and optional status."""
        decision = self._authorize(
            action_type="skill.read",
            resource_type="skill",
            resource_id=None,
            risk_level="low",
            scope=scope,
            context={"status": status},
            approval_present=False,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        list_skills = getattr(self._repository, "list_skills", None)
        if callable(list_skills):
            result = list_skills(scope=scope, status=status, limit=limit)
            if isinstance(result, list):
                return [item for item in result if isinstance(item, SkillRecord)]
        return []

    def transition_skill(self, request: SkillActivationRequest) -> SkillRecord:
        """Transition a skill status through policy gates."""
        skill = _get_skill(self._repository, request.skill_id)
        if skill is None:
            raise ValueError("skill_not_found")
        if not can_transition_skill(skill.status, request.to_status):
            raise ValueError(f"invalid_skill_transition:{skill.status}->{request.to_status}")
        action_type = _action_for_transition(request.to_status)
        if request.to_status == "active":
            autonomy = self._autonomy_decision(
                action_type=action_type,
                resource_type="skill",
                resource_id=skill.skill_id,
                risk_level=skill.risk_level,
                actor_id=request.actor_id,
                scope=skill.owner_scope,
                metadata=request.metadata,
            )
            if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
                reason = getattr(autonomy, "reason", "autonomy_denied")
                raise ValueError(f"autonomy_denied:{reason}")
        decision = self._authorize(
            action_type=action_type,
            resource_type="skill",
            resource_id=skill.skill_id,
            risk_level=skill.risk_level,
            scope=skill.owner_scope,
            context=request.model_dump(mode="json"),
            approval_present=False,
            actor_id=request.actor_id,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        if request.to_status == "active" and _skill_requires_approval(
            skill.risk_level,
            request.metadata,
        ):
            gate = self._approval_gate_for_transition(skill, request)
            raise ValueError(_approval_reason(gate))
        now = datetime.now(UTC)
        updated = skill.model_copy(
            update={
                "status": request.to_status,
                "metadata": {**skill.metadata, **request.metadata},
                "updated_at": now,
                "activated_at": now if request.to_status == "active" else skill.activated_at,
                "disabled_at": now if request.to_status == "disabled" else skill.disabled_at,
            }
        )
        saved = _save_skill(self._repository, updated)
        event_type = _event_type_for_status(request.to_status)
        self._record_event(
            SkillActivationEvent(
                activation_event_id=f"activation-{uuid4().hex}",
                skill_id=saved.skill_id,
                skill_version_id=None,
                trace_id=None,
                event_type=event_type,
                from_status=skill.status,
                to_status=saved.status,
                reason=request.reason,
                actor_id=request.actor_id,
                payload=request.metadata,
                created_at=now,
            )
        )
        self._emit_skill(saved, event_type, _event_intensity(event_type))
        return saved

    def match_skills(self, request: SkillMatchRequest) -> list[SkillMatchResult]:
        """Match active skills as procedural memory."""
        decision = self._authorize(
            action_type="skill.match",
            resource_type="skill",
            resource_id=None,
            risk_level="low",
            scope=request.scope,
            context=request.model_dump(mode="json"),
            approval_present=False,
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        return self._matcher.match(request)

    def _authorize(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        context: dict[str, Any],
        approval_present: bool,
        actor_id: str | None = None,
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _record_event(self, event: SkillActivationEvent) -> None:
        save_event = getattr(self._repository, "save_activation_event", None)
        if callable(save_event):
            save_event(event)

    def _approval_gate_for_promotion(
        self,
        request: SkillPromotionRequest,
        candidate: SkillCandidate,
    ) -> ApprovalGateResult | None:
        return evaluate_approval_gate(
            self._approval_service,
            trace_id=candidate.source_trace_ids[0] if candidate.source_trace_ids else None,
            actor_id=request.actor_id,
            workspace_id=None,
            action_type="skill.promote",
            resource_type="skill_candidate",
            resource_id=candidate.candidate_id,
            requested_risk_level=candidate.risk_level,
            security_scope=request.owner_scope,
            payload={"candidate_id": candidate.candidate_id, "activate": request.activate},
            context={
                "approval_present": bool(request.metadata.get("approval_present")),
                "affects_skill_activation": True,
            },
            metadata=request.metadata,
        )

    def _approval_gate_for_transition(
        self,
        skill: SkillRecord,
        request: SkillActivationRequest,
    ) -> ApprovalGateResult | None:
        return evaluate_approval_gate(
            self._approval_service,
            trace_id=None,
            actor_id=request.actor_id,
            workspace_id=None,
            action_type="skill.activate",
            resource_type="skill",
            resource_id=skill.skill_id,
            requested_risk_level=skill.risk_level,
            security_scope=skill.owner_scope,
            payload={"skill_id": skill.skill_id},
            context={
                "approval_present": bool(request.metadata.get("approval_present")),
                "affects_skill_activation": True,
            },
            metadata=request.metadata,
        )

    def _autonomy_decision(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str,
        risk_level: str,
        actor_id: str | None,
        scope: list[str],
        metadata: dict[str, Any],
    ) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    actor_id=actor_id,
                    workspace_id=None,
                    requested_mode="dry_run",
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    risk_level=cast(Any, risk_level),
                    approval_present=bool(metadata.get("approval_present")),
                    delegation_id=_metadata_str(metadata, "delegation_id"),
                    context={"security_scope": scope},
                    metadata=metadata,
                )
            ),
        )

    def _emit_candidate(
        self,
        candidate: SkillCandidate,
        event_type: str,
        intensity: float,
    ) -> None:
        _emit(
            self._telemetry_service,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{candidate.candidate_id}-{event_type}",
                trace_id=candidate.source_trace_ids[0]
                if candidate.source_trace_ids
                else candidate.candidate_id,
                event_type=event_type,  # type: ignore[arg-type]
                node_type="candidate",
                node_id=candidate.candidate_id,
                edge_from=candidate.reflection_id,
                edge_to=candidate.candidate_id,
                intensity=intensity,
                payload={"status": candidate.status},
                created_at=datetime.now(UTC),
            ),
        )

    def _emit_skill(self, skill: SkillRecord, event_type: str, intensity: float) -> None:
        _emit(
            self._telemetry_service,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{skill.skill_id}-{event_type}",
                trace_id=skill.skill_id,
                event_type=event_type,  # type: ignore[arg-type]
                node_type="skill",
                node_id=skill.skill_id,
                edge_from=skill.candidate_id,
                edge_to=skill.skill_id,
                intensity=intensity,
                payload={"status": skill.status, "current_version": skill.current_version},
                created_at=datetime.now(UTC),
            ),
        )


def can_transition_skill(from_status: str, to_status: str) -> bool:
    """Return whether a skill status transition is allowed."""
    return to_status in ALLOWED_SKILL_TRANSITIONS.get(from_status, set())


def _skill_requires_approval(risk_level: str, metadata: dict[str, Any]) -> bool:
    if bool(metadata.get("approval_present")):
        return False
    return risk_level in {"high", "critical"}


def _approval_reason(gate: ApprovalGateResult | None) -> str:
    if gate is None:
        return "approval_required"
    if gate.final_decision == "block":
        return gate.reason
    return (
        f"approval_required:{gate.approval_request_id}"
        if gate.approval_request_id
        else "approval_required"
    )


def _promotion_validation_reason(candidate: SkillCandidate) -> str | None:
    if candidate.status not in {"approved", "under_review"}:
        return "candidate_not_reviewable"
    if candidate.confidence < 0.65:
        return "candidate_confidence_below_threshold"
    if not candidate.source_trace_ids and not candidate.source_task_ids:
        return "candidate_missing_source_evidence"
    if not candidate.procedure_steps:
        return "candidate_missing_procedure_steps"
    for step in candidate.procedure_steps:
        if step.action_type not in ACTION_POLICY:
            return "candidate_contains_non_generic_step"
    return None


def _promotion_response(
    request: SkillPromotionRequest,
    promoted: bool,
    reason: str,
) -> SkillPromotionResponse:
    return SkillPromotionResponse(
        promoted=promoted,
        skill_id=None,
        skill_version_id=None,
        candidate_id=request.candidate_id,
        status="rejected",
        reason=reason,
    )


def _action_for_transition(to_status: str) -> str:
    if to_status == "active":
        return "skill.activate"
    if to_status == "disabled":
        return "skill.disable"
    return "skill.archive"


def _event_type_for_status(to_status: str) -> SkillActivationEventType:
    if to_status == "active":
        return "skill_activated"
    if to_status == "disabled":
        return "skill_disabled"
    return "skill_archived"


def _event_intensity(event_type: str) -> float:
    if event_type == "skill_activated":
        return 1.0
    if event_type == "skill_disabled":
        return 0.4
    return 0.2


def _get_reflection(repository: object, reflection_id: str) -> ReflectionRecord | None:
    get_reflection = getattr(repository, "get_reflection", None)
    if callable(get_reflection):
        result = get_reflection(reflection_id)
        if isinstance(result, ReflectionRecord) or result is None:
            return result
    return None


def _get_candidate(repository: object, candidate_id: str) -> SkillCandidate | None:
    get_candidate = getattr(repository, "get_candidate", None)
    if callable(get_candidate):
        result = get_candidate(candidate_id)
        if isinstance(result, SkillCandidate) or result is None:
            return result
    return None


def _save_candidate(repository: object, candidate: SkillCandidate) -> SkillCandidate:
    save_candidate = getattr(repository, "save_candidate", None)
    if callable(save_candidate):
        result = save_candidate(candidate)
        if isinstance(result, SkillCandidate):
            return result
    return candidate


def _get_skill(repository: object, skill_id: str) -> SkillRecord | None:
    get_skill = getattr(repository, "get_skill", None)
    if callable(get_skill):
        result = get_skill(skill_id)
        if isinstance(result, SkillRecord) or result is None:
            return result
    return None


def _save_skill(repository: object, skill: SkillRecord) -> SkillRecord:
    save_skill = getattr(repository, "save_skill", None)
    if callable(save_skill):
        result = save_skill(skill)
        if isinstance(result, SkillRecord):
            return result
    return skill


def _save_version(repository: object, version: SkillVersion) -> SkillVersion:
    save_version = getattr(repository, "save_version", None)
    if callable(save_version):
        result = save_version(version)
        if isinstance(result, SkillVersion):
            return result
    return version


def _within_scope(owner_scope: list[str], scope: list[str]) -> bool:
    return not scope or any(item in owner_scope for item in scope)


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None


def _emit(telemetry_service: object | None, event: VisualTelemetryEvent) -> None:
    if telemetry_service is None:
        return
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
        return
    save = getattr(telemetry_service, "save_visual_telemetry", None)
    if callable(save):
        save(event.trace_id, [event])

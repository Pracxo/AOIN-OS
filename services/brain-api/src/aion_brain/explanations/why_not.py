"""Deterministic why/why-not answer service."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.explanations import WhyNotAnswer, WhyNotRequest
from aion_brain.explanations._shared import (
    authorize,
    clamp,
    emit_explanation_telemetry,
    items_from_source,
    now_utc,
    object_id,
    object_value,
    string_refs,
    unique,
)
from aion_brain.explanations.redaction import sanitize_explanation_payload
from aion_brain.explanations.repository import ExplanationRepository

_NEXT_STEPS = {
    "approval_present": "request_approval",
    "policy_permission": "review_policy",
    "autonomy_mode": "switch_to_dry_run",
    "evidence_grounding": "add_evidence",
    "capability_available": "enable_optional_adapter_through_config",
    "adapter_enabled": "enable_optional_adapter_through_config",
    "runtime_permission": "run_diagnostics",
}


class WhyNotService:
    """Answer why an action did not continue using observable local records."""

    def __init__(
        self,
        explanation_repository: ExplanationRepository,
        policy_adapter: object,
        *,
        policy_service: object | None = None,
        autonomy_service: object | None = None,
        approval_service: object | None = None,
        risk_service: object | None = None,
        capability_awareness_service: object | None = None,
        limitation_service: object | None = None,
        response_service: object | None = None,
        outcome_service: object | None = None,
        telemetry_service: object | None = None,
        audit_ledger: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = explanation_repository
        self._policy_adapter = policy_adapter
        self._policy_service = policy_service
        self._autonomy_service = autonomy_service
        self._approval_service = approval_service
        self._risk_service = risk_service
        self._capability_awareness_service = capability_awareness_service
        self._limitation_service = limitation_service
        self._response_service = response_service
        self._outcome_service = outcome_service
        self._telemetry_service = telemetry_service
        self._audit_ledger = audit_ledger
        self._settings = settings

    def answer(self, request: WhyNotRequest) -> WhyNotAnswer:
        """Build, store, audit, and return a why-not answer."""

        if not bool(getattr(self._settings, "why_not_enabled", True)):
            raise RuntimeError("why_not_disabled")
        authorize(
            self._policy_adapter,
            action_type="explanation.why_not",
            resource_type=request.target_type,
            resource_id=request.target_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            context={"requested_action": request.requested_action},
        )
        blockers = _blockers_for(request, self)
        missing_requirements = _missing_requirements(blockers)
        next_steps = _next_steps(missing_requirements, blockers)
        metadata, redaction = sanitize_explanation_payload(
            {**request.metadata, "redaction_metadata": {}, "owner_scope": request.owner_scope}
        )
        if redaction["redacted"]:
            metadata["redaction_metadata"] = redaction
        answer = WhyNotAnswer(
            why_not_id=request.why_not_id or f"why-not-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            question=request.question,
            target_type=request.target_type,
            target_id=request.target_id,
            requested_action=request.requested_action,
            answer=_answer_text(blockers),
            blockers=blockers,
            missing_requirements=missing_requirements,
            next_possible_steps=next_steps,
            refs=_refs(blockers),
            confidence=_confidence(blockers),
            metadata=metadata,
            created_by=request.created_by,
            created_at=now_utc(),
        )
        stored = self._repository.save_why_not(answer)
        self._audit(request, stored)
        emit_explanation_telemetry(
            self._telemetry_service,
            event_type="why_not_answer_created",
            node_type="why_not",
            node_id=stored.why_not_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            owner_scope=request.owner_scope,
            payload={
                "target_type": stored.target_type,
                "missing_requirements": missing_requirements,
            },
        )
        return stored

    def get(self, why_not_id: str, scope: list[str]) -> WhyNotAnswer | None:
        """Return one why-not answer."""

        authorize(
            self._policy_adapter,
            action_type="explanation.read",
            resource_type="why_not",
            resource_id=why_not_id,
            scope=scope,
        )
        answer = self._repository.get_why_not(why_not_id)
        if answer is None:
            return None
        owner_scope = answer.metadata.get("owner_scope")
        if isinstance(owner_scope, list) and not set(owner_scope) & set(scope):
            return None
        return answer

    def list(
        self,
        trace_id: str | None = None,
        target_type: str | None = None,
        limit: int = 50,
    ) -> list[WhyNotAnswer]:
        """List why-not answers."""

        return self._repository.list_why_not(
            trace_id=trace_id,
            target_type=target_type,
            limit=limit,
        )

    def _audit(self, request: WhyNotRequest, answer: WhyNotAnswer) -> None:
        record_audit_event(
            self._audit_ledger,
            action_type="explanation.why_not",
            resource_type="why_not",
            resource_id=answer.why_not_id,
            event_type="why_not_answer_created",
            outcome="completed",
            source_component="why_not_service",
            trace_id=answer.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            payload={
                "target_type": answer.target_type,
                "target_id": answer.target_id,
                "missing_requirements": answer.missing_requirements,
            },
            metadata={"owner_scope": request.owner_scope},
        )


def _blockers_for(request: WhyNotRequest, service: WhyNotService) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    blockers.extend(_policy_blockers(request, service._policy_service))
    blockers.extend(_approval_blockers(request, service._approval_service))
    blockers.extend(_autonomy_blockers(request, service._autonomy_service))
    blockers.extend(_risk_blockers(request, service._risk_service))
    blockers.extend(_capability_blockers(request, service._capability_awareness_service))
    blockers.extend(_limitation_blockers(request, service._limitation_service))
    blockers.extend(_response_blockers(request, service._response_service))
    blockers.extend(_outcome_blockers(request, service._outcome_service))
    blockers.extend(_metadata_blockers(request.metadata))
    if not blockers:
        blockers.append(
            {
                "type": "insufficient_records",
                "missing_requirement": "ask_clarifying_question",
                "reason": "No blocking record was available for this target.",
                "refs": [],
            }
        )
    return blockers


def _policy_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    decisions = (
        items_from_source(source, ("list_policy_decisions", "list_decisions"), request.trace_id)
        if request.trace_id
        else []
    )
    blockers: list[dict[str, Any]] = []
    for decision in decisions:
        if bool(object_value(decision, "allow", True)):
            continue
        blockers.append(
            {
                "type": "policy_denied",
                "missing_requirement": "policy_permission",
                "reason": str(object_value(decision, "reason", "policy_denied")),
                "refs": [object_id(decision, "decision_id") or ""],
            }
        )
    return blockers


def _approval_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    approval_id = request.metadata.get("approval_request_id")
    approvals = (
        items_from_source(
            source, ("get_request", "get", "get_approval"), approval_id, request.owner_scope
        )
        if approval_id
        else items_from_source(
            source, ("list_pending", "list_requests", "list"), request.owner_scope
        )
    )
    return [
        {
            "type": "approval_required",
            "missing_requirement": "approval_present",
            "reason": "A required approval has not been completed.",
            "refs": [object_id(item, "approval_request_id") or ""],
        }
        for item in approvals
        if str(object_value(item, "status", "pending")) == "pending"
    ]


def _autonomy_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    decisions = items_from_source(
        source, ("list_decisions", "list", "get_decision"), request.trace_id
    )
    blockers = [
        {
            "type": "autonomy_denied",
            "missing_requirement": "autonomy_mode",
            "reason": str(object_value(item, "reason", "autonomy_denied")),
            "refs": [object_id(item, "autonomy_decision_id", "decision_id") or ""],
        }
        for item in decisions
        if object_value(item, "allow", True) is False
    ]
    if request.metadata.get("autonomy_allowed") is False:
        blockers.append(
            {
                "type": "autonomy_denied",
                "missing_requirement": "autonomy_mode",
                "reason": "The current autonomy mode does not allow this action.",
                "refs": string_refs(request.metadata.get("autonomy_decision_id")),
            }
        )
    return blockers


def _risk_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    assessments = items_from_source(
        source, ("list_assessments", "list", "get_assessment"), request.trace_id
    )
    return [
        {
            "type": "risk_blocked",
            "missing_requirement": "lower_risk",
            "reason": "A risk assessment blocked or escalated the action.",
            "refs": [object_id(item, "risk_assessment_id") or ""],
        }
        for item in assessments
        if str(object_value(item, "decision", "")) in {"block", "require_approval"}
    ]


def _capability_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    capability_id = request.metadata.get("capability_id") or request.target_id
    records = (
        items_from_source(
            source,
            ("get_capability", "get", "get_capability_awareness"),
            capability_id,
            request.owner_scope,
        )
        if capability_id
        else []
    )
    blockers = [
        {
            "type": "capability_unavailable",
            "missing_requirement": "capability_available",
            "reason": "The requested capability is unavailable or disabled.",
            "refs": [object_id(item, "awareness_id", "capability_id", "capability_key") or ""],
        }
        for item in records
        if str(object_value(item, "availability", "available")) != "available"
        or str(object_value(item, "status", "active")) != "active"
    ]
    if request.metadata.get("capability_available") is False:
        blockers.append(
            {
                "type": "capability_unavailable",
                "missing_requirement": "capability_available",
                "reason": "The requested capability is unavailable or disabled.",
                "refs": string_refs(request.metadata.get("capability_id")),
            }
        )
    return blockers


def _limitation_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    limitations = items_from_source(source, ("list_limitations", "list"), request.owner_scope)
    return [
        {
            "type": "limitation_active",
            "missing_requirement": "adapter_enabled",
            "reason": str(object_value(item, "title", "An active limitation applies.")),
            "refs": [object_id(item, "limitation_id") or ""],
        }
        for item in limitations
        if str(object_value(item, "status", "")) == "active"
        and str(object_value(item, "severity", "")) in {"high", "critical"}
    ]


def _response_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    response_id = request.metadata.get("response_id") or request.target_id
    response = (
        items_from_source(source, ("get_response", "get"), response_id) if response_id else []
    )
    return [
        {
            "type": "response_ungrounded",
            "missing_requirement": "evidence_grounding",
            "reason": "The response lacks required grounding.",
            "refs": [object_id(item, "response_id") or ""],
        }
        for item in response
        if object_value(item, "grounded", True) is False
    ]


def _outcome_blockers(request: WhyNotRequest, source: object | None) -> list[dict[str, Any]]:
    outcomes = items_from_source(
        source, ("list_outcomes", "list", "query"), scope=request.owner_scope, limit=50
    )
    return [
        {
            "type": "outcome_missing_effects",
            "missing_requirement": "run_diagnostics",
            "reason": "The outcome record reports missing or failed effects.",
            "refs": [object_id(item, "outcome_id") or ""],
        }
        for item in outcomes
        if str(object_value(item, "status", "")) in {"failed", "partial", "contradicted"}
    ]


def _metadata_blockers(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if metadata.get("approval_required") is True:
        blockers.append(
            {
                "type": "approval_required",
                "missing_requirement": "approval_present",
                "reason": "This action requires approval before it can continue.",
                "refs": string_refs(metadata.get("approval_request_id")),
            }
        )
    if metadata.get("missing_evidence") is True:
        blockers.append(
            {
                "type": "missing_evidence",
                "missing_requirement": "evidence_grounding",
                "reason": "Evidence grounding is missing.",
                "refs": string_refs(metadata.get("evidence_refs")),
            }
        )
    return blockers


def _missing_requirements(blockers: list[dict[str, Any]]) -> list[str]:
    return unique(
        [
            str(blocker.get("missing_requirement"))
            for blocker in blockers
            if blocker.get("missing_requirement")
        ]
    )


def _next_steps(missing_requirements: list[str], blockers: list[dict[str, Any]]) -> list[str]:
    steps = [_NEXT_STEPS.get(requirement, requirement) for requirement in missing_requirements]
    if any(blocker.get("type") == "insufficient_records" for blocker in blockers):
        steps.append("ask_clarifying_question")
    steps.extend(["review_policy", "run_diagnostics"] if not steps else [])
    return unique([step for step in steps if step])


def _refs(blockers: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for blocker in blockers:
        refs.extend(string_refs(blocker.get("refs")))
    return unique(refs)


def _confidence(blockers: list[dict[str, Any]]) -> float:
    if any(blocker.get("type") == "insufficient_records" for blocker in blockers):
        return 0.35
    return clamp(0.65 + (0.05 * min(len(_refs(blockers)), 4)))


def _answer_text(blockers: list[dict[str, Any]]) -> str:
    if any(blocker.get("type") == "policy_denied" for blocker in blockers):
        return "The action did not continue because policy denied it."
    if any(blocker.get("type") == "approval_required" for blocker in blockers):
        return "The action did not continue because approval is required."
    if any(blocker.get("type") == "autonomy_denied" for blocker in blockers):
        return "The action did not continue because the current autonomy mode does not allow it."
    if any(blocker.get("type") == "capability_unavailable" for blocker in blockers):
        return "The action did not continue because the capability is unavailable."
    if any(blocker.get("type") == "missing_evidence" for blocker in blockers):
        return "The action did not continue because evidence grounding is missing."
    return "AION found limited records and cannot identify a single blocker."


__all__ = ["WhyNotService"]

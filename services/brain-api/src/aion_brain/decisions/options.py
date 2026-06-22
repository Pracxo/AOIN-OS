"""Decision option service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.decisions import (
    DecisionOption,
    DecisionOptionCreateRequest,
    DecisionOptionType,
)
from aion_brain.contracts.effects import ExpectedEffectCreateRequest
from aion_brain.decisions._shared import authorize, emit_telemetry, provenance_optional
from aion_brain.decisions.repository import DecisionRepository


class DecisionOptionService:
    """Manage candidate options without executing them."""

    def __init__(
        self,
        repository: DecisionRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        provenance_service: object | None = None,
        expected_effect_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._provenance_service = provenance_service
        self._expected_effect_service = expected_effect_service

    def create_option(self, request: DecisionOptionCreateRequest) -> DecisionOption:
        frame = self._repository.get_frame(request.decision_frame_id)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        authorize(
            self._policy_adapter,
            action_type="decision.option.create",
            resource_type="decision_option",
            resource_id=request.decision_option_id,
            scope=frame.owner_scope,
            trace_id=frame.trace_id,
            actor_id=frame.actor_id,
            workspace_id=frame.workspace_id,
            risk_level=request.risk_level,
            context={"option_type": request.option_type},
        )
        now = datetime.now(UTC)
        option = DecisionOption(
            decision_option_id=request.decision_option_id or f"decision-option-{uuid4().hex}",
            decision_frame_id=request.decision_frame_id,
            option_type=request.option_type,
            status="proposed",
            title=request.title,
            description=request.description,
            action_type=request.action_type,
            target_type=request.target_type,
            target_id=request.target_id,
            expected_effects=request.expected_effects,
            required_permissions=request.required_permissions,
            required_approvals=request.required_approvals,
            risk_level=request.risk_level,
            reversibility=request.reversibility,
            cost_estimate=request.cost_estimate,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_option(option)
        provenance_optional(
            self._provenance_service,
            stored.decision_option_id,
            stored.decision_frame_id,
            "option_for_frame",
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="decision_option_created",
            node_type="decision_option",
            node_id=stored.decision_option_id,
            intensity=0.5,
            trace_id=frame.trace_id,
            edge_from=frame.decision_frame_id,
            edge_to=stored.decision_option_id,
            payload={"owner_scope": frame.owner_scope, "option_type": stored.option_type},
        )
        if request.metadata.get("create_expected_effects") is True:
            self._create_expected_effects(stored, frame.owner_scope, frame.trace_id)
        return stored

    def list_options(
        self,
        decision_frame_id: str,
        status: str | None = None,
    ) -> list[DecisionOption]:
        return self._repository.list_options(decision_frame_id, status=status)

    def archive_option(
        self,
        decision_option_id: str,
        actor_id: str | None,
        reason: str,
    ) -> DecisionOption:
        option = self._repository.get_option(decision_option_id)
        if option is None:
            raise ValueError("decision_option_not_found")
        frame = self._repository.get_frame(option.decision_frame_id)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        authorize(
            self._policy_adapter,
            action_type="decision.option.update",
            resource_type="decision_option",
            resource_id=decision_option_id,
            scope=frame.owner_scope,
            actor_id=actor_id,
            trace_id=frame.trace_id,
            context={"reason": reason},
        )
        archived = option.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**option.metadata, "archive_reason": reason},
            }
        )
        return self._repository.save_option(archived)

    def propose_default_options(self, decision_frame_id: str) -> list[DecisionOption]:
        frame = self._repository.get_frame(decision_frame_id)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        proposals: list[DecisionOptionCreateRequest] = []
        constraints = set(frame.constraints)
        if "unclear_goal" in constraints:
            proposals.append(_proposal(frame.decision_frame_id, "clarify", "Clarify the goal."))
        if not frame.evidence_refs and not frame.memory_refs:
            proposals.append(
                _proposal(
                    frame.decision_frame_id,
                    "retrieve_more_context",
                    "Retrieve more context before choosing.",
                    action_type="memory.retrieve",
                    risk_level="low",
                    reversibility="reversible",
                )
            )
        if frame.goal_refs or frame.task_refs:
            proposals.append(
                _proposal(
                    frame.decision_frame_id,
                    "create_plan",
                    "Create a generic plan from the available context.",
                    action_type="plan.create",
                    risk_level="medium",
                )
            )
        if any(item.startswith("action_type:") for item in frame.constraints):
            proposals.append(
                _proposal(
                    frame.decision_frame_id,
                    "dry_run",
                    "Run a dry-run projection before any controlled action.",
                    action_type="decision.counterfactual.run",
                    risk_level="medium",
                )
            )
        if "high_risk" in constraints or "critical_risk" in constraints:
            proposals.append(
                _proposal(
                    frame.decision_frame_id,
                    "request_approval",
                    "Request approval before proceeding.",
                    risk_level="high",
                    reversibility="reversible",
                )
            )
        if "high_uncertainty" in constraints:
            proposals.append(
                _proposal(frame.decision_frame_id, "defer", "Defer until uncertainty drops.")
            )
        if "policy_blocked" in constraints or "autonomy_blocked" in constraints:
            proposals.append(_proposal(frame.decision_frame_id, "no_op", "Take no action."))
        if not proposals:
            proposals.append(
                _proposal(frame.decision_frame_id, "observe", "Observe and preserve context.")
            )
        return [self.create_option(request) for request in proposals]

    def _create_expected_effects(
        self,
        option: DecisionOption,
        owner_scope: list[str],
        trace_id: str | None,
    ) -> None:
        create = getattr(self._expected_effect_service, "create_expected_effect", None)
        if not callable(create):
            return
        for raw in option.expected_effects:
            if not isinstance(raw, dict):
                continue
            create(
                ExpectedEffectCreateRequest(
                    expected_effect_id=_str_or_none(raw.get("expected_effect_id")),
                    trace_id=_str_or_none(raw.get("trace_id")) or trace_id,
                    source_type="decision_option",
                    source_id=option.decision_option_id,
                    effect_type=cast(Any, raw.get("effect_type", "generic")),
                    subject_ref=_str_or_none(raw.get("subject_ref")),
                    predicate=str(raw.get("predicate") or "effect_expected"),
                    object_ref=_str_or_none(raw.get("object_ref")),
                    expected_value=_dict_or_empty(raw.get("expected_value")),
                    success_criteria=_dict_or_empty(raw.get("success_criteria")),
                    required=bool(raw.get("required", True)),
                    confidence=float(raw.get("confidence", 0.5)),
                    owner_scope=owner_scope,
                    evidence_refs=_list_of_str(raw.get("evidence_refs")),
                    metadata={
                        **_dict_or_empty(raw.get("metadata")),
                        "source": "decision_option",
                        "created_from_decision_metadata": True,
                    },
                )
            )


def _proposal(
    decision_frame_id: str,
    option_type: str,
    description: str,
    *,
    action_type: str | None = None,
    risk_level: str = "low",
    reversibility: str = "unknown",
) -> DecisionOptionCreateRequest:
    return DecisionOptionCreateRequest(
        decision_frame_id=decision_frame_id,
        option_type=cast(DecisionOptionType, option_type),
        title=option_type.replace("_", " ").title(),
        description=description,
        action_type=action_type,
        risk_level=cast(Any, risk_level),
        reversibility=cast(Any, reversibility),
        metadata={"proposed_by": "deterministic_decision_option_service"},
    )


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _dict_or_empty(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_of_str(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []

"""Decision journal service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import ActionProposalCreateRequest
from aion_brain.contracts.decisions import DecisionRecord, DecisionRecordRequest
from aion_brain.decisions._shared import (
    audit_optional,
    authorize,
    emit_telemetry,
    provenance_optional,
    scope_matches,
)
from aion_brain.decisions.repository import DecisionRepository


class DecisionJournalService:
    """Record decisions without executing selected options."""

    def __init__(
        self,
        repository: DecisionRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        action_proposal_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._action_proposal_service = action_proposal_service

    def set_action_proposal_service(self, service: object | None) -> None:
        """Attach the optional action proposal broker after kernel assembly."""

        self._action_proposal_service = service

    def record_decision(self, request: DecisionRecordRequest) -> DecisionRecord:
        frame = self._repository.get_frame(request.decision_frame_id)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        option = (
            self._repository.get_option(request.selected_option_id)
            if request.selected_option_id
            else None
        )
        authorize(
            self._policy_adapter,
            action_type="decision.record.create",
            resource_type="decision_record",
            resource_id=request.decision_record_id,
            scope=frame.owner_scope,
            trace_id=request.trace_id or frame.trace_id,
            actor_id=request.actor_id or frame.actor_id,
            workspace_id=request.workspace_id or frame.workspace_id,
            risk_level=option.risk_level if option else "low",
            approval_present=request.approval_present,
            context={"decision_type": request.decision_type, "no_execution": True},
        )
        metadata = {**request.metadata, "selected_option_not_executed": True}
        approval_request_id = None
        if option and option.risk_level in {"high", "critical"} and not request.approval_present:
            metadata["approval_required"] = True
            approval_request_id = "approval_required"
        record = DecisionRecord(
            decision_record_id=request.decision_record_id or f"decision-record-{uuid4().hex}",
            decision_frame_id=request.decision_frame_id,
            selected_option_id=request.selected_option_id,
            trace_id=request.trace_id or frame.trace_id,
            actor_id=request.actor_id or frame.actor_id,
            workspace_id=request.workspace_id or frame.workspace_id,
            status="recorded",
            decision_type=request.decision_type,
            rationale=request.rationale,
            evaluation_refs=request.evaluation_refs,
            counterfactual_refs=request.counterfactual_refs,
            approval_request_id=approval_request_id,
            metadata=metadata,
            created_by=request.created_by,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_record(record)
        audit_optional(
            self._audit_sink,
            "decision_recorded",
            {"decision_record_id": stored.decision_record_id, "no_execution": True},
        )
        if stored.selected_option_id:
            provenance_optional(
                self._provenance_service,
                stored.decision_record_id,
                stored.selected_option_id,
                "records_selected_option",
            )
        if option is not None and option.metadata.get("create_action_proposal") is True:
            create_proposal = getattr(self._action_proposal_service, "create_proposal", None)
            if callable(create_proposal):
                create_proposal(
                    ActionProposalCreateRequest(
                        trace_id=stored.trace_id,
                        actor_id=stored.actor_id,
                        workspace_id=stored.workspace_id,
                        source_type="decision",
                        source_id=stored.decision_record_id,
                        proposal_type="generic",
                        title=option.title,
                        description=option.description,
                        action_type=option.action_type or "generic",
                        target_type=option.target_type or "noop",
                        target_id=option.target_id,
                        owner_scope=frame.owner_scope,
                        proposed_payload={"decision_option_id": option.decision_option_id},
                        required_permissions=option.required_permissions,
                        required_approvals=option.required_approvals,
                        risk_level=option.risk_level,
                        decision_refs=[stored.decision_record_id],
                        metadata={"source": "decision_journal", "no_execution": True},
                        created_by=stored.created_by,
                    )
                )
        emit_telemetry(
            self._telemetry_service,
            event_type="decision_recorded",
            node_type="decision",
            node_id=stored.decision_record_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={"owner_scope": frame.owner_scope, "no_execution": True},
        )
        return stored

    def get_record(self, decision_record_id: str, scope: list[str]) -> DecisionRecord | None:
        authorize(
            self._policy_adapter,
            action_type="decision.record.read",
            resource_type="decision_record",
            resource_id=decision_record_id,
            scope=scope,
        )
        record = self._repository.get_record(decision_record_id)
        if record is None:
            return None
        frame = self._repository.get_frame(record.decision_frame_id)
        if frame is not None and not scope_matches(frame.owner_scope, scope):
            return None
        return record

    def list_records(
        self,
        scope: list[str],
        decision_frame_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[DecisionRecord]:
        authorize(
            self._policy_adapter,
            action_type="decision.record.read",
            resource_type="decision_record",
            resource_id=None,
            scope=scope,
        )
        return self._repository.list_records(
            scope=scope,
            decision_frame_id=decision_frame_id,
            status=status,
            limit=limit,
        )

    def supersede_record(
        self,
        decision_record_id: str,
        actor_id: str | None,
        reason: str,
        scope: list[str],
    ) -> DecisionRecord:
        record = self.get_record(decision_record_id, scope)
        if record is None:
            raise ValueError("decision_record_not_found")
        authorize(
            self._policy_adapter,
            action_type="decision.record.update",
            resource_type="decision_record",
            resource_id=decision_record_id,
            scope=scope,
            actor_id=actor_id,
            context={"reason": reason},
        )
        superseded = record.model_copy(
            update={
                "status": "superseded",
                "superseded_at": datetime.now(UTC),
                "metadata": {**record.metadata, "supersede_reason": reason},
            }
        )
        stored = self._repository.save_record(superseded)
        emit_telemetry(
            self._telemetry_service,
            event_type="decision_superseded",
            node_type="decision",
            node_id=stored.decision_record_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"owner_scope": scope, "reason": reason},
        )
        return stored

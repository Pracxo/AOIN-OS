"""Action proposal service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.action_proposals.redaction import redact_action_payload
from aion_brain.contracts.action_proposals import (
    ActionBlocker,
    ActionProposal,
    ActionProposalCreateRequest,
    ActionProposalQuery,
    ActionProposalQueryResult,
    ActionProposalType,
)
from aion_brain.contracts.model_outputs import ToolIntentCandidate
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ActionProposalService:
    """Create and manage action proposals without executing them."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        blocker_service: object | None = None,
        tool_intent_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._blocker_service = blocker_service
        self._tool_intent_repository = tool_intent_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ActionProposalService:
        return ActionProposalService(
            self._repository,
            self._policy_adapter,
            blocker_service=self._blocker_service,
            tool_intent_repository=self._tool_intent_repository,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_proposal(self, request: ActionProposalCreateRequest) -> ActionProposal:
        """Create a proposal record. This never creates a command or run."""

        if self._settings is not None and not bool(
            getattr(self._settings, "action_proposals_enabled", True)
        ):
            raise RuntimeError("action_proposals_disabled")
        authorize(
            self._policy_adapter,
            action_type="action_proposal.create",
            resource_type="action_proposal",
            resource_id=request.action_proposal_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=request.risk_level,
        )
        redacted_payload, findings = redact_action_payload(request.proposed_payload)
        now = datetime.now(UTC)
        proposal = ActionProposal(
            action_proposal_id=request.action_proposal_id or f"action-proposal-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            status="proposed",
            proposal_type=request.proposal_type,
            title=request.title,
            description=request.description,
            action_type=request.action_type,
            target_type=request.target_type,
            target_id=request.target_id,
            owner_scope=request.owner_scope,
            proposed_payload=redacted_payload,
            required_permissions=request.required_permissions,
            required_approvals=request.required_approvals,
            risk_level=request.risk_level,
            autonomy_mode_required=request.autonomy_mode_required,
            sandbox_profile_id=request.sandbox_profile_id,
            capability_refs=request.capability_refs,
            evidence_refs=request.evidence_refs,
            decision_refs=request.decision_refs,
            model_output_refs=request.model_output_refs,
            tool_intent_refs=request.tool_intent_refs,
            blocker_refs=[],
            metadata={
                **request.metadata,
                "redaction_findings": findings,
                "no_execution": True,
            },
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        blockers = self._preliminary_blockers(proposal)
        if blockers:
            proposal = proposal.model_copy(
                update={
                    "status": "blocked",
                    "blocker_refs": [blocker.action_blocker_id for blocker in blockers],
                }
            )
        stored = _save_proposal(self._repository, proposal)
        self._record_audit("action_proposal_created", stored.action_proposal_id)
        self._record_provenance(stored.source_id, stored.action_proposal_id, "proposes_action")
        emit_telemetry(
            self._telemetry_service,
            event_type="action_proposal_created",
            node_type="action_proposal",
            node_id=stored.action_proposal_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "proposal_type": stored.proposal_type},
        )
        if stored.status == "blocked":
            emit_telemetry(
                self._telemetry_service,
                event_type="action_proposal_blocked",
                node_type="action_proposal",
                node_id=stored.action_proposal_id,
                intensity=1.0,
                trace_id=stored.trace_id,
                payload={"blocker_refs": stored.blocker_refs},
            )
        return stored

    def get_proposal(self, action_proposal_id: str, scope: list[str]) -> ActionProposal | None:
        authorize(
            self._policy_adapter,
            action_type="action_proposal.read",
            resource_type="action_proposal",
            resource_id=action_proposal_id,
            scope=scope,
            risk_level="low",
        )
        proposal = _get_proposal(self._repository, action_proposal_id)
        if proposal is None or not _scope_matches(proposal.owner_scope, scope):
            return None
        return proposal

    def query(self, query: ActionProposalQuery) -> ActionProposalQueryResult:
        authorize(
            self._policy_adapter,
            action_type="action_proposal.read",
            resource_type="action_proposal",
            resource_id=query.trace_id,
            scope=query.scope,
            trace_id=query.trace_id,
            risk_level="low",
        )
        run_query = getattr(self._repository, "query", None)
        if not callable(run_query):
            return ActionProposalQueryResult(total_count=0)
        result = run_query(query)
        return (
            result
            if isinstance(result, ActionProposalQueryResult)
            else ActionProposalQueryResult(total_count=0)
        )

    def archive_proposal(
        self, action_proposal_id: str, actor_id: str | None, reason: str
    ) -> ActionProposal:
        proposal = _require_proposal(self._repository, action_proposal_id)
        authorize(
            self._policy_adapter,
            action_type="action_proposal.update",
            resource_type="action_proposal",
            resource_id=action_proposal_id,
            scope=proposal.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        archived = proposal.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**proposal.metadata, "archive_reason": reason},
            }
        )
        return _save_proposal(self._repository, archived)

    def soft_delete_proposal(
        self, action_proposal_id: str, actor_id: str | None, reason: str
    ) -> bool:
        proposal = _require_proposal(self._repository, action_proposal_id)
        authorize(
            self._policy_adapter,
            action_type="action_proposal.delete",
            resource_type="action_proposal",
            resource_id=action_proposal_id,
            scope=proposal.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        deleted = proposal.model_copy(
            update={
                "status": "archived",
                "deleted_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**proposal.metadata, "delete_reason": reason},
            }
        )
        _save_proposal(self._repository, deleted)
        return True

    def build_from_tool_intent(
        self,
        tool_intent_id: str,
        owner_scope: list[str],
        created_by: str | None = None,
    ) -> ActionProposal:
        """Build a proposal from a captured tool intent without executing it."""

        get_intent = getattr(self._tool_intent_repository, "get_tool_intent", None)
        intent = get_intent(tool_intent_id) if callable(get_intent) else None
        if not isinstance(intent, ToolIntentCandidate):
            raise ValueError("tool_intent_not_found")
        return self.create_proposal(
            ActionProposalCreateRequest(
                trace_id=intent.trace_id,
                source_type="tool_intent",
                source_id=intent.tool_intent_id,
                proposal_type=_proposal_type_for_intent(intent),
                title=f"Review {intent.intent_type} intent",
                description="Action proposal created from a reviewed tool intent.",
                action_type=intent.action_type or "generic",
                target_type=intent.target_type or intent.intent_type,
                target_id=intent.target_id,
                owner_scope=owner_scope,
                proposed_payload=intent.arguments_redacted,
                required_permissions=[],
                required_approvals=[],
                risk_level=intent.risk_level,
                model_output_refs=[intent.model_output_id] if intent.model_output_id else [],
                tool_intent_refs=[intent.tool_intent_id],
                metadata={"source": "tool_intent_review"},
                created_by=created_by,
            )
        )

    def _preliminary_blockers(self, proposal: ActionProposal) -> list[ActionBlocker]:
        blockers: list[ActionBlocker] = []
        external_enabled = bool(
            getattr(self._settings, "action_proposal_external_targets_enabled", False)
        )
        if not external_enabled and _looks_external(proposal):
            blocker = self._create_blocker(
                proposal,
                blocker_type="external_action_blocked",
                severity="high",
                reason="external_targets_disabled",
            )
            if isinstance(blocker, ActionBlocker):
                blockers.append(blocker)
        if proposal.source_type == "tool_intent" and not bool(
            getattr(self._settings, "tool_intent_execution_enabled", False)
        ):
            blocker = self._create_blocker(
                proposal,
                blocker_type="tool_execution_disabled",
                severity="high",
                reason="tool_intent_execution_disabled",
            )
            if isinstance(blocker, ActionBlocker):
                blockers.append(blocker)
        return blockers

    def _create_blocker(
        self,
        proposal: ActionProposal,
        *,
        blocker_type: str,
        severity: str,
        reason: str,
    ) -> object:
        create = getattr(self._blocker_service, "create_blocker", None)
        if not callable(create):
            return object()
        return create(
            action_proposal_id=proposal.action_proposal_id,
            trace_id=proposal.trace_id,
            blocker_type=blocker_type,
            severity=severity,
            reason=reason,
            source_type=proposal.source_type,
            source_id=proposal.source_id,
            metadata={"target_type": proposal.target_type},
        )

    def _record_audit(self, event_type: str, action_proposal_id: str) -> None:
        record = getattr(self._audit_sink, "record_event", None)
        if callable(record):
            try:
                record({"event_type": event_type, "action_proposal_id": action_proposal_id})
            except Exception:
                return

    def _record_provenance(self, source_id: str, target_id: str, relation_type: str) -> None:
        link = getattr(self._provenance_service, "record_link", None)
        if callable(link):
            try:
                link(source_id, target_id, relation_type)
            except Exception:
                return


def _proposal_type_for_intent(intent: ToolIntentCandidate) -> ActionProposalType:
    mapping: dict[str, ActionProposalType] = {
        "command_dispatch": "command",
        "workflow_run": "workflow",
        "capability_invoke": "capability",
        "mcp_tool": "mcp_tool",
        "memory_write": "memory_governance",
    }
    return mapping.get(intent.intent_type, "generic")


def _looks_external(proposal: ActionProposal) -> bool:
    values = {
        proposal.target_type.lower(),
        str(proposal.proposed_payload.get("target_system", "")).lower(),
        str(proposal.proposed_payload.get("target_type", "")).lower(),
    }
    return bool(values.intersection({"external", "external_system", "provider", "webhook"}))


def _save_proposal(repository: object, proposal: ActionProposal) -> ActionProposal:
    save = getattr(repository, "save_proposal", None)
    stored = save(proposal) if callable(save) else proposal
    return stored if isinstance(stored, ActionProposal) else proposal


def _get_proposal(repository: object, action_proposal_id: str) -> ActionProposal | None:
    get = getattr(repository, "get_proposal", None)
    proposal = get(action_proposal_id) if callable(get) else None
    return proposal if isinstance(proposal, ActionProposal) else None


def _require_proposal(repository: object, action_proposal_id: str) -> ActionProposal:
    proposal = _get_proposal(repository, action_proposal_id)
    if proposal is None:
        raise ValueError("action_proposal_not_found")
    return proposal


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["ActionProposalService"]

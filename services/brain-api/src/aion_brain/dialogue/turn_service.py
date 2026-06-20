"""Dialogue turn orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.attention import AttentionSignalCreateRequest
from aion_brain.contracts.audit_integrity import ProvenanceLink
from aion_brain.contracts.autonomy import AutonomyDecision, AutonomyDecisionRequest
from aion_brain.contracts.beliefs import ClaimExtractionRequest
from aion_brain.contracts.dialogue import (
    ClarificationRequest,
    DialogueMessage,
    DialogueMessageCreateRequest,
    DialogueSession,
    DialogueSessionCreateRequest,
    DialogueTurnRequest,
    DialogueTurnResult,
)
from aion_brain.contracts.entities import EntityResolutionRequest
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.explanations import ExplanationRequest, WhyNotRequest
from aion_brain.contracts.responses import ResponseComposeRequest, ResponseDraft
from aion_brain.contracts.self_model import SelfDescriptionRequest
from aion_brain.contracts.situations import ContextContinuityRequest
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.contracts.working_memory import WorkingMemoryWriteRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.clarification import ClarificationManager
from aion_brain.dialogue.memory_handoff import DialogueMemoryHandoffService
from aion_brain.dialogue.message_service import DialogueMessageService
from aion_brain.dialogue.session_service import DialogueSessionService
from aion_brain.responses.composer import ResponseComposer
from aion_brain.responses.delivery import ResponseDeliveryService
from aion_brain.responses.verifier import ResponseVerifier

_BOUNDED_MODES = {"observe", "assist", "plan_only", "dry_run"}


class DialogueTurnService:
    """Run one safe backend dialogue turn."""

    def __init__(
        self,
        *,
        session_service: DialogueSessionService,
        message_service: DialogueMessageService,
        clarification_manager: ClarificationManager,
        response_composer: ResponseComposer,
        response_verifier: ResponseVerifier,
        response_delivery: ResponseDeliveryService,
        brain_loop: object | None,
        attention_controller: object | None,
        working_memory_service: object | None,
        memory_handoff_service: DialogueMemoryHandoffService,
        policy_adapter: object,
        autonomy_governor: object | None,
        audit_ledger: object | None,
        provenance_service: object | None,
        telemetry_service: object | None,
        settings: object | None,
        claim_extractor: object | None = None,
        belief_service: object | None = None,
        entity_resolver: object | None = None,
        context_continuity_service: object | None = None,
        self_description_service: object | None = None,
        explanation_builder: object | None = None,
        why_not_service: object | None = None,
    ) -> None:
        self._session_service = session_service
        self._message_service = message_service
        self._clarification_manager = clarification_manager
        self._response_composer = response_composer
        self._response_verifier = response_verifier
        self._response_delivery = response_delivery
        self._brain_loop = brain_loop
        self._attention_controller = attention_controller
        self._working_memory_service = working_memory_service
        self._memory_handoff_service = memory_handoff_service
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._audit_ledger = audit_ledger
        self._provenance_service = provenance_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._claim_extractor = claim_extractor
        self._belief_service = belief_service
        self._entity_resolver = entity_resolver
        self._context_continuity_service = context_continuity_service
        self._self_description_service = self_description_service
        self._explanation_builder = explanation_builder
        self._why_not_service = why_not_service

    def turn(self, request: DialogueTurnRequest) -> DialogueTurnResult:
        """Run one bounded dialogue turn."""

        if not bool(getattr(self._settings, "dialogue_enabled", True)):
            raise RuntimeError("dialogue_disabled")
        if request.mode not in _BOUNDED_MODES:
            raise ValueError("controlled dialogue mode is not supported in v0.1")
        trace_id = request.metadata.get("trace_id")
        trace_id = str(trace_id) if isinstance(trace_id, str) else f"trace-{uuid4().hex}"
        authorize(
            self._policy_adapter,
            action_type="dialogue.turn",
            resource_type="dialogue",
            resource_id=request.dialogue_session_id,
            scope=request.owner_scope,
            trace_id=trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="medium",
            context={"mode": request.mode},
        )
        autonomy = self._autonomy_decision(request, trace_id)
        session = self._session(request, trace_id)
        emit_telemetry(
            self._telemetry_service,
            event_type="dialogue_turn_started",
            node_type="dialogue",
            node_id=session.dialogue_session_id,
            intensity=0.6,
            trace_id=trace_id,
            payload={"owner_scope": session.owner_scope, "mode": request.mode},
        )
        user_message = self._message_service.create_message(
            DialogueMessageCreateRequest(
                dialogue_session_id=session.dialogue_session_id,
                trace_id=trace_id,
                actor_id=request.actor_id or session.actor_id,
                workspace_id=request.workspace_id or session.workspace_id,
                role="user",
                message_type="text",
                content=request.message,
                metadata=request.metadata,
            )
        )
        self._attention(user_message, session)
        self._working_memory(user_message, session)
        extracted_claim_ids = self._extract_claims_if_requested(request, session, user_message)
        entity_resolution_run_ids = self._resolve_entities_if_requested(
            request,
            session,
            user_message,
        )
        constraints: list[str] = []
        trace: DecisionTrace | None = None
        clarification: ClarificationRequest | None = None
        if autonomy is not None and not autonomy.allow:
            constraints.extend(autonomy.constraints or [autonomy.reason, "autonomy_denied"])
        elif request.use_brain_loop:
            trace = self._run_brain_loop(request, session, user_message, trace_id)
            if trace is not None:
                constraints.extend(str(item) for item in trace.outcome.get("constraints", []) or [])
                if _requires_clarification(trace):
                    clarification = self._clarification_manager.create_clarification(
                        session.dialogue_session_id,
                        user_message.message_id,
                        trace.trace_id,
                        _clarification_question(trace),
                        "brain_loop_requires_clarification",
                        True,
                        {"source": "dialogue_turn"},
                    )
        response = self._compose(
            request,
            session,
            user_message,
            trace,
            clarification,
            constraints,
        )
        verification = self._response_verifier.verify(response.response_id)
        self._response_delivery.deliver_api_return(
            response.response_id,
            session.dialogue_session_id,
            trace.trace_id if trace is not None else trace_id,
        )
        if request.metadata.get("remember") is True:
            self._memory_handoff_service.remember_message_summary(
                user_message.message_id,
                session.owner_scope,
                approval_present=bool(request.metadata.get("approval_present", False)),
            )
        self._record_continuity(request, session, user_message, trace_id)
        self._audit_turn(session, user_message, response, verification.status)
        self._provenance(session, user_message, response, trace)
        emit_telemetry(
            self._telemetry_service,
            event_type="dialogue_turn_completed",
            node_type="dialogue",
            node_id=session.dialogue_session_id,
            intensity=0.7,
            trace_id=trace.trace_id if trace is not None else trace_id,
            edge_from=user_message.message_id,
            edge_to=response.response_id,
            payload={"owner_scope": session.owner_scope, "response_id": response.response_id},
        )
        return DialogueTurnResult(
            dialogue_session=session,
            user_message=user_message,
            response=self._response_composer.get_response(response.response_id) or response,
            clarification=clarification,
            trace_id=trace.trace_id if trace is not None else trace_id,
            attention_decision_id=None,
            reasoning_id=trace.reasoning_refs[0] if trace and trace.reasoning_refs else None,
            plan_id=trace.plan_id if trace is not None else None,
            constraints=constraints,
            metadata={
                "mode": request.mode,
                "verification_status": verification.status,
                "external_delivery": False,
                "extracted_claim_ids": extracted_claim_ids,
                "entity_resolution_run_ids": entity_resolution_run_ids,
            },
            created_at=datetime.now(UTC),
        )

    def _record_continuity(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
        trace_id: str,
    ) -> None:
        if request.metadata.get("record_continuity") is not True:
            return
        record = getattr(self._context_continuity_service, "record", None)
        if not callable(record):
            return
        refs = request.metadata.get("continuity_refs")
        try:
            record(
                ContextContinuityRequest(
                    trace_id=trace_id,
                    actor_id=message.actor_id,
                    workspace_id=message.workspace_id,
                    dialogue_session_id=session.dialogue_session_id,
                    situation_id=str(request.metadata.get("situation_id"))
                    if request.metadata.get("situation_id")
                    else None,
                    continuity_type="dialogue_turn",
                    refs=[str(item) for item in refs] if isinstance(refs, list) else [],
                    reason="Dialogue turn continuity recorded.",
                    owner_scope=session.owner_scope,
                    metadata={"message_id": message.message_id},
                )
            )
        except Exception:
            return

    def _resolve_entities_if_requested(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
    ) -> list[str]:
        explicit = request.metadata.get("extract_entities") is True
        enabled = bool(getattr(self._settings, "entity_auto_extract_from_dialogue", False))
        if not explicit and not enabled:
            return []
        resolve = getattr(self._entity_resolver, "resolve", None)
        if not callable(resolve):
            return []
        try:
            result = resolve(
                EntityResolutionRequest(
                    trace_id=message.trace_id,
                    actor_id=message.actor_id,
                    workspace_id=message.workspace_id,
                    owner_scope=session.owner_scope,
                    source_type="dialogue_message",
                    source_id=message.message_id,
                    text=message.content,
                    create_missing_entities=bool(
                        request.metadata.get("create_missing_entities", False)
                    ),
                    dry_run=bool(request.metadata.get("entity_resolution_dry_run", False)),
                    metadata={"dialogue_session_id": session.dialogue_session_id},
                    created_by=message.actor_id,
                )
            )
            return [str(result.resolution_run_id)]
        except Exception:
            return []

    def _extract_claims_if_requested(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
    ) -> list[str]:
        explicit = request.metadata.get("extract_claims") is True
        enabled = bool(getattr(self._settings, "belief_auto_extract_from_dialogue", False))
        if not explicit and not enabled:
            return []
        extract = getattr(self._claim_extractor, "extract", None)
        create_claim = getattr(self._belief_service, "create_claim", None)
        if not callable(extract) or not callable(create_claim):
            return []
        try:
            result = extract(
                ClaimExtractionRequest(
                    source_type="user_message",
                    source_id=message.message_id,
                    text=message.content,
                    trace_id=message.trace_id,
                    owner_scope=session.owner_scope,
                    max_claims=int(request.metadata.get("max_claims", 10)),
                    metadata={"dialogue_session_id": session.dialogue_session_id},
                )
            )
            claim_ids: list[str] = []
            for claim_request in result.extracted_claims:
                claim = create_claim(
                    claim_request.model_copy(
                        update={
                            "actor_id": message.actor_id,
                            "workspace_id": message.workspace_id,
                        }
                    )
                )
                claim_ids.append(str(claim.claim_id))
                emit_telemetry(
                    self._telemetry_service,
                    event_type="belief_claim_extracted",
                    node_type="claim",
                    node_id=str(claim.claim_id),
                    intensity=float(getattr(claim, "confidence", 0.5)),
                    trace_id=message.trace_id,
                    edge_from=message.message_id,
                    edge_to=str(claim.claim_id),
                    payload={"source_type": "user_message"},
                )
            return claim_ids
        except Exception:
            return []

    def _session(self, request: DialogueTurnRequest, trace_id: str) -> DialogueSession:
        if request.dialogue_session_id is not None:
            existing = self._session_service.get_session(
                request.dialogue_session_id,
                request.owner_scope,
            )
            if existing is not None:
                return existing
            if not request.create_session:
                raise ValueError("dialogue_session_not_found")
        return self._session_service.create_session(
            DialogueSessionCreateRequest(
                dialogue_session_id=request.dialogue_session_id,
                trace_id=trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                session_type="general",
                title=request.session_title or "Dialogue Session",
                owner_scope=request.owner_scope,
                metadata={"source": "dialogue_turn"},
                created_by=request.actor_id,
            )
        )

    def _autonomy_decision(
        self,
        request: DialogueTurnRequest,
        trace_id: str,
    ) -> AutonomyDecision | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        try:
            result = decide(
                AutonomyDecisionRequest(
                    trace_id=trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode=cast(Any, request.mode),
                    action_type="dialogue.turn",
                    resource_type="dialogue",
                    resource_id=request.dialogue_session_id,
                    risk_level="low",
                    approval_present=bool(request.metadata.get("approval_present", False)),
                    context={"owner_scope": request.owner_scope, "mode": request.mode},
                    metadata={"source": "dialogue_turn"},
                )
            )
            return result if isinstance(result, AutonomyDecision) else None
        except Exception:
            return None

    def _run_brain_loop(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
        trace_id: str,
    ) -> DecisionTrace | None:
        think = getattr(self._brain_loop, "think", None)
        if not callable(think):
            return None
        event = AIONEvent(
            event_id=f"event-dialogue-{message.message_id}",
            source="aion.dialogue",
            event_type="dialogue.message",
            actor_id=message.actor_id,
            workspace_id=message.workspace_id,
            payload_type="dialogue_message",
            payload={
                "dialogue_session_id": session.dialogue_session_id,
                "message_id": message.message_id,
                "content_hash": message.content_hash,
                "requested_mode": request.mode,
                "goal": request.session_title or session.title,
            },
            timestamp=datetime.now(UTC),
            correlation_id=None,
            trace_id=trace_id,
            security_scope=session.owner_scope,
        )
        try:
            result = think(event)
            return result if isinstance(result, DecisionTrace) else None
        except Exception:
            return None

    def _compose(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
        trace: DecisionTrace | None,
        clarification: ClarificationRequest | None,
        constraints: list[str],
    ) -> ResponseDraft:
        context: dict[str, Any] = {
            "owner_scope": session.owner_scope,
            "constraints": constraints,
            "retrieved_memory_ids": trace.memory_refs if trace is not None else [],
            "evidence_refs": [],
            "open_questions": [clarification.question] if clarification is not None else [],
        }
        metadata: dict[str, Any] = {
            "owner_scope": session.owner_scope,
            "dialogue_turn": True,
            "requires_clarification": clarification is not None,
        }
        if clarification is not None:
            metadata["clarification_question"] = clarification.question
        outcome = trace.outcome if trace is not None else {"constraints": constraints}
        if _is_self_description_question(message.content):
            self_description = self._self_description(session.owner_scope)
            if self_description is not None:
                outcome = {
                    **outcome,
                    "summary": (
                        f"{self_description.name} means {self_description.full_name}. "
                        f"{self_description.summary} "
                        "The self model is descriptive and diagnostic."
                    ),
                }
                metadata["self_description_source"] = "self_model"
        explanation_result = self._explanation_result(request, session, message, trace)
        if explanation_result:
            outcome = {**outcome, "summary": explanation_result["summary"]}
            metadata.update(explanation_result["metadata"])
        return self._response_composer.compose(
            ResponseComposeRequest(
                dialogue_session_id=session.dialogue_session_id,
                message_id=message.message_id,
                trace_id=trace.trace_id if trace is not None else message.trace_id,
                reasoning_id=trace.reasoning_refs[0] if trace and trace.reasoning_refs else None,
                plan_id=trace.plan_id if trace is not None else None,
                goal=session.title,
                context=context,
                reasoning_result=outcome,
                plan={"plan_id": trace.plan_id} if trace and trace.plan_id else {},
                require_grounding=request.require_grounding,
                response_type="answer",
                metadata=metadata,
            )
        )

    def _explanation_result(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
        trace: DecisionTrace | None,
    ) -> dict[str, Any] | None:
        use_explanations = request.metadata.get(
            "use_explanations"
        ) is True or _is_explanation_question(message.content)
        if not use_explanations:
            return None
        if _is_why_not_question(message.content):
            answer = self._why_not_answer(request, session, message, trace)
            if answer is None:
                return None
            return {
                "summary": answer.answer,
                "metadata": {
                    "why_not_id": answer.why_not_id,
                    "explanation_source": "why_not_service",
                },
            }
        explanation = self._explanation(request, session, message, trace)
        if explanation is None:
            return None
        return {
            "summary": explanation.summary,
            "metadata": {
                "explanation_id": explanation.explanation_id,
                "explanation_source": "explanation_builder",
            },
        }

    def _why_not_answer(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
        trace: DecisionTrace | None,
    ) -> Any | None:
        answer = getattr(self._why_not_service, "answer", None)
        if not callable(answer):
            return None
        try:
            return answer(
                WhyNotRequest(
                    trace_id=trace.trace_id if trace is not None else message.trace_id,
                    actor_id=message.actor_id,
                    workspace_id=message.workspace_id,
                    question=message.content,
                    target_type="trace",
                    target_id=trace.trace_id if trace is not None else message.trace_id,
                    requested_action=str(request.metadata.get("requested_action"))
                    if request.metadata.get("requested_action")
                    else None,
                    owner_scope=session.owner_scope,
                    metadata={**request.metadata, "source": "dialogue_turn"},
                    created_by=message.actor_id,
                )
            )
        except Exception:
            return None

    def _explanation(
        self,
        request: DialogueTurnRequest,
        session: DialogueSession,
        message: DialogueMessage,
        trace: DecisionTrace | None,
    ) -> Any | None:
        explain = getattr(self._explanation_builder, "explain", None)
        if not callable(explain):
            return None
        target_type = str(request.metadata.get("explanation_target_type") or "trace")
        target_id = (
            str(request.metadata.get("explanation_target_id"))
            if request.metadata.get("explanation_target_id")
            else (trace.trace_id if trace is not None else message.trace_id)
        )
        try:
            return explain(
                ExplanationRequest(
                    trace_id=trace.trace_id if trace is not None else message.trace_id,
                    actor_id=message.actor_id,
                    workspace_id=message.workspace_id,
                    explanation_type="why",
                    target_type=target_type,  # type: ignore[arg-type]
                    target_id=target_id,
                    question=message.content,
                    require_grounding=bool(
                        request.metadata.get("require_explanation_grounding", False)
                    ),
                    owner_scope=session.owner_scope,
                    metadata={**request.metadata, "source": "dialogue_turn"},
                    created_by=message.actor_id,
                )
            )
        except Exception:
            return None

    def _self_description(self, scope: list[str]) -> Any | None:
        describe = getattr(self._self_description_service, "describe", None)
        if not callable(describe):
            return None
        try:
            return describe(
                SelfDescriptionRequest(
                    scope=scope,
                    include_capabilities=True,
                    include_limitations=True,
                    include_architecture=False,
                    include_status=True,
                )
            )
        except Exception:
            return None

    def _attention(self, message: DialogueMessage, session: DialogueSession) -> None:
        create_signal = getattr(self._attention_controller, "create_signal", None)
        if not callable(create_signal):
            return
        try:
            create_signal(
                AttentionSignalCreateRequest(
                    attention_signal_id=None,
                    trace_id=message.trace_id,
                    actor_id=message.actor_id,
                    workspace_id=message.workspace_id,
                    signal_type="event_received",
                    source_type="event",
                    source_id=message.message_id,
                    title="Dialogue message received",
                    payload={
                        "dialogue_session_id": session.dialogue_session_id,
                        "message_id": message.message_id,
                        "content_hash": message.content_hash,
                    },
                    urgency=0.4,
                    importance=0.5,
                    confidence=0.8,
                    risk_level="low",
                    owner_scope=session.owner_scope,
                    metadata={"source": "dialogue_turn"},
                )
            )
        except Exception:
            return

    def _working_memory(self, message: DialogueMessage, session: DialogueSession) -> None:
        write_slot = getattr(self._working_memory_service, "write_slot", None)
        if not callable(write_slot):
            return
        try:
            write_slot(
                WorkingMemoryWriteRequest(
                    slot_id=None,
                    focus_session_id=session.active_focus_session_id,
                    trace_id=message.trace_id,
                    actor_id=message.actor_id,
                    workspace_id=message.workspace_id,
                    slot_type="scratchpad",
                    source_type="user_input",
                    source_id=message.message_id,
                    content={
                        "dialogue_session_id": session.dialogue_session_id,
                        "message_id": message.message_id,
                        "content_hash": message.content_hash,
                    },
                    summary="Dialogue message received.",
                    priority=0.45,
                    confidence=0.8,
                    ttl_seconds=None,
                    pinned=False,
                    owner_scope=session.owner_scope,
                    metadata={"source": "dialogue_turn"},
                )
            )
        except Exception:
            return

    def _audit_turn(
        self,
        session: DialogueSession,
        message: DialogueMessage,
        response: ResponseDraft,
        verification_status: str,
    ) -> None:
        record_audit_event(
            self._audit_ledger,
            action_type="dialogue.turn",
            resource_type="dialogue_session",
            resource_id=session.dialogue_session_id,
            event_type="dialogue_turn_completed",
            outcome="completed",
            source_component="dialogue_turn_service",
            trace_id=response.trace_id or message.trace_id,
            actor_id=message.actor_id,
            workspace_id=message.workspace_id,
            payload={
                "message_id": message.message_id,
                "response_id": response.response_id,
                "verification_status": verification_status,
            },
        )

    def _provenance(
        self,
        session: DialogueSession,
        message: DialogueMessage,
        response: ResponseDraft,
        trace: DecisionTrace | None,
    ) -> None:
        create_link = getattr(self._provenance_service, "create_link", None)
        if not callable(create_link):
            return
        try:
            create_link(
                ProvenanceLink(
                    provenance_link_id=f"provenance-{uuid4().hex}",
                    trace_id=response.trace_id or message.trace_id,
                    source_type="dialogue_message",
                    source_id=message.message_id,
                    target_type="response",
                    target_id=response.response_id,
                    relation_type="produced",
                    confidence=0.8,
                    evidence_refs=response.evidence_refs,
                    metadata={"dialogue_session_id": session.dialogue_session_id},
                    created_at=datetime.now(UTC),
                    deleted_at=None,
                )
            )
            if trace is not None:
                create_link(
                    ProvenanceLink(
                        provenance_link_id=f"provenance-{uuid4().hex}",
                        trace_id=trace.trace_id,
                        source_type="trace",
                        source_id=trace.trace_id,
                        target_type="response",
                        target_id=response.response_id,
                        relation_type="produced",
                        confidence=0.8,
                        evidence_refs=response.evidence_refs,
                        metadata={"dialogue_session_id": session.dialogue_session_id},
                        created_at=datetime.now(UTC),
                        deleted_at=None,
                    )
                )
        except Exception:
            return


def _requires_clarification(trace: DecisionTrace) -> bool:
    return bool(
        trace.outcome.get("requires_clarification")
        or trace.outcome.get("reasoning_requires_clarification")
    )


def _clarification_question(trace: DecisionTrace) -> str:
    value = trace.outcome.get("clarification_question")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "What should AION clarify before continuing?"


def _is_self_description_question(message: str) -> bool:
    lowered = message.lower()
    return any(
        phrase in lowered
        for phrase in (
            "what is aion",
            "what are you",
            "what can you do",
            "what are your limits",
        )
    )


def _is_explanation_question(message: str) -> bool:
    lowered = message.lower()
    return any(
        phrase in lowered
        for phrase in (
            "why",
            "why not",
            "explain",
            "what happened",
            "why was this blocked",
        )
    )


def _is_why_not_question(message: str) -> bool:
    lowered = message.lower()
    return "why not" in lowered or "why was this blocked" in lowered or "blocked" in lowered

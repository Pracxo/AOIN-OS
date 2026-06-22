from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from aion_brain.contracts.dialogue import DialogueSessionCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.dialogue.clarification import ClarificationManager
from aion_brain.dialogue.memory_handoff import DialogueMemoryHandoffService
from aion_brain.dialogue.message_service import DialogueMessageService
from aion_brain.dialogue.repository import DialogueRepository
from aion_brain.dialogue.session_service import DialogueSessionService
from aion_brain.dialogue.turn_service import DialogueTurnService
from aion_brain.responses.composer import ResponseComposer
from aion_brain.responses.delivery import ResponseDeliveryService
from aion_brain.responses.feedback import DialogueFeedbackService
from aion_brain.responses.verifier import ResponseVerifier


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied_for_test",
            constraints=["test_deny"],
            audit_level="high",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeBrainLoop:
    def __init__(self, *, requires_clarification: bool = False) -> None:
        self.calls = 0
        self.requires_clarification = requires_clarification

    def think(self, event: object) -> DecisionTrace:
        self.calls += 1
        return DecisionTrace(
            trace_id="trace-dialogue",
            event_id="event-dialogue",
            intent_id="intent-1",
            context_id="context-1",
            plan_id="plan-1",
            memory_refs=["memory-1"],
            capability_refs=[],
            reasoning_refs=["reasoning-1"],
            execution_refs=[],
            policy_decisions=[],
            outcome={
                "status": "planned",
                "summary": "I found relevant context and prepared a plan.",
                "requires_clarification": self.requires_clarification,
                "clarification_question": "What should happen next?",
            },
            created_at=datetime.now(UTC),
        )


class FakeMemoryService:
    def __init__(self) -> None:
        self.records: list[object] = []

    def create(self, record: object) -> object:
        self.records.append(record)
        return record


def service_bundle(
    policy: object | None = None,
    *,
    brain_loop: object | None = None,
    memory_service: object | None = None,
    claim_extractor: object | None = None,
    belief_service: object | None = None,
    entity_resolver: object | None = None,
    settings: object | None = None,
) -> SimpleNamespace:
    repository = DialogueRepository()
    policy_adapter = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    session_service = DialogueSessionService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
    )
    message_service = DialogueMessageService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
        settings=SimpleNamespace(
            dialogue_store_messages=True,
            dialogue_redact_sensitive_content=True,
        ),
    )
    clarification_manager = ClarificationManager(
        repository,
        message_service,
        policy_adapter,
        telemetry_service=telemetry,
    )
    response_composer = ResponseComposer(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
        settings=SimpleNamespace(response_require_grounding_default=False),
    )
    response_verifier = ResponseVerifier(repository, policy_adapter, telemetry_service=telemetry)
    response_delivery = ResponseDeliveryService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
    )
    feedback_service = DialogueFeedbackService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
    )
    handoff = DialogueMemoryHandoffService(
        repository,
        policy_adapter,
        memory_service or FakeMemoryService(),
        telemetry_service=telemetry,
        settings=SimpleNamespace(dialogue_memory_handoff_enabled=True),
    )
    turn_service = DialogueTurnService(
        session_service=session_service,
        message_service=message_service,
        clarification_manager=clarification_manager,
        response_composer=response_composer,
        response_verifier=response_verifier,
        response_delivery=response_delivery,
        brain_loop=brain_loop,
        attention_controller=None,
        working_memory_service=None,
        memory_handoff_service=handoff,
        policy_adapter=policy_adapter,
        autonomy_governor=None,
        audit_ledger=None,
        provenance_service=None,
        telemetry_service=telemetry,
        settings=settings or SimpleNamespace(dialogue_enabled=True),
        claim_extractor=claim_extractor,
        belief_service=belief_service,
        entity_resolver=entity_resolver,
    )
    return SimpleNamespace(
        repository=repository,
        policy=policy_adapter,
        telemetry=telemetry,
        session_service=session_service,
        message_service=message_service,
        clarification_manager=clarification_manager,
        response_composer=response_composer,
        response_verifier=response_verifier,
        response_delivery=response_delivery,
        feedback_service=feedback_service,
        handoff=handoff,
        turn_service=turn_service,
    )


def create_session(bundle: SimpleNamespace) -> str:
    session = bundle.session_service.create_session(
        DialogueSessionCreateRequest(
            title="Test Session",
            owner_scope=["workspace:main"],
            metadata={},
        )
    )
    return str(session.dialogue_session_id)

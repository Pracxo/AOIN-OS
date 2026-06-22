"""Response candidate service for governed model outputs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.model_outputs import (
    ModelOutputRecord,
    ResponseCandidate,
    ResponseCandidateType,
)
from aion_brain.contracts.responses import ResponseDraft, ResponseType
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.hashing import hash_message_content
from aion_brain.model_outputs.hash import hash_model_output


class ResponseCandidateService:
    """Create and review response candidates without external delivery."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        response_repository: object | None = None,
        response_verifier: object | None = None,
        grounding_verifier: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._response_repository = response_repository
        self._response_verifier = response_verifier
        self._grounding_verifier = grounding_verifier
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ResponseCandidateService:
        return ResponseCandidateService(
            self._repository,
            self._policy_adapter,
            response_repository=self._response_repository,
            response_verifier=self._response_verifier,
            grounding_verifier=self._grounding_verifier,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_from_output(
        self,
        model_output_id: str,
        owner_scope: list[str],
        require_grounding: bool = False,
    ) -> ResponseCandidate:
        """Create a response candidate from redacted model output."""

        authorize(
            self._policy_adapter,
            action_type="model_output.response_candidate.create",
            resource_type="response_candidate",
            resource_id=model_output_id,
            scope=owner_scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
        )
        output = _get_output(self._repository, model_output_id)
        grounded = bool(output.metadata.get("grounding_refs"))
        status = "blocked" if require_grounding and not grounded else "proposed"
        constraints = ["grounding_required"] if require_grounding and not grounded else []
        candidate = ResponseCandidate(
            response_candidate_id=f"response-candidate-{uuid4().hex}",
            model_output_id=output.model_output_id,
            trace_id=output.trace_id,
            dialogue_session_id=_metadata_str(output.metadata, "dialogue_session_id"),
            prompt_packet_id=output.prompt_packet_id,
            status=status,  # type: ignore[arg-type]
            response_type=_response_type(output),
            content=output.redacted_output,
            content_hash=hash_model_output(output.redacted_output),
            grounded=grounded,
            citation_refs=_metadata_list(output.metadata, "citation_refs"),
            grounding_refs=_metadata_list(output.metadata, "grounding_refs"),
            belief_refs=_metadata_list(output.metadata, "belief_refs"),
            entity_refs=_metadata_list(output.metadata, "entity_refs"),
            unsupported_statement_refs=[],
            verification_refs=[],
            confidence=0.75 if not constraints else 0.35,
            score=0.8 if not constraints else 0.3,
            constraints=constraints,
            metadata={"owner_scope": owner_scope, "source": "model_output_governance"},
            created_by=self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_response_candidate", None)
        stored = save(candidate) if callable(save) else candidate
        stored = stored if isinstance(stored, ResponseCandidate) else candidate
        emit_telemetry(
            self._telemetry_service,
            event_type="response_candidate_created",
            node_type="response_candidate",
            node_id=stored.response_candidate_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            payload={"status": stored.status},
        )
        return stored

    def promote_to_response(
        self,
        response_candidate_id: str,
        actor_id: str | None,
        approval_present: bool = False,
        reason: str = "",
    ) -> ResponseCandidate:
        """Promote a verified candidate to a local ResponseDraft only."""

        candidate = self._get_candidate(response_candidate_id)
        scope = _metadata_list(candidate.metadata, "owner_scope") or ["workspace:main"]
        authorize(
            self._policy_adapter,
            action_type="model_output.response_candidate.update",
            resource_type="response_candidate",
            resource_id=response_candidate_id,
            scope=scope,
            trace_id=candidate.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            approval_present=approval_present,
            context={"reason": reason},
        )
        if candidate.status == "blocked":
            raise PermissionError("blocked_response_candidate")
        if not _verifier_passed(self._response_verifier, candidate):
            raise PermissionError("response_verifier_failed")
        response_id = f"response-{uuid4().hex}"
        save_response = getattr(self._response_repository, "save_response", None)
        if callable(save_response):
            save_response(
                ResponseDraft(
                    response_id=response_id,
                    dialogue_session_id=candidate.dialogue_session_id,
                    message_id=None,
                    trace_id=candidate.trace_id,
                    reasoning_id=None,
                    plan_id=None,
                    status="draft",
                    response_type=_draft_response_type(candidate.response_type),
                    content=candidate.content,
                    content_hash=hash_message_content(candidate.content),
                    grounded=candidate.grounded,
                    grounding_refs=candidate.grounding_refs,
                    memory_refs=[],
                    evidence_refs=[],
                    clarification_refs=[],
                    constraints=candidate.constraints,
                    metadata={"response_candidate_id": candidate.response_candidate_id},
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
        promoted = candidate.model_copy(
            update={
                "status": "promoted",
                "promoted_response_id": response_id,
                "metadata": {**candidate.metadata, "promotion_reason": reason},
            }
        )
        update = getattr(self._repository, "update_response_candidate", None)
        stored = update(promoted) if callable(update) else promoted
        emit_telemetry(
            self._telemetry_service,
            event_type="response_candidate_promoted",
            node_type="response_candidate",
            node_id=promoted.response_candidate_id,
            intensity=0.8,
            trace_id=promoted.trace_id,
            payload={"promoted_response_id": response_id},
        )
        return stored if isinstance(stored, ResponseCandidate) else promoted

    def list_candidates(
        self,
        scope: list[str],
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[ResponseCandidate]:
        """List response candidates."""

        authorize(
            self._policy_adapter,
            action_type="model_output.response_candidate.read",
            resource_type="response_candidate",
            resource_id=trace_id,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_candidates = getattr(self._repository, "list_response_candidates", None)
        if not callable(list_candidates):
            return []
        result = list_candidates(scope, status=status, trace_id=trace_id, limit=limit)
        return [item for item in result if isinstance(item, ResponseCandidate)]

    def _get_candidate(self, response_candidate_id: str) -> ResponseCandidate:
        get_candidate = getattr(self._repository, "get_response_candidate", None)
        candidate = get_candidate(response_candidate_id) if callable(get_candidate) else None
        if not isinstance(candidate, ResponseCandidate):
            raise ValueError("response_candidate_not_found")
        return candidate


def _get_output(repository: object, model_output_id: str) -> ModelOutputRecord:
    get_output = getattr(repository, "get_output", None)
    output = get_output(model_output_id) if callable(get_output) else None
    if not isinstance(output, ModelOutputRecord):
        raise ValueError("model_output_not_found")
    return output


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) else None


def _metadata_list(metadata: dict[str, Any], key: str) -> list[str]:
    value = metadata.get(key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _response_type(output: ModelOutputRecord) -> ResponseCandidateType:
    if output.output_type == "empty":
        return "status"
    if "unable to comply" in output.redacted_output.lower():
        return "refusal"
    return "answer"


def _draft_response_type(response_type: ResponseCandidateType) -> ResponseType:
    if response_type == "answer":
        return "answer"
    if response_type == "clarification":
        return "clarification"
    if response_type == "refusal":
        return "refusal"
    if response_type == "status":
        return "status"
    if response_type == "summary":
        return "status"
    return "answer"


def _verifier_passed(verifier: object | None, candidate: ResponseCandidate) -> bool:
    verify_candidate = getattr(verifier, "verify_candidate", None)
    if not callable(verify_candidate):
        return True
    result = verify_candidate(candidate)
    if isinstance(result, bool):
        return result
    return bool(getattr(result, "allow", False) or getattr(result, "status", "") == "passed")


__all__ = ["ResponseCandidateService"]

"""Deterministic response composer for dialogue turns."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.grounding import GroundingVerificationRequest
from aion_brain.contracts.prompts import PromptCompileRequest
from aion_brain.contracts.responses import ResponseComposeRequest, ResponseDraft, ResponseType
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.hashing import hash_message_content
from aion_brain.dialogue.repository import DialogueRepository


class ResponseComposer:
    """Compose deterministic, grounded response drafts."""

    def __init__(
        self,
        repository: DialogueRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
        confidence_calibrator: object | None = None,
        explanation_builder: object | None = None,
        citation_mapper: object | None = None,
        grounding_verifier: object | None = None,
        prompt_compiler: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._confidence_calibrator = confidence_calibrator
        self._explanation_builder = explanation_builder
        self._citation_mapper = citation_mapper
        self._grounding_verifier = grounding_verifier
        self._prompt_compiler = prompt_compiler

    def set_explanation_builder(self, explanation_builder: object | None) -> None:
        """Attach the explanation builder after kernel assembly."""

        self._explanation_builder = explanation_builder

    def set_grounding_services(
        self,
        citation_mapper: object | None,
        grounding_verifier: object | None,
    ) -> None:
        """Attach grounding services after kernel assembly."""

        self._citation_mapper = citation_mapper
        self._grounding_verifier = grounding_verifier

    def set_prompt_compiler(self, prompt_compiler: object | None) -> None:
        """Attach prompt compiler after kernel assembly."""

        self._prompt_compiler = prompt_compiler

    def compose(self, request: ResponseComposeRequest) -> ResponseDraft:
        """Compose and persist one deterministic response draft."""

        response_id = request.response_id or f"response-{uuid4().hex}"
        scope = _scope_from_request(request)
        authorize(
            self._policy_adapter,
            action_type="dialogue.response.compose",
            resource_type="response",
            resource_id=response_id,
            scope=scope,
            trace_id=request.trace_id,
            risk_level="low",
            context={"response_type": request.response_type},
        )
        require_grounding = request.require_grounding or bool(
            getattr(self._settings, "response_require_grounding_default", False)
        )
        evidence_refs = (
            _string_refs(request.context, "evidence_refs")
            + _string_refs(
                request.reasoning_result,
                "evidence_refs",
            )
            + _string_refs(request.metadata, "evidence_refs")
        )
        memory_refs = (
            _string_refs(request.context, "retrieved_memory_ids")
            + _string_refs(
                request.reasoning_result,
                "memory_refs",
            )
            + _string_refs(request.metadata, "memory_refs")
        )
        belief_refs = _string_refs(request.metadata, "belief_refs")
        entity_refs = _string_refs(request.metadata, "entity_refs")
        grounding_refs = _unique(
            _string_refs(request.context, "grounding_refs")
            + _string_refs(request.metadata, "grounding_refs")
            + evidence_refs
            + belief_refs
            + memory_refs
            + entity_refs
        )
        clarification_question = _clarification_question(request)
        constraints = _constraints(request)
        response_type: ResponseType = request.response_type
        grounded = bool(evidence_refs or grounding_refs)
        status = "draft"
        metadata = {
            **request.metadata,
            "require_grounding": require_grounding,
            "deterministic_composer": True,
        }
        if belief_refs:
            metadata["belief_refs"] = _unique(belief_refs)
        if entity_refs:
            metadata["entity_refs"] = _unique(entity_refs)
        effective_style = request.metadata.get("effective_style")
        if isinstance(effective_style, dict):
            metadata["style_profile_applied"] = effective_style.get("style_profile_id")
            metadata["style_constraints_preserved"] = True
        if clarification_question:
            response_type = "clarification"
            content = f"I need one clarification before continuing: {clarification_question}"
        elif _decision_recommendation(request):
            response_type = "status"
            content = _decision_recommendation(request) or "A decision recommendation is available."
        elif _blocked(constraints, request):
            response_type = "status"
            status = "blocked"
            content = _blocked_content(constraints)
        elif require_grounding and not grounded:
            response_type = "status"
            status = "blocked"
            constraints = [*constraints, "grounding_required"]
            content = "More grounding is needed before I can provide a reliable response."
        elif explanation_summary := _explanation_summary(self._explanation_builder, request):
            content = explanation_summary
            metadata["explanation_included"] = True
        else:
            content = _response_content(request)
        metadata.update(
            _compile_response_prompt(
                self._prompt_compiler,
                request,
                response_id=response_id,
                content=content,
                scope=scope,
            )
        )
        now = datetime.now(UTC)
        if bool(getattr(self._settings, "confidence_calibration_enabled", True)):
            calibration = _calibrate_response(
                self._confidence_calibrator,
                response_id,
                request.trace_id,
                evidence_refs,
                memory_refs,
                require_grounding,
                metadata,
            )
            if calibration is not None:
                metadata["calibration_id"] = calibration.calibration_id
                metadata["confidence_level"] = calibration.confidence_level
                metadata["required_disclosures"] = calibration.required_disclosures
                if calibration.required_disclosures:
                    constraints = _unique([*constraints, *calibration.required_disclosures])
        draft = ResponseDraft(
            response_id=response_id,
            dialogue_session_id=request.dialogue_session_id,
            message_id=request.message_id,
            trace_id=request.trace_id,
            reasoning_id=request.reasoning_id,
            plan_id=request.plan_id,
            status=cast(Any, status),
            response_type=response_type,
            content=content,
            content_hash=hash_message_content(content),
            grounded=grounded,
            grounding_refs=grounding_refs,
            memory_refs=_unique(memory_refs),
            evidence_refs=_unique(evidence_refs),
            clarification_refs=_string_refs(request.context, "clarification_refs"),
            constraints=_unique(constraints),
            metadata=metadata,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_response(draft)
        stored = self._apply_grounding_if_required(stored, require_grounding, scope)
        emit_telemetry(
            self._telemetry_service,
            event_type="response_composed",
            node_type="response",
            node_id=stored.response_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            edge_from=stored.message_id,
            edge_to=stored.response_id,
            payload={
                "owner_scope": scope,
                "status": stored.status,
                "response_type": stored.response_type,
            },
        )
        if stored.status == "blocked":
            emit_telemetry(
                self._telemetry_service,
                event_type="response_blocked",
                node_type="response",
                node_id=stored.response_id,
                intensity=1.0,
                trace_id=stored.trace_id,
                payload={"owner_scope": scope, "constraints": stored.constraints},
            )
        return stored

    def _apply_grounding_if_required(
        self,
        response: ResponseDraft,
        require_grounding: bool,
        scope: list[str],
    ) -> ResponseDraft:
        if not require_grounding or response.status == "blocked":
            return response
        metadata = dict(response.metadata)
        required_source_types = _string_refs(metadata, "required_source_types")
        try:
            map_response = getattr(self._citation_mapper, "map_response", None)
            if callable(map_response):
                citation_map = map_response(
                    response.response_id,
                    scope,
                    required_source_types,
                )
                metadata["citation_map_id"] = citation_map.citation_map_id
                metadata["grounding_coverage_score"] = citation_map.coverage_score
            verify = getattr(self._grounding_verifier, "verify", None)
            if callable(verify):
                verification = verify(
                    GroundingVerificationRequest(
                        trace_id=response.trace_id,
                        response_id=response.response_id,
                        target_type="response",
                        target_id=response.response_id,
                        owner_scope=scope,
                        required_source_types=cast(Any, required_source_types),
                        require_evidence=bool(
                            metadata.get("require_evidence")
                            or getattr(
                                self._settings,
                                "grounding_require_evidence_default",
                                False,
                            )
                        ),
                        allow_memory_only=bool(
                            getattr(
                                self._settings,
                                "grounding_allow_memory_only_default",
                                False,
                            )
                        ),
                        metadata={"source": "response_composer"},
                    )
                )
                metadata["grounding_verification_id"] = verification.grounding_verification_id
                metadata["grounding_status"] = verification.status
                response = response.model_copy(
                    update={
                        "grounded": verification.grounded,
                        "metadata": metadata,
                        "updated_at": datetime.now(UTC),
                    }
                )
                return self._repository.save_response(response)
        except Exception:
            metadata["grounding_status"] = "unavailable"
            response = response.model_copy(
                update={"metadata": metadata, "updated_at": datetime.now(UTC)}
            )
            return self._repository.save_response(response)
        return response

    def get_response(self, response_id: str) -> ResponseDraft | None:
        """Return one stored response draft."""

        return self._repository.get_response(response_id)


def _response_content(request: ResponseComposeRequest) -> str:
    summary = _first_text(
        request.reasoning_result,
        ("summary", "result_summary", "message"),
    )
    if summary:
        return summary
    plan_summary = _plan_summary(request.plan)
    if plan_summary:
        return plan_summary
    if request.goal:
        return f"I found relevant context for: {request.goal}."
    return "I found relevant context and prepared a response."


def _explanation_summary(
    explanation_builder: object | None, request: ResponseComposeRequest
) -> str | None:
    explicit = request.metadata.get("explanation_summary")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    explanation_id = request.metadata.get("explanation_id")
    if not explanation_id:
        return None
    get_explanation = getattr(explanation_builder, "get", None)
    if not callable(get_explanation):
        return None
    try:
        explanation = get_explanation(str(explanation_id), _scope_from_request(request))
    except Exception:
        return None
    summary = getattr(explanation, "summary", None)
    return summary.strip() if isinstance(summary, str) and summary.strip() else None


def _decision_recommendation(request: ResponseComposeRequest) -> str | None:
    raw = request.metadata.get("decision_recommendation") or request.context.get(
        "decision_recommendation"
    )
    if not isinstance(raw, dict):
        return None
    option = raw.get("recommended_option_title") or raw.get("recommended_option_id")
    if not option:
        return None
    constraints = raw.get("constraints")
    suffix = ""
    if isinstance(constraints, list) and constraints:
        suffix = f" Current constraints: {', '.join(str(item) for item in constraints)}."
    return (
        f"The strongest available option is {option}. "
        f"This is a recommendation, not execution.{suffix}"
    )


def _blocked_content(constraints: list[str]) -> str:
    if any("approval" in item for item in constraints):
        return "This action is waiting for approval."
    if any("autonomy" in item for item in constraints):
        return "The current autonomy mode allows planning only."
    return "This response is blocked by the current safety constraints."


def _plan_summary(plan: dict[str, Any]) -> str | None:
    steps = plan.get("steps")
    if isinstance(steps, list) and steps:
        return f"I prepared a generic plan with {len(steps)} step(s)."
    status = plan.get("status")
    if isinstance(status, str):
        return f"I prepared a plan with status: {status}."
    return None


def _clarification_question(request: ResponseComposeRequest) -> str | None:
    value = request.metadata.get("clarification_question")
    if isinstance(value, str) and value.strip():
        return value.strip()
    open_questions = request.context.get("open_questions")
    if isinstance(open_questions, list) and open_questions:
        first = open_questions[0]
        if isinstance(first, str) and first.strip():
            return first.strip()
    if bool(request.reasoning_result.get("requires_clarification")):
        question = request.reasoning_result.get("clarification_question")
        return str(question) if question else "What outcome should I optimize for?"
    return None


def _blocked(constraints: list[str], request: ResponseComposeRequest) -> bool:
    if any("blocked" in item or "denied" in item for item in constraints):
        return True
    return bool(request.reasoning_result.get("blocked") or request.plan.get("blocked"))


def _constraints(request: ResponseComposeRequest) -> list[str]:
    values: list[str] = []
    for payload in (request.context, request.reasoning_result, request.plan, request.metadata):
        raw = payload.get("constraints")
        if isinstance(raw, list):
            values.extend(str(item) for item in raw)
    return _unique(values)


def _scope_from_request(request: ResponseComposeRequest) -> list[str]:
    for payload in (request.metadata, request.context):
        raw = payload.get("owner_scope") or payload.get("scope") or payload.get("security_scope")
        if isinstance(raw, list):
            values = [str(item) for item in raw]
            if values:
                return values
    return ["workspace:main"]


def _string_refs(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return []


def _first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _compile_response_prompt(
    prompt_compiler: object | None,
    request: ResponseComposeRequest,
    *,
    response_id: str,
    content: str,
    scope: list[str],
) -> dict[str, Any]:
    compile_prompt = getattr(prompt_compiler, "compile", None)
    if not callable(compile_prompt):
        return {}
    try:
        result = compile_prompt(
            PromptCompileRequest(
                trace_id=request.trace_id,
                packet_type="response",
                response_id=response_id,
                instruction_resolution_id=_metadata_str(
                    request.metadata, "instruction_resolution_id"
                ),
                grounding_verification_id=_metadata_str(
                    request.metadata, "grounding_verification_id"
                ),
                owner_scope=scope,
                user_message=content,
                max_chars=int(request.metadata.get("prompt_max_chars", 12000)),
                include_redacted_preview=True,
                store_packet=True,
                metadata={
                    "source": "response_composer",
                    "context": request.context,
                    "reasoning_refs": _string_refs(request.reasoning_result, "reasoning_refs"),
                    "evidence_refs": _string_refs(request.metadata, "evidence_refs"),
                    "memory_refs": _string_refs(request.metadata, "memory_refs"),
                },
                created_by=_metadata_str(request.metadata, "created_by"),
            )
        )
    except Exception:
        return {"prompt_governance_status": "unavailable"}
    packet = getattr(result, "prompt_packet", None)
    manifest = getattr(result, "model_input_manifest", None)
    return {
        "prompt_governance_status": getattr(packet, "status", "unknown"),
        "prompt_packet_id": getattr(packet, "prompt_packet_id", None),
        "prompt_boundary_check_id": getattr(packet, "boundary_check_id", None),
        "model_input_manifest_id": getattr(manifest, "model_input_manifest_id", None),
    }


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None


def _calibrate_response(
    calibrator: object | None,
    response_id: str,
    trace_id: str | None,
    evidence_refs: list[str],
    memory_refs: list[str],
    require_grounding: bool,
    metadata: dict[str, Any],
) -> Any | None:
    calibrate_response = getattr(calibrator, "calibrate_response", None)
    if not callable(calibrate_response):
        return None
    try:
        return calibrate_response(
            response_id,
            trace_id=trace_id,
            evidence_refs=evidence_refs,
            memory_refs=memory_refs,
            require_grounding=require_grounding,
            metadata=metadata,
        )
    except Exception:
        return None

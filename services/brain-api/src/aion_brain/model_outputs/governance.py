"""Model output governance orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import ToolIntentReviewRequest
from aion_brain.contracts.model_outputs import ModelOutputCreateRequest, ModelOutputRecord
from aion_brain.contracts.output_governance import (
    ModelOutputQuery,
    ModelOutputQueryResult,
    OutputGovernanceRequest,
    OutputGovernanceRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.model_outputs.hash import estimate_output_tokens, hash_model_output
from aion_brain.model_outputs.parser import OutputParser
from aion_brain.model_outputs.redaction import redact_model_output
from aion_brain.model_outputs.unsafe_detector import UnsafeOutputDetector


class OutputGovernanceService:
    """Receive, parse, validate, and govern model outputs."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        parser: OutputParser | None = None,
        unsafe_detector: UnsafeOutputDetector | None = None,
        structured_validator: object | None = None,
        response_candidate_service: object | None = None,
        tool_intent_service: object | None = None,
        tool_intent_review_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._parser = parser or OutputParser()
        self._unsafe_detector = unsafe_detector or UnsafeOutputDetector()
        self._structured_validator = structured_validator
        self._response_candidate_service = response_candidate_service
        self._tool_intent_service = tool_intent_service
        self._tool_intent_review_service = tool_intent_review_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> OutputGovernanceService:
        return OutputGovernanceService(
            self._repository,
            self._policy_adapter,
            parser=self._parser,
            unsafe_detector=self._unsafe_detector,
            structured_validator=self._structured_validator,
            response_candidate_service=self._response_candidate_service,
            tool_intent_service=self._tool_intent_service,
            tool_intent_review_service=self._tool_intent_review_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def set_tool_intent_review_service(self, service: object | None) -> None:
        """Attach the optional action proposal tool-intent review service."""

        self._tool_intent_review_service = service

    def provider_simulation_requirements(self) -> dict[str, object]:
        """Return provider-simulation output governance requirements."""

        return {
            "output_governance_required": True,
            "tool_intent_blocking_required": bool(
                getattr(self._settings, "output_governance_block_tool_intents_default", True)
            ),
            "grounding_required": bool(
                getattr(self._settings, "output_governance_require_grounding_default", False)
            ),
            "raw_output_storage_allowed": bool(
                getattr(self._settings, "model_output_store_raw", False)
            ),
        }

    def receive_output(self, request: ModelOutputCreateRequest) -> ModelOutputRecord:
        """Receive and persist a redacted model output record."""

        if self._settings is not None and not bool(
            getattr(self._settings, "model_outputs_enabled", True)
        ):
            raise RuntimeError("model_outputs_disabled")
        authorize(
            self._policy_adapter,
            action_type="model_output.create",
            resource_type="model_output",
            resource_id=request.model_output_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id or request.actor_id,
            workspace_id=self._actor_context.workspace_id or request.workspace_id,
            risk_level="medium",
        )
        redacted_output, findings = redact_model_output(request.raw_output)
        safety_findings = [*findings, *self._unsafe_detector.detect(redacted_output)]
        output = ModelOutputRecord(
            model_output_id=request.model_output_id or f"model-output-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            prompt_packet_id=request.prompt_packet_id,
            model_input_manifest_id=request.model_input_manifest_id,
            model_route=request.model_route,
            provider_type=request.provider_type,
            status="received",
            output_type=request.output_type,
            raw_output_hash=hash_model_output(request.raw_output),
            redacted_output=redacted_output,
            output_redacted=redacted_output != request.raw_output,
            token_estimate=estimate_output_tokens(redacted_output),
            char_count=len(redacted_output),
            safety_findings=safety_findings,
            metadata={
                **request.metadata,
                "owner_scope": request.owner_scope,
                "raw_output_stored": bool(getattr(self._settings, "model_output_store_raw", False)),
            },
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_output", None)
        stored = save(output) if callable(save) else output
        stored = stored if isinstance(stored, ModelOutputRecord) else output
        emit_telemetry(
            self._telemetry_service,
            event_type="model_output_received",
            node_type="model_output",
            node_id=stored.model_output_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "output_type": stored.output_type},
        )
        return stored

    def govern(self, request: OutputGovernanceRequest) -> OutputGovernanceRun:
        """Run deterministic governance for one model output."""

        if self._settings is not None and not bool(
            getattr(self._settings, "output_governance_enabled", True)
        ):
            raise RuntimeError("output_governance_disabled")
        authorize(
            self._policy_adapter,
            action_type="model_output.govern",
            resource_type="model_output",
            resource_id=request.model_output_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
        )
        output = self.get_output(request.model_output_id, request.owner_scope)
        if output is None:
            raise ValueError("model_output_not_found")
        issues = [*output.safety_findings, *self._unsafe_detector.detect(output.redacted_output)]
        segments = self._parser.parse(output) if request.parse_segments else []
        if segments:
            save_segments = getattr(self._repository, "save_segments", None)
            saved_segments = save_segments(segments) if callable(save_segments) else segments
            segments = [item for item in saved_segments if hasattr(item, "output_segment_id")]
            emit_telemetry(
                self._telemetry_service,
                event_type="model_output_parsed",
                node_type="model_output",
                node_id=output.model_output_id,
                intensity=0.55,
                trace_id=output.trace_id,
                payload={"segment_count": len(segments)},
            )
        validations = []
        if request.validate_structured:
            validate = getattr(self._structured_validator, "validate", None)
            if callable(validate):
                try:
                    validations.append(validate(output.model_output_id, "generic_json"))
                except Exception:
                    issues.append(
                        {"code": "structured_validation_unavailable", "severity": "medium"}
                    )
        candidates = []
        if request.create_response_candidate:
            create_candidate = getattr(self._response_candidate_service, "create_from_output", None)
            if callable(create_candidate):
                candidates.append(
                    create_candidate(
                        output.model_output_id,
                        request.owner_scope,
                        request.require_grounding
                        or bool(
                            getattr(
                                self._settings,
                                "output_governance_require_grounding_default",
                                False,
                            )
                        ),
                    )
                )
        intents = []
        if request.detect_tool_intents:
            capture = getattr(self._tool_intent_service, "capture_from_segments", None)
            if callable(capture):
                intents = capture(output.model_output_id, segments)
        if request.metadata.get("review_tool_intents") is True and bool(
            getattr(self._settings, "action_proposal_auto_create_from_tool_intent", False)
        ):
            review = getattr(self._tool_intent_review_service, "review", None)
            if callable(review):
                for intent in intents:
                    review(
                        ToolIntentReviewRequest(
                            tool_intent_id=intent.tool_intent_id,
                            decision="create_proposal",
                            actor_id=output.actor_id,
                            workspace_id=output.workspace_id,
                            owner_scope=request.owner_scope,
                            created_by=request.created_by,
                        )
                    )
        block_tool_intents = bool(
            getattr(self._settings, "output_governance_block_tool_intents_default", True)
        )
        blocked = _blocked(issues, intents, block_tool_intents)
        score = max(
            0.0,
            1.0
            - (0.25 * len([i for i in issues if i.get("severity") == "critical"]))
            - (0.1 * len(intents)),
        )
        run = OutputGovernanceRun(
            output_governance_id=request.output_governance_id or f"output-governance-{uuid4().hex}",
            trace_id=request.trace_id or output.trace_id,
            model_output_id=output.model_output_id,
            status="blocked" if blocked else ("warning" if issues or intents else "passed"),
            owner_scope=request.owner_scope,
            parsed_segments=segments,
            response_candidates=candidates,
            tool_intents=intents,
            structured_validations=validations,
            blocked=blocked,
            issues=issues,
            constraints=_constraints(blocked, intents, block_tool_intents),
            score=score,
            result={
                "response_candidate_id": candidates[0].response_candidate_id
                if candidates
                else None,
                "tool_intent_count": len(intents),
                "redacted_output_only": True,
            },
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        save_run = getattr(self._repository, "save_governance_run", None)
        stored = save_run(run) if callable(save_run) else run
        stored = stored if isinstance(stored, OutputGovernanceRun) else run
        update_status = getattr(self._repository, "update_output_status", None)
        if callable(update_status):
            update_status(output.model_output_id, "blocked" if stored.blocked else "governed")
        emit_telemetry(
            self._telemetry_service,
            event_type="model_output_governed",
            node_type="output_governance",
            node_id=stored.output_governance_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "blocked": stored.blocked},
        )
        if stored.blocked:
            emit_telemetry(
                self._telemetry_service,
                event_type="model_output_blocked",
                node_type="output_governance",
                node_id=stored.output_governance_id,
                intensity=1.0,
                trace_id=stored.trace_id,
                payload={"constraints": stored.constraints},
            )
        return stored

    def get_output(self, model_output_id: str, scope: list[str]) -> ModelOutputRecord | None:
        """Return one redacted model output record."""

        authorize(
            self._policy_adapter,
            action_type="model_output.read",
            resource_type="model_output",
            resource_id=model_output_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get_output = getattr(self._repository, "get_output", None)
        output = get_output(model_output_id) if callable(get_output) else None
        return output if isinstance(output, ModelOutputRecord) else None

    def query(self, query: ModelOutputQuery) -> ModelOutputQueryResult:
        """Query redacted model output records."""

        authorize(
            self._policy_adapter,
            action_type="model_output.read",
            resource_type="model_output",
            resource_id=query.trace_id,
            scope=query.scope,
            trace_id=query.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        query_call = getattr(self._repository, "query", None)
        result = query_call(query) if callable(query_call) else None
        if isinstance(result, ModelOutputQueryResult):
            return result
        return ModelOutputQueryResult(
            total_count=0, constraints=["repository_unavailable"], metadata={}
        )

    def soft_delete_output(self, model_output_id: str, actor_id: str | None, reason: str) -> bool:
        """Soft delete a model output record."""

        authorize(
            self._policy_adapter,
            action_type="model_output.delete",
            resource_type="model_output",
            resource_id=model_output_id,
            scope=["workspace:main"],
            trace_id=self._actor_context.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        delete = getattr(self._repository, "soft_delete_output", None)
        return bool(delete(model_output_id) if callable(delete) else False)

    def get_governance_run(self, output_governance_id: str) -> OutputGovernanceRun | None:
        get_run = getattr(self._repository, "get_governance_run", None)
        run = get_run(output_governance_id) if callable(get_run) else None
        return run if isinstance(run, OutputGovernanceRun) else None


def _blocked(issues: list[dict[str, object]], intents: list[object], block_intents: bool) -> bool:
    if block_intents and intents:
        return True
    return any(str(issue.get("severity")) == "critical" for issue in issues)


def _constraints(blocked: bool, intents: list[object], block_intents: bool) -> list[str]:
    constraints = ["redacted_output_only"]
    if block_intents and intents:
        constraints.append("tool_intents_blocked_by_default")
    if blocked:
        constraints.append("output_governance_blocked")
    return constraints


__all__ = ["OutputGovernanceService"]

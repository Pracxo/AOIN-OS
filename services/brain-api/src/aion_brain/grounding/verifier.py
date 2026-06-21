"""Grounding verification service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.grounding import (
    GroundingVerificationRequest,
    GroundingVerificationRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.grounding.audit import (
    create_grounding_provenance_link,
    record_grounding_audit,
)


class GroundingVerifier:
    """Verify grounding for response-like targets."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object,
        *,
        citation_mapper: object | None = None,
        coverage_service: object | None = None,
        source_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        actor_context: ActorContext | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._citation_mapper = citation_mapper
        self._coverage_service = coverage_service
        self._source_service = source_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._actor_context = actor_context or ActorContext()
        self._settings = settings

    def with_actor_context(self, actor_context: ActorContext) -> GroundingVerifier:
        return GroundingVerifier(
            self._repository,
            self._policy_adapter,
            citation_mapper=self._citation_mapper,
            coverage_service=self._coverage_service,
            source_service=self._source_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            actor_context=actor_context,
            settings=self._settings,
        )

    def verify(self, request: GroundingVerificationRequest) -> GroundingVerificationRun:
        """Run deterministic grounding verification."""

        verification_id = (
            request.grounding_verification_id or f"grounding-verification-{uuid4().hex}"
        )
        try:
            authorize(
                self._policy_adapter,
                action_type="grounding.verify",
                resource_type=request.target_type,
                resource_id=request.target_id or request.response_id or request.explanation_id,
                scope=request.owner_scope,
                trace_id=request.trace_id or self._actor_context.trace_id,
                actor_id=request.created_by or self._actor_context.actor_id,
                workspace_id=self._actor_context.workspace_id,
                risk_level="low",
                context={
                    "required_source_types": request.required_source_types,
                    "require_evidence": request.require_evidence,
                },
            )
        except PermissionError as exc:
            return _save_run(
                self._repository,
                _run(
                    request,
                    verification_id,
                    "blocked_by_policy",
                    False,
                    0,
                    0,
                    0,
                    0,
                    0.0,
                    [{"code": "policy_denied", "reason": str(exc)}],
                    {},
                ),
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="grounding_verification_started",
            node_type="grounding",
            node_id=verification_id,
            intensity=0.4,
            trace_id=request.trace_id,
            payload={"owner_scope": request.owner_scope, "target_type": request.target_type},
        )
        citation_map = self._citation_map_for_request(request)
        coverage = _coverage_for_request(self._coverage_service, request, citation_map)
        unsupported_count = len(citation_map.unsupported_statement_ids)
        citation_count = len(citation_map.citation_ids)
        checked_count = citation_count + unsupported_count
        required_missing = list(citation_map.missing_source_types)
        if coverage is not None:
            required_missing = list(coverage.missing_source_types)
        grounded = unsupported_count == 0 and not required_missing and citation_count > 0
        threshold = float(getattr(self._settings, "grounding_min_coverage_score", 0.65))
        coverage_score = (
            coverage.coverage_score if coverage is not None else citation_map.coverage_score
        )
        status = _status(grounded, coverage_score, threshold, unsupported_count, required_missing)
        issues = _issues(citation_map, coverage, request)
        run = _run(
            request,
            verification_id,
            status,
            grounded,
            checked_count,
            citation_count,
            unsupported_count,
            citation_count,
            coverage_score,
            issues,
            {
                "citation_map_id": citation_map.citation_map_id,
                "source_coverage_id": coverage.source_coverage_id if coverage else None,
            },
        )
        saved = _save_run(self._repository, run)
        emit_telemetry(
            self._telemetry_service,
            event_type="grounding_verification_completed",
            node_type="grounding",
            node_id=saved.grounding_verification_id,
            intensity=saved.coverage_score,
            trace_id=saved.trace_id,
            payload={"owner_scope": saved.owner_scope, "status": saved.status},
        )
        audit_entry_id = record_grounding_audit(
            self._audit_sink,
            action_type="grounding.verify",
            resource_type="grounding_verification",
            resource_id=saved.grounding_verification_id,
            event_type="grounding_verification_completed",
            trace_id=saved.trace_id,
            actor_context=self._actor_context,
            payload={
                "status": saved.status,
                "grounded": saved.grounded,
                "coverage_score": saved.coverage_score,
                "citation_map_id": saved.result.get("citation_map_id"),
            },
        )
        create_grounding_provenance_link(
            self._provenance_service,
            source_type="grounding_verification",
            source_id=saved.grounding_verification_id,
            target_type="citation_map",
            target_id=str(saved.result.get("citation_map_id"))
            if saved.result.get("citation_map_id")
            else None,
            trace_id=saved.trace_id,
            relation_type="evaluated_by",
            audit_entry_id=audit_entry_id,
        )
        return saved

    def get_verification(self, grounding_verification_id: str) -> GroundingVerificationRun | None:
        get = getattr(self._repository, "get_verification_run", None)
        result = get(grounding_verification_id) if callable(get) else None
        return result if isinstance(result, GroundingVerificationRun) else None

    def list_verification_runs(self, limit: int = 100) -> list[GroundingVerificationRun]:
        list_runs = getattr(self._repository, "list_verification_runs", None)
        result = list_runs(limit=limit) if callable(list_runs) else []
        return [item for item in result if isinstance(item, GroundingVerificationRun)]

    def _citation_map_for_request(self, request: GroundingVerificationRequest) -> Any:
        mapper = self._citation_mapper
        if request.response_id:
            map_response = getattr(mapper, "map_response", None)
            if callable(map_response):
                try:
                    return map_response(
                        request.response_id,
                        request.owner_scope,
                        [str(item) for item in _required_types(request)],
                    )
                except ValueError:
                    if request.text is None:
                        raise
        if request.text:
            map_text = getattr(mapper, "map_text", None)
            if callable(map_text):
                sources = _list_sources(
                    self._source_service,
                    request.owner_scope,
                    trace_id=request.trace_id,
                    limit=500,
                )
                return map_text(
                    text=request.text,
                    trace_id=request.trace_id,
                    owner_scope=request.owner_scope,
                    sources=sources,
                    target_type=request.target_type,
                    target_id=request.target_id or request.explanation_id or request.response_id,
                    required_source_types=[str(item) for item in _required_types(request)],
                    metadata={"grounding_verification_id": request.grounding_verification_id},
                )
        latest = getattr(self._repository, "latest_citation_map", None)
        if callable(latest):
            result = latest(response_id=request.response_id, explanation_id=request.explanation_id)
            if result is not None:
                return result
        raise ValueError("citation_map_unavailable")


def _run(
    request: GroundingVerificationRequest,
    verification_id: str,
    status: str,
    grounded: bool,
    checked_count: int,
    supported_count: int,
    unsupported_count: int,
    citation_count: int,
    coverage_score: float,
    issues: list[dict[str, Any]],
    result: dict[str, Any],
) -> GroundingVerificationRun:
    now = datetime.now(UTC)
    return GroundingVerificationRun(
        grounding_verification_id=verification_id,
        trace_id=request.trace_id,
        response_id=request.response_id,
        explanation_id=request.explanation_id,
        target_type=request.target_type,
        target_id=request.target_id,
        status=status,  # type: ignore[arg-type]
        owner_scope=request.owner_scope,
        grounded=grounded,
        checked_statement_count=checked_count,
        supported_statement_count=supported_count,
        unsupported_statement_count=unsupported_count,
        citation_count=citation_count,
        coverage_score=max(0.0, min(1.0, coverage_score)),
        issues=issues,
        result=result,
        created_by=request.created_by,
        created_at=now,
        completed_at=now,
    )


def _required_types(request: GroundingVerificationRequest) -> list[str]:
    required = [str(item) for item in request.required_source_types]
    if request.require_evidence and "evidence" not in required:
        required.append("evidence")
    if request.require_belief_support and "belief_claim" not in required:
        required.append("belief_claim")
    return required


def _coverage_for_request(
    coverage_service: object | None,
    request: GroundingVerificationRequest,
    citation_map: object,
) -> Any | None:
    report = getattr(coverage_service, "report", None)
    if not callable(report):
        return None
    return report(
        response_id=getattr(citation_map, "response_id", request.response_id),
        explanation_id=request.explanation_id,
        owner_scope=request.owner_scope,
        required_source_types=[str(item) for item in _required_types(request)],
    )


def _status(
    grounded: bool,
    coverage_score: float,
    threshold: float,
    unsupported_count: int,
    missing: list[str],
) -> str:
    if missing:
        return "insufficient_sources"
    if unsupported_count > 0 and coverage_score <= 0:
        return "failed"
    if grounded and coverage_score >= threshold:
        return "passed"
    return "warning" if coverage_score > 0 else "failed"


def _issues(
    citation_map: object,
    coverage: object | None,
    request: GroundingVerificationRequest,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for constraint in getattr(citation_map, "constraints", []) or []:
        issues.append({"code": str(constraint), "severity": "medium"})
    missing = getattr(coverage, "missing_source_types", []) if coverage is not None else []
    for source_type in missing:
        issues.append({"code": f"missing_source_type:{source_type}", "severity": "high"})
    if request.allow_memory_only is False and any(
        "memory" in str(item) for item in getattr(citation_map, "constraints", [])
    ):
        issues.append({"code": "memory_only_support_not_allowed", "severity": "medium"})
    return issues


def _save_run(repository: object, run: GroundingVerificationRun) -> GroundingVerificationRun:
    save = getattr(repository, "save_verification_run", None)
    if callable(save):
        result = save(run)
        if isinstance(result, GroundingVerificationRun):
            return result
    return run


def _list_sources(service: object | None, scope: list[str], **kwargs: Any) -> list[object]:
    list_sources = getattr(service, "list_sources", None)
    if callable(list_sources):
        try:
            from aion_brain.contracts.grounding import GroundingQuery

            result = list_sources(GroundingQuery(scope=scope, **kwargs))
        except TypeError:
            result = list_sources(scope, **kwargs)
        return list(result) if isinstance(result, list) else []
    return []


__all__ = ["GroundingVerifier"]

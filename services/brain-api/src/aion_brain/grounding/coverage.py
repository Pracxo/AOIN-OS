"""Source coverage reporting."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.grounding import (
    GroundingSource,
    GroundingSourceType,
    SourceCoverageReport,
    SourceCoverageStatus,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.grounding.audit import record_grounding_audit


class SourceCoverageService:
    """Build deterministic source coverage reports."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> SourceCoverageService:
        return SourceCoverageService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            actor_context=actor_context,
        )

    def report(
        self,
        response_id: str | None,
        explanation_id: str | None,
        owner_scope: list[str],
        required_source_types: list[str],
    ) -> SourceCoverageReport:
        """Create and persist a coverage report."""

        authorize(
            self._policy_adapter,
            action_type="grounding.coverage.read",
            resource_type="source_coverage",
            resource_id=response_id or explanation_id,
            scope=owner_scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        citations = _list_citations(
            self._repository,
            response_id=response_id,
            explanation_id=explanation_id,
            limit=500,
        )
        sources = _sources_for_citations(self._repository, citations, owner_scope)
        counts = Counter(source.source_type for source in sources)
        required = [cast(GroundingSourceType, item) for item in required_source_types]
        missing = [item for item in required if counts.get(item, 0) == 0]
        weak_refs = [
            source.grounding_source_id
            for source in sources
            if source.trust_level in {"memory_recall", "belief_uncertain", "unverified", "unknown"}
        ]
        strong_refs = [
            source.grounding_source_id
            for source in sources
            if source.trust_level in {"primary", "belief_supported", "system_state"}
        ]
        coverage_score = _coverage_score(citations, required, missing, weak_refs)
        report = SourceCoverageReport(
            source_coverage_id=f"source-coverage-{uuid4().hex}",
            trace_id=_first_trace(citations, sources),
            response_id=response_id,
            explanation_id=explanation_id,
            status=_status(coverage_score, missing),
            owner_scope=owner_scope,
            source_counts={str(key): int(value) for key, value in counts.items()},
            required_source_types=required,
            missing_source_types=missing,
            weak_source_refs=weak_refs,
            strong_source_refs=strong_refs,
            coverage_score=coverage_score,
            recommendations=_recommendations(missing, weak_refs, strong_refs),
            metadata={"citation_count": len(citations), "source_count": len(sources)},
            created_at=datetime.now(UTC),
        )
        saved = _save_report(self._repository, report)
        emit_telemetry(
            self._telemetry_service,
            event_type="source_coverage_report_created",
            node_type="source_coverage",
            node_id=saved.source_coverage_id,
            intensity=saved.coverage_score,
            trace_id=saved.trace_id,
            payload={"owner_scope": owner_scope, "status": saved.status},
        )
        record_grounding_audit(
            self._audit_sink,
            action_type="grounding.coverage.read",
            resource_type="source_coverage",
            resource_id=saved.source_coverage_id,
            event_type="source_coverage_report_created",
            trace_id=saved.trace_id,
            actor_context=self._actor_context,
            payload={
                "response_id": saved.response_id,
                "explanation_id": saved.explanation_id,
                "status": saved.status,
                "coverage_score": saved.coverage_score,
            },
        )
        return saved


def _list_citations(repository: object, **kwargs: Any) -> list[object]:
    list_citations = getattr(repository, "list_citations", None)
    if callable(list_citations):
        result = list_citations(**kwargs)
        if isinstance(result, list):
            return result
    return []


def _sources_for_citations(
    repository: object,
    citations: list[object],
    owner_scope: list[str],
) -> list[GroundingSource]:
    get_source = getattr(repository, "get_source", None)
    sources: list[GroundingSource] = []
    for citation in citations:
        grounding_source_id = getattr(citation, "grounding_source_id", None)
        if callable(get_source) and isinstance(grounding_source_id, str):
            source = get_source(grounding_source_id)
            if isinstance(source, GroundingSource) and _scope_matches(
                source.owner_scope,
                owner_scope,
            ):
                sources.append(source)
    return sources


def _save_report(repository: object, report: SourceCoverageReport) -> SourceCoverageReport:
    save = getattr(repository, "save_coverage_report", None)
    if callable(save):
        result = save(report)
        if isinstance(result, SourceCoverageReport):
            return result
    return report


def _first_trace(citations: list[object], sources: list[GroundingSource]) -> str | None:
    for item in [*citations, *sources]:
        trace_id = getattr(item, "trace_id", None)
        if isinstance(trace_id, str) and trace_id:
            return trace_id
    return None


def _coverage_score(
    citations: list[object],
    required: list[GroundingSourceType],
    missing: list[GroundingSourceType],
    weak_refs: list[str],
) -> float:
    if not citations:
        return 0.0
    base = sum(float(getattr(item, "confidence", 0.0)) for item in citations) / len(citations)
    if required:
        base *= max(0.0, 1.0 - (len(missing) / len(required)))
    if weak_refs and not required:
        base = min(base, 0.6)
    return max(0.0, min(1.0, base))


def _status(score: float, missing: list[GroundingSourceType]) -> SourceCoverageStatus:
    if missing:
        return "failed"
    if score >= 0.65:
        return "passed"
    return "warning" if score > 0 else "failed"


def _recommendations(
    missing: list[GroundingSourceType],
    weak_refs: list[str],
    strong_refs: list[str],
) -> list[str]:
    recommendations: list[str] = []
    if "evidence" in missing or "evidence_chunk" in missing:
        recommendations.append("add_evidence")
    if "belief_claim" in missing:
        recommendations.append("verify_belief_support")
    if weak_refs:
        recommendations.append("avoid_memory_only_claim")
        recommendations.append("mark_low_confidence")
    if not strong_refs:
        recommendations.append("remove_unsupported_statement")
    return list(dict.fromkeys(recommendations))


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(requested_scope))


__all__ = ["SourceCoverageService"]

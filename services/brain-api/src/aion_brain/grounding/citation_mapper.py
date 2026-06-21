"""Deterministic citation mapper."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.citations import (
    CitationCreateRequest,
    CitationRecord,
    ResponseCitationMap,
    ResponseCitationMapStatus,
    UnsupportedStatement,
    UnsupportedStatementSeverity,
)
from aion_brain.contracts.grounding import GroundingSource, GroundingSourceType
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.grounding.audit import (
    create_grounding_provenance_link,
    record_grounding_audit,
)
from aion_brain.grounding.hash import hash_statement
from aion_brain.grounding.redaction import sanitize_payload
from aion_brain.grounding.statement_splitter import StatementSplitter
from aion_brain.grounding.support_checker import SupportChecker


class CitationMapper:
    """Map public response statements to existing grounding sources."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object,
        *,
        citation_service: object | None = None,
        source_service: object | None = None,
        response_service: object | None = None,
        explanation_service: object | None = None,
        splitter: StatementSplitter | None = None,
        support_checker: SupportChecker | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        actor_context: ActorContext | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._citation_service = citation_service
        self._source_service = source_service
        self._response_service = response_service
        self._explanation_service = explanation_service
        self._splitter = splitter or StatementSplitter()
        self._support_checker = support_checker or SupportChecker()
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._actor_context = actor_context or ActorContext()
        self._settings = settings

    def with_actor_context(self, actor_context: ActorContext) -> CitationMapper:
        return CitationMapper(
            self._repository,
            self._policy_adapter,
            citation_service=self._citation_service,
            source_service=self._source_service,
            response_service=self._response_service,
            explanation_service=self._explanation_service,
            splitter=self._splitter,
            support_checker=self._support_checker,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            actor_context=actor_context,
            settings=self._settings,
        )

    def map_response(
        self,
        response_id: str,
        owner_scope: list[str],
        required_source_types: list[str] | None = None,
    ) -> ResponseCitationMap:
        """Build a citation map for a stored response draft."""

        response = _load_by_id(self._response_service, response_id)
        if response is None:
            raise ValueError("response_not_found")
        text = str(getattr(response, "content", ""))
        trace_id = cast(str | None, getattr(response, "trace_id", None))
        sources = self._sources_for_response(response, owner_scope)
        return self.map_text(
            text=text,
            trace_id=trace_id,
            owner_scope=owner_scope,
            sources=sources,
            target_type="response",
            target_id=response_id,
            required_source_types=required_source_types or [],
            metadata={"response_id": response_id},
        )

    def map_text(
        self,
        text: str,
        trace_id: str | None,
        owner_scope: list[str],
        sources: list[GroundingSource],
        target_type: str,
        target_id: str | None,
        required_source_types: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResponseCitationMap:
        """Map arbitrary public text to provided candidate sources."""

        response_id = _response_id_for(target_type, target_id, text)
        required = [cast(GroundingSourceType, item) for item in (required_source_types or [])]
        authorize(
            self._policy_adapter,
            action_type="grounding.map",
            resource_type=target_type,
            resource_id=target_id,
            scope=owner_scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
            context={"required_source_types": required},
        )
        max_statements = int(getattr(self._settings, "grounding_statement_split_max", 100))
        statements = self._splitter.split(text, max_statements)
        citation_ids: list[str] = []
        unsupported_ids: list[str] = []
        constraints: list[str] = []
        source_types_present = {source.source_type for source in sources}
        missing_source_types = [item for item in required if item not in source_types_present]
        for statement in statements:
            check = self._support_checker.check_statement(
                statement,
                sources,
                require_evidence="evidence" in required,
                allow_memory_only=bool(
                    getattr(self._settings, "grounding_allow_memory_only_default", False)
                ),
            )
            if check["supported"]:
                citation = self._create_citation(
                    statement=statement,
                    trace_id=trace_id,
                    response_id=response_id,
                    explanation_id=target_id if target_type == "explanation" else None,
                    sources=sources,
                    check=check,
                    owner_scope=owner_scope,
                )
                citation_ids.append(citation.citation_id)
                continue
            unsupported = self._save_unsupported(
                statement,
                trace_id,
                response_id,
                target_id if target_type == "explanation" else None,
                check,
                required,
                owner_scope,
            )
            unsupported_ids.append(unsupported.unsupported_statement_id)
            constraints.extend(str(item) for item in check.get("issues", []))
        coverage_score = len(citation_ids) / len(statements) if statements else 1.0
        status = _map_status(coverage_score, unsupported_ids, missing_source_types)
        citation_map = ResponseCitationMap(
            citation_map_id=f"citation-map-{uuid4().hex}",
            response_id=response_id,
            trace_id=trace_id or self._actor_context.trace_id,
            status=status,
            grounded=coverage_score >= 1.0 and not missing_source_types,
            citation_ids=citation_ids,
            unsupported_statement_ids=unsupported_ids,
            coverage_score=coverage_score,
            required_source_types=required,
            missing_source_types=missing_source_types,
            constraints=_unique(
                [
                    *constraints,
                    *[f"missing_source_type:{item}" for item in missing_source_types],
                ]
            ),
            metadata=cast(
                dict[str, Any],
                sanitize_payload(
                    {
                        **(metadata or {}),
                        "target_type": target_type,
                        "target_id": target_id,
                        "owner_scope": owner_scope,
                        "statement_count": len(statements),
                    }
                ),
            ),
            created_at=datetime.now(UTC),
        )
        saved = _save_citation_map(self._repository, citation_map)
        emit_telemetry(
            self._telemetry_service,
            event_type="citation_map_created",
            node_type="citation_map",
            node_id=saved.citation_map_id,
            intensity=saved.coverage_score,
            trace_id=saved.trace_id,
            payload={"owner_scope": owner_scope, "status": saved.status},
        )
        audit_entry_id = record_grounding_audit(
            self._audit_sink,
            action_type="grounding.map",
            resource_type="citation_map",
            resource_id=saved.citation_map_id,
            event_type="citation_map_created",
            trace_id=saved.trace_id,
            actor_context=self._actor_context,
            payload={
                "response_id": saved.response_id,
                "status": saved.status,
                "coverage_score": saved.coverage_score,
            },
        )
        create_grounding_provenance_link(
            self._provenance_service,
            source_type="response" if target_type != "explanation" else "explanation",
            source_id=saved.response_id,
            target_type="citation_map",
            target_id=saved.citation_map_id,
            trace_id=saved.trace_id,
            relation_type="produced",
            audit_entry_id=audit_entry_id,
        )
        return saved

    def _sources_for_response(
        self,
        response: object,
        owner_scope: list[str],
    ) -> list[GroundingSource]:
        metadata = getattr(response, "metadata", {})
        trace_id = getattr(response, "trace_id", None)
        refs = _refs_from_payload(metadata)
        for attr in ("evidence_refs", "memory_refs", "grounding_refs"):
            for item in getattr(response, attr, []) or []:
                refs.setdefault(attr, []).append(str(item))
        sources = _list_sources(
            self._source_service,
            owner_scope,
            trace_id=trace_id if isinstance(trace_id, str) else None,
            limit=500,
        )
        if not any(refs.values()):
            return sources
        allowed = set(_flatten(refs))
        return [
            source
            for source in sources
            if source.source_id in allowed
            or source.grounding_source_id in allowed
            or set(
                source.evidence_refs + source.memory_refs + source.belief_refs + source.entity_refs
            )
            & allowed
        ] or sources

    def _create_citation(
        self,
        *,
        statement: str,
        trace_id: str | None,
        response_id: str,
        explanation_id: str | None,
        sources: list[GroundingSource],
        check: dict[str, Any],
        owner_scope: list[str],
    ) -> CitationRecord:
        source = _matching_source(sources, check)
        if source is None:
            raise ValueError("support_source_not_found")
        request = CitationCreateRequest(
            trace_id=trace_id,
            response_id=response_id,
            explanation_id=explanation_id,
            source_type=source.source_type,
            source_id=source.source_id,
            grounding_source_id=source.grounding_source_id,
            citation_type=cast(Any, check.get("citation_type", "source_reference")),
            label=f"{source.title}: {statement[:80]}",
            quote=statement,
            confidence=float(check.get("confidence", 0.5)),
            verified=bool(check.get("support_level") in {"strong", "moderate"}),
            metadata={"owner_scope": owner_scope, "support_level": check.get("support_level")},
        )
        create = getattr(self._citation_service, "create_citation", None)
        if callable(create):
            result = create(request)
            if isinstance(result, CitationRecord):
                return result
        citation = CitationRecord(
            citation_id=request.citation_id or f"citation-{uuid4().hex}",
            trace_id=request.trace_id,
            response_id=request.response_id,
            explanation_id=request.explanation_id,
            source_type=request.source_type,
            source_id=request.source_id,
            grounding_source_id=request.grounding_source_id,
            citation_type=request.citation_type,
            label=request.label,
            quote=request.quote,
            start_char=None,
            end_char=None,
            confidence=request.confidence,
            verified=request.verified,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        return _save_citation(self._repository, citation)

    def _save_unsupported(
        self,
        statement: str,
        trace_id: str | None,
        response_id: str,
        explanation_id: str | None,
        check: dict[str, Any],
        required: list[GroundingSourceType],
        owner_scope: list[str],
    ) -> UnsupportedStatement:
        issues = [str(item) for item in check.get("issues", [])]
        unsupported = UnsupportedStatement(
            unsupported_statement_id=f"unsupported-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            response_id=response_id,
            explanation_id=explanation_id,
            statement_text=statement,
            statement_hash=hash_statement(statement),
            reason=issues[0] if issues else "unsupported_statement",
            severity=_severity_for_issues(issues),
            required_support=[str(item) for item in required] or ["grounding_source"],
            candidate_source_refs=[str(item) for item in check.get("source_refs", [])],
            metadata={"owner_scope": owner_scope, "issues": issues},
            created_at=datetime.now(UTC),
            resolved_at=None,
        )
        saved = _save_unsupported(self._repository, unsupported)
        emit_telemetry(
            self._telemetry_service,
            event_type="unsupported_statement_detected",
            node_type="unsupported_statement",
            node_id=saved.unsupported_statement_id,
            intensity=1.0 if saved.severity in {"high", "critical"} else 0.7,
            trace_id=saved.trace_id,
            payload={"owner_scope": owner_scope, "severity": saved.severity},
        )
        audit_entry_id = record_grounding_audit(
            self._audit_sink,
            action_type="grounding.map",
            resource_type="unsupported_statement",
            resource_id=saved.unsupported_statement_id,
            event_type="unsupported_statement_detected",
            trace_id=saved.trace_id,
            actor_context=self._actor_context,
            payload={"severity": saved.severity, "reason": saved.reason},
        )
        create_grounding_provenance_link(
            self._provenance_service,
            source_type="unsupported_statement",
            source_id=saved.unsupported_statement_id,
            target_type="explanation" if saved.explanation_id else "response",
            target_id=saved.explanation_id or saved.response_id,
            trace_id=saved.trace_id,
            relation_type="referenced",
            audit_entry_id=audit_entry_id,
        )
        return saved


def _load_by_id(service: object | None, object_id: str) -> object | None:
    for name in ("get_response", "get", "get_record"):
        method = getattr(service, name, None)
        if callable(method):
            try:
                return cast(object | None, method(object_id))
            except TypeError:
                continue
    return None


def _refs_from_payload(payload: object) -> dict[str, list[str]]:
    if not isinstance(payload, dict):
        return {}
    refs: dict[str, list[str]] = {}
    for key in ("evidence_refs", "belief_refs", "memory_refs", "entity_refs", "provenance_refs"):
        raw = payload.get(key)
        if isinstance(raw, list):
            refs[key] = [str(item) for item in raw if item]
    return refs


def _flatten(refs: dict[str, list[str]]) -> list[str]:
    values: list[str] = []
    for items in refs.values():
        values.extend(items)
    return values


def _response_id_for(target_type: str, target_id: str | None, text: str) -> str:
    if target_type == "response" and target_id:
        return target_id
    if target_id:
        return target_id
    return f"{target_type}-{hash_statement(text)[:16]}"


def _matching_source(
    sources: list[GroundingSource],
    check: dict[str, Any],
) -> GroundingSource | None:
    ids = set(str(item) for item in check.get("grounding_source_ids", []))
    source_refs = set(str(item) for item in check.get("source_refs", []))
    for source in sources:
        if source.grounding_source_id in ids or source.source_id in source_refs:
            return source
    return sources[0] if sources else None


def _save_citation(repository: object, citation: CitationRecord) -> CitationRecord:
    save = getattr(repository, "save_citation", None)
    if callable(save):
        result = save(citation)
        if isinstance(result, CitationRecord):
            return result
    return citation


def _save_unsupported(repository: object, statement: UnsupportedStatement) -> UnsupportedStatement:
    save = getattr(repository, "save_unsupported", None)
    if callable(save):
        result = save(statement)
        if isinstance(result, UnsupportedStatement):
            return result
    return statement


def _save_citation_map(
    repository: object,
    citation_map: ResponseCitationMap,
) -> ResponseCitationMap:
    save = getattr(repository, "save_citation_map", None)
    if callable(save):
        result = save(citation_map)
        if isinstance(result, ResponseCitationMap):
            return result
    return citation_map


def _list_sources(service: object | None, scope: list[str], **kwargs: Any) -> list[GroundingSource]:
    list_sources = getattr(service, "list_sources", None)
    if callable(list_sources):
        try:
            from aion_brain.contracts.grounding import GroundingQuery

            result = list_sources(GroundingQuery(scope=scope, **kwargs))
        except TypeError:
            result = list_sources(scope, **kwargs)
        if isinstance(result, list):
            return [item for item in result if isinstance(item, GroundingSource)]
    return []


def _map_status(
    coverage_score: float,
    unsupported_ids: list[str],
    missing_source_types: list[GroundingSourceType],
) -> ResponseCitationMapStatus:
    if missing_source_types:
        return "insufficient_sources"
    if not unsupported_ids and coverage_score >= 1.0:
        return "passed"
    if coverage_score > 0:
        return "warning"
    return "failed"


def _severity_for_issues(issues: list[str]) -> UnsupportedStatementSeverity:
    if any(item in {"contradicted_support", "missing_evidence"} for item in issues):
        return "high"
    if "memory_not_truth" in issues:
        return "medium"
    return "low"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = ["CitationMapper"]

"""Grounding source normalization service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.grounding import (
    GroundingQuery,
    GroundingSource,
    GroundingSourceCreateRequest,
    GroundingTrustLevel,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.grounding.audit import record_grounding_audit
from aion_brain.grounding.hash import hash_source_content
from aion_brain.grounding.redaction import sanitize_payload


class GroundingSourceService:
    """Create and read normalized grounding sources."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object,
        *,
        evidence_service: object | None = None,
        belief_service: object | None = None,
        memory_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._evidence_service = evidence_service
        self._belief_service = belief_service
        self._memory_service = memory_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> GroundingSourceService:
        return GroundingSourceService(
            self._repository,
            self._policy_adapter,
            evidence_service=self._evidence_service,
            belief_service=self._belief_service,
            memory_service=self._memory_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            actor_context=actor_context,
        )

    def create_source(self, request: GroundingSourceCreateRequest) -> GroundingSource:
        """Create a policy-gated source record."""

        authorize(
            self._policy_adapter,
            action_type="grounding.source.create",
            resource_type="grounding_source",
            resource_id=request.grounding_source_id or request.source_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level=_risk_from_sensitivity(request.sensitivity),
            context={"source_type": request.source_type, "trust_level": request.trust_level},
        )
        source = GroundingSource(
            grounding_source_id=request.grounding_source_id or f"grounding-source-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            title=request.title,
            summary=request.summary,
            content_hash=request.content_hash or hash_source_content(request.summary),
            sensitivity=request.sensitivity,
            trust_level=request.trust_level,
            evidence_refs=request.evidence_refs,
            belief_refs=request.belief_refs,
            memory_refs=request.memory_refs,
            entity_refs=request.entity_refs,
            provenance_refs=request.provenance_refs,
            owner_scope=request.owner_scope,
            metadata=cast(dict[str, Any], sanitize_payload(request.metadata)),
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        saved = _save_source(self._repository, source)
        emit_telemetry(
            self._telemetry_service,
            event_type="grounding_source_created",
            node_type="grounding",
            node_id=saved.grounding_source_id,
            intensity=0.5,
            trace_id=saved.trace_id,
            payload={"owner_scope": saved.owner_scope, "source_type": saved.source_type},
        )
        record_grounding_audit(
            self._audit_sink,
            action_type="grounding.source.create",
            resource_type="grounding_source",
            resource_id=saved.grounding_source_id,
            event_type="grounding_source_created",
            trace_id=saved.trace_id,
            actor_context=self._actor_context,
            payload={
                "source_type": saved.source_type,
                "source_id": saved.source_id,
                "trust_level": saved.trust_level,
            },
        )
        return saved

    def get_source(self, grounding_source_id: str, scope: list[str]) -> GroundingSource | None:
        """Return one source after policy and scope checks."""

        authorize(
            self._policy_adapter,
            action_type="grounding.source.read",
            resource_type="grounding_source",
            resource_id=grounding_source_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        source = _get_source(self._repository, grounding_source_id)
        if source is None or not _scope_matches(source.owner_scope, scope):
            return None
        return source

    def list_sources(self, query: GroundingQuery) -> list[GroundingSource]:
        """List sources matching a mandatory scope."""

        authorize(
            self._policy_adapter,
            action_type="grounding.source.read",
            resource_type="grounding_source",
            resource_id=None,
            scope=query.scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
            context={"trace_id": query.trace_id},
        )
        return _list_sources(
            self._repository,
            query.scope,
            trace_id=query.trace_id,
            source_type=query.source_type,
            trust_level=query.trust_level,
            include_deleted=query.include_deleted,
            limit=query.limit,
        )

    def build_from_evidence(self, evidence_id: str, scope: list[str]) -> GroundingSource:
        """Build a primary/derived source from an Evidence Vault record."""

        get_evidence = getattr(self._evidence_service, "get_evidence", None)
        evidence = get_evidence(evidence_id, scope) if callable(get_evidence) else None
        if evidence is None:
            raise ValueError("evidence_not_found")
        return self.create_source(
            GroundingSourceCreateRequest(
                trace_id=getattr(evidence, "trace_id", None),
                source_type="evidence",
                source_id=evidence_id,
                title=str(getattr(evidence, "title", evidence_id)),
                summary=str(getattr(evidence, "summary", evidence_id)),
                content_hash=str(
                    getattr(evidence, "content_hash", hash_source_content(evidence_id))
                ),
                sensitivity=cast(Any, getattr(evidence, "sensitivity", "internal")),
                trust_level=(
                    "primary" if getattr(evidence, "source_type", "") != "memory" else "derived"
                ),
                evidence_refs=[evidence_id],
                owner_scope=scope,
                metadata={"source_ref": getattr(evidence, "source_ref", None)},
            )
        )

    def build_from_belief(self, claim_id: str, scope: list[str]) -> GroundingSource:
        """Build a source from a belief claim without treating contradicted claims as strong."""

        get_claim = getattr(self._belief_service, "get_claim", None)
        claim = get_claim(claim_id, scope) if callable(get_claim) else None
        if claim is None:
            raise ValueError("belief_not_found")
        status = str(getattr(claim, "status", "unknown"))
        trust_level: GroundingTrustLevel = "belief_supported"
        if status == "uncertain":
            trust_level = "belief_uncertain"
        elif status == "contradicted":
            trust_level = "unverified"
        text = str(getattr(claim, "claim_text", claim_id))
        return self.create_source(
            GroundingSourceCreateRequest(
                trace_id=getattr(claim, "trace_id", None),
                source_type="belief_claim",
                source_id=claim_id,
                title="Belief claim",
                summary=text,
                content_hash=str(getattr(claim, "claim_hash", hash_source_content(text))),
                sensitivity=cast(Any, getattr(claim, "sensitivity", "internal")),
                trust_level=trust_level,
                evidence_refs=list(getattr(claim, "evidence_refs", [])),
                belief_refs=[claim_id],
                memory_refs=list(getattr(claim, "memory_refs", [])),
                owner_scope=scope,
                metadata={"belief_status": status},
            )
        )

    def build_from_memory(self, memory_id: str, scope: list[str]) -> GroundingSource:
        """Build a weak memory-recall source."""

        get_memory = getattr(self._memory_service, "get", None) or getattr(
            self._memory_service,
            "get_memory",
            None,
        )
        memory = get_memory(memory_id) if callable(get_memory) else None
        if memory is None:
            raise ValueError("memory_not_found")
        text = str(getattr(memory, "summary", memory_id))
        return self.create_source(
            GroundingSourceCreateRequest(
                trace_id=getattr(memory, "source_event_id", None),
                source_type="memory",
                source_id=memory_id,
                title=str(getattr(memory, "memory_type", "memory")),
                summary=text,
                content_hash=hash_source_content(text),
                sensitivity=cast(Any, getattr(memory, "sensitivity", "internal")),
                trust_level="memory_recall",
                memory_refs=[memory_id],
                owner_scope=scope,
                metadata={"memory_recall_is_not_truth": True},
            )
        )


def _save_source(repository: object, source: GroundingSource) -> GroundingSource:
    save = getattr(repository, "save_source", None)
    if callable(save):
        result = save(source)
        if isinstance(result, GroundingSource):
            return result
    return source


def _get_source(repository: object, grounding_source_id: str) -> GroundingSource | None:
    get = getattr(repository, "get_source", None)
    if callable(get):
        result = get(grounding_source_id)
        if result is None or isinstance(result, GroundingSource):
            return result
    return None


def _list_sources(
    repository: object,
    scope: list[str],
    **kwargs: Any,
) -> list[GroundingSource]:
    list_sources = getattr(repository, "list_sources", None)
    if callable(list_sources):
        result = list_sources(scope, **kwargs)
        if isinstance(result, list):
            return [item for item in result if isinstance(item, GroundingSource)]
    return []


def _scope_matches(record_scope: list[str], scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(scope))


def _risk_from_sensitivity(sensitivity: str) -> str:
    if sensitivity == "restricted":
        return "high"
    if sensitivity == "confidential":
        return "medium"
    return "low"


__all__ = ["GroundingSourceService"]

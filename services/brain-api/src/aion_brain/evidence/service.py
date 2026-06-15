"""Policy-gated Evidence Vault service."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.evidence import (
    EvidenceChunk,
    EvidenceIngestRequest,
    EvidenceIngestResponse,
    EvidenceLink,
    EvidenceRecord,
    EvidenceSearchRequest,
    EvidenceSearchResult,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.evidence.chunker import EvidenceChunker
from aion_brain.evidence.content_hash import sha256_text
from aion_brain.evidence.search import search_evidence_records
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.storage.base import ObjectStoreAdapter


class EvidencePolicyDenied(Exception):
    """Raised when policy denies evidence access."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class EvidenceService:
    """Evidence Vault service with deterministic text grounding."""

    def __init__(
        self,
        *,
        evidence_repository: object,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
        object_store: ObjectStoreAdapter | None = None,
        actor_context: ActorContext | None = None,
        chunker: EvidenceChunker | None = None,
    ) -> None:
        self._repository = evidence_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._object_store = object_store
        self._actor_context = actor_context or ActorContext()
        self._chunker = chunker or EvidenceChunker()
        self._enricher = PolicyInputEnricher()

    def with_actor_context(self, actor_context: ActorContext) -> "EvidenceService":
        """Return a service instance sharing dependencies with actor context."""
        return EvidenceService(
            evidence_repository=self._repository,
            policy_adapter=self._policy_adapter,
            telemetry_service=self._telemetry_service,
            object_store=self._object_store,
            actor_context=actor_context,
            chunker=self._chunker,
        )

    def ingest(
        self,
        request: EvidenceIngestRequest,
        actor_context: ActorContext | None = None,
    ) -> EvidenceIngestResponse:
        """Ingest text evidence or metadata-only content refs."""
        context = actor_context or self._actor_context
        self._ensure_allowed(
            "evidence.create",
            "evidence",
            request.evidence_id,
            _risk_from_sensitivity(request.sensitivity),
            request.owner_scope,
            {"source_type": request.source_type, "sensitivity": request.sensitivity},
            context,
        )
        evidence_id = request.evidence_id or f"evidence-{uuid4().hex}"
        now = datetime.now(UTC)
        metadata = _metadata_with_actor_context(request.metadata, context)
        chunks: list[EvidenceChunk] = []
        content_ref: str | None
        if request.content_text:
            content_hash = sha256_text(request.content_text)
            content_ref = f"evidence://{evidence_id}"
            summary = request.summary or _summary_from_text(request.content_text)
            chunks = self._chunker.chunk_text(
                evidence_id,
                request.content_text,
                request.chunk_size_chars,
                request.chunk_overlap_chars,
            )
        else:
            content_hash = sha256_text(request.content_ref or evidence_id)
            content_ref = request.content_ref
            summary = request.summary or "Metadata-only evidence reference."

        evidence = EvidenceRecord(
            evidence_id=evidence_id,
            trace_id=request.trace_id,
            source_type=request.source_type,
            source_ref=request.source_ref,
            owner_scope=request.owner_scope,
            title=request.title,
            summary=summary,
            content_hash=content_hash,
            content_ref=content_ref,
            media_type=request.media_type,
            sensitivity=request.sensitivity,
            confidence=request.confidence,
            metadata=metadata,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        saved = _save_evidence(self._repository, evidence)
        saved_chunks = _save_chunks(self._repository, chunks)
        self._emit("evidence_created", "evidence", saved.evidence_id, 0.5, saved.trace_id, {})
        for chunk in saved_chunks:
            self._emit(
                "evidence_chunk_created",
                "chunk",
                chunk.chunk_id,
                0.4,
                saved.trace_id,
                {"evidence_id": saved.evidence_id},
            )
        return EvidenceIngestResponse(
            ingested=True,
            evidence=saved,
            chunk_count=len(saved_chunks),
            reason=None,
        )

    def get_evidence(self, evidence_id: str, scope: list[str]) -> EvidenceRecord | None:
        """Return evidence after policy and scope checks."""
        evidence = _get_evidence(self._repository, evidence_id)
        if evidence is None or not _scope_matches(evidence.owner_scope, scope):
            return None
        self._ensure_allowed(
            "evidence.read",
            "evidence",
            evidence_id,
            "low",
            scope,
            {"sensitivity": evidence.sensitivity},
            self._actor_context,
        )
        if _restricted_blocked(evidence, self._actor_context):
            return None
        return evidence

    def get_chunks(self, evidence_id: str, scope: list[str]) -> list[EvidenceChunk]:
        """Return evidence chunks after policy and scope checks."""
        evidence = self.get_evidence(evidence_id, scope)
        if evidence is None:
            return []
        return _get_chunks(self._repository, evidence_id)

    def search(self, request: EvidenceSearchRequest) -> list[EvidenceSearchResult]:
        """Search evidence using deterministic lexical matching."""
        self._ensure_allowed(
            "evidence.search",
            "evidence",
            None,
            "low",
            request.scope,
            {"source_types": request.source_types},
            self._actor_context,
        )
        records = [
            record
            for record in _list_evidence(
                self._repository,
                request.scope,
                [str(source_type) for source_type in request.source_types],
            )
            if not _restricted_blocked(record, self._actor_context)
        ]
        chunks_by_id = {
            record.evidence_id: _get_chunks(self._repository, record.evidence_id)
            for record in records
        }
        results = search_evidence_records(
            query=request.query,
            evidence_records=records,
            chunks_by_evidence_id=chunks_by_id,
            limit=request.limit,
            min_score=request.min_score,
        )
        for result in results:
            self._emit(
                "evidence_retrieved",
                "evidence",
                result.evidence.evidence_id,
                result.score,
                result.evidence.trace_id,
                {"chunk_id": result.chunk.chunk_id if result.chunk is not None else None},
            )
        return results

    def link(self, link: EvidenceLink) -> EvidenceLink:
        """Store an evidence link after policy and scope checks."""
        evidence = _get_evidence(self._repository, link.evidence_id)
        if evidence is None:
            raise ValueError("evidence_not_found")
        self._ensure_allowed(
            "evidence.link",
            "evidence",
            link.evidence_id,
            "medium",
            evidence.owner_scope,
            {"target_type": link.target_type, "relation_type": link.relation_type},
            self._actor_context,
        )
        saved = _save_link(self._repository, link)
        self._emit(
            "evidence_linked",
            "evidence",
            saved.evidence_id,
            saved.confidence,
            saved.trace_id,
            {"target_type": saved.target_type, "target_id": saved.target_id},
        )
        return saved

    def list_links(self, evidence_id: str, scope: list[str]) -> list[EvidenceLink]:
        """List evidence links after read policy and scope checks."""
        evidence = self.get_evidence(evidence_id, scope)
        if evidence is None:
            return []
        return _list_links(self._repository, evidence_id)

    def soft_delete(self, evidence_id: str, scope: list[str]) -> bool:
        """Soft-delete evidence after policy and scope checks."""
        evidence = _get_evidence(self._repository, evidence_id)
        if evidence is None or not _scope_matches(evidence.owner_scope, scope):
            return False
        self._ensure_allowed(
            "evidence.delete",
            "evidence",
            evidence_id,
            "high",
            scope,
            {"operation": "soft_delete"},
            self._actor_context,
            approval_present=True,
        )
        deleted = _soft_delete(self._repository, evidence_id)
        if deleted:
            self._emit("evidence_deleted", "evidence", evidence_id, 0.2, evidence.trace_id, {})
        return deleted

    def soft_delete_link(self, link_id: str) -> bool:
        """Soft-delete one evidence link while preserving source evidence."""
        delete_link = getattr(self._repository, "soft_delete_link", None)
        if callable(delete_link):
            return bool(delete_link(link_id))
        return False

    def _ensure_allowed(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        context: dict[str, object],
        actor_context: ActorContext,
        *,
        approval_present: bool = False,
    ) -> None:
        request = PolicyRequest(
            request_id=f"{action_type}-{resource_id or uuid4().hex}",
            trace_id=actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=approval_present,
            requested_permissions=[],
            security_scope=scope,
            context=context,
        )
        decision = self._policy_adapter.authorize(self._enricher.enrich(request, actor_context))
        if not decision.allow:
            raise EvidencePolicyDenied(decision)

    def _emit(
        self,
        event_type: VisualTelemetryEventType,
        node_type: VisualNodeType,
        node_id: str,
        intensity: float,
        trace_id: str | None,
        payload: dict[str, object],
    ) -> None:
        _emit(
            self._telemetry_service,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{node_id}-{event_type}",
                trace_id=trace_id or self._actor_context.trace_id or node_id,
                event_type=event_type,
                node_type=node_type,
                node_id=node_id,
                edge_from=self._actor_context.actor_id,
                edge_to=node_id,
                intensity=max(0.0, min(1.0, intensity)),
                payload=payload,
                created_at=datetime.now(UTC),
            ),
        )


def _save_evidence(repository: object, evidence: EvidenceRecord) -> EvidenceRecord:
    save = getattr(repository, "save_evidence", None)
    if callable(save):
        result = save(evidence)
        if isinstance(result, EvidenceRecord):
            return result
    return evidence


def _save_chunks(repository: object, chunks: list[EvidenceChunk]) -> list[EvidenceChunk]:
    save = getattr(repository, "save_chunks", None)
    if callable(save):
        result = save(chunks)
        if isinstance(result, list) and all(isinstance(chunk, EvidenceChunk) for chunk in result):
            return result
    return chunks


def _get_evidence(repository: object, evidence_id: str) -> EvidenceRecord | None:
    get = getattr(repository, "get_evidence", None)
    if callable(get):
        result = get(evidence_id)
        if result is None or isinstance(result, EvidenceRecord):
            return result
    return None


def _get_chunks(repository: object, evidence_id: str) -> list[EvidenceChunk]:
    get = getattr(repository, "get_chunks", None)
    if callable(get):
        result = get(evidence_id)
        if isinstance(result, list):
            return [chunk for chunk in result if isinstance(chunk, EvidenceChunk)]
    return []


def _list_evidence(
    repository: object,
    scope: list[str],
    source_types: list[str],
) -> list[EvidenceRecord]:
    list_evidence = getattr(repository, "list_evidence", None)
    if callable(list_evidence):
        result = list_evidence(scope, source_types=source_types)
        if isinstance(result, list):
            return [record for record in result if isinstance(record, EvidenceRecord)]
    return []


def _save_link(repository: object, link: EvidenceLink) -> EvidenceLink:
    save = getattr(repository, "save_link", None)
    if callable(save):
        result = save(link)
        if isinstance(result, EvidenceLink):
            return result
    return link


def _list_links(repository: object, evidence_id: str) -> list[EvidenceLink]:
    list_links = getattr(repository, "list_links", None)
    if callable(list_links):
        result = list_links(evidence_id)
        if isinstance(result, list):
            return [link for link in result if isinstance(link, EvidenceLink)]
    return []


def _soft_delete(repository: object, evidence_id: str) -> bool:
    delete = getattr(repository, "soft_delete_evidence", None)
    if callable(delete):
        return bool(delete(evidence_id))
    return False


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _restricted_blocked(evidence: EvidenceRecord, actor_context: ActorContext) -> bool:
    return evidence.sensitivity == "restricted" and "evidence.restricted.read" not in set(
        actor_context.permissions
    )


def _risk_from_sensitivity(sensitivity: str) -> str:
    if sensitivity == "restricted":
        return "high"
    if sensitivity == "confidential":
        return "medium"
    return "low"


def _summary_from_text(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= 280:
        return compact
    return f"{compact[:277]}..."


def _metadata_with_actor_context(
    metadata: dict[str, object],
    actor_context: ActorContext,
) -> dict[str, object]:
    result = dict(metadata)
    if actor_context.actor_id:
        result["actor_id"] = actor_context.actor_id
    if actor_context.workspace_id:
        result["workspace_id"] = actor_context.workspace_id
    return result


def _emit(telemetry_service: object | None, event: VisualTelemetryEvent) -> None:
    if telemetry_service is None:
        return
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
        return
    save = getattr(telemetry_service, "save_visual_telemetry", None)
    if callable(save):
        save(event.trace_id, [event])

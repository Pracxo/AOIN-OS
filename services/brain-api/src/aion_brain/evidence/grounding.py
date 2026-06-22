"""Deterministic source grounding service."""

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.evidence import (
    EvidenceLink,
    EvidenceSearchRequest,
    GroundingClaim,
    GroundingRequest,
    GroundingResponse,
    GroundingVerificationStatus,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.evidence.links import has_contradicting_link
from aion_brain.evidence.service import EvidencePolicyDenied, EvidenceService
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher


class GroundingService:
    """Create deterministic grounding claims from Evidence Vault search results."""

    def __init__(
        self,
        *,
        evidence_service: EvidenceService,
        grounding_repository: object,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._evidence_service = evidence_service
        self._repository = grounding_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()
        self._enricher = PolicyInputEnricher()

    def with_actor_context(self, actor_context: ActorContext) -> "GroundingService":
        """Return a service instance sharing dependencies with actor context."""
        return GroundingService(
            evidence_service=self._evidence_service.with_actor_context(actor_context),
            grounding_repository=self._repository,
            policy_adapter=self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def ground(self, request: GroundingRequest) -> GroundingResponse:
        """Ground statements in available evidence without model calls."""
        self._ensure_allowed(request)
        claims: list[GroundingClaim] = []
        for statement in request.statements:
            search_results = self._evidence_service.search(
                EvidenceSearchRequest(
                    query=statement.statement,
                    scope=request.scope,
                    source_types=[],
                    limit=50,
                    min_score=request.min_score,
                )
            )
            if request.evidence_ids:
                allowed = set(request.evidence_ids)
                search_results = [
                    result for result in search_results if result.evidence.evidence_id in allowed
                ]
            selected = search_results[: request.limit_per_statement]
            evidence_refs = _unique(result.evidence.evidence_id for result in selected)
            chunk_refs = _unique(
                result.chunk.chunk_id for result in selected if result.chunk is not None
            )
            score = max((result.score for result in selected), default=0.0)
            links = _links_for_evidence_ids(self._repository, evidence_refs, "contradicts")
            status = _status(score, bool(chunk_refs), links)
            claim = GroundingClaim(
                claim_id=f"claim-{statement.statement_id}-{uuid4().hex}",
                trace_id=request.trace_id,
                statement=statement.statement,
                evidence_refs=evidence_refs,
                chunk_refs=chunk_refs,
                score=score,
                verification_status=status,
                rationale=_rationale(status, score),
                created_at=datetime.now(UTC),
            )
            saved = _save_claim(self._repository, claim)
            claims.append(saved)
            _emit_grounding(self._telemetry_service, saved)
        return GroundingResponse(
            trace_id=request.trace_id,
            claims=claims,
            created_at=datetime.now(UTC),
        )

    def _ensure_allowed(self, request: GroundingRequest) -> None:
        policy_request = PolicyRequest(
            request_id=f"evidence-ground-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type="evidence.ground",
            resource_type="evidence",
            resource_id=None,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=request.scope,
            context={"statement_count": len(request.statements)},
        )
        decision = self._policy_adapter.authorize(
            self._enricher.enrich(policy_request, self._actor_context)
        )
        if not decision.allow:
            raise EvidencePolicyDenied(decision)


def _status(
    score: float,
    has_chunk_refs: bool,
    contradicting_links: list[EvidenceLink],
) -> GroundingVerificationStatus:
    if contradicting_links and score >= 0.45:
        return "contradicted"
    if score >= 0.45 and has_chunk_refs:
        return "supported"
    return "insufficient_evidence"


def _rationale(status: GroundingVerificationStatus, score: float) -> str:
    if status == "supported":
        return f"Statement has deterministic lexical support with score {score:.2f}."
    if status == "contradicted":
        return f"Selected evidence has an explicit contradicts link with score {score:.2f}."
    return f"Insufficient overlapping evidence; deterministic score {score:.2f}."


def _save_claim(repository: object, claim: GroundingClaim) -> GroundingClaim:
    save = getattr(repository, "save_grounding_claim", None)
    if callable(save):
        result = save(claim)
        if isinstance(result, GroundingClaim):
            return result
    return claim


def _links_for_evidence_ids(
    repository: object,
    evidence_ids: list[str],
    relation_type: str,
) -> list[EvidenceLink]:
    list_links = getattr(repository, "list_links_for_evidence_ids", None)
    if callable(list_links):
        result = list_links(evidence_ids, relation_type=relation_type)
        if isinstance(result, list):
            links = [link for link in result if isinstance(link, EvidenceLink)]
            if has_contradicting_link(links):
                return links
    return []


def _unique(values: Iterable[str | None]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _emit_grounding(telemetry_service: object | None, claim: GroundingClaim) -> None:
    if telemetry_service is None:
        return
    event = VisualTelemetryEvent(
        telemetry_id=f"telemetry-{claim.claim_id}-evidence_grounded",
        trace_id=claim.trace_id or claim.claim_id,
        event_type="evidence_grounded",
        node_type="claim",
        node_id=claim.claim_id,
        edge_from=claim.evidence_refs[0] if claim.evidence_refs else None,
        edge_to=claim.claim_id,
        intensity=claim.score,
        payload={"verification_status": claim.verification_status},
        created_at=datetime.now(UTC),
    )
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
        return
    save = getattr(telemetry_service, "save_visual_telemetry", None)
    if callable(save):
        save(event.trace_id, [event])

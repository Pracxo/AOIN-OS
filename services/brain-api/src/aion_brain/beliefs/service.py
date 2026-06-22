"""Belief claim lifecycle service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.beliefs.normalizer import hash_normalized_claim, normalize_claim_text
from aion_brain.beliefs.repository import BeliefRepository
from aion_brain.contracts.beliefs import (
    BeliefClaim,
    BeliefClaimCreateRequest,
    BeliefClaimStatus,
    BeliefRelationType,
    BeliefRevision,
    BeliefSourceType,
    BeliefSupport,
    BeliefSupportType,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry


class BeliefService:
    """Create, read, revise, and soft-delete belief claims."""

    def __init__(
        self,
        belief_repository: BeliefRepository,
        policy_adapter: object,
        *,
        audit_ledger: object | None = None,
        provenance_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = belief_repository
        self._policy_adapter = policy_adapter
        self._audit_ledger = audit_ledger
        self._provenance_service = provenance_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def create_claim(self, request: BeliefClaimCreateRequest) -> BeliefClaim:
        """Create or return one explicit belief claim."""
        authorize(
            self._policy_adapter,
            action_type="belief.claim.create",
            resource_type="belief_claim",
            resource_id=request.claim_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"source_type": request.source_type},
        )
        normalized = normalize_claim_text(request.claim_text)
        claim_hash = hash_normalized_claim(normalized)
        duplicate = self._repository.find_duplicate(
            claim_hash,
            request.source_type,
            request.source_id,
        )
        if duplicate is not None:
            return duplicate
        now = datetime.now(UTC)
        status = _initial_status(
            request.confidence,
            request.evidence_refs,
            _setting_float(self._settings, "belief_min_supported_confidence", 0.65),
        )
        claim = BeliefClaim(
            claim_id=request.claim_id or f"belief-claim-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            claim_text=request.claim_text,
            normalized_claim=normalized,
            claim_hash=claim_hash,
            claim_type=request.claim_type,
            status=status,
            confidence=request.confidence,
            sensitivity=request.sensitivity,
            owner_scope=request.owner_scope,
            source_type=request.source_type,
            source_id=request.source_id,
            evidence_refs=list(request.evidence_refs),
            memory_refs=list(request.memory_refs),
            graph_refs=list(request.graph_refs),
            response_refs=list(request.response_refs),
            metadata=dict(request.metadata),
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            observed_at=request.observed_at or now,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        stored = self._repository.save_claim(claim)
        for support in _supports_for_claim(stored):
            self._repository.save_support(support)
        self._record_audit(stored)
        self._record_provenance(stored)
        emit_telemetry(
            self._telemetry_service,
            event_type="belief_claim_created",
            node_type="claim",
            node_id=stored.claim_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "status": stored.status},
        )
        return stored

    def get_claim(self, claim_id: str, scope: list[str]) -> BeliefClaim | None:
        """Return one claim visible to scope."""
        authorize(
            self._policy_adapter,
            action_type="belief.claim.read",
            resource_type="belief_claim",
            resource_id=claim_id,
            scope=scope,
        )
        claim = self._repository.get_claim(claim_id)
        if claim is None or not _scope_matches(claim.owner_scope, scope):
            return None
        return claim

    def revise_claim(
        self,
        claim_id: str,
        to_status: str,
        new_confidence: float,
        reason: str,
        created_by: str | None = None,
    ) -> BeliefRevision:
        """Revise one claim status and confidence."""
        claim = self._require_claim(claim_id)
        authorize(
            self._policy_adapter,
            action_type="belief.claim.update",
            resource_type="belief_claim",
            resource_id=claim_id,
            scope=claim.owner_scope,
            trace_id=claim.trace_id,
            actor_id=created_by,
            risk_level="medium",
            context={"to_status": to_status},
        )
        revision = _revision_for_claim(
            claim,
            to_status=to_status,
            new_confidence=new_confidence,
            reason=reason,
            created_by=created_by,
        )
        self._repository.save_revision(revision)
        self._repository.save_claim(
            claim.model_copy(
                update={
                    "status": revision.to_status,
                    "confidence": revision.new_confidence,
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="belief_claim_revised",
            node_type="claim",
            node_id=claim_id,
            intensity=revision.new_confidence,
            trace_id=claim.trace_id,
            payload={"from_status": claim.status, "to_status": revision.to_status},
        )
        return revision

    def soft_delete_claim(
        self,
        claim_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft-delete one claim."""
        claim = self._require_claim(claim_id)
        authorize(
            self._policy_adapter,
            action_type="belief.claim.delete",
            resource_type="belief_claim",
            resource_id=claim_id,
            scope=claim.owner_scope,
            actor_id=actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        deleted = claim.model_copy(
            update={
                "deleted_at": datetime.now(UTC),
                "status": "archived",
                "updated_at": datetime.now(UTC),
                "metadata": {**claim.metadata, "delete_reason": reason, "deleted_by": actor_id},
            }
        )
        self._repository.save_claim(deleted)
        return True

    def _require_claim(self, claim_id: str) -> BeliefClaim:
        claim = self._repository.get_claim(claim_id)
        if claim is None:
            raise ValueError("belief_claim_not_found")
        return claim

    def _record_audit(self, claim: BeliefClaim) -> None:
        record = getattr(self._audit_ledger, "record_event", None)
        if not callable(record):
            return
        try:
            record(
                "belief_claim_created",
                claim.claim_id,
                {
                    "claim_id": claim.claim_id,
                    "status": claim.status,
                    "confidence": claim.confidence,
                },
            )
        except Exception:
            return

    def _record_provenance(self, claim: BeliefClaim) -> None:
        create = getattr(self._provenance_service, "create_link", None)
        if not callable(create):
            return
        try:
            create(
                source_type=claim.source_type,
                source_id=claim.source_id or claim.claim_id,
                target_type="belief_claim",
                target_id=claim.claim_id,
                relation_type="derived_from",
                metadata={"claim_status": claim.status},
            )
        except Exception:
            return


def _initial_status(
    confidence: float,
    evidence_refs: list[str],
    supported_threshold: float,
) -> BeliefClaimStatus:
    if evidence_refs and confidence >= supported_threshold:
        return "supported"
    return "uncertain"


def _supports_for_claim(claim: BeliefClaim) -> list[BeliefSupport]:
    now = datetime.now(UTC)
    supports: list[BeliefSupport] = []
    for evidence_ref in claim.evidence_refs:
        supports.append(
            _support(
                claim.claim_id,
                "evidence",
                "evidence",
                evidence_ref,
                "grounded_by",
                min(1.0, claim.confidence + 0.1),
                now,
            )
        )
    for memory_ref in claim.memory_refs:
        supports.append(
            _support(claim.claim_id, "memory", "memory", memory_ref, "references", 0.45, now)
        )
    for graph_ref in claim.graph_refs:
        supports.append(
            _support(claim.claim_id, "graph", "graph", graph_ref, "references", 0.45, now)
        )
    for response_ref in claim.response_refs:
        supports.append(
            _support(
                claim.claim_id,
                "reasoning",
                "dialogue_response",
                response_ref,
                "references",
                0.4,
                now,
            )
        )
    return supports


def _support(
    claim_id: str,
    support_type: str,
    source_type: str,
    source_id: str,
    relation_type: str,
    strength: float,
    created_at: datetime,
) -> BeliefSupport:
    return BeliefSupport(
        support_id=f"belief-support-{uuid4().hex}",
        claim_id=claim_id,
        support_type=cast(BeliefSupportType, support_type),
        source_type=cast(BeliefSourceType, source_type),
        source_id=source_id,
        relation_type=cast(BeliefRelationType, relation_type),
        strength=strength,
        confidence=strength,
        metadata={"auto_created": True},
        created_at=created_at,
        deleted_at=None,
    )


def _revision_for_claim(
    claim: BeliefClaim,
    *,
    to_status: str,
    new_confidence: float,
    reason: str,
    created_by: str | None,
) -> BeliefRevision:
    return BeliefRevision(
        revision_id=f"belief-revision-{uuid4().hex}",
        claim_id=claim.claim_id,
        trace_id=claim.trace_id,
        from_status=claim.status,
        to_status=cast(BeliefClaimStatus, to_status),
        previous_confidence=claim.confidence,
        new_confidence=new_confidence,
        reason=reason,
        evidence_refs=claim.evidence_refs,
        metadata={},
        created_by=created_by,
        created_at=datetime.now(UTC),
    )


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))


def _setting_float(settings: object | None, name: str, default: float) -> float:
    return float(getattr(settings, name, default))

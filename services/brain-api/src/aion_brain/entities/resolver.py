"""Deterministic entity resolver."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.entities import (
    EntityCreateRequest,
    EntityExtractMentionsRequest,
    EntityMention,
    EntityMentionCreateRequest,
    EntityQuery,
    EntityRecord,
    EntityResolutionCandidate,
    EntityResolutionRequest,
    EntityResolutionResult,
    ReferenceEndpointType,
    ReferenceLink,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.entities.mention_extractor import EntityMentionExtractor
from aion_brain.entities.normalizer import lexical_tokens, normalize_entity_name
from aion_brain.entities.repository import EntityRepository


class EntityResolver:
    """Resolve mentions into canonical entity references without model calls."""

    def __init__(
        self,
        repository: EntityRepository,
        policy_adapter: object,
        *,
        mention_extractor: EntityMentionExtractor | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._mention_extractor = mention_extractor or EntityMentionExtractor()
        self._telemetry_service = telemetry_service
        self._settings = settings

    def extract_mentions(
        self,
        request: EntityExtractMentionsRequest,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[EntityMentionCreateRequest]:
        """Policy-gated deterministic mention extraction."""
        authorize(
            self._policy_adapter,
            action_type="entity.extract_mentions",
            resource_type="entity_mention",
            resource_id=request.source_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            risk_level="low",
        )
        return self._mention_extractor.extract(request)

    def create_mention(
        self,
        request: EntityMentionCreateRequest,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> EntityMention:
        """Persist one explicit mention through the resolver boundary."""
        authorize(
            self._policy_adapter,
            action_type="entity.mention.create",
            resource_type="entity_mention",
            resource_id=request.mention_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            risk_level="low",
        )
        if request.entity_id is not None:
            entity = self._repository.get_entity(request.entity_id)
            if entity is None or not set(entity.owner_scope).intersection(request.owner_scope):
                raise ValueError("entity_not_found")
        mention = EntityMention(
            mention_id=request.mention_id or f"entity-mention-{uuid4().hex}",
            trace_id=request.trace_id,
            entity_id=request.entity_id,
            source_type=request.source_type,
            source_id=request.source_id,
            mention_text=request.mention_text,
            normalized_mention=normalize_entity_name(request.mention_text),
            mention_type=request.mention_type,
            start_char=request.start_char,
            end_char=request.end_char,
            confidence=request.confidence,
            resolved=request.entity_id is not None,
            resolution_score=1.0 if request.entity_id is not None else None,
            owner_scope=request.owner_scope,
            metadata=dict(request.metadata),
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        stored = self._repository.save_mention(mention)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_mention_created",
            node_type="mention",
            node_id=stored.mention_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"resolved": stored.resolved, "source_type": stored.source_type},
        )
        return stored

    def list_mentions(
        self,
        entity_id: str,
        scope: list[str],
        *,
        limit: int = 100,
    ) -> list[EntityMention]:
        """List mentions for one entity through a policy boundary."""
        entity = self._repository.get_entity(entity_id)
        if entity is None or not set(entity.owner_scope).intersection(scope):
            raise ValueError("entity_not_found")
        authorize(
            self._policy_adapter,
            action_type="entity.mention.read",
            resource_type="entity_mention",
            resource_id=entity_id,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_mentions(scope=scope, entity_ids=[entity_id], limit=limit)

    def get_resolution_result(
        self,
        resolution_run_id: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> EntityResolutionResult | None:
        """Return a stored resolution run when visible to the requested scope."""
        authorize(
            self._policy_adapter,
            action_type="entity.resolve",
            resource_type="entity_resolution",
            resource_id=resolution_run_id,
            scope=scope,
            actor_id=actor_id,
            workspace_id=workspace_id,
            risk_level="low",
        )
        result = self._repository.get_resolution_result(resolution_run_id)
        if result is None or not set(result.owner_scope).intersection(scope):
            return None
        return result

    def resolve(self, request: EntityResolutionRequest) -> EntityResolutionResult:
        """Resolve supplied or extracted mentions against the canonical registry."""
        authorize(
            self._policy_adapter,
            action_type="entity.resolve",
            resource_type="entity_resolution",
            resource_id=request.resolution_run_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"dry_run": request.dry_run},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_resolution_started",
            node_type="resolution",
            node_id=request.resolution_run_id or "entity-resolution-pending",
            intensity=0.5,
            trace_id=request.trace_id,
            payload={"dry_run": request.dry_run},
        )
        mentions = self._mentions_for_request(request)
        threshold = _setting_float(self._settings, "entity_resolution_min_score", 0.72)
        create_missing = request.create_missing_entities or _setting_bool(
            self._settings,
            "entity_resolution_create_missing_default",
            False,
        )
        candidates: dict[str, list[EntityResolutionCandidate]] = {}
        created_mentions: list[EntityMention] = []
        created_entities: list[EntityRecord] = []
        created_links: list[ReferenceLink] = []
        resolved_count = 0
        for mention_request in mentions:
            ranked = self._rank_candidates(mention_request)
            candidates[mention_request.mention_text] = ranked
            best = ranked[0] if ranked and ranked[0].score >= threshold else None
            entity = best.entity if best is not None else None
            if entity is None and create_missing and not request.dry_run:
                entity = self._create_missing_entity(request, mention_request)
                created_entities.append(entity)
            if entity is not None:
                resolved_count += 1
            if not request.dry_run:
                mention = self._persist_mention(mention_request, entity, best)
                created_mentions.append(mention)
                if (
                    entity is not None
                    and request.auto_link
                    and request.source_type
                    and request.source_id
                ):
                    created_links.append(self._create_reference_link(request, entity, mention))
        now = datetime.now(UTC)
        result = EntityResolutionResult(
            resolution_run_id=request.resolution_run_id or f"entity-resolution-{uuid4().hex}",
            status="dry_run" if request.dry_run else "completed",
            owner_scope=request.owner_scope,
            source_type=request.source_type,
            source_id=request.source_id,
            mentions_seen=len(mentions),
            mentions_resolved=resolved_count,
            mentions_unresolved=max(0, len(mentions) - resolved_count),
            entities_created=len(created_entities),
            reference_links_created=len(created_links),
            candidates=candidates,
            created_mentions=created_mentions,
            created_entities=created_entities,
            created_links=created_links,
            constraints=["dry_run_no_persistence"] if request.dry_run else [],
            metadata={"threshold": threshold, "create_missing_entities": create_missing},
            created_at=now,
            completed_at=now,
        )
        stored = self._repository.save_resolution_result(result)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_resolution_completed",
            node_type="resolution",
            node_id=stored.resolution_run_id,
            intensity=0.8 if stored.mentions_resolved else 0.4,
            trace_id=request.trace_id,
            payload={
                "mentions_seen": stored.mentions_seen,
                "mentions_resolved": stored.mentions_resolved,
                "dry_run": request.dry_run,
            },
        )
        return stored

    def _mentions_for_request(
        self,
        request: EntityResolutionRequest,
    ) -> list[EntityMentionCreateRequest]:
        if request.mentions:
            return request.mentions
        if not request.text or not request.source_type or not request.source_id:
            return []
        return self._mention_extractor.extract(
            EntityExtractMentionsRequest(
                source_type=request.source_type,
                source_id=request.source_id,
                text=request.text,
                owner_scope=request.owner_scope,
                trace_id=request.trace_id,
            )
        )

    def _rank_candidates(
        self,
        mention: EntityMentionCreateRequest,
    ) -> list[EntityResolutionCandidate]:
        normalized = normalize_entity_name(mention.mention_text)
        query_result = self._repository.query_entities(
            EntityQuery(
                query=normalized,
                scope=mention.owner_scope,
                statuses=["active", "proposed"],
                include_merged=False,
                limit=50,
            )
        )
        candidates: list[EntityResolutionCandidate] = []
        for entity in query_result.entities:
            score, reasons, matched_aliases = _score_entity_match(entity, mention)
            if score <= 0:
                continue
            candidates.append(
                EntityResolutionCandidate(
                    entity=entity,
                    score=score,
                    reasons=reasons,
                    matched_aliases=matched_aliases,
                    confidence=min(1.0, (score + entity.confidence + mention.confidence) / 3),
                )
            )
        entity_aliases = self._repository.list_aliases(normalized_alias=normalized)
        for alias in entity_aliases:
            alias_entity = self._repository.get_entity(alias.entity_id)
            if alias_entity is None or not set(alias_entity.owner_scope).intersection(
                mention.owner_scope
            ):
                continue
            if any(
                candidate.entity.entity_id == alias_entity.entity_id for candidate in candidates
            ):
                continue
            score = min(1.0, 0.55 + (0.25 * alias.confidence) + (0.1 * mention.confidence))
            candidates.append(
                EntityResolutionCandidate(
                    entity=alias_entity,
                    score=score,
                    reasons=["alias_match"],
                    matched_aliases=[alias.alias],
                    confidence=min(1.0, (score + alias_entity.confidence + alias.confidence) / 3),
                )
            )
        return sorted(
            candidates,
            key=lambda candidate: (-candidate.score, candidate.entity.entity_id),
        )

    def _create_missing_entity(
        self,
        request: EntityResolutionRequest,
        mention: EntityMentionCreateRequest,
    ) -> EntityRecord:
        authorize(
            self._policy_adapter,
            action_type="entity.create",
            resource_type="entity",
            resource_id=None,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"source": "entity_resolution"},
        )
        now = datetime.now(UTC)
        create = EntityCreateRequest(
            trace_id=request.trace_id,
            canonical_name=mention.mention_text,
            entity_type="unknown",
            owner_scope=request.owner_scope,
            confidence=mention.confidence,
            sensitivity="internal",
            metadata={"created_from_resolution_run": request.resolution_run_id},
            created_by=request.created_by,
        )
        normalized = normalize_entity_name(create.canonical_name)
        entity = EntityRecord(
            entity_id=create.entity_id or f"entity-{uuid4().hex}",
            trace_id=create.trace_id,
            canonical_name=create.canonical_name,
            normalized_name=normalized,
            entity_type=create.entity_type,
            status="proposed",
            owner_scope=create.owner_scope,
            concept_refs=[],
            evidence_refs=[],
            memory_refs=[],
            belief_refs=[],
            graph_refs=[],
            confidence=create.confidence,
            sensitivity=create.sensitivity,
            metadata=dict(create.metadata),
            created_by=create.created_by,
            created_at=now,
            updated_at=now,
            merged_into_entity_id=None,
            archived_at=None,
            deleted_at=None,
        )
        return self._repository.save_entity(entity)

    def _persist_mention(
        self,
        mention_request: EntityMentionCreateRequest,
        entity: EntityRecord | None,
        best: EntityResolutionCandidate | None,
    ) -> EntityMention:
        mention = EntityMention(
            mention_id=mention_request.mention_id or f"entity-mention-{uuid4().hex}",
            trace_id=mention_request.trace_id,
            entity_id=entity.entity_id if entity is not None else None,
            source_type=mention_request.source_type,
            source_id=mention_request.source_id,
            mention_text=mention_request.mention_text,
            normalized_mention=normalize_entity_name(mention_request.mention_text),
            mention_type=mention_request.mention_type if entity is not None else "unresolved",
            start_char=mention_request.start_char,
            end_char=mention_request.end_char,
            confidence=mention_request.confidence,
            resolved=entity is not None,
            resolution_score=best.score if best is not None else None,
            owner_scope=mention_request.owner_scope,
            metadata=dict(mention_request.metadata),
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        stored = self._repository.save_mention(mention)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_mention_created",
            node_type="mention",
            node_id=stored.mention_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            edge_from=stored.source_id,
            edge_to=stored.entity_id,
            payload={"resolved": stored.resolved},
        )
        return stored

    def _create_reference_link(
        self,
        request: EntityResolutionRequest,
        entity: EntityRecord,
        mention: EntityMention,
    ) -> ReferenceLink:
        link = ReferenceLink(
            reference_link_id=f"reference-link-{uuid4().hex}",
            trace_id=request.trace_id,
            source_type=_reference_endpoint_for_source(request.source_type),
            source_id=request.source_id or mention.source_id,
            target_type="entity",
            target_id=entity.entity_id,
            relation_type="refers_to",
            entity_id=entity.entity_id,
            concept_id=None,
            confidence=mention.resolution_score or mention.confidence,
            evidence_refs=[],
            metadata={"mention_id": mention.mention_id},
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        stored = self._repository.save_reference_link(link)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_reference_resolved",
            node_type="reference",
            node_id=stored.reference_link_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            edge_from=stored.source_id,
            edge_to=stored.target_id,
            payload={"entity_id": entity.entity_id},
        )
        return stored


def _score_entity_match(
    entity: EntityRecord,
    mention: EntityMentionCreateRequest,
) -> tuple[float, list[str], list[str]]:
    normalized = normalize_entity_name(mention.mention_text)
    score = 0.0
    reasons: list[str] = []
    matched_aliases: list[str] = []
    if normalized == entity.normalized_name:
        score += 0.6
        reasons.append("exact_name")
    elif lexical_tokens(normalized).intersection(lexical_tokens(entity.normalized_name)):
        score += 0.25
        reasons.append("token_overlap")
    if set(entity.owner_scope).intersection(mention.owner_scope):
        score += 0.15
        reasons.append("scope_overlap")
    refs = _metadata_refs(mention.metadata)
    if refs and _entity_refs(entity).intersection(refs):
        score += 0.15
        reasons.append("reference_overlap")
    score += 0.1 * mention.confidence
    score += 0.1 * entity.confidence
    return min(1.0, score), reasons, matched_aliases


def _metadata_refs(metadata: dict[str, object]) -> set[str]:
    refs: set[str] = set()
    for key in ("evidence_refs", "memory_refs", "belief_refs", "graph_refs", "concept_refs"):
        value = metadata.get(key)
        if isinstance(value, list):
            refs.update(str(item) for item in value)
    return refs


def _entity_refs(entity: EntityRecord) -> set[str]:
    return set(
        entity.evidence_refs
        + entity.memory_refs
        + entity.belief_refs
        + entity.graph_refs
        + entity.concept_refs
    )


def _reference_endpoint_for_source(source_type: str | None) -> ReferenceEndpointType:
    if source_type in {
        "dialogue_message",
        "response",
        "evidence",
        "evidence_chunk",
        "memory",
        "belief_claim",
        "graph_node",
        "graph_edge",
        "trace",
        "command",
        "workflow",
        "task",
        "audit_entry",
        "system",
    }:
        return cast(ReferenceEndpointType, source_type)
    return "system"


def _setting_float(settings: object | None, name: str, default: float) -> float:
    value = getattr(settings, name, default)
    if isinstance(value, int | float):
        return float(value)
    return default


def _setting_bool(settings: object | None, name: str, default: bool) -> bool:
    value = getattr(settings, name, default)
    return bool(value)

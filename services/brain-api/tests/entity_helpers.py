from __future__ import annotations

from types import SimpleNamespace

from aion_brain.concepts.repository import ConceptRepository
from aion_brain.concepts.service import ConceptService
from aion_brain.contracts.entities import EntityCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.entities.aliases import EntityAliasService
from aion_brain.entities.mention_extractor import EntityMentionExtractor
from aion_brain.entities.merge import EntityMergeService
from aion_brain.entities.query import EntityQueryService
from aion_brain.entities.references import ReferenceLinkService
from aion_brain.entities.repository import EntityRepository
from aion_brain.entities.resolver import EntityResolver
from aion_brain.entities.service import EntityService
from aion_brain.entities.split import EntitySplitService


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied_for_test",
            constraints=["test"],
            audit_level="high",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def entity_bundle(policy: object | None = None) -> SimpleNamespace:
    repository = EntityRepository()
    concept_repository = ConceptRepository()
    policy_adapter = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    settings = SimpleNamespace(
        entity_resolution_min_score=0.72,
        entity_resolution_create_missing_default=False,
        entity_merge_requires_approval=True,
    )
    entity_service = EntityService(repository, policy_adapter, telemetry_service=telemetry)
    return SimpleNamespace(
        repository=repository,
        concept_repository=concept_repository,
        policy=policy_adapter,
        telemetry=telemetry,
        settings=settings,
        entity_service=entity_service,
        entity_query_service=EntityQueryService(entity_service),
        concept_service=ConceptService(
            concept_repository,
            policy_adapter,
            telemetry_service=telemetry,
        ),
        alias_service=EntityAliasService(repository, policy_adapter, telemetry_service=telemetry),
        reference_service=ReferenceLinkService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
        ),
        extractor=EntityMentionExtractor(),
        resolver=EntityResolver(
            repository,
            policy_adapter,
            mention_extractor=EntityMentionExtractor(),
            telemetry_service=telemetry,
            settings=settings,
        ),
        merge_service=EntityMergeService(
            repository,
            policy_adapter,
            telemetry_service=telemetry,
            settings=settings,
        ),
        split_service=EntitySplitService(repository, policy_adapter, telemetry_service=telemetry),
    )


def create_entity(bundle: SimpleNamespace, name: str = "Test Reference") -> object:
    return bundle.entity_service.create(
        EntityCreateRequest(
            canonical_name=name,
            entity_type="generic",
            owner_scope=["workspace:main"],
            confidence=0.8,
        )
    )

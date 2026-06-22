from __future__ import annotations

import pytest

from aion_brain.contracts.entities import (
    EntityAliasCreateRequest,
    EntityDeleteRequest,
    EntityMergeProposalCreateRequest,
    EntityProposalDecisionRequest,
    EntityQuery,
    ReferenceLinkCreateRequest,
)
from tests.entity_helpers import DenyPolicy, create_entity, entity_bundle


def test_entity_service_create_query_alias_and_reference() -> None:
    bundle = entity_bundle()
    entity = create_entity(bundle, "Test Reference")

    alias = bundle.alias_service.add_alias(
        EntityAliasCreateRequest(entity_id=entity.entity_id, alias="Test Ref"),
        ["workspace:main"],
    )
    link = bundle.reference_service.create_link(
        ReferenceLinkCreateRequest(
            source_type="memory",
            source_id="memory-1",
            target_type="entity",
            target_id=entity.entity_id,
            entity_id=entity.entity_id,
        ),
        ["workspace:main"],
    )
    result = bundle.entity_service.query(
        EntityQuery(query="test ref", scope=["workspace:main"], limit=10)
    )

    assert alias.normalized_alias == "test ref"
    assert link.target_id == entity.entity_id
    assert result.entities[0].entity_id == entity.entity_id


def test_entity_soft_delete_does_not_hard_delete() -> None:
    bundle = entity_bundle()
    entity = create_entity(bundle, "Soft Delete Reference")

    deleted = bundle.entity_service.soft_delete(
        entity.entity_id,
        ["workspace:main"],
        EntityDeleteRequest(reason="test"),
    )

    assert deleted.deleted_at is not None
    assert bundle.repository.get_entity(entity.entity_id) is not None


def test_entity_merge_requires_explicit_approval() -> None:
    bundle = entity_bundle()
    primary = create_entity(bundle, "Primary Reference")
    duplicate = create_entity(bundle, "Duplicate Reference")
    proposal = bundle.merge_service.propose(
        EntityMergeProposalCreateRequest(
            primary_entity_id=primary.entity_id,
            duplicate_entity_id=duplicate.entity_id,
            reason="similar references",
        ),
        ["workspace:main"],
    )

    with pytest.raises(PermissionError):
        bundle.merge_service.approve(
            proposal.merge_proposal_id,
            ["workspace:main"],
            EntityProposalDecisionRequest(reason="no approval", approval_present=False),
        )

    approved = bundle.merge_service.approve(
        proposal.merge_proposal_id,
        ["workspace:main"],
        EntityProposalDecisionRequest(reason="approved", approval_present=True),
    )

    assert approved.status == "completed"
    assert bundle.repository.get_entity(duplicate.entity_id).status == "merged"


def test_policy_deny_blocks_entity_create() -> None:
    bundle = entity_bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        create_entity(bundle)

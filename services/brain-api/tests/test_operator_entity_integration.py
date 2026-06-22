from __future__ import annotations

from typing import cast

from aion_brain.contracts.entities import (
    EntityMentionCreateRequest,
    EntityMergeProposalCreateRequest,
    EntityRecord,
    EntitySplitProposalCreateRequest,
)
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from tests.dialogue_helpers import AllowPolicy
from tests.entity_helpers import create_entity, entity_bundle


def test_operator_action_center_surfaces_entity_items() -> None:
    bundle = entity_bundle()
    primary = cast(EntityRecord, create_entity(bundle, "Primary Reference"))
    duplicate = cast(EntityRecord, create_entity(bundle, "Duplicate Reference"))
    mention = bundle.resolver.create_mention(
        EntityMentionCreateRequest(
            source_type="generic",
            source_id="source-1",
            mention_text="Unresolved Reference",
            confidence=0.8,
            owner_scope=["workspace:main"],
        )
    )
    merge = bundle.merge_service.propose(
        EntityMergeProposalCreateRequest(
            primary_entity_id=primary.entity_id,
            duplicate_entity_id=duplicate.entity_id,
            reason="same generic reference",
        ),
        ["workspace:main"],
    )
    split = bundle.split_service.propose(
        EntitySplitProposalCreateRequest(
            entity_id=primary.entity_id,
            reason="too broad",
        ),
        ["workspace:main"],
    )
    action_center = ActionCenterService(
        OperatorRepository(),
        policy_adapter=AllowPolicy(),
        entity_repository=bundle.repository,
        entity_merge_service=bundle.merge_service,
        entity_split_service=bundle.split_service,
    )

    items = action_center.build_action_items(["workspace:main"])
    source_ids = {item.source_id for item in items}

    assert mention.mention_id in source_ids
    assert merge.merge_proposal_id in source_ids
    assert split.split_proposal_id in source_ids


def test_operator_queue_builder_counts_entity_queues() -> None:
    bundle = entity_bundle()
    entity = cast(EntityRecord, create_entity(bundle))
    bundle.resolver.create_mention(
        EntityMentionCreateRequest(
            source_type="generic",
            source_id="source-1",
            mention_text="Unresolved Reference",
            confidence=0.8,
            owner_scope=["workspace:main"],
        )
    )
    bundle.split_service.propose(
        EntitySplitProposalCreateRequest(entity_id=entity.entity_id, reason="too broad"),
        ["workspace:main"],
    )
    builder = QueueSummaryBuilder(
        entity_repository=bundle.repository,
        entity_split_service=bundle.split_service,
    )

    queues = builder.build_queues(["workspace:main"])
    unresolved = next(queue for queue in queues if queue.title == "Unresolved Entity Mentions")
    splits = next(queue for queue in queues if queue.title == "Entity Split Proposals")

    assert unresolved.metadata["available"] is True
    assert unresolved.metadata["item_count"] == 1
    assert splits.metadata["available"] is True
    assert splits.metadata["item_count"] == 1

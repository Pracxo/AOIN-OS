from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.entities import EntityCreateRequest, EntityMergeProposal


def test_entity_contract_rejects_hidden_reasoning_text() -> None:
    with pytest.raises(ValidationError):
        EntityCreateRequest(
            canonical_name="hidden_reasoning marker",
            owner_scope=["workspace:main"],
        )


def test_entity_contract_rejects_sensitive_identity_metadata() -> None:
    with pytest.raises(ValidationError):
        EntityCreateRequest(
            canonical_name="Generic Reference",
            owner_scope=["workspace:main"],
            metadata={"race": "not allowed"},
        )


def test_entity_merge_proposal_rejects_self_merge() -> None:
    with pytest.raises(ValidationError):
        EntityMergeProposal(
            merge_proposal_id="merge-1",
            primary_entity_id="entity-1",
            duplicate_entity_id="entity-1",
            status="proposed",
            score=0.9,
            reason="same entity",
        )

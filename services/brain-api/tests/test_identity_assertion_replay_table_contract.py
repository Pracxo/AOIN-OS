from __future__ import annotations

import inspect

from aion_brain.contracts.identity_assertion_replay import TABLE_NAME
from aion_brain.production_auth import identity_assertion_replay_repository as repository_module
from aion_brain.production_auth.identity_assertion_replay_repository import (
    aion_identity_assertion_replay_claims,
    identity_assertion_replay_metadata,
)


def test_replay_table_has_only_authorized_columns_and_indexes() -> None:
    assert aion_identity_assertion_replay_claims.name == TABLE_NAME
    assert aion_identity_assertion_replay_claims.metadata is identity_assertion_replay_metadata
    assert set(aion_identity_assertion_replay_claims.c.keys()) == {
        "replay_key",
        "issuer_fingerprint",
        "assertion_fingerprint",
        "claimed_at",
        "assertion_expires_at",
        "retain_until",
        "created_at",
    }
    assert aion_identity_assertion_replay_claims.c.replay_key.primary_key
    assert {index.name for index in aion_identity_assertion_replay_claims.indexes} == {
        "ix_aion_identity_assertion_replay_retain_until",
        "ix_aion_identity_assertion_replay_claimed_at",
        "ix_aion_identity_assertion_replay_assertion_expires_at",
    }


def test_replay_repository_does_not_reuse_idempotency_table() -> None:
    source = inspect.getsource(repository_module)
    assert "idempotency" not in source
    assert "aion_idempotency_records" not in source
    claim_source = inspect.getsource(repository_module.IdentityAssertionReplayRepository.claim)
    assert "delete(" not in claim_source
    assert "merge(" not in source

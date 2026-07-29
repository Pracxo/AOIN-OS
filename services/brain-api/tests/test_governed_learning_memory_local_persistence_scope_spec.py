from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION224_AUTHORIZATION_SCOPE,
    AION224_SOURCE_SCOPE,
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
)
from test_governed_learning_memory_program_authorization import REPO_ROOT, load_json


def test_aion224_scope_is_exact_and_source_state_matches_program_state() -> None:
    program = load_json("docs/governed-learning-memory/program-ledger.json")
    record = next(
        x
        for x in load_json("docs/governed-learning-memory/authorization-ledger.json")["records"]
        if x["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    assert (
        record["authorization_scope"] == AION224_AUTHORIZATION_SCOPE
        and record["authorized_source_scope"] == AION224_SOURCE_SCOPE
    )
    for relative in AION224_SOURCE_SCOPE:
        if relative.endswith("__init__.py"):
            continue
        exists = (REPO_ROOT / relative).exists()
        if program["program_state"] in {
            IMPLEMENTED_PENDING_CLOSEOUT_STATE,
            ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
            ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
            CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
        }:
            assert exists, relative
        else:
            assert not exists, relative

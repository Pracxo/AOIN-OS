from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_continual_learning_authorization_validator_passes() -> None:
    auth227.validate_continual_learning_pilot_authorization(REPO_ROOT)


def test_conditional_authorization_is_exact_and_sole_active() -> None:
    _, ledger = auth227.validate_ledgers(REPO_ROOT)
    record = auth227.record_by_id(ledger["records"], auth227.NEXT_AUTHORIZATION_ID)
    auth227.validate_authorization_record(record)
    if ledger["active_glm_implementation_authorization_count"] == 0:
        assert ledger["active_authorizations"] == []
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_closed_by_task"] == "AION-229"
    else:
        assert ledger["active_authorizations"] == [auth227.NEXT_AUTHORIZATION_ID]

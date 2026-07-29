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
    assert ledger["active_authorizations"] == [auth227.NEXT_AUTHORIZATION_ID]

from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion225_authorization_is_closed_and_non_reusable() -> None:
    _, ledger = auth227.validate_ledgers(REPO_ROOT)
    record = auth227.record_by_id(ledger["records"], auth227.CURRENT_AUTHORIZATION_ID)
    auth227.validate_aion225_closeout(record)
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_consumed_by_prs"] == [142, 143]

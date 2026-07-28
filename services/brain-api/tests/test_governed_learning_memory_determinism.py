from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context


def test_dry_run_transaction_fingerprint_is_deterministic_for_same_inputs():
    first = sample_transaction_context(transaction_id="promotion-transaction-deterministic")
    second = sample_transaction_context(transaction_id="promotion-transaction-deterministic")

    assert first.result.result_fingerprint == second.result.result_fingerprint
    assert first.record.journal_record_fingerprint == second.record.journal_record_fingerprint

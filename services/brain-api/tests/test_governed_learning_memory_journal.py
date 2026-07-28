from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context


def test_in_memory_journal_is_copy_on_write_and_idempotent():
    context = sample_transaction_context()
    updated = context.journal.with_transaction(context.record)

    assert updated is context.journal
    assert context.journal.transaction_by_id(context.result.transaction_id) == context.record
    assert context.journal.records[0].persistent_write_applied is False

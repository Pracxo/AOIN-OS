from __future__ import annotations

import time

from test_governed_learning_memory_contracts import sample_transaction_context


def test_single_candidate_dry_run_stays_within_local_performance_budget():
    started = time.perf_counter()
    context = sample_transaction_context(transaction_id="promotion-transaction-performance")
    elapsed = time.perf_counter() - started

    assert context.result.result_fingerprint
    assert elapsed < 3.0

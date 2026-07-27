from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from public_research_pilot_test_helpers import run_simulation


def test_four_deterministic_sessions_can_run_without_shared_state() -> None:
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = tuple(pool.map(lambda _: run_simulation().status, range(4)))
    assert statuses == ("completed", "completed", "completed", "completed")

from __future__ import annotations

import time

from public_research_pilot_test_helpers import run_simulation


def test_deterministic_pilot_finishes_quickly() -> None:
    started = time.perf_counter()
    run_simulation()
    assert time.perf_counter() - started < 2.0

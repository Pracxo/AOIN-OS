from __future__ import annotations

import time

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_secure_runtime_fixture_performance_smoke() -> None:
    started = time.perf_counter()
    fixture = secure_runtime_fixture()
    elapsed = time.perf_counter() - started

    assert fixture.dispatch.status.value == "simulated"
    assert elapsed < 2.0

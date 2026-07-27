from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_boundary_flag_remains_disabled() -> None:
    result = run_simulation()
    assert result.session.background_execution is False
    assert result.runtime_effect is False

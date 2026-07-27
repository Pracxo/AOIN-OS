from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_deterministic_fake_backends_replay_same_fingerprint() -> None:
    assert run_simulation().result_fingerprint == run_simulation().result_fingerprint

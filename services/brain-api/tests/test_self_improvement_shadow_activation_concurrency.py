"""AION-181 concurrent validation tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    SHADOW_ACTIVATION_REASON_CODES,
    validate_activation_candidate,
)


def test_parallel_candidate_validation_is_stateless(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)

    def validate(_: int) -> str:
        return validate_activation_candidate(ctx["candidate"], now=NOW).fingerprint

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(validate, range(32)))
    assert len(set(results)) == 1
    assert SHADOW_ACTIVATION_REASON_CODES == tuple(SHADOW_ACTIVATION_REASON_CODES)

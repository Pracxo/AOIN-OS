"""AION-178 CI-safe performance smoke tests."""

from __future__ import annotations

import time

from test_self_improvement_shadow_contracts import (
    NOW,
    make_bundle,
    make_manifest,
    make_observation,
    make_reference,
)

from aion_brain.self_improvement.shadow_mode import evaluate_shadow_metrics
from aion_brain.self_improvement.shadow_pipeline import (
    generate_shadow_hypotheses,
    mine_shadow_failure_patterns,
)
from aion_brain.self_improvement.shadow_redaction import validate_shadow_safe_value


def test_shadow_performance_smoke_is_ci_safe() -> None:
    start = time.monotonic()
    for index in range(10_000):
        make_reference(f"shadow-ref-{index}")
    for index in range(5_000):
        validate_shadow_safe_value({"metric": index, "summary": "Retrieval ranking"})
    observations = tuple(make_observation(f"shadow-observation-{index}") for index in range(10))
    for _ in range(2_000):
        evaluate_shadow_metrics(observations)
    for _ in range(1_000):
        mine_shadow_failure_patterns(observations, maximum_patterns=10, created_at=NOW)
    patterns = mine_shadow_failure_patterns(observations, maximum_patterns=10, created_at=NOW)
    for _ in range(1_000):
        generate_shadow_hypotheses(patterns, maximum_hypotheses=10, created_at=NOW)
    manifest = make_manifest()
    for _ in range(500):
        make_bundle(manifest=manifest)

    assert time.monotonic() - start < 30.0

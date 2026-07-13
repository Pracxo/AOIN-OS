from __future__ import annotations

import time
from datetime import UTC, datetime

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthPolicyRequest,
)
from aion_brain.production_auth import ProductionAuthCoreService
from aion_brain.production_auth.canonical import canonical_json_bytes, sha256_fingerprint


def test_canonical_serialization_performance_smoke() -> None:
    payload = {
        "schema_version": "production-auth-core/v1",
        "items": [
            {"field": f"value-{index}", "runtime_enabled": False}
            for index in range(250)
        ],
    }

    started = time.perf_counter()
    encoded = canonical_json_bytes(payload)
    elapsed = time.perf_counter() - started

    assert encoded
    assert elapsed < 2.0


def test_fingerprint_and_blocked_policy_performance_smoke() -> None:
    service = ProductionAuthCoreService(
        ProductionAuthCoreConfig(),
        clock=lambda: datetime(2026, 7, 13, tzinfo=UTC),
        id_factory=lambda prefix: f"{prefix}-perf",
    )
    request = ProductionAuthPolicyRequest(
        request_id="request-perf",
        requested_operation="policy_evaluation_preview",
    )
    payload = {"runtime_enabled": False, "reason_codes": ["production_auth_runtime_disabled"]}

    started = time.perf_counter()
    for _ in range(1000):
        assert sha256_fingerprint(payload)
    fingerprint_elapsed = time.perf_counter() - started

    started = time.perf_counter()
    for _ in range(1000):
        assert service.evaluate_policy(request).outcome == "blocked"
    policy_elapsed = time.perf_counter() - started

    assert fingerprint_elapsed < 5.0
    assert policy_elapsed < 10.0

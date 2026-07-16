from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthPolicyRequest,
)
from aion_brain.production_auth import ProductionAuthCoreService
from aion_brain.production_auth.reason_codes import REQUIRED_REASON_CODES

FIXED_NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)


def test_concurrent_status_reads_do_not_share_mutable_state_or_enable_runtime() -> None:
    service = ProductionAuthCoreService(
        ProductionAuthCoreConfig(),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-concurrent",
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(lambda _: service.status(), range(32)))

    assert {status.runtime_enabled for status in statuses} == {False}
    assert {status.fingerprint for status in statuses} == {statuses[0].fingerprint}
    assert len({id(status.metadata) for status in statuses}) == len(statuses)

    try:
        statuses[0].metadata["leak"] = "blocked"
    except TypeError:
        pass
    assert "leak" not in statuses[1].metadata


def test_concurrent_policy_evaluations_remain_blocked_and_deterministic() -> None:
    service = ProductionAuthCoreService(
        ProductionAuthCoreConfig(),
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-concurrent",
    )
    request = ProductionAuthPolicyRequest(
        request_id="request-concurrent",
        requested_operation="policy_evaluation_preview",
        metadata={"request_kind": "concurrency"},
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        decisions = list(executor.map(lambda _: service.evaluate_policy(request), range(32)))

    assert {decision.outcome for decision in decisions} == {"blocked"}
    assert {decision.runtime_effect for decision in decisions} == {False}
    assert {decision.fingerprint for decision in decisions} == {decisions[0].fingerprint}
    assert tuple(decisions[0].reason_codes) == REQUIRED_REASON_CODES
    assert "request_kind" not in decisions[0].metadata

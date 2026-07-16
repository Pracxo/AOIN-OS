from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_boundary import ProductionAuthRequestIdentityBoundary

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def test_concurrent_boundary_builds_do_not_leak_identity_state() -> None:
    boundary = ProductionAuthRequestIdentityBoundary(clock=lambda: FIXED_NOW)

    async def build(index: int) -> tuple[str, bool, bool]:
        bundle = await boundary.build_bundle(
            RequestContext(
                request_id=f"request-{index}",
                trace_id=f"trace-{index}",
                correlation_id=f"corr-{index}",
                actor_id=f"actor-{index}",
                method="GET",
                path="/health",
                started_at=FIXED_NOW,
            )
        )
        return (
            bundle.identity_context.request_id,
            bundle.identity_context.authenticated,
            bundle.identity_context.runtime_effect,
        )

    async def run_all() -> list[tuple[str, bool, bool]]:
        return list(await asyncio.gather(*(build(index) for index in range(40))))

    results = asyncio.run(run_all())

    assert len({request_id for request_id, _, _ in results}) == 40
    assert all(authenticated is False for _, authenticated, _ in results)
    assert all(runtime_effect is False for _, _, runtime_effect in results)

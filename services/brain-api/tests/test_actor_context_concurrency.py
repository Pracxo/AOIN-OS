"""AION-160 actor-context concurrency and isolation tests."""

from concurrent.futures import ThreadPoolExecutor

from aion_brain.contracts.actor_context_resolution import ActorContextResolutionInput
from aion_brain.production_auth.actor_context import ProductionAuthActorContextResolver


def test_concurrent_non_development_resolutions_remain_isolated_and_anonymous() -> None:
    resolver = ProductionAuthActorContextResolver()

    def resolve(index: int) -> tuple[str | None, str | None, tuple[str, ...], str | None]:
        bundle = resolver.resolve(
            ActorContextResolutionInput(
                request_id=f"request-{index}",
                trace_id=f"trace-{index}",
                correlation_id=f"corr-{index}",
            )
        )
        return (
            bundle.actor_context.actor_id,
            bundle.actor_context.workspace_id,
            tuple(bundle.actor_context.permissions),
            bundle.actor_context.correlation_id,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(resolve, range(24)))

    assert all(actor_id is None for actor_id, _, _, _ in results)
    assert all(workspace_id is None for _, workspace_id, _, _ in results)
    assert all(permissions == () for _, _, permissions, _ in results)
    assert {correlation_id for *_, correlation_id in results} == {
        f"corr-{index}" for index in range(24)
    }

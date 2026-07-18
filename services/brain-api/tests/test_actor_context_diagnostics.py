"""AION-160 actor-context diagnostic tests."""

from aion_brain.production_auth.actor_context import ProductionAuthActorContextResolver


def test_kernel_container_exposes_safe_actor_context_resolver_diagnostics() -> None:
    resolver = ProductionAuthActorContextResolver()
    snapshot = resolver.diagnostic_snapshot(
        development_simulation_active=False
    )

    assert snapshot.actor_context_trust_boundary_remediated is True
    assert snapshot.actor_context_resolution_state == "implemented_fail_closed"
    assert snapshot.non_development_identity_headers_ignored is True
    assert snapshot.request_identity_context_precedence is True
    assert snapshot.request_context_correlation_projection is True
    assert snapshot.request_context_identity_metadata_ignored is True
    assert snapshot.authenticated_actor_context_enabled is False
    assert snapshot.identity_verification_enabled is False
    assert snapshot.authenticated_requests_enabled is False
    assert snapshot.production_auth_runtime_enabled is False
    assert snapshot.runtime_no_go_status is True

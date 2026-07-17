"""Fail-closed production actor-context resolver."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from aion_brain.contracts.actor_context_resolution import (
    DEVELOPMENT_REASON_CODES,
    INVALID_REQUEST_IDENTITY_REASON_CODES,
    REQUEST_IDENTITY_REASON_CODES,
    REQUIRED_REASON_CODES,
    ActorContextResolutionBundle,
    ActorContextResolutionInput,
    ActorContextResolutionReasonCode,
    ActorContextResolutionSource,
    utc_now,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.production_auth.actor_context_evidence import (
    build_actor_context_resolution_bundle,
    build_actor_context_resolution_diagnostic_snapshot,
)


class ProductionAuthActorContextResolver:
    """Resolve route ActorContext without trusting production identity headers."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[str], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory or (lambda prefix: f"{prefix}-{uuid4().hex}")

    def resolve(
        self,
        resolution_input: ActorContextResolutionInput,
    ) -> ActorContextResolutionBundle:
        """Resolve an ActorContext from structured safe primitives only."""

        try:
            if resolution_input.development_simulation_enabled:
                return self._development_bundle(resolution_input)
            if resolution_input.request_identity_context_present:
                if resolution_input.request_identity_context_valid:
                    return self._request_identity_disabled_bundle(resolution_input)
                return self._anonymous_bundle(
                    resolution_input,
                    source="anonymous_fail_closed",
                    reason_codes=INVALID_REQUEST_IDENTITY_REASON_CODES,
                    resolution_failed=True,
                    failure_reason="request_identity_context_invalid",
                )
            return self._anonymous_bundle(
                resolution_input,
                source="anonymous_fail_closed",
                reason_codes=REQUIRED_REASON_CODES,
            )
        except Exception:
            return self._anonymous_bundle(
                ActorContextResolutionInput(
                    request_id=resolution_input.request_id,
                    trace_id=resolution_input.trace_id,
                    correlation_id=resolution_input.correlation_id,
                    request_identity_context_present=(
                        resolution_input.request_identity_context_present
                    ),
                    request_identity_context_valid=False,
                    development_simulation_enabled=False,
                    metadata={"failure_path": "resolver_exception_fail_closed"},
                ),
                source="anonymous_fail_closed",
                reason_codes=INVALID_REQUEST_IDENTITY_REASON_CODES,
                resolution_failed=True,
                failure_reason="actor_context_resolution_failed_closed",
            )

    def diagnostic_snapshot(
        self,
        *,
        development_simulation_active: bool = False,
    ) -> object:
        """Return process-safe actor-context diagnostics."""

        return build_actor_context_resolution_diagnostic_snapshot(
            development_simulation_active=development_simulation_active,
            clock=self._clock,
            id_factory=self._id_factory,
        )

    def _development_bundle(
        self,
        resolution_input: ActorContextResolutionInput,
    ) -> ActorContextResolutionBundle:
        actor_context = ActorContext(
            actor_id=resolution_input.development_actor_id,
            actor_type="user",
            workspace_id=resolution_input.development_workspace_id,
            roles=list(resolution_input.development_roles),
            permissions=list(resolution_input.development_permissions),
            security_scope=list(resolution_input.development_security_scope),
            correlation_id=resolution_input.correlation_id,
            trace_id=resolution_input.trace_id,
            dev_mode=True,
        )
        return build_actor_context_resolution_bundle(
            resolution_input=resolution_input,
            actor_context=actor_context,
            source="development_simulation",
            reason_codes=DEVELOPMENT_REASON_CODES,
            clock=self._clock,
            id_factory=self._id_factory,
        )

    def _request_identity_disabled_bundle(
        self,
        resolution_input: ActorContextResolutionInput,
    ) -> ActorContextResolutionBundle:
        return self._anonymous_bundle(
            resolution_input,
            source="request_identity_disabled",
            reason_codes=REQUEST_IDENTITY_REASON_CODES,
        )

    def _anonymous_bundle(
        self,
        resolution_input: ActorContextResolutionInput,
        *,
        source: ActorContextResolutionSource,
        reason_codes: tuple[ActorContextResolutionReasonCode, ...],
        resolution_failed: bool = False,
        failure_reason: str | None = None,
    ) -> ActorContextResolutionBundle:
        actor_context = ActorContext(
            actor_id=None,
            actor_type=None,
            workspace_id=None,
            roles=[],
            permissions=[],
            security_scope=[],
            correlation_id=resolution_input.correlation_id,
            trace_id=resolution_input.trace_id,
            dev_mode=False,
        )
        return build_actor_context_resolution_bundle(
            resolution_input=resolution_input,
            actor_context=actor_context,
            source=source,
            reason_codes=reason_codes,
            resolution_failed=resolution_failed,
            failure_reason=failure_reason,
            clock=self._clock,
            id_factory=self._id_factory,
        )


__all__ = ["ProductionAuthActorContextResolver"]

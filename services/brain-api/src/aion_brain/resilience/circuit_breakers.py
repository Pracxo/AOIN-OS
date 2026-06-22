"""Circuit breaker service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.resilience import CircuitBreaker
from aion_brain.policy.base import PolicyAdapter
from aion_brain.resilience._shared import authorize, emit_resilience_event
from aion_brain.resilience.repository import ResilienceRepository


class CircuitBreakerService:
    """Policy-gated generic circuit breaker registry."""

    def __init__(
        self,
        repository: ResilienceRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_breaker(self, breaker: CircuitBreaker) -> CircuitBreaker:
        """Create or replace a circuit breaker."""
        authorize(
            self._policy_adapter,
            "resilience.circuit_breaker.create",
            breaker.owner_scope,
            resource_type="circuit_breaker",
            resource_id=breaker.name,
            risk_level="medium",
        )
        now = datetime.now(UTC)
        return self._repository.save_circuit_breaker(
            breaker.model_copy(
                update={
                    "created_at": breaker.created_at or now,
                    "updated_at": now,
                }
            )
        )

    def get_breaker(self, name: str) -> CircuitBreaker | None:
        """Return one breaker by name."""
        authorize(
            self._policy_adapter,
            "resilience.circuit_breaker.read",
            ["workspace:main"],
            resource_type="circuit_breaker",
            resource_id=name,
        )
        return self._repository.get_circuit_breaker(name)

    def list_breakers(
        self,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[CircuitBreaker]:
        """List circuit breakers."""
        authorize(
            self._policy_adapter,
            "resilience.circuit_breaker.read",
            ["workspace:main"],
            context={"status": status, "target_type": target_type},
        )
        return self._repository.list_circuit_breakers(status=status, target_type=target_type)

    def record_success(self, name: str) -> CircuitBreaker:
        """Record one successful call."""
        breaker = self._required(name)
        if breaker.status == "disabled":
            return breaker
        updates: dict[str, Any] = {
            "success_count": breaker.success_count + 1,
            "updated_at": datetime.now(UTC),
        }
        if breaker.status == "half_open":
            updates.update(
                {
                    "status": cast(Any, "closed"),
                    "failure_count": 0,
                    "closed_at": datetime.now(UTC),
                    "opened_at": None,
                    "half_opened_at": None,
                }
            )
        saved = self._repository.save_circuit_breaker(breaker.model_copy(update=updates))
        if breaker.status == "half_open" and saved.status == "closed":
            self._emit("circuit_breaker_closed", saved, 0.5)
        return saved

    def record_failure(self, name: str, reason: str | None = None) -> CircuitBreaker:
        """Record one failed call and open the circuit when threshold is reached."""
        breaker = self._required(name)
        if breaker.status == "disabled":
            return breaker
        now = datetime.now(UTC)
        failure_count = breaker.failure_count + 1
        status = breaker.status
        updates: dict[str, Any] = {
            "failure_count": failure_count,
            "last_failure_at": now,
            "updated_at": now,
            "metadata": {**breaker.metadata, "last_failure_reason": reason or "failure"},
        }
        if status == "half_open" or failure_count >= breaker.failure_threshold:
            updates.update(
                {
                    "status": cast(Any, "open"),
                    "opened_at": now,
                    "half_opened_at": None,
                }
            )
        saved = self._repository.save_circuit_breaker(breaker.model_copy(update=updates))
        if saved.status == "open" and breaker.status != "open":
            self._emit("circuit_breaker_opened", saved, 1.0)
        return saved

    def allow_call(self, name: str, now: datetime | None = None) -> bool:
        """Return whether a call can proceed under breaker state."""
        breaker = self._required(name)
        if breaker.status in {"closed", "disabled"}:
            return True
        current = now or datetime.now(UTC)
        if breaker.status == "open":
            opened_at = _aware(breaker.opened_at) or current
            if current >= opened_at + timedelta(seconds=breaker.recovery_timeout_seconds):
                updated = self._repository.save_circuit_breaker(
                    breaker.model_copy(
                        update={
                            "status": cast(Any, "half_open"),
                            "half_opened_at": current,
                            "success_count": 0,
                            "updated_at": current,
                        }
                    )
                )
                self._emit("circuit_breaker_half_opened", updated, 0.8)
                return True
            return False
        if breaker.status == "half_open":
            return breaker.success_count < breaker.half_open_max_calls
        return False

    def reset(self, name: str, actor_id: str | None, reason: str) -> CircuitBreaker:
        """Reset one breaker to closed."""
        authorize(
            self._policy_adapter,
            "resilience.circuit_breaker.update",
            ["workspace:main"],
            actor_id=actor_id,
            resource_type="circuit_breaker",
            resource_id=name,
            risk_level="medium",
            context={"reason": reason},
        )
        breaker = self._required(name)
        saved = self._repository.save_circuit_breaker(
            breaker.model_copy(
                update={
                    "status": cast(Any, "closed"),
                    "failure_count": 0,
                    "success_count": 0,
                    "opened_at": None,
                    "half_opened_at": None,
                    "closed_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "metadata": {**breaker.metadata, "reset_reason": reason},
                }
            )
        )
        self._emit("circuit_breaker_reset", saved, 0.5)
        return saved

    def _required(self, name: str) -> CircuitBreaker:
        breaker = self._repository.get_circuit_breaker(name)
        if breaker is None:
            raise AIONNotFoundException("circuit_breaker_not_found")
        return breaker

    def _emit(self, event_type: str, breaker: CircuitBreaker, intensity: float) -> None:
        emit_resilience_event(
            self._telemetry_service,
            event_type=event_type,
            node_type="circuit_breaker",
            node_id=breaker.circuit_breaker_id,
            intensity=intensity,
            payload={"name": breaker.name, "status": breaker.status},
        )


def _aware(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)

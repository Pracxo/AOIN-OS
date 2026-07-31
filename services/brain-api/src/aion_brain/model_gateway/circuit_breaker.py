"""Local deterministic circuit-breaker state."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.model_gateway import (
    DETERMINISTIC_PROVIDER_ID,
    MAXIMUM_CIRCUIT_BREAKER_RECORDS,
    ModelCircuitBreakerRecord,
    ModelCircuitBreakerState,
    ModelGatewayCircuitBreakerStatus,
    ensure_gateway_utc,
)


def closed_circuit_state(model_id: str) -> ModelCircuitBreakerState:
    """Return the default closed state for a reference model."""

    return ModelCircuitBreakerState(
        provider_id=DETERMINISTIC_PROVIDER_ID,
        model_id=model_id,
        status=ModelGatewayCircuitBreakerStatus.closed,
        routing_allowed=True,
    )


class InMemoryModelCircuitBreakerRepository:
    """Copy-on-write circuit-breaker repository with explicit transitions only."""

    def __init__(self) -> None:
        self._states: dict[str, ModelCircuitBreakerState] = {}
        self._records: dict[str, ModelCircuitBreakerRecord] = {}

    def state_for_model(self, model_id: str) -> ModelCircuitBreakerState:
        """Return current state, defaulting to closed."""

        return self._states.get(model_id) or closed_circuit_state(model_id)

    def transition(
        self,
        *,
        record_id: str,
        model_id: str,
        next_status: ModelGatewayCircuitBreakerStatus,
        reason_code: str,
        deterministic_fixture_failure: bool,
        created_at: datetime,
    ) -> ModelCircuitBreakerState:
        """Record an explicit deterministic transition."""

        if len(self._records) >= MAXIMUM_CIRCUIT_BREAKER_RECORDS:
            raise ValueError("circuit-breaker record limit exceeded")
        previous = self.state_for_model(model_id)
        record = ModelCircuitBreakerRecord(
            record_id=record_id,
            provider_id=DETERMINISTIC_PROVIDER_ID,
            model_id=model_id,
            previous_status=previous.status,
            next_status=next_status,
            deterministic_fixture_failure=deterministic_fixture_failure,
            reason_code=reason_code,
            created_at=ensure_gateway_utc(created_at),
        )
        routing_allowed = next_status != ModelGatewayCircuitBreakerStatus.open
        state = ModelCircuitBreakerState(
            provider_id=DETERMINISTIC_PROVIDER_ID,
            model_id=model_id,
            status=next_status,
            record_fingerprints=(*previous.record_fingerprints, record.record_fingerprint or ""),
            routing_allowed=routing_allowed,
        )
        self._records = {**self._records, record.record_id: record}
        self._states = {**self._states, model_id: state}
        return state

    def list_records(self) -> tuple[ModelCircuitBreakerRecord, ...]:
        """Return records in deterministic order."""

        return tuple(self._records[key] for key in sorted(self._records))

    def list_states(self) -> tuple[ModelCircuitBreakerState, ...]:
        """Return states in deterministic order."""

        return tuple(self._states[key] for key in sorted(self._states))

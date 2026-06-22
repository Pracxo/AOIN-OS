"""Resilience contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.resilience import (
    CircuitBreaker,
    FaultInjectionRule,
    ResilienceTestRunRequest,
    RetryPolicy,
)
from tests.resilience_fakes import SCOPE, circuit_breaker, fault_rule, retry_policy


def test_retry_policy_validates_attempts_and_delay_bounds() -> None:
    with pytest.raises(ValidationError):
        RetryPolicy(**{**retry_policy().model_dump(), "max_attempts": 11})

    with pytest.raises(ValidationError):
        RetryPolicy(
            **{
                **retry_policy().model_dump(),
                "initial_delay_ms": 2000,
                "max_delay_ms": 1000,
            }
        )


def test_retry_policy_rejects_secret_like_metadata() -> None:
    with pytest.raises(ValidationError):
        RetryPolicy(**{**retry_policy().model_dump(), "metadata": {"api_key": "hidden"}})


def test_circuit_breaker_validates_threshold_bounds() -> None:
    with pytest.raises(ValidationError):
        CircuitBreaker(**{**circuit_breaker().model_dump(), "failure_threshold": 0})


def test_fault_rule_validates_probability_duration_scope_and_secrets() -> None:
    with pytest.raises(ValidationError):
        FaultInjectionRule(**{**fault_rule().model_dump(), "probability": 1.2})
    with pytest.raises(ValidationError):
        FaultInjectionRule(**{**fault_rule().model_dump(), "duration_ms": 0})
    with pytest.raises(ValidationError):
        FaultInjectionRule(**{**fault_rule().model_dump(), "owner_scope": []})
    with pytest.raises(ValidationError):
        FaultInjectionRule(**{**fault_rule().model_dump(), "metadata": {"token": "hidden"}})


def test_resilience_test_run_request_requires_owner_scope() -> None:
    with pytest.raises(ValidationError):
        ResilienceTestRunRequest(owner_scope=[])

    request = ResilienceTestRunRequest(owner_scope=SCOPE)
    assert request.mode == "dry_run"

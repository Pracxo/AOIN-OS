"""Fault injection service tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.resilience.fault_injection import FaultInjectionService
from tests.resilience_fakes import AllowPolicy, DenyPolicy, fault_rule, repository, settings


def test_fault_injection_disabled_by_default() -> None:
    service = FaultInjectionService(repository(), AllowPolicy(), settings=settings())
    service.create_rule(fault_rule())

    assert service.should_inject("command", None, {"seed": "x"}) is None


def test_fault_injection_selects_matching_rule_when_enabled() -> None:
    service = FaultInjectionService(
        repository(),
        AllowPolicy(),
        settings=settings(AION_FAULT_INJECTION_ENABLED=True),
    )
    rule = service.create_rule(fault_rule())

    selected = service.should_inject("command", None, {"seed": "x"})

    assert selected is not None
    assert selected.fault_rule_id == rule.fault_rule_id
    assert service.apply_fault(rule)["would_inject"] is True


def test_fault_injection_disable_and_policy_deny() -> None:
    service = FaultInjectionService(
        repository(),
        AllowPolicy(),
        settings=settings(AION_FAULT_INJECTION_ENABLED=True),
    )
    created = service.create_rule(fault_rule())

    disabled = service.disable_rule(created.fault_rule_id, "tester", "stop")

    assert disabled.status == "disabled"

    denied = FaultInjectionService(
        repository(),
        DenyPolicy("resilience.fault_rule.create"),
        settings=settings(AION_FAULT_INJECTION_ENABLED=True),
    )
    with pytest.raises(AIONPolicyDeniedException):
        denied.create_rule(fault_rule("denied"))

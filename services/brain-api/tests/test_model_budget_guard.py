"""Model budget guard tests."""

from aion_brain.model_gateway.budget import ModelBudgetGuard
from tests.model_gateway_fakes import deterministic_profile_contract as deterministic_profile
from tests.model_gateway_fakes import external_profile, gateway_request, repository


def test_budget_guard_estimates_tokens_deterministically() -> None:
    guard = ModelBudgetGuard(repository())
    assert guard.estimate_tokens("abcd") == 1
    assert guard.estimate_tokens("abcde") == 2


def test_budget_guard_blocks_external_provider_without_budget() -> None:
    guard = ModelBudgetGuard(repository(), default_daily_budget=0)
    assert guard.authorize_budget(gateway_request(), external_profile()) is None


def test_budget_guard_allows_deterministic_provider_with_zero_cost() -> None:
    guard = ModelBudgetGuard(repository(), default_daily_budget=0)
    budget = guard.authorize_budget(gateway_request(), deterministic_profile())
    assert budget is not None
    assert budget.limit_amount == 0

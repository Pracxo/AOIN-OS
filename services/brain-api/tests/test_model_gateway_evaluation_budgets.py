from aion234_test_support import report, scenario


def test_context_token_cost_latency_budgets_pass() -> None:
    payload = report()
    assert scenario(payload, "context_budget_enforcement")["passed"] is True
    assert scenario(payload, "token_budget_enforcement")["passed"] is True
    assert scenario(payload, "cost_and_latency_budget_integrity")["passed"] is True

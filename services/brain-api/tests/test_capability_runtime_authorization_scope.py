from aion234_test_support import capability_auth

EXPECTED_SCOPE = (
    "authenticated-local-untrusted-model-output-bound-explicit-operator-capability-plan-"
    "closed-capability-connector-manifest-schema-validated-in-memory-sandbox-"
    "deterministic-reference-execution-policy-risk-guardrail-approval-budget-"
    "kill-switch-audit-provenance-rollback-no-external-effect-core"
)


def test_authorization_scope_is_exact() -> None:
    assert capability_auth()["authorization_scope"] == EXPECTED_SCOPE

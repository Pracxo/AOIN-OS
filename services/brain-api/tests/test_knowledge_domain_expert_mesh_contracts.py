from aion_brain.contracts.knowledge_domain_expert_mesh import (
    AUTHORIZATION_TRANSACTION_ID,
    DOMAIN_EXPERT_MESH_CONTRACT_SCHEMA_VERSION,
    CaseRiskClass,
    DomainExpertMeshResourceBudget,
    ExpertPerspectiveRole,
    ExpertReportPosition,
)


def test_contract_constants_and_enums_are_exact():
    assert DOMAIN_EXPERT_MESH_CONTRACT_SCHEMA_VERSION == "aion-knowledge-domain-expert-mesh/v1"
    assert AUTHORIZATION_TRANSACTION_ID == "AION-212-KI-0005"
    assert {item.value for item in CaseRiskClass} == {"low", "moderate", "high", "critical"}
    assert "human_expert" not in {item.value for item in ExpertPerspectiveRole}
    assert "claim_true" not in {item.value for item in ExpertReportPosition}


def test_budget_preserves_zero_runtime_effects():
    budget = DomainExpertMeshResourceBudget()
    assert budget.maximum_persistent_mesh_write_batch == 0
    assert budget.maximum_model_provider_calls == 0
    assert budget.maximum_tool_executions == 0
    assert budget.maximum_network_calls == 0

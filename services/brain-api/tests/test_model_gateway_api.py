"""Model gateway API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.contracts.model_gateway import ModelBudgetRecord
from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container
from tests.model_gateway_fakes import external_profile, external_provider, gateway_request


def test_model_gateway_provider_profile_complete_usage_and_budget_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    provider_response = client.post(
        "/brain/model-providers",
        json=external_provider().model_dump(mode="json"),
    )
    assert provider_response.status_code == 200
    assert client.get("/brain/model-providers").status_code == 200
    assert client.get("/brain/model-providers/external-provider").status_code == 200
    assert client.post("/brain/model-providers/external-provider/health-check").status_code == 200

    profile_response = client.post(
        "/brain/model-profiles",
        json=external_profile().model_dump(mode="json"),
    )
    assert profile_response.status_code == 200
    assert client.get("/brain/model-profiles").status_code == 200
    assert client.get("/brain/model-profiles/external-profile").status_code == 200

    complete_response = client.post(
        "/brain/model-gateway/complete",
        json=gateway_request().model_dump(mode="json"),
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"
    assert client.get("/brain/model-usage").status_code == 200

    budget = ModelBudgetRecord(
        budget_id="budget-1",
        workspace_id="workspace-1",
        actor_id="actor-1",
        scope=["workspace:main"],
        budget_type="daily",
        limit_amount=10,
        used_amount=0,
        currency="USD",
        status="active",
        resets_at=None,
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert (
        client.post("/brain/model-budgets", json=budget.model_dump(mode="json")).status_code == 200
    )
    assert client.get("/brain/model-budgets").status_code == 200
    assert client.post("/brain/model-profiles/external-profile/disable", json={}).status_code == 200
    assert (
        client.post("/brain/model-providers/external-provider/disable", json={}).status_code == 200
    )

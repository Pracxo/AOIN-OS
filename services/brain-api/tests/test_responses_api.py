from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_response_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    compose = client.post(
        "/brain/responses/compose",
        json={"reasoning_result": {"summary": "Done."}},
    )
    assert compose.status_code == 200
    response_id = compose.json()["response_id"]

    get_response = client.get(f"/brain/responses/{response_id}")
    assert get_response.status_code == 200

    verify = client.post(f"/brain/responses/{response_id}/verify")
    assert verify.status_code == 200
    assert verify.json()["status"] == "passed"

    delivery = client.post(f"/brain/responses/{response_id}/deliver-local")
    assert delivery.status_code == 200
    assert delivery.json()["delivery_type"] == "api_return"

    deliveries = client.get(f"/brain/responses/{response_id}/deliveries")
    assert deliveries.status_code == 200
    assert len(deliveries.json()) == 1

from __future__ import annotations

from aion_brain.contracts.responses import ResponseComposeRequest
from tests.dialogue_helpers import service_bundle


def test_response_delivery_service_creates_local_delivery_only() -> None:
    bundle = service_bundle()
    response = bundle.response_composer.compose(
        ResponseComposeRequest(reasoning_result={"summary": "Done."})
    )

    delivery = bundle.response_delivery.deliver_api_return(response.response_id, None, None)

    assert delivery.delivery_type == "api_return"
    assert delivery.output_channel == "api"
    assert delivery.delivered_to is None

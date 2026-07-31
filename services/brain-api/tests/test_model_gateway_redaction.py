from __future__ import annotations

import pytest

from aion_brain.contracts.model_gateway import reject_gateway_protected_material
from tests.model_gateway_aion233_test_support import gateway_flow


def test_prompt_response_and_provider_payloads_are_not_retained() -> None:
    flow = gateway_flow()
    assert flow.request.prompt_body_retained is False
    assert flow.response.transient_output is not None
    retained = flow.response.model_dump()
    assert "transient_output" not in retained
    assert flow.provenance.raw_prompt_retained is False
    assert flow.provenance.raw_response_retained is False


def test_protected_material_rejection_does_not_require_storage() -> None:
    with pytest.raises(ValueError):
        reject_gateway_protected_material({"raw_prompt": "secret"})

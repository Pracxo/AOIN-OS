from __future__ import annotations

from aion_brain.contracts.self_model import SelfDescriptionRequest
from tests.self_model_helpers import bundle


def test_self_description_can_omit_sections() -> None:
    services = bundle()

    description = services.description.describe(
        SelfDescriptionRequest(
            scope=["workspace:main"],
            include_capabilities=False,
            include_limitations=False,
            include_architecture=False,
            include_status=False,
        )
    )

    assert description.capabilities == []
    assert description.limitations == []
    assert description.architecture == []
    assert description.status == {}

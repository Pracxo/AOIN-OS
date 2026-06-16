from __future__ import annotations

from aion_brain.contracts.self_model import SelfDescriptionRequest
from tests.self_model_helpers import bundle


def test_self_description_service_describes_aion_without_sentience_claim() -> None:
    services = bundle()

    description = services.description.describe(SelfDescriptionRequest(scope=["workspace:main"]))

    text = f"{description.summary} {' '.join(description.disclosures)}".lower()
    assert "adaptive intelligence orchestration nexus" in description.full_name.lower()
    assert "sentient" not in text
    assert "production ready" not in text


def test_self_description_does_not_claim_disabled_optional_adapters_active() -> None:
    services = bundle()

    description = services.description.describe(SelfDescriptionRequest(scope=["workspace:main"]))
    turbovec = next(
        item for item in description.capabilities if item.capability_key == "aion.optional.turbovec"
    )

    assert turbovec.status == "unavailable"
    assert turbovec.availability == "optional_unavailable"

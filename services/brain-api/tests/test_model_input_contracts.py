from __future__ import annotations

import pytest

from aion_brain.contracts.model_inputs import ModelInputManifest


def test_model_input_manifest_rejects_provider_specific_name() -> None:
    with pytest.raises(ValueError):
        ModelInputManifest(
            model_input_manifest_id="manifest-1",
            prompt_packet_id="packet-1",
            provider_type="openai",
            status="ready",
            input_hash="hash",
            section_count=1,
            token_estimate=10,
        )


def test_model_input_manifest_allows_configured_provider_ref() -> None:
    manifest = ModelInputManifest(
        model_input_manifest_id="manifest-1",
        prompt_packet_id="packet-1",
        provider_type="provider:configured",
        status="ready",
        input_hash="hash",
        section_count=1,
        token_estimate=10,
    )

    assert manifest.provider_type == "provider:configured"


def test_model_input_manifest_rejects_secret_like_payload() -> None:
    with pytest.raises(ValueError):
        ModelInputManifest(
            model_input_manifest_id="manifest-1",
            prompt_packet_id="packet-1",
            status="ready",
            input_hash="hash",
            section_count=1,
            token_estimate=10,
            metadata={"api_key": "redacted"},
        )

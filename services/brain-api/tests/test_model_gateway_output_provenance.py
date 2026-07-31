from __future__ import annotations

from tests.model_gateway_aion233_test_support import gateway_flow


def test_output_provenance_contains_only_fingerprints_and_untrusted_classification() -> None:
    provenance = gateway_flow(structured=True).provenance
    dumped = provenance.model_dump()
    assert provenance.output_classification.value == "untrusted_validated_structured"
    assert provenance.raw_prompt_retained is False
    assert provenance.raw_response_retained is False
    assert "Summarize" not in str(dumped)

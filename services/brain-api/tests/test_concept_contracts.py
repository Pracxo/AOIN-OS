from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.concepts import ConceptCreateRequest


def test_concept_create_contract_rejects_empty_scope() -> None:
    with pytest.raises(ValidationError):
        ConceptCreateRequest(
            name="Generic Concept",
            description="A generic concept.",
            owner_scope=[],
        )


def test_concept_create_contract_rejects_secret_metadata() -> None:
    with pytest.raises(ValidationError):
        ConceptCreateRequest(
            name="Generic Concept",
            description="A generic concept.",
            owner_scope=["workspace:main"],
            metadata={"api_key": "redacted"},
        )

"""Explicit claim binding for the AION-219 public research pilot."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchClaimSpecification,
    public_research_fingerprint,
    validate_safe_identifier,
)
from aion_brain.contracts.knowledge_research import validate_hex64

FROZEN_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)


class PublicResearchClaimBinding(BaseModel):
    """Redacted explicit claim-to-source binding."""

    model_config = FROZEN_CONFIG

    binding_id: str
    claim_specification_id: str
    claim_id: str
    source_snapshot_ids: tuple[str, ...]
    citation_ids: tuple[str, ...]
    evidence_direction_by_source: dict[str, Literal["supports", "opposes", "contextual"]]
    target_valid_time: datetime
    jurisdiction_fingerprint: str
    version_scope_fingerprint: str
    domain_code_fingerprints: tuple[str, ...]
    automatic_claim_extraction_enabled: Literal[False] = False
    automatic_claim_acceptance_enabled: Literal[False] = False
    automatic_claim_rejection_enabled: Literal[False] = False
    claim_true_assigned: Literal[False] = False
    claim_false_assigned: Literal[False] = False
    binding_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("binding_id", "claim_specification_id", "claim_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim binding id")

    @field_validator("source_snapshot_ids", "citation_ids")
    @classmethod
    def tuple_ids_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(
            validate_safe_identifier(value, "claim binding tuple") for value in values
        )
        if tuple(sorted(normalized)) != normalized:
            raise ValueError("claim binding tuples must be sorted")
        return normalized

    @field_validator("evidence_direction_by_source")
    @classmethod
    def directions_are_safe(
        cls,
        values: dict[str, Literal["supports", "opposes", "contextual"]],
    ) -> dict[str, Literal["supports", "opposes", "contextual"]]:
        return {
            validate_safe_identifier(key, "claim binding direction"): value
            for key, value in sorted(values.items())
        }

    @field_validator(
        "jurisdiction_fingerprint",
        "version_scope_fingerprint",
        "binding_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim binding fingerprint")

    @field_validator("domain_code_fingerprints")
    @classmethod
    def domain_hashes_are_hex(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(validate_hex64(value, "domain code fingerprint") for value in values)
        if tuple(sorted(normalized)) != normalized:
            raise ValueError("domain code fingerprints must be sorted")
        return normalized


def bind_explicit_claim_specifications(
    specifications: tuple[PublicResearchClaimSpecification, ...],
    *,
    available_source_snapshot_ids: tuple[str, ...],
    available_citation_ids: tuple[str, ...],
) -> tuple[PublicResearchClaimBinding, ...]:
    """Build deterministic claim bindings without automatic claim extraction."""

    available_sources = set(available_source_snapshot_ids)
    available_citations = set(available_citation_ids)
    bindings: list[PublicResearchClaimBinding] = []
    for index, specification in enumerate(
        sorted(specifications, key=lambda item: item.claim_specification_id),
        start=1,
    ):
        missing = set(specification.evidence_bindings) - available_sources - available_citations
        if missing:
            raise ValueError("claim evidence binding does not resolve")
        source_ids = tuple(
            sorted(item for item in specification.evidence_bindings if item in available_sources)
        )
        citation_ids = tuple(
            sorted(item for item in specification.evidence_bindings if item in available_citations)
        )
        payload = {
            "claim_specification_id": specification.claim_specification_id,
            "claim_id": specification.claim_id,
            "source_snapshot_ids": source_ids,
            "citation_ids": citation_ids,
            "evidence_direction_by_source": specification.evidence_direction_by_source,
            "target_valid_time": specification.target_valid_time.isoformat(),
        }
        binding_id = f"public-research-claim-binding-{index:04d}"
        bindings.append(
            PublicResearchClaimBinding(
                binding_id=binding_id,
                claim_specification_id=specification.claim_specification_id,
                claim_id=specification.claim_id,
                source_snapshot_ids=source_ids,
                citation_ids=citation_ids,
                evidence_direction_by_source=specification.evidence_direction_by_source,
                target_valid_time=specification.target_valid_time,
                jurisdiction_fingerprint=public_research_fingerprint(
                    {"jurisdiction": specification.jurisdiction}
                ),
                version_scope_fingerprint=public_research_fingerprint(
                    {"version_scope": specification.version_scope}
                ),
                domain_code_fingerprints=tuple(
                    sorted(
                        public_research_fingerprint({"domain_code": code})
                        for code in specification.domain_codes
                    )
                ),
                binding_fingerprint=public_research_fingerprint(payload),
            )
        )
    return tuple(bindings)


__all__ = ["PublicResearchClaimBinding", "bind_explicit_claim_specifications"]

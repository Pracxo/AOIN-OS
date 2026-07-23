"""Source provenance records for controlled research evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    SOURCE_PROVENANCE_SCHEMA_VERSION,
    LicencePolicyStatus,
    ResearchAdapterType,
    ResearchSourceClass,
    RobotsPolicyStatus,
    ensure_utc,
    reject_protected_material,
    validate_hex64,
    validate_safe_identifier,
)


class SourceProvenanceRecord(BaseModel):
    """Declared and transport metadata for an immutable source snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-provenance/v1"] = (
        SOURCE_PROVENANCE_SCHEMA_VERSION
    )
    provenance_id: str
    snapshot_id: str
    canonical_url_fingerprint: str
    content_sha256: str
    source_class: ResearchSourceClass
    declared_author: str | None = Field(default=None, max_length=200)
    declared_publisher: str | None = Field(default=None, max_length=200)
    declared_title: str | None = Field(default=None, max_length=300)
    declared_publication_timestamp: datetime | None = None
    declared_modification_timestamp: datetime | None = None
    retrieval_timestamp: datetime
    metadata_sources: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    robots_policy_status: RobotsPolicyStatus
    licence_policy_status: LicencePolicyStatus
    redirect_chain_fingerprint: str
    destination_validation_fingerprint: str
    safe_headers_fingerprint: str
    adapter_type: ResearchAdapterType
    operator_invoked: Literal[True] = True
    redacted: Literal[True] = True
    source_claims_verified: Literal[False] = False
    provenance_fingerprint: str

    @field_validator("provenance_id", "snapshot_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "provenance identifier")

    @field_validator(
        "canonical_url_fingerprint",
        "content_sha256",
        "redirect_chain_fingerprint",
        "destination_validation_fingerprint",
        "safe_headers_fingerprint",
        "provenance_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "provenance fingerprint")

    @field_validator("declared_author", "declared_publisher", "declared_title")
    @classmethod
    def declared_metadata_is_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_protected_material(value, "declared metadata")
        return value

    @field_validator(
        "declared_publication_timestamp",
        "declared_modification_timestamp",
        "retrieval_timestamp",
    )
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value, "provenance timestamp")

    @field_validator("metadata_sources")
    @classmethod
    def metadata_sources_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_protected_material(item, "metadata_sources")
        return value


__all__ = ["SourceProvenanceRecord"]

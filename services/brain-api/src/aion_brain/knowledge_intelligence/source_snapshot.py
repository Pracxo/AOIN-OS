"""Immutable source snapshot metadata for controlled research."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    SOURCE_SNAPSHOT_SCHEMA_VERSION,
    LicencePolicyStatus,
    ResearchContentType,
    ResearchMethod,
    ResearchSourceClass,
    RobotsPolicyStatus,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    sha256_bytes,
    validate_hex64,
    validate_safe_identifier,
)


class SourceSnapshot(BaseModel):
    """Immutable metadata for one acquired untrusted source artifact."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-snapshot/v1"] = SOURCE_SNAPSHOT_SCHEMA_VERSION
    snapshot_id: str
    plan_id: str
    candidate_id: str
    query_ids: tuple[str, ...]
    original_url_fingerprint: str
    canonical_url: str
    final_url: str
    method: ResearchMethod
    status_code: int = Field(ge=100, le=599)
    content_type: ResearchContentType
    character_encoding: str | None
    content_length: int = Field(ge=0)
    content_sha256: str
    safe_headers: dict[str, str]
    redirect_chain: tuple[str, ...] = Field(default_factory=tuple)
    source_class: ResearchSourceClass
    robots_policy_status: RobotsPolicyStatus
    licence_policy_status: LicencePolicyStatus
    publication_timestamp: datetime | None = None
    modification_timestamp: datetime | None = None
    retrieval_timestamp: datetime
    content_artifact_id: str
    content_present_in_memory: bool
    redacted_preview: str = Field(default="", max_length=512)
    snapshot_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    untrusted_content: Literal[True] = True
    verified_fact: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_created: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("snapshot_id", "plan_id", "candidate_id", "content_artifact_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "snapshot identifier")

    @field_validator("query_ids")
    @classmethod
    def query_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate query IDs are rejected")
        for item in value:
            validate_safe_identifier(item, "query_id")
        return value

    @field_validator("original_url_fingerprint", "content_sha256", "snapshot_fingerprint")
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "snapshot fingerprint")

    @field_validator(
        "publication_timestamp",
        "modification_timestamp",
        "retrieval_timestamp",
    )
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value, "source snapshot timestamp")

    @field_validator("redacted_preview")
    @classmethod
    def preview_is_redacted(cls, value: str) -> str:
        reject_protected_material(value, "redacted_preview")
        return value

    @model_validator(mode="after")
    def snapshot_is_safe(self) -> Self:
        if self.content_present_in_memory is False:
            return self
        if self.content_length < 1:
            raise ValueError("in-memory content must have a positive length")
        return self


@dataclass(frozen=True)
class EphemeralSourceArtifact:
    """Bounded source bytes retained only by an explicit caller."""

    snapshot_id: str
    content_bytes: bytes = field(repr=False)
    content_sha256: str

    def __post_init__(self) -> None:
        validate_safe_identifier(self.snapshot_id, "snapshot_id")
        digest = sha256_bytes(self.content_bytes)
        if digest != self.content_sha256:
            raise ValueError("content fingerprint mismatch")

    def purge(self) -> EphemeralSourceArtifact:
        """Return an empty artifact with the same identity and digest."""

        return EphemeralSourceArtifact(
            snapshot_id=self.snapshot_id,
            content_bytes=b"",
            content_sha256=sha256_bytes(b""),
        )


def snapshot_fingerprint(snapshot_payload: dict[str, object]) -> str:
    """Fingerprint a snapshot payload excluding the fingerprint field itself."""

    payload = dict(snapshot_payload)
    payload.pop("snapshot_fingerprint", None)
    return fingerprint_payload(payload)


__all__ = ["EphemeralSourceArtifact", "SourceSnapshot", "snapshot_fingerprint"]

"""Research adapter protocols and disabled/local implementations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    MAXIMUM_RESPONSE_BYTES_PER_SOURCE,
    ResearchFetchRequest,
    ResearchFetchResponse,
    ResearchMethod,
    ResearchQuery,
    SourceCandidate,
    fingerprint_payload,
    reject_protected_material,
    sha256_bytes,
    utc_now,
)
from aion_brain.knowledge_intelligence.research_policy import (
    canonicalize_research_url,
    parse_and_validate_content_type,
    project_safe_response_headers,
    validate_character_encoding,
)


class ResearchAdapterDisabledError(RuntimeError):
    """Raised when a disabled adapter is invoked."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class ResearchSearchAdapter(Protocol):
    """Protocol for injected search adapters."""

    def search(
        self,
        query: ResearchQuery,
        *,
        maximum_results: int,
    ) -> tuple[SourceCandidate, ...]:
        """Return deterministic source candidates for a query."""


class ResearchFetchAdapter(Protocol):
    """Protocol for injected fetch adapters."""

    def fetch(self, request: ResearchFetchRequest) -> ResearchFetchResponse:
        """Fetch exactly one request through an explicit adapter."""


class DisabledResearchSearchAdapter:
    """Fail-closed no-network search adapter."""

    reason_code = "research_search_adapter_disabled"

    def search(
        self,
        query: ResearchQuery,
        *,
        maximum_results: int,
    ) -> tuple[SourceCandidate, ...]:
        raise ResearchAdapterDisabledError(self.reason_code)


class InMemoryResearchSearchAdapter:
    """Deterministic immutable search adapter over explicit candidates."""

    def __init__(self, mapping: dict[str, tuple[SourceCandidate, ...]]) -> None:
        self._mapping = {
            query_id: tuple(sorted(candidates, key=lambda item: item.candidate_id))
            for query_id, candidates in mapping.items()
        }
        for query_id, candidates in self._mapping.items():
            if len({item.original_url for item in candidates}) != len(candidates):
                raise ValueError("duplicate canonical URL in in-memory search mapping")
            for candidate in candidates:
                if query_id not in candidate.query_ids:
                    raise ValueError("candidate query IDs must match mapping key")

    def search(
        self,
        query: ResearchQuery,
        *,
        maximum_results: int,
    ) -> tuple[SourceCandidate, ...]:
        if maximum_results < 0:
            raise ValueError("maximum_results must be non-negative")
        return self._mapping.get(query.query_id, ())[:maximum_results]


class DisabledResearchFetchAdapter:
    """Fail-closed no-network fetch adapter."""

    reason_code = "research_adapter_disabled"

    def fetch(self, request: ResearchFetchRequest) -> ResearchFetchResponse:
        raise ResearchAdapterDisabledError(self.reason_code)


class InMemoryResearchFetchAdapter:
    """Deterministic in-memory fetch adapter over explicit response fixtures."""

    def __init__(self, fixtures: dict[tuple[str, str], ResearchFetchResponse]) -> None:
        self._fixtures = dict(fixtures)
        if len(self._fixtures) != len(fixtures):
            raise ValueError("duplicate fetch fixture registration")

    def fetch(self, request: ResearchFetchRequest) -> ResearchFetchResponse:
        key = (request.method, request.canonical_url)
        if key not in self._fixtures:
            raise ValueError("fetch fixture is unavailable")
        response = self._fixtures[key]
        if response.request_id != request.request_id:
            raise ValueError("fetch fixture request ID mismatch")
        if response.body_length > request.maximum_response_bytes:
            raise ValueError("response-size budget exceeded")
        return response


class FixtureResponseEnvelope(BaseModel):
    """Strict schema accepted by the explicit local fixture adapter."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

    synthetic: Literal[True]
    redacted: Literal[True]
    request_method: ResearchMethod
    canonical_url: str
    status_code: int = Field(ge=100, le=599)
    peer_address: str
    response_headers: dict[str, str]
    content_type: str
    character_encoding: str | None = None
    body_utf8: str = Field(max_length=MAXIMUM_RESPONSE_BYTES_PER_SOURCE)

    @field_validator("canonical_url")
    @classmethod
    def canonical_url_is_safe(cls, value: str) -> str:
        return canonicalize_research_url(value).canonical_url

    @field_validator("response_headers")
    @classmethod
    def headers_are_safe(cls, value: dict[str, str]) -> dict[str, str]:
        project_safe_response_headers(value)
        return value

    @field_validator("body_utf8")
    @classmethod
    def body_is_redacted_fixture(cls, value: str) -> str:
        reject_protected_material(value, "fixture body")
        return value

    @model_validator(mode="after")
    def content_policy_holds(self) -> Self:
        content_type = parse_and_validate_content_type(self.content_type)
        validate_character_encoding(content_type, self.character_encoding)
        return self


class ExplicitLocalFixtureResearchAdapter:
    """Read exactly one explicit synthetic fixture envelope outside the repository."""

    def __init__(self, fixture_path: Path, *, repository_root: Path) -> None:
        self._fixture_path = _validate_fixture_path(fixture_path, repository_root=repository_root)

    def fetch(self, request: ResearchFetchRequest) -> ResearchFetchResponse:
        raw_text = self._fixture_path.read_text(encoding="utf-8")
        reject_protected_material(raw_text, "fixture envelope")
        envelope = FixtureResponseEnvelope.model_validate(json.loads(raw_text))
        if envelope.request_method != request.method:
            raise ValueError("fixture method mismatch")
        if envelope.canonical_url != request.canonical_url:
            raise ValueError("fixture URL mismatch")
        body = envelope.body_utf8.encode("utf-8")
        if len(body) > request.maximum_response_bytes:
            raise ValueError("response-size budget exceeded")
        content_type = parse_and_validate_content_type(envelope.content_type)
        encoding = validate_character_encoding(content_type, envelope.character_encoding)
        retrieved_at = utc_now()
        safe_headers = project_safe_response_headers(envelope.response_headers)
        payload = {
            "request_id": request.request_id,
            "status_code": envelope.status_code,
            "canonical_url": envelope.canonical_url,
            "peer_address": envelope.peer_address,
            "headers": safe_headers,
            "body_sha256": sha256_bytes(body),
            "retrieved_at": retrieved_at.isoformat(),
        }
        return ResearchFetchResponse(
            request_id=request.request_id,
            status_code=envelope.status_code,
            response_url=envelope.canonical_url,
            peer_address=envelope.peer_address,
            safe_response_headers=safe_headers,
            content_type=content_type,
            character_encoding=encoding,
            body=body,
            body_length=len(body),
            retrieved_at=retrieved_at,
            fingerprint=fingerprint_payload(payload),
        )


class DisabledResearchHttpTransport:
    """Policy placeholder that never performs a public network fetch."""

    system_http_transport_available = False
    public_network_fetch_available = False


class OperatorInvokedHttpResearchAdapter:
    """Authorized policy wrapper whose live transport remains unavailable."""

    operator_invoked_http_adapter_policy_available = True
    system_http_transport_available = False
    public_network_fetch_available = False

    def __init__(self, transport: DisabledResearchHttpTransport | None = None) -> None:
        self._transport = transport or DisabledResearchHttpTransport()

    def fetch(self, request: ResearchFetchRequest) -> ResearchFetchResponse:
        raise ResearchAdapterDisabledError("research_network_transport_unavailable")


def _validate_fixture_path(fixture_path: Path, *, repository_root: Path) -> Path:
    if not fixture_path.is_absolute():
        raise ValueError("fixture path must be absolute")
    if fixture_path.is_symlink():
        raise ValueError("symlink fixture file is rejected")
    root = repository_root.resolve()
    try:
        path = fixture_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("fixture file is missing") from exc
    if root == path or root in path.parents:
        raise ValueError("repository fixture paths are rejected")
    if path.name.startswith("."):
        raise ValueError("hidden fixture file is rejected")
    if not path.is_file():
        raise ValueError("fixture path must be a regular file")
    if path.stat().st_size > MAXIMUM_RESPONSE_BYTES_PER_SOURCE:
        raise ValueError("fixture file is too large")
    return path


__all__ = [
    "DisabledResearchFetchAdapter",
    "DisabledResearchHttpTransport",
    "DisabledResearchSearchAdapter",
    "ExplicitLocalFixtureResearchAdapter",
    "FixtureResponseEnvelope",
    "InMemoryResearchFetchAdapter",
    "InMemoryResearchSearchAdapter",
    "OperatorInvokedHttpResearchAdapter",
    "ResearchAdapterDisabledError",
    "ResearchFetchAdapter",
    "ResearchSearchAdapter",
]

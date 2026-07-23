from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel

from aion_brain.contracts.knowledge_research import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    ResearchFetchResponse,
    ResearchPlan,
    ResearchQuery,
    SourceCandidate,
    fingerprint_payload,
    research_plan_fingerprint,
    research_query_fingerprint,
    sha256_bytes,
    source_candidate_fingerprint,
)
from aion_brain.knowledge_intelligence.research_budget import ResearchResourceBudget

NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def valid_query(query_id: str = "query-001") -> ResearchQuery:
    payload = {
        "query_id": query_id,
        "research_question": "What does the synthetic standard record state?",
        "research_purpose": "Collect untrusted synthetic evidence for operator review.",
        "language": "en",
        "requested_source_classes": ("official_standard",),
        "requested_content_types": ("text/plain",),
        "domain_hints": ("research.example.invalid",),
        "created_at": NOW,
    }
    return ResearchQuery(
        **payload,
        query_fingerprint=research_query_fingerprint(_json_payload(payload)),
    )


def valid_candidate(
    candidate_id: str = "candidate-001",
    *,
    query_id: str = "query-001",
    url: str = "https://research.example.invalid/source.txt",
) -> SourceCandidate:
    payload = {
        "candidate_id": candidate_id,
        "query_ids": (query_id,),
        "original_url": url,
        "source_class": "official_standard",
        "expected_content_types": ("text/plain",),
        "robots_policy_status": "allowed",
        "licence_policy_status": "permitted",
        "operator_supplied": True,
        "search_adapter_type": "disabled",
        "created_at": NOW,
    }
    return SourceCandidate(
        **payload,
        candidate_fingerprint=source_candidate_fingerprint(_json_payload(payload)),
    )


def valid_plan(
    *,
    candidate: SourceCandidate | None = None,
    adapter_type: str = "in_memory",
) -> ResearchPlan:
    query = valid_query()
    chosen_candidate = candidate or valid_candidate()
    budget_fingerprint = fingerprint_payload(ResearchResourceBudget().model_dump(mode="json"))
    payload = {
        "plan_id": "plan-001",
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "queries": (query,),
        "explicit_domain_allowlist": ("research.example.invalid",),
        "explicit_source_candidates": (chosen_candidate,),
        "allowed_methods": ("GET", "HEAD"),
        "allowed_content_types": ("text/plain",),
        "research_adapter_type": adapter_type,
        "search_adapter_type": "disabled",
        "resource_budget_fingerprint": budget_fingerprint,
        "created_at": NOW,
        "expires_at": NOW + timedelta(hours=1),
    }
    return ResearchPlan(
        **payload,
        plan_fingerprint=research_plan_fingerprint(_json_payload(payload)),
    )


def valid_response(
    *,
    request_id: str = "request-001",
    url: str = "https://research.example.invalid/source.txt",
    body: bytes = b"synthetic evidence for operator review",
) -> ResearchFetchResponse:
    payload = {
        "request_id": request_id,
        "status_code": 200,
        "response_url": url,
        "peer_address": "93.184.216.34",
        "safe_response_headers": {"Content-Type": "text/plain"},
        "content_type": "text/plain",
        "character_encoding": "utf-8",
        "body_sha256": sha256_bytes(body),
        "body_length": len(body),
        "retrieved_at": NOW,
    }
    return ResearchFetchResponse(
        request_id=request_id,
        status_code=200,
        response_url=url,
        peer_address="93.184.216.34",
        safe_response_headers={"Content-Type": "text/plain"},
        content_type="text/plain",
        character_encoding="utf-8",
        body=body,
        body_length=len(body),
        retrieved_at=NOW,
        fingerprint=fingerprint_payload(_json_payload(payload)),
    )


def _json_payload(payload: dict[str, object]) -> dict[str, object]:
    converted: dict[str, object] = {}
    for key, value in payload.items():
        converted[key] = _json_value(value)
    return converted


def _json_value(value: object) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value

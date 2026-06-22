"""Pagination helpers for public AION APIs."""

from __future__ import annotations

import base64
import json
from typing import Any

from aion_brain.api_support.errors import AIONValidationException
from aion_brain.contracts.api import AIONPage, AIONPageInfo, RequestContext


def build_page(
    items: list[Any],
    limit: int,
    next_cursor: str | None,
    previous_cursor: str | None = None,
    total_count: int | None = None,
    context: RequestContext | None = None,
) -> AIONPage:
    """Build a generic AION page without exposing storage offsets."""
    return AIONPage(
        items=items,
        page=AIONPageInfo(
            limit=limit,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
            has_next=next_cursor is not None,
            total_count=total_count,
        ),
        trace_id=context.trace_id if context else None,
        correlation_id=context.correlation_id if context else None,
        request_id=context.request_id if context else None,
    )


def encode_cursor(data: dict[str, Any]) -> str:
    """Encode URL-safe base64 JSON cursor data deterministically."""
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode URL-safe base64 JSON cursor data."""
    try:
        payload = base64.urlsafe_b64decode(cursor.encode("ascii"))
        decoded = json.loads(payload.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AIONValidationException("Invalid pagination cursor.") from exc
    if not isinstance(decoded, dict):
        raise AIONValidationException("Invalid pagination cursor.")
    return decoded

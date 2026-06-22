"""API pagination contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.api_support.errors import AIONValidationException
from aion_brain.api_support.pagination import build_page, decode_cursor, encode_cursor
from aion_brain.contracts.api import AIONPageRequest


def test_page_request_validates_limit() -> None:
    with pytest.raises(ValidationError):
        AIONPageRequest(limit=0)
    with pytest.raises(ValidationError):
        AIONPageRequest(limit=501)


def test_cursor_encode_decode_is_deterministic() -> None:
    first = encode_cursor({"created_at": "2026-01-01", "id": "b"})
    second = encode_cursor({"id": "b", "created_at": "2026-01-01"})

    assert first == second
    assert decode_cursor(first) == {"created_at": "2026-01-01", "id": "b"}


def test_invalid_cursor_raises_validation_exception() -> None:
    with pytest.raises(AIONValidationException):
        decode_cursor("not valid cursor")


def test_build_page_includes_page_metadata() -> None:
    page = build_page([{"id": "one"}], limit=1, next_cursor="next")

    assert page.page.has_next is True
    assert page.items == [{"id": "one"}]

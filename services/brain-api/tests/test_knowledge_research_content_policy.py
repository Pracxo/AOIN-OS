from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.research_policy import parse_and_validate_content_type


@pytest.mark.parametrize(
    "content_type",
    [
        "text/html",
        "text/plain",
        "application/json",
        "application/pdf",
        "application/xml",
        "text/xml",
    ],
)
def test_allowed_mime_types_are_accepted(content_type: str):
    assert parse_and_validate_content_type(f"{content_type}; charset=utf-8") == content_type


@pytest.mark.parametrize(
    "content_type",
    [
        "application/octet-stream",
        "application/zip",
        "application/x-msdownload",
        "video/mp4",
        "audio/mp3",
    ],
)
def test_disallowed_content_types_are_rejected(content_type: str):
    with pytest.raises(ValueError):
        parse_and_validate_content_type(content_type)

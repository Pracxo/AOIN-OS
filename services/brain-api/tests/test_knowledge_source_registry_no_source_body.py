from __future__ import annotations

from knowledge_source_registry_implementation_helpers import valid_batch


def test_source_registry_serialization_excludes_source_body_preview_urls_and_headers():
    rendered = valid_batch().model_dump_json().lower()
    forbidden = (
        "synthetic evidence for operator review",
        "redacted_preview",
        "content_artifact_id",
        "https://research.example.invalid",
        "content-type",
        "authorization:",
        "cookie:",
    )
    for marker in forbidden:
        assert marker not in rendered
    assert '"source_body_present":false' in rendered
    assert '"source_body_bytes":0' in rendered

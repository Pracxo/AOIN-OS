from __future__ import annotations

from tests.grounding_helpers import service_bundle, source


def test_citation_mapper_creates_citations_and_unsupported_statements() -> None:
    bundle = service_bundle()

    citation_map = bundle.mapper.map_text(
        text=("AION records deterministic source support. This unrelated statement has no source."),
        trace_id="trace-1",
        owner_scope=["workspace:main"],
        sources=[source()],
        target_type="response",
        target_id="response-1",
    )

    assert citation_map.citation_ids
    assert citation_map.unsupported_statement_ids
    assert 0.0 < citation_map.coverage_score < 1.0


def test_citation_mapper_required_source_types_report_missing() -> None:
    bundle = service_bundle()

    citation_map = bundle.mapper.map_text(
        text="AION records deterministic source support.",
        trace_id="trace-1",
        owner_scope=["workspace:main"],
        sources=[],
        target_type="generic",
        target_id="target-1",
        required_source_types=["evidence"],
    )

    assert citation_map.status == "insufficient_sources"
    assert citation_map.missing_source_types == ["evidence"]

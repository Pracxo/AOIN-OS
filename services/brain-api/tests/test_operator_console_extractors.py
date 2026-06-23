from __future__ import annotations

from aion_brain.contracts.operator_console import ConsoleViewModelRequest
from aion_brain.operator_console.data_sources import view_data_sources
from aion_brain.operator_console.extractors import extract_sections


def test_extractor_returns_unavailable_section_for_missing_service() -> None:
    request = ConsoleViewModelRequest(view="overview", owner_scope=["workspace:main"])
    sources = view_data_sources("overview", owner_scope=request.owner_scope, container=object())

    sections = extract_sections(request, sources, container=object())

    assert sections
    assert {section.status for section in sections} == {"unavailable"}


def test_extractor_does_not_mutate_source_records() -> None:
    request = ConsoleViewModelRequest(view="overview", owner_scope=["workspace:main"])
    sources = view_data_sources("overview", owner_scope=request.owner_scope, container=object())
    before = [source.model_dump() for source in sources]

    extract_sections(request, sources, container=object())

    assert [source.model_dump() for source in sources] == before

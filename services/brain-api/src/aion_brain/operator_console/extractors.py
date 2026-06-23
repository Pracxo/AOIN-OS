"""Best-effort read-only extractors for Operator Console sections."""

from __future__ import annotations

from aion_brain.contracts.operator_console import (
    ConsoleDataSource,
    ConsoleViewModelRequest,
    ConsoleViewSection,
)
from aion_brain.operator_console.action_boundaries import (
    allowed_action_descriptors,
    forbidden_action_descriptors,
)
from aion_brain.operator_console.redaction import redact_console_payload


class ConsoleExtractor:
    """Extract redacted summaries from already-assembled services."""

    def __init__(self, container: object | None = None) -> None:
        self._container = container

    def section_for_source(
        self,
        request: ConsoleViewModelRequest,
        source: ConsoleDataSource,
    ) -> ConsoleViewSection:
        """Build one redacted, read-only section for a source."""
        service = getattr(self._container, source.service_name, None) if self._container else None
        if service is None:
            return ConsoleViewSection(
                section_key=source.source_key,
                title=source.source_key.replace("_", " ").title(),
                status="unavailable",
                severity="medium",
                summary=f"{source.source_key} source is unavailable.",
                items=[],
                data_sources=[source],
                allowed_actions=[],
                forbidden_actions=forbidden_action_descriptors()
                if request.include_forbidden_actions
                else [],
                blockers=[{"source_key": source.source_key, "status": "unavailable"}],
                warnings=[],
                refs=[],
                metadata={"read_only": True},
            )
        item = redact_console_payload(
            {
                "source_key": source.source_key,
                "service_name": source.service_name,
                "available": True,
                "read_only": True,
            }
        )
        return ConsoleViewSection(
            section_key=source.source_key,
            title=source.source_key.replace("_", " ").title(),
            status="ready",
            severity="low",
            summary=f"{source.source_key} is available for read-only console projection.",
            items=[item],
            data_sources=[source],
            allowed_actions=allowed_action_descriptors() if request.include_actions else [],
            forbidden_actions=forbidden_action_descriptors()
            if request.include_forbidden_actions
            else [],
            blockers=[],
            warnings=[],
            refs=[source.endpoint_hint] if request.include_refs and source.endpoint_hint else [],
            metadata={"read_only": True},
        )


def extract_sections(
    request: ConsoleViewModelRequest,
    sources: list[ConsoleDataSource],
    *,
    container: object | None = None,
) -> list[ConsoleViewSection]:
    """Extract sections for all sources."""
    extractor = ConsoleExtractor(container)
    return [extractor.section_for_source(request, source) for source in sources]


__all__ = ["ConsoleExtractor", "extract_sections"]

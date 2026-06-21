"""Deterministic model output parser."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.model_outputs import ModelOutputRecord, ModelOutputSegment
from aion_brain.model_outputs.hash import hash_output_segment
from aion_brain.model_outputs.unsafe_detector import UnsafeOutputDetector

_FENCED_BLOCK = re.compile(r"```(?P<label>[A-Za-z0-9_-]*)\n(?P<body>.*?)```", re.S)
_TOOL_PREFIXES = ("tool:", "function_call:", "action:", "mcp:", "capability:", "command:")
_REFUSAL_PHRASES = ("i can't", "i cannot", "i will not", "unable to comply")
_UNCERTAINTY_PHRASES = ("not sure", "uncertain", "i don't know", "cannot determine")


class OutputParser:
    """Parse redacted model output into generic segments."""

    def __init__(self, detector: UnsafeOutputDetector | None = None) -> None:
        self._detector = detector or UnsafeOutputDetector()

    def parse(self, model_output: ModelOutputRecord) -> list[ModelOutputSegment]:
        """Return deterministic redacted output segments."""

        text = model_output.redacted_output
        raw_segments: list[tuple[str, str, bool]] = []
        for match in _FENCED_BLOCK.finditer(text):
            label = match.group("label").lower()
            body = match.group("body").strip()
            if not body:
                continue
            segment_type = "json_block" if label == "json" or body.startswith("{") else "code_block"
            raw_segments.append(
                (segment_type, body, segment_type == "code_block" and _looks_executable(body))
            )
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lowered = stripped.lower()
            if stripped.startswith(("- ", "* ")):
                raw_segments.append(("bullet", stripped[2:].strip(), False))
            elif any(lowered.startswith(prefix) for prefix in _TOOL_PREFIXES):
                raw_segments.append(("tool_intent", stripped, True))
            elif lowered.startswith(("citation:", "source:", "[citation]")):
                raw_segments.append(("citation_hint", stripped, False))
            elif any(phrase in lowered for phrase in _REFUSAL_PHRASES):
                raw_segments.append(("refusal", stripped, False))
            elif any(phrase in lowered for phrase in _UNCERTAINTY_PHRASES):
                raw_segments.append(("uncertainty", stripped, False))
        if not raw_segments and text.strip():
            raw_segments.append(("answer_text", text.strip(), False))
        segments: list[ModelOutputSegment] = []
        for index, (segment_type, content, unsafe) in enumerate(raw_segments, start=1):
            findings = self._detector.detect(content, source_type="output_segment")
            segments.append(
                ModelOutputSegment(
                    output_segment_id=f"output-segment-{uuid4().hex}",
                    model_output_id=model_output.model_output_id,
                    trace_id=model_output.trace_id,
                    segment_order=index,
                    segment_type=segment_type,  # type: ignore[arg-type]
                    content=content,
                    content_hash=hash_output_segment(content),
                    confidence=0.8 if not unsafe and not findings else 0.4,
                    unsafe=unsafe or bool(findings),
                    findings=findings,
                    metadata={"deterministic_parser": True},
                    created_at=datetime.now(UTC),
                )
            )
        return segments


def _looks_executable(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in ("rm -rf", "curl ", "sudo ", "python ", "bash "))


__all__ = ["OutputParser"]

"""Deterministic unsafe model output detector."""

from __future__ import annotations

import re
from typing import Any

from aion_brain.model_outputs.redaction import (
    contains_hidden_reasoning_marker,
    contains_secret_like_text,
)


class UnsafeOutputDetector:
    """Detect generic unsafe output patterns without external classifiers."""

    def detect(self, text: str, source_type: str = "model_output") -> list[dict[str, Any]]:
        """Return redacted unsafe output findings."""

        lowered = text.lower()
        findings: list[dict[str, Any]] = []
        if contains_hidden_reasoning_marker(text):
            findings.append(_finding("protected_reasoning_detected", "critical", source_type))
        if "raw prompt" in lowered or "raw_prompt" in lowered or "system prompt:" in lowered:
            findings.append(_finding("protected_prompt_echo_detected", "high", source_type))
        if contains_secret_like_text(text):
            findings.append(_finding("secret_like_output", "critical", source_type))
        if "bypass policy" in lowered or "pretend policy allows" in lowered:
            findings.append(_finding("policy_bypass_instruction", "critical", source_type))
        if "bypass approval" in lowered or "approval is not needed" in lowered:
            findings.append(_finding("approval_bypass_instruction", "critical", source_type))
        if "exceed autonomy" in lowered or "ignore autonomy" in lowered:
            findings.append(_finding("autonomy_bypass_instruction", "critical", source_type))
        if re.search(r"\b(execute|run|call)\b.{0,30}\b(tool|command|capability|mcp)\b", lowered):
            findings.append(_finding("tool_execution_instruction", "high", source_type))
        if re.search(r"\[[0-9]+\]", text) and "source" not in lowered and "citation" not in lowered:
            findings.append(_finding("hallucinated_citation_marker", "medium", source_type))
        if "i can do anything" in lowered or "all capabilities are available" in lowered:
            findings.append(_finding("unsupported_capability_claim", "high", source_type))
        if "production ready" in lowered or "fully production-ready" in lowered:
            findings.append(_finding("production_readiness_claim", "medium", source_type))
        if "i am sentient" in lowered or "i have consciousness" in lowered:
            findings.append(_finding("sentience_claim", "high", source_type))
        return findings


def _finding(code: str, severity: str, source_type: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "source_type": source_type,
        "snippet": "[redacted]",
    }


__all__ = ["UnsafeOutputDetector"]

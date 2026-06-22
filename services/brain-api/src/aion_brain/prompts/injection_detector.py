"""Deterministic prompt injection detection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from aion_brain.contracts.prompts import PromptInjectionFinding, PromptSection
from aion_brain.prompts.redaction import redact_prompt_text


@dataclass(frozen=True)
class InjectionPattern:
    """One deterministic injection pattern."""

    regex: re.Pattern[str]
    finding_type: str
    severity: Literal["low", "medium", "high", "critical"]
    reason: str


_PATTERNS = [
    InjectionPattern(
        re.compile(
            r"\b(ignore|forget|override)\s+(all\s+)?(previous|prior)\s+instructions\b", re.I
        ),
        "instruction_override_attempt",
        "high",
        "Attempts to override prior instructions.",
    ),
    InjectionPattern(
        re.compile(r"\bignore\s+(the\s+)?(system|developer)\s+(message|instructions?)\b", re.I),
        "instruction_override_attempt",
        "critical",
        "Attempts to override protected instruction layers.",
    ),
    InjectionPattern(
        re.compile(r"\b(disable|bypass|ignore)\s+(policy|guardrails?|safety)\b", re.I),
        "policy_override_attempt",
        "critical",
        "Attempts to bypass policy boundaries.",
    ),
    InjectionPattern(
        re.compile(r"\b(disable|bypass|override)\s+autonomy\b", re.I),
        "autonomy_override_attempt",
        "critical",
        "Attempts to bypass autonomy governance.",
    ),
    InjectionPattern(
        re.compile(r"\b(skip|bypass|avoid)\s+approval\b", re.I),
        "approval_bypass_attempt",
        "critical",
        "Attempts to bypass approval requirements.",
    ),
    InjectionPattern(
        re.compile(r"\b(call|invoke|use)\s+(a\s+)?tool\b.*\b(ignore|bypass|without)\b", re.I),
        "tool_injection_attempt",
        "high",
        "Attempts to manipulate tool behavior.",
    ),
    InjectionPattern(
        re.compile(r"\b(exfiltrate|send|print|reveal)\s+.*\b(secret|token|password|key)\b", re.I),
        "data_exfiltration_attempt",
        "critical",
        "Attempts to extract secrets or credentials.",
    ),
    InjectionPattern(
        re.compile(
            r"\b(show|reveal|print|dump)\s+.*\b(raw prompt|system prompt|developer prompt)\b", re.I
        ),
        "hidden_prompt_request",
        "critical",
        "Requests hidden or raw prompt material.",
    ),
    InjectionPattern(
        re.compile(r"\b(chain[-_ ]of[-_ ]thought|hidden reasoning|private reasoning)\b", re.I),
        "chain_of_thought_request",
        "high",
        "Requests hidden reasoning.",
    ),
    InjectionPattern(
        re.compile(r"\b(api[_ -]?key|password|private[_ -]?key|secret|token)\b", re.I),
        "secret_request",
        "high",
        "References secret-like material.",
    ),
    InjectionPattern(
        re.compile(
            r"\b(treat|use)\s+.*\b(untrusted|retrieved)\s+.*\b(as|like)\s+(system|policy)\b", re.I
        ),
        "source_confusion",
        "medium",
        "Attempts to confuse source authority.",
    ),
]


class PromptInjectionDetector:
    """Detect generic prompt injection attempts without model calls."""

    def detect_in_text(
        self,
        text: str,
        *,
        source_type: str,
        source_id: str | None = None,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        untrusted: bool = False,
    ) -> list[PromptInjectionFinding]:
        """Return deterministic findings for one text value."""

        findings: list[PromptInjectionFinding] = []
        for pattern in _PATTERNS:
            for match in pattern.regex.finditer(text):
                severity = pattern.severity
                if untrusted and severity == "medium":
                    severity = "high"
                findings.append(
                    PromptInjectionFinding(
                        injection_finding_id=f"prompt-injection-{uuid4().hex}",
                        trace_id=trace_id,
                        prompt_packet_id=prompt_packet_id,
                        source_type=source_type,
                        source_id=source_id,
                        finding_type=pattern.finding_type,  # type: ignore[arg-type]
                        severity=severity,
                        status="open",
                        matched_text_redacted=_safe_match(match.group(0)),
                        reason=pattern.reason,
                        recommended_action=_recommended_action(severity),
                        metadata={"detector": "deterministic"},
                        created_at=datetime.now(UTC),
                    )
                )
        return findings

    def detect_in_sections(
        self,
        sections: list[PromptSection],
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
    ) -> list[PromptInjectionFinding]:
        """Return deterministic findings for prompt sections."""

        findings: list[PromptInjectionFinding] = []
        for section in sections:
            findings.extend(
                self.detect_in_text(
                    section.content,
                    source_type=section.section_type,
                    source_id=section.source_id or section.section_id,
                    trace_id=trace_id,
                    prompt_packet_id=prompt_packet_id,
                    untrusted=section.trust_level == "untrusted_context",
                )
            )
            if section.trust_level == "untrusted_context" and _looks_instructional(section.content):
                findings.append(
                    PromptInjectionFinding(
                        injection_finding_id=f"prompt-injection-{uuid4().hex}",
                        trace_id=trace_id,
                        prompt_packet_id=prompt_packet_id,
                        source_type=section.section_type,
                        source_id=section.source_id or section.section_id,
                        finding_type="untrusted_context_instruction",
                        severity="high",
                        status="open",
                        matched_text_redacted="[redacted]",
                        reason="Untrusted context appears to issue instructions.",
                        recommended_action="block_or_downgrade_section",
                        metadata={"section_id": section.section_id},
                        created_at=datetime.now(UTC),
                    )
                )
        return findings


def _looks_instructional(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("you must", "you should", "ignore", "override"))


def _recommended_action(severity: str) -> str:
    if severity in {"high", "critical"}:
        return "block_or_downgrade_section"
    if severity == "medium":
        return "warn_and_isolate_section"
    return "record_and_continue"


def _safe_match(text: str) -> str:
    redacted, metadata = redact_prompt_text(text)
    if metadata["redacted"]:
        return redacted
    lowered = redacted.lower()
    for marker in ("chain-of-thought", "chain of thought", "hidden reasoning", "raw prompt"):
        lowered = lowered.replace(marker, "[redacted]")
    if lowered != redacted.lower():
        return "[redacted]"
    return redacted[:160]


__all__ = ["PromptInjectionDetector"]

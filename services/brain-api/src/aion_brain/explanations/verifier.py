"""Deterministic explanation verifier."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.explanations import (
    ExplanationRecord,
    ExplanationVerification,
    ExplanationVerificationStatus,
    contains_hidden_reasoning_marker,
    contains_raw_prompt_marker,
)
from aion_brain.contracts.trace_narratives import TraceNarrative, trace_payload_has_hidden_reasoning
from aion_brain.dialogue._shared import emit_telemetry
from aion_brain.explanations.redaction import sanitize_explanation_payload


class ExplanationVerifier:
    """Verify public explanation contracts without external calls."""

    def __init__(self, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def verify_explanation(self, explanation: ExplanationRecord) -> ExplanationVerification:
        """Verify one explanation record."""

        issues = _explanation_issues(explanation)
        verification = ExplanationVerification(
            verification_id=f"explanation-verification-{uuid4().hex}",
            explanation_id=explanation.explanation_id,
            trace_narrative_id=None,
            status=_status(issues),
            grounded=explanation.grounded,
            no_hidden_reasoning=not any(
                issue["code"] == "hidden_reasoning_present" for issue in issues
            ),
            no_secrets=not any(issue["code"] == "secret_like_payload_present" for issue in issues),
            no_raw_prompts=not any(issue["code"] == "raw_prompt_present" for issue in issues),
            issues=issues,
            score=_score(issues),
            created_at=datetime.now(UTC),
        )
        _emit_verification(self._telemetry_service, explanation, verification)
        return verification

    def verify_trace_narrative(self, narrative: TraceNarrative) -> ExplanationVerification:
        """Verify one trace narrative."""

        issues: list[dict[str, Any]] = []
        if contains_hidden_reasoning_marker(
            narrative.summary
        ) or trace_payload_has_hidden_reasoning(narrative.timeline):
            issues.append({"code": "hidden_reasoning_present", "severity": "critical"})
        if contains_raw_prompt_marker(narrative.summary):
            issues.append({"code": "raw_prompt_present", "severity": "critical"})
        _, metadata = sanitize_explanation_payload(narrative.model_dump(mode="json"))
        if metadata["redacted"]:
            issues.append({"code": "secret_like_payload_present", "severity": "critical"})
        if not narrative.audit_refs and not narrative.timeline:
            issues.append({"code": "insufficient_records", "severity": "medium"})
        return ExplanationVerification(
            verification_id=f"trace-narrative-verification-{uuid4().hex}",
            explanation_id=None,
            trace_narrative_id=narrative.trace_narrative_id,
            status=_status(issues),
            grounded=bool(narrative.audit_refs or narrative.timeline),
            no_hidden_reasoning=not any(
                issue["code"] == "hidden_reasoning_present" for issue in issues
            ),
            no_secrets=not any(issue["code"] == "secret_like_payload_present" for issue in issues),
            no_raw_prompts=not any(issue["code"] == "raw_prompt_present" for issue in issues),
            issues=issues,
            score=_score(issues),
            created_at=datetime.now(UTC),
        )


def _explanation_issues(explanation: ExplanationRecord) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    text = f"{explanation.title}\n{explanation.summary}"
    if contains_hidden_reasoning_marker(text):
        issues.append({"code": "hidden_reasoning_present", "severity": "critical"})
    if contains_raw_prompt_marker(text):
        issues.append({"code": "raw_prompt_present", "severity": "critical"})
    _, metadata = sanitize_explanation_payload(explanation.model_dump(mode="json"))
    if metadata["redacted"]:
        issues.append({"code": "secret_like_payload_present", "severity": "critical"})
    if explanation.metadata.get("require_grounding") is True and not explanation.grounded:
        issues.append({"code": "grounding_required_missing", "severity": "high"})
    if explanation.metadata.get("unsupported_capability_claim") is True:
        issues.append({"code": "unsupported_capability_claim", "severity": "high"})
    return issues


def _status(issues: list[dict[str, Any]]) -> ExplanationVerificationStatus:
    if any(issue.get("severity") == "critical" for issue in issues):
        return "failed"
    if issues:
        return "warning"
    return "passed"


def _score(issues: list[dict[str, Any]]) -> float:
    penalty = sum(0.35 if issue.get("severity") == "critical" else 0.2 for issue in issues)
    return max(0.0, min(1.0, 1.0 - penalty))


def _emit_verification(
    telemetry_service: object | None,
    explanation: ExplanationRecord,
    verification: ExplanationVerification,
) -> None:
    event_type = (
        "explanation_verified" if verification.status != "failed" else "explanation_blocked"
    )
    emit_telemetry(
        telemetry_service,
        event_type=event_type,
        node_type="explanation",
        node_id=explanation.explanation_id,
        intensity=0.8 if verification.status == "passed" else 1.0,
        trace_id=explanation.trace_id,
        payload={
            "owner_scope": _scope(explanation),
            "status": verification.status,
            "score": verification.score,
        },
    )


def _scope(explanation: ExplanationRecord) -> list[str]:
    raw = explanation.metadata.get("owner_scope")
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    if explanation.workspace_id:
        return [f"workspace:{explanation.workspace_id}"]
    return ["workspace:main"]


__all__ = ["ExplanationVerifier"]

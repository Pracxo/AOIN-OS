"""Prompt egress guard tests."""

from __future__ import annotations

from tests.model_provider_hardening_helpers import egress_request, services


def test_prompt_egress_guard_rejects_raw_prompt() -> None:
    guard = services()["egress_guard"]

    preview = guard.preview(  # type: ignore[attr-defined]
        egress_request(prompt_summary={"raw_prompt": "do not store"})
    )

    assert preview.status == "blocked"
    assert preview.external_call_allowed is False
    assert "raw_prompt" not in preview.redacted_prompt_summary
    assert preview.blocked_fields == ["raw_prompt"]


def test_prompt_egress_guard_rejects_hidden_reasoning() -> None:
    guard = services()["egress_guard"]

    preview = guard.preview(  # type: ignore[attr-defined]
        egress_request(prompt_summary={"notes": "hidden reasoning goes here"})
    )

    assert preview.status == "blocked"
    assert preview.redacted_prompt_summary["notes"] == "[REDACTED]"
    assert preview.blockers[0]["blocker_type"] == "hidden_reasoning_detected"

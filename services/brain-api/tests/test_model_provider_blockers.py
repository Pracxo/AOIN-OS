"""Model provider blocker tests."""

from __future__ import annotations

from aion_brain.contracts.model_provider_hardening import ModelProviderBlockerDismissRequest
from tests.model_provider_hardening_helpers import egress_request, services


def test_blocker_service_dismiss_does_not_enable_provider() -> None:
    bundle = services()
    guard = bundle["egress_guard"]
    blocker_service = bundle["blocker_service"]
    repo = bundle["repository"]
    guard.preview(egress_request(prompt_summary={"raw_prompt": "do not store"}))  # type: ignore[attr-defined]
    blocker = repo.list_blockers(status="open", limit=1)[0]  # type: ignore[attr-defined]

    dismissed = blocker_service.dismiss_blocker(  # type: ignore[attr-defined]
        blocker.provider_blocker_id,
        ["workspace:main"],
        ModelProviderBlockerDismissRequest(reason="accepted for local review"),
    )

    assert dismissed.status == "dismissed"
    assert dismissed.metadata["provider_enabled"] is False

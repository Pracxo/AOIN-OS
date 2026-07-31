from __future__ import annotations

import pytest

from tests.model_gateway_aion233_test_support import gateway_flow, safe_result_fingerprint


def test_exact_replay_returns_existing_safe_result_and_changed_replay_is_rejected() -> None:
    flow = gateway_flow()
    repo = flow.setup.service.request_repository
    assert repo.check_request_idempotency(flow.request) == ("new", None)
    repo.record_safe_result(
        envelope=flow.request,
        safe_result_fingerprint=safe_result_fingerprint(flow),
        created_at=flow.setup.plan.created_at,
    )
    status, record = repo.check_request_idempotency(flow.request)
    assert status == "exact_replay"
    assert record is not None
    payload = flow.request.model_dump(mode="python")
    payload["safe_metadata_fingerprint"] = "1" * 64
    payload.pop("request_fingerprint", None)
    changed = type(flow.request).model_validate(payload)
    with pytest.raises(ValueError, match="changed replay rejected"):
        repo.check_request_idempotency(changed)

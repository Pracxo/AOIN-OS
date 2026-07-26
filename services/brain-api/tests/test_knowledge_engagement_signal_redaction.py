from __future__ import annotations

import pytest
from knowledge_verified_memory_test_helpers import fp

from aion_brain.contracts.knowledge_verified_memory import EngagementSignalKind
from aion_brain.knowledge_intelligence.engagement_signal_policy import build_engagement_signal


def test_engagement_signal_rejects_raw_user_message_metadata() -> None:
    with pytest.raises(ValueError):
        build_engagement_signal(
            signal_id="signal-raw",
            signal_kind=EngagementSignalKind.RESPONSE_REJECTED,
            session_fingerprint=fp("session"),
            response_fingerprint=fp("response"),
            subject_fingerprint=fp("subject"),
            bounded_outcome_code="raw_user_message",
        )

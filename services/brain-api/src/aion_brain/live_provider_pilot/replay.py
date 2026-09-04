"""Replay checks for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    LiveProviderReplayOutcome,
    LiveProviderReplayRecord,
)


class InMemoryLiveProviderReplayRepository:
    """In-memory replay ledger cleared after evidence projection."""

    def __init__(self) -> None:
        self._records: dict[str, str] = {}

    def record(self, *, request_id: str, request_fingerprint: str) -> None:
        """Record the first request fingerprint."""

        self._records[request_id] = request_fingerprint

    def check_exact_replay(
        self,
        *,
        replay_id: str,
        request_id: str,
        replay_request_fingerprint: str,
        created_at: datetime,
    ) -> LiveProviderReplayRecord:
        """Return exact replay evidence without a provider call."""

        original = self._require(request_id)
        return LiveProviderReplayRecord(
            replay_id=replay_id,
            request_id=request_id,
            original_request_fingerprint=original,
            replay_request_fingerprint=replay_request_fingerprint,
            outcome=LiveProviderReplayOutcome.exact_replay_returned,
            created_at=created_at,
        )

    def reject_changed_replay(
        self,
        *,
        replay_id: str,
        request_id: str,
        replay_request_fingerprint: str,
        created_at: datetime,
    ) -> LiveProviderReplayRecord:
        """Reject changed replay before transport."""

        original = self._require(request_id)
        return LiveProviderReplayRecord(
            replay_id=replay_id,
            request_id=request_id,
            original_request_fingerprint=original,
            replay_request_fingerprint=replay_request_fingerprint,
            outcome=LiveProviderReplayOutcome.changed_replay_rejected,
            created_at=created_at,
        )

    def clear(self) -> None:
        """Clear replay data after evidence projection."""

        self._records = {}

    def _require(self, request_id: str) -> str:
        fingerprint = self._records.get(request_id)
        if fingerprint is None:
            raise ValueError("unknown replay request")
        return fingerprint

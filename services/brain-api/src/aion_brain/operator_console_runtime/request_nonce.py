"""Ephemeral in-memory mutation nonce store for AION-237."""

from __future__ import annotations

import base64
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime

from aion_brain.contracts.operator_console_integration import (
    ALL_RESOURCE_LIMITS,
    OperatorConsoleMutationNonceRecord,
    OperatorConsoleNonceStatus,
    fingerprint_text,
    utc_now,
)


class MutationNonceRejected(ValueError):
    """Raised when a mutation nonce is missing or invalid."""


class StaleMutationNonceRejected(MutationNonceRejected):
    """Raised when a previously valid mutation nonce is replayed."""


@dataclass(frozen=True)
class IssuedMutationNonce:
    raw_nonce: str
    record: OperatorConsoleMutationNonceRecord


class InMemoryMutationNonceStore:
    """Hold one raw mutation nonce per local console session in memory only."""

    def __init__(self) -> None:
        self._raw_by_session: dict[str, str] = {}
        self._record_by_session: dict[str, OperatorConsoleMutationNonceRecord] = {}
        self._seen_fingerprints_by_session: dict[str, set[str]] = {}
        self._rotations_by_session: dict[str, int] = {}

    def issue(
        self,
        *,
        console_session_id: str,
        host: str,
        origin: str,
        expires_at: datetime,
    ) -> IssuedMutationNonce:
        raw_nonce = _generate_raw_nonce()
        generation = self._record_by_session.get(console_session_id)
        next_generation = 1 if generation is None else generation.generation + 1
        record = _record(
            console_session_id=console_session_id,
            raw_nonce=raw_nonce,
            generation=next_generation,
            status=OperatorConsoleNonceStatus.current,
            host=host,
            origin=origin,
            expires_at=expires_at,
        )
        self._raw_by_session[console_session_id] = raw_nonce
        self._record_by_session[console_session_id] = record
        self._seen_fingerprints_by_session.setdefault(console_session_id, set()).add(
            record.nonce_fingerprint
        )
        return IssuedMutationNonce(raw_nonce=raw_nonce, record=record)

    def current_record(self, console_session_id: str) -> OperatorConsoleMutationNonceRecord | None:
        return self._record_by_session.get(console_session_id)

    def current_raw_nonce(self, console_session_id: str) -> str | None:
        return self._raw_by_session.get(console_session_id)

    def validate(
        self,
        *,
        console_session_id: str,
        raw_nonce: str | None,
        host: str,
        origin: str,
        now: datetime | None = None,
    ) -> OperatorConsoleMutationNonceRecord:
        if not raw_nonce:
            raise MutationNonceRejected("mutation nonce missing")
        record = self._record_by_session.get(console_session_id)
        current_raw = self._raw_by_session.get(console_session_id)
        if record is None or current_raw is None:
            raise MutationNonceRejected("mutation nonce invalid")
        validation_time = now or utc_now()
        if record.expires_at <= validation_time:
            raise MutationNonceRejected("mutation nonce expired")
        if record.host_fingerprint != fingerprint_text("host", host):
            raise MutationNonceRejected("mutation nonce host binding mismatch")
        if record.origin_fingerprint != fingerprint_text("origin", origin):
            raise MutationNonceRejected("mutation nonce origin binding mismatch")
        candidate_fingerprint = fingerprint_text("mutation-nonce", raw_nonce)
        if not hmac.compare_digest(raw_nonce, current_raw):
            seen = self._seen_fingerprints_by_session.get(console_session_id, set())
            if candidate_fingerprint in seen:
                raise StaleMutationNonceRejected("mutation nonce stale")
            raise MutationNonceRejected("mutation nonce invalid")
        return record

    def consume_and_rotate(
        self,
        *,
        console_session_id: str,
        raw_nonce: str,
        host: str,
        origin: str,
        expires_at: datetime,
    ) -> IssuedMutationNonce:
        current = self.validate(
            console_session_id=console_session_id,
            raw_nonce=raw_nonce,
            host=host,
            origin=origin,
        )
        rotations = self._rotations_by_session.get(console_session_id, 0)
        if rotations >= ALL_RESOURCE_LIMITS["maximum_mutation_nonce_rotations_per_session"]:
            raise MutationNonceRejected("mutation nonce rotation limit exceeded")
        consumed = current.model_copy(update={"status": OperatorConsoleNonceStatus.consumed})
        self._record_by_session[console_session_id] = consumed
        self._rotations_by_session[console_session_id] = rotations + 1
        return self.issue(
            console_session_id=console_session_id,
            host=host,
            origin=origin,
            expires_at=expires_at,
        )

    def invalidate(self, console_session_id: str) -> OperatorConsoleMutationNonceRecord | None:
        raw_nonce = self._raw_by_session.pop(console_session_id, None)
        record = self._record_by_session.get(console_session_id)
        if raw_nonce is not None:
            self._seen_fingerprints_by_session.setdefault(console_session_id, set()).add(
                fingerprint_text("mutation-nonce", raw_nonce)
            )
        if record is None:
            return None
        invalidated = record.model_copy(update={"status": OperatorConsoleNonceStatus.invalidated})
        self._record_by_session[console_session_id] = invalidated
        return invalidated

    def clear(self) -> None:
        self._raw_by_session.clear()
        self._record_by_session.clear()
        self._seen_fingerprints_by_session.clear()
        self._rotations_by_session.clear()

    def rotation_count(self, console_session_id: str) -> int:
        return self._rotations_by_session.get(console_session_id, 0)


def _generate_raw_nonce() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")


def _record(
    *,
    console_session_id: str,
    raw_nonce: str,
    generation: int,
    status: OperatorConsoleNonceStatus,
    host: str,
    origin: str,
    expires_at: datetime,
) -> OperatorConsoleMutationNonceRecord:
    return OperatorConsoleMutationNonceRecord(
        console_session_id=console_session_id,
        nonce_fingerprint=fingerprint_text("mutation-nonce", raw_nonce),
        generation=generation,
        status=status,
        host_fingerprint=fingerprint_text("host", host),
        origin_fingerprint=fingerprint_text("origin", origin),
        issued_at=utc_now(),
        expires_at=expires_at,
    )

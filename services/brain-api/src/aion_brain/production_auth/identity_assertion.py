"""Canonical helpers for offline identity assertion verification."""

from __future__ import annotations

import base64
import binascii
import re
from typing import Any

from pydantic import BaseModel

from aion_brain.contracts.identity_assertion import (
    DOMAIN_SEPARATOR,
    MAXIMUM_PAYLOAD_CANONICAL_BYTES,
)
from aion_brain.production_auth.canonical import canonical_json_bytes

_BASE64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def encode_base64url_unpadded(value: bytes) -> str:
    """Return strict unpadded base64url text for bytes."""

    if not isinstance(value, bytes) or not value:
        raise ValueError("base64url input must be non-empty bytes")
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def decode_base64url_unpadded(value: str, expected_length: int | None = None) -> bytes:
    """Decode strict unpadded base64url without reflecting attacker input."""

    if not isinstance(value, str) or not value:
        raise ValueError("base64url value is malformed")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("base64url value is malformed") from exc
    if "=" in value or not _BASE64URL_RE.fullmatch(value):
        raise ValueError("base64url value is malformed")
    if len(value) % 4 == 1:
        raise ValueError("base64url value is malformed")
    padded = value + ("=" * ((4 - len(value) % 4) % 4))
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (binascii.Error, ValueError) as exc:
        raise ValueError("base64url value is malformed") from exc
    if encode_base64url_unpadded(decoded) != value:
        raise ValueError("base64url value is malformed")
    if expected_length is not None and len(decoded) != expected_length:
        raise ValueError("base64url value length is invalid")
    return decoded


def identity_assertion_payload_bytes(payload: Any) -> bytes:
    """Return canonical payload bytes, excluding envelope key ID and signature."""

    if isinstance(payload, BaseModel):
        value = payload.model_dump(mode="json")
    else:
        value = payload
    canonical = canonical_json_bytes(value)
    if len(canonical) > MAXIMUM_PAYLOAD_CANONICAL_BYTES:
        raise ValueError("payload canonical JSON exceeds maximum size")
    return canonical


def identity_assertion_signing_input(payload: Any) -> bytes:
    """Return domain-separated canonical signing input for Ed25519 verification."""

    return DOMAIN_SEPARATOR + identity_assertion_payload_bytes(payload)


__all__ = [
    "decode_base64url_unpadded",
    "encode_base64url_unpadded",
    "identity_assertion_payload_bytes",
    "identity_assertion_signing_input",
]

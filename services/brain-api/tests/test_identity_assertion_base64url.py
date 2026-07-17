from __future__ import annotations

import pytest

from aion_brain.production_auth.identity_assertion import (
    decode_base64url_unpadded,
    encode_base64url_unpadded,
)


def test_base64url_round_trip_is_unpadded() -> None:
    encoded = encode_base64url_unpadded(b"abc123")
    assert encoded == "YWJjMTIz"
    assert decode_base64url_unpadded(encoded) == b"abc123"


@pytest.mark.parametrize("value", ["YQ==", "ab+c", "ab/c", "ab c", "", "abcde", "é"])
def test_malformed_base64url_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="base64url value"):
        decode_base64url_unpadded(value)


def test_expected_length_is_enforced() -> None:
    encoded = encode_base64url_unpadded(b"abc")
    with pytest.raises(ValueError, match="length"):
        decode_base64url_unpadded(encoded, expected_length=32)


def test_non_canonical_encoding_is_rejected() -> None:
    with pytest.raises(ValueError):
        decode_base64url_unpadded("AA===")

"""Release checksum tests."""

from __future__ import annotations

import hashlib

from aion_brain.release_package.checksums import root_checksum, sha256_bytes, sha256_file


def test_sha256_helpers_are_deterministic(tmp_path) -> None:
    path = tmp_path / "README.md"
    path.write_bytes(b"aion")

    assert sha256_file(path) == hashlib.sha256(b"aion").hexdigest()
    assert sha256_bytes(b"aion") == hashlib.sha256(b"aion").hexdigest()


def test_root_checksum_is_order_independent() -> None:
    first = root_checksum({"b": "2", "a": "1"})
    second = root_checksum({"a": "1", "b": "2"})

    assert first == second

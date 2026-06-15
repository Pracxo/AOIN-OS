"""Backup checksum tests."""

from __future__ import annotations

from aion_brain.backups.checksums import root_checksum, sha256_file, sha256_jsonl_records


def test_sha256_jsonl_records_is_deterministic_by_record_id() -> None:
    first = sha256_jsonl_records([{"id": "b", "value": 2}, {"id": "a", "value": 1}])
    second = sha256_jsonl_records([{"id": "a", "value": 1}, {"id": "b", "value": 2}])

    assert first == second


def test_sha256_file_and_root_checksum(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "data.jsonl"
    path.write_text('{"id":"a"}\n', encoding="utf-8")
    checksum = sha256_file(path)

    assert checksum
    assert root_checksum({"resources/data.jsonl": checksum}) == root_checksum(
        {"resources/data.jsonl": checksum}
    )

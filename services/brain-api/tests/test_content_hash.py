"""Content hash tests."""

from aion_brain.evidence.content_hash import normalize_text_for_hash, sha256_text


def test_content_hash_is_deterministic() -> None:
    """Same content hashes the same way."""
    assert sha256_text("alpha beta") == sha256_text("alpha beta")


def test_content_hash_normalizes_line_endings_and_trailing_whitespace() -> None:
    """Line ending normalization preserves stable content addressing."""
    assert sha256_text("alpha \r\nbeta  \n") == sha256_text("alpha\nbeta\n")
    assert normalize_text_for_hash("alpha  \r\nbeta\t") == "alpha\nbeta"


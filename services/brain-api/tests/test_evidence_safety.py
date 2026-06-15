"""Evidence safety boundary tests."""

import re
from pathlib import Path

from tests.test_evidence_service import make_ingest_request, make_service


class FailingObjectStore:
    """Object store fake that proves ingestion does not touch object storage."""

    def put_bytes(self, data: bytes, media_type: str, metadata: dict[str, object]) -> object:
        raise AssertionError("binary object storage should not be used in v0.1")

    def get_bytes(self, content_ref: str) -> bytes:
        raise AssertionError("metadata-only refs must not be fetched")

    def delete(self, content_ref: str) -> bool:
        raise AssertionError("object deletion is not part of evidence soft delete")


def test_no_url_fetch_happens_for_url_metadata() -> None:
    """URL metadata is stored without network fetches."""
    service = make_service()

    response = service.ingest(
        make_ingest_request(
            content_text=None,
            content_ref="https://example.invalid/source",
            source_type="url_metadata",
        )
    )

    assert response.chunk_count == 0
    assert response.evidence.content_ref == "https://example.invalid/source"


def test_no_binary_upload_or_object_storage_is_required() -> None:
    """Text and metadata-only ingestion avoid object storage."""
    service = make_service()
    service._object_store = FailingObjectStore()  # noqa: SLF001

    response = service.ingest(make_ingest_request(content_text="alpha beta"))

    assert response.ingested is True


def test_no_pdf_parsing_ocr_external_storage_sdk_or_domain_logic_exists() -> None:
    """Evidence source stays free of forbidden v0.1 integrations."""
    evidence_root = Path("src/aion_brain/evidence")
    storage_root = Path("src/aion_brain/storage")
    text = "\n".join(
        path.read_text()
        for root in (evidence_root, storage_root)
        for path in root.glob("*.py")
    ).lower()

    forbidden_terms = [
        "pypdf",
        "pdfplumber",
        "ocr",
        "tesseract",
        "boto3",
        "finance",
        "trading",
        "healthcare",
        "procurement",
    ]
    forbidden_imports = [r"(^|\n)\s*import\s+minio\b", r"(^|\n)\s*from\s+minio\b"]
    assert not any(term in text for term in forbidden_terms)
    assert not any(re.search(pattern, text) for pattern in forbidden_imports)

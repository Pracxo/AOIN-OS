"""MinIO object storage adapter placeholder."""

from aion_brain.contracts.evidence import ObjectRef


class MinIOAdapter:
    """MinIO is planned as AION's S3-compatible object storage adapter.

    AION contracts must remain independent of MinIO internals.
    """

    def put_bytes(self, data: bytes, media_type: str, metadata: dict[str, object]) -> ObjectRef:
        """MinIO writes are not implemented in v0.1."""
        raise NotImplementedError("MinIO object storage is reserved for a later AION task.")

    def get_bytes(self, content_ref: str) -> bytes:
        """MinIO reads are not implemented in v0.1."""
        raise NotImplementedError("MinIO object storage is reserved for a later AION task.")

    def delete(self, content_ref: str) -> bool:
        """MinIO deletes are not implemented in v0.1."""
        raise NotImplementedError("MinIO object storage is reserved for a later AION task.")

"""In-memory object store for tests."""

from aion_brain.contracts.evidence import ObjectRef, reject_secret_metadata
from aion_brain.evidence.content_hash import sha256_bytes


class InMemoryObjectStore:
    """Process-local object store for tests."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put_bytes(self, data: bytes, media_type: str, metadata: dict[str, object]) -> ObjectRef:
        """Store bytes in memory."""
        reject_secret_metadata(metadata)
        content_hash = sha256_bytes(data)
        content_ref = f"memory://objects/{content_hash}"
        self._objects[content_ref] = data
        return ObjectRef(
            content_ref=content_ref,
            content_hash=content_hash,
            media_type=media_type,
            size_bytes=len(data),
            metadata=dict(metadata),
        )

    def get_bytes(self, content_ref: str) -> bytes:
        """Read bytes from memory."""
        return self._objects[content_ref]

    def delete(self, content_ref: str) -> bool:
        """Delete bytes from memory."""
        return self._objects.pop(content_ref, None) is not None

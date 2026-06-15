"""Object storage adapter interface."""

from typing import Protocol

from aion_brain.contracts.evidence import ObjectRef


class ObjectStoreAdapter(Protocol):
    """Boundary for future object storage engines."""

    def put_bytes(self, data: bytes, media_type: str, metadata: dict[str, object]) -> ObjectRef:
        """Store bytes and return an AION object reference."""
        ...

    def get_bytes(self, content_ref: str) -> bytes:
        """Read bytes for an AION object reference."""
        ...

    def delete(self, content_ref: str) -> bool:
        """Delete bytes for an AION object reference."""
        ...


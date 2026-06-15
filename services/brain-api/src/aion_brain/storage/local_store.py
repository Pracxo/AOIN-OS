"""Local filesystem object store adapter."""

from pathlib import Path

from aion_brain.contracts.evidence import ObjectRef, reject_secret_metadata
from aion_brain.evidence.content_hash import sha256_bytes


class LocalObjectStore:
    """Store bytes under a configured local object root."""

    def __init__(self, object_root: str) -> None:
        self._root = Path(object_root)

    def put_bytes(self, data: bytes, media_type: str, metadata: dict[str, object]) -> ObjectRef:
        """Store bytes locally using the content hash as the filename."""
        reject_secret_metadata(metadata)
        content_hash = sha256_bytes(data)
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._root / content_hash
        path.write_bytes(data)
        return ObjectRef(
            content_ref=f"local://objects/{content_hash}",
            content_hash=content_hash,
            media_type=media_type,
            size_bytes=len(data),
            metadata=dict(metadata),
        )

    def get_bytes(self, content_ref: str) -> bytes:
        """Read local bytes by content reference."""
        return self._path_for_ref(content_ref).read_bytes()

    def delete(self, content_ref: str) -> bool:
        """Delete local bytes by content reference."""
        path = self._path_for_ref(content_ref)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _path_for_ref(self, content_ref: str) -> Path:
        prefix = "local://objects/"
        if not content_ref.startswith(prefix):
            raise ValueError("unsupported local content_ref")
        return self._root / content_ref.removeprefix(prefix)


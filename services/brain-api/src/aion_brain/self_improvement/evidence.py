"""Evidence redaction helpers for governed self-improvement."""

from __future__ import annotations

from typing import Any, NoReturn

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)
SENSITIVE_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin " "private key-----")


def redact_evidence_payload(value: Any) -> Any:
    """Return a deterministic, immutable evidence payload with obvious secrets redacted."""

    return _freeze_redacted(_redact(value))


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if any(part in normalized_key for part in SENSITIVE_KEY_PARTS):
                redacted[str(key)] = REDACTED
            else:
                redacted[str(key)] = _redact(nested)
        return redacted
    if isinstance(value, list | tuple):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in SENSITIVE_VALUE_MARKERS):
            return REDACTED
    return value


class _FrozenRedactedDict(dict[str, Any]):
    """Immutable dict for already-redacted evidence payloads."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("self-improvement redacted evidence is immutable")

    def __setitem__(self, key: str, value: Any) -> NoReturn:
        self._blocked(key, value)

    def __delitem__(self, key: str) -> NoReturn:
        self._blocked(key)

    def clear(self) -> NoReturn:
        self._blocked()

    def pop(self, key: str, default: Any = None) -> NoReturn:  # noqa: ARG002
        self._blocked(key, default)

    def popitem(self) -> NoReturn:
        self._blocked()

    def setdefault(self, key: str, default: Any = None) -> NoReturn:
        self._blocked(key, default)

    def update(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._blocked(*args, **kwargs)


def _freeze_redacted(value: Any) -> Any:
    if isinstance(value, dict):
        return _FrozenRedactedDict(
            {str(key): _freeze_redacted(nested) for key, nested in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze_redacted(item) for item in value)
    return value

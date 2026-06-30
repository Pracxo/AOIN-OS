"""Connector credential secret redaction preview."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.contracts.connector_credentials import ConnectorSecretRedactionResult, utc_now
from aion_brain.dialogue._shared import emit_telemetry

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
}
_TOKEN_KEY_PARTS = {"access_token", "refresh_token", "id_token", "token"}
_SECRET_VALUE_MARKERS = (
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
    "bearer ",
    "basic ",
)
_REDACTED = "[REDACTED]"


class ConnectorSecretRedactionService:
    """Redact secret-like payload fields without persisting the payload."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def preview(self, payload: dict[str, Any]) -> ConnectorSecretRedactionResult:
        """Return a redacted copy and detection metadata."""

        blocked_fields: list[str] = []
        secret_detected = False
        token_detected = False
        credential_field_detected = False
        redacted = _redact_payload(
            payload,
            path=(),
            blocked_fields=blocked_fields,
            flags={
                "secret_detected": False,
                "token_detected": False,
                "credential_field_detected": False,
            },
        )
        secret_detected = bool(_redact_payload.flags["secret_detected"])  # type: ignore[attr-defined]
        token_detected = bool(_redact_payload.flags["token_detected"])  # type: ignore[attr-defined]
        credential_field_detected = bool(
            _redact_payload.flags["credential_field_detected"]  # type: ignore[attr-defined]
        )
        result = ConnectorSecretRedactionResult(
            redaction_id=f"connector-secret-redaction-{uuid4().hex}",
            status="redacted" if blocked_fields else "clear",
            redaction_applied=bool(blocked_fields),
            secret_detected=secret_detected,
            token_detected=token_detected,
            credential_field_detected=credential_field_detected,
            redacted_payload=redacted if isinstance(redacted, dict) else {},
            blocked_fields=blocked_fields,
            warnings=[
                {
                    "code": "redaction_preview_only",
                    "status": "open",
                }
            ],
            metadata={
                "storage_allowed": False,
                "credential_access_allowed": False,
                "token_access_allowed": False,
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_secret_redaction_previewed",
            node_type="connector_secret_redaction",
            node_id=result.redaction_id,
            intensity=0.7 if result.redaction_applied else 0.45,
            trace_id=result.redaction_id,
            payload={"redaction_applied": result.redaction_applied, "storage_allowed": False},
        )
        return result


def _redact_payload(
    value: Any,
    *,
    path: tuple[str, ...],
    blocked_fields: list[str],
    flags: dict[str, bool],
) -> Any:
    _redact_payload.flags = flags  # type: ignore[attr-defined]
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            key_text = str(key)
            nested_path = (*path, key_text)
            if _field_should_be_redacted(key_text, nested):
                lowered = key_text.lower()
                flags["secret_detected"] = flags["secret_detected"] or _is_secret_key(lowered)
                flags["token_detected"] = flags["token_detected"] or _is_token_key(lowered)
                flags["credential_field_detected"] = (
                    flags["credential_field_detected"] or "credential" in lowered
                )
                blocked_fields.append(".".join(nested_path))
                redacted[key_text] = _REDACTED
            else:
                redacted[key_text] = _redact_payload(
                    nested,
                    path=nested_path,
                    blocked_fields=blocked_fields,
                    flags=flags,
                )
        return redacted
    if isinstance(value, list):
        return [
            _redact_payload(
                item,
                path=(*path, str(index)),
                blocked_fields=blocked_fields,
                flags=flags,
            )
            for index, item in enumerate(value)
        ]
    if isinstance(value, str) and _value_has_secret_marker(value):
        flags["secret_detected"] = True
        blocked_fields.append(".".join(path) if path else "payload")
        return _REDACTED
    return value


def _field_should_be_redacted(key: str, value: Any) -> bool:
    lowered = key.lower()
    return _is_secret_key(lowered) or _is_token_key(lowered) or (
        isinstance(value, str) and _value_has_secret_marker(value)
    )


def _is_secret_key(lowered: str) -> bool:
    return any(part in lowered for part in _SECRET_KEY_PARTS)


def _is_token_key(lowered: str) -> bool:
    return any(part in lowered for part in _TOKEN_KEY_PARTS)


def _value_has_secret_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _SECRET_VALUE_MARKERS)


__all__ = ["ConnectorSecretRedactionService"]

"""Bounded request parsing and routing for the AION-237 local bridge."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import count
from typing import Any

from pydantic import ValidationError

from aion_brain.contracts.operator_console_integration import (
    ALL_RESOURCE_LIMITS,
    CONTENT_SECURITY_POLICY,
    MUTATION_NONCE_REQUEST_HEADER,
    MUTATION_NONCE_RESPONSE_HEADER,
    OPERATOR_CONFIRMATION_HEADER,
    SECURITY_HEADERS,
    OperatorConsoleHttpDisposition,
    json_depth,
    json_item_count,
    reject_protected_material,
)
from aion_brain.operator_console_runtime.origin_policy import (
    validate_fetch_metadata,
    validate_forwarded_headers,
    validate_host_header,
    validate_origin_header,
    validate_request_target,
)
from aion_brain.operator_console_runtime.request_nonce import (
    MutationNonceRejected,
    StaleMutationNonceRejected,
)


@dataclass(frozen=True)
class RouterResponse:
    status_code: int
    body: dict[str, Any]
    disposition: OperatorConsoleHttpDisposition
    headers: dict[str, str] = field(default_factory=dict)
    terminal: bool = False


class BoundedJsonRequestParser:
    """Parse JSON POST requests with strict local-console limits."""

    def parse(self, *, headers: Mapping[str, Sequence[str]], body: bytes) -> dict[str, Any]:
        content_length_values = _header_values(headers, "Content-Length")
        if len(content_length_values) != 1:
            raise RequestParseError("content length rejected", status_code=400)
        try:
            content_length = int(content_length_values[0])
        except ValueError as exc:
            raise RequestParseError("content length rejected", status_code=400) from exc
        if content_length < 0:
            raise RequestParseError("content length rejected", status_code=400)
        if content_length > ALL_RESOURCE_LIMITS["maximum_request_body_bytes"]:
            raise RequestParseError("request body too large", status_code=413)
        if len(body) != content_length:
            raise RequestParseError("request body length mismatch", status_code=400)
        if _header_values(headers, "Transfer-Encoding"):
            raise RequestParseError("transfer encoding rejected", status_code=400)
        if _header_values(headers, "Content-Encoding"):
            raise RequestParseError("content encoding rejected", status_code=400)
        if _header_values(headers, "Expect"):
            raise RequestParseError("expect header rejected", status_code=400)
        content_type = _header_values(headers, "Content-Type")
        if len(content_type) != 1 or content_type[0] != "application/json":
            raise RequestParseError("unsupported content type", status_code=415)
        try:
            text = body.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise RequestParseError("request body rejected", status_code=400) from exc
        try:
            payload = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_json_constant,
            )
        except ValueError as exc:
            raise RequestParseError("malformed JSON", status_code=400) from exc
        if not isinstance(payload, dict):
            raise RequestParseError("JSON root must be an object", status_code=400)
        if json_depth(payload) > ALL_RESOURCE_LIMITS["maximum_json_depth"]:
            raise RequestParseError("JSON depth exceeded", status_code=400)
        if json_item_count(payload) > ALL_RESOURCE_LIMITS["maximum_json_items_per_request"]:
            raise RequestParseError("JSON item count exceeded", status_code=400)
        try:
            reject_protected_material(payload)
        except ValueError as exc:
            raise RequestParseError("protected material rejected", status_code=400) from exc
        return payload


class RequestParseError(ValueError):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class OperatorConsoleRequestRouter:
    """Route the exact ten local API endpoints to the in-memory bridge service."""

    def __init__(self, *, service: Any, port: int) -> None:
        self.service = service
        self.port = port
        self.parser = BoundedJsonRequestParser()
        self._request_counter = count(1)

    def handle(
        self,
        *,
        method: str,
        target: str,
        headers: Mapping[str, Sequence[str]],
        body: bytes = b"",
    ) -> RouterResponse:
        method = method.upper()
        request_id = f"local-http-{next(self._request_counter)}"
        try:
            validate_request_target(target, method=method)
            validate_forwarded_headers(tuple(headers))
            validate_fetch_metadata(_first_header(headers, "Sec-Fetch-Site"), method=method)
            host = validate_host_header(_header_values(headers, "Host"), port=self.port)
            origin = validate_origin_header(
                _header_values(headers, "Origin"),
                method=method,
                port=self.port,
            )
        except ValueError as exc:
            status = 403 if "Host" in str(exc) or "Origin" in str(exc) else 400
            return _error(status, "request_boundary_rejected")

        route_path = target.partition("?")[0]
        if method in {"OPTIONS", "HEAD"}:
            return _error(405, "method_not_allowed")
        if route_path not in _AUTHORIZED_API_ROUTES:
            return _error(404, "route_not_found")
        if method != _AUTHORIZED_API_ROUTES[route_path]:
            return _error(405, "method_not_allowed")
        if method == "GET":
            return self._handle_get(route_path, host=host, origin=origin)
        return self._handle_post(
            route_path=route_path,
            headers=headers,
            body=body,
            host=host,
            origin=origin,
            request_id=request_id,
        )

    def _handle_get(self, route_path: str, *, host: str, origin: str) -> RouterResponse:
        if route_path == "/aion/local/v1/bootstrap":
            payload, raw_nonce = self.service.bootstrap(host=host, origin=origin)
            return RouterResponse(
                status_code=200,
                body=payload,
                disposition=OperatorConsoleHttpDisposition.served,
                headers={MUTATION_NONCE_RESPONSE_HEADER: raw_nonce},
            )
        if route_path == "/aion/local/v1/status":
            return _ok(self.service.status())
        if route_path == "/aion/local/v1/health":
            return _ok(self.service.health(listener_active=True))
        if route_path == "/aion/local/v1/observability":
            return _ok(self.service.observability())
        if route_path == "/aion/local/v1/audit":
            return _ok(self.service.audit())
        return _error(404, "route_not_found")

    def _handle_post(
        self,
        *,
        route_path: str,
        headers: Mapping[str, Sequence[str]],
        body: bytes,
        host: str,
        origin: str,
        request_id: str,
    ) -> RouterResponse:
        try:
            payload = self.parser.parse(headers=headers, body=body)
        except RequestParseError as exc:
            return _error(exc.status_code, "request_body_rejected")
        header_confirmation = _first_header(headers, OPERATOR_CONFIRMATION_HEADER)
        if header_confirmation:
            payload = {**payload, "operator_confirmation": header_confirmation}
        if self.service.is_killed() and route_path not in {
            "/aion/local/v1/kill",
            "/aion/local/v1/session/close",
        }:
            self.service.block_after_kill(request_id)
            return _error(410, "request_blocked_by_kill_switch")
        raw_nonce = _first_header(headers, MUTATION_NONCE_REQUEST_HEADER)
        terminal = route_path in {"/aion/local/v1/kill", "/aion/local/v1/session/close"}
        try:
            self.service.validate_nonce(raw_nonce=raw_nonce, host=host, origin=origin)
        except StaleMutationNonceRejected:
            return _error(409, "stale_mutation_nonce")
        except MutationNonceRejected:
            return _error(403, "mutation_nonce_rejected")

        replacement_nonce: str | None = None
        if not terminal:
            try:
                replacement_nonce = self.service.rotate_nonce(
                    raw_nonce=raw_nonce or "",
                    host=host,
                    origin=origin,
                )
            except MutationNonceRejected:
                return _error(403, "mutation_nonce_rejected")

        try:
            if route_path == "/aion/local/v1/model/simulate":
                result = self.service.simulate_model(payload)
            elif route_path == "/aion/local/v1/capability/execute":
                result = self.service.execute_capability(payload)
            elif route_path == "/aion/local/v1/connector/simulate":
                result = self.service.simulate_connector(payload)
            elif route_path == "/aion/local/v1/kill":
                result = self.service.kill(payload)
            elif route_path == "/aion/local/v1/session/close":
                result = self.service.close(payload)
            else:
                return _error(404, "route_not_found")
        except ValidationError:
            return _error(400, "request_schema_rejected")
        except PermissionError:
            headers_out = {}
            if replacement_nonce is not None:
                headers_out[MUTATION_NONCE_RESPONSE_HEADER] = replacement_nonce
            return _error(409, "request_blocked", headers=headers_out)
        except ValueError:
            headers_out = {}
            if replacement_nonce is not None:
                headers_out[MUTATION_NONCE_RESPONSE_HEADER] = replacement_nonce
            return _error(400, "request_rejected", headers=headers_out)

        if terminal:
            self.service.invalidate_nonce()
        headers_out = {}
        if replacement_nonce is not None:
            headers_out[MUTATION_NONCE_RESPONSE_HEADER] = replacement_nonce
        return RouterResponse(
            status_code=200,
            body=result,
            disposition=(
                OperatorConsoleHttpDisposition.killed
                if route_path == "/aion/local/v1/kill"
                else (
                    OperatorConsoleHttpDisposition.closed
                    if route_path == "/aion/local/v1/session/close"
                    else OperatorConsoleHttpDisposition.accepted
                )
            ),
            headers=headers_out,
            terminal=terminal,
        )


_AUTHORIZED_API_ROUTES: dict[str, str] = {
    "/aion/local/v1/bootstrap": "GET",
    "/aion/local/v1/status": "GET",
    "/aion/local/v1/health": "GET",
    "/aion/local/v1/observability": "GET",
    "/aion/local/v1/audit": "GET",
    "/aion/local/v1/model/simulate": "POST",
    "/aion/local/v1/capability/execute": "POST",
    "/aion/local/v1/connector/simulate": "POST",
    "/aion/local/v1/kill": "POST",
    "/aion/local/v1/session/close": "POST",
}


def _ok(payload: dict[str, Any]) -> RouterResponse:
    return RouterResponse(
        status_code=200,
        body=payload,
        disposition=OperatorConsoleHttpDisposition.served,
    )


def _error(
    status_code: int,
    code: str,
    *,
    headers: Mapping[str, str] | None = None,
) -> RouterResponse:
    return RouterResponse(
        status_code=status_code,
        body={"ok": False, "error_code": code},
        disposition=OperatorConsoleHttpDisposition.rejected,
        headers=dict(headers or {}),
    )


def response_headers(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    headers = dict(SECURITY_HEADERS)
    headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
    headers.update(dict(extra or {}))
    return headers


def response_body_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _header_values(headers: Mapping[str, Sequence[str]], name: str) -> tuple[str, ...]:
    values: list[str] = []
    for key, nested in headers.items():
        if key.lower() == name.lower():
            values.extend(str(item) for item in nested)
    return tuple(values)


def _first_header(headers: Mapping[str, Sequence[str]], name: str) -> str | None:
    values = _header_values(headers, name)
    return values[0] if len(values) == 1 else None


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"unsupported JSON constant: {value}")

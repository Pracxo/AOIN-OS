"""Loopback-only HTTP server for the AION-237 local console bridge."""

from __future__ import annotations

import http.server
import ipaddress
import json
import socket
import socketserver
import threading
import time
from collections.abc import Mapping, Sequence
from typing import Any, cast

from aion_brain.contracts.operator_console_integration import (
    ALL_RESOURCE_LIMITS,
    LOOPBACK_BIND_HOST,
    SECURITY_HEADERS,
    STATIC_ASSET_ROUTES,
    OperatorConsoleHttpDisposition,
    OperatorConsoleStaticAsset,
    fingerprint_bytes,
    static_asset_manifest_from_bytes,
)
from aion_brain.operator_console_runtime.origin_policy import validate_request_target
from aion_brain.operator_console_runtime.request_router import (
    OperatorConsoleRequestRouter,
    RouterResponse,
    response_body_bytes,
    response_headers,
)
from aion_brain.operator_console_runtime.session_bridge import (
    ControlledLocalOperatorConsoleService,
)


class ControlledLoopbackHttpServer:
    """One explicit local listener serving exact static assets and ten API routes."""

    def __init__(self, *, assets: Mapping[str, bytes], port: int = 0) -> None:
        _validate_numeric_loopback()
        if port < 0 or port > 65535:
            raise ValueError("invalid local port")
        manifest = static_asset_manifest_from_bytes(assets)
        httpd = _BoundedThreadingHttpServer((LOOPBACK_BIND_HOST, port), _Handler)
        actual_port = int(httpd.server_address[1])
        service = ControlledLocalOperatorConsoleService(
            bound_port=actual_port,
            static_asset_manifest=manifest,
        )
        httpd.assets_by_route = {asset.route_path: asset for asset in manifest.assets}
        httpd.router = OperatorConsoleRequestRouter(service=service, port=actual_port)
        httpd.started_at = time.time()
        self._httpd = httpd
        self._thread: threading.Thread | None = None
        self._closed = False
        self.service = service
        self.static_asset_manifest = manifest
        self.bound_port = actual_port

    @property
    def base_url(self) -> str:
        return f"http://{LOOPBACK_BIND_HOST}:{self.bound_port}"

    @property
    def closed(self) -> bool:
        return self._closed

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("local console listener already started")
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="aion-operator-console-loopback",
        )
        self._thread.start()

    def shutdown(self) -> None:
        if self._closed:
            return
        self.service.cleanup()
        if self._thread is not None:
            self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._closed = True


class _BoundedThreadingHttpServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = False
    block_on_close = True
    address_family = socket.AF_INET
    request_queue_size = ALL_RESOURCE_LIMITS["maximum_concurrent_requests"]

    assets_by_route: dict[str, OperatorConsoleStaticAsset]
    router: OperatorConsoleRequestRouter
    started_at: float

    def __init__(
        self,
        server_address: tuple[str, int],
        handler: type[http.server.BaseHTTPRequestHandler],
    ):
        self._semaphore = threading.BoundedSemaphore(
            ALL_RESOURCE_LIMITS["maximum_concurrent_requests"]
        )
        super().__init__(server_address, handler)

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)

    def process_request(self, request: Any, client_address: Any) -> None:
        if not self._semaphore.acquire(blocking=False):
            request.close()
            return
        super().process_request(request, client_address)

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._semaphore.release()


class _Handler(http.server.BaseHTTPRequestHandler):
    server_version = "AIONLocalConsole/1"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    def do_HEAD(self) -> None:
        self._send_router_response(
            RouterResponse(
                status_code=405,
                body={"ok": False, "error_code": "method_not_allowed"},
                disposition=OperatorConsoleHttpDisposition.rejected,
            )
        )

    def do_OPTIONS(self) -> None:
        self._send_router_response(
            RouterResponse(
                status_code=405,
                body={"ok": False, "error_code": "method_not_allowed"},
                disposition=OperatorConsoleHttpDisposition.rejected,
            )
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle(self) -> None:
        server = cast(_BoundedThreadingHttpServer, self.server)
        method = self.command.upper()
        if method == "GET" and self.path in STATIC_ASSET_ROUTES:
            self._serve_static(server.assets_by_route)
            return
        headers = _headers_from_request(tuple(self.headers.raw_items()))
        body = self._read_body(headers)
        response = server.router.handle(
            method=method,
            target=self.path,
            headers=headers,
            body=body,
        )
        self._send_router_response(response)

    def _serve_static(self, assets_by_route: Mapping[str, OperatorConsoleStaticAsset]) -> None:
        try:
            validate_request_target(self.path, method="GET")
        except ValueError:
            self._send_static_error(400, "static_target_rejected")
            return
        if "?" in self.path:
            self._send_static_error(404, "static_route_not_found")
            return
        asset = assets_by_route.get(self.path)
        if asset is None:
            self._send_static_error(404, "static_route_not_found")
            return
        body = asset.content
        headers = response_headers()
        headers["Content-Type"] = asset.mime_type
        headers["Content-Length"] = str(len(body))
        headers["X-AION-Static-Asset-Fingerprint"] = asset.asset_fingerprint or fingerprint_bytes(
            "static-asset",
            body,
        )
        self.send_response(200)
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_static_error(self, status_code: int, code: str) -> None:
        self._send_router_response(
            RouterResponse(
                status_code=status_code,
                body={"ok": False, "error_code": code},
                disposition=OperatorConsoleHttpDisposition.rejected,
            )
        )

    def _read_body(self, headers: Mapping[str, Sequence[str]]) -> bytes:
        values = tuple(headers.get("Content-Length", ()))
        if len(values) != 1:
            return b""
        try:
            length = int(values[0])
        except ValueError:
            return b""
        if length <= 0 or length > ALL_RESOURCE_LIMITS["maximum_request_body_bytes"]:
            return b""
        return self.rfile.read(length)

    def _send_router_response(self, response: RouterResponse) -> None:
        body = response_body_bytes(response.body)
        if len(body) > ALL_RESOURCE_LIMITS["maximum_response_body_bytes"]:
            body = json.dumps(
                {"ok": False, "error_code": "response_body_too_large"},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            status_code = 500
        else:
            status_code = response.status_code
        headers = response_headers(response.headers)
        headers["Content-Type"] = "application/json; charset=utf-8"
        headers["Content-Length"] = str(len(body))
        self.send_response(status_code)
        for name, value in headers.items():
            if name.startswith("Access-Control-") or name == "Set-Cookie":
                continue
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


def _headers_from_request(items: Sequence[tuple[str, str]]) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = {}
    canonical: dict[str, str] = {}
    for key, value in items:
        lowered = key.lower()
        header_name = canonical.setdefault(lowered, key)
        values.setdefault(header_name, []).append(value)
    return {key: tuple(nested) for key, nested in values.items()}


def _validate_numeric_loopback() -> None:
    address = ipaddress.ip_address(LOOPBACK_BIND_HOST)
    if address.version != 4 or not address.is_loopback:
        raise ValueError("numeric loopback binding required")
    if SECURITY_HEADERS.get("Cache-Control") != "no-store":
        raise ValueError("local bridge security headers are incomplete")

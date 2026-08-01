from __future__ import annotations

import json
import socket
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from aion_brain.contracts.operator_console_integration import (
    AUTHORIZED_ROUTE_PAIRS,
    CONFIRM_CAPABILITY,
    CONFIRM_CLOSE,
    CONFIRM_KILL,
    CONFIRM_MODEL_TEXT,
    CONTENT_SECURITY_POLICY,
    LOOPBACK_BIND_HOST,
    SECURITY_HEADERS,
    STATIC_ASSET_ROUTES,
    default_route_manifest,
)
from aion_brain.operator_console_runtime.local_http import ControlledLoopbackHttpServer
from aion_brain.operator_console_runtime.origin_policy import validate_loopback_bind_address

REPO_ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = REPO_ROOT / "operator-console-static"


def _assets() -> dict[str, bytes]:
    return {
        name: (STATIC_DIR / name).read_bytes()
        for name in ("index.html", "styles.css", "app.js", "live-console.js")
    }


class _Response:
    def __init__(self, status: int, headers: Mapping[str, str], body: bytes) -> None:
        self.status = status
        self.headers = dict(headers)
        self.body = body

    def json(self) -> dict[str, Any]:
        return json.loads(self.body.decode("utf-8")) if self.body else {}

    def header(self, name: str) -> str:
        return self.headers.get(name.lower(), "")


def _request(
    *,
    port: int,
    method: str,
    target: str,
    payload: Mapping[str, Any] | None = None,
    nonce: str | None = None,
    confirmation: str | None = None,
    host: str | None = None,
    origin: str | None = None,
    extra_headers: tuple[str, ...] = (),
) -> _Response:
    body = b"" if payload is None else json.dumps(payload, sort_keys=True).encode()
    lines = [
        f"{method} {target} HTTP/1.1",
        f"Host: {host or f'{LOOPBACK_BIND_HOST}:{port}'}",
        "Connection: close",
    ]
    if method == "POST":
        lines.extend(
            [
                "Content-Type: application/json",
                f"Content-Length: {len(body)}",
                f"Origin: {origin or f'http://{LOOPBACK_BIND_HOST}:{port}'}",
                f"X-AION-Operator-Confirmation: {confirmation or ''}",
                f"X-AION-Mutation-Nonce: {nonce or ''}",
            ]
        )
    lines.extend(extra_headers)
    request_bytes = ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((LOOPBACK_BIND_HOST, port))
        sock.sendall(request_bytes)
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    raw = b"".join(chunks)
    header_bytes, _, response_body = raw.partition(b"\r\n\r\n")
    header_lines = header_bytes.decode("iso-8859-1").split("\r\n")
    headers: dict[str, str] = {}
    for line in header_lines[1:]:
        name, _, value = line.partition(":")
        headers[name.lower()] = value.strip()
    return _Response(int(header_lines[0].split()[1]), headers, response_body)


@pytest.fixture()
def server() -> ControlledLoopbackHttpServer:
    bridge = ControlledLoopbackHttpServer(assets=_assets(), port=0)
    bridge.start()
    try:
        yield bridge
    finally:
        bridge.shutdown()


def test_route_manifest_static_asset_manifest_and_security_headers(
    server: ControlledLoopbackHttpServer,
) -> None:
    manifest = default_route_manifest()
    assert {item.path: item.method for item in manifest.routes} == AUTHORIZED_ROUTE_PAIRS
    assert len(manifest.routes) == 10
    observed_assets = {
        asset.route_path: asset.asset_name for asset in server.static_asset_manifest.assets
    }
    assert observed_assets == STATIC_ASSET_ROUTES
    assert len(server.static_asset_manifest.assets) == 5

    response = _request(port=server.bound_port, method="GET", target="/live-console.js")

    assert response.status == 200
    assert response.header("content-security-policy") == CONTENT_SECURITY_POLICY
    assert response.header("cache-control") == "no-store"
    assert response.header("connection") == "close"
    assert "access-control-allow-origin" not in response.headers
    assert "set-cookie" not in response.headers


def test_loopback_bind_policy_and_rejected_static_targets(
    server: ControlledLoopbackHttpServer,
) -> None:
    validate_loopback_bind_address("127.0.0.1")
    for host in ("0.0.0.0", "::", "::1", "localhost", "192.168.1.10", ""):
        with pytest.raises(ValueError):
            validate_loopback_bind_address(host)

    traversal = _request(port=server.bound_port, method="GET", target="/../index.html")
    demo_data = _request(port=server.bound_port, method="GET", target="/demo-data/x.json")
    head = _request(port=server.bound_port, method="HEAD", target="/")

    assert traversal.status in {400, 404}
    assert demo_data.status == 404
    assert head.status == 405


def test_origin_host_and_request_parser_rejections(
    server: ControlledLoopbackHttpServer,
) -> None:
    bootstrap = _request(port=server.bound_port, method="GET", target="/aion/local/v1/bootstrap")
    nonce = bootstrap.header("x-aion-mutation-nonce")
    payload = {"request_id": "model-reject", "mode": "text", "transient_prompt": "local"}

    wrong_origin = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/model/simulate",
        payload=payload,
        nonce=nonce,
        confirmation=CONFIRM_MODEL_TEXT,
        origin="http://127.0.0.1:1",
    )
    wrong_host = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/model/simulate",
        payload=payload,
        nonce=nonce,
        confirmation=CONFIRM_MODEL_TEXT,
        host="127.0.0.1:1",
    )
    transfer_encoded = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/model/simulate",
        payload=payload,
        nonce=nonce,
        confirmation=CONFIRM_MODEL_TEXT,
        extra_headers=("Transfer-Encoding: chunked",),
    )
    query_action = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/model/simulate?x=1",
        payload=payload,
        nonce=nonce,
        confirmation=CONFIRM_MODEL_TEXT,
    )
    absolute_target = _request(
        port=server.bound_port,
        method="POST",
        target=f"http://127.0.0.1:{server.bound_port}/aion/local/v1/model/simulate",
        payload=payload,
        nonce=nonce,
        confirmation=CONFIRM_MODEL_TEXT,
    )

    assert wrong_origin.status == 403
    assert wrong_host.status == 403
    assert transfer_encoded.status == 400
    assert query_action.status == 400
    assert absolute_target.status == 400


def test_nonce_rotation_stale_nonce_kill_and_close_lifecycle(
    server: ControlledLoopbackHttpServer,
) -> None:
    bootstrap = _request(port=server.bound_port, method="GET", target="/aion/local/v1/bootstrap")
    nonce = bootstrap.header("x-aion-mutation-nonce")
    assert nonce

    model = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/model/simulate",
        payload={"request_id": "model-text", "mode": "text", "transient_prompt": "local state"},
        nonce=nonce,
        confirmation=CONFIRM_MODEL_TEXT,
    )
    replacement = model.header("x-aion-mutation-nonce")
    stale = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/model/simulate",
        payload={"request_id": "model-stale", "mode": "text", "transient_prompt": "local"},
        nonce=nonce,
        confirmation=CONFIRM_MODEL_TEXT,
    )
    capability = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/capability/execute",
        payload={
            "request_id": "capability-normalize",
            "capability_id": "capability.text.normalize",
            "transient_input": {"text": "AION Runtime"},
            "input_schema_id": "capability.text.normalize:input",
            "output_schema_id": "capability.text.normalize:output",
        },
        nonce=replacement,
        confirmation=CONFIRM_CAPABILITY,
    )

    assert model.status == 200
    assert replacement and replacement != nonce
    assert stale.status == 409
    assert capability.status == 200

    close_nonce = capability.header("x-aion-mutation-nonce")
    close = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/session/close",
        payload={"request_id": "session-close"},
        nonce=close_nonce,
        confirmation=CONFIRM_CLOSE,
    )
    second = _request(port=server.bound_port, method="GET", target="/aion/local/v1/bootstrap")
    kill_nonce = second.header("x-aion-mutation-nonce")
    killed = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/kill",
        payload={"request_id": "kill-control"},
        nonce=kill_nonce,
        confirmation=CONFIRM_KILL,
    )
    blocked = _request(
        port=server.bound_port,
        method="POST",
        target="/aion/local/v1/capability/execute",
        payload={
            "request_id": "post-kill-capability",
            "capability_id": "capability.text.normalize",
            "transient_input": {"text": "blocked"},
            "input_schema_id": "capability.text.normalize:input",
            "output_schema_id": "capability.text.normalize:output",
        },
        nonce=kill_nonce,
        confirmation=CONFIRM_CAPABILITY,
    )

    assert close.status == 200
    assert second.status == 200
    assert killed.status == 200
    assert killed.header("x-aion-mutation-nonce") == ""
    assert blocked.status == 410


def test_security_header_contract_matches_runtime_constants() -> None:
    assert SECURITY_HEADERS["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert SECURITY_HEADERS["Connection"] == "close"
    assert "unsafe-inline" not in CONTENT_SECURITY_POLICY
    assert "unsafe-eval" not in CONTENT_SECURITY_POLICY

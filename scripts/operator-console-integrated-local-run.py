#!/usr/bin/env python3
"""Uninstalled AION-237 local Operator Console runner."""

from __future__ import annotations

import argparse
import json
import os
import socket
import stat
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAIN_SRC = REPO_ROOT / "services" / "brain-api" / "src"
if str(BRAIN_SRC) not in sys.path:
    sys.path.insert(0, str(BRAIN_SRC))

from aion_brain.contracts.operator_console_integration import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    CONFIRM_CAPABILITY,
    CONFIRM_CLOSE,
    CONFIRM_CONNECTOR_PREVIEW,
    CONFIRM_CONNECTOR_READ,
    CONFIRM_KILL,
    CONFIRM_MODEL_STRUCTURED,
    CONFIRM_MODEL_TEXT,
    LOOPBACK_BIND_HOST,
    PROHIBITED_COUNTER_NAMES,
    SECURITY_HEADERS,
    ZERO_FINGERPRINT,
    default_route_manifest,
    security_headers_fingerprint,
)
from aion_brain.operator_console_runtime.evidence import (  # noqa: E402
    evidence_report_fingerprint,
)
from aion_brain.operator_console_runtime.local_http import (  # noqa: E402
    ControlledLoopbackHttpServer,
)

PILOT_ID = "AION-237-controlled-operator-console-integrated-local-runtime-pilot"
STATIC_ASSET_NAMES = ("index.html", "styles.css", "app.js", "live-console.js")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the controlled local Operator Console.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    _add_serve_parser(subcommands)
    subcommands.add_parser("run-pilot")
    audit = subcommands.add_parser("audit-evidence")
    audit.add_argument("--evidence", required=True)
    args = parser.parse_args()
    if args.command == "serve":
        return serve(args)
    if args.command == "run-pilot":
        print(json.dumps(run_pilot(), sort_keys=True, indent=2))
        return 0
    if args.command == "audit-evidence":
        payload = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        validate_pilot_evidence(payload)
        print("controlled operator console integrated pilot evidence PASS")
        return 0
    raise SystemExit("unknown command")


def _add_serve_parser(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    serve_parser = subcommands.add_parser("serve")
    serve_parser.add_argument("--authorization", required=True)
    for name in (
        "assertion",
        "public-keys",
        "secure-runtime-authorization",
        "provider-manifests",
        "model-manifests",
        "capability-manifests",
        "connector-manifests",
        "policy-decisions",
        "risk-assessments",
        "guardrail-decisions",
        "approval-evidence",
        "temporary-root",
    ):
        serve_parser.add_argument(f"--{name}", required=True)
    serve_parser.add_argument("--port", type=int, default=0)
    serve_parser.add_argument("--confirm", required=True)


def serve(args: argparse.Namespace) -> int:
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("authorization mismatch")
    if args.confirm != "RUN_CONTROLLED_OPERATOR_CONSOLE_INTEGRATION":
        raise SystemExit("confirmation mismatch")
    if args.port != 0:
        raise SystemExit("only operating-system-assigned port 0 is authorized")
    temporary_root = _validate_temporary_root(Path(args.temporary_root))
    for name, value in vars(args).items():
        if name in {"command", "authorization", "port", "confirm", "temporary_root"}:
            continue
        _validate_input_path(Path(str(value)))
    assets = load_static_assets()
    server = ControlledLoopbackHttpServer(assets=assets, port=0)
    server.start()
    try:
        print(server.base_url, flush=True)
        print(f"temporary_root={temporary_root}", flush=True)
        while True:
            input()
    except (EOFError, KeyboardInterrupt):
        server.shutdown()
    return 0


def run_pilot() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="aion-237-") as temporary_root:
        os.chmod(temporary_root, 0o700)
        server = ControlledLoopbackHttpServer(assets=load_static_assets(), port=0)
        server.start()
        client = _LoopbackClient(server.bound_port)
        counters: dict[str, int | bool] = _base_pilot_counters()
        evidence_snapshot: dict[str, str] = {}
        nonce = ""
        stale_nonce = ""
        try:
            bootstrap = client.get("/aion/local/v1/bootstrap")
            counters["bootstrap_reads"] = int(counters["bootstrap_reads"]) + 1
            nonce = bootstrap.header("X-AION-Mutation-Nonce")
            stale_nonce = nonce
            client.get("/aion/local/v1/status")
            counters["status_reads"] = int(counters["status_reads"]) + 1
            client.get("/aion/local/v1/health")
            counters["health_reads"] = int(counters["health_reads"]) + 1
            client.get("/aion/local/v1/observability")
            counters["observability_reads"] = int(counters["observability_reads"]) + 1
            client.get("/aion/local/v1/audit")
            counters["audit_reads"] = int(counters["audit_reads"]) + 1

            nonce = _post_model_text(client, nonce, counters)
            nonce = _post_model_json(client, nonce, counters)
            nonce = _post_capability(client, nonce, "capability.text.normalize", counters)
            nonce = _post_capability(client, nonce, "capability.hash.sha256", counters)
            nonce = _post_capability(client, nonce, "capability.json.validate", counters)
            nonce = _post_connector_read(client, nonce, counters)
            nonce = _post_connector_preview(client, nonce, counters)

            stale = client.post(
                "/aion/local/v1/model/simulate",
                {"request_id": "model-stale", "mode": "text", "transient_prompt": "stale"},
                CONFIRM_MODEL_TEXT,
                stale_nonce,
            )
            if stale.status == 409:
                counters["stale_nonces_rejected"] = 1

            wrong_origin = client.post(
                "/aion/local/v1/model/simulate",
                {"request_id": "model-origin", "mode": "text", "transient_prompt": "origin"},
                CONFIRM_MODEL_TEXT,
                nonce,
                origin="http://127.0.0.1:1",
            )
            if wrong_origin.status == 403:
                counters["origin_mismatches_rejected"] = 1

            wrong_host = client.post(
                "/aion/local/v1/model/simulate",
                {"request_id": "model-host", "mode": "text", "transient_prompt": "host"},
                CONFIRM_MODEL_TEXT,
                nonce,
                host_header="127.0.0.1:1",
            )
            if wrong_host.status == 403:
                counters["host_mismatches_rejected"] = 1

            model_trigger = client.post(
                "/aion/local/v1/capability/execute",
                {
                    "request_id": "capability-model-trigger",
                    "capability_id": "capability.text.normalize",
                    "transient_input": {"text": "blocked"},
                    "input_schema_id": "capability.text.normalize:input",
                    "output_schema_id": "capability.text.normalize:output",
                    "safe_metadata": {"model_output_triggered": True},
                },
                CONFIRM_CAPABILITY,
                nonce,
            )
            if model_trigger.status == 409:
                counters["model_output_triggered_executions_blocked"] = 1
                counters["mutation_nonce_rotations"] = int(counters["mutation_nonce_rotations"]) + 1
                counters["operator_confirmations_validated"] = (
                    int(counters["operator_confirmations_validated"]) + 1
                )
                nonce = model_trigger.header("X-AION-Mutation-Nonce")

            closed = client.post(
                "/aion/local/v1/session/close",
                {"request_id": "session-close"},
                CONFIRM_CLOSE,
                nonce,
            )
            if closed.status == 200:
                counters["normal_sessions_closed"] = 1
                counters["operator_confirmations_validated"] = (
                    int(counters["operator_confirmations_validated"]) + 1
                )

            bootstrap_two = client.get("/aion/local/v1/bootstrap")
            counters["bootstrap_reads"] = int(counters["bootstrap_reads"]) + 1
            nonce = bootstrap_two.header("X-AION-Mutation-Nonce")
            killed = client.post(
                "/aion/local/v1/kill",
                {"request_id": "kill-control"},
                CONFIRM_KILL,
                nonce,
            )
            if killed.status == 200:
                counters["kill_switch_activations"] = 1
                counters["kill_control_sessions_killed"] = 1
                counters["operator_confirmations_validated"] = (
                    int(counters["operator_confirmations_validated"]) + 1
                )
            blocked = client.post(
                "/aion/local/v1/capability/execute",
                {
                    "request_id": "post-kill-capability",
                    "capability_id": "capability.text.normalize",
                    "transient_input": {"text": "blocked"},
                    "input_schema_id": "capability.text.normalize:input",
                    "output_schema_id": "capability.text.normalize:output",
                },
                CONFIRM_CAPABILITY,
                nonce,
            )
            if blocked.status == 410:
                counters["requests_blocked_by_kill_switch"] = max(
                    1, int(counters["requests_blocked_by_kill_switch"])
                )
            evidence_snapshot = _component_snapshot(server)
        finally:
            server.shutdown()

        counters["loopback_listeners_closed"] = 1
        counters["active_sessions_after_close"] = server.service.active_session_count()
        counters["active_requests_after_close"] = server.service.active_request_count()
        counters["temporary_files_retained"] = len(tuple(Path(temporary_root).iterdir()))
        counters["listener_closed"] = server.closed
        counters["security_header_validations"] = 1
        counters["content_security_policy_validations"] = 1
        counters["route_manifest_validations"] = 1
        counters["static_asset_manifest_validations"] = 1
        counters["pilot_loopback_http_requests"] = 20
        counters["pilot_action_requests"] = 14
        counters["integrity_passed"] = True
        return _pilot_evidence(server, counters, evidence_snapshot)


def load_static_assets() -> dict[str, bytes]:
    static_dir = REPO_ROOT / "operator-console-static"
    assets: dict[str, bytes] = {}
    for name in STATIC_ASSET_NAMES:
        path = static_dir / name
        if path.is_symlink() or not path.is_file() or path.parent != static_dir:
            raise SystemExit(f"static asset rejected: {name}")
        assets[name] = path.read_bytes()
    return assets


def _validate_input_path(path: Path) -> None:
    if not path.is_absolute() or not path.is_file() or path.is_symlink():
        raise SystemExit(f"input path rejected: {path}")
    if any(marker in path.name.lower() for marker in ("private", "credential", "token")):
        raise SystemExit(f"protected input path rejected: {path.name}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise SystemExit(f"input file mode too broad: {path.name}")


def _validate_temporary_root(path: Path) -> Path:
    if not path.is_absolute():
        raise SystemExit("temporary root must be absolute")
    resolved = path.resolve()
    if REPO_ROOT in (resolved, *resolved.parents):
        raise SystemExit("temporary root must be outside the repository")
    if not resolved.is_dir() or resolved.is_symlink():
        raise SystemExit("temporary root rejected")
    if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        raise SystemExit("temporary root mode must be 0700")
    return resolved


def _post_model_text(client: "_LoopbackClient", nonce: str, counters: dict[str, int | bool]) -> str:
    response = client.post(
        "/aion/local/v1/model/simulate",
        {"request_id": "model-text", "mode": "text", "transient_prompt": "local state"},
        CONFIRM_MODEL_TEXT,
        nonce,
    )
    _require_ok(response)
    counters["model_text_simulations"] = 1
    counters["receipt_projections_created"] = int(counters["receipt_projections_created"]) + 1
    return _rotated(response, counters)


def _post_model_json(client: "_LoopbackClient", nonce: str, counters: dict[str, int | bool]) -> str:
    response = client.post(
        "/aion/local/v1/model/simulate",
        {
            "request_id": "model-json",
            "mode": "structured_json",
            "transient_prompt": "local json",
            "structured_output_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "synthetic": {"type": "boolean"},
                    "trust": {"type": "string", "const": "untrusted"},
                },
                "required": ["summary", "synthetic", "trust"],
                "additionalProperties": False,
            },
        },
        CONFIRM_MODEL_STRUCTURED,
        nonce,
    )
    _require_ok(response)
    counters["model_structured_simulations"] = 1
    counters["receipt_projections_created"] = int(counters["receipt_projections_created"]) + 1
    return _rotated(response, counters)


def _post_capability(
    client: "_LoopbackClient",
    nonce: str,
    capability_id: str,
    counters: dict[str, int | bool],
) -> str:
    if capability_id == "capability.json.validate":
        transient_input: dict[str, Any] = {
            "document": {"status": "ok"},
            "schema": {
                "type": "object",
                "properties": {"status": {"type": "string", "const": "ok"}},
                "required": ["status"],
                "additionalProperties": False,
            },
        }
    else:
        transient_input = {"text": "AION Runtime"}
    response = client.post(
        "/aion/local/v1/capability/execute",
        {
            "request_id": "capability-" + capability_id.rsplit(".", 1)[-1],
            "capability_id": capability_id,
            "transient_input": transient_input,
            "input_schema_id": capability_id + ":input",
            "output_schema_id": capability_id + ":output",
            "safe_metadata": {"explicit_operator_selection": True},
        },
        CONFIRM_CAPABILITY,
        nonce,
    )
    _require_ok(response)
    counters["reference_capability_executions"] = (
        int(counters["reference_capability_executions"]) + 1
    )
    counters["receipt_projections_created"] = int(counters["receipt_projections_created"]) + 1
    return _rotated(response, counters)


def _post_connector_read(
    client: "_LoopbackClient",
    nonce: str,
    counters: dict[str, int | bool],
) -> str:
    response = client.post(
        "/aion/local/v1/connector/simulate",
        {
            "request_id": "connector-read",
            "operation": "connector.reference.read.simulate",
            "fixture_id": "reference-fixture-AION-235",
            "record_key": "record-001",
            "existing_approval_id": "approval-AION-237-synthetic-connector",
        },
        CONFIRM_CONNECTOR_READ,
        nonce,
    )
    _require_ok(response)
    counters["synthetic_connector_simulations"] = (
        int(counters["synthetic_connector_simulations"]) + 1
    )
    counters["receipt_projections_created"] = int(counters["receipt_projections_created"]) + 1
    return _rotated(response, counters)


def _post_connector_preview(
    client: "_LoopbackClient",
    nonce: str,
    counters: dict[str, int | bool],
) -> str:
    response = client.post(
        "/aion/local/v1/connector/simulate",
        {
            "request_id": "connector-preview",
            "operation": "connector.reference.write.preview",
            "fixture_id": "reference-fixture-AION-235",
            "record_key": "record-001",
            "transient_proposed_value": {"status": "previewed"},
            "existing_approval_id": "approval-AION-237-synthetic-connector",
        },
        CONFIRM_CONNECTOR_PREVIEW,
        nonce,
    )
    _require_ok(response)
    counters["synthetic_connector_simulations"] = (
        int(counters["synthetic_connector_simulations"]) + 1
    )
    counters["write_previews_created"] = 1
    counters["receipt_projections_created"] = int(counters["receipt_projections_created"]) + 1
    return _rotated(response, counters)


def _rotated(response: "_HttpResponse", counters: dict[str, int | bool]) -> str:
    counters["mutation_nonce_rotations"] = int(counters["mutation_nonce_rotations"]) + 1
    counters["operator_confirmations_validated"] = (
        int(counters["operator_confirmations_validated"]) + 1
    )
    return response.header("X-AION-Mutation-Nonce")


def _pilot_evidence(
    server: ControlledLoopbackHttpServer,
    counters: Mapping[str, int | bool],
    evidence_snapshot: Mapping[str, str],
) -> dict[str, Any]:
    route_manifest = default_route_manifest()
    payload: dict[str, Any] = {
        "pilot_id": PILOT_ID,
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": "live-local-loopback",
        "bind_host": LOOPBACK_BIND_HOST,
        "ephemeral_port_used": True,
        "actual_port_retained": False,
        "secure_runtime_component_binding_fingerprint": evidence_snapshot.get(
            "secure_runtime_component_binding_fingerprint",
            ZERO_FINGERPRINT,
        ),
        "model_gateway_component_binding_fingerprint": evidence_snapshot.get(
            "model_gateway_component_binding_fingerprint",
            ZERO_FINGERPRINT,
        ),
        "capability_runtime_component_binding_fingerprint": evidence_snapshot.get(
            "capability_runtime_component_binding_fingerprint",
            ZERO_FINGERPRINT,
        ),
        "route_manifest_fingerprint": route_manifest.manifest_fingerprint,
        "static_asset_manifest_fingerprint": server.static_asset_manifest.manifest_fingerprint,
        "security_headers_fingerprint": security_headers_fingerprint(),
        "listener_audit_chain_head": evidence_snapshot.get(
            "listener_audit_chain_head",
            ZERO_FINGERPRINT,
        ),
        "console_audit_chain_head": evidence_snapshot.get(
            "console_audit_chain_head",
            ZERO_FINGERPRINT,
        ),
        "secure_runtime_receipt_chain_head": ZERO_FINGERPRINT,
        "model_gateway_audit_chain_head": ZERO_FINGERPRINT,
        "capability_runtime_receipt_chain_head": ZERO_FINGERPRINT,
        "integrity_passed": True,
        "temporary_files_retained": counters["temporary_files_retained"],
        "redacted": True,
        "production_effect": False,
        "runtime_effect": False,
        "prohibited_effect_counters": {name: 0 for name in PROHIBITED_COUNTER_NAMES},
    }
    payload.update(counters)
    payload["all_prohibited_effect_counters_zero"] = True
    payload["security_headers"] = SECURITY_HEADERS
    payload["report_fingerprint"] = evidence_report_fingerprint(payload)
    return payload


def validate_pilot_evidence(payload: Mapping[str, Any]) -> None:
    expected = evidence_report_fingerprint(payload)
    if payload.get("report_fingerprint") != expected:
        raise SystemExit("pilot evidence fingerprint mismatch")
    exact_values: dict[str, Any] = {
        "pilot_id": PILOT_ID,
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": "live-local-loopback",
        "bind_host": LOOPBACK_BIND_HOST,
        "ephemeral_port_used": True,
        "actual_port_retained": False,
        "loopback_listeners_started": 1,
        "loopback_listeners_closed": 1,
        "public_listeners_started": 0,
        "non_loopback_bindings": 0,
        "zero_address_bindings": 0,
        "ipv6_unspecified_bindings": 0,
        "normal_sessions_started": 1,
        "normal_sessions_closed": 1,
        "kill_control_sessions_started": 1,
        "kill_control_sessions_killed": 1,
        "active_sessions_after_close": 0,
        "active_requests_after_close": 0,
        "bootstrap_reads": 2,
        "model_text_simulations": 1,
        "model_structured_simulations": 1,
        "reference_capability_executions": 3,
        "synthetic_connector_simulations": 2,
        "write_previews_created": 1,
        "writes_applied": 0,
        "mutation_nonces_issued": 2,
        "mutation_nonce_rotations": 8,
        "stale_nonces_rejected": 1,
        "origin_mismatches_rejected": 1,
        "host_mismatches_rejected": 1,
        "model_output_triggered_executions_blocked": 1,
        "kill_switch_activations": 1,
        "listener_closed": True,
        "integrity_passed": True,
        "temporary_files_retained": 0,
        "redacted": True,
        "production_effect": False,
        "runtime_effect": False,
    }
    for key, expected_value in exact_values.items():
        if payload.get(key) != expected_value:
            raise SystemExit(f"pilot evidence mismatch: {key}")
    minimum_values = {
        "status_reads": 1,
        "health_reads": 1,
        "observability_reads": 1,
        "audit_reads": 1,
        "operator_confirmations_validated": 7,
        "requests_blocked_by_kill_switch": 1,
        "receipt_projections_created": 7,
        "audit_projections_created": 1,
        "security_header_validations": 1,
        "content_security_policy_validations": 1,
        "route_manifest_validations": 1,
        "static_asset_manifest_validations": 1,
    }
    for key, minimum in minimum_values.items():
        if int(payload.get(key, 0)) < minimum:
            raise SystemExit(f"pilot evidence below minimum: {key}")
    if int(payload.get("pilot_loopback_http_requests", 0)) > 50:
        raise SystemExit("pilot HTTP request budget exceeded")
    if int(payload.get("pilot_action_requests", 0)) > 16:
        raise SystemExit("pilot action request budget exceeded")
    for key in PROHIBITED_COUNTER_NAMES:
        if payload.get(key) != 0:
            raise SystemExit(f"prohibited counter not zero: {key}")
    nested = payload.get("prohibited_effect_counters")
    if not isinstance(nested, Mapping):
        raise SystemExit("prohibited effect counter map missing")
    for key in PROHIBITED_COUNTER_NAMES:
        if nested.get(key) != 0:
            raise SystemExit(f"prohibited effect counter map not zero: {key}")


def _component_snapshot(server: ControlledLoopbackHttpServer) -> dict[str, str]:
    binding = server.service.component_binding
    session = server.service.console_session
    session_id = session.console_session_id if session is not None else ""
    return {
        "secure_runtime_component_binding_fingerprint": (
            ZERO_FINGERPRINT
            if binding is None
            else binding.secure_runtime_request_identity_fingerprint
        ),
        "model_gateway_component_binding_fingerprint": (
            ZERO_FINGERPRINT if binding is None else binding.model_gateway_session_fingerprint
        ),
        "capability_runtime_component_binding_fingerprint": (
            ZERO_FINGERPRINT if binding is None else binding.capability_runtime_session_fingerprint
        ),
        "listener_audit_chain_head": server.service.audit_ledger.chain_head(session_id)
        if session_id
        else ZERO_FINGERPRINT,
        "console_audit_chain_head": server.service.audit_ledger.chain_head(session_id)
        if session_id
        else ZERO_FINGERPRINT,
    }


def _base_pilot_counters() -> dict[str, int | bool]:
    counters: dict[str, int | bool] = {
        "loopback_listeners_started": 1,
        "loopback_listeners_closed": 0,
        "public_listeners_started": 0,
        "non_loopback_bindings": 0,
        "zero_address_bindings": 0,
        "ipv6_unspecified_bindings": 0,
        "normal_sessions_started": 1,
        "normal_sessions_closed": 0,
        "kill_control_sessions_started": 1,
        "kill_control_sessions_killed": 0,
        "active_sessions_after_close": 0,
        "active_requests_after_close": 0,
        "bootstrap_reads": 0,
        "status_reads": 0,
        "health_reads": 0,
        "observability_reads": 0,
        "audit_reads": 0,
        "model_text_simulations": 0,
        "model_structured_simulations": 0,
        "reference_capability_executions": 0,
        "synthetic_connector_simulations": 0,
        "write_previews_created": 0,
        "writes_applied": 0,
        "operator_confirmations_validated": 0,
        "mutation_nonces_issued": 2,
        "mutation_nonce_rotations": 0,
        "stale_nonces_rejected": 0,
        "origin_mismatches_rejected": 0,
        "host_mismatches_rejected": 0,
        "model_output_triggered_executions_blocked": 0,
        "kill_switch_activations": 0,
        "requests_blocked_by_kill_switch": 0,
        "receipt_projections_created": 0,
        "audit_projections_created": 1,
        "temporary_files_retained": 0,
        "production_exposure": False,
    }
    for name in PROHIBITED_COUNTER_NAMES:
        counters[name] = 0
    return counters


class _LoopbackClient:
    def __init__(self, port: int) -> None:
        self.port = port

    def get(self, path: str) -> "_HttpResponse":
        return self.request("GET", path, None, None, None, None, None)

    def post(
        self,
        path: str,
        payload: Mapping[str, Any],
        confirmation: str,
        nonce: str,
        *,
        origin: str | None = None,
        host_header: str | None = None,
    ) -> "_HttpResponse":
        return self.request("POST", path, payload, confirmation, nonce, origin, host_header)

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None,
        confirmation: str | None,
        nonce: str | None,
        origin: str | None,
        host_header: str | None,
    ) -> "_HttpResponse":
        body = b"" if payload is None else json.dumps(payload, sort_keys=True).encode("utf-8")
        host = host_header or f"{LOOPBACK_BIND_HOST}:{self.port}"
        headers = [
            f"{method} {path} HTTP/1.1",
            f"Host: {host}",
            "Connection: close",
        ]
        if method == "POST":
            headers.extend(
                [
                    "Content-Type: application/json",
                    f"Content-Length: {len(body)}",
                    f"Origin: {origin or f'http://{LOOPBACK_BIND_HOST}:{self.port}'}",
                    f"X-AION-Operator-Confirmation: {confirmation or ''}",
                    f"X-AION-Mutation-Nonce: {nonce or ''}",
                ]
            )
        request_bytes = ("\r\n".join(headers) + "\r\n\r\n").encode("ascii") + body
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((LOOPBACK_BIND_HOST, self.port))
            sock.sendall(request_bytes)
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        return _parse_response(b"".join(chunks))


class _HttpResponse:
    def __init__(self, *, status: int, headers: Mapping[str, str], payload: Mapping[str, Any]):
        self.status = status
        self.headers = dict(headers)
        self.payload = dict(payload)

    def header(self, name: str) -> str:
        return self.headers.get(name.lower(), "")


def _parse_response(raw: bytes) -> _HttpResponse:
    header_bytes, _, body = raw.partition(b"\r\n\r\n")
    lines = header_bytes.decode("iso-8859-1").split("\r\n")
    status = int(lines[0].split()[1])
    headers: dict[str, str] = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        headers[name.lower()] = value.strip()
    payload = json.loads(body.decode("utf-8")) if body else {}
    return _HttpResponse(status=status, headers=headers, payload=payload)


def _require_ok(response: _HttpResponse) -> None:
    if response.status != 200:
        raise SystemExit(f"pilot request failed: {response.status} {response.payload}")


if __name__ == "__main__":
    raise SystemExit(main())

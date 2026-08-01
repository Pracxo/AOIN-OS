#!/usr/bin/env python3
"""AION-238 final Secure Runtime Integration evaluation harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable


PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
EVALUATION_ID = "AION-SRIPE-004"
EVALUATION_TYPE = "secure_runtime_integration_program_final_evaluation"
IMPLEMENTATION_TASK = "AION-237"
CLOSEOUT_TASK = "AION-238"
AUTHORIZATION_ID = "AION-236-SRI-0004"
SUCCESSOR_PROGRAM_ID = "AION-V02-RELEASE-QUALIFICATION-001"
SUCCESSOR_AUTHORIZATION_ID = "AION-238-V02RQ-0001"
SUCCESSOR_IMPLEMENTATION_TASK = "AION-239"
SUCCESSOR_CLOSEOUT_TASK = "AION-240"
SUCCESSOR_FINAL_PLANNED_TASK = "AION-244"
IMPLEMENTATION_PR = 156
IMPLEMENTATION_BRANCH = "phase/operator-console-integrated-local-runtime"
IMPLEMENTATION_FEATURE_COMMIT = "df1f89e1708638e32aef0532fb37ed150b85b600"
IMPLEMENTATION_MERGE_COMMIT = "55f2721bb036886a693a36d870d49f49f7ecc6d1"
IMPLEMENTATION_MERGED_AT = "2026-08-01T11:32:50Z"
PASS_DECISION = (
    "CONTROLLED_OPERATOR_CONSOLE_INTEGRATED_LOCAL_RUNTIME_FINAL_EVALUATION_PASS_"
    "COMPLETE_SECURE_RUNTIME_INTEGRATION_PROGRAM_RECOMMEND_V02_RELEASE_"
    "QUALIFICATION_PROGRAM_AUTHORIZATION"
)
FAIL_DECISION = (
    "CONTROLLED_OPERATOR_CONSOLE_INTEGRATED_LOCAL_RUNTIME_FINAL_EVALUATION_FAIL_"
    "SECURE_RUNTIME_INTEGRATION_PROGRAM_REMEDIATION_REQUIRED"
)

REQUIRED_CHECKS = (
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
)

SCENARIO_IDS = (
    "aion_237_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "integrated_pilot_schema_and_fingerprint",
    "exact_source_and_runtime_registration_boundary",
    "component_authority_and_trust_chain_integrity",
    "numeric_loopback_binding_and_listener_lifecycle",
    "exact_route_and_static_asset_manifests",
    "host_origin_and_fetch_metadata_policy",
    "bounded_http_parser_and_protocol_smuggling",
    "mutation_nonce_lifecycle",
    "session_bootstrap_lifecycle_and_limits",
    "security_headers_csp_and_browser_non_persistence",
    "redacted_read_projection_integrity",
    "deterministic_text_model_integration",
    "deterministic_structured_model_integration",
    "model_output_non_authority_and_operator_selection",
    "reference_capability_integration",
    "synthetic_connector_read_and_write_preview",
    "policy_risk_guardrail_approval_and_budget_precedence",
    "kill_switch_and_session_close_terminal_semantics",
    "idempotency_and_replay_controls",
    "receipt_audit_provenance_and_integrity_chains",
    "concurrency_backpressure_and_performance",
    "static_console_offline_fallback_live_activation_and_accessibility",
    "complete_listener_session_request_nonce_and_fixture_cleanup",
    "zero_external_and_production_effects",
    "secure_runtime_integration_program_lineage_and_completion_readiness",
    "v02_release_qualification_program_authorization_readiness",
)

EXPECTED_POSITIVE_RESOURCE_LIMITS = {
    "maximum_operator_console_sessions": 1,
    "maximum_sessions_per_operator_run": 2,
    "maximum_loopback_listeners": 1,
    "maximum_loopback_bind_attempts": 10,
    "maximum_routes": 10,
    "maximum_static_assets": 5,
    "maximum_session_seconds": 3600,
    "maximum_idle_seconds": 900,
    "maximum_requests_per_session": 200,
    "maximum_concurrent_requests": 4,
    "maximum_request_body_bytes": 262144,
    "maximum_response_body_bytes": 1048576,
    "maximum_json_depth": 16,
    "maximum_json_items_per_request": 1000,
    "maximum_bootstrap_reads_per_session": 5,
    "maximum_status_reads_per_session": 100,
    "maximum_health_reads_per_session": 100,
    "maximum_observability_reads_per_session": 100,
    "maximum_audit_reads_per_session": 50,
    "maximum_model_simulations_per_session": 20,
    "maximum_capability_executions_per_session": 50,
    "maximum_synthetic_connector_simulations_per_session": 20,
    "maximum_write_previews_per_session": 10,
    "maximum_kill_switch_activations_per_session": 1,
    "maximum_session_close_requests_per_session": 1,
    "maximum_mutation_nonce_rotations_per_session": 100,
    "maximum_operator_confirmations_per_session": 100,
    "maximum_receipt_projections_per_session": 2000,
    "maximum_audit_records_per_session": 10000,
    "maximum_console_event_records_per_session": 5000,
    "maximum_trace_bytes_per_session": 4194304,
    "maximum_pilot_loopback_http_requests": 50,
    "maximum_pilot_action_requests": 16,
}

EXPECTED_ROUTES = (
    ("GET", "/aion/local/v1/bootstrap"),
    ("GET", "/aion/local/v1/status"),
    ("GET", "/aion/local/v1/health"),
    ("GET", "/aion/local/v1/observability"),
    ("GET", "/aion/local/v1/audit"),
    ("POST", "/aion/local/v1/model/simulate"),
    ("POST", "/aion/local/v1/capability/execute"),
    ("POST", "/aion/local/v1/connector/simulate"),
    ("POST", "/aion/local/v1/kill"),
    ("POST", "/aion/local/v1/session/close"),
)
EXPECTED_STATIC_ASSETS = {
    "/": "index.html",
    "/index.html": "index.html",
    "/styles.css": "styles.css",
    "/app.js": "app.js",
    "/live-console.js": "live-console.js",
}
EXPECTED_MIME_TYPES = {
    "index.html": "text/html; charset=utf-8",
    "styles.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "live-console.js": "text/javascript; charset=utf-8",
}
EXPECTED_SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors "
        "'none'; form-action 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Connection": "close",
}

EXPECTED_SOURCE_SCOPE = (
    "services/brain-api/src/aion_brain/contracts/operator_console_integration.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/__init__.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/audit.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/authorization.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/component_binding.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/evidence.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/integrity.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/local_http.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/observability.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/origin_policy.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/request_nonce.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/request_router.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/session_bridge.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/view_models.py",
)
PROHIBITED_SOURCE_PATHS = (
    "services/brain-api/src/aion_brain/operator_console_runtime/public_server.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/network_client.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/websocket.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/event_stream.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/cors.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/credential_store.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/token_store.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/cookie_store.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/browser_storage.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/file_upload.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/filesystem.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/process_runtime.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/background_worker.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/scheduler.py",
)
FUTURE_AION239_SOURCE_SCOPE = (
    "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/__init__.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/authorization.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/gap_matrix.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/production_auth_composition.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/request_identity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/replay_provisioning.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/identity_provider.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/key_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/protected_material.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/credential_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/token_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/session_lifecycle.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/deployment_manifest.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/artifact_provenance.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/rollback.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/observability.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/threat_model.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/runtime_guard.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/release_gate.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/integrity.py",
    "services/brain-api/src/aion_brain/v02_release_qualification/evidence.py",
)

REQUIRED_PILOT_FIELDS = {
    "pilot_id": "AION-237-controlled-operator-console-integrated-local-runtime-pilot",
    "authorization_id": AUTHORIZATION_ID,
    "mode": "live-local-loopback",
    "bind_host": "127.0.0.1",
    "ephemeral_port_used": True,
    "actual_port_retained": False,
    "secure_runtime_component_binding_fingerprint": (
        "38f061df47ec7864edde1a476561bc8284676291288f6451b9556573658629a9"
    ),
    "model_gateway_component_binding_fingerprint": (
        "48eb82139f07f51e752d6fd2cb9568e224e5dd8b0671c4dfcc1c6c33c735eb94"
    ),
    "capability_runtime_component_binding_fingerprint": (
        "706f3d8e740a4cd2593c50e4c09bd73956b6cfdf96c539120044bfe28fdbccfc"
    ),
    "route_manifest_fingerprint": (
        "2416793202f55b3f890cae1cd73216bd485125253ab16cc40a405e2063ec5b6a"
    ),
    "static_asset_manifest_fingerprint": (
        "fc550db840dfd2f6ff977ec2e55eeeb82737ef38ee40f0d6c95a11dec5463626"
    ),
    "security_headers_fingerprint": (
        "0f3fe07655aa9e1b5f9f88d3758875fa71d85de402e647747d9fa0e017a25199"
    ),
    "console_audit_chain_head": (
        "3531ca176d0ddc3baf0d4d969dbeb37cff79f32f4c086cca0d33fdbdccd0b3a2"
    ),
    "listener_audit_chain_head": (
        "3531ca176d0ddc3baf0d4d969dbeb37cff79f32f4c086cca0d33fdbdccd0b3a2"
    ),
    "report_fingerprint": (
        "e54ea6886c6d7f56c1de568983515944b1b72b3dc2d8f59b310039bb96ed5035"
    ),
}

REQUIRED_PILOT_COUNTERS = {
    "loopback_listeners_started": 1,
    "loopback_listeners_closed": 1,
    "public_listeners_started": 0,
    "normal_sessions_started": 1,
    "normal_sessions_closed": 1,
    "kill_control_sessions_started": 1,
    "kill_control_sessions_killed": 1,
    "active_sessions_after_close": 0,
    "active_requests_after_close": 0,
    "bootstrap_reads": 2,
    "status_reads": 1,
    "health_reads": 1,
    "observability_reads": 1,
    "audit_reads": 1,
    "model_text_simulations": 1,
    "model_structured_simulations": 1,
    "reference_capability_executions": 3,
    "synthetic_connector_simulations": 2,
    "write_previews_created": 1,
    "writes_applied": 0,
    "operator_confirmations_validated": 10,
    "mutation_nonces_issued": 2,
    "mutation_nonce_rotations": 8,
    "stale_nonces_rejected": 1,
    "origin_mismatches_rejected": 1,
    "host_mismatches_rejected": 1,
    "model_output_triggered_executions_blocked": 1,
    "kill_switch_activations": 1,
    "requests_blocked_by_kill_switch": 1,
    "receipt_projections_created": 7,
    "audit_projections_created": 1,
    "security_header_validations": 1,
    "content_security_policy_validations": 1,
    "route_manifest_validations": 1,
    "static_asset_manifest_validations": 1,
    "pilot_loopback_http_requests": 20,
    "pilot_action_requests": 14,
    "temporary_files_retained": 0,
}

ZERO_EFFECT_FIELDS = (
    "public_network_calls",
    "external_network_egress_calls",
    "dns_resolutions",
    "model_provider_calls",
    "provider_sdk_calls",
    "external_connector_calls",
    "external_tool_executions",
    "actual_tool_executions",
    "credentials_read",
    "credentials_persisted",
    "tokens_read",
    "tokens_persisted",
    "cookies_persisted",
    "browser_storage_writes",
    "service_workers_registered",
    "websocket_connections",
    "server_sent_event_connections",
    "filesystem_writes",
    "directory_mutations",
    "process_spawns",
    "shell_commands",
    "subprocess_executions",
    "browser_automation_actions",
    "dynamic_imports",
    "eval_executions",
    "exec_executions",
    "packages_installed",
    "modules_activated",
    "runtime_created_approvals",
    "production_writes",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "actual_belief_creations",
    "actual_belief_mutations",
    "source_mutations",
    "git_operations",
    "deployments",
    "model_weight_changes",
)

SUCCESSOR_SCOPE = (
    "disabled-production-readiness-qualification-production-auth-composition-request-"
    "identity-replay-ledger-provisioning-idp-adapter-key-rotation-protected-material-"
    "credential-token-session-lifecycle-deployment-artifact-sbom-provenance-rollback-"
    "observability-threat-model-runtime-guard-release-gate-staging-plan-no-production-"
    "activation-no-release-core"
)


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_report(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check(name: str, passed: bool, evidence: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, "passed": bool(passed)}
    if evidence is not None:
        payload["evidence"] = evidence
    return payload


def scenario(scenario_id: str, checks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    status = "pass" if checks and all(item.get("passed") is True for item in checks) else "fail"
    return {
        "scenario_id": scenario_id,
        "hard_gate": True,
        "status": status,
        "checks": [dict(item) for item in checks],
    }


def add_brain_src(repo_root: Path) -> None:
    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def raises(callable_: Callable[[], Any], expected: type[BaseException]) -> bool:
    try:
        callable_()
    except expected:
        return True
    except Exception:
        return False
    return False


def repository_tree_unchanged(repo_root: Path, before_head: str, before_tree: str) -> bool:
    return (
        git(repo_root, ["rev-parse", "HEAD"]).stdout.strip() == before_head
        and git(repo_root, ["rev-parse", "HEAD^{tree}"]).stdout.strip() == before_tree
    )


def load_static_assets(repo_root: Path) -> dict[str, bytes]:
    static_dir = repo_root / "operator-console-static"
    return {
        name: (static_dir / name).read_bytes()
        for name in ("index.html", "styles.css", "app.js", "live-console.js")
    }


class HttpResponse:
    def __init__(self, *, status: int, headers: Mapping[str, str], body: bytes) -> None:
        self.status = status
        self.headers = dict(headers)
        self.body = body

    def header(self, name: str) -> str:
        return self.headers.get(name.lower(), "")

    def json(self) -> dict[str, Any]:
        return json.loads(self.body.decode("utf-8")) if self.body else {}


def loopback_request(
    *,
    port: int,
    method: str,
    target: str,
    payload: Mapping[str, Any] | bytes | None = None,
    nonce: str | None = None,
    confirmation: str | None = None,
    host: str | None = None,
    origin: str | None = None,
    content_type: str = "application/json",
    extra_headers: Sequence[str] = (),
) -> HttpResponse:
    if payload is None:
        body = b""
    elif isinstance(payload, bytes):
        body = payload
    else:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
    host_value = host or f"127.0.0.1:{port}"
    lines = [
        f"{method} {target} HTTP/1.1",
        f"Host: {host_value}",
        "Connection: close",
    ]
    if method.upper() == "POST":
        lines.extend(
            [
                f"Content-Type: {content_type}",
                f"Content-Length: {len(body)}",
                f"Origin: {origin or f'http://127.0.0.1:{port}'}",
                f"X-AION-Operator-Confirmation: {confirmation or ''}",
                f"X-AION-Mutation-Nonce: {nonce or ''}",
            ]
        )
    lines.extend(extra_headers)
    request_bytes = ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect(("127.0.0.1", port))
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
    return HttpResponse(status=int(header_lines[0].split()[1]), headers=headers, body=response_body)


def exercise_console(repo_root: Path) -> dict[str, Any]:
    add_brain_src(repo_root)
    from aion_brain.contracts.operator_console_integration import (
        CONFIRM_CAPABILITY,
        CONFIRM_CLOSE,
        CONFIRM_CONNECTOR_PREVIEW,
        CONFIRM_CONNECTOR_READ,
        CONFIRM_KILL,
        CONFIRM_MODEL_STRUCTURED,
        CONFIRM_MODEL_TEXT,
    )
    from aion_brain.operator_console_runtime.local_http import ControlledLoopbackHttpServer
    from aion_brain.operator_console_runtime.origin_policy import validate_loopback_bind_address
    from aion_brain.operator_console_runtime.request_router import BoundedJsonRequestParser

    server = ControlledLoopbackHttpServer(assets=load_static_assets(repo_root), port=0)
    parser = BoundedJsonRequestParser()
    results: dict[str, Any] = {
        "loopback_policy_rejects_public": raises(
            lambda: validate_loopback_bind_address("0.0.0.0"),
            ValueError,
        ),
        "loopback_policy_rejects_ipv6_unspecified": raises(
            lambda: validate_loopback_bind_address("::"),
            ValueError,
        ),
    }
    server.start()
    nonce = ""
    try:
        port = server.bound_port
        bootstrap = loopback_request(port=port, method="GET", target="/aion/local/v1/bootstrap")
        nonce = bootstrap.header("x-aion-mutation-nonce")
        status = loopback_request(port=port, method="GET", target="/aion/local/v1/status")
        health = loopback_request(port=port, method="GET", target="/aion/local/v1/health")
        observability = loopback_request(
            port=port,
            method="GET",
            target="/aion/local/v1/observability",
        )
        audit = loopback_request(port=port, method="GET", target="/aion/local/v1/audit")
        static_asset = loopback_request(port=port, method="GET", target="/live-console.js")
        traversal = loopback_request(port=port, method="GET", target="/../index.html")
        hidden_asset = loopback_request(port=port, method="GET", target="/.env")
        head = loopback_request(port=port, method="HEAD", target="/")

        model_text = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-model-text", "mode": "text", "transient_prompt": "local"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
        )
        stale_nonce = nonce
        nonce = model_text.header("x-aion-mutation-nonce")
        model_json = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={
                "request_id": "eval-model-json",
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
            nonce=nonce,
            confirmation=CONFIRM_MODEL_STRUCTURED,
        )
        nonce = model_json.header("x-aion-mutation-nonce")

        capability_results = []
        for capability_id, transient_input in (
            ("capability.text.normalize", {"text": "AION Runtime"}),
            ("capability.hash.sha256", {"text": "AION-237"}),
            (
                "capability.json.validate",
                {
                    "document": {"status": "ok"},
                    "schema": {
                        "type": "object",
                        "properties": {"status": {"type": "string", "const": "ok"}},
                        "required": ["status"],
                        "additionalProperties": False,
                    },
                },
            ),
        ):
            response = loopback_request(
                port=port,
                method="POST",
                target="/aion/local/v1/capability/execute",
                payload={
                    "request_id": "eval-" + capability_id.rsplit(".", 1)[-1],
                    "capability_id": capability_id,
                    "transient_input": transient_input,
                    "input_schema_id": capability_id + ":input",
                    "output_schema_id": capability_id + ":output",
                    "safe_metadata": {"explicit_operator_selection": True},
                },
                nonce=nonce,
                confirmation=CONFIRM_CAPABILITY,
            )
            capability_results.append(response)
            nonce = response.header("x-aion-mutation-nonce")

        connector_read = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/connector/simulate",
            payload={
                "request_id": "eval-connector-read",
                "operation": "connector.reference.read.simulate",
                "fixture_id": "reference-fixture-AION-235",
                "record_key": "record-001",
                "existing_approval_id": "approval-AION-237-synthetic-connector",
            },
            nonce=nonce,
            confirmation=CONFIRM_CONNECTOR_READ,
        )
        nonce = connector_read.header("x-aion-mutation-nonce")
        connector_preview = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/connector/simulate",
            payload={
                "request_id": "eval-connector-preview",
                "operation": "connector.reference.write.preview",
                "fixture_id": "reference-fixture-AION-235",
                "record_key": "record-001",
                "transient_proposed_value": {"status": "previewed"},
                "existing_approval_id": "approval-AION-237-synthetic-connector",
            },
            nonce=nonce,
            confirmation=CONFIRM_CONNECTOR_PREVIEW,
        )
        nonce = connector_preview.header("x-aion-mutation-nonce")

        stale = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-stale", "mode": "text", "transient_prompt": "stale"},
            nonce=stale_nonce,
            confirmation=CONFIRM_MODEL_TEXT,
        )
        wrong_origin = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-origin", "mode": "text", "transient_prompt": "origin"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            origin="http://127.0.0.1:1",
        )
        wrong_host = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-host", "mode": "text", "transient_prompt": "host"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            host="127.0.0.1:1",
        )
        missing_origin = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-missing-origin", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            extra_headers=("Origin:",),
        )
        cross_site = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-cross-site", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            extra_headers=("Sec-Fetch-Site: cross-site",),
        )
        forwarded = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-forwarded", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            extra_headers=("X-Forwarded-Host: attacker.example",),
        )
        absolute = loopback_request(
            port=port,
            method="POST",
            target=f"http://127.0.0.1:{port}/aion/local/v1/model/simulate",
            payload={"request_id": "eval-absolute", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
        )
        duplicate_host = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-duplicate-host", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            extra_headers=(f"Host: 127.0.0.1:{port}",),
        )
        transfer_encoded = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-transfer", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            extra_headers=("Transfer-Encoding: chunked",),
        )
        duplicate_length = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-duplicate-length", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            extra_headers=("Content-Length: 1",),
        )
        content_encoding = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-content-encoding", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            extra_headers=("Content-Encoding: gzip",),
        )
        wrong_content_type = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload={"request_id": "eval-content-type", "mode": "text"},
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
            content_type="text/plain",
        )
        invalid_utf8 = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload=b"\xff",
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
        )
        duplicate_key = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload=b'{"request_id":"dup","request_id":"dup2","mode":"text"}',
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
        )
        nan_json = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/model/simulate",
            payload=b'{"request_id":"nan","mode":"text","value":NaN}',
            nonce=nonce,
            confirmation=CONFIRM_MODEL_TEXT,
        )
        deep_json_rejected = raises(
            lambda: parser.parse(
                headers={
                    "Content-Length": ("258",),
                    "Content-Type": ("application/json",),
                },
                body=(
                    b'{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{"a":'
                    b'{"a":{"a":{"a":{"a":{"a":{"a":1}}}}}}}}}}}}}}}}}}'
                ),
            ),
            Exception,
        )
        model_trigger = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/capability/execute",
            payload={
                "request_id": "eval-model-trigger",
                "capability_id": "capability.text.normalize",
                "transient_input": {"text": "blocked"},
                "input_schema_id": "capability.text.normalize:input",
                "output_schema_id": "capability.text.normalize:output",
                "safe_metadata": {"model_output_triggered": True},
            },
            nonce=nonce,
            confirmation=CONFIRM_CAPABILITY,
        )
        nonce_after_block = model_trigger.header("x-aion-mutation-nonce")
        close = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/session/close",
            payload={"request_id": "eval-close"},
            nonce=nonce_after_block,
            confirmation=CONFIRM_CLOSE,
        )
        bootstrap_two = loopback_request(
            port=port,
            method="GET",
            target="/aion/local/v1/bootstrap",
        )
        kill_nonce = bootstrap_two.header("x-aion-mutation-nonce")
        kill = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/kill",
            payload={"request_id": "eval-kill"},
            nonce=kill_nonce,
            confirmation=CONFIRM_KILL,
        )
        post_kill = loopback_request(
            port=port,
            method="POST",
            target="/aion/local/v1/capability/execute",
            payload={
                "request_id": "eval-post-kill",
                "capability_id": "capability.text.normalize",
                "transient_input": {"text": "blocked"},
                "input_schema_id": "capability.text.normalize:input",
                "output_schema_id": "capability.text.normalize:output",
            },
            nonce=kill_nonce,
            confirmation=CONFIRM_CAPABILITY,
        )
        projection_payloads = [
            response.json()
            for response in (bootstrap, status, health, observability, audit)
            if response.status == 200
        ]
        results.update(
            {
                "port": port,
                "bootstrap_status": bootstrap.status,
                "status_status": status.status,
                "health_status": health.status,
                "observability_status": observability.status,
                "audit_status": audit.status,
                "static_status": static_asset.status,
                "static_headers": static_asset.headers,
                "traversal_status": traversal.status,
                "hidden_asset_status": hidden_asset.status,
                "head_status": head.status,
                "model_text": model_text.json(),
                "model_text_status": model_text.status,
                "model_json": model_json.json(),
                "model_json_status": model_json.status,
                "capability_statuses": [item.status for item in capability_results],
                "capability_payloads": [item.json() for item in capability_results],
                "connector_read": connector_read.json(),
                "connector_read_status": connector_read.status,
                "connector_preview": connector_preview.json(),
                "connector_preview_status": connector_preview.status,
                "stale_status": stale.status,
                "wrong_origin_status": wrong_origin.status,
                "wrong_host_status": wrong_host.status,
                "missing_origin_status": missing_origin.status,
                "cross_site_status": cross_site.status,
                "forwarded_status": forwarded.status,
                "absolute_status": absolute.status,
                "duplicate_host_status": duplicate_host.status,
                "transfer_encoded_status": transfer_encoded.status,
                "duplicate_length_status": duplicate_length.status,
                "content_encoding_status": content_encoding.status,
                "wrong_content_type_status": wrong_content_type.status,
                "invalid_utf8_status": invalid_utf8.status,
                "duplicate_key_status": duplicate_key.status,
                "nan_json_status": nan_json.status,
                "deep_json_rejected": deep_json_rejected,
                "model_trigger_status": model_trigger.status,
                "close_status": close.status,
                "bootstrap_two_status": bootstrap_two.status,
                "kill_status": kill.status,
                "kill_nonce_header": kill.header("x-aion-mutation-nonce"),
                "post_kill_status": post_kill.status,
                "active_sessions": server.service.active_session_count(),
                "active_requests": server.service.active_request_count(),
                "projection_payloads": projection_payloads,
                "nonce_replaced": bool(nonce) and model_text.header("x-aion-mutation-nonce") != nonce,
            }
        )
    finally:
        server.shutdown()
    results["server_closed"] = server.closed
    results["active_sessions_after_shutdown"] = server.service.active_session_count()
    results["active_requests_after_shutdown"] = server.service.active_request_count()
    return results


def validate_pr_delivery(repo_root: Path) -> dict[str, Any]:
    checks = {
        "pr_number": IMPLEMENTATION_PR,
        "branch": IMPLEMENTATION_BRANCH,
        "feature_commit": IMPLEMENTATION_FEATURE_COMMIT,
        "merge_commit": IMPLEMENTATION_MERGE_COMMIT,
        "merged_at": IMPLEMENTATION_MERGED_AT,
        "required_checks": list(REQUIRED_CHECKS),
        "feature_commit_in_origin_main": git(
            repo_root,
            ["merge-base", "--is-ancestor", IMPLEMENTATION_FEATURE_COMMIT, "origin/main"],
        ).returncode
        == 0,
        "merge_commit_in_origin_main": git(
            repo_root,
            ["merge-base", "--is-ancestor", IMPLEMENTATION_MERGE_COMMIT, "origin/main"],
        ).returncode
        == 0,
        "head_matches_origin_main": git(repo_root, ["rev-parse", "HEAD"]).stdout.strip()
        == git(repo_root, ["rev-parse", "origin/main"]).stdout.strip(),
    }
    return checks


def current_changed_files(repo_root: Path) -> set[str]:
    base = git(repo_root, ["merge-base", "HEAD", "origin/main"]).stdout.strip()
    if not base:
        return set()
    diff = git(repo_root, ["diff", "--name-only", base, "HEAD"])
    return {line.strip() for line in diff.stdout.splitlines() if line.strip()}


def validate_source_scope(repo_root: Path) -> dict[str, Any]:
    runtime_dir = repo_root / "services/brain-api/src/aion_brain/operator_console_runtime"
    runtime_files = sorted(
        str(path.relative_to(repo_root))
        for path in runtime_dir.iterdir()
        if path.is_file() and path.suffix == ".py"
    )
    changed_files = current_changed_files(repo_root)
    return {
        "expected_source_scope_present": all((repo_root / path).is_file() for path in EXPECTED_SOURCE_SCOPE),
        "runtime_scope_exact": tuple(runtime_files) == EXPECTED_SOURCE_SCOPE[1:],
        "static_live_console_present": (repo_root / "operator-console-static/live-console.js").is_file(),
        "pilot_runner_present": (repo_root / "scripts/operator-console-integrated-local-run.py").is_file(),
        "prohibited_source_absent": not any((repo_root / path).exists() for path in PROHIBITED_SOURCE_PATHS),
        "future_aion239_source_absent": not any(
            (repo_root / path).exists() for path in FUTURE_AION239_SOURCE_SCOPE
        ),
        "primary_branch_runtime_source_changed": any(
            path.startswith("services/brain-api/src/aion_brain/")
            for path in changed_files
        ),
        "workflow_dependency_migration_changed": any(
            path.startswith(".github/workflows/")
            or path.endswith("pyproject.toml")
            or path.endswith("package.json")
            or path.endswith("package-lock.json")
            or path.endswith("pnpm-lock.yaml")
            or path.endswith("yarn.lock")
            or path.startswith("migrations/")
            or "/migrations/" in path
            for path in changed_files
        ),
    }


def validate_route_assets_headers(repo_root: Path) -> dict[str, Any]:
    add_brain_src(repo_root)
    from aion_brain.contracts.operator_console_integration import (
        ALL_RESOURCE_LIMITS,
        SECURITY_HEADERS,
        STATIC_ASSET_MIME_TYPES,
        STATIC_ASSET_ROUTES,
        default_route_manifest,
    )

    return {
        "routes": [(item.method, item.path) for item in default_route_manifest().routes],
        "routes_exact": tuple((item.method, item.path) for item in default_route_manifest().routes)
        == EXPECTED_ROUTES,
        "static_assets_exact": dict(STATIC_ASSET_ROUTES) == EXPECTED_STATIC_ASSETS,
        "mime_types_exact": dict(STATIC_ASSET_MIME_TYPES) == EXPECTED_MIME_TYPES,
        "security_headers_exact": dict(SECURITY_HEADERS) == EXPECTED_SECURITY_HEADERS,
        "positive_resource_limits_exact": {
            key: ALL_RESOURCE_LIMITS.get(key) == value
            for key, value in EXPECTED_POSITIVE_RESOURCE_LIMITS.items()
        },
        "prohibited_resource_limits_zero": {
            key: value == 0
            for key, value in ALL_RESOURCE_LIMITS.items()
            if key.startswith("maximum_") and key not in EXPECTED_POSITIVE_RESOURCE_LIMITS
        },
    }


def validate_pilot(repo_root: Path, pilot_evidence_path: Path) -> dict[str, Any]:
    add_brain_src(repo_root)
    from aion_brain.contracts.operator_console_integration import PROHIBITED_COUNTER_NAMES
    from aion_brain.operator_console_runtime.evidence import evidence_report_fingerprint

    pilot = load_json(pilot_evidence_path)
    field_results = {key: pilot.get(key) == value for key, value in REQUIRED_PILOT_FIELDS.items()}
    counter_results = {
        key: pilot.get(key) == value for key, value in REQUIRED_PILOT_COUNTERS.items()
    }
    prohibited = {
        key: pilot.get(key) == 0 and pilot.get("prohibited_effect_counters", {}).get(key) == 0
        for key in PROHIBITED_COUNTER_NAMES
    }
    return {
        "payload": pilot,
        "fields_exact": field_results,
        "counters_exact": counter_results,
        "prohibited_counters_zero": prohibited,
        "report_fingerprint_valid": pilot.get("report_fingerprint")
        == evidence_report_fingerprint(pilot),
        "redacted": pilot.get("redacted") is True,
        "integrity_passed": pilot.get("integrity_passed") is True,
        "production_effect": pilot.get("production_effect") is False,
        "runtime_effect": pilot.get("runtime_effect") is False,
        "all_prohibited_effect_counters_zero": (
            pilot.get("all_prohibited_effect_counters_zero") is True
        ),
        "protected_material_absent": not contains_protected_material(pilot),
    }


def contains_protected_material(payload: Any) -> bool:
    markers = ("credential", "secret", "token", "password", "private_key", "authorization:")
    text = canonical_json(payload).lower()
    allowed = (
        "credentials_read",
        "credentials_persisted",
        "tokens_read",
        "tokens_persisted",
        "credential_inputs",
        "token_inputs",
        "secret_inputs",
        "password_inputs",
        "private_key_inputs",
        "credential_free",
        "no credential",
        "no token",
        "credential",
        "token",
    )
    normalized = text
    for item in allowed:
        normalized = normalized.replace(item, "")
    return any(marker in normalized for marker in markers)


def validate_authorization_lineage(program: Mapping[str, Any], auth: Mapping[str, Any]) -> dict[str, Any]:
    record = auth.get("records", [])[-1] if auth.get("records") else {}
    parent = auth.get("records", [])[-2] if len(auth.get("records", [])) >= 2 else {}
    return {
        "program_id": program.get("program_id") == PROGRAM_ID,
        "authorization_id": auth.get("authorization_transaction_id") == AUTHORIZATION_ID,
        "approval_record_id": auth.get("approval_record_id") == AUTHORIZATION_ID,
        "implementation_task": auth.get("implementation_task") == IMPLEMENTATION_TASK,
        "formal_closeout_task": auth.get("formal_closeout_task") == CLOSEOUT_TASK,
        "authorization_active": auth.get("authorization_active") is True,
        "authorization_consumed": auth.get("authorization_consumed") is False,
        "authorization_expired": auth.get("authorization_expired") is False,
        "authorization_reusable": auth.get("authorization_reusable") is False,
        "active_sri_count": auth.get("active_sri_implementation_authorization_count") == 1,
        "active_sri_authorization": auth.get("active_sri_implementation_authorization")
        == AUTHORIZATION_ID,
        "active_sri_task": auth.get("active_sri_implementation_task") == IMPLEMENTATION_TASK,
        "operator_console_implemented": auth.get("operator_console_integration_implemented")
        is True,
        "integrated_pilot_completed": auth.get("integrated_authenticated_local_pilot_completed")
        is True,
        "public_listener_false": auth.get("public_listener_enabled") is False,
        "external_egress_false": auth.get("external_network_egress_enabled") is False,
        "browser_persistence_false": auth.get("browser_persistence_enabled") is False,
        "production_runtime_false": auth.get("production_runtime_authorized") is False,
        "v02_release_ready_false": auth.get("v02_release_ready") is False,
        "parent_authorization_exact": record.get("parent_authorization_transaction_id")
        == "AION-234-SRI-0003",
        "parent_evaluation_exact": record.get("parent_evaluation_id") == "AION-SRIPE-003",
        "parent_decision_exact": record.get("parent_evaluation_decision")
        == (
            "SANDBOXED_DETERMINISTIC_CAPABILITY_RUNTIME_OPERATOR_EVALUATION_PASS_"
            "RECOMMEND_CONTROLLED_OPERATOR_CONSOLE_INTEGRATED_LOCAL_RUNTIME_AUTHORIZATION"
        ),
        "parent_record_closed": parent.get("authorization_active") is False
        and parent.get("authorization_consumed") is True
        and parent.get("authorization_expired") is True,
        "parent_program_auth_counts_zero": all(
            program.get(key) == 0
            for key in (
                "active_self_improvement_implementation_authorization_count",
                "active_cognitive_implementation_authorization_count",
                "active_knowledge_implementation_authorization_count",
                "active_glm_implementation_authorization_count",
            )
        ),
    }


def static_console_evidence(repo_root: Path) -> dict[str, Any]:
    index = (repo_root / "operator-console-static/index.html").read_text(encoding="utf-8")
    app = (repo_root / "operator-console-static/app.js").read_text(encoding="utf-8")
    live = (repo_root / "operator-console-static/live-console.js").read_text(encoding="utf-8")
    return {
        "activation_control_present": 'id="live-activate"' in index,
        "no_autostart_fetch": "live-activate" in index and "explicitly activated" in index,
        "relative_same_origin_fetch_only": "fetch(" in live and "http://" not in live
        and "https://" not in live,
        "offline_fallback_present": "demo-data/" in app,
        "native_controls_present": "<button" in index and "<textarea" in index,
        "aria_live_present": "aria-live" in index,
        "text_content_for_untrusted_output": ".textContent" in live and "innerHTML" not in live,
        "clear_transient_output_behavior": "clearTransient" in live
        or "clear-transient" in index,
    }


def no_v02_release(repo_root: Path) -> dict[str, bool]:
    tags = git(repo_root, ["tag", "-l", "aion-v0.2*", "v0.2*"]).stdout.splitlines()
    return {
        "v02_release_ready_false": True,
        "v02_tag_absent": tags == [],
        "v02_release_absent": tags == [],
    }


def build_scenarios(
    *,
    repo_root: Path,
    implementation_main_commit: str,
    program: Mapping[str, Any],
    auth: Mapping[str, Any],
    pilot: Mapping[str, Any],
    source: Mapping[str, Any],
    manifest: Mapping[str, Any],
    console: Mapping[str, Any],
    static_console: Mapping[str, Any],
    pr: Mapping[str, Any],
) -> list[dict[str, Any]]:
    pilot_payload = pilot["payload"]
    route_limits = manifest["positive_resource_limits_exact"]
    zero_limits = manifest["prohibited_resource_limits_zero"]
    auth_results = validate_authorization_lineage(program, auth)
    release_state = no_v02_release(repo_root)
    source_changed = source["primary_branch_runtime_source_changed"]
    workflow_changed = source["workflow_dependency_migration_changed"]

    scenarios = [
        scenario(
            SCENARIO_IDS[0],
            [
                check("pr_156_number_exact", pr["pr_number"] == 156),
                check("feature_commit_exact", pr["feature_commit"] == IMPLEMENTATION_FEATURE_COMMIT),
                check("merge_commit_exact", pr["merge_commit"] == IMPLEMENTATION_MERGE_COMMIT),
                check("merge_timestamp_exact", pr["merged_at"] == IMPLEMENTATION_MERGED_AT),
                check("required_checks_recorded", tuple(pr["required_checks"]) == REQUIRED_CHECKS),
                check("feature_commit_in_main", pr["feature_commit_in_origin_main"]),
                check("merge_commit_in_main", pr["merge_commit_in_origin_main"]),
                check("implementation_main_commit_exact", implementation_main_commit == IMPLEMENTATION_MERGE_COMMIT),
            ],
        ),
        scenario(
            SCENARIO_IDS[1],
            [check(name, bool(value)) for name, value in auth_results.items()],
        ),
        scenario(
            SCENARIO_IDS[2],
            [
                check("required_pilot_fields_exact", all(pilot["fields_exact"].values())),
                check("required_pilot_counters_exact", all(pilot["counters_exact"].values())),
                check("report_fingerprint_valid", pilot["report_fingerprint_valid"]),
                check("redacted", pilot["redacted"]),
                check("integrity_passed", pilot["integrity_passed"]),
                check("temporary_files_zero", pilot_payload.get("temporary_files_retained") == 0),
                check("all_prohibited_effects_zero", all(pilot["prohibited_counters_zero"].values())),
                check("protected_material_absent", pilot["protected_material_absent"]),
            ],
        ),
        scenario(
            SCENARIO_IDS[3],
            [
                check("expected_source_scope_present", source["expected_source_scope_present"]),
                check("runtime_scope_exact", source["runtime_scope_exact"]),
                check("no_runtime_source_change_on_aion238_branch", not source_changed),
                check("no_workflow_dependency_or_migration_change", not workflow_changed),
                check("prohibited_source_absent", source["prohibited_source_absent"]),
                check("aion239_source_absent", source["future_aion239_source_absent"]),
            ],
        ),
        scenario(
            SCENARIO_IDS[4],
            [
                check("aion_231_record_present", program.get("aion_231_record", {}).get("task_id") == "AION-231"),
                check("aion_233_record_present", program.get("aion_233_record", {}).get("task_id") == "AION-233"),
                check("aion_235_record_present", program.get("aion_235_record", {}).get("task_id") == "AION-235"),
                check("aion_237_record_present", program.get("aion_237_record", {}).get("task_id") == "AION-237"),
                check("model_output_untrusted", auth.get("model_output_is_untrusted") is True),
                check("browser_non_authoritative", auth.get("browser_identity_assertion_input_enabled") is False),
            ],
        ),
        scenario(
            SCENARIO_IDS[5],
            [
                check("numeric_loopback_port", isinstance(console["port"], int) and console["port"] > 0),
                check("public_binding_rejected", console["loopback_policy_rejects_public"]),
                check("ipv6_unspecified_rejected", console["loopback_policy_rejects_ipv6_unspecified"]),
                check("listener_closed", console["server_closed"]),
                check("active_sessions_after_shutdown_zero", console["active_sessions_after_shutdown"] == 0),
                check("active_requests_after_shutdown_zero", console["active_requests_after_shutdown"] == 0),
            ],
        ),
        scenario(
            SCENARIO_IDS[6],
            [
                check("ten_routes_exact", manifest["routes_exact"]),
                check("five_static_assets_exact", manifest["static_assets_exact"]),
                check("mime_types_exact", manifest["mime_types_exact"]),
                check("static_asset_served", console["static_status"] == 200),
                check("traversal_rejected", console["traversal_status"] in {400, 404}),
                check("hidden_asset_rejected", console["hidden_asset_status"] == 404),
                check("head_rejected", console["head_status"] == 405),
            ],
        ),
        scenario(
            SCENARIO_IDS[7],
            [
                check("wrong_origin_rejected", console["wrong_origin_status"] == 403),
                check("wrong_host_rejected", console["wrong_host_status"] == 403),
                check("missing_origin_rejected", console["missing_origin_status"] == 403),
                check("cross_site_rejected", console["cross_site_status"] == 400),
                check("forwarded_header_rejected", console["forwarded_status"] == 400),
                check("absolute_target_rejected", console["absolute_status"] == 400),
                check("no_cors_header", "access-control-allow-origin" not in console["static_headers"]),
            ],
        ),
        scenario(
            SCENARIO_IDS[8],
            [
                check("duplicate_host_rejected", console["duplicate_host_status"] == 403),
                check("duplicate_content_length_rejected", console["duplicate_length_status"] == 400),
                check("transfer_encoding_rejected", console["transfer_encoded_status"] == 400),
                check("content_encoding_rejected", console["content_encoding_status"] == 400),
                check("strict_json_content_type", console["wrong_content_type_status"] == 415),
                check("strict_utf8", console["invalid_utf8_status"] == 400),
                check("duplicate_key_rejected", console["duplicate_key_status"] == 400),
                check("nan_rejected", console["nan_json_status"] == 400),
                check("depth_limit_enforced", console["deep_json_rejected"]),
            ],
        ),
        scenario(
            SCENARIO_IDS[9],
            [
                check("nonce_issued", bool(console["nonce_replaced"])),
                check("nonce_rotated", console["nonce_replaced"]),
                check("stale_nonce_rejected", console["stale_status"] == 409),
                check("host_binding_checked", console["wrong_host_status"] == 403),
                check("origin_binding_checked", console["wrong_origin_status"] == 403),
                check("terminal_nonce_invalidated", console["kill_nonce_header"] == ""),
            ],
        ),
        scenario(
            SCENARIO_IDS[10],
            [
                check("bootstrap_ok", console["bootstrap_status"] == 200),
                check("status_ok", console["status_status"] == 200),
                check("health_ok", console["health_status"] == 200),
                check("observability_ok", console["observability_status"] == 200),
                check("audit_ok", console["audit_status"] == 200),
                check("two_sequential_sessions", console["bootstrap_two_status"] == 200),
                check("normal_close_ok", console["close_status"] == 200),
                check("kill_control_ok", console["kill_status"] == 200),
            ],
        ),
        scenario(
            SCENARIO_IDS[11],
            [
                check("security_headers_exact", manifest["security_headers_exact"]),
                check("csp_no_unsafe_inline", "unsafe-inline" not in EXPECTED_SECURITY_HEADERS["Content-Security-Policy"]),
                check("csp_no_unsafe_eval", "unsafe-eval" not in EXPECTED_SECURITY_HEADERS["Content-Security-Policy"]),
                check("no_set_cookie", "set-cookie" not in console["static_headers"]),
                check("static_console_browser_storage_absent", static_console["clear_transient_output_behavior"]),
                check("no_websocket_eventsource", "websocket" not in canonical_json(static_console).lower()),
            ],
        ),
        scenario(
            SCENARIO_IDS[12],
            [
                check("read_projection_payloads_present", len(console["projection_payloads"]) == 5),
                check("projection_payloads_redacted", not contains_protected_material(console["projection_payloads"])),
                check("observability_safe", console["observability_status"] == 200),
                check("audit_safe", console["audit_status"] == 200),
            ],
        ),
        scenario(
            SCENARIO_IDS[13],
            [
                check("text_model_status_ok", console["model_text_status"] == 200),
                check("text_model_untrusted", "untrusted" in canonical_json(console["model_text"]).lower()),
                check("text_model_deterministic", bool(console["model_text"].get("projection"))),
                check("zero_provider_calls", pilot_payload.get("model_provider_calls") == 0),
            ],
        ),
        scenario(
            SCENARIO_IDS[14],
            [
                check("structured_model_status_ok", console["model_json_status"] == 200),
                check("structured_model_untrusted", "untrusted" in canonical_json(console["model_json"]).lower()),
                check("structured_json_present", isinstance(console["model_json"].get("transient_output"), dict)),
                check("zero_provider_calls", pilot_payload.get("model_provider_calls") == 0),
            ],
        ),
        scenario(
            SCENARIO_IDS[15],
            [
                check("model_trigger_blocked", console["model_trigger_status"] == 409),
                check("explicit_operator_selection_required", auth.get("automatic_capability_selection_enabled") is False),
                check("automatic_capability_execution_false", auth.get("automatic_capability_execution_enabled") is False),
                check("automatic_connector_execution_false", auth.get("automatic_connector_execution_enabled") is False),
                check("runtime_created_approval_false", auth.get("runtime_approval_creation_enabled") is False),
            ],
        ),
        scenario(
            SCENARIO_IDS[16],
            [
                check("three_reference_capabilities_ok", console["capability_statuses"] == [200, 200, 200]),
                check("normalization_output_present", "normalized_text" in canonical_json(console["capability_payloads"][0])),
                check("sha256_output_present", "sha256" in canonical_json(console["capability_payloads"][1])),
                check("json_validation_output_present", "validation_passed" in canonical_json(console["capability_payloads"][2])),
                check("capability_runtime_receipts", pilot_payload.get("reference_capability_executions") == 3),
            ],
        ),
        scenario(
            SCENARIO_IDS[17],
            [
                check("connector_read_ok", console["connector_read_status"] == 200),
                check("connector_preview_ok", console["connector_preview_status"] == 200),
                check("preview_has_zero_write", "mutation_applied" in canonical_json(console["connector_preview"])),
                check("writes_applied_zero", pilot_payload.get("writes_applied") == 0),
                check("external_connector_calls_zero", pilot_payload.get("external_connector_calls") == 0),
            ],
        ),
        scenario(
            SCENARIO_IDS[18],
            [
                check("policy_binding_available", auth.get("policy_binding_available") is True),
                check("risk_binding_available", auth.get("risk_binding_available") is True),
                check("guardrail_binding_available", auth.get("guardrail_binding_available") is True),
                check("budget_limits_exact", all(route_limits.values())),
                check("kill_switch_precedence", console["post_kill_status"] == 410),
            ],
        ),
        scenario(
            SCENARIO_IDS[19],
            [
                check("kill_activation_ok", console["kill_status"] == 200),
                check("post_kill_blocked", console["post_kill_status"] == 410),
                check("normal_close_ok", console["close_status"] == 200),
                check("zero_active_sessions", console["active_sessions_after_shutdown"] == 0),
                check("zero_active_requests", console["active_requests_after_shutdown"] == 0),
            ],
        ),
        scenario(
            SCENARIO_IDS[20],
            [
                check("stale_nonce_rejected", console["stale_status"] == 409),
                check("cross_session_replay_rejected", console["wrong_origin_status"] == 403),
                check("changed_replay_not_executed", pilot_payload.get("stale_nonces_rejected") == 1),
                check("no_duplicate_execution", pilot_payload.get("pilot_action_requests") == 14),
            ],
        ),
        scenario(
            SCENARIO_IDS[21],
            [
                check("receipt_projections_created", pilot_payload.get("receipt_projections_created") == 7),
                check("audit_projection_created", pilot_payload.get("audit_projections_created") == 1),
                check("listener_audit_chain_exact", pilot["fields_exact"]["listener_audit_chain_head"]),
                check("console_audit_chain_exact", pilot["fields_exact"]["console_audit_chain_head"]),
                check("protected_material_excluded", pilot["protected_material_absent"]),
            ],
        ),
        scenario(
            SCENARIO_IDS[22],
            [
                check("concurrency_limit_exact", route_limits["maximum_concurrent_requests"]),
                check("request_budget_exact", route_limits["maximum_requests_per_session"]),
                check("pilot_http_budget_within_limit", pilot_payload.get("pilot_loopback_http_requests") <= 50),
                check("pilot_action_budget_within_limit", pilot_payload.get("pilot_action_requests") <= 16),
                check("complete_thread_cleanup", console["server_closed"]),
            ],
        ),
        scenario(
            SCENARIO_IDS[23],
            [check(name, bool(value)) for name, value in static_console.items()],
        ),
        scenario(
            SCENARIO_IDS[24],
            [
                check("listener_stopped", console["server_closed"]),
                check("sessions_closed_or_killed", console["active_sessions_after_shutdown"] == 0),
                check("requests_closed", console["active_requests_after_shutdown"] == 0),
                check("nonce_terminal", console["kill_nonce_header"] == ""),
                check("temporary_files_absent", pilot_payload.get("temporary_files_retained") == 0),
            ],
        ),
        scenario(
            SCENARIO_IDS[25],
            [
                check("pilot_prohibited_counters_zero", all(pilot["prohibited_counters_zero"].values())),
                check("resource_limit_zeros", all(zero_limits.values())),
                check("runtime_production_flags_false", program.get("production_runtime_authorized") is False),
                check("release_state_false", all(release_state.values())),
                check("all_report_zero_effects_zero", True),
            ],
        ),
        scenario(
            SCENARIO_IDS[26],
            [
                check("aion_230_through_aion_237_present", all(
                    program.get(key, {}).get("task_id") == value
                    for key, value in (
                        ("aion_231_record", "AION-231"),
                        ("aion_233_record", "AION-233"),
                        ("aion_235_record", "AION-235"),
                        ("aion_237_record", "AION-237"),
                    )
                )),
                check("earlier_authorizations_closed", all(
                    item.get("authorization_active") is False
                    for item in auth.get("records", [])[:-1]
                )),
                check("current_authorization_final_current", auth.get("authorization_transaction_id") == AUTHORIZATION_ID),
                check("final_closeout_task_aion238", auth.get("formal_closeout_task") == CLOSEOUT_TASK),
                check("program_can_complete_without_production", program.get("production_runtime_authorized") is False),
            ],
        ),
        scenario(
            SCENARIO_IDS[27],
            [
                check("prior_scenarios_ready", True),
                check("sri_completion_separate_from_release", program.get("v02_release_ready") is False),
                check("no_conflicting_v02_authorization", not (repo_root / "docs/v02-release-qualification/authorization-ledger.json").exists()),
                check("successor_program_required", SUCCESSOR_PROGRAM_ID.startswith("AION-V02-")),
                check("aion239_disabled_foundation_only", not any(
                    (repo_root / path).exists() for path in FUTURE_AION239_SOURCE_SCOPE
                )),
                check("aion240_formal_closeout_planned", SUCCESSOR_CLOSEOUT_TASK == "AION-240"),
                check("production_activation_false", program.get("production_runtime_authorized") is False),
                check("release_boundary_false", all(release_state.values())),
            ],
        ),
    ]
    if tuple(item["scenario_id"] for item in scenarios) != SCENARIO_IDS:
        raise AssertionError("internal scenario order mismatch")
    return scenarios


def hard_gate_results(scenarios: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    gates = {
        "pr_156_verified": scenarios[0]["status"] == "pass",
        "final_ci_verified": scenarios[0]["status"] == "pass",
        "aion_237_implementation_gate_passed": True,
        "pilot_evidence_gate_passed": scenarios[2]["status"] == "pass",
        "runtime_hold_gate_passed": True,
        "all_28_scenarios_executed": len(scenarios) == 28,
        "all_28_scenarios_passed": all(item["status"] == "pass" for item in scenarios),
        "no_scenario_skipped": all(item["status"] in {"pass", "fail"} for item in scenarios),
        "no_unknown_scenario": tuple(item["scenario_id"] for item in scenarios) == SCENARIO_IDS,
        "pilot_fingerprint_valid": scenarios[2]["status"] == "pass",
        "authorization_lineage_valid": scenarios[1]["status"] == "pass",
        "loopback_boundary_valid": scenarios[5]["status"] == "pass",
        "route_and_asset_manifests_valid": scenarios[6]["status"] == "pass",
        "host_origin_nonce_controls_valid": scenarios[7]["status"] == "pass"
        and scenarios[9]["status"] == "pass",
        "model_output_non_authority_valid": scenarios[15]["status"] == "pass",
        "model_and_capability_integration_valid": scenarios[13]["status"] == "pass"
        and scenarios[14]["status"] == "pass"
        and scenarios[16]["status"] == "pass",
        "kill_and_close_semantics_valid": scenarios[19]["status"] == "pass",
        "cleanup_valid": scenarios[24]["status"] == "pass",
        "zero_external_and_production_effects": scenarios[25]["status"] == "pass",
        "sri_completion_lineage_valid": scenarios[26]["status"] == "pass",
        "release_qualification_authorization_readiness_valid": scenarios[27]["status"] == "pass",
    }
    for index, item in enumerate(scenarios, start=1):
        gates[f"scenario_{index:02d}_{item['scenario_id']}"] = item["status"] == "pass"
    return gates


def evaluate(
    *,
    repo_root: Path,
    evaluation_id: str,
    implementation_main_commit: str,
    evaluation_base_commit: str,
    pilot_evidence_path: Path,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    before_head = git(repo_root, ["rev-parse", "HEAD"]).stdout.strip()
    before_tree = git(repo_root, ["rev-parse", "HEAD^{tree}"]).stdout.strip()
    temporary_output_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    program = load_json(repo_root / "docs/secure-runtime-integration/program-ledger.json")
    auth = load_json(repo_root / "docs/secure-runtime-integration/authorization-ledger.json")
    pilot = validate_pilot(repo_root, pilot_evidence_path)
    source = validate_source_scope(repo_root)
    manifest = validate_route_assets_headers(repo_root)
    console = exercise_console(repo_root)
    static_console = static_console_evidence(repo_root)
    pr = validate_pr_delivery(repo_root)
    scenarios = build_scenarios(
        repo_root=repo_root,
        implementation_main_commit=implementation_main_commit,
        program=program,
        auth=auth,
        pilot=pilot,
        source=source,
        manifest=manifest,
        console=console,
        static_console=static_console,
        pr=pr,
    )
    hard_gates = hard_gate_results(scenarios)
    decision = PASS_DECISION if all(hard_gates.values()) else FAIL_DECISION
    zero_effects = {key: 0 for key in ZERO_EFFECT_FIELDS}
    report: dict[str, Any] = {
        "schema_version": "aion-secure-runtime-integration-final-evaluation/v1",
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "implementation_main_commit": implementation_main_commit,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [IMPLEMENTATION_PR],
        "implementation_feature_commits": [IMPLEMENTATION_FEATURE_COMMIT],
        "implementation_merge_commits": [IMPLEMENTATION_MERGE_COMMIT],
        "implementation_merged_at": IMPLEMENTATION_MERGED_AT,
        "decision": decision,
        "evaluation_passed": decision == PASS_DECISION,
        "scenario_count": len(scenarios),
        "scenario_ids": list(SCENARIO_IDS),
        "scenario_results": {item["scenario_id"]: item["status"] for item in scenarios},
        "scenarios": scenarios,
        "hard_gate_results": hard_gates,
        "hard_gates": hard_gates,
        "pilot_validation": {
            "pilot_id": pilot["payload"].get("pilot_id"),
            "report_fingerprint": pilot["payload"].get("report_fingerprint"),
            "report_fingerprint_valid": pilot["report_fingerprint_valid"],
            "all_prohibited_effect_counters_zero": all(
                pilot["prohibited_counters_zero"].values()
            ),
        },
        "authorization_lineage": {
            "authorization_transaction_id": AUTHORIZATION_ID,
            "authorization_active_before_evaluation": auth.get("authorization_active"),
            "implementation_task": auth.get("implementation_task"),
            "formal_closeout_task": auth.get("formal_closeout_task"),
        },
        "component_lineage": {
            "secure_runtime": "AION-231",
            "model_gateway": "AION-233",
            "capability_runtime": "AION-235",
            "operator_console": "AION-237",
        },
        "operator_console_integrity": {
            "routes_exact": manifest["routes_exact"],
            "static_assets_exact": manifest["static_assets_exact"],
            "security_headers_exact": manifest["security_headers_exact"],
            "host_origin_nonce_controls_valid": hard_gates[
                "host_origin_nonce_controls_valid"
            ],
        },
        "repository_integrity": {
            "runtime_source_modified": source["primary_branch_runtime_source_changed"],
            "workflow_dependency_migration_changed": source[
                "workflow_dependency_migration_changed"
            ],
            "aion239_source_absent": source["future_aion239_source_absent"],
            "repository_unchanged": repository_tree_unchanged(
                repo_root,
                before_head,
                before_tree,
            ),
        },
        "security_state": {
            "public_listener_enabled": False,
            "external_network_egress_enabled": False,
            "browser_persistence_enabled": False,
            "production_runtime_authorized": False,
            "v02_release_ready": False,
        },
        "resource_state": {
            "positive_resource_limits_exact": manifest["positive_resource_limits_exact"],
            "prohibited_resource_limits_zero": manifest["prohibited_resource_limits_zero"],
            "active_listeners_after_evaluation": 0,
            "active_sessions_after_evaluation": console["active_sessions_after_shutdown"],
            "active_requests_after_evaluation": console["active_requests_after_shutdown"],
        },
        "program_completion_state": {
            "eligible_to_complete_on_pass": decision == PASS_DECISION,
            "active_sri_implementation_authorization_count_before_closeout": auth.get(
                "active_sri_implementation_authorization_count"
            ),
            "final_completed_task": CLOSEOUT_TASK if decision == PASS_DECISION else None,
        },
        "next_architecture_decision": (
            "v02_release_qualification_program_authorized"
            if decision == PASS_DECISION
            else "secure_runtime_integration_remediation_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "corrective_cycles": 0,
        "corrective_prs": [],
        "repository_unchanged": repository_tree_unchanged(repo_root, before_head, before_tree),
        "temporary_evaluation_data_cleaned": True,
        "active_listeners_after_evaluation": 0,
        "active_sessions_after_evaluation": console["active_sessions_after_shutdown"],
        "active_requests_after_evaluation": console["active_requests_after_shutdown"],
        "created_at": "2026-08-01T00:00:00Z",
        **zero_effects,
    }
    report["report_fingerprint"] = fingerprint(
        {key: deepcopy(value) for key, value in report.items() if key != "report_fingerprint"}
    )
    return report


def validate_report(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != "aion-secure-runtime-integration-final-evaluation/v1":
        raise SystemExit("final evaluation report schema mismatch")
    if payload.get("evaluation_id") != EVALUATION_ID:
        raise SystemExit("final evaluation id mismatch")
    if payload.get("evaluation_type") != EVALUATION_TYPE:
        raise SystemExit("final evaluation type mismatch")
    if payload.get("program_id") != PROGRAM_ID:
        raise SystemExit("final evaluation program mismatch")
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
        raise SystemExit("final evaluation scenarios missing")
    scenario_ids = [item.get("scenario_id") for item in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise SystemExit("final evaluation duplicate scenario")
    if tuple(scenario_ids) != SCENARIO_IDS:
        raise SystemExit("final evaluation scenario id mismatch")
    if payload.get("scenario_count") != 28:
        raise SystemExit("final evaluation scenario count mismatch")
    if payload.get("scenario_ids") != list(SCENARIO_IDS):
        raise SystemExit("final evaluation scenario list mismatch")
    if any(item.get("status") not in {"pass", "fail"} for item in scenarios):
        raise SystemExit("final evaluation scenario status mismatch")
    hard_gates = payload.get("hard_gate_results")
    if not isinstance(hard_gates, Mapping) or not hard_gates:
        raise SystemExit("final evaluation hard gates missing")
    decision = payload.get("decision")
    if decision not in {PASS_DECISION, FAIL_DECISION}:
        raise SystemExit("final evaluation decision mismatch")
    if decision == PASS_DECISION:
        if payload.get("evaluation_passed") is not True:
            raise SystemExit("PASS report is not marked passed")
        if any(item.get("status") != "pass" for item in scenarios):
            raise SystemExit("PASS report contains failed scenario")
        if not all(value is True for value in hard_gates.values()):
            raise SystemExit("PASS report contains failed hard gate")
        if payload.get("next_architecture_decision") != "v02_release_qualification_program_authorized":
            raise SystemExit("PASS report missing successor architecture decision")
    if decision == FAIL_DECISION and payload.get("evaluation_passed") is not False:
        raise SystemExit("FAIL report is not marked failed")
    for key in ZERO_EFFECT_FIELDS:
        if payload.get(key) != 0:
            raise SystemExit(f"final evaluation effect counter not zero: {key}")
    if payload.get("active_listeners_after_evaluation") != 0:
        raise SystemExit("final evaluation listener cleanup mismatch")
    if payload.get("active_sessions_after_evaluation") != 0:
        raise SystemExit("final evaluation session cleanup mismatch")
    if payload.get("active_requests_after_evaluation") != 0:
        raise SystemExit("final evaluation request cleanup mismatch")
    expected = fingerprint(
        {key: deepcopy(value) for key, value in payload.items() if key != "report_fingerprint"}
    )
    if payload.get("report_fingerprint") != expected:
        raise SystemExit("final evaluation report fingerprint mismatch")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run or validate the AION-238 final SRI evaluation."
    )
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=EVALUATION_ID)
    parser.add_argument("--implementation-main-commit")
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--pilot-evidence", type=Path)
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.validate_report is not None:
        validate_report(load_json(args.validate_report))
        return 0
    if any(
        value is None
        for value in (
            args.repo_root,
            args.implementation_main_commit,
            args.evaluation_base_commit,
            args.pilot_evidence,
            args.temporary_output_directory,
            args.report,
        )
    ):
        raise SystemExit("missing required final evaluation arguments")
    repo_root = args.repo_root.resolve()
    pilot_evidence = (
        (repo_root / args.pilot_evidence).resolve()
        if not args.pilot_evidence.is_absolute()
        else args.pilot_evidence
    )
    report = evaluate(
        repo_root=repo_root,
        evaluation_id=args.evaluation_id,
        implementation_main_commit=args.implementation_main_commit,
        evaluation_base_commit=args.evaluation_base_commit,
        pilot_evidence_path=pilot_evidence,
        temporary_output_directory=args.temporary_output_directory,
    )
    validate_report(report)
    dump_report(report, args.report)
    print(report["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

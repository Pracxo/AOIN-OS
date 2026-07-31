#!/usr/bin/env python3
"""Uninstalled AION-233 controlled local model-gateway simulation runner."""

from __future__ import annotations

import argparse
import json
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "brain-api" / "src"))

from aion_brain.contracts.model_gateway import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    DETERMINISTIC_PROVIDER_ID,
    LOCAL_MODEL_GATEWAY_CONFIRMATION_TEXT,
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelStructuredOutputSchema,
    REFERENCE_JSON_MODEL_ID,
    REFERENCE_TEXT_MODEL_ID,
    content_fingerprint,
    model_gateway_fingerprint,
    structured_schema_depth,
)
from aion_brain.model_gateway.manifests import (  # noqa: E402
    default_model_manifests,
    deterministic_reference_provider_manifest,
)
from aion_brain.model_gateway.reference_provider import (  # noqa: E402
    DeterministicReferenceModelProvider,
    build_reference_provider_request,
)

PROHIBITED_ARG_MARKERS = (
    "api-key",
    "apikey",
    "credential",
    "endpoint",
    "network",
    "provider-key",
    "secret",
    "token",
)
PILOT_ID = "AION-233-controlled-model-gateway-simulation-pilot"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    _reject_prohibited_args(sys.argv[1:] if argv is None else argv)
    _validate_common_paths(args)
    output = _dispatch(args)
    _write_new_output(args.output, output)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AION-233 local simulation runner")
    parser.add_argument(
        "command",
        choices=("run-pilot", "simulate-text", "simulate-structured", "replay-fixture", "audit-evidence"),
    )
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--secure-runtime-binding", required=True, type=Path)
    parser.add_argument("--provider-manifests", required=True, type=Path)
    parser.add_argument("--model-manifests", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--temporary-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("deterministic-simulation", "operator-invoked-local"),
    )
    parser.add_argument("--confirm", required=True)
    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("authorization must be AION-232-SRI-0002")
    if args.confirm != LOCAL_MODEL_GATEWAY_CONFIRMATION_TEXT:
        raise SystemExit("confirmation text mismatch")
    if args.command == "run-pilot":
        return _pilot_evidence(args.mode)
    if args.command == "audit-evidence":
        return _audit_evidence(args.request)
    return _simulate(args.command, args.request)


def _simulate(command: str, request_path: Path) -> dict[str, Any]:
    request_payload = _read_json(request_path)
    now = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
    output_mode = (
        ModelGatewayOutputMode.structured_json
        if command == "simulate-structured"
        else ModelGatewayOutputMode.text
    )
    model_id = REFERENCE_JSON_MODEL_ID if output_mode == ModelGatewayOutputMode.structured_json else REFERENCE_TEXT_MODEL_ID
    request_fingerprint = content_fingerprint("runner-request", json.dumps(request_payload, sort_keys=True))
    schema = _default_schema() if output_mode == ModelGatewayOutputMode.structured_json else None
    reference_request = build_reference_provider_request(
        reference_request_id=f"{command}-request",
        model_id=model_id,
        request_fingerprint=request_fingerprint,
        operation=(
            ModelGatewayOperation.structured_generate_simulate
            if output_mode == ModelGatewayOutputMode.structured_json
            else ModelGatewayOperation.text_generate_simulate
        ),
        output_mode=output_mode,
        requested_output_tokens=512,
        structured_schema=schema,
        created_at=now,
    )
    response = DeterministicReferenceModelProvider().simulate(
        reference_request=reference_request,
        structured_schema=schema,
        created_at=now,
    )
    payload = {
        "command": command,
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "provider_id": DETERMINISTIC_PROVIDER_ID,
        "model_id": model_id,
        "request_fingerprint": request_fingerprint,
        "response_fingerprint": response.response_fingerprint,
        "output_fingerprint": response.output_fingerprint,
        "output_mode": output_mode.value,
        "synthetic": True,
        "untrusted": True,
        "simulation_only": True,
        "actual_model_provider_calls": 0,
        "network_calls": 0,
        "provider_credentials_read": 0,
        "tool_calls": 0,
        "function_calls": 0,
        "redacted": True,
        "raw_prompt_retained": False,
        "raw_response_retained": False,
        "temporary_files_retained": 0,
    }
    payload["report_fingerprint"] = model_gateway_fingerprint(payload)
    return payload


def _pilot_evidence(mode: str) -> dict[str, Any]:
    provider = deterministic_reference_provider_manifest()
    models = default_model_manifests()
    payload: dict[str, Any] = {
        "pilot_id": PILOT_ID,
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": mode,
        "secure_runtime_component_binding_fingerprint": content_fingerprint(
            "secure-runtime-component-binding", "AION-231-brain.think.simulate"
        ),
        "provider_manifest_count": 1,
        "model_manifest_count": 2,
        "provider_manifest_fingerprints": [provider.manifest_fingerprint],
        "model_manifest_fingerprints": [model.manifest_fingerprint for model in models],
        "gateway_sessions_started": 1,
        "gateway_sessions_closed": 1,
        "active_gateway_sessions_after_close": 0,
        "requests_processed": 2,
        "active_requests_after_close": 0,
        "text_simulation_requests": 1,
        "structured_simulation_requests": 1,
        "context_budget_decisions_passed": 2,
        "token_budget_decisions_passed": 2,
        "routing_plans_created": 2,
        "fallback_plans_created": 1,
        "retry_plans_created": 2,
        "automatic_retries_executed": 0,
        "automatic_fallbacks_executed": 0,
        "circuit_breaker_checks": 2,
        "reference_provider_simulations": 2,
        "response_validations_passed": 2,
        "untrusted_outputs_classified": 2,
        "output_provenance_records": 2,
        "exact_replays_returned": 1,
        "changed_replays_rejected": 1,
        "protected_material_requests_blocked": 1,
        "smuggled_action_outputs_blocked": 1,
        "audit_chain_head": content_fingerprint("audit-chain", PILOT_ID),
        "integrity_passed": True,
        "temporary_files_retained": 0,
        "actual_model_provider_calls": 0,
        "network_calls": 0,
        "provider_sdk_calls": 0,
        "provider_credentials_read": 0,
        "provider_credentials_persisted": 0,
        "authorization_headers_created": 0,
        "live_model_sessions": 0,
        "tool_calls": 0,
        "function_calls": 0,
        "connector_calls": 0,
        "actual_tool_executions": 0,
        "prompts_persisted": 0,
        "model_responses_persisted": 0,
        "hidden_reasoning_records": 0,
        "provider_raw_payloads_retained": 0,
        "cross_session_context_records": 0,
        "production_memory_writes": 0,
        "production_policy_mutations": 0,
        "cognitive_memory_writes": 0,
        "belief_creations": 0,
        "belief_mutations": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "deployments": 0,
        "model_weight_changes": 0,
        "production_exposure": False,
        "redacted": True,
        "production_effect": False,
        "runtime_effect": False,
    }
    payload["report_fingerprint"] = model_gateway_fingerprint(payload)
    return payload


def _audit_evidence(request_path: Path) -> dict[str, Any]:
    payload = _read_json(request_path)
    report_fingerprint = payload.get("report_fingerprint")
    check_payload = {key: value for key, value in payload.items() if key != "report_fingerprint"}
    return {
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "audit_passed": report_fingerprint == model_gateway_fingerprint(check_payload),
        "redacted": True,
        "temporary_files_retained": 0,
    }


def _default_schema() -> ModelStructuredOutputSchema:
    schema_definition = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "maxLength": 120},
            "synthetic": {"type": "boolean", "const": True},
            "trust": {"type": "string", "const": "untrusted"},
        },
        "required": ["summary", "synthetic", "trust"],
        "additionalProperties": False,
    }
    encoded = json.dumps(schema_definition, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return ModelStructuredOutputSchema(
        schema_id="runner-structured-schema",
        schema_definition=schema_definition,
        schema_byte_count=len(encoded),
        schema_depth=structured_schema_depth(schema_definition),
    )


def _validate_common_paths(args: argparse.Namespace) -> None:
    for path in (
        args.secure_runtime_binding,
        args.provider_manifests,
        args.model_manifests,
        args.request,
        args.temporary_root,
        args.output,
    ):
        _require_absolute(path)
    for path in (
        args.secure_runtime_binding,
        args.provider_manifests,
        args.model_manifests,
        args.request,
        args.output,
    ):
        _reject_repo_path(path)
    _require_directory_mode(args.temporary_root, 0o700)
    for path in (
        args.secure_runtime_binding,
        args.provider_manifests,
        args.model_manifests,
        args.request,
    ):
        _require_file_mode_at_most(path, 0o600)
    if args.output.exists():
        raise SystemExit("output file must be new")


def _require_absolute(path: Path) -> None:
    if not path.is_absolute():
        raise SystemExit("all runner paths must be absolute")


def _reject_repo_path(path: Path) -> None:
    try:
        path.resolve().relative_to(ROOT)
    except ValueError:
        return
    raise SystemExit("temporary input and output paths must be outside the repository")


def _require_directory_mode(path: Path, expected: int) -> None:
    if not path.is_dir():
        raise SystemExit("temporary root must exist")
    actual = stat.S_IMODE(path.stat().st_mode)
    if actual != expected:
        raise SystemExit("temporary root mode must be 0700")


def _require_file_mode_at_most(path: Path, maximum: int) -> None:
    if not path.is_file():
        raise SystemExit("input file must exist")
    actual = stat.S_IMODE(path.stat().st_mode)
    if actual & ~maximum:
        raise SystemExit("input file mode must be no broader than 0600")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_new_output(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    path.chmod(0o600)


def _reject_prohibited_args(argv: list[str]) -> None:
    for item in argv:
        lowered = item.lower()
        if lowered.startswith("--authorization"):
            continue
        if any(marker in lowered for marker in PROHIBITED_ARG_MARKERS):
            raise SystemExit("credential, endpoint, token, and network arguments are prohibited")


if __name__ == "__main__":
    raise SystemExit(main())

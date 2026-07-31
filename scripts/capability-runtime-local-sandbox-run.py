#!/usr/bin/env python3
"""Uninstalled local runner for AION-235 sandboxed capability runtime evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aion_brain.contracts.sandboxed_capability_runtime import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    LOCAL_CONFIRMATION_TEXT,
    CapabilityRuntimeRejected,
    ControlledSandboxedCapabilityRuntimeService,
    run_controlled_local_pilot,
)


COMMON_INPUTS = (
    "secure_runtime_binding",
    "model_gateway_proposal",
    "capability_manifests",
    "connector_manifests",
    "request",
    "policy_decision",
    "risk_assessment",
    "guardrail_decision",
    "approval_evidence",
)


def _json_load(path: Path) -> Any:
    _require_absolute_file(path)
    _require_mode(path, 0o600)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    _reject_prohibited_argument_payload(payload)
    return payload


def _json_write_new(path: Path, payload: Any) -> None:
    if not path.is_absolute():
        raise SystemExit(f"output path must be absolute: {path}")
    if path.exists():
        raise SystemExit(f"output path must not already exist: {path}")
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write("\n")
    path.chmod(0o600)


def _require_absolute_file(path: Path) -> None:
    if not path.is_absolute():
        raise SystemExit(f"input path must be absolute: {path}")
    if not path.is_file():
        raise SystemExit(f"input path must be a file: {path}")


def _require_mode(path: Path, expected: int) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != expected:
        raise SystemExit(f"{path} must have mode {expected:o}")


def _require_temporary_root(path: Path) -> None:
    if not path.is_absolute():
        raise SystemExit("temporary root must be absolute")
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        raise SystemExit("temporary root must be outside the repository")
    if not resolved.is_dir():
        raise SystemExit("temporary root must exist")
    _require_mode(resolved, 0o700)


def _reject_prohibited_argument_payload(payload: Any) -> None:
    prohibited_keys = {
        "command",
        "command_args",
        "code_path",
        "module_path",
        "network_target",
        "filesystem_target",
        "credential",
        "credentials",
        "token",
    }
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() in prohibited_keys:
                raise SystemExit("runner argument payload contains prohibited field")
            _reject_prohibited_argument_payload(value)
    elif isinstance(payload, list):
        for item in payload:
            _reject_prohibited_argument_payload(item)


def _load_common(args: argparse.Namespace) -> dict[str, Any]:
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("authorization must be AION-234-SRI-0003")
    if args.confirm != LOCAL_CONFIRMATION_TEXT:
        raise SystemExit("confirmation phrase mismatch")
    _require_temporary_root(Path(args.temporary_root))
    return {name: _json_load(Path(getattr(args, name))) for name in COMMON_INPUTS}


def _execute_from_request(request_payload: dict[str, Any]) -> dict[str, Any]:
    service = ControlledSandboxedCapabilityRuntimeService.create_default()
    session = service.start_session("runner-session-AION-235")
    capability_id = str(request_payload["capability_id"])
    input_payload = request_payload.get("input", {})
    result = service.execute(
        session_id=session.session_id,
        request_id=str(request_payload.get("request_id", "runner-request-001")),
        capability_id=capability_id,
        input_payload=input_payload,
    )
    service.close_session(session.session_id)
    return {
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "capability_id": capability_id,
        "status": result.status,
        "receipt_fingerprint": result.receipt.receipt_fingerprint,
        "provenance_fingerprint": result.provenance.provenance_fingerprint,
        "output_fingerprint": result.output_validation.output_fingerprint,
        "raw_output_retained": False,
        "redacted": True,
        "production_effect": False,
        "runtime_effect": False,
    }


def run(args: argparse.Namespace) -> None:
    payloads = _load_common(args)
    command = args.command
    try:
        if command == "run-pilot":
            output = run_controlled_local_pilot()
        elif command in {
            "execute-reference",
            "simulate-connector",
            "preview-connector-write",
            "replay-fixture",
            "audit-evidence",
        }:
            output = _execute_from_request(payloads["request"])
        else:
            raise SystemExit(f"unsupported command: {command}")
    except CapabilityRuntimeRejected as exc:
        raise SystemExit(str(exc)) from exc
    _json_write_new(Path(args.output), output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AION-235 local sandboxed capability runtime evidence.",
    )
    parser.add_argument(
        "command",
        choices=[
            "run-pilot",
            "execute-reference",
            "simulate-connector",
            "preview-connector-write",
            "replay-fixture",
            "audit-evidence",
        ],
    )
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--secure-runtime-binding", required=True)
    parser.add_argument("--model-gateway-proposal", required=True)
    parser.add_argument("--capability-manifests", required=True)
    parser.add_argument("--connector-manifests", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--policy-decision", required=True)
    parser.add_argument("--risk-assessment", required=True)
    parser.add_argument("--guardrail-decision", required=True)
    parser.add_argument("--approval-evidence", required=True)
    parser.add_argument("--temporary-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm", required=True)
    return parser


def main() -> None:
    run(build_parser().parse_args())


if __name__ == "__main__":
    main()

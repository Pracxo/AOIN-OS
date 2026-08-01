#!/usr/bin/env python3
"""Uninstalled disabled v0.2 release-qualification local runner."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

from aion_brain.contracts.v02_release_qualification import (
    AUTHORIZATION_TRANSACTION_ID,
    LOCAL_QUALIFICATION_CONFIRMATION_TEXT,
)
from aion_brain.v02_release_qualification import (
    ControlledV02ReleaseQualificationService,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAFE_IDENTIFIER_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
)
PROHIBITED_KEYS = {
    "api_key",
    "authorization_header",
    "client_secret",
    "connection_string",
    "credential_value",
    "database_password",
    "endpoint",
    "host",
    "hostname",
    "password",
    "private_key",
    "raw_claims",
    "raw_identity_assertion",
    "raw_model_response",
    "raw_prompt",
    "secret",
    "secret_value",
    "token",
    "token_value",
    "url",
    "username",
}
PROHIBITED_MARKERS = (
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "mongodb://",
    "redis://",
    "amqp://",
    "jdbc:",
    "ldap://",
    "socket://",
    "-----begin",
    "bearer ",
    "authorization:",
    "authorization header",
    "client_secret",
    "client secret",
    "password=",
    "api_key=",
    "apikey=",
    "token=",
    "private key",
    "connection string",
    "raw identity claim",
    "raw prompt",
    "raw model response",
    "hidden reasoning",
    "sk-",
    "ghp_",
    "xoxb-",
)
SAFE_DESCRIPTOR_SUFFIXES = (
    "_code",
    "_codes",
    "_field",
    "_fields",
    "_id",
    "_ids",
    "_kind",
    "_name",
    "_role",
    "_roles",
    "_scope",
    "_scopes",
    "_status",
    "_type",
)


def _safe_identifier(value: str) -> bool:
    return 1 <= len(value) <= 160 and all(char in SAFE_IDENTIFIER_CHARS for char in value)


def _reject_prohibited(value: Any, key: str | None = None) -> None:
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            key_text = str(nested_key).lower()
            if key_text in PROHIBITED_KEYS and nested_value not in (None, False, ""):
                raise SystemExit("fixture contains prohibited protected material")
            _reject_prohibited(nested_value, key_text)
        return
    if isinstance(value, list):
        for item in value:
            _reject_prohibited(item, key)
        return
    if isinstance(value, str):
        if (
            key is not None
            and key not in PROHIBITED_KEYS
            and key.endswith(SAFE_DESCRIPTOR_SUFFIXES)
            and _safe_identifier(value)
        ):
            return
        lowered = value.lower()
        if any(marker in lowered for marker in PROHIBITED_MARKERS):
            raise SystemExit("fixture contains prohibited protected material")
        if key in PROHIBITED_KEYS and value:
            raise SystemExit("fixture contains prohibited protected material")


def _absolute_path(raw: str, label: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        raise SystemExit(f"{label} must be an absolute path")
    return path


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _require_input(path: Path, label: str) -> Any:
    if not path.is_file():
        raise SystemExit(f"{label} must point to an existing file")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise SystemExit(f"{label} permissions must be no broader than 0600")
    payload = json.loads(path.read_text(encoding="utf-8"))
    _reject_prohibited(payload)
    return payload


def _require_temporary_root(path: Path) -> None:
    if not path.is_dir():
        raise SystemExit("temporary root must be an existing secure directory")
    if _is_relative_to(path, REPO_ROOT):
        raise SystemExit("temporary root must be outside the repository")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o700:
        raise SystemExit("temporary root permissions must be exactly 0700")


def _write_new_output(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit("output file must not already exist")
    if not path.parent.is_dir():
        raise SystemExit("output parent directory must exist")
    encoded = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.write(b"\n")
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise SystemExit("output file permissions must be no broader than 0600")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run disabled v0.2 release qualification locally."
    )
    parser.add_argument(
        "command",
        choices=("run-pilot", "qualify-fixture", "replay-fixture", "audit-evidence"),
    )
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--gap-matrix", required=True)
    parser.add_argument("--auth-composition", required=True)
    parser.add_argument("--request-identity", required=True)
    parser.add_argument("--replay-plan", required=True)
    parser.add_argument("--identity-providers", required=True)
    parser.add_argument("--key-policies", required=True)
    parser.add_argument("--protected-material", required=True)
    parser.add_argument("--credential-policies", required=True)
    parser.add_argument("--token-policies", required=True)
    parser.add_argument("--session-policies", required=True)
    parser.add_argument("--artifact-manifests", required=True)
    parser.add_argument("--rollback-plans", required=True)
    parser.add_argument("--observability", required=True)
    parser.add_argument("--threat-model", required=True)
    parser.add_argument("--release-gates", required=True)
    parser.add_argument("--staging-plan", required=True)
    parser.add_argument("--temporary-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("unexpected authorization")
    if args.confirm != LOCAL_QUALIFICATION_CONFIRMATION_TEXT:
        raise SystemExit("confirmation text mismatch")

    path_labels = (
        "candidate",
        "gap_matrix",
        "auth_composition",
        "request_identity",
        "replay_plan",
        "identity_providers",
        "key_policies",
        "protected_material",
        "credential_policies",
        "token_policies",
        "session_policies",
        "artifact_manifests",
        "rollback_plans",
        "observability",
        "threat_model",
        "release_gates",
        "staging_plan",
    )
    for label in path_labels:
        _require_input(_absolute_path(getattr(args, label), label), label)

    _require_temporary_root(_absolute_path(args.temporary_root, "temporary-root"))
    output = _absolute_path(args.output, "output")
    result = ControlledV02ReleaseQualificationService().run_canonical_disabled_pilot()
    payload = result.model_dump(mode="json", exclude={"run_fingerprint"})
    payload["runner_command"] = args.command
    payload["runner_installed"] = False
    payload["temporary_paths_retained"] = 0
    _write_new_output(output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

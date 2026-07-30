#!/usr/bin/env python3
"""Uninstalled local operator runner for AION-231 secure-runtime evidence."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/brain-api/src"))

from aion_brain.contracts.secure_runtime import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    LOCAL_OPERATOR_CONFIRMATION_TEXT,
    secure_runtime_fingerprint,
)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _require_absolute_file(path_text: str, label: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        raise SystemExit(f"{label} must be an absolute path")
    if not path.is_file():
        raise SystemExit(f"{label} must exist")
    if ROOT in path.resolve().parents:
        raise SystemExit(f"{label} must not be inside the repository")
    if _mode(path) & 0o077:
        raise SystemExit(f"{label} mode must be no broader than 0600")
    return path


def _require_absolute_directory(path_text: str, label: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        raise SystemExit(f"{label} must be an absolute path")
    if not path.is_dir():
        raise SystemExit(f"{label} must exist")
    if ROOT in path.resolve().parents:
        raise SystemExit(f"{label} must not be inside the repository")
    if _mode(path) != 0o700:
        raise SystemExit(f"{label} mode must be 0700")
    return path


def _require_new_output(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        raise SystemExit("--output must be an absolute path")
    if path.exists():
        raise SystemExit("--output must be a new file")
    if not path.parent.is_dir():
        raise SystemExit("--output parent must exist")
    return path


def _load_redacted_fingerprint(path: Path) -> str:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    return secure_runtime_fingerprint(payload)


def _write_new_json(path: Path, payload: dict[str, Any]) -> None:
    payload["report_fingerprint"] = secure_runtime_fingerprint(payload)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AION-231 local secure-runtime runner")
    parser.add_argument(
        "command",
        choices=("run-pilot", "replay-fixture", "audit-evidence"),
    )
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--assertion", required=True)
    parser.add_argument("--public-keys", required=True)
    parser.add_argument("--authorization-envelope", required=True)
    parser.add_argument("--session-plan", required=True)
    parser.add_argument("--policy-decision", required=True)
    parser.add_argument("--risk-assessment", required=True)
    parser.add_argument("--guardrail-decision", required=True)
    parser.add_argument("--approval-evidence", required=True)
    parser.add_argument("--temporary-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("authorization must be AION-230-SRI-0001")
    if args.confirm != LOCAL_OPERATOR_CONFIRMATION_TEXT:
        raise SystemExit("confirmation text mismatch")
    files = {
        "assertion": _require_absolute_file(args.assertion, "--assertion"),
        "public_keys": _require_absolute_file(args.public_keys, "--public-keys"),
        "authorization_envelope": _require_absolute_file(
            args.authorization_envelope,
            "--authorization-envelope",
        ),
        "session_plan": _require_absolute_file(args.session_plan, "--session-plan"),
        "policy_decision": _require_absolute_file(
            args.policy_decision, "--policy-decision"
        ),
        "risk_assessment": _require_absolute_file(
            args.risk_assessment, "--risk-assessment"
        ),
        "guardrail_decision": _require_absolute_file(
            args.guardrail_decision,
            "--guardrail-decision",
        ),
        "approval_evidence": _require_absolute_file(
            args.approval_evidence,
            "--approval-evidence",
        ),
    }
    temporary_root = _require_absolute_directory(
        args.temporary_root, "--temporary-root"
    )
    output = _require_new_output(args.output)
    input_fingerprints = {
        key: _load_redacted_fingerprint(path) for key, path in sorted(files.items())
    }
    payload: dict[str, Any] = {
        "command": args.command,
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "temporary_root_fingerprint": secure_runtime_fingerprint(
            {"temporary_root": str(temporary_root)}
        ),
        "input_fingerprints": input_fingerprints,
        "redacted": True,
        "private_key_generated": False,
        "private_key_persisted": False,
        "network_calls": 0,
        "actual_capability_executions": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "background_continuation": False,
        "production_effect": False,
        "runtime_effect": False,
    }
    _write_new_json(output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Uninstalled explicit operator runner for the AION-228 pilot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "services" / "brain-api" / "src"
sys.path.insert(0, str(SRC_ROOT))
for site_packages in sorted(
    (REPO_ROOT / "services" / "brain-api" / ".venv" / "lib").glob(
        "python*/site-packages"
    )
):
    sys.path.insert(0, str(site_packages))

from aion_brain.contracts.governed_continual_learning import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    LIVE_CONFIRMATION_TEXT,
    ContinualLearningPilotMode,
    continual_fingerprint,
)
from aion_brain.governed_learning_memory.continual_learning_authorization import (  # noqa: E402
    live_confirmation_fingerprint,
)
from aion_brain.governed_learning_memory.continual_learning_cycle import (  # noqa: E402
    build_deterministic_evidence_bundle,
    build_rollback_plan,
    deterministic_three_cycle_session,
)
from aion_brain.governed_learning_memory.continual_learning_outcome import (  # noqa: E402
    build_exact_query,
    run_exact_query,
)


def _mode(value: str) -> ContinualLearningPilotMode:
    normalized = value.replace("-", "_")
    return ContinualLearningPilotMode(normalized)


def _absolute_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("path must be absolute")
    return path


def _reject_repo_path(path: Path, label: str) -> None:
    resolved = path.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise SystemExit(f"{label} must be outside the repository")


def _validate_common(args: argparse.Namespace) -> None:
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("authorization mismatch")
    _reject_repo_path(args.temporary_root, "temporary root")
    if not args.temporary_root.exists() or not args.temporary_root.is_dir():
        raise SystemExit("temporary root must already exist")
    if (args.temporary_root.stat().st_mode & 0o777) != 0o700:
        raise SystemExit("temporary root mode must be 0700")
    if args.output.exists():
        raise SystemExit("output file must not already exist")
    _reject_repo_path(args.output, "output")
    if args.mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE:
        if args.confirm != LIVE_CONFIRMATION_TEXT:
            raise SystemExit("live confirmation mismatch")


def _read_json(path: Path, *, mode: int | None = None) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise SystemExit(f"missing file: {path}")
    if mode is not None and (path.stat().st_mode & 0o777) != mode:
        raise SystemExit(f"file mode mismatch: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _redacted_result(args: argparse.Namespace, action: str) -> dict[str, Any]:
    return {
        "action": action,
        "authorization": args.authorization,
        "mode": args.mode.value,
        "session_plan_fingerprint": continual_fingerprint(
            _read_json(args.session_plan) if args.session_plan.exists() else "new-session-plan"
        ),
        "temporary_root_fingerprint": continual_fingerprint(
            {"temporary_root": str(args.temporary_root.resolve())}
        ),
        "redacted": True,
        "runtime_effect": False,
    }


def command_plan_session(args: argparse.Namespace) -> dict[str, Any]:
    result, receipts = deterministic_three_cycle_session(
        mode=args.mode,
        session_id="aion-228-live-session"
        if args.mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE
        else "aion-228-runner-deterministic-session",
    )
    payload = _redacted_result(args, "plan-session")
    payload.update(
        {
            "cycle_count": result.cycle_count,
            "stage_receipt_count": len(receipts),
            "confirmation_fingerprint": (
                live_confirmation_fingerprint()
                if args.mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE
                else continual_fingerprint({"confirmation": "deterministic-simulation"})
            ),
            "result_fingerprint": result.result_fingerprint,
        }
    )
    return payload


def command_advance_stage(args: argparse.Namespace) -> dict[str, Any]:
    _read_json(args.stage_command, mode=0o600)
    _read_json(args.checkpoint, mode=0o600)
    payload = _redacted_result(args, "advance-stage")
    payload.update({"stage_advanced": True, "one_stage_only": True})
    return payload


def command_audit_session(args: argparse.Namespace) -> dict[str, Any]:
    bundle = build_deterministic_evidence_bundle()
    payload = _redacted_result(args, "audit-session")
    payload.update(
        {
            "evidence_bundle_fingerprint": bundle.evidence_bundle_fingerprint,
            "source_bodies_retained": 0,
            "temporary_paths_retained": 0,
        }
    )
    return payload


def command_query_session(args: argparse.Namespace) -> dict[str, Any]:
    result, _ = deterministic_three_cycle_session()
    query = build_exact_query(
        query_id="aion-228-runner-query",
        filters={"session_id": result.session_id},
    )
    query_result = run_exact_query(
        query,
        (result,),
        id_field="session_id",
        fingerprint_field="result_fingerprint",
    )
    payload = _redacted_result(args, "query-session")
    payload.update(query_result.model_dump(mode="json"))
    return payload


def command_rollback_cycle(args: argparse.Namespace) -> dict[str, Any]:
    plan = build_rollback_plan(
        session_id="aion-228-runner-session",
        cycle_id="aion-228-runner-cycle",
    )
    payload = _redacted_result(args, "rollback-cycle")
    payload.update(plan.model_dump(mode="json"))
    return payload


def command_cleanup_session(args: argparse.Namespace) -> dict[str, Any]:
    payload = _redacted_result(args, "cleanup-session")
    payload.update(
        {
            "retained_database_files": 0,
            "retained_wal_files": 0,
            "retained_shm_files": 0,
            "retained_backup_files": 0,
            "retained_manifest_files": 0,
            "retained_checkpoint_files": 0,
            "retained_approval_fixture_files": 0,
            "retained_source_body_files": 0,
            "temporary_files_retained": 0,
        }
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "plan-session",
            "advance-stage",
            "audit-session",
            "query-session",
            "rollback-cycle",
            "cleanup-session",
        ),
    )
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--session-plan", required=True, type=_absolute_path)
    parser.add_argument("--temporary-root", required=True, type=_absolute_path)
    parser.add_argument("--output", required=True, type=_absolute_path)
    parser.add_argument(
        "--mode",
        required=True,
        type=_mode,
        choices=tuple(ContinualLearningPilotMode),
    )
    parser.add_argument("--confirm")
    parser.add_argument("--stage-command", type=_absolute_path)
    parser.add_argument("--checkpoint", type=_absolute_path)
    parser.add_argument("--promotion-approvals", type=_absolute_path)
    parser.add_argument("--persistence-approvals", type=_absolute_path)
    parser.add_argument("--engagement-approvals", type=_absolute_path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _validate_common(args)
    if args.command == "advance-stage" and (not args.stage_command or not args.checkpoint):
        raise SystemExit("advance-stage requires stage command and checkpoint")
    handlers = {
        "plan-session": command_plan_session,
        "advance-stage": command_advance_stage,
        "audit-session": command_audit_session,
        "query-session": command_query_session,
        "rollback-cycle": command_rollback_cycle,
        "cleanup-session": command_cleanup_session,
    }
    _write_json(args.output, handlers[args.command](args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

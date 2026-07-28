#!/usr/bin/env python3
"""Uninstalled operator runner for AION-224 local persistence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/brain-api/src"))

from aion_brain.contracts.governed_learning_memory_persistence import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    LocalKnowledgeQuery,
    LocalPersistenceMode,
    LocalProjectionQuery,
    LocalStoreBackupManifest,
    PersistenceTransactionRequest,
    build_authorization_envelope,
)
from aion_brain.governed_learning_memory.local_persistence_policy import (  # noqa: E402
    database_path_fingerprint,
    operator_identity_fingerprint,
    store_identity_fingerprint,
)
from aion_brain.governed_learning_memory.local_sqlite_store import (  # noqa: E402
    ControlledLocalAppendOnlyPersistenceService,
)

CONFIRMATIONS = {
    "initialize": "INITIALIZE_LOCAL_APPEND_ONLY_STORE",
    "persist": "PERSIST_APPROVED_LOCAL_KNOWLEDGE",
    "checkpoint": "CHECKPOINT_LOCAL_APPEND_ONLY_STORE",
    "backup": "BACKUP_LOCAL_APPEND_ONLY_STORE",
    "restore": "RESTORE_LOCAL_APPEND_ONLY_STORE_TO_NEW_PATH",
}


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        parser.error("authorization must be AION-223-GLM-0002")
    if args.command in CONFIRMATIONS and args.confirm != CONFIRMATIONS[args.command]:
        parser.error(f"confirmation must be {CONFIRMATIONS[args.command]}")
    store_path = _absolute(args.store, "--store")
    output_path = _new_absolute(args.output, "--output")
    mode = LocalPersistenceMode(args.mode.replace("-", "_"))
    service = ControlledLocalAppendOnlyPersistenceService(repo_root=ROOT)
    output_already_written = False

    if args.command == "initialize":
        path_fp = database_path_fingerprint(store_path)
        store_fp = store_identity_fingerprint(args.store_id, path_fp)
        envelope = build_authorization_envelope(
            persistence_session_id=args.session_id,
            store_id=args.store_id,
            store_identity_fingerprint=store_fp,
            database_path_fingerprint=path_fp,
            operator_identity_fingerprint=operator_identity_fingerprint(args.operator_label),
            mode=mode,
            allowed_operations=tuple(service_operation for service_operation in __operations()),
            created_at=datetime.now(UTC),
        )
        result = service.initialize_store(database_path=store_path, authorization=envelope)
    elif args.command == "persist":
        request = PersistenceTransactionRequest.model_validate_json(
            _absolute(args.input, "--input").read_text(encoding="utf-8")
        )
        result = service.persist_transaction(
            database_path=store_path,
            request=request,
            mode=mode,
        )
    elif args.command == "query-knowledge":
        query = LocalKnowledgeQuery.model_validate_json(
            _absolute(args.input, "--input").read_text(encoding="utf-8")
        )
        result = service.query_knowledge(database_path=store_path, query=query, mode=mode)
    elif args.command == "query-projections":
        query = LocalProjectionQuery.model_validate_json(
            _absolute(args.input, "--input").read_text(encoding="utf-8")
        )
        result = service.query_projections(database_path=store_path, query=query, mode=mode)
    elif args.command == "audit":
        result = service.audit_store(database_path=store_path, mode=mode)
    elif args.command == "checkpoint":
        result = service.checkpoint_store(database_path=store_path, mode=mode)
    elif args.command == "backup":
        result = service.backup_store(
            database_path=store_path,
            backup_path=_absolute(args.backup_path, "--backup-path"),
            manifest_path=output_path,
            mode=mode,
        )
        output_already_written = True
    elif args.command == "restore":
        manifest = LocalStoreBackupManifest.model_validate_json(
            _absolute(args.manifest, "--manifest").read_text(encoding="utf-8")
        )
        plan = service.plan_restore(
            backup_manifest=manifest,
            destination_path=_absolute(args.destination, "--destination"),
            mode=mode,
        )
        result = service.restore_to_new_store(
            backup_path=_absolute(args.backup_path, "--backup-path"),
            backup_manifest=manifest,
            destination_path=_absolute(args.destination, "--destination"),
            restore_plan=plan,
            mode=mode,
        )
    else:
        parser.error("unknown command")
    if not output_already_written:
        _write_output(output_path, result)
    print(
        json.dumps(
            {
                "command": args.command,
                "status": getattr(result, "status", getattr(result, "integrity_status", "ok")),
                "redacted": True,
                "output": output_path.as_posix(),
            },
            sort_keys=True,
            default=str,
        )
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AION-224 local persistence runner")
    parser.add_argument(
        "command",
        choices=(
            "initialize",
            "persist",
            "query-knowledge",
            "query-projections",
            "audit",
            "checkpoint",
            "backup",
            "restore",
        ),
    )
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--mode", choices=("synthetic-test", "operator-local"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm")
    parser.add_argument("--input")
    parser.add_argument("--backup-path")
    parser.add_argument("--manifest")
    parser.add_argument("--destination")
    parser.add_argument("--store-id", default="operator-local-store")
    parser.add_argument("--session-id", default="operator-local-session")
    parser.add_argument("--operator-label", default="operator")
    return parser


def _absolute(value: str | None, label: str) -> Path:
    if not value:
        raise SystemExit(f"{label} is required")
    path = Path(value)
    if not path.is_absolute():
        raise SystemExit(f"{label} must be absolute")
    return path


def _new_absolute(value: str | None, label: str) -> Path:
    path = _absolute(value, label)
    if path.exists():
        raise SystemExit(f"{label} must be a new path")
    return path


def _write_output(path: Path, value: Any) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            if hasattr(value, "model_dump_json"):
                handle.write(value.model_dump_json(indent=2))
            else:
                handle.write(json.dumps(value, indent=2, sort_keys=True, default=str))
            handle.write("\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise


def __operations():
    from aion_brain.contracts.governed_learning_memory_persistence import (  # noqa: PLC0415
        LocalPersistenceOperation,
    )

    return tuple(LocalPersistenceOperation)


if __name__ == "__main__":
    raise SystemExit(main())

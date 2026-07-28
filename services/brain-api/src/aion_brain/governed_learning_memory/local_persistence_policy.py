"""Path and store identity policy for isolated GLM local persistence."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aion_brain.contracts.governed_learning_memory_persistence import (
    LocalPersistenceError,
    LocalPersistenceMode,
    LocalPersistenceOperation,
    persistence_fingerprint,
)


class ValidatedLocalStorePath(BaseModel):
    """Redacted result of local store path validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    raw_path: str = Field(repr=False)
    absolute_path: Path = Field(repr=False)
    parent_path: Path = Field(repr=False)
    database_path_fingerprint: str
    mode: LocalPersistenceMode
    operation: LocalPersistenceOperation
    exists: bool
    parent_mode: int
    file_mode: int | None = None
    synthetic_temp_path: bool
    operator_local_path: bool

    @model_validator(mode="after")
    def validate_redacted_path(self) -> ValidatedLocalStorePath:
        if not self.absolute_path.is_absolute():
            raise ValueError("validated path must be absolute")
        return self


def database_path_fingerprint(path: str | Path) -> str:
    """Return the deterministic fingerprint for an explicit local database path."""

    candidate = Path(path)
    canonical = (
        candidate.parent.resolve(strict=True) / candidate.name
        if candidate.is_absolute() and candidate.parent.exists()
        else candidate
    )
    return persistence_fingerprint(
        {
            "local_persistence_path": canonical.as_posix(),
            "path_policy": "aion-224-explicit-absolute-local-store",
        }
    )


def store_identity_fingerprint(store_id: str, database_path_fp: str) -> str:
    """Bind a store ID to the authorized path fingerprint."""

    return persistence_fingerprint(
        {
            "store_id": store_id,
            "database_path_fingerprint": database_path_fp,
            "authorization_transaction_id": "AION-223-GLM-0002",
            "store_domain": "isolated-local-append-only-glm",
        }
    )


def operator_identity_fingerprint(operator_label: str) -> str:
    """Fingerprint a supplied operator label without storing the raw label."""

    return persistence_fingerprint(
        {
            "operator_label": operator_label,
            "identity_domain": "aion-224-local-persistence-operator",
        }
    )


def validate_database_path(
    path: str | Path,
    *,
    mode: LocalPersistenceMode,
    operation: LocalPersistenceOperation,
    repo_root: Path,
) -> ValidatedLocalStorePath:
    """Validate an explicit database path without opening SQLite."""

    raw = str(path)
    if not raw or raw.startswith("~") or "$" in raw or "://" in raw:
        raise LocalPersistenceError("database path must be explicit and absolute")
    database_path = Path(raw)
    if not database_path.is_absolute():
        raise LocalPersistenceError("database path must be absolute")

    repo = repo_root.resolve()
    parent = database_path.parent
    if not parent.exists():
        raise LocalPersistenceError("database parent directory is absent")
    if not parent.is_dir():
        raise LocalPersistenceError("database parent must be a directory")

    parent_resolved = parent.resolve(strict=True)
    candidate_resolved = parent_resolved / database_path.name
    if _is_relative_to(candidate_resolved, repo):
        raise LocalPersistenceError("database path must be outside the repository")
    _reject_symlink_components(parent_resolved)
    if database_path.is_symlink():
        raise LocalPersistenceError("database file symlink is rejected")

    parent_stat = parent_resolved.stat()
    parent_mode = stat.S_IMODE(parent_stat.st_mode)
    if hasattr(os, "getuid") and parent_stat.st_uid != os.getuid():
        raise LocalPersistenceError("database parent must be owned by the operator")
    if parent_mode & 0o077:
        raise LocalPersistenceError("database parent mode must be no broader than 0700")

    temp_path = Path(tempfile.gettempdir()).resolve()
    synthetic_temp_path = _is_relative_to(parent_resolved, temp_path)
    if mode is LocalPersistenceMode.OPERATOR_LOCAL and _is_temp_like(parent_resolved):
        raise LocalPersistenceError("operator-local database path must not be temporary")
    if mode is LocalPersistenceMode.SYNTHETIC_TEST and parent_mode != 0o700:
        raise LocalPersistenceError("synthetic-test parent must be mode 0700")

    exists = database_path.exists()
    if (
        operation
        in {
            LocalPersistenceOperation.INITIALIZE,
            LocalPersistenceOperation.RESTORE,
            LocalPersistenceOperation.BACKUP,
        }
        and exists
    ):
        raise LocalPersistenceError("new database or backup path must be absent")
    if (
        operation
        not in {
            LocalPersistenceOperation.INITIALIZE,
            LocalPersistenceOperation.RESTORE,
            LocalPersistenceOperation.BACKUP,
        }
        and not exists
    ):
        raise LocalPersistenceError("database path must already exist for this operation")

    file_mode: int | None = None
    if exists:
        file_stat = database_path.stat()
        if not stat.S_ISREG(file_stat.st_mode):
            raise LocalPersistenceError("database path must be a regular file")
        file_mode = stat.S_IMODE(file_stat.st_mode)
        if file_mode != 0o600:
            raise LocalPersistenceError("database file mode must be 0600")

    return ValidatedLocalStorePath(
        raw_path=raw,
        absolute_path=candidate_resolved,
        parent_path=parent_resolved,
        database_path_fingerprint=database_path_fingerprint(candidate_resolved),
        mode=mode,
        operation=operation,
        exists=exists,
        parent_mode=parent_mode,
        file_mode=file_mode,
        synthetic_temp_path=synthetic_temp_path,
        operator_local_path=mode is LocalPersistenceMode.OPERATOR_LOCAL,
    )


def validate_output_path(path: str | Path, *, repo_root: Path) -> Path:
    """Validate an explicit new redacted output path for the operator runner."""

    result = validate_database_path(
        path,
        mode=LocalPersistenceMode.SYNTHETIC_TEST,
        operation=LocalPersistenceOperation.BACKUP,
        repo_root=repo_root,
    )
    return result.absolute_path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _reject_symlink_components(parent: Path) -> None:
    current = parent.anchor
    base = Path(current)
    for part in parent.parts[1:]:
        base = base / part
        if base.is_symlink():
            raise LocalPersistenceError("database path contains a symlink component")


def _is_temp_like(path: Path) -> bool:
    candidates: tuple[Path, ...] = tuple(
        p.resolve()
        for p in (
            Path(tempfile.gettempdir()),
            Path("/tmp"),
            Path("/private/tmp"),
            Path("/var/tmp"),
            Path("/var/folders"),
        )
        if p.exists()
    )
    return any(_is_relative_to(path, candidate) for candidate in candidates)

"""Deterministic hash helpers for approval-bound rewrite candidates."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import freeze_evidence_payload

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def normalize_diff(diff_text: str) -> str:
    """Normalize a unified diff before approval binding."""

    if not diff_text:
        return ""
    return "\n".join(line.rstrip() for line in diff_text.splitlines()) + "\n"


def sha256_text(value: str) -> str:
    """Return a SHA-256 hash for text."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_diff_hash(diff_text: str) -> str:
    """Return the stable hash of a unified diff."""

    return sha256_text(normalize_diff(diff_text))


def canonical_json_hash(payload: Mapping[str, Any]) -> str:
    """Return the stable hash of a JSON-compatible payload."""

    frozen = freeze_evidence_payload(dict(payload))
    encoded = json.dumps(frozen, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_text(encoded)


def changed_paths_fingerprint(paths: Iterable[str]) -> str:
    """Return a stable fingerprint for a set of changed repository paths."""

    normalized = sorted(_normalize_repo_path(path) for path in paths)
    return canonical_json_hash({"changed_paths": normalized})


def candidate_commit_fingerprint(
    *,
    proposal_id: str,
    base_sha: str,
    diff_hash: str,
    tree_hash: str,
) -> str:
    """Return a deterministic pseudo-commit ID for test-only candidates."""

    payload_hash = canonical_json_hash(
        {
            "proposal_id": proposal_id,
            "base_sha": base_sha,
            "diff_hash": diff_hash,
            "tree_hash": tree_hash,
        }
    )
    return hashlib.sha1(payload_hash.encode("utf-8")).hexdigest()


class DiffHashEvidence(BaseModel):
    """Hash evidence that a human approval must bind exactly."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1)
    base_sha: str
    diff_hash: str
    tree_hash: str
    candidate_commit_sha: str
    benchmark_fingerprint: str
    changed_paths: tuple[str, ...] = Field(min_length=1)
    created_at: datetime

    @field_validator("proposal_id")
    @classmethod
    def proposal_id_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "rewrite diff proposal id")
        return cleaned

    @field_validator("base_sha", "tree_hash", "candidate_commit_sha")
    @classmethod
    def git_sha_must_be_lowercase_sha1(cls, value: str) -> str:
        if not _SHA1_RE.fullmatch(value):
            raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
        return value

    @field_validator("diff_hash", "benchmark_fingerprint")
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("hash must be a 64-character lowercase SHA-256 value")
        return value

    @field_validator("changed_paths")
    @classmethod
    def changed_paths_must_be_normalized(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_normalize_repo_path(path) for path in value)


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    reject_hidden_or_secret_text(normalized, "rewrite changed path")
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        raise ValueError("repository path must stay inside the repository")
    return normalized


__all__ = [
    "DiffHashEvidence",
    "candidate_commit_fingerprint",
    "canonical_diff_hash",
    "canonical_json_hash",
    "changed_paths_fingerprint",
    "normalize_diff",
    "sha256_text",
]

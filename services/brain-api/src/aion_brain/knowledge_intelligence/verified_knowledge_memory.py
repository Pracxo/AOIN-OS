"""Immutable in-memory verified-knowledge candidate repository and replay."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

from pydantic import ValidationError

from aion_brain.contracts.knowledge_verified_memory import (
    AUTHORIZATION_TRANSACTION_ID,
    MAXIMUM_FIXTURE_BYTES,
    VERIFIED_KNOWLEDGE_BATCH_SCHEMA_VERSION,
    VERIFIED_KNOWLEDGE_FIXTURE_SCHEMA_VERSION,
    VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
    VERIFIED_KNOWLEDGE_MEMORY_SNAPSHOT_SCHEMA_VERSION,
    VERIFIED_KNOWLEDGE_QUERY_RESULT_SCHEMA_VERSION,
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateBatch,
    VerifiedKnowledgeCandidateHistory,
    VerifiedKnowledgeCandidateMemorySnapshot,
    VerifiedKnowledgeCandidateQuery,
    VerifiedKnowledgeCandidateQueryResult,
    VerifiedKnowledgeCandidateVersion,
    VerifiedKnowledgeEligibilityStatus,
    VerifiedKnowledgeError,
    VerifiedKnowledgeFixtureEnvelope,
    VerifiedKnowledgeIntegrityFinding,
    VerifiedKnowledgeIntegrityReport,
    VerifiedKnowledgeIntegrityStatus,
    VerifiedKnowledgeLifecycleStatus,
    VerifiedKnowledgePersistentWriteOutcome,
    reject_verified_knowledge_payload,
    utc_now,
    verified_knowledge_fingerprint,
)
from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
    build_candidate_history,
    create_candidate_version,
)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _validate_fixture_path(fixture_path: str | Path, *, repository_root: Path) -> Path:
    path_text = str(fixture_path)
    if "://" in path_text or "$" in path_text or path_text.startswith("~"):
        raise VerifiedKnowledgeError("fixture path must be an explicit local path")
    path = Path(fixture_path)
    if not path.is_absolute():
        raise VerifiedKnowledgeError("fixture path must be absolute")
    if any(part.startswith(".") for part in path.parts if part not in {path.anchor, ""}):
        raise VerifiedKnowledgeError("hidden fixture paths are rejected")
    if path.is_symlink():
        raise VerifiedKnowledgeError("symlink fixture file is rejected")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise VerifiedKnowledgeError("fixture file is missing") from exc
    root = repository_root.resolve(strict=True)
    if _is_relative_to(resolved, root):
        raise VerifiedKnowledgeError("fixture path must be outside the repository")
    if not resolved.is_file():
        raise VerifiedKnowledgeError("fixture path must be a regular file")
    if resolved.stat().st_size > MAXIMUM_FIXTURE_BYTES:
        raise VerifiedKnowledgeError("fixture file is too large")
    return resolved


class ExplicitLocalVerifiedKnowledgeFixtureReplay:
    """Read one explicit synthetic fixture into memory without mutation."""

    def __init__(self, *, repository_root: Path) -> None:
        self._repository_root = repository_root

    def load_fixture(self, fixture_path: str | Path) -> VerifiedKnowledgeFixtureEnvelope:
        """Load and validate a UTF-8 JSON fixture envelope."""

        path = _validate_fixture_path(fixture_path, repository_root=self._repository_root)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise VerifiedKnowledgeError("fixture file must be valid UTF-8") from exc
        reject_verified_knowledge_payload(text, "verified knowledge fixture")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise VerifiedKnowledgeError("fixture file must be JSON") from exc
        return VerifiedKnowledgeFixtureEnvelope.model_validate(data)


class InMemoryVerifiedKnowledgeCandidateRepository:
    """Per-instance copy-on-write repository with no persistent backend."""

    def __init__(
        self,
        versions: Iterable[VerifiedKnowledgeCandidateVersion] = (),
        *,
        snapshots: Iterable[VerifiedKnowledgeCandidateMemorySnapshot] = (),
        repository_root: Path | None = None,
    ) -> None:
        version_map: dict[str, VerifiedKnowledgeCandidateVersion] = {}
        pair_map: dict[tuple[str, int], str] = {}
        snapshot_map: dict[str, VerifiedKnowledgeCandidateMemorySnapshot] = {}
        for version in versions:
            _add_version(version_map, pair_map, version)
        for snapshot in snapshots:
            existing = snapshot_map.get(snapshot.snapshot_id)
            if (
                existing is not None
                and existing.snapshot_fingerprint != snapshot.snapshot_fingerprint
            ):
                raise VerifiedKnowledgeError("same snapshot ID with changed payload rejected")
            snapshot_map[snapshot.snapshot_id] = snapshot
        self._versions: Mapping[str, VerifiedKnowledgeCandidateVersion] = MappingProxyType(
            dict(version_map)
        )
        self._version_pairs: Mapping[tuple[str, int], str] = MappingProxyType(dict(pair_map))
        self._snapshots: Mapping[str, VerifiedKnowledgeCandidateMemorySnapshot] = (
            MappingProxyType(dict(snapshot_map))
        )
        self._repository_root = repository_root or Path.cwd()

    def with_candidate(
        self, candidate: VerifiedKnowledgeCandidate
    ) -> InMemoryVerifiedKnowledgeCandidateRepository:
        """Return a new repository with an immutable version for candidate."""

        previous = self._latest_version_for_identity(candidate.candidate_identity_id)
        version = create_candidate_version(candidate, previous_version=previous)
        return self.with_candidate_version(version)

    def with_batch(
        self, batch: VerifiedKnowledgeCandidateBatch
    ) -> InMemoryVerifiedKnowledgeCandidateRepository:
        """Return a new repository containing every candidate from a batch."""

        repo = self
        for candidate in batch.candidates:
            repo = repo.with_candidate(candidate)
        return repo

    def with_candidate_version(
        self, version: VerifiedKnowledgeCandidateVersion
    ) -> InMemoryVerifiedKnowledgeCandidateRepository:
        """Return a new repository with version added or idempotently replayed."""

        version_map = dict(self._versions)
        pair_map = dict(self._version_pairs)
        _add_version(version_map, pair_map, version)
        if version.version_number > 1:
            previous = version.previous_candidate_version_id
            if previous is None or previous not in version_map:
                raise VerifiedKnowledgeError("candidate version previous link missing")
        return InMemoryVerifiedKnowledgeCandidateRepository(
            version_map.values(),
            snapshots=self._snapshots.values(),
            repository_root=self._repository_root,
        )

    def candidate_by_id(self, candidate_id: str) -> VerifiedKnowledgeCandidate | None:
        """Return an exact candidate ID match from immutable in-memory versions."""

        for version in self._versions.values():
            if version.candidate_id == candidate_id:
                return version.candidate
        return None

    def latest_candidate_by_identity(
        self, candidate_identity_id: str
    ) -> VerifiedKnowledgeCandidate | None:
        """Return the latest candidate for one exact candidate identity."""

        version = self._latest_version_for_identity(candidate_identity_id)
        return None if version is None else version.candidate

    def history_by_identity(
        self, candidate_identity_id: str
    ) -> VerifiedKnowledgeCandidateHistory:
        """Return contiguous immutable history for one candidate identity."""

        versions = tuple(
            version
            for version in self._versions.values()
            if version.candidate_identity_id == candidate_identity_id
        )
        return build_candidate_history(versions)

    def snapshot(
        self,
        snapshot_id: str = "verified-memory-snapshot-001",
        *,
        created_at: datetime | None = None,
    ) -> VerifiedKnowledgeCandidateMemorySnapshot:
        """Build a deterministic read-only memory snapshot without storing it."""

        latest_versions = tuple(
            sorted(self._latest_versions(), key=lambda item: item.candidate.candidate_id)
        )
        candidates = tuple(version.candidate for version in latest_versions)
        eligible = tuple(
            candidate
            for candidate in candidates
            if candidate.eligibility_decision.status
            is VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
        )
        revalidation = tuple(
            candidate
            for candidate in candidates
            if (
                candidate.eligibility_decision.status
                is VerifiedKnowledgeEligibilityStatus.REVALIDATION_REQUIRED
                or candidate.lifecycle_status
                is VerifiedKnowledgeLifecycleStatus.REVALIDATION_REQUIRED
            )
        )
        payload = {
            "schema_version": VERIFIED_KNOWLEDGE_MEMORY_SNAPSHOT_SCHEMA_VERSION,
            "snapshot_id": snapshot_id,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "candidate_ids": tuple(candidate.candidate_id for candidate in candidates),
            "candidate_identity_ids": tuple(
                candidate.candidate_identity_id for candidate in candidates
            ),
            "latest_version_ids": tuple(
                version.candidate_version_id for version in latest_versions
            ),
            "candidate_count": len(candidates),
            "eligible_candidate_count": len(eligible),
            "ineligible_candidate_count": len(candidates) - len(eligible),
            "revalidation_required_count": len(revalidation),
            "support_candidate_count": sum(
                1
                for candidate in candidates
                if candidate.candidate_kind.value == "support_candidate"
            ),
            "refutation_candidate_count": sum(
                1
                for candidate in candidates
                if candidate.candidate_kind.value == "refutation_candidate"
            ),
            "created_at": created_at or utc_now(),
            "synthetic": True,
            "read_only": True,
            "redacted": True,
            "persistent_write_applied": False,
            "runtime_effect": False,
        }
        return VerifiedKnowledgeCandidateMemorySnapshot.model_validate(
            {**payload, "snapshot_fingerprint": verified_knowledge_fingerprint(payload)}
        )

    def query(
        self, query: VerifiedKnowledgeCandidateQuery
    ) -> VerifiedKnowledgeCandidateQueryResult:
        """Run bounded exact matching over immutable in-memory candidates."""

        matches: list[VerifiedKnowledgeCandidate] = []
        for version in sorted(self._versions.values(), key=lambda item: item.candidate_id):
            candidate = version.candidate
            if not _candidate_matches(candidate, query):
                continue
            matches.append(candidate)
            if len(matches) >= query.limit:
                break
        candidates = tuple(matches)
        payload = {
            "schema_version": VERIFIED_KNOWLEDGE_QUERY_RESULT_SCHEMA_VERSION,
            "query": query,
            "candidates": candidates,
            "result_count": len(candidates),
            "semantic_search_used": False,
            "engagement_ranking_used": False,
            "popularity_ranking_used": False,
            "runtime_effect": False,
        }
        return VerifiedKnowledgeCandidateQueryResult.model_validate(
            {**payload, "query_result_fingerprint": verified_knowledge_fingerprint(payload)}
        )

    def replay_fixture(
        self, fixture_path: str | Path
    ) -> InMemoryVerifiedKnowledgeCandidateRepository:
        """Replay explicit synthetic candidate records in memory only."""

        fixture = ExplicitLocalVerifiedKnowledgeFixtureReplay(
            repository_root=self._repository_root
        ).load_fixture(fixture_path)
        repo = self
        for record in fixture.fixture_records:
            repo = repo._replay_record(record)
        return repo

    def audit(self) -> VerifiedKnowledgeIntegrityReport:
        """Audit repository version uniqueness and immutable boundary flags."""

        findings: list[VerifiedKnowledgeIntegrityFinding] = []
        try:
            for version in self._versions.values():
                _add_version({}, {}, version)
            status = VerifiedKnowledgeIntegrityStatus.PASSED
            reason = "verified_memory_integrity_passed"
        except ValueError:
            status = VerifiedKnowledgeIntegrityStatus.FAILED
            reason = "verified_memory_integrity_failed"
        findings.append(
            VerifiedKnowledgeIntegrityFinding.model_validate(
                {
                    "finding_id": "finding-verified-memory-repository",
                    "status": status,
                    "reason_codes": (reason,),
                    "safe_ids": tuple(sorted(self._versions)),
                    "fingerprints": tuple(
                        sorted(version.version_fingerprint for version in self._versions.values())
                    ),
                    "bounded_count": len(self._versions),
                    "redacted_summary": "verified knowledge repository audit",
                    "runtime_effect": False,
                }
            )
        )
        payload = {
            "schema_version": VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
            "report_id": "integrity-verified-memory-repository",
            "status": status,
            "findings": tuple(sorted(findings, key=lambda finding: finding.finding_id)),
            "finding_count": len(findings),
            "read_only": True,
            "redacted": True,
            "persistent_write_applied": False,
            "runtime_effect": False,
        }
        return VerifiedKnowledgeIntegrityReport.model_validate(
            {**payload, "report_fingerprint": verified_knowledge_fingerprint(payload)}
        )

    def reject_persistent_write(
        self, payload: object | None = None
    ) -> VerifiedKnowledgePersistentWriteOutcome:
        """Always fail closed, including empty persistent-write requests."""

        _ = payload
        return VerifiedKnowledgePersistentWriteOutcome.PERSISTENT_WRITE_DISABLED

    def _latest_versions(self) -> tuple[VerifiedKnowledgeCandidateVersion, ...]:
        latest: dict[str, VerifiedKnowledgeCandidateVersion] = {}
        for version in self._versions.values():
            current = latest.get(version.candidate_identity_id)
            if current is None or version.version_number > current.version_number:
                latest[version.candidate_identity_id] = version
        return tuple(latest[key] for key in sorted(latest))

    def _latest_version_for_identity(
        self, candidate_identity_id: str
    ) -> VerifiedKnowledgeCandidateVersion | None:
        matches = [
            version
            for version in self._versions.values()
            if version.candidate_identity_id == candidate_identity_id
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.version_number)

    def _replay_record(
        self, record: Mapping[str, object]
    ) -> InMemoryVerifiedKnowledgeCandidateRepository:
        payload: object
        if "candidate_version" in record:
            payload = record["candidate_version"]
        elif "payload" in record:
            payload = record["payload"]
        else:
            payload = record
        try:
            version = VerifiedKnowledgeCandidateVersion.model_validate(payload)
        except ValidationError:
            candidate = VerifiedKnowledgeCandidate.model_validate(payload)
            return self.with_candidate(candidate)
        return self.with_candidate_version(version)


def _add_version(
    version_map: dict[str, VerifiedKnowledgeCandidateVersion],
    pair_map: dict[tuple[str, int], str],
    version: VerifiedKnowledgeCandidateVersion,
) -> None:
    existing = version_map.get(version.candidate_version_id)
    if existing is not None:
        if existing.version_fingerprint != version.version_fingerprint:
            raise VerifiedKnowledgeError("same version ID with changed payload rejected")
        return
    key = (version.candidate_identity_id, version.version_number)
    existing_id = pair_map.get(key)
    if existing_id is not None:
        existing_version = version_map[existing_id]
        if existing_version.version_fingerprint != version.version_fingerprint:
            raise VerifiedKnowledgeError("same version identity with changed payload rejected")
        return
    version_map[version.candidate_version_id] = version
    pair_map[key] = version.candidate_version_id


def _candidate_matches(
    candidate: VerifiedKnowledgeCandidate,
    query: VerifiedKnowledgeCandidateQuery,
) -> bool:
    if query.candidate_id is not None and candidate.candidate_id != query.candidate_id:
        return False
    if (
        query.candidate_identity_id is not None
        and candidate.candidate_identity_id != query.candidate_identity_id
    ):
        return False
    if query.candidate_kind is not None and candidate.candidate_kind is not query.candidate_kind:
        return False
    if query.claim_id is not None and candidate.claim_id != query.claim_id:
        return False
    if query.assessment_id is not None and candidate.assessment_id != query.assessment_id:
        return False
    if query.mesh_session_id is not None and candidate.mesh_session_id != query.mesh_session_id:
        return False
    if query.synthesis_id is not None and candidate.synthesis_id != query.synthesis_id:
        return False
    if (
        query.tool_verification_session_id is not None
        and query.tool_verification_session_id not in candidate.tool_verification_session_ids
    ):
        return False
    if (
        query.eligibility_status is not None
        and candidate.eligibility_decision.status is not query.eligibility_status
    ):
        return False
    if (
        query.lifecycle_status is not None
        and candidate.lifecycle_status is not query.lifecycle_status
    ):
        return False
    if (
        query.operator_review_required is not None
        and candidate.operator_review_required != query.operator_review_required
    ):
        return False
    if query.revalidation_due is not None:
        due = candidate.revalidation_due_at is not None
        if due != query.revalidation_due:
            return False
    if query.expired is not None:
        expired = (
            candidate.expires_at is not None
            or candidate.lifecycle_status is VerifiedKnowledgeLifecycleStatus.EXPIRED
        )
        if expired != query.expired:
            return False
    if query.minimum_version is not None and candidate.candidate_version < query.minimum_version:
        return False
    if query.maximum_version is not None and candidate.candidate_version > query.maximum_version:
        return False
    return True


def build_verified_knowledge_candidate_batch(
    *,
    batch_id: str,
    candidates: Iterable[VerifiedKnowledgeCandidate],
) -> VerifiedKnowledgeCandidateBatch:
    """Build a deterministic candidate batch."""

    ordered = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_BATCH_SCHEMA_VERSION,
        "batch_id": batch_id,
        "candidates": ordered,
        "candidate_count": len(ordered),
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeCandidateBatch.model_validate(
        {**payload, "batch_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_verified_knowledge_fixture_envelope(
    *,
    fixture_id: str,
    fixture_records: Iterable[Mapping[str, Any]],
) -> VerifiedKnowledgeFixtureEnvelope:
    """Build an explicit synthetic fixture envelope."""

    records = tuple(dict(record) for record in fixture_records)
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_FIXTURE_SCHEMA_VERSION,
        "fixture_id": fixture_id,
        "fixture_records": records,
        "fixture_record_count": len(records),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeFixtureEnvelope.model_validate(
        {**payload, "fixture_fingerprint": verified_knowledge_fingerprint(payload)}
    )


__all__ = [
    "ExplicitLocalVerifiedKnowledgeFixtureReplay",
    "InMemoryVerifiedKnowledgeCandidateRepository",
    "build_verified_knowledge_candidate_batch",
    "build_verified_knowledge_fixture_envelope",
]

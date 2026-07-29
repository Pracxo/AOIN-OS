"""Temporary persistence composition for the AION-228 pilot."""

from __future__ import annotations

from pathlib import Path

from aion_brain.contracts.governed_continual_learning import (
    ContinualLearningPersistenceBinding,
    ContinualLearningPersistenceStatus,
    build_record,
    continual_fingerprint,
    fingerprint_file_path,
    utc_now,
)
from aion_brain.governed_learning_memory.local_sqlite_store import (
    ControlledLocalAppendOnlyPersistenceService,
)


class ControlledContinualLearningPersistenceAdapter:
    """AION-228 temporary-store binding over the local append-only service."""

    component_service = ControlledLocalAppendOnlyPersistenceService

    def build_temporary_persistence_binding(
        self,
        *,
        session_id: str,
        cycle_id: str,
        transaction_id: str,
        temporary_store_path: Path,
        approval_bundle_fingerprint: str,
        knowledge_identity_ids: tuple[str, ...],
        knowledge_version_ids: tuple[str, ...],
        projection_record_fingerprints: tuple[str, ...],
    ) -> ContinualLearningPersistenceBinding:
        """Record a dual-approved temporary persistence result without retaining the store."""

        return build_record(
            ContinualLearningPersistenceBinding,
            {
                "schema_version": "aion-glm-continual-learning-persistence-binding/v1",
                "binding_id": f"{cycle_id}-persistence-binding",
                "session_id": session_id,
                "cycle_id": cycle_id,
                "transaction_id": transaction_id,
                "status": ContinualLearningPersistenceStatus.TEMPORARILY_PERSISTED,
                "temporary_store_fingerprint": fingerprint_file_path(temporary_store_path),
                "persistence_receipt_fingerprint": continual_fingerprint(
                    {"transaction": transaction_id, "versions": knowledge_version_ids}
                ),
                "knowledge_identity_ids": knowledge_identity_ids,
                "knowledge_version_ids": knowledge_version_ids,
                "projection_record_fingerprints": projection_record_fingerprints,
                "approval_bundle_fingerprint": approval_bundle_fingerprint,
                "approval_count": 2,
                "created_at": utc_now(),
            },
            "persistence_binding_fingerprint",
        )

    def build_noop_persistence_binding(
        self,
        *,
        session_id: str,
        cycle_id: str,
        transaction_id: str,
    ) -> ContinualLearningPersistenceBinding:
        """Record a cycle-policy no-op for cycles that must not write."""

        return build_record(
            ContinualLearningPersistenceBinding,
            {
                "schema_version": "aion-glm-continual-learning-persistence-binding/v1",
                "binding_id": f"{cycle_id}-persistence-binding",
                "session_id": session_id,
                "cycle_id": cycle_id,
                "transaction_id": transaction_id,
                "status": ContinualLearningPersistenceStatus.NOT_APPLICABLE,
                "temporary_store_fingerprint": continual_fingerprint(
                    {"temporary_store": "not_applicable"}
                ),
                "persistence_receipt_fingerprint": continual_fingerprint(
                    {"persistence": "not_applicable"}
                ),
                "knowledge_identity_ids": (),
                "knowledge_version_ids": (),
                "projection_record_fingerprints": (),
                "approval_bundle_fingerprint": continual_fingerprint(
                    {"approval": "not_applicable"}
                ),
                "approval_count": 0,
                "created_at": utc_now(),
            },
            "persistence_binding_fingerprint",
        )

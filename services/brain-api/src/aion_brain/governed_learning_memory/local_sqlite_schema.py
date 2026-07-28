"""Static SQLite schema v1 for isolated GLM local persistence."""

# ruff: noqa: E501

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from aion_brain.contracts.governed_learning_memory_persistence import (
    LOCAL_PERSISTENCE_CONTRACT_SCHEMA_VERSION,
    SQLITE_APPLICATION_ID,
    SQLITE_USER_VERSION,
    persistence_fingerprint,
)

APPLICATION_TABLES: Final[tuple[str, ...]] = (
    "glm_store_metadata",
    "glm_persistence_transactions",
    "glm_approval_bindings",
    "glm_candidate_evidence_receipts",
    "glm_knowledge_identities",
    "glm_knowledge_versions",
    "glm_memory_projection_records",
    "glm_belief_projection_candidates",
    "glm_ledger_events",
)

APPEND_ONLY_TABLES: Final[tuple[str, ...]] = APPLICATION_TABLES

CREATE_TABLE_STATEMENTS: Final[tuple[str, ...]] = (
    """
    CREATE TABLE glm_store_metadata (
      store_id TEXT PRIMARY KEY,
      store_identity_fingerprint TEXT NOT NULL UNIQUE,
      schema_version TEXT NOT NULL,
      schema_fingerprint TEXT NOT NULL,
      application_id INTEGER NOT NULL,
      authorization_transaction_id TEXT NOT NULL,
      created_at TEXT NOT NULL,
      status TEXT NOT NULL,
      metadata_fingerprint TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE glm_persistence_transactions (
      transaction_id TEXT PRIMARY KEY,
      store_id TEXT NOT NULL REFERENCES glm_store_metadata(store_id),
      request_fingerprint TEXT NOT NULL,
      promotion_plan_fingerprint TEXT NOT NULL,
      promotion_result_fingerprint TEXT NOT NULL,
      persistence_authorization_fingerprint TEXT NOT NULL,
      approval_bundle_fingerprint TEXT NOT NULL,
      transaction_fingerprint TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL,
      started_at TEXT NOT NULL,
      committed_at TEXT NOT NULL,
      ledger_start_sequence INTEGER NOT NULL,
      ledger_end_sequence INTEGER NOT NULL,
      ledger_head_before TEXT NOT NULL,
      ledger_head_after TEXT NOT NULL,
      transaction_chain_head TEXT NOT NULL,
      knowledge_identity_count INTEGER NOT NULL,
      knowledge_version_count INTEGER NOT NULL,
      projection_count INTEGER NOT NULL,
      belief_candidate_count INTEGER NOT NULL,
      candidate_receipt_count INTEGER NOT NULL,
      production_memory_written INTEGER NOT NULL DEFAULT 0 CHECK (production_memory_written = 0),
      actual_belief_created INTEGER NOT NULL DEFAULT 0 CHECK (actual_belief_created = 0),
      actual_belief_mutated INTEGER NOT NULL DEFAULT 0 CHECK (actual_belief_mutated = 0),
      automatic_promotion_applied INTEGER NOT NULL DEFAULT 0 CHECK (automatic_promotion_applied = 0),
      payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE glm_approval_bindings (
      binding_id TEXT PRIMARY KEY,
      transaction_id TEXT NOT NULL REFERENCES glm_persistence_transactions(transaction_id),
      role TEXT NOT NULL,
      action_type TEXT NOT NULL,
      approval_scope_fingerprint TEXT NOT NULL,
      request_fingerprint TEXT NOT NULL,
      decision_fingerprint TEXT NOT NULL,
      approver_identity_fingerprint TEXT NOT NULL,
      transaction_binding_fingerprint TEXT NOT NULL,
      persisted_raw_payload INTEGER NOT NULL DEFAULT 0 CHECK (persisted_raw_payload = 0),
      binding_fingerprint TEXT NOT NULL UNIQUE,
      payload_json TEXT NOT NULL,
      UNIQUE (request_fingerprint, decision_fingerprint, transaction_binding_fingerprint)
    )
    """,
    """
    CREATE TABLE glm_candidate_evidence_receipts (
      candidate_receipt_id TEXT PRIMARY KEY,
      transaction_id TEXT NOT NULL REFERENCES glm_persistence_transactions(transaction_id),
      candidate_id TEXT NOT NULL,
      candidate_fingerprint TEXT NOT NULL,
      lineage_fingerprint TEXT NOT NULL,
      eligibility_fingerprint TEXT NOT NULL,
      candidate_integrity_fingerprint TEXT NOT NULL,
      promotion_plan_fingerprint TEXT NOT NULL,
      promotion_result_fingerprint TEXT NOT NULL,
      candidate_body_persisted INTEGER NOT NULL DEFAULT 0 CHECK (candidate_body_persisted = 0),
      receipt_fingerprint TEXT NOT NULL UNIQUE,
      payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE glm_knowledge_identities (
      knowledge_identity_id TEXT PRIMARY KEY,
      claim_identity_fingerprint TEXT NOT NULL,
      valid_time_fingerprint TEXT NOT NULL,
      jurisdiction_fingerprint TEXT NOT NULL,
      version_scope_fingerprint TEXT NOT NULL,
      created_transaction_id TEXT NOT NULL REFERENCES glm_persistence_transactions(transaction_id),
      identity_fingerprint TEXT NOT NULL UNIQUE,
      payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE glm_knowledge_versions (
      knowledge_version_id TEXT PRIMARY KEY,
      knowledge_identity_id TEXT NOT NULL REFERENCES glm_knowledge_identities(knowledge_identity_id),
      version_number INTEGER NOT NULL,
      event_type TEXT NOT NULL,
      candidate_posture TEXT NOT NULL,
      candidate_id TEXT NOT NULL,
      approved_bounded_statement TEXT NOT NULL,
      bounded_summary TEXT NOT NULL,
      language_code TEXT NOT NULL,
      sensitivity TEXT NOT NULL CHECK (sensitivity IN ('public', 'internal')),
      content_fingerprint TEXT NOT NULL,
      candidate_fingerprint TEXT NOT NULL,
      lineage_fingerprint TEXT NOT NULL,
      approval_bundle_fingerprint TEXT NOT NULL,
      promotion_plan_fingerprint TEXT NOT NULL,
      promotion_result_fingerprint TEXT NOT NULL,
      confidence_cap TEXT NOT NULL,
      valid_from TEXT NOT NULL,
      valid_to TEXT,
      supersedes_version_id TEXT,
      retracts_version_id TEXT,
      expires_version_id TEXT,
      created_transaction_id TEXT NOT NULL REFERENCES glm_persistence_transactions(transaction_id),
      version_fingerprint TEXT NOT NULL UNIQUE,
      payload_json TEXT NOT NULL,
      UNIQUE (knowledge_identity_id, version_number)
    )
    """,
    """
    CREATE TABLE glm_memory_projection_records (
      projection_record_id TEXT PRIMARY KEY,
      projection_type TEXT NOT NULL CHECK (projection_type IN ('semantic', 'episodic', 'procedural')),
      transaction_id TEXT NOT NULL REFERENCES glm_persistence_transactions(transaction_id),
      knowledge_identity_id TEXT NOT NULL REFERENCES glm_knowledge_identities(knowledge_identity_id),
      knowledge_version_id TEXT NOT NULL REFERENCES glm_knowledge_versions(knowledge_version_id),
      content_reference_fingerprint TEXT NOT NULL,
      summary TEXT NOT NULL,
      confidence_cap TEXT NOT NULL,
      sensitivity TEXT NOT NULL CHECK (sensitivity IN ('public', 'internal')),
      owner_scope_fingerprints_json TEXT NOT NULL,
      provenance_fingerprints_json TEXT NOT NULL,
      projection_fingerprint TEXT NOT NULL UNIQUE,
      created_transaction_id TEXT NOT NULL REFERENCES glm_persistence_transactions(transaction_id),
      production_memory_written INTEGER NOT NULL DEFAULT 0 CHECK (production_memory_written = 0),
      payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE glm_belief_projection_candidates (
      belief_candidate_id TEXT PRIMARY KEY,
      transaction_id TEXT NOT NULL REFERENCES glm_persistence_transactions(transaction_id),
      knowledge_identity_id TEXT NOT NULL REFERENCES glm_knowledge_identities(knowledge_identity_id),
      knowledge_version_id TEXT NOT NULL REFERENCES glm_knowledge_versions(knowledge_version_id),
      proposed_posture TEXT NOT NULL,
      confidence_cap TEXT NOT NULL,
      uncertainty_fingerprint TEXT NOT NULL,
      contradiction_fingerprint TEXT NOT NULL,
      provenance_fingerprints_json TEXT NOT NULL,
      candidate_fingerprint TEXT NOT NULL UNIQUE,
      actual_belief_created INTEGER NOT NULL DEFAULT 0 CHECK (actual_belief_created = 0),
      actual_belief_mutated INTEGER NOT NULL DEFAULT 0 CHECK (actual_belief_mutated = 0),
      payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE glm_ledger_events (
      global_sequence INTEGER PRIMARY KEY,
      transaction_id TEXT NOT NULL,
      transaction_sequence INTEGER NOT NULL,
      event_type TEXT NOT NULL,
      record_type TEXT NOT NULL,
      record_id TEXT NOT NULL,
      record_fingerprint TEXT NOT NULL,
      previous_global_hash TEXT NOT NULL,
      global_event_hash TEXT NOT NULL UNIQUE,
      previous_transaction_hash TEXT NOT NULL,
      transaction_event_hash TEXT NOT NULL UNIQUE,
      created_at TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      UNIQUE (transaction_id, transaction_sequence)
    )
    """,
)

CREATE_INDEX_STATEMENTS: Final[tuple[str, ...]] = (
    "CREATE INDEX idx_glm_versions_identity ON glm_knowledge_versions (knowledge_identity_id)",
    "CREATE INDEX idx_glm_versions_transaction ON glm_knowledge_versions (created_transaction_id)",
    "CREATE INDEX idx_glm_versions_candidate_id ON glm_knowledge_versions (candidate_id)",
    "CREATE INDEX idx_glm_versions_candidate ON glm_knowledge_versions (candidate_fingerprint)",
    "CREATE INDEX idx_glm_projections_transaction ON glm_memory_projection_records (transaction_id)",
    "CREATE INDEX idx_glm_projections_identity ON glm_memory_projection_records (knowledge_identity_id)",
    "CREATE INDEX idx_glm_belief_transaction ON glm_belief_projection_candidates (transaction_id)",
    "CREATE INDEX idx_glm_ledger_transaction ON glm_ledger_events (transaction_id)",
)


def _trigger_statement(table: str, action: str) -> str:
    return f"""
    CREATE TRIGGER {table}_reject_{action.lower()}
    BEFORE {action} ON {table}
    BEGIN
      SELECT RAISE(ABORT, 'AION-224 append-only violation: {table} {action.lower()} rejected');
    END
    """


CREATE_TRIGGER_STATEMENTS: Final[tuple[str, ...]] = tuple(
    _trigger_statement(table, action)
    for table in APPEND_ONLY_TABLES
    for action in ("UPDATE", "DELETE")
)

EXPECTED_TRIGGER_NAMES: Final[tuple[str, ...]] = tuple(
    f"{table}_reject_{action}" for table in APPEND_ONLY_TABLES for action in ("update", "delete")
)

EXPECTED_INDEX_NAMES: Final[tuple[str, ...]] = tuple(
    statement.split()[2] for statement in CREATE_INDEX_STATEMENTS
)

CREATE_SCHEMA_SQL: Final[str] = (
    ";\n".join([*CREATE_TABLE_STATEMENTS, *CREATE_INDEX_STATEMENTS, *CREATE_TRIGGER_STATEMENTS])
    + ";\n"
)

EXPECTED_SQLITE_PRAGMAS: Final = MappingProxyType(
    {
        "foreign_keys": 1,
        "journal_mode": "wal",
        "synchronous": 2,
        "trusted_schema": 0,
        "recursive_triggers": 0,
        "auto_vacuum": 0,
        "temp_store": 2,
        "application_id": SQLITE_APPLICATION_ID,
        "user_version": SQLITE_USER_VERSION,
    }
)

SCHEMA_FINGERPRINT: Final[str] = persistence_fingerprint(
    {
        "schema_version": LOCAL_PERSISTENCE_CONTRACT_SCHEMA_VERSION,
        "application_id": SQLITE_APPLICATION_ID,
        "user_version": SQLITE_USER_VERSION,
        "tables": APPLICATION_TABLES,
        "indexes": EXPECTED_INDEX_NAMES,
        "triggers": EXPECTED_TRIGGER_NAMES,
        "sql": CREATE_SCHEMA_SQL,
    }
)

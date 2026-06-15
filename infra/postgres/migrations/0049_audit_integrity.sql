CREATE TABLE IF NOT EXISTS aion_audit_entries (
  audit_entry_id TEXT PRIMARY KEY,
  sequence_number BIGINT NOT NULL UNIQUE,
  trace_id TEXT NULL,
  correlation_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  action_type TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NULL,
  event_type TEXT NOT NULL,
  outcome TEXT NOT NULL,
  risk_level TEXT NULL,
  policy_decision_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  risk_assessment_id TEXT NULL,
  approval_request_id TEXT NULL,
  command_id TEXT NULL,
  source_component TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  previous_hash TEXT NULL,
  entry_hash TEXT NOT NULL UNIQUE,
  hash_algorithm TEXT NOT NULL,
  canonical_payload JSONB NOT NULL,
  redaction_metadata JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_sequence_number ON aion_audit_entries(sequence_number);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_trace_id ON aion_audit_entries(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_correlation_id ON aion_audit_entries(correlation_id);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_actor_id ON aion_audit_entries(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_workspace_id ON aion_audit_entries(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_action_type ON aion_audit_entries(action_type);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_resource_type ON aion_audit_entries(resource_type);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_resource_id ON aion_audit_entries(resource_id);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_event_type ON aion_audit_entries(event_type);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_outcome ON aion_audit_entries(outcome);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_source_component ON aion_audit_entries(source_component);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_entry_hash ON aion_audit_entries(entry_hash);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_previous_hash ON aion_audit_entries(previous_hash);
CREATE INDEX IF NOT EXISTS ix_aion_audit_entries_created_at ON aion_audit_entries(created_at);

CREATE TABLE IF NOT EXISTS aion_audit_integrity_checkpoints (
  checkpoint_id TEXT PRIMARY KEY,
  from_sequence BIGINT NOT NULL,
  to_sequence BIGINT NOT NULL,
  entry_count INTEGER NOT NULL,
  root_hash TEXT NOT NULL,
  previous_checkpoint_hash TEXT NULL,
  checkpoint_hash TEXT NOT NULL,
  hash_algorithm TEXT NOT NULL,
  status TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_audit_checkpoints_from_sequence ON aion_audit_integrity_checkpoints(from_sequence);
CREATE INDEX IF NOT EXISTS ix_aion_audit_checkpoints_to_sequence ON aion_audit_integrity_checkpoints(to_sequence);
CREATE INDEX IF NOT EXISTS ix_aion_audit_checkpoints_root_hash ON aion_audit_integrity_checkpoints(root_hash);
CREATE INDEX IF NOT EXISTS ix_aion_audit_checkpoints_checkpoint_hash ON aion_audit_integrity_checkpoints(checkpoint_hash);
CREATE INDEX IF NOT EXISTS ix_aion_audit_checkpoints_status ON aion_audit_integrity_checkpoints(status);
CREATE INDEX IF NOT EXISTS ix_aion_audit_checkpoints_created_at ON aion_audit_integrity_checkpoints(created_at);

CREATE TABLE IF NOT EXISTS aion_provenance_links (
  provenance_link_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  audit_entry_id TEXT NULL,
  evidence_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_trace_id ON aion_provenance_links(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_source_type ON aion_provenance_links(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_source_id ON aion_provenance_links(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_target_type ON aion_provenance_links(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_target_id ON aion_provenance_links(target_id);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_relation_type ON aion_provenance_links(relation_type);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_audit_entry_id ON aion_provenance_links(audit_entry_id);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_deleted_at ON aion_provenance_links(deleted_at);
CREATE INDEX IF NOT EXISTS ix_aion_provenance_links_created_at ON aion_provenance_links(created_at);

CREATE TABLE IF NOT EXISTS aion_audit_verification_runs (
  audit_verification_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  from_sequence BIGINT NULL,
  to_sequence BIGINT NULL,
  checked_count INTEGER NOT NULL,
  valid_count INTEGER NOT NULL,
  invalid_count INTEGER NOT NULL,
  missing_count INTEGER NOT NULL,
  violations JSONB NOT NULL,
  report JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_audit_verification_trace_id ON aion_audit_verification_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_audit_verification_status ON aion_audit_verification_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_audit_verification_from_sequence ON aion_audit_verification_runs(from_sequence);
CREATE INDEX IF NOT EXISTS ix_aion_audit_verification_to_sequence ON aion_audit_verification_runs(to_sequence);
CREATE INDEX IF NOT EXISTS ix_aion_audit_verification_created_at ON aion_audit_verification_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_audit_export_records (
  audit_export_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  export_type TEXT NOT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  from_sequence BIGINT NULL,
  to_sequence BIGINT NULL,
  filters JSONB NOT NULL,
  redaction_mode TEXT NOT NULL,
  output_ref TEXT NULL,
  file_count INTEGER NOT NULL,
  entry_count INTEGER NOT NULL,
  checksum TEXT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_audit_export_trace_id ON aion_audit_export_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_audit_export_export_type ON aion_audit_export_records(export_type);
CREATE INDEX IF NOT EXISTS ix_aion_audit_export_status ON aion_audit_export_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_audit_export_redaction_mode ON aion_audit_export_records(redaction_mode);
CREATE INDEX IF NOT EXISTS ix_aion_audit_export_created_at ON aion_audit_export_records(created_at);

CREATE TABLE IF NOT EXISTS aion_resource_index_records (
  resource_index_id TEXT PRIMARY KEY,
  resource_uri TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  source_system TEXT NOT NULL,
  status TEXT NOT NULL,
  visibility TEXT NOT NULL,
  sensitivity TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  tags JSONB NOT NULL,
  refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  content_hash TEXT NULL,
  first_seen_at TIMESTAMPTZ NOT NULL,
  last_seen_at TIMESTAMPTZ NOT NULL,
  deleted_at TIMESTAMPTZ NULL,
  archived_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_resource_index_resource_uri ON aion_resource_index_records (resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_resource_type ON aion_resource_index_records (resource_type);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_resource_id ON aion_resource_index_records (resource_id);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_trace_id ON aion_resource_index_records (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_actor_id ON aion_resource_index_records (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_workspace_id ON aion_resource_index_records (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_source_system ON aion_resource_index_records (source_system);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_status ON aion_resource_index_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_visibility ON aion_resource_index_records (visibility);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_sensitivity ON aion_resource_index_records (sensitivity);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_content_hash ON aion_resource_index_records (content_hash);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_first_seen_at ON aion_resource_index_records (first_seen_at);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_last_seen_at ON aion_resource_index_records (last_seen_at);
CREATE INDEX IF NOT EXISTS ix_aion_resource_index_deleted_at ON aion_resource_index_records (deleted_at);

CREATE TABLE IF NOT EXISTS aion_resource_reference_links (
  resource_link_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  source_resource_uri TEXT NOT NULL,
  target_resource_uri TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  discovered_by TEXT NOT NULL,
  evidence_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  verified_at TIMESTAMPTZ NULL,
  broken_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_resource_links_trace_id ON aion_resource_reference_links (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_resource_links_source_uri ON aion_resource_reference_links (source_resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_resource_links_target_uri ON aion_resource_reference_links (target_resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_resource_links_source_type ON aion_resource_reference_links (source_type);
CREATE INDEX IF NOT EXISTS ix_aion_resource_links_target_type ON aion_resource_reference_links (target_type);
CREATE INDEX IF NOT EXISTS ix_aion_resource_links_relation_type ON aion_resource_reference_links (relation_type);
CREATE INDEX IF NOT EXISTS ix_aion_resource_links_status ON aion_resource_reference_links (status);
CREATE INDEX IF NOT EXISTS ix_aion_resource_links_created_at ON aion_resource_reference_links (created_at);

CREATE TABLE IF NOT EXISTS aion_registry_backlinks (
  backlink_id TEXT PRIMARY KEY,
  resource_uri TEXT NOT NULL,
  referring_resource_uri TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  status TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_registry_backlinks_resource_uri ON aion_registry_backlinks (resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_registry_backlinks_referring_uri ON aion_registry_backlinks (referring_resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_registry_backlinks_relation_type ON aion_registry_backlinks (relation_type);
CREATE INDEX IF NOT EXISTS ix_aion_registry_backlinks_status ON aion_registry_backlinks (status);
CREATE INDEX IF NOT EXISTS ix_aion_registry_backlinks_created_at ON aion_registry_backlinks (created_at);

CREATE TABLE IF NOT EXISTS aion_broken_reference_records (
  broken_reference_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  source_resource_uri TEXT NOT NULL,
  target_resource_uri TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  issue_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  validation_run_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL,
  dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_trace_id ON aion_broken_reference_records (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_source_uri ON aion_broken_reference_records (source_resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_target_uri ON aion_broken_reference_records (target_resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_issue_type ON aion_broken_reference_records (issue_type);
CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_severity ON aion_broken_reference_records (severity);
CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_status ON aion_broken_reference_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_validation_run_id ON aion_broken_reference_records (validation_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_broken_refs_created_at ON aion_broken_reference_records (created_at);

CREATE TABLE IF NOT EXISTS aion_orphaned_resource_records (
  orphaned_resource_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  resource_uri TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  source_system TEXT NOT NULL,
  issue_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  inbound_ref_count INTEGER NOT NULL,
  outbound_ref_count INTEGER NOT NULL,
  validation_run_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL,
  dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_orphans_trace_id ON aion_orphaned_resource_records (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_orphans_resource_uri ON aion_orphaned_resource_records (resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_orphans_resource_type ON aion_orphaned_resource_records (resource_type);
CREATE INDEX IF NOT EXISTS ix_aion_orphans_source_system ON aion_orphaned_resource_records (source_system);
CREATE INDEX IF NOT EXISTS ix_aion_orphans_issue_type ON aion_orphaned_resource_records (issue_type);
CREATE INDEX IF NOT EXISTS ix_aion_orphans_severity ON aion_orphaned_resource_records (severity);
CREATE INDEX IF NOT EXISTS ix_aion_orphans_status ON aion_orphaned_resource_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_orphans_validation_run_id ON aion_orphaned_resource_records (validation_run_id);

CREATE TABLE IF NOT EXISTS aion_reference_validation_runs (
  validation_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  resource_types JSONB NOT NULL,
  source_systems JSONB NOT NULL,
  resources_checked INTEGER NOT NULL,
  links_checked INTEGER NOT NULL,
  broken_count INTEGER NOT NULL,
  orphaned_count INTEGER NOT NULL,
  stale_count INTEGER NOT NULL,
  broken_references JSONB NOT NULL,
  orphaned_resources JSONB NOT NULL,
  warnings JSONB NOT NULL,
  failures JSONB NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_reference_runs_trace_id ON aion_reference_validation_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_reference_runs_status ON aion_reference_validation_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_reference_runs_mode ON aion_reference_validation_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_reference_runs_created_at ON aion_reference_validation_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_registry_rebuild_runs (
  rebuild_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  resource_types JSONB NOT NULL,
  source_systems JSONB NOT NULL,
  resources_seen INTEGER NOT NULL,
  resources_indexed INTEGER NOT NULL,
  links_indexed INTEGER NOT NULL,
  skipped INTEGER NOT NULL,
  failures JSONB NOT NULL,
  warnings JSONB NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_rebuild_runs_trace_id ON aion_registry_rebuild_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_rebuild_runs_status ON aion_registry_rebuild_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_rebuild_runs_mode ON aion_registry_rebuild_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_rebuild_runs_created_at ON aion_registry_rebuild_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_registry_snapshots (
  registry_snapshot_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  snapshot_type TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  resource_count INTEGER NOT NULL,
  link_count INTEGER NOT NULL,
  broken_count INTEGER NOT NULL,
  orphaned_count INTEGER NOT NULL,
  resource_type_counts JSONB NOT NULL,
  source_system_counts JSONB NOT NULL,
  root_hash TEXT NOT NULL,
  report JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_registry_snapshots_trace_id ON aion_registry_snapshots (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_registry_snapshots_status ON aion_registry_snapshots (status);
CREATE INDEX IF NOT EXISTS ix_aion_registry_snapshots_type ON aion_registry_snapshots (snapshot_type);
CREATE INDEX IF NOT EXISTS ix_aion_registry_snapshots_root_hash ON aion_registry_snapshots (root_hash);
CREATE INDEX IF NOT EXISTS ix_aion_registry_snapshots_created_at ON aion_registry_snapshots (created_at);

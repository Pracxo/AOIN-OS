CREATE TABLE IF NOT EXISTS aion_operator_snapshots (
  operator_snapshot_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  snapshot_type TEXT NOT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  overview JSONB NOT NULL,
  action_items JSONB NOT NULL,
  queue_summaries JSONB NOT NULL,
  readiness JSONB NOT NULL,
  generated_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_operator_snapshots_trace_id ON aion_operator_snapshots(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_snapshots_actor_id ON aion_operator_snapshots(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_snapshots_workspace_id ON aion_operator_snapshots(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_snapshots_snapshot_type ON aion_operator_snapshots(snapshot_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_snapshots_status ON aion_operator_snapshots(status);
CREATE INDEX IF NOT EXISTS ix_aion_operator_snapshots_created_at ON aion_operator_snapshots(created_at);

CREATE TABLE IF NOT EXISTS aion_operator_action_items (
  action_item_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  category TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  runbook_ref TEXT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  acknowledged_at TIMESTAMPTZ NULL,
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_operator_action_items_trace_id ON aion_operator_action_items(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_items_source_type ON aion_operator_action_items(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_items_category ON aion_operator_action_items(category);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_items_severity ON aion_operator_action_items(severity);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_items_status ON aion_operator_action_items(status);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_items_created_at ON aion_operator_action_items(created_at);

CREATE TABLE IF NOT EXISTS aion_operator_acknowledgements (
  acknowledgement_id TEXT PRIMARY KEY,
  action_item_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  reason TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_operator_ack_action_item_id ON aion_operator_acknowledgements(action_item_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_ack_source_type ON aion_operator_acknowledgements(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_ack_source_id ON aion_operator_acknowledgements(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_ack_actor_id ON aion_operator_acknowledgements(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_ack_workspace_id ON aion_operator_acknowledgements(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_ack_created_at ON aion_operator_acknowledgements(created_at);

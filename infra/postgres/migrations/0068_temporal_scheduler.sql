ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS trace_id TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS actor_id TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS workspace_id TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS name TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS description TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS target_type TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS action_mode TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS target_payload JSONB NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS recurrence JSONB NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS start_at TIMESTAMPTZ NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS end_at TIMESTAMPTZ NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS next_due_at TIMESTAMPTZ NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS last_due_at TIMESTAMPTZ NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS last_tick_run_id TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS owner_scope JSONB NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS created_by TEXT NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS disabled_at TIMESTAMPTZ NULL;
ALTER TABLE aion_schedules ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL;

CREATE INDEX IF NOT EXISTS ix_aion_schedules_trace_id ON aion_schedules(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_schedules_actor_id ON aion_schedules(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_schedules_workspace_id ON aion_schedules(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_schedules_target_type ON aion_schedules(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_schedules_next_due_at ON aion_schedules(next_due_at);
CREATE INDEX IF NOT EXISTS ix_aion_schedules_last_tick_run_id ON aion_schedules(last_tick_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_schedules_deleted_at ON aion_schedules(deleted_at);

CREATE TABLE IF NOT EXISTS aion_schedule_due_items (
    due_item_id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    target_type TEXT NOT NULL,
    action_mode TEXT NOT NULL,
    target_payload JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    created_from_tick_run_id TEXT NULL,
    processed_at TIMESTAMPTZ NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_schedule_due_items_schedule_id ON aion_schedule_due_items(schedule_id);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_due_items_trace_id ON aion_schedule_due_items(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_due_items_workspace_id ON aion_schedule_due_items(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_due_items_due_at ON aion_schedule_due_items(due_at);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_due_items_status ON aion_schedule_due_items(status);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_due_items_created_at ON aion_schedule_due_items(created_at);

CREATE TABLE IF NOT EXISTS aion_reminders (
    reminder_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    schedule_id TEXT NULL,
    due_item_id TEXT NULL,
    reminder_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    refs JSONB NOT NULL,
    snooze_count INTEGER NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ NULL,
    snoozed_until TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_reminders_trace_id ON aion_reminders(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_actor_id ON aion_reminders(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_workspace_id ON aion_reminders(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_schedule_id ON aion_reminders(schedule_id);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_due_item_id ON aion_reminders(due_item_id);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_reminder_type ON aion_reminders(reminder_type);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_due_at ON aion_reminders(due_at);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_status ON aion_reminders(status);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_created_at ON aion_reminders(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_reminders_deleted_at ON aion_reminders(deleted_at);

CREATE TABLE IF NOT EXISTS aion_scheduler_tick_runs (
    tick_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    owner_scope JSONB NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    tick_at TIMESTAMPTZ NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    schedules_checked INTEGER NOT NULL,
    due_items_created INTEGER NOT NULL,
    reminders_created INTEGER NOT NULL,
    notifications_created INTEGER NOT NULL,
    action_proposals_created INTEGER NOT NULL,
    operator_items_created INTEGER NOT NULL,
    schedules_missed INTEGER NOT NULL,
    policy_decision_ids JSONB NOT NULL,
    result JSONB NOT NULL,
    errors JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_scheduler_tick_runs_trace_id ON aion_scheduler_tick_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_tick_runs_workspace_id ON aion_scheduler_tick_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_tick_runs_mode ON aion_scheduler_tick_runs(mode);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_tick_runs_status ON aion_scheduler_tick_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_tick_runs_tick_at ON aion_scheduler_tick_runs(tick_at);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_tick_runs_created_at ON aion_scheduler_tick_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_schedule_policies (
    policy_id TEXT PRIMARY KEY,
    policy_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    conditions JSONB NOT NULL,
    action_on_violation TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_schedule_policies_policy_type ON aion_schedule_policies(policy_type);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_policies_status ON aion_schedule_policies(status);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_policies_action_on_violation ON aion_schedule_policies(action_on_violation);
CREATE INDEX IF NOT EXISTS ix_aion_schedule_policies_created_at ON aion_schedule_policies(created_at);

CREATE TABLE IF NOT EXISTS aion_scheduler_reports (
    report_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    workspace_id TEXT NULL,
    owner_scope JSONB NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    active_schedule_count INTEGER NOT NULL,
    due_item_count INTEGER NOT NULL,
    reminder_count INTEGER NOT NULL,
    missed_schedule_count INTEGER NOT NULL,
    failed_tick_count INTEGER NOT NULL,
    findings JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_scheduler_reports_trace_id ON aion_scheduler_reports(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_reports_workspace_id ON aion_scheduler_reports(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_reports_status ON aion_scheduler_reports(status);
CREATE INDEX IF NOT EXISTS ix_aion_scheduler_reports_created_at ON aion_scheduler_reports(created_at);

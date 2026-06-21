CREATE TABLE IF NOT EXISTS aion_notification_topics (
    topic_id TEXT PRIMARY KEY,
    topic_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    category TEXT NOT NULL,
    severity_default TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_notification_topics_topic_key ON aion_notification_topics(topic_key);
CREATE INDEX IF NOT EXISTS ix_aion_notification_topics_status ON aion_notification_topics(status);
CREATE INDEX IF NOT EXISTS ix_aion_notification_topics_category ON aion_notification_topics(category);
CREATE INDEX IF NOT EXISTS ix_aion_notification_topics_severity_default ON aion_notification_topics(severity_default);
CREATE INDEX IF NOT EXISTS ix_aion_notification_topics_created_at ON aion_notification_topics(created_at);

CREATE TABLE IF NOT EXISTS aion_notification_subscriptions (
    subscription_id TEXT PRIMARY KEY,
    topic_key TEXT NOT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    subscriber_type TEXT NOT NULL,
    subscriber_ref TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    severity_threshold TEXT NOT NULL,
    filters JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_topic_key ON aion_notification_subscriptions(topic_key);
CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_actor_id ON aion_notification_subscriptions(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_workspace_id ON aion_notification_subscriptions(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_subscriber_type ON aion_notification_subscriptions(subscriber_type);
CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_channel ON aion_notification_subscriptions(channel);
CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_status ON aion_notification_subscriptions(status);
CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_severity_threshold ON aion_notification_subscriptions(severity_threshold);
CREATE INDEX IF NOT EXISTS ix_aion_notification_subscriptions_created_at ON aion_notification_subscriptions(created_at);

CREATE TABLE IF NOT EXISTS aion_notifications (
    notification_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    topic_key TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NULL,
    target_type TEXT NULL,
    target_id TEXT NULL,
    owner_scope JSONB NOT NULL,
    refs JSONB NOT NULL,
    delivery_channels JSONB NOT NULL,
    delivered_to JSONB NOT NULL,
    read_by JSONB NOT NULL,
    acknowledged_by JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at TIMESTAMPTZ NULL,
    acknowledged_at TIMESTAMPTZ NULL,
    resolved_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_notifications_trace_id ON aion_notifications(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_actor_id ON aion_notifications(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_workspace_id ON aion_notifications(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_topic_key ON aion_notifications(topic_key);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_status ON aion_notifications(status);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_severity ON aion_notifications(severity);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_source_type ON aion_notifications(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_source_id ON aion_notifications(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_target_type ON aion_notifications(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_target_id ON aion_notifications(target_id);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_created_at ON aion_notifications(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_notifications_deleted_at ON aion_notifications(deleted_at);

CREATE TABLE IF NOT EXISTS aion_alerts (
    alert_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    alert_type TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NULL,
    owner_scope JSONB NOT NULL,
    notification_ids JSONB NOT NULL,
    blocker_refs JSONB NOT NULL,
    run_refs JSONB NOT NULL,
    action_refs JSONB NOT NULL,
    evidence_refs JSONB NOT NULL,
    audit_refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ NULL,
    resolved_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_alerts_trace_id ON aion_alerts(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_actor_id ON aion_alerts(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_workspace_id ON aion_alerts(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_alert_type ON aion_alerts(alert_type);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_status ON aion_alerts(status);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_severity ON aion_alerts(severity);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_source_type ON aion_alerts(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_source_id ON aion_alerts(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_created_at ON aion_alerts(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_alerts_deleted_at ON aion_alerts(deleted_at);

CREATE TABLE IF NOT EXISTS aion_escalation_policies (
    escalation_policy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    topic_key TEXT NULL,
    alert_type TEXT NULL,
    severity_threshold TEXT NOT NULL,
    delay_seconds INTEGER NOT NULL,
    repeat_limit INTEGER NOT NULL,
    escalation_channel TEXT NOT NULL,
    escalation_target TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    conditions JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_escalation_policies_name ON aion_escalation_policies(name);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_policies_status ON aion_escalation_policies(status);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_policies_topic_key ON aion_escalation_policies(topic_key);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_policies_alert_type ON aion_escalation_policies(alert_type);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_policies_severity_threshold ON aion_escalation_policies(severity_threshold);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_policies_escalation_channel ON aion_escalation_policies(escalation_channel);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_policies_created_at ON aion_escalation_policies(created_at);

CREATE TABLE IF NOT EXISTS aion_escalation_records (
    escalation_record_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    alert_id TEXT NULL,
    notification_id TEXT NULL,
    escalation_policy_id TEXT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    escalation_channel TEXT NOT NULL,
    escalation_target TEXT NOT NULL,
    reason TEXT NOT NULL,
    local_only BOOLEAN NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ NULL,
    resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_trace_id ON aion_escalation_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_alert_id ON aion_escalation_records(alert_id);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_notification_id ON aion_escalation_records(notification_id);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_policy_id ON aion_escalation_records(escalation_policy_id);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_status ON aion_escalation_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_severity ON aion_escalation_records(severity);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_channel ON aion_escalation_records(escalation_channel);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_local_only ON aion_escalation_records(local_only);
CREATE INDEX IF NOT EXISTS ix_aion_escalation_records_created_at ON aion_escalation_records(created_at);

CREATE TABLE IF NOT EXISTS aion_notification_digests (
    digest_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    digest_type TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    notification_ids JSONB NOT NULL,
    alert_ids JSONB NOT NULL,
    counts JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_notification_digests_trace_id ON aion_notification_digests(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_notification_digests_actor_id ON aion_notification_digests(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_notification_digests_workspace_id ON aion_notification_digests(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_notification_digests_digest_type ON aion_notification_digests(digest_type);
CREATE INDEX IF NOT EXISTS ix_aion_notification_digests_status ON aion_notification_digests(status);
CREATE INDEX IF NOT EXISTS ix_aion_notification_digests_created_at ON aion_notification_digests(created_at);

"""Settings tests."""

from aion_brain.config import Settings


def test_settings_defaults_match_env_example(monkeypatch) -> None:
    """Settings defaults match the documented local environment."""
    for key in [
        "AION_ENV",
        "AION_SERVICE_NAME",
        "AION_VERSION",
        "DATABASE_URL",
        "REDIS_URL",
        "NATS_URL",
        "OPA_URL",
        "LOG_LEVEL",
        "AION_SEMANTIC_VECTOR_DIMENSIONS",
        "AION_DEFAULT_SEMANTIC_ADAPTER",
        "AION_EMBEDDING_ADAPTER",
        "AION_TURBOVEC_ENABLED",
        "AION_TURBOVEC_INDEX_NAME",
        "AION_TURBOVEC_INDEX_DIR",
        "AION_TURBOVEC_BIT_WIDTH",
        "AION_TURBOVEC_AUTO_PERSIST",
        "AION_TURBOVEC_FAIL_OPEN_TO_PGVECTOR",
        "AION_GRAPHITI_ENABLED",
        "AION_GRAPHITI_CONFIG_NAME",
        "AION_GRAPHITI_BACKEND_TYPE",
        "AION_GRAPHITI_ENDPOINT_REF",
        "AION_GRAPHITI_FAIL_OPEN_TO_POSTGRES_GRAPH",
        "AION_DEFAULT_GRAPH_MEMORY_ADAPTER",
        "AION_MCP_ENABLED",
        "AION_MCP_ALLOW_NETWORK",
        "AION_MCP_ALLOW_STDIO",
        "AION_MCP_TIMEOUT_SECONDS",
        "AION_MCP_DEFAULT_RISK_LEVEL",
        "AION_MCP_AUTO_REGISTER_CAPABILITIES",
        "AION_MEMORY_GOVERNANCE_ENABLED",
        "AION_MEMORY_DECAY_ENABLED",
        "AION_MEMORY_CONFLICT_SCAN_ENABLED",
        "AION_MEMORY_COMPACTION_ENABLED",
        "AION_MEMORY_DEFAULT_DECAY_HALF_LIFE_DAYS",
        "AION_MEMORY_LOW_CONFIDENCE_THRESHOLD",
        "AION_MEMORY_COMPACTION_REQUIRES_APPROVAL",
        "AION_MEMORY_FORGETTING_REQUIRES_APPROVAL",
        "AION_MEMORY_RETENTION_SWEEP_LIMIT_DEFAULT",
        "AION_API_VERSION",
        "AION_API_REQUEST_AUDIT_ENABLED",
        "AION_API_ERROR_DETAIL_ENABLED",
        "AION_API_STACKTRACE_EXPOSED",
        "AION_API_DEFAULT_PAGE_LIMIT",
        "AION_API_MAX_PAGE_LIMIT",
        "AION_API_OPENAPI_HYGIENE_ENABLED",
        "AION_EVENT_REACTION_ROUTER_ENABLED",
        "AION_EVENT_AUTO_DISPATCH_ENABLED",
        "AION_EVENT_REACTION_DEFAULT_MODE",
        "AION_EVENT_REACTION_MAX_ACTIONS_DEFAULT",
        "AION_EVENT_DEAD_LETTER_ENABLED",
        "AION_EVENT_REPLAY_MAX_COUNT",
        "AION_POLICY_CATALOG_ENABLED",
        "AION_POLICY_TEST_HARNESS_ENABLED",
        "AION_POLICY_BUNDLE_EXPORT_ENABLED",
        "AION_OPA_STATUS_CHECK_ENABLED",
        "AION_POLICY_DEFAULTS_SEED_ENABLED",
        "AION_SCENARIOS_ENABLED",
        "AION_SCENARIO_CONTROLLED_MODE_ENABLED",
        "AION_SCENARIO_DEFAULT_TIMEOUT_SECONDS",
        "AION_SCENARIO_DEFAULT_OWNER_SCOPE",
        "AION_RELEASE_BASELINE_ENABLED",
        "AION_RELEASE_PACKAGING_ENABLED",
        "AION_RELEASE_PACKAGE_OUTPUT_DIR",
        "AION_RELEASE_PACKAGE_INCLUDE_SOURCE",
        "AION_RELEASE_PACKAGE_MAX_FILE_SIZE_MB",
        "AION_RELEASE_PACKAGE_SBOM_PLACEHOLDER_ENABLED",
        "AION_RESILIENCE_ENABLED",
        "AION_CIRCUIT_BREAKERS_ENABLED",
        "AION_FAULT_INJECTION_ENABLED",
        "AION_DEGRADED_MODE_ENABLED",
        "AION_DEPENDENCY_HEALTH_ENABLED",
        "AION_RETRY_POLICY_REGISTRY_ENABLED",
        "AION_RESILIENCE_FAIL_FREEZE_ON_CRITICAL",
        "AION_LEARNING_SYNTHESIS_ENABLED",
        "AION_EXPERIENCE_LEDGER_ENABLED",
        "AION_PATTERN_MINING_ENABLED",
        "AION_LESSON_RECORDS_ENABLED",
        "AION_SKILL_SUGGESTIONS_ENABLED",
        "AION_REGRESSION_SUGGESTIONS_ENABLED",
        "AION_LEARNING_AUTO_SYNTHESIS_ENABLED",
        "AION_LEARNING_MIN_PATTERN_FREQUENCY",
        "AION_LEARNING_MIN_PATTERN_CONFIDENCE",
        "AION_LEARNING_SKILL_SUGGESTIONS_PROMOTION_ALLOWED_DEFAULT",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.env == "development"
    assert settings.service_name == "aion-brain-api"
    assert settings.version == "0.1.0"
    assert settings.database_url == "postgresql+psycopg://aion:aion_dev_password@postgres:5432/aion"
    assert settings.redis_url == "redis://redis:6379/0"
    assert settings.nats_url == "nats://nats:4222"
    assert settings.opa_url == "http://opa:8181"
    assert settings.log_level == "INFO"
    assert settings.semantic_vector_dimensions == 384
    assert settings.default_semantic_adapter == "pgvector"
    assert settings.embedding_adapter == "hash"
    assert settings.visual_default_limit == 500
    assert settings.visual_intensity_half_life_seconds == 3600
    assert settings.visual_stream_poll_interval_seconds == 1.0
    assert settings.visual_stream_max_events_default == 100
    assert settings.observability_adapter == "local"
    assert settings.api_version == "v0.1"
    assert settings.api_request_audit_enabled is True
    assert settings.api_error_detail_enabled is True
    assert settings.api_stacktrace_exposed is False
    assert settings.api_default_page_limit == 50
    assert settings.api_max_page_limit == 500
    assert settings.api_openapi_hygiene_enabled is True
    assert settings.event_reaction_router_enabled is True
    assert settings.event_auto_dispatch_enabled is False
    assert settings.event_reaction_default_mode == "dry_run"
    assert settings.event_reaction_max_actions_default == 25
    assert settings.event_dead_letter_enabled is True
    assert settings.event_replay_max_count == 3
    assert settings.policy_catalog_enabled is True
    assert settings.policy_test_harness_enabled is True
    assert settings.policy_bundle_export_enabled is True
    assert settings.opa_status_check_enabled is True
    assert settings.policy_defaults_seed_enabled is False
    assert settings.scenarios_enabled is True
    assert settings.scenario_controlled_mode_enabled is False
    assert settings.scenario_default_timeout_seconds == 30
    assert settings.scenario_default_owner_scope == "workspace:dev-workspace"
    assert settings.release_baseline_enabled is True
    assert settings.release_packaging_enabled is True
    assert settings.release_package_output_dir == "artifacts/releases"
    assert settings.release_package_include_source is True
    assert settings.release_package_max_file_size_mb == 10
    assert settings.release_package_sbom_placeholder_enabled is True
    assert settings.resilience_enabled is True
    assert settings.circuit_breakers_enabled is True
    assert settings.fault_injection_enabled is False
    assert settings.degraded_mode_enabled is True
    assert settings.dependency_health_enabled is True
    assert settings.retry_policy_registry_enabled is True
    assert settings.resilience_fail_freeze_on_critical is True
    assert settings.learning_synthesis_enabled is True
    assert settings.experience_ledger_enabled is True
    assert settings.pattern_mining_enabled is True
    assert settings.lesson_records_enabled is True
    assert settings.skill_suggestions_enabled is True
    assert settings.regression_suggestions_enabled is True
    assert settings.learning_auto_synthesis_enabled is False
    assert settings.learning_min_pattern_frequency == 2
    assert settings.learning_min_pattern_confidence == 0.6
    assert settings.learning_skill_suggestions_promotion_allowed_default is False
    assert settings.runtime_adapter == "langgraph"
    assert settings.graph_memory_adapter == "postgres_graph"
    assert settings.default_graph_memory_adapter == "postgres_graph"
    assert settings.model_gateway_adapter == "deterministic"
    assert settings.policy_adapter == "opa"
    assert settings.turbovec_enabled is False
    assert settings.turbovec_index_name == "default"
    assert settings.turbovec_index_dir == "./.aion_indexes/turbovec"
    assert settings.turbovec_bit_width == 4
    assert settings.turbovec_auto_persist is True
    assert settings.turbovec_fail_open_to_pgvector is True
    assert settings.graphiti_enabled is False
    assert settings.graphiti_config_name == "default"
    assert settings.graphiti_backend_type == "unknown"
    assert settings.graphiti_endpoint_ref is None
    assert settings.graphiti_fail_open_to_postgres_graph is True
    assert settings.mcp_enabled is False
    assert settings.mcp_allow_network is False
    assert settings.mcp_allow_stdio is False
    assert settings.mcp_timeout_seconds == 15.0
    assert settings.mcp_default_risk_level == "medium"
    assert settings.mcp_auto_register_capabilities is False
    assert settings.memory_governance_enabled is True
    assert settings.memory_decay_enabled is True
    assert settings.memory_conflict_scan_enabled is True
    assert settings.memory_compaction_enabled is True
    assert settings.memory_default_decay_half_life_days == 90
    assert settings.memory_low_confidence_threshold == 0.35
    assert settings.memory_compaction_requires_approval is False
    assert settings.memory_forgetting_requires_approval is True
    assert settings.memory_retention_sweep_limit_default == 1000


def test_settings_read_environment_variables(monkeypatch) -> None:
    """Settings read AION and infrastructure environment variables."""
    monkeypatch.setenv("AION_ENV", "test")
    monkeypatch.setenv("AION_SERVICE_NAME", "aion-test-api")
    monkeypatch.setenv("AION_VERSION", "9.9.9")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://example")
    monkeypatch.setenv("REDIS_URL", "redis://example:6379/0")
    monkeypatch.setenv("NATS_URL", "nats://example:4222")
    monkeypatch.setenv("OPA_URL", "http://example:8181")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("AION_SEMANTIC_VECTOR_DIMENSIONS", "128")
    monkeypatch.setenv("AION_DEFAULT_SEMANTIC_ADAPTER", "in-memory")
    monkeypatch.setenv("AION_EMBEDDING_ADAPTER", "hash")
    monkeypatch.setenv("AION_TURBOVEC_ENABLED", "true")
    monkeypatch.setenv("AION_TURBOVEC_INDEX_NAME", "test-index")
    monkeypatch.setenv("AION_TURBOVEC_INDEX_DIR", "/tmp/aion-turbovec")
    monkeypatch.setenv("AION_TURBOVEC_BIT_WIDTH", "8")
    monkeypatch.setenv("AION_TURBOVEC_AUTO_PERSIST", "false")
    monkeypatch.setenv("AION_TURBOVEC_FAIL_OPEN_TO_PGVECTOR", "false")
    monkeypatch.setenv("AION_GRAPHITI_ENABLED", "true")
    monkeypatch.setenv("AION_GRAPHITI_CONFIG_NAME", "test-graphiti")
    monkeypatch.setenv("AION_GRAPHITI_BACKEND_TYPE", "in_memory_fake")
    monkeypatch.setenv("AION_GRAPHITI_ENDPOINT_REF", "local-endpoint-ref")
    monkeypatch.setenv("AION_GRAPHITI_FAIL_OPEN_TO_POSTGRES_GRAPH", "false")
    monkeypatch.setenv("AION_DEFAULT_GRAPH_MEMORY_ADAPTER", "graphiti")
    monkeypatch.setenv("AION_MCP_ENABLED", "true")
    monkeypatch.setenv("AION_MCP_ALLOW_NETWORK", "true")
    monkeypatch.setenv("AION_MCP_ALLOW_STDIO", "true")
    monkeypatch.setenv("AION_MCP_TIMEOUT_SECONDS", "3.5")
    monkeypatch.setenv("AION_MCP_DEFAULT_RISK_LEVEL", "low")
    monkeypatch.setenv("AION_MCP_AUTO_REGISTER_CAPABILITIES", "true")
    monkeypatch.setenv("AION_MEMORY_GOVERNANCE_ENABLED", "false")
    monkeypatch.setenv("AION_MEMORY_DECAY_ENABLED", "false")
    monkeypatch.setenv("AION_MEMORY_CONFLICT_SCAN_ENABLED", "false")
    monkeypatch.setenv("AION_MEMORY_COMPACTION_ENABLED", "false")
    monkeypatch.setenv("AION_MEMORY_DEFAULT_DECAY_HALF_LIFE_DAYS", "45")
    monkeypatch.setenv("AION_MEMORY_LOW_CONFIDENCE_THRESHOLD", "0.25")
    monkeypatch.setenv("AION_MEMORY_COMPACTION_REQUIRES_APPROVAL", "true")
    monkeypatch.setenv("AION_MEMORY_FORGETTING_REQUIRES_APPROVAL", "false")
    monkeypatch.setenv("AION_MEMORY_RETENTION_SWEEP_LIMIT_DEFAULT", "250")
    monkeypatch.setenv("AION_API_VERSION", "v9")
    monkeypatch.setenv("AION_API_REQUEST_AUDIT_ENABLED", "false")
    monkeypatch.setenv("AION_API_ERROR_DETAIL_ENABLED", "false")
    monkeypatch.setenv("AION_API_STACKTRACE_EXPOSED", "true")
    monkeypatch.setenv("AION_API_DEFAULT_PAGE_LIMIT", "25")
    monkeypatch.setenv("AION_API_MAX_PAGE_LIMIT", "250")
    monkeypatch.setenv("AION_API_OPENAPI_HYGIENE_ENABLED", "false")
    monkeypatch.setenv("AION_SCENARIOS_ENABLED", "false")
    monkeypatch.setenv("AION_SCENARIO_CONTROLLED_MODE_ENABLED", "true")
    monkeypatch.setenv("AION_SCENARIO_DEFAULT_TIMEOUT_SECONDS", "9")
    monkeypatch.setenv("AION_SCENARIO_DEFAULT_OWNER_SCOPE", "workspace:test")
    monkeypatch.setenv("AION_RELEASE_BASELINE_ENABLED", "false")
    monkeypatch.setenv("AION_RELEASE_PACKAGING_ENABLED", "false")
    monkeypatch.setenv("AION_RELEASE_PACKAGE_OUTPUT_DIR", "artifacts/test-releases")
    monkeypatch.setenv("AION_RELEASE_PACKAGE_INCLUDE_SOURCE", "false")
    monkeypatch.setenv("AION_RELEASE_PACKAGE_MAX_FILE_SIZE_MB", "3")
    monkeypatch.setenv("AION_RELEASE_PACKAGE_SBOM_PLACEHOLDER_ENABLED", "false")
    monkeypatch.setenv("AION_RESILIENCE_ENABLED", "false")
    monkeypatch.setenv("AION_CIRCUIT_BREAKERS_ENABLED", "false")
    monkeypatch.setenv("AION_FAULT_INJECTION_ENABLED", "true")
    monkeypatch.setenv("AION_DEGRADED_MODE_ENABLED", "false")
    monkeypatch.setenv("AION_DEPENDENCY_HEALTH_ENABLED", "false")
    monkeypatch.setenv("AION_RETRY_POLICY_REGISTRY_ENABLED", "false")
    monkeypatch.setenv("AION_RESILIENCE_FAIL_FREEZE_ON_CRITICAL", "false")
    monkeypatch.setenv("AION_LEARNING_SYNTHESIS_ENABLED", "false")
    monkeypatch.setenv("AION_EXPERIENCE_LEDGER_ENABLED", "false")
    monkeypatch.setenv("AION_PATTERN_MINING_ENABLED", "false")
    monkeypatch.setenv("AION_LESSON_RECORDS_ENABLED", "false")
    monkeypatch.setenv("AION_SKILL_SUGGESTIONS_ENABLED", "false")
    monkeypatch.setenv("AION_REGRESSION_SUGGESTIONS_ENABLED", "false")
    monkeypatch.setenv("AION_LEARNING_AUTO_SYNTHESIS_ENABLED", "true")
    monkeypatch.setenv("AION_LEARNING_MIN_PATTERN_FREQUENCY", "5")
    monkeypatch.setenv("AION_LEARNING_MIN_PATTERN_CONFIDENCE", "0.85")
    monkeypatch.setenv(
        "AION_LEARNING_SKILL_SUGGESTIONS_PROMOTION_ALLOWED_DEFAULT",
        "true",
    )

    settings = Settings(_env_file=None)

    assert settings.env == "test"
    assert settings.service_name == "aion-test-api"
    assert settings.version == "9.9.9"
    assert settings.database_url == "postgresql+psycopg://example"
    assert settings.redis_url == "redis://example:6379/0"
    assert settings.nats_url == "nats://example:4222"
    assert settings.opa_url == "http://example:8181"
    assert settings.log_level == "DEBUG"
    assert settings.semantic_vector_dimensions == 128
    assert settings.default_semantic_adapter == "in-memory"
    assert settings.embedding_adapter == "hash"
    assert settings.turbovec_enabled is True
    assert settings.turbovec_index_name == "test-index"
    assert settings.turbovec_index_dir == "/tmp/aion-turbovec"
    assert settings.turbovec_bit_width == 8
    assert settings.turbovec_auto_persist is False
    assert settings.turbovec_fail_open_to_pgvector is False
    assert settings.graphiti_enabled is True
    assert settings.graphiti_config_name == "test-graphiti"
    assert settings.graphiti_backend_type == "in_memory_fake"
    assert settings.graphiti_endpoint_ref == "local-endpoint-ref"
    assert settings.graphiti_fail_open_to_postgres_graph is False
    assert settings.default_graph_memory_adapter == "graphiti"
    assert settings.mcp_enabled is True
    assert settings.mcp_allow_network is True
    assert settings.mcp_allow_stdio is True
    assert settings.mcp_timeout_seconds == 3.5
    assert settings.mcp_default_risk_level == "low"
    assert settings.mcp_auto_register_capabilities is True
    assert settings.memory_governance_enabled is False
    assert settings.memory_decay_enabled is False
    assert settings.memory_conflict_scan_enabled is False
    assert settings.memory_compaction_enabled is False
    assert settings.memory_default_decay_half_life_days == 45
    assert settings.memory_low_confidence_threshold == 0.25
    assert settings.memory_compaction_requires_approval is True
    assert settings.memory_forgetting_requires_approval is False
    assert settings.memory_retention_sweep_limit_default == 250
    assert settings.api_version == "v9"
    assert settings.api_request_audit_enabled is False
    assert settings.api_error_detail_enabled is False
    assert settings.api_stacktrace_exposed is True
    assert settings.api_default_page_limit == 25
    assert settings.api_max_page_limit == 250
    assert settings.api_openapi_hygiene_enabled is False
    assert settings.scenarios_enabled is False
    assert settings.scenario_controlled_mode_enabled is True
    assert settings.scenario_default_timeout_seconds == 9
    assert settings.scenario_default_owner_scope == "workspace:test"
    assert settings.release_baseline_enabled is False
    assert settings.release_packaging_enabled is False
    assert settings.release_package_output_dir == "artifacts/test-releases"
    assert settings.release_package_include_source is False
    assert settings.release_package_max_file_size_mb == 3
    assert settings.release_package_sbom_placeholder_enabled is False
    assert settings.resilience_enabled is False
    assert settings.circuit_breakers_enabled is False
    assert settings.fault_injection_enabled is True
    assert settings.degraded_mode_enabled is False
    assert settings.dependency_health_enabled is False
    assert settings.retry_policy_registry_enabled is False
    assert settings.resilience_fail_freeze_on_critical is False
    assert settings.learning_synthesis_enabled is False
    assert settings.experience_ledger_enabled is False
    assert settings.pattern_mining_enabled is False
    assert settings.lesson_records_enabled is False
    assert settings.skill_suggestions_enabled is False
    assert settings.regression_suggestions_enabled is False
    assert settings.learning_auto_synthesis_enabled is True
    assert settings.learning_min_pattern_frequency == 5
    assert settings.learning_min_pattern_confidence == 0.85
    assert settings.learning_skill_suggestions_promotion_allowed_default is True

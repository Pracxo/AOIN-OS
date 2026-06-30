"""Application settings for AION Brain."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    env: str = Field(default="development", validation_alias=AliasChoices("AION_ENV", "env"))
    service_name: str = Field(
        default="aion-brain-api",
        validation_alias=AliasChoices("AION_SERVICE_NAME", "service_name"),
    )
    version: str = Field(default="0.1.0", validation_alias=AliasChoices("AION_VERSION", "version"))
    database_url: str = Field(
        default="postgresql+psycopg://aion:aion_dev_password@postgres:5432/aion",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    redis_url: str = Field(
        default="redis://redis:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )
    nats_url: str = Field(
        default="nats://nats:4222",
        validation_alias=AliasChoices("NATS_URL", "nats_url"),
    )
    opa_url: str = Field(
        default="http://opa:8181",
        validation_alias=AliasChoices("OPA_URL", "opa_url"),
    )
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL", "log_level"))
    semantic_vector_dimensions: int = Field(
        default=384,
        validation_alias=AliasChoices(
            "AION_SEMANTIC_VECTOR_DIMENSIONS",
            "semantic_vector_dimensions",
        ),
    )
    default_semantic_adapter: str = Field(
        default="pgvector",
        validation_alias=AliasChoices(
            "AION_DEFAULT_SEMANTIC_ADAPTER",
            "default_semantic_adapter",
        ),
    )
    embedding_adapter: str = Field(
        default="hash",
        validation_alias=AliasChoices("AION_EMBEDDING_ADAPTER", "embedding_adapter"),
    )
    dev_auth_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_DEV_AUTH_ENABLED", "dev_auth_enabled"),
    )
    default_dev_actor_id: str = Field(
        default="dev-user",
        validation_alias=AliasChoices("AION_DEFAULT_DEV_ACTOR_ID", "default_dev_actor_id"),
    )
    default_dev_workspace_id: str = Field(
        default="dev-workspace",
        validation_alias=AliasChoices(
            "AION_DEFAULT_DEV_WORKSPACE_ID",
            "default_dev_workspace_id",
        ),
    )
    evidence_default_chunk_size_chars: int = Field(
        default=2000,
        validation_alias=AliasChoices(
            "AION_EVIDENCE_DEFAULT_CHUNK_SIZE_CHARS",
            "evidence_default_chunk_size_chars",
        ),
    )
    evidence_default_chunk_overlap_chars: int = Field(
        default=200,
        validation_alias=AliasChoices(
            "AION_EVIDENCE_DEFAULT_CHUNK_OVERLAP_CHARS",
            "evidence_default_chunk_overlap_chars",
        ),
    )
    local_object_root: str = Field(
        default="./.aion_objects",
        validation_alias=AliasChoices("AION_LOCAL_OBJECT_ROOT", "local_object_root"),
    )
    repo_root: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AION_REPO_ROOT", "repo_root"),
    )
    default_object_store: str = Field(
        default="local",
        validation_alias=AliasChoices("AION_DEFAULT_OBJECT_STORE", "default_object_store"),
    )
    visual_default_limit: int = Field(
        default=500,
        validation_alias=AliasChoices("AION_VISUAL_DEFAULT_LIMIT", "visual_default_limit"),
    )
    visual_intensity_half_life_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices(
            "AION_VISUAL_INTENSITY_HALF_LIFE_SECONDS",
            "visual_intensity_half_life_seconds",
        ),
    )
    visual_stream_poll_interval_seconds: float = Field(
        default=1.0,
        validation_alias=AliasChoices(
            "AION_VISUAL_STREAM_POLL_INTERVAL_SECONDS",
            "visual_stream_poll_interval_seconds",
        ),
    )
    visual_stream_max_events_default: int = Field(
        default=100,
        validation_alias=AliasChoices(
            "AION_VISUAL_STREAM_MAX_EVENTS_DEFAULT",
            "visual_stream_max_events_default",
        ),
    )
    observability_adapter: str = Field(
        default="local",
        validation_alias=AliasChoices("AION_OBSERVABILITY_ADAPTER", "observability_adapter"),
    )
    resource_registry_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RESOURCE_REGISTRY_ENABLED",
            "resource_registry_enabled",
        ),
    )
    resource_reference_validation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RESOURCE_REFERENCE_VALIDATION_ENABLED",
            "resource_reference_validation_enabled",
        ),
    )
    registry_rebuild_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_REGISTRY_REBUILD_ENABLED", "registry_rebuild_enabled"),
    )
    registry_snapshots_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_REGISTRY_SNAPSHOTS_ENABLED",
            "registry_snapshots_enabled",
        ),
    )
    registry_auto_index_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_REGISTRY_AUTO_INDEX_ENABLED",
            "registry_auto_index_enabled",
        ),
    )
    registry_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_REGISTRY_CREATE_NOTIFICATIONS_DEFAULT",
            "registry_create_notifications_default",
        ),
    )
    registry_create_incident_signals_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_REGISTRY_CREATE_INCIDENT_SIGNALS_DEFAULT",
            "registry_create_incident_signals_default",
        ),
    )
    registry_max_resources_per_rebuild: int = Field(
        default=5000,
        validation_alias=AliasChoices(
            "AION_REGISTRY_MAX_RESOURCES_PER_REBUILD",
            "registry_max_resources_per_rebuild",
        ),
    )
    contract_registry_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONTRACT_REGISTRY_ENABLED",
            "contract_registry_enabled",
        ),
    )
    contract_snapshot_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONTRACT_SNAPSHOT_ENABLED",
            "contract_snapshot_enabled",
        ),
    )
    compatibility_scan_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_COMPATIBILITY_SCAN_ENABLED",
            "compatibility_scan_enabled",
        ),
    )
    interface_inventory_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_INTERFACE_INVENTORY_ENABLED",
            "interface_inventory_enabled",
        ),
    )
    contract_registry_auto_snapshot_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONTRACT_REGISTRY_AUTO_SNAPSHOT_ENABLED",
            "contract_registry_auto_snapshot_enabled",
        ),
    )
    compatibility_breaking_changes_fail_freeze: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_COMPATIBILITY_BREAKING_CHANGES_FAIL_FREEZE",
            "compatibility_breaking_changes_fail_freeze",
        ),
    )
    contract_registry_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONTRACT_REGISTRY_CREATE_NOTIFICATIONS_DEFAULT",
            "contract_registry_create_notifications_default",
        ),
    )
    contract_registry_max_interfaces_per_scan: int = Field(
        default=100000,
        validation_alias=AliasChoices(
            "AION_CONTRACT_REGISTRY_MAX_INTERFACES_PER_SCAN",
            "contract_registry_max_interfaces_per_scan",
        ),
    )
    extensions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_EXTENSIONS_ENABLED", "extensions_enabled"),
    )
    extension_registry_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXTENSION_REGISTRY_ENABLED",
            "extension_registry_enabled",
        ),
    )
    extension_manifest_validation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXTENSION_MANIFEST_VALIDATION_ENABLED",
            "extension_manifest_validation_enabled",
        ),
    )
    extension_compatibility_gate_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXTENSION_COMPATIBILITY_GATE_ENABLED",
            "extension_compatibility_gate_enabled",
        ),
    )
    extension_install_plans_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXTENSION_INSTALL_PLANS_ENABLED",
            "extension_install_plans_enabled",
        ),
    )
    extension_code_loading_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXTENSION_CODE_LOADING_ENABLED",
            "extension_code_loading_enabled",
        ),
    )
    extension_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXTENSION_ACTIVATION_ENABLED",
            "extension_activation_enabled",
        ),
    )
    extension_external_sources_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXTENSION_EXTERNAL_SOURCES_ENABLED",
            "extension_external_sources_enabled",
        ),
    )
    extension_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXTENSION_CREATE_NOTIFICATIONS_DEFAULT",
            "extension_create_notifications_default",
        ),
    )
    module_slots_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_MODULE_SLOTS_ENABLED", "module_slots_enabled"),
    )
    capability_bindings_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CAPABILITY_BINDINGS_ENABLED",
            "capability_bindings_enabled",
        ),
    )
    binding_validation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_BINDING_VALIDATION_ENABLED",
            "binding_validation_enabled",
        ),
    )
    module_mount_plans_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_MOUNT_PLANS_ENABLED",
            "module_mount_plans_enabled",
        ),
    )
    route_binding_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ROUTE_BINDING_PREVIEW_ENABLED",
            "route_binding_preview_enabled",
        ),
    )
    module_slot_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_SLOT_ACTIVATION_ENABLED",
            "module_slot_activation_enabled",
        ),
    )
    capability_binding_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CAPABILITY_BINDING_ACTIVATION_ENABLED",
            "capability_binding_activation_enabled",
        ),
    )
    dynamic_route_registration_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_DYNAMIC_ROUTE_REGISTRATION_ENABLED",
            "dynamic_route_registration_enabled",
        ),
    )
    module_activation_requests_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_ACTIVATION_REQUESTS_ENABLED",
            "module_activation_requests_enabled",
        ),
    )
    module_activation_gate_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_ACTIVATION_GATE_ENABLED",
            "module_activation_gate_enabled",
        ),
    )
    module_activation_reviews_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_ACTIVATION_REVIEWS_ENABLED",
            "module_activation_reviews_enabled",
        ),
    )
    module_activation_plans_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_ACTIVATION_PLANS_ENABLED",
            "module_activation_plans_enabled",
        ),
    )
    runtime_registration_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUNTIME_REGISTRATION_PREVIEW_ENABLED",
            "runtime_registration_preview_enabled",
        ),
    )
    module_activation_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_ACTIVATION_EXECUTION_ENABLED",
            "module_activation_execution_enabled",
        ),
    )
    runtime_registration_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RUNTIME_REGISTRATION_ENABLED",
            "runtime_registration_enabled",
        ),
    )
    module_activation_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_ACTIVATION_CREATE_NOTIFICATIONS_DEFAULT",
            "module_activation_create_notifications_default",
        ),
    )
    module_binding_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_BINDING_CREATE_NOTIFICATIONS_DEFAULT",
            "module_binding_create_notifications_default",
        ),
    )
    module_mock_runtime_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_MOCK_RUNTIME_ENABLED",
            "module_mock_runtime_enabled",
        ),
    )
    module_mock_profiles_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_MOCK_PROFILES_ENABLED",
            "module_mock_profiles_enabled",
        ),
    )
    module_mock_invocation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODULE_MOCK_INVOCATION_ENABLED",
            "module_mock_invocation_enabled",
        ),
    )
    module_mock_controlled_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_MOCK_CONTROLLED_EXECUTION_ENABLED",
            "module_mock_controlled_execution_enabled",
        ),
    )
    module_mock_code_loading_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_MOCK_CODE_LOADING_ENABLED",
            "module_mock_code_loading_enabled",
        ),
    )
    module_mock_external_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_MOCK_EXTERNAL_CALLS_ENABLED",
            "module_mock_external_calls_enabled",
        ),
    )
    module_mock_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODULE_MOCK_CREATE_NOTIFICATIONS_DEFAULT",
            "module_mock_create_notifications_default",
        ),
    )
    model_provider_hardening_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODEL_PROVIDER_HARDENING_ENABLED",
            "model_provider_hardening_enabled",
        ),
    )
    model_provider_profiles_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODEL_PROVIDER_PROFILES_ENABLED",
            "model_provider_profiles_enabled",
        ),
    )
    prompt_egress_guard_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PROMPT_EGRESS_GUARD_ENABLED",
            "prompt_egress_guard_enabled",
        ),
    )
    model_provider_simulation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODEL_PROVIDER_SIMULATION_ENABLED",
            "model_provider_simulation_enabled",
        ),
    )
    model_provider_readiness_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODEL_PROVIDER_READINESS_ENABLED",
            "model_provider_readiness_enabled",
        ),
    )
    external_model_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXTERNAL_MODEL_CALLS_ENABLED",
            "external_model_calls_enabled",
        ),
    )
    model_provider_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODEL_PROVIDER_CREDENTIALS_ENABLED",
            "model_provider_credentials_enabled",
        ),
    )
    model_provider_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODEL_PROVIDER_CREATE_NOTIFICATIONS_DEFAULT",
            "model_provider_create_notifications_default",
        ),
    )
    conformance_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_CONFORMANCE_ENABLED", "conformance_enabled"),
    )
    conformance_profiles_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONFORMANCE_PROFILES_ENABLED",
            "conformance_profiles_enabled",
        ),
    )
    capability_test_vectors_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CAPABILITY_TEST_VECTORS_ENABLED",
            "capability_test_vectors_enabled",
        ),
    )
    mock_invocation_simulator_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MOCK_INVOCATION_SIMULATOR_ENABLED",
            "mock_invocation_simulator_enabled",
        ),
    )
    extension_readiness_gate_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXTENSION_READINESS_GATE_ENABLED",
            "extension_readiness_gate_enabled",
        ),
    )
    conformance_code_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONFORMANCE_CODE_EXECUTION_ENABLED",
            "conformance_code_execution_enabled",
        ),
    )
    conformance_external_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONFORMANCE_EXTERNAL_CALLS_ENABLED",
            "conformance_external_calls_enabled",
        ),
    )
    readiness_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_READINESS_ACTIVATION_ENABLED",
            "readiness_activation_enabled",
        ),
    )
    conformance_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONFORMANCE_CREATE_NOTIFICATIONS_DEFAULT",
            "conformance_create_notifications_default",
        ),
    )
    golden_path_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_GOLDEN_PATH_ENABLED", "golden_path_enabled"),
    )
    golden_path_fixture_seeding_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_GOLDEN_PATH_FIXTURE_SEEDING_ENABLED",
            "golden_path_fixture_seeding_enabled",
        ),
    )
    golden_path_release_smoke_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_GOLDEN_PATH_RELEASE_SMOKE_ENABLED",
            "golden_path_release_smoke_enabled",
        ),
    )
    golden_path_controlled_mode_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_GOLDEN_PATH_CONTROLLED_MODE_ENABLED",
            "golden_path_controlled_mode_enabled",
        ),
    )
    golden_path_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_GOLDEN_PATH_CREATE_NOTIFICATIONS_DEFAULT",
            "golden_path_create_notifications_default",
        ),
    )
    golden_path_create_operator_items_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_GOLDEN_PATH_CREATE_OPERATOR_ITEMS_DEFAULT",
            "golden_path_create_operator_items_default",
        ),
    )
    golden_path_workspace_id_default: str = Field(
        default="golden-path",
        validation_alias=AliasChoices(
            "AION_GOLDEN_PATH_WORKSPACE_ID_DEFAULT",
            "golden_path_workspace_id_default",
        ),
    )
    golden_path_release_ready_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices(
            "AION_GOLDEN_PATH_RELEASE_READY_THRESHOLD",
            "golden_path_release_ready_threshold",
        ),
    )
    bootstrap_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_BOOTSTRAP_ENABLED", "bootstrap_enabled"),
    )
    setup_doctor_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SETUP_DOCTOR_ENABLED", "setup_doctor_enabled"),
    )
    seed_bundles_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SEED_BUNDLES_ENABLED", "seed_bundles_enabled"),
    )
    bootstrap_controlled_mode_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BOOTSTRAP_CONTROLLED_MODE_ENABLED",
            "bootstrap_controlled_mode_enabled",
        ),
    )
    bootstrap_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BOOTSTRAP_CREATE_NOTIFICATIONS_DEFAULT",
            "bootstrap_create_notifications_default",
        ),
    )
    bootstrap_create_operator_items_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_BOOTSTRAP_CREATE_OPERATOR_ITEMS_DEFAULT",
            "bootstrap_create_operator_items_default",
        ),
    )
    bootstrap_local_profile_default: str = Field(
        default="local.dev",
        validation_alias=AliasChoices(
            "AION_BOOTSTRAP_LOCAL_PROFILE_DEFAULT",
            "bootstrap_local_profile_default",
        ),
    )
    bootstrap_readiness_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices(
            "AION_BOOTSTRAP_READINESS_THRESHOLD",
            "bootstrap_readiness_threshold",
        ),
    )
    bootstrap_enable_external_features: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BOOTSTRAP_ENABLE_EXTERNAL_FEATURES",
            "bootstrap_enable_external_features",
        ),
    )
    release_candidate_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RELEASE_CANDIDATE_ENABLED",
            "release_candidate_enabled",
        ),
    )
    rc_gate_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_RC_GATE_ENABLED", "rc_gate_enabled"),
    )
    rc_evidence_pack_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RC_EVIDENCE_PACK_ENABLED",
            "rc_evidence_pack_enabled",
        ),
    )
    rc_controlled_mode_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RC_CONTROLLED_MODE_ENABLED",
            "rc_controlled_mode_enabled",
        ),
    )
    rc_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RC_CREATE_NOTIFICATIONS_DEFAULT",
            "rc_create_notifications_default",
        ),
    )
    rc_create_operator_items_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RC_CREATE_OPERATOR_ITEMS_DEFAULT",
            "rc_create_operator_items_default",
        ),
    )
    rc_release_ready_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices(
            "AION_RC_RELEASE_READY_THRESHOLD",
            "rc_release_ready_threshold",
        ),
    )
    rc_fail_on_critical: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_RC_FAIL_ON_CRITICAL", "rc_fail_on_critical"),
    )
    rc_fail_on_missing_required: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RC_FAIL_ON_MISSING_REQUIRED",
            "rc_fail_on_missing_required",
        ),
    )
    lifecycle_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_LIFECYCLE_ENABLED", "lifecycle_enabled"),
    )
    retention_policy_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RETENTION_POLICY_ENABLED",
            "retention_policy_enabled",
        ),
    )
    archive_planner_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_ARCHIVE_PLANNER_ENABLED", "archive_planner_enabled"),
    )
    redaction_planner_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_REDACTION_PLANNER_ENABLED",
            "redaction_planner_enabled",
        ),
    )
    purge_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_PURGE_PREVIEW_ENABLED", "purge_preview_enabled"),
    )
    lifecycle_controlled_actions_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LIFECYCLE_CONTROLLED_ACTIONS_ENABLED",
            "lifecycle_controlled_actions_enabled",
        ),
    )
    lifecycle_hard_delete_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LIFECYCLE_HARD_DELETE_ENABLED",
            "lifecycle_hard_delete_enabled",
        ),
    )
    lifecycle_default_retention_days: int = Field(
        default=365,
        validation_alias=AliasChoices(
            "AION_LIFECYCLE_DEFAULT_RETENTION_DAYS",
            "lifecycle_default_retention_days",
        ),
    )
    lifecycle_require_backup_before_archive: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LIFECYCLE_REQUIRE_BACKUP_BEFORE_ARCHIVE",
            "lifecycle_require_backup_before_archive",
        ),
    )
    lifecycle_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LIFECYCLE_CREATE_NOTIFICATIONS_DEFAULT",
            "lifecycle_create_notifications_default",
        ),
    )
    lifecycle_create_incident_signals_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LIFECYCLE_CREATE_INCIDENT_SIGNALS_DEFAULT",
            "lifecycle_create_incident_signals_default",
        ),
    )
    run_supervision_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUN_SUPERVISION_ENABLED",
            "run_supervision_enabled",
        ),
    )
    run_control_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_RUN_CONTROL_ENABLED", "run_control_enabled"),
    )
    run_timeout_policy_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUN_TIMEOUT_POLICY_ENABLED",
            "run_timeout_policy_enabled",
        ),
    )
    run_compensation_planning_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUN_COMPENSATION_PLANNING_ENABLED",
            "run_compensation_planning_enabled",
        ),
    )
    run_supervision_background_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RUN_SUPERVISION_BACKGROUND_ENABLED",
            "run_supervision_background_enabled",
        ),
    )
    run_control_controlled_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RUN_CONTROL_CONTROLLED_ENABLED",
            "run_control_controlled_enabled",
        ),
    )
    compensation_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_COMPENSATION_EXECUTION_ENABLED",
            "compensation_execution_enabled",
        ),
    )
    run_supervision_default_stall_seconds: int = Field(
        default=900,
        validation_alias=AliasChoices(
            "AION_RUN_SUPERVISION_DEFAULT_STALL_SECONDS",
            "run_supervision_default_stall_seconds",
        ),
    )
    notifications_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_NOTIFICATIONS_ENABLED", "notifications_enabled"),
    )
    alert_router_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_ALERT_ROUTER_ENABLED", "alert_router_enabled"),
    )
    notification_subscriptions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_NOTIFICATION_SUBSCRIPTIONS_ENABLED",
            "notification_subscriptions_enabled",
        ),
    )
    escalation_queue_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_ESCALATION_QUEUE_ENABLED", "escalation_queue_enabled"),
    )
    notification_digests_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_NOTIFICATION_DIGESTS_ENABLED",
            "notification_digests_enabled",
        ),
    )
    external_notifications_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXTERNAL_NOTIFICATIONS_ENABLED",
            "external_notifications_enabled",
        ),
    )
    notification_local_delivery_only: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_NOTIFICATION_LOCAL_DELIVERY_ONLY",
            "notification_local_delivery_only",
        ),
    )
    notification_auto_create_operator_items: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_NOTIFICATION_AUTO_CREATE_OPERATOR_ITEMS",
            "notification_auto_create_operator_items",
        ),
    )
    incidents_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_INCIDENTS_ENABLED", "incidents_enabled"),
    )
    incident_signal_ingestion_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_INCIDENT_SIGNAL_INGESTION_ENABLED",
            "incident_signal_ingestion_enabled",
        ),
    )
    incident_correlation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_INCIDENT_CORRELATION_ENABLED",
            "incident_correlation_enabled",
        ),
    )
    root_cause_candidates_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ROOT_CAUSE_CANDIDATES_ENABLED",
            "root_cause_candidates_enabled",
        ),
    )
    recovery_review_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RECOVERY_REVIEW_ENABLED",
            "recovery_review_enabled",
        ),
    )
    incident_auto_create_from_alerts: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_INCIDENT_AUTO_CREATE_FROM_ALERTS",
            "incident_auto_create_from_alerts",
        ),
    )
    incident_correlation_default_window_minutes: int = Field(
        default=60,
        validation_alias=AliasChoices(
            "AION_INCIDENT_CORRELATION_DEFAULT_WINDOW_MINUTES",
            "incident_correlation_default_window_minutes",
        ),
    )
    incident_max_signals_per_run: int = Field(
        default=1000,
        validation_alias=AliasChoices(
            "AION_INCIDENT_MAX_SIGNALS_PER_RUN",
            "incident_max_signals_per_run",
        ),
    )
    recovery_review_create_actions_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RECOVERY_REVIEW_CREATE_ACTIONS_DEFAULT",
            "recovery_review_create_actions_default",
        ),
    )
    scheduler_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SCHEDULER_ENABLED", "scheduler_enabled"),
    )
    scheduler_tick_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SCHEDULER_TICK_ENABLED", "scheduler_tick_enabled"),
    )
    scheduler_background_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_SCHEDULER_BACKGROUND_ENABLED",
            "scheduler_background_enabled",
        ),
    )
    reminders_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_REMINDERS_ENABLED", "reminders_enabled"),
    )
    scheduler_create_notifications_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SCHEDULER_CREATE_NOTIFICATIONS_DEFAULT",
            "scheduler_create_notifications_default",
        ),
    )
    scheduler_create_action_proposals_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_SCHEDULER_CREATE_ACTION_PROPOSALS_DEFAULT",
            "scheduler_create_action_proposals_default",
        ),
    )
    scheduler_create_operator_items_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SCHEDULER_CREATE_OPERATOR_ITEMS_DEFAULT",
            "scheduler_create_operator_items_default",
        ),
    )
    scheduler_max_due_items_per_tick: int = Field(
        default=1000,
        validation_alias=AliasChoices(
            "AION_SCHEDULER_MAX_DUE_ITEMS_PER_TICK",
            "scheduler_max_due_items_per_tick",
        ),
    )
    scheduler_default_timezone: str = Field(
        default="UTC",
        validation_alias=AliasChoices(
            "AION_SCHEDULER_DEFAULT_TIMEZONE",
            "scheduler_default_timezone",
        ),
    )
    dialogue_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_DIALOGUE_ENABLED", "dialogue_enabled"),
    )
    response_composer_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RESPONSE_COMPOSER_ENABLED",
            "response_composer_enabled",
        ),
    )
    clarification_loop_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CLARIFICATION_LOOP_ENABLED",
            "clarification_loop_enabled",
        ),
    )
    dialogue_memory_handoff_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_DIALOGUE_MEMORY_HANDOFF_ENABLED",
            "dialogue_memory_handoff_enabled",
        ),
    )
    dialogue_store_messages: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_DIALOGUE_STORE_MESSAGES",
            "dialogue_store_messages",
        ),
    )
    dialogue_redact_sensitive_content: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_DIALOGUE_REDACT_SENSITIVE_CONTENT",
            "dialogue_redact_sensitive_content",
        ),
    )
    response_require_grounding_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RESPONSE_REQUIRE_GROUNDING_DEFAULT",
            "response_require_grounding_default",
        ),
    )
    grounding_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_GROUNDING_ENABLED", "grounding_enabled"),
    )
    citation_mapper_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CITATION_MAPPER_ENABLED",
            "citation_mapper_enabled",
        ),
    )
    grounding_verification_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_GROUNDING_VERIFICATION_ENABLED",
            "grounding_verification_enabled",
        ),
    )
    source_coverage_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SOURCE_COVERAGE_ENABLED",
            "source_coverage_enabled",
        ),
    )
    grounding_require_evidence_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_GROUNDING_REQUIRE_EVIDENCE_DEFAULT",
            "grounding_require_evidence_default",
        ),
    )
    grounding_allow_memory_only_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_GROUNDING_ALLOW_MEMORY_ONLY_DEFAULT",
            "grounding_allow_memory_only_default",
        ),
    )
    grounding_statement_split_max: int = Field(
        default=100,
        validation_alias=AliasChoices(
            "AION_GROUNDING_STATEMENT_SPLIT_MAX",
            "grounding_statement_split_max",
        ),
    )
    grounding_min_coverage_score: float = Field(
        default=0.65,
        validation_alias=AliasChoices(
            "AION_GROUNDING_MIN_COVERAGE_SCORE",
            "grounding_min_coverage_score",
        ),
    )
    explanations_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_EXPLANATIONS_ENABLED", "explanations_enabled"),
    )
    trace_narratives_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_TRACE_NARRATIVES_ENABLED",
            "trace_narratives_enabled",
        ),
    )
    why_not_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_WHY_NOT_ENABLED", "why_not_enabled"),
    )
    explanation_feedback_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXPLANATION_FEEDBACK_ENABLED",
            "explanation_feedback_enabled",
        ),
    )
    explanation_require_grounding_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXPLANATION_REQUIRE_GROUNDING_DEFAULT",
            "explanation_require_grounding_default",
        ),
    )
    explanation_max_steps_default: int = Field(
        default=50,
        validation_alias=AliasChoices(
            "AION_EXPLANATION_MAX_STEPS_DEFAULT",
            "explanation_max_steps_default",
        ),
    )
    explanation_store_records: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXPLANATION_STORE_RECORDS",
            "explanation_store_records",
        ),
    )
    explanation_forbid_hidden_reasoning: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXPLANATION_FORBID_HIDDEN_REASONING",
            "explanation_forbid_hidden_reasoning",
        ),
    )
    instructions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_INSTRUCTIONS_ENABLED", "instructions_enabled"),
    )
    preferences_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_PREFERENCES_ENABLED", "preferences_enabled"),
    )
    constraint_resolver_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONSTRAINT_RESOLVER_ENABLED",
            "constraint_resolver_enabled",
        ),
    )
    style_profiles_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_STYLE_PROFILES_ENABLED",
            "style_profiles_enabled",
        ),
    )
    instruction_conflict_detection_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_INSTRUCTION_CONFLICT_DETECTION_ENABLED",
            "instruction_conflict_detection_enabled",
        ),
    )
    preference_learning_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PREFERENCE_LEARNING_ENABLED",
            "preference_learning_enabled",
        ),
    )
    preference_auto_confirm_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_PREFERENCE_AUTO_CONFIRM_ENABLED",
            "preference_auto_confirm_enabled",
        ),
    )
    instruction_resolution_store_runs: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_INSTRUCTION_RESOLUTION_STORE_RUNS",
            "instruction_resolution_store_runs",
        ),
    )
    self_model_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SELF_MODEL_ENABLED", "self_model_enabled"),
    )
    capability_awareness_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CAPABILITY_AWARENESS_ENABLED",
            "capability_awareness_enabled",
        ),
    )
    limitation_ledger_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LIMITATION_LEDGER_ENABLED",
            "limitation_ledger_enabled",
        ),
    )
    confidence_calibration_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONFIDENCE_CALIBRATION_ENABLED",
            "confidence_calibration_enabled",
        ),
    )
    introspection_snapshots_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_INTROSPECTION_SNAPSHOTS_ENABLED",
            "introspection_snapshots_enabled",
        ),
    )
    self_assessment_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SELF_ASSESSMENT_ENABLED", "self_assessment_enabled"),
    )
    self_description_include_limitations_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SELF_DESCRIPTION_INCLUDE_LIMITATIONS_DEFAULT",
            "self_description_include_limitations_default",
        ),
    )
    confidence_low_threshold: float = Field(
        default=0.4,
        validation_alias=AliasChoices("AION_CONFIDENCE_LOW_THRESHOLD", "confidence_low_threshold"),
    )
    confidence_high_threshold: float = Field(
        default=0.75,
        validation_alias=AliasChoices(
            "AION_CONFIDENCE_HIGH_THRESHOLD",
            "confidence_high_threshold",
        ),
    )
    scenarios_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SCENARIOS_ENABLED", "scenarios_enabled"),
    )
    scenario_controlled_mode_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_SCENARIO_CONTROLLED_MODE_ENABLED",
            "scenario_controlled_mode_enabled",
        ),
    )
    scenario_default_timeout_seconds: int = Field(
        default=30,
        validation_alias=AliasChoices(
            "AION_SCENARIO_DEFAULT_TIMEOUT_SECONDS",
            "scenario_default_timeout_seconds",
        ),
    )
    scenario_default_owner_scope: str = Field(
        default="workspace:dev-workspace",
        validation_alias=AliasChoices(
            "AION_SCENARIO_DEFAULT_OWNER_SCOPE",
            "scenario_default_owner_scope",
        ),
    )
    release_baseline_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RELEASE_BASELINE_ENABLED",
            "release_baseline_enabled",
        ),
    )
    aion_release_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("AION_RELEASE_VERSION", "aion_release_version"),
    )
    aion_release_channel: str = Field(
        default="alpha",
        validation_alias=AliasChoices("AION_RELEASE_CHANNEL", "aion_release_channel"),
    )
    versioning_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_VERSIONING_ENABLED", "versioning_enabled"),
    )
    freeze_gate_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_FREEZE_GATE_ENABLED", "freeze_gate_enabled"),
    )
    compatibility_matrix_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_COMPATIBILITY_MATRIX_ENABLED",
            "compatibility_matrix_enabled",
        ),
    )
    release_artifact_manifest_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RELEASE_ARTIFACT_MANIFEST_ENABLED",
            "release_artifact_manifest_enabled",
        ),
    )
    migration_baseline_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MIGRATION_BASELINE_ENABLED",
            "migration_baseline_enabled",
        ),
    )
    release_packaging_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RELEASE_PACKAGING_ENABLED",
            "release_packaging_enabled",
        ),
    )
    release_package_output_dir: str = Field(
        default="artifacts/releases",
        validation_alias=AliasChoices(
            "AION_RELEASE_PACKAGE_OUTPUT_DIR",
            "release_package_output_dir",
        ),
    )
    release_package_include_source: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RELEASE_PACKAGE_INCLUDE_SOURCE",
            "release_package_include_source",
        ),
    )
    release_package_max_file_size_mb: int = Field(
        default=10,
        gt=0,
        validation_alias=AliasChoices(
            "AION_RELEASE_PACKAGE_MAX_FILE_SIZE_MB",
            "release_package_max_file_size_mb",
        ),
    )
    release_package_sbom_placeholder_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RELEASE_PACKAGE_SBOM_PLACEHOLDER_ENABLED",
            "release_package_sbom_placeholder_enabled",
        ),
    )
    backups_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_BACKUPS_ENABLED", "backups_enabled"),
    )
    backup_output_dir: str = Field(
        default="artifacts/backups",
        validation_alias=AliasChoices("AION_BACKUP_OUTPUT_DIR", "backup_output_dir"),
    )
    backup_default_redaction_mode: str = Field(
        default="redact_sensitive",
        validation_alias=AliasChoices(
            "AION_BACKUP_DEFAULT_REDACTION_MODE",
            "backup_default_redaction_mode",
        ),
    )
    backup_restore_apply_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BACKUP_RESTORE_APPLY_ENABLED",
            "backup_restore_apply_enabled",
        ),
    )
    backup_max_records_per_resource_default: int = Field(
        default=100000,
        validation_alias=AliasChoices(
            "AION_BACKUP_MAX_RECORDS_PER_RESOURCE_DEFAULT",
            "backup_max_records_per_resource_default",
        ),
    )
    backup_include_visual_telemetry_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BACKUP_INCLUDE_VISUAL_TELEMETRY_DEFAULT",
            "backup_include_visual_telemetry_default",
        ),
    )
    performance_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_PERFORMANCE_ENABLED", "performance_enabled"),
    )
    benchmark_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_BENCHMARK_ENABLED", "benchmark_enabled"),
    )
    benchmark_controlled_mode_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BENCHMARK_CONTROLLED_MODE_ENABLED",
            "benchmark_controlled_mode_enabled",
        ),
    )
    performance_sample_api_requests: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PERFORMANCE_SAMPLE_API_REQUESTS",
            "performance_sample_api_requests",
        ),
    )
    performance_default_threshold_ms: int = Field(
        default=1000,
        gt=0,
        validation_alias=AliasChoices(
            "AION_PERFORMANCE_DEFAULT_THRESHOLD_MS",
            "performance_default_threshold_ms",
        ),
    )
    performance_baseline_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices(
            "AION_PERFORMANCE_BASELINE_VERSION",
            "performance_baseline_version",
        ),
    )
    security_baseline_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SECURITY_BASELINE_ENABLED",
            "security_baseline_enabled",
        ),
    )
    secret_scanner_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SECRET_SCANNER_ENABLED", "secret_scanner_enabled"),
    )
    hardening_gate_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_HARDENING_GATE_ENABLED", "hardening_gate_enabled"),
    )
    runtime_config_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_RUNTIME_CONFIG_ENABLED", "runtime_config_enabled"),
    )
    runtime_feature_overrides_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUNTIME_FEATURE_OVERRIDES_ENABLED",
            "runtime_feature_overrides_enabled",
        ),
    )
    runtime_config_mutation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUNTIME_CONFIG_MUTATION_ENABLED",
            "runtime_config_mutation_enabled",
        ),
    )
    runtime_config_snapshot_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUNTIME_CONFIG_SNAPSHOT_ENABLED",
            "runtime_config_snapshot_enabled",
        ),
    )
    runtime_config_safe_defaults_required: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUNTIME_CONFIG_SAFE_DEFAULTS_REQUIRED",
            "runtime_config_safe_defaults_required",
        ),
    )
    runtime_config_allow_sensitive_values: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_RUNTIME_CONFIG_ALLOW_SENSITIVE_VALUES",
            "runtime_config_allow_sensitive_values",
        ),
    )
    resilience_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_RESILIENCE_ENABLED", "resilience_enabled"),
    )
    circuit_breakers_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_CIRCUIT_BREAKERS_ENABLED", "circuit_breakers_enabled"),
    )
    fault_injection_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_FAULT_INJECTION_ENABLED", "fault_injection_enabled"),
    )
    degraded_mode_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_DEGRADED_MODE_ENABLED", "degraded_mode_enabled"),
    )
    dependency_health_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_DEPENDENCY_HEALTH_ENABLED",
            "dependency_health_enabled",
        ),
    )
    retry_policy_registry_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RETRY_POLICY_REGISTRY_ENABLED",
            "retry_policy_registry_enabled",
        ),
    )
    resilience_fail_freeze_on_critical: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RESILIENCE_FAIL_FREEZE_ON_CRITICAL",
            "resilience_fail_freeze_on_critical",
        ),
    )
    audit_integrity_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_AUDIT_INTEGRITY_ENABLED",
            "audit_integrity_enabled",
        ),
    )
    audit_hash_algorithm: str = Field(
        default="sha256",
        validation_alias=AliasChoices("AION_AUDIT_HASH_ALGORITHM", "audit_hash_algorithm"),
    )
    audit_export_output_dir: str = Field(
        default="artifacts/audit",
        validation_alias=AliasChoices(
            "AION_AUDIT_EXPORT_OUTPUT_DIR",
            "audit_export_output_dir",
        ),
    )
    audit_checkpoint_interval: int = Field(
        default=1000,
        validation_alias=AliasChoices(
            "AION_AUDIT_CHECKPOINT_INTERVAL",
            "audit_checkpoint_interval",
        ),
    )
    audit_record_payloads: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_AUDIT_RECORD_PAYLOADS", "audit_record_payloads"),
    )
    audit_redact_sensitive_payloads: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_AUDIT_REDACT_SENSITIVE_PAYLOADS",
            "audit_redact_sensitive_payloads",
        ),
    )
    audit_fail_closed_on_integrity_error: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_AUDIT_FAIL_CLOSED_ON_INTEGRITY_ERROR",
            "audit_fail_closed_on_integrity_error",
        ),
    )
    operator_control_tower_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONTROL_TOWER_ENABLED",
            "operator_control_tower_enabled",
        ),
    )
    operator_snapshot_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_SNAPSHOT_ENABLED",
            "operator_snapshot_enabled",
        ),
    )
    operator_action_center_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTION_CENTER_ENABLED",
            "operator_action_center_enabled",
        ),
    )
    operator_acknowledgements_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACKNOWLEDGEMENTS_ENABLED",
            "operator_acknowledgements_enabled",
        ),
    )
    operator_max_action_items_default: int = Field(
        default=100,
        validation_alias=AliasChoices(
            "AION_OPERATOR_MAX_ACTION_ITEMS_DEFAULT",
            "operator_max_action_items_default",
        ),
    )
    operator_max_queue_items_default: int = Field(
        default=100,
        validation_alias=AliasChoices(
            "AION_OPERATOR_MAX_QUEUE_ITEMS_DEFAULT",
            "operator_max_queue_items_default",
        ),
    )
    operator_console_view_models_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONSOLE_VIEW_MODELS_ENABLED",
            "operator_console_view_models_enabled",
        ),
    )
    operator_console_contract_audit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONSOLE_CONTRACT_AUDIT_ENABLED",
            "operator_console_contract_audit_enabled",
        ),
    )
    operator_console_read_only: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONSOLE_READ_ONLY",
            "operator_console_read_only",
        ),
    )
    operator_console_write_actions_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONSOLE_WRITE_ACTIONS_ENABLED",
            "operator_console_write_actions_enabled",
        ),
    )
    operator_console_frontend_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONSOLE_FRONTEND_ENABLED",
            "operator_console_frontend_enabled",
        ),
    )
    operator_console_redaction_required: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONSOLE_REDACTION_REQUIRED",
            "operator_console_redaction_required",
        ),
    )
    operator_console_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OPERATOR_CONSOLE_CREATE_NOTIFICATIONS_DEFAULT",
            "operator_console_create_notifications_default",
        ),
    )
    local_auth_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_LOCAL_AUTH_ENABLED", "local_auth_enabled"),
    )
    local_auth_dev_identity_simulation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_AUTH_DEV_IDENTITY_SIMULATION_ENABLED",
            "local_auth_dev_identity_simulation_enabled",
        ),
    )
    local_auth_role_filtering_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_AUTH_ROLE_FILTERING_ENABLED",
            "local_auth_role_filtering_enabled",
        ),
    )
    local_auth_role_matrix_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_AUTH_ROLE_MATRIX_ENABLED",
            "local_auth_role_matrix_enabled",
        ),
    )
    local_auth_role_access_audit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_AUTH_ROLE_ACCESS_AUDIT_ENABLED",
            "local_auth_role_access_audit_enabled",
        ),
    )
    local_auth_audit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_AUTH_AUDIT_ENABLED",
            "local_auth_audit_enabled",
        ),
    )
    production_auth_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_PRODUCTION_AUTH_ENABLED", "production_auth_enabled"),
    )
    auth_runtime_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_AUTH_RUNTIME_ENABLED", "auth_runtime_enabled"),
    )
    auth_runtime_mock_claims_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_MOCK_CLAIMS_PREVIEW_ENABLED",
            "auth_runtime_mock_claims_preview_enabled",
        ),
    )
    auth_runtime_actor_mapping_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_ACTOR_MAPPING_PREVIEW_ENABLED",
            "auth_runtime_actor_mapping_preview_enabled",
        ),
    )
    auth_runtime_external_identity_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_EXTERNAL_IDENTITY_ENABLED",
            "auth_runtime_external_identity_enabled",
        ),
    )
    auth_runtime_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_CREDENTIALS_ENABLED",
            "auth_runtime_credentials_enabled",
        ),
    )
    auth_runtime_token_issuance_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_TOKEN_ISSUANCE_ENABLED",
            "auth_runtime_token_issuance_enabled",
        ),
    )
    auth_runtime_cookie_issuance_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_COOKIE_ISSUANCE_ENABLED",
            "auth_runtime_cookie_issuance_enabled",
        ),
    )
    auth_runtime_session_persistence_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_SESSION_PERSISTENCE_ENABLED",
            "auth_runtime_session_persistence_enabled",
        ),
    )
    auth_runtime_login_endpoint_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_LOGIN_ENDPOINT_ENABLED",
            "auth_runtime_login_endpoint_enabled",
        ),
    )
    auth_runtime_logout_endpoint_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_RUNTIME_LOGOUT_ENDPOINT_ENABLED",
            "auth_runtime_logout_endpoint_enabled",
        ),
    )
    connector_runtime_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_RUNTIME_ENABLED",
            "connector_runtime_enabled",
        ),
    )
    connector_mock_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_MOCK_PREVIEW_ENABLED",
            "connector_mock_preview_enabled",
        ),
    )
    connector_egress_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_EGRESS_PREVIEW_ENABLED",
            "connector_egress_preview_enabled",
        ),
    )
    connector_ingress_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_INGRESS_PREVIEW_ENABLED",
            "connector_ingress_preview_enabled",
        ),
    )
    connector_external_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_EXTERNAL_CALLS_ENABLED",
            "connector_external_calls_enabled",
        ),
    )
    connector_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_CREDENTIALS_ENABLED",
            "connector_credentials_enabled",
        ),
    )
    connector_token_storage_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_TOKEN_STORAGE_ENABLED",
            "connector_token_storage_enabled",
        ),
    )
    connector_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_ACTIVATION_ENABLED",
            "connector_activation_enabled",
        ),
    )
    connector_route_registration_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_ROUTE_REGISTRATION_ENABLED",
            "connector_route_registration_enabled",
        ),
    )
    connector_simulator_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SIMULATOR_ENABLED",
            "connector_simulator_enabled",
        ),
    )
    connector_dry_run_simulation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_DRY_RUN_SIMULATION_ENABLED",
            "connector_dry_run_simulation_enabled",
        ),
    )
    connector_replay_fixtures_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_REPLAY_FIXTURES_ENABLED",
            "connector_replay_fixtures_enabled",
        ),
    )
    connector_policy_readiness_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_READINESS_ENABLED",
            "connector_policy_readiness_enabled",
        ),
    )
    connector_simulator_external_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SIMULATOR_EXTERNAL_CALLS_ENABLED",
            "connector_simulator_external_calls_enabled",
        ),
    )
    connector_simulator_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SIMULATOR_CREDENTIALS_ENABLED",
            "connector_simulator_credentials_enabled",
        ),
    )
    connector_simulator_tokens_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SIMULATOR_TOKENS_ENABLED",
            "connector_simulator_tokens_enabled",
        ),
    )
    connector_simulator_runtime_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SIMULATOR_RUNTIME_ACTIVATION_ENABLED",
            "connector_simulator_runtime_activation_enabled",
        ),
    )
    connector_policy_catalog_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_CATALOG_ENABLED",
            "connector_policy_catalog_enabled",
        ),
    )
    connector_policy_dry_run_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_DRY_RUN_ENABLED",
            "connector_policy_dry_run_enabled",
        ),
    )
    connector_policy_runtime_allow_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_RUNTIME_ALLOW_ENABLED",
            "connector_policy_runtime_allow_enabled",
        ),
    )
    connector_policy_external_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_EXTERNAL_CALLS_ENABLED",
            "connector_policy_external_calls_enabled",
        ),
    )
    connector_policy_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_CREDENTIALS_ENABLED",
            "connector_policy_credentials_enabled",
        ),
    )
    connector_policy_tokens_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_TOKENS_ENABLED",
            "connector_policy_tokens_enabled",
        ),
    )
    connector_policy_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_POLICY_ACTIVATION_ENABLED",
            "connector_policy_activation_enabled",
        ),
    )
    connector_sandbox_design_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_DESIGN_ENABLED",
            "connector_sandbox_design_enabled",
        ),
    )
    connector_sandbox_readiness_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_READINESS_ENABLED",
            "connector_sandbox_readiness_enabled",
        ),
    )
    connector_sandbox_runtime_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_RUNTIME_EXECUTION_ENABLED",
            "connector_sandbox_runtime_execution_enabled",
        ),
    )
    connector_sandbox_filesystem_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_FILESYSTEM_ENABLED",
            "connector_sandbox_filesystem_enabled",
        ),
    )
    connector_sandbox_network_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_NETWORK_ENABLED",
            "connector_sandbox_network_enabled",
        ),
    )
    connector_sandbox_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_CREDENTIALS_ENABLED",
            "connector_sandbox_credentials_enabled",
        ),
    )
    connector_sandbox_tokens_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_TOKENS_ENABLED",
            "connector_sandbox_tokens_enabled",
        ),
    )
    connector_sandbox_process_spawn_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_PROCESS_SPAWN_ENABLED",
            "connector_sandbox_process_spawn_enabled",
        ),
    )
    connector_sandbox_dynamic_import_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_DYNAMIC_IMPORT_ENABLED",
            "connector_sandbox_dynamic_import_enabled",
        ),
    )
    connector_sandbox_package_install_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_PACKAGE_INSTALL_ENABLED",
            "connector_sandbox_package_install_enabled",
        ),
    )
    connector_sandbox_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SANDBOX_ACTIVATION_ENABLED",
            "connector_sandbox_activation_enabled",
        ),
    )
    connector_credentials_architecture_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_CREDENTIALS_ARCHITECTURE_ENABLED",
            "connector_credentials_architecture_enabled",
        ),
    )
    connector_credentials_readiness_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_CREDENTIALS_READINESS_ENABLED",
            "connector_credentials_readiness_enabled",
        ),
    )
    connector_credentials_redaction_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_CREDENTIALS_REDACTION_PREVIEW_ENABLED",
            "connector_credentials_redaction_preview_enabled",
        ),
    )
    connector_credentials_storage_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_CREDENTIALS_STORAGE_ENABLED",
            "connector_credentials_storage_enabled",
        ),
    )
    connector_tokens_storage_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_TOKENS_STORAGE_ENABLED",
            "connector_tokens_storage_enabled",
        ),
    )
    connector_secret_material_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_SECRET_MATERIAL_ENABLED",
            "connector_secret_material_enabled",
        ),
    )
    connector_external_identity_runtime_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_EXTERNAL_IDENTITY_RUNTIME_ENABLED",
            "connector_external_identity_runtime_enabled",
        ),
    )
    connector_runtime_credential_access_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_RUNTIME_CREDENTIAL_ACCESS_ENABLED",
            "connector_runtime_credential_access_enabled",
        ),
    )
    auth_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTH_CREDENTIALS_ENABLED",
            "auth_credentials_enabled",
        ),
    )
    auth_sessions_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_AUTH_SESSIONS_ENABLED", "auth_sessions_enabled"),
    )
    external_identity_provider_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EXTERNAL_IDENTITY_PROVIDER_ENABLED",
            "external_identity_provider_enabled",
        ),
    )
    local_auth_write_actions_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_AUTH_WRITE_ACTIONS_ENABLED",
            "local_auth_write_actions_enabled",
        ),
    )
    local_session_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_PREVIEW_ENABLED",
            "local_session_preview_enabled",
        ),
    )
    local_session_context_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_CONTEXT_ENABLED",
            "local_session_context_enabled",
        ),
    )
    local_session_audit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_AUDIT_ENABLED",
            "local_session_audit_enabled",
        ),
    )
    local_session_dev_only: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_LOCAL_SESSION_DEV_ONLY", "local_session_dev_only"),
    )
    local_session_read_only: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_LOCAL_SESSION_READ_ONLY", "local_session_read_only"),
    )
    local_session_credentials_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_CREDENTIALS_ENABLED",
            "local_session_credentials_enabled",
        ),
    )
    local_session_tokens_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_TOKENS_ENABLED",
            "local_session_tokens_enabled",
        ),
    )
    local_session_cookies_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_COOKIES_ENABLED",
            "local_session_cookies_enabled",
        ),
    )
    local_session_persistence_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_PERSISTENCE_ENABLED",
            "local_session_persistence_enabled",
        ),
    )
    local_session_write_actions_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_WRITE_ACTIONS_ENABLED",
            "local_session_write_actions_enabled",
        ),
    )
    local_session_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_EXECUTION_ENABLED",
            "local_session_execution_enabled",
        ),
    )
    local_session_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_ACTIVATION_ENABLED",
            "local_session_activation_enabled",
        ),
    )
    local_session_external_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LOCAL_SESSION_EXTERNAL_CALLS_ENABLED",
            "local_session_external_calls_enabled",
        ),
    )
    action_authorization_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ACTION_AUTHORIZATION_ENABLED",
            "action_authorization_enabled",
        ),
    )
    dry_run_action_authorization_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_DRY_RUN_ACTION_AUTHORIZATION_ENABLED",
            "dry_run_action_authorization_enabled",
        ),
    )
    action_authorization_audit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ACTION_AUTHORIZATION_AUDIT_ENABLED",
            "action_authorization_audit_enabled",
        ),
    )
    action_authorization_write_allowed: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ACTION_AUTHORIZATION_WRITE_ALLOWED",
            "action_authorization_write_allowed",
        ),
    )
    action_authorization_execution_allowed: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ACTION_AUTHORIZATION_EXECUTION_ALLOWED",
            "action_authorization_execution_allowed",
        ),
    )
    action_authorization_activation_allowed: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ACTION_AUTHORIZATION_ACTIVATION_ALLOWED",
            "action_authorization_activation_allowed",
        ),
    )
    action_authorization_external_calls_allowed: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ACTION_AUTHORIZATION_EXTERNAL_CALLS_ALLOWED",
            "action_authorization_external_calls_allowed",
        ),
    )
    operator_actions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTIONS_ENABLED",
            "operator_actions_enabled",
        ),
    )
    operator_action_previews_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTION_PREVIEWS_ENABLED",
            "operator_action_previews_enabled",
        ),
    )
    operator_action_reviews_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTION_REVIEWS_ENABLED",
            "operator_action_reviews_enabled",
        ),
    )
    operator_action_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTION_EXECUTION_ENABLED",
            "operator_action_execution_enabled",
        ),
    )
    operator_action_external_calls_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTION_EXTERNAL_CALLS_ENABLED",
            "operator_action_external_calls_enabled",
        ),
    )
    operator_action_activation_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTION_ACTIVATION_ENABLED",
            "operator_action_activation_enabled",
        ),
    )
    operator_action_create_notifications_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OPERATOR_ACTION_CREATE_NOTIFICATIONS_DEFAULT",
            "operator_action_create_notifications_default",
        ),
    )
    security_scan_max_file_size_mb: int = Field(
        default=5,
        ge=1,
        le=50,
        validation_alias=AliasChoices(
            "AION_SECURITY_SCAN_MAX_FILE_SIZE_MB",
            "security_scan_max_file_size_mb",
        ),
    )
    security_fail_on_high_findings: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SECURITY_FAIL_ON_HIGH_FINDINGS",
            "security_fail_on_high_findings",
        ),
    )
    security_allow_secret_scan_ignore_comments: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SECURITY_ALLOW_SECRET_SCAN_IGNORE_COMMENTS",
            "security_allow_secret_scan_ignore_comments",
        ),
    )
    resource_budget_enforcement_default: str = Field(
        default="report_only",
        validation_alias=AliasChoices(
            "AION_RESOURCE_BUDGET_ENFORCEMENT_DEFAULT",
            "resource_budget_enforcement_default",
        ),
    )
    api_version: str = Field(
        default="v0.1",
        validation_alias=AliasChoices("AION_API_VERSION", "api_version"),
    )
    api_request_audit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_API_REQUEST_AUDIT_ENABLED",
            "api_request_audit_enabled",
        ),
    )
    api_error_detail_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_API_ERROR_DETAIL_ENABLED", "api_error_detail_enabled"),
    )
    api_stacktrace_exposed: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_API_STACKTRACE_EXPOSED",
            "api_stacktrace_exposed",
        ),
    )
    api_default_page_limit: int = Field(
        default=50,
        validation_alias=AliasChoices("AION_API_DEFAULT_PAGE_LIMIT", "api_default_page_limit"),
    )
    api_max_page_limit: int = Field(
        default=500,
        validation_alias=AliasChoices("AION_API_MAX_PAGE_LIMIT", "api_max_page_limit"),
    )
    api_openapi_hygiene_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_API_OPENAPI_HYGIENE_ENABLED",
            "api_openapi_hygiene_enabled",
        ),
    )
    event_reaction_router_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EVENT_REACTION_ROUTER_ENABLED",
            "event_reaction_router_enabled",
        ),
    )
    event_auto_dispatch_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_EVENT_AUTO_DISPATCH_ENABLED",
            "event_auto_dispatch_enabled",
        ),
    )
    event_reaction_default_mode: str = Field(
        default="dry_run",
        validation_alias=AliasChoices(
            "AION_EVENT_REACTION_DEFAULT_MODE",
            "event_reaction_default_mode",
        ),
    )
    event_reaction_max_actions_default: int = Field(
        default=25,
        validation_alias=AliasChoices(
            "AION_EVENT_REACTION_MAX_ACTIONS_DEFAULT",
            "event_reaction_max_actions_default",
        ),
    )
    event_dead_letter_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EVENT_DEAD_LETTER_ENABLED",
            "event_dead_letter_enabled",
        ),
    )
    event_replay_max_count: int = Field(
        default=3,
        validation_alias=AliasChoices("AION_EVENT_REPLAY_MAX_COUNT", "event_replay_max_count"),
    )
    command_bus_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_COMMAND_BUS_ENABLED", "command_bus_enabled"),
    )
    idempotency_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_IDEMPOTENCY_ENABLED", "idempotency_enabled"),
    )
    idempotency_default_ttl_seconds: int = Field(
        default=86400,
        validation_alias=AliasChoices(
            "AION_IDEMPOTENCY_DEFAULT_TTL_SECONDS",
            "idempotency_default_ttl_seconds",
        ),
    )
    outbox_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_OUTBOX_ENABLED", "outbox_enabled"),
    )
    outbox_process_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OUTBOX_PROCESS_ENABLED",
            "outbox_process_enabled",
        ),
    )
    outbox_default_max_attempts: int = Field(
        default=3,
        validation_alias=AliasChoices(
            "AION_OUTBOX_DEFAULT_MAX_ATTEMPTS",
            "outbox_default_max_attempts",
        ),
    )
    inbox_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_INBOX_ENABLED", "inbox_enabled"),
    )
    processing_lease_ttl_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices(
            "AION_PROCESSING_LEASE_TTL_SECONDS",
            "processing_lease_ttl_seconds",
        ),
    )
    consistency_checker_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONSISTENCY_CHECKER_ENABLED",
            "consistency_checker_enabled",
        ),
    )
    runtime_adapter: str = Field(
        default="langgraph",
        validation_alias=AliasChoices("AION_RUNTIME_ADAPTER", "runtime_adapter"),
    )
    graph_memory_adapter: str = Field(
        default="postgres_graph",
        validation_alias=AliasChoices("AION_GRAPH_MEMORY_ADAPTER", "graph_memory_adapter"),
    )
    default_graph_memory_adapter: str = Field(
        default="postgres_graph",
        validation_alias=AliasChoices(
            "AION_DEFAULT_GRAPH_MEMORY_ADAPTER",
            "AION_GRAPH_MEMORY_ADAPTER",
            "default_graph_memory_adapter",
            "graph_memory_adapter",
        ),
    )
    model_gateway_adapter: str = Field(
        default="deterministic",
        validation_alias=AliasChoices("AION_MODEL_GATEWAY_ADAPTER", "model_gateway_adapter"),
    )
    model_gateway_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_ENABLED",
            "model_gateway_enabled",
        ),
    )
    model_gateway_default_provider: str = Field(
        default="deterministic",
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_DEFAULT_PROVIDER",
            "model_gateway_default_provider",
        ),
    )
    model_gateway_default_profile: str = Field(
        default="aion-deterministic-v0",
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_DEFAULT_PROFILE",
            "model_gateway_default_profile",
        ),
    )
    model_gateway_allow_external_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_ALLOW_EXTERNAL_DEFAULT",
            "model_gateway_allow_external_default",
        ),
    )
    model_gateway_timeout_seconds: float = Field(
        default=30.0,
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_TIMEOUT_SECONDS",
            "model_gateway_timeout_seconds",
        ),
    )
    model_gateway_max_input_tokens_default: int = Field(
        default=8000,
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_MAX_INPUT_TOKENS_DEFAULT",
            "model_gateway_max_input_tokens_default",
        ),
    )
    model_gateway_max_output_tokens_default: int = Field(
        default=1000,
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_MAX_OUTPUT_TOKENS_DEFAULT",
            "model_gateway_max_output_tokens_default",
        ),
    )
    model_gateway_daily_budget_default: float = Field(
        default=0.0,
        validation_alias=AliasChoices(
            "AION_MODEL_GATEWAY_DAILY_BUDGET_DEFAULT",
            "model_gateway_daily_budget_default",
        ),
    )
    model_outputs_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_MODEL_OUTPUTS_ENABLED", "model_outputs_enabled"),
    )
    output_governance_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OUTPUT_GOVERNANCE_ENABLED",
            "output_governance_enabled",
        ),
    )
    structured_output_validation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_STRUCTURED_OUTPUT_VALIDATION_ENABLED",
            "structured_output_validation_enabled",
        ),
    )
    model_output_store_raw: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MODEL_OUTPUT_STORE_RAW",
            "model_output_store_raw",
        ),
    )
    model_output_redaction_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODEL_OUTPUT_REDACTION_ENABLED",
            "model_output_redaction_enabled",
        ),
    )
    tool_intent_capture_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_TOOL_INTENT_CAPTURE_ENABLED",
            "tool_intent_capture_enabled",
        ),
    )
    tool_intent_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_TOOL_INTENT_EXECUTION_ENABLED",
            "tool_intent_execution_enabled",
        ),
    )
    output_governance_require_grounding_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OUTPUT_GOVERNANCE_REQUIRE_GROUNDING_DEFAULT",
            "output_governance_require_grounding_default",
        ),
    )
    output_governance_block_tool_intents_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OUTPUT_GOVERNANCE_BLOCK_TOOL_INTENTS_DEFAULT",
            "output_governance_block_tool_intents_default",
        ),
    )
    action_proposals_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ACTION_PROPOSALS_ENABLED",
            "action_proposals_enabled",
        ),
    )
    tool_intent_review_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_TOOL_INTENT_REVIEW_ENABLED",
            "tool_intent_review_enabled",
        ),
    )
    execution_handoff_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXECUTION_HANDOFF_ENABLED",
            "execution_handoff_enabled",
        ),
    )
    action_proposal_auto_create_from_tool_intent: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ACTION_PROPOSAL_AUTO_CREATE_FROM_TOOL_INTENT",
            "action_proposal_auto_create_from_tool_intent",
        ),
    )
    action_handoff_controlled_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ACTION_HANDOFF_CONTROLLED_ENABLED",
            "action_handoff_controlled_enabled",
        ),
    )
    action_handoff_requires_approval_default: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ACTION_HANDOFF_REQUIRES_APPROVAL_DEFAULT",
            "action_handoff_requires_approval_default",
        ),
    )
    action_proposal_external_targets_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ACTION_PROPOSAL_EXTERNAL_TARGETS_ENABLED",
            "action_proposal_external_targets_enabled",
        ),
    )
    litellm_base_url: str = Field(
        default="http://litellm:4000",
        validation_alias=AliasChoices("AION_LITELLM_BASE_URL", "litellm_base_url"),
    )
    openai_compatible_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AION_OPENAI_COMPATIBLE_BASE_URL",
            "openai_compatible_base_url",
        ),
    )
    prompt_redaction_block_on_secret: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PROMPT_REDACTION_BLOCK_ON_SECRET",
            "prompt_redaction_block_on_secret",
        ),
    )
    prompts_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_PROMPTS_ENABLED", "prompts_enabled"),
    )
    prompt_compiler_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PROMPT_PACKET_COMPILER_ENABLED",
            "AION_PROMPT_COMPILER_ENABLED",
            "prompt_compiler_enabled",
        ),
    )
    prompt_boundary_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PROMPT_BOUNDARY_GUARD_ENABLED",
            "AION_PROMPT_BOUNDARY_ENABLED",
            "prompt_boundary_enabled",
        ),
    )
    prompt_store_packets: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_PROMPT_STORE_PACKETS", "prompt_store_packets"),
    )
    prompt_store_rendered_text: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_PROMPT_STORE_RENDERED_TEXT",
            "prompt_store_rendered_text",
        ),
    )
    prompt_preview_default_redaction_level: str = Field(
        default="safe",
        validation_alias=AliasChoices(
            "AION_PROMPT_PREVIEW_DEFAULT_REDACTION_LEVEL",
            "prompt_preview_default_redaction_level",
        ),
    )
    prompt_preview_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_PROMPT_PREVIEW_ENABLED", "prompt_preview_enabled"),
    )
    prompt_default_max_chars: int = Field(
        default=12000,
        validation_alias=AliasChoices("AION_PROMPT_DEFAULT_MAX_CHARS", "prompt_default_max_chars"),
    )
    prompt_injection_detection_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PROMPT_INJECTION_DETECTION_ENABLED",
            "prompt_injection_detection_enabled",
        ),
    )
    prompt_injection_block_high_severity: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PROMPT_INJECTION_BLOCK_HIGH_SEVERITY",
            "prompt_injection_block_high_severity",
        ),
    )
    model_input_manifest_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODEL_INPUT_MANIFEST_ENABLED",
            "model_input_manifest_enabled",
        ),
    )
    model_input_manifest_store_hashes_only: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MODEL_INPUT_MANIFEST_STORE_HASHES_ONLY",
            "model_input_manifest_store_hashes_only",
        ),
    )
    turbovec_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_TURBOVEC_ENABLED", "turbovec_enabled"),
    )
    turbovec_index_name: str = Field(
        default="default",
        validation_alias=AliasChoices("AION_TURBOVEC_INDEX_NAME", "turbovec_index_name"),
    )
    turbovec_index_dir: str = Field(
        default="./.aion_indexes/turbovec",
        validation_alias=AliasChoices("AION_TURBOVEC_INDEX_DIR", "turbovec_index_dir"),
    )
    turbovec_bit_width: int = Field(
        default=4,
        validation_alias=AliasChoices("AION_TURBOVEC_BIT_WIDTH", "turbovec_bit_width"),
    )
    turbovec_auto_persist: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_TURBOVEC_AUTO_PERSIST", "turbovec_auto_persist"),
    )
    turbovec_fail_open_to_pgvector: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_TURBOVEC_FAIL_OPEN_TO_PGVECTOR",
            "turbovec_fail_open_to_pgvector",
        ),
    )
    graphiti_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_GRAPHITI_ENABLED", "graphiti_enabled"),
    )
    graphiti_config_name: str = Field(
        default="default",
        validation_alias=AliasChoices("AION_GRAPHITI_CONFIG_NAME", "graphiti_config_name"),
    )
    graphiti_backend_type: str = Field(
        default="unknown",
        validation_alias=AliasChoices("AION_GRAPHITI_BACKEND_TYPE", "graphiti_backend_type"),
    )
    graphiti_endpoint_ref: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AION_GRAPHITI_ENDPOINT_REF", "graphiti_endpoint_ref"),
    )
    graphiti_fail_open_to_postgres_graph: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_GRAPHITI_FAIL_OPEN_TO_POSTGRES_GRAPH",
            "graphiti_fail_open_to_postgres_graph",
        ),
    )
    mcp_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_MCP_ENABLED", "mcp_enabled"),
    )
    mcp_allow_network: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_MCP_ALLOW_NETWORK", "mcp_allow_network"),
    )
    mcp_allow_stdio: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_MCP_ALLOW_STDIO", "mcp_allow_stdio"),
    )
    mcp_timeout_seconds: float = Field(
        default=15.0,
        validation_alias=AliasChoices("AION_MCP_TIMEOUT_SECONDS", "mcp_timeout_seconds"),
    )
    mcp_default_risk_level: str = Field(
        default="medium",
        validation_alias=AliasChoices("AION_MCP_DEFAULT_RISK_LEVEL", "mcp_default_risk_level"),
    )
    mcp_auto_register_capabilities: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MCP_AUTO_REGISTER_CAPABILITIES",
            "mcp_auto_register_capabilities",
        ),
    )
    workflow_engine_adapter: str = Field(
        default="local",
        validation_alias=AliasChoices(
            "AION_WORKFLOW_ENGINE_ADAPTER",
            "workflow_engine_adapter",
        ),
    )
    workflow_local_worker_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_WORKFLOW_LOCAL_WORKER_ENABLED",
            "workflow_local_worker_enabled",
        ),
    )
    workflow_local_worker_poll_interval_seconds: float = Field(
        default=5.0,
        validation_alias=AliasChoices(
            "AION_WORKFLOW_LOCAL_WORKER_POLL_INTERVAL_SECONDS",
            "workflow_local_worker_poll_interval_seconds",
        ),
    )
    workflow_local_worker_max_runs_per_tick: int = Field(
        default=1,
        validation_alias=AliasChoices(
            "AION_WORKFLOW_LOCAL_WORKER_MAX_RUNS_PER_TICK",
            "workflow_local_worker_max_runs_per_tick",
        ),
    )
    workflow_scheduler_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_WORKFLOW_SCHEDULER_ENABLED",
            "workflow_scheduler_enabled",
        ),
    )
    workflow_scheduler_tick_seconds: float = Field(
        default=60.0,
        validation_alias=AliasChoices(
            "AION_WORKFLOW_SCHEDULER_TICK_SECONDS",
            "workflow_scheduler_tick_seconds",
        ),
    )
    temporal_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_TEMPORAL_ENABLED", "temporal_enabled"),
    )
    temporal_endpoint_ref: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AION_TEMPORAL_ENDPOINT_REF", "temporal_endpoint_ref"),
    )
    temporal_namespace: str = Field(
        default="default",
        validation_alias=AliasChoices("AION_TEMPORAL_NAMESPACE", "temporal_namespace"),
    )
    temporal_task_queue: str = Field(
        default="aion-brain",
        validation_alias=AliasChoices("AION_TEMPORAL_TASK_QUEUE", "temporal_task_queue"),
    )
    risk_engine_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_RISK_ENGINE_ENABLED", "risk_engine_enabled"),
    )
    guardrails_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_GUARDRAILS_ENABLED", "guardrails_enabled"),
    )
    approvals_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_APPROVALS_ENABLED", "approvals_enabled"),
    )
    approval_default_expiry_hours: int = Field(
        default=72,
        validation_alias=AliasChoices(
            "AION_APPROVAL_DEFAULT_EXPIRY_HOURS",
            "approval_default_expiry_hours",
        ),
    )
    high_risk_requires_approval: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_HIGH_RISK_REQUIRES_APPROVAL",
            "high_risk_requires_approval",
        ),
    )
    critical_risk_blocks_by_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CRITICAL_RISK_BLOCKS_BY_DEFAULT",
            "critical_risk_blocks_by_default",
        ),
    )
    policy_adapter: str = Field(
        default="opa",
        validation_alias=AliasChoices("AION_POLICY_ADAPTER", "policy_adapter"),
    )
    attention_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_ATTENTION_ENABLED", "attention_enabled"),
    )
    working_memory_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_WORKING_MEMORY_ENABLED",
            "working_memory_enabled",
        ),
    )
    working_memory_default_ttl_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices(
            "AION_WORKING_MEMORY_DEFAULT_TTL_SECONDS",
            "working_memory_default_ttl_seconds",
        ),
    )
    working_memory_max_slots_default: int = Field(
        default=100,
        validation_alias=AliasChoices(
            "AION_WORKING_MEMORY_MAX_SLOTS_DEFAULT",
            "working_memory_max_slots_default",
        ),
    )
    attention_default_max_signals: int = Field(
        default=10,
        validation_alias=AliasChoices(
            "AION_ATTENTION_DEFAULT_MAX_SIGNALS",
            "attention_default_max_signals",
        ),
    )
    attention_default_max_slots: int = Field(
        default=20,
        validation_alias=AliasChoices(
            "AION_ATTENTION_DEFAULT_MAX_SLOTS",
            "attention_default_max_slots",
        ),
    )
    context_budget_default_max_items: int = Field(
        default=20,
        validation_alias=AliasChoices(
            "AION_CONTEXT_BUDGET_DEFAULT_MAX_ITEMS",
            "context_budget_default_max_items",
        ),
    )
    context_budget_default_max_chars: int = Field(
        default=12000,
        validation_alias=AliasChoices(
            "AION_CONTEXT_BUDGET_DEFAULT_MAX_CHARS",
            "context_budget_default_max_chars",
        ),
    )
    interrupt_priority_threshold: float = Field(
        default=0.75,
        validation_alias=AliasChoices(
            "AION_INTERRUPT_PRIORITY_THRESHOLD",
            "interrupt_priority_threshold",
        ),
    )
    memory_governance_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MEMORY_GOVERNANCE_ENABLED",
            "memory_governance_enabled",
        ),
    )
    memory_decay_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_MEMORY_DECAY_ENABLED", "memory_decay_enabled"),
    )
    memory_conflict_scan_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MEMORY_CONFLICT_SCAN_ENABLED",
            "memory_conflict_scan_enabled",
        ),
    )
    memory_compaction_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MEMORY_COMPACTION_ENABLED",
            "memory_compaction_enabled",
        ),
    )
    memory_default_decay_half_life_days: int = Field(
        default=90,
        validation_alias=AliasChoices(
            "AION_MEMORY_DEFAULT_DECAY_HALF_LIFE_DAYS",
            "memory_default_decay_half_life_days",
        ),
    )
    memory_low_confidence_threshold: float = Field(
        default=0.35,
        validation_alias=AliasChoices(
            "AION_MEMORY_LOW_CONFIDENCE_THRESHOLD",
            "memory_low_confidence_threshold",
        ),
    )
    memory_compaction_requires_approval: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_MEMORY_COMPACTION_REQUIRES_APPROVAL",
            "memory_compaction_requires_approval",
        ),
    )
    memory_forgetting_requires_approval: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_MEMORY_FORGETTING_REQUIRES_APPROVAL",
            "memory_forgetting_requires_approval",
        ),
    )
    memory_retention_sweep_limit_default: int = Field(
        default=1000,
        validation_alias=AliasChoices(
            "AION_MEMORY_RETENTION_SWEEP_LIMIT_DEFAULT",
            "memory_retention_sweep_limit_default",
        ),
    )
    autonomy_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_AUTONOMY_ENABLED", "autonomy_enabled"),
    )
    autonomy_default_mode: str = Field(
        default="assist",
        validation_alias=AliasChoices("AION_AUTONOMY_DEFAULT_MODE", "autonomy_default_mode"),
    )
    autonomy_default_max_mode: str = Field(
        default="dry_run",
        validation_alias=AliasChoices(
            "AION_AUTONOMY_DEFAULT_MAX_MODE",
            "autonomy_default_max_mode",
        ),
    )
    autonomy_default_max_risk_level: str = Field(
        default="medium",
        validation_alias=AliasChoices(
            "AION_AUTONOMY_DEFAULT_MAX_RISK_LEVEL",
            "autonomy_default_max_risk_level",
        ),
    )
    autonomy_external_models_allowed_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTONOMY_EXTERNAL_MODELS_ALLOWED_DEFAULT",
            "autonomy_external_models_allowed_default",
        ),
    )
    autonomy_external_tools_allowed_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTONOMY_EXTERNAL_TOOLS_ALLOWED_DEFAULT",
            "autonomy_external_tools_allowed_default",
        ),
    )
    autonomy_background_workflows_allowed_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTONOMY_BACKGROUND_WORKFLOWS_ALLOWED_DEFAULT",
            "autonomy_background_workflows_allowed_default",
        ),
    )
    autonomy_scheduler_allowed_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTONOMY_SCHEDULER_ALLOWED_DEFAULT",
            "autonomy_scheduler_allowed_default",
        ),
    )
    autonomy_skill_promotion_allowed_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTONOMY_SKILL_PROMOTION_ALLOWED_DEFAULT",
            "autonomy_skill_promotion_allowed_default",
        ),
    )
    autonomy_memory_forgetting_allowed_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_AUTONOMY_MEMORY_FORGETTING_ALLOWED_DEFAULT",
            "autonomy_memory_forgetting_allowed_default",
        ),
    )
    cognitive_cycles_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_COGNITIVE_CYCLES_ENABLED",
            "cognitive_cycles_enabled",
        ),
    )
    sleep_consolidation_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SLEEP_CONSOLIDATION_ENABLED",
            "sleep_consolidation_enabled",
        ),
    )
    cycle_controlled_mode_requires_approval: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CYCLE_CONTROLLED_MODE_REQUIRES_APPROVAL",
            "cycle_controlled_mode_requires_approval",
        ),
    )
    cycle_default_working_memory_sweep_limit: int = Field(
        default=100,
        validation_alias=AliasChoices(
            "AION_CYCLE_DEFAULT_WORKING_MEMORY_SWEEP_LIMIT",
            "cycle_default_working_memory_sweep_limit",
        ),
    )
    cycle_default_memory_decay_limit: int = Field(
        default=500,
        validation_alias=AliasChoices(
            "AION_CYCLE_DEFAULT_MEMORY_DECAY_LIMIT",
            "cycle_default_memory_decay_limit",
        ),
    )
    cycle_default_conflict_scan_limit: int = Field(
        default=500,
        validation_alias=AliasChoices(
            "AION_CYCLE_DEFAULT_CONFLICT_SCAN_LIMIT",
            "cycle_default_conflict_scan_limit",
        ),
    )
    cycle_default_compaction_max_records: int = Field(
        default=100,
        validation_alias=AliasChoices(
            "AION_CYCLE_DEFAULT_COMPACTION_MAX_RECORDS",
            "cycle_default_compaction_max_records",
        ),
    )
    cycle_auto_run_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_CYCLE_AUTO_RUN_ENABLED",
            "cycle_auto_run_enabled",
        ),
    )
    sandbox_control_plane_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SANDBOX_CONTROL_PLANE_ENABLED",
            "sandbox_control_plane_enabled",
        ),
    )
    sandbox_execution_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_SANDBOX_EXECUTION_ENABLED",
            "sandbox_execution_enabled",
        ),
    )
    sandbox_default_type: str = Field(
        default="local_noop",
        validation_alias=AliasChoices("AION_SANDBOX_DEFAULT_TYPE", "sandbox_default_type"),
    )
    sandbox_docker_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AION_SANDBOX_DOCKER_ENABLED", "sandbox_docker_enabled"),
    )
    sandbox_firecracker_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_SANDBOX_FIRECRACKER_ENABLED",
            "sandbox_firecracker_enabled",
        ),
    )
    secret_ref_vault_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SECRET_REF_VAULT_ENABLED", "secret_ref_vault_enabled"),
    )
    connector_registry_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONNECTOR_REGISTRY_ENABLED",
            "connector_registry_enabled",
        ),
    )
    runtime_permissions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_RUNTIME_PERMISSIONS_ENABLED",
            "runtime_permissions_enabled",
        ),
    )
    policy_catalog_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_POLICY_CATALOG_ENABLED", "policy_catalog_enabled"),
    )
    policy_test_harness_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_POLICY_TEST_HARNESS_ENABLED",
            "policy_test_harness_enabled",
        ),
    )
    policy_bundle_export_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_POLICY_BUNDLE_EXPORT_ENABLED",
            "policy_bundle_export_enabled",
        ),
    )
    opa_status_check_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_OPA_STATUS_CHECK_ENABLED", "opa_status_check_enabled"),
    )
    policy_defaults_seed_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_POLICY_DEFAULTS_SEED_ENABLED",
            "policy_defaults_seed_enabled",
        ),
    )
    beliefs_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_BELIEFS_ENABLED", "beliefs_enabled"),
    )
    concepts_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_CONCEPTS_ENABLED", "concepts_enabled"),
    )
    entities_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_ENTITIES_ENABLED", "entities_enabled"),
    )
    entity_resolution_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ENTITY_RESOLUTION_ENABLED",
            "entity_resolution_enabled",
        ),
    )
    entity_mention_extraction_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ENTITY_MENTION_EXTRACTION_ENABLED",
            "entity_mention_extraction_enabled",
        ),
    )
    entity_auto_extract_from_dialogue: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ENTITY_AUTO_EXTRACT_FROM_DIALOGUE",
            "entity_auto_extract_from_dialogue",
        ),
    )
    entity_auto_extract_from_evidence: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ENTITY_AUTO_EXTRACT_FROM_EVIDENCE",
            "entity_auto_extract_from_evidence",
        ),
    )
    entity_auto_extract_from_memory: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ENTITY_AUTO_EXTRACT_FROM_MEMORY",
            "entity_auto_extract_from_memory",
        ),
    )
    entity_auto_merge_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ENTITY_AUTO_MERGE_ENABLED",
            "entity_auto_merge_enabled",
        ),
    )
    entity_merge_requires_approval: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_ENTITY_MERGE_REQUIRES_APPROVAL",
            "entity_merge_requires_approval",
        ),
    )
    entity_resolution_min_score: float = Field(
        default=0.72,
        validation_alias=AliasChoices(
            "AION_ENTITY_RESOLUTION_MIN_SCORE",
            "entity_resolution_min_score",
        ),
    )
    entity_resolution_create_missing_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_ENTITY_RESOLUTION_CREATE_MISSING_DEFAULT",
            "entity_resolution_create_missing_default",
        ),
    )
    belief_truth_maintenance_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_BELIEF_TRUTH_MAINTENANCE_ENABLED",
            "belief_truth_maintenance_enabled",
        ),
    )
    belief_claim_extraction_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_BELIEF_CLAIM_EXTRACTION_ENABLED",
            "belief_claim_extraction_enabled",
        ),
    )
    belief_auto_extract_from_dialogue: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BELIEF_AUTO_EXTRACT_FROM_DIALOGUE",
            "belief_auto_extract_from_dialogue",
        ),
    )
    belief_auto_extract_from_evidence: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_BELIEF_AUTO_EXTRACT_FROM_EVIDENCE",
            "belief_auto_extract_from_evidence",
        ),
    )
    belief_min_supported_confidence: float = Field(
        default=0.65,
        validation_alias=AliasChoices(
            "AION_BELIEF_MIN_SUPPORTED_CONFIDENCE",
            "belief_min_supported_confidence",
        ),
    )
    belief_stale_after_days: int = Field(
        default=180,
        validation_alias=AliasChoices(
            "AION_BELIEF_STALE_AFTER_DAYS",
            "belief_stale_after_days",
        ),
    )
    belief_contradiction_detection_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_BELIEF_CONTRADICTION_DETECTION_ENABLED",
            "belief_contradiction_detection_enabled",
        ),
    )
    situations_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_SITUATIONS_ENABLED", "situations_enabled"),
    )
    situation_projection_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SITUATION_PROJECTION_ENABLED",
            "situation_projection_enabled",
        ),
    )
    temporal_state_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_TEMPORAL_STATE_ENABLED", "temporal_state_enabled"),
    )
    context_continuity_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_CONTEXT_CONTINUITY_ENABLED",
            "context_continuity_enabled",
        ),
    )
    situation_auto_project_from_dialogue: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_SITUATION_AUTO_PROJECT_FROM_DIALOGUE",
            "situation_auto_project_from_dialogue",
        ),
    )
    situation_auto_project_from_events: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_SITUATION_AUTO_PROJECT_FROM_EVENTS",
            "situation_auto_project_from_events",
        ),
    )
    situation_projection_default_window_hours: int = Field(
        default=24,
        validation_alias=AliasChoices(
            "AION_SITUATION_PROJECTION_DEFAULT_WINDOW_HOURS",
            "situation_projection_default_window_hours",
        ),
    )
    situation_max_state_atoms_default: int = Field(
        default=500,
        validation_alias=AliasChoices(
            "AION_SITUATION_MAX_STATE_ATOMS_DEFAULT",
            "situation_max_state_atoms_default",
        ),
    )
    decisions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_DECISIONS_ENABLED", "decisions_enabled"),
    )
    counterfactuals_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_COUNTERFACTUALS_ENABLED", "counterfactuals_enabled"),
    )
    decision_auto_commit_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_DECISION_AUTO_COMMIT_ENABLED",
            "decision_auto_commit_enabled",
        ),
    )
    decision_default_utility_profile: str = Field(
        default="generic-balanced",
        validation_alias=AliasChoices(
            "AION_DECISION_DEFAULT_UTILITY_PROFILE",
            "decision_default_utility_profile",
        ),
    )
    decision_require_approval_for_high_risk: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_DECISION_REQUIRE_APPROVAL_FOR_HIGH_RISK",
            "decision_require_approval_for_high_risk",
        ),
    )
    decision_max_options_default: int = Field(
        default=10,
        validation_alias=AliasChoices(
            "AION_DECISION_MAX_OPTIONS_DEFAULT",
            "decision_max_options_default",
        ),
    )
    decision_counterfactual_max_changes_default: int = Field(
        default=25,
        validation_alias=AliasChoices(
            "AION_DECISION_COUNTERFACTUAL_MAX_CHANGES_DEFAULT",
            "decision_counterfactual_max_changes_default",
        ),
    )
    decision_controlled_mode_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_DECISION_CONTROLLED_MODE_ENABLED",
            "decision_controlled_mode_enabled",
        ),
    )
    outcomes_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("AION_OUTCOMES_ENABLED", "outcomes_enabled"),
    )
    effect_verification_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EFFECT_VERIFICATION_ENABLED",
            "effect_verification_enabled",
        ),
    )
    outcome_feedback_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OUTCOME_FEEDBACK_ENABLED",
            "outcome_feedback_enabled",
        ),
    )
    outcome_auto_collect_from_commands: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OUTCOME_AUTO_COLLECT_FROM_COMMANDS",
            "outcome_auto_collect_from_commands",
        ),
    )
    outcome_auto_collect_from_workflows: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OUTCOME_AUTO_COLLECT_FROM_WORKFLOWS",
            "outcome_auto_collect_from_workflows",
        ),
    )
    outcome_auto_verify_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_OUTCOME_AUTO_VERIFY_ENABLED",
            "outcome_auto_verify_enabled",
        ),
    )
    outcome_learning_feedback_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_OUTCOME_LEARNING_FEEDBACK_ENABLED",
            "outcome_learning_feedback_enabled",
        ),
    )
    outcome_min_verified_score: float = Field(
        default=0.75,
        validation_alias=AliasChoices(
            "AION_OUTCOME_MIN_VERIFIED_SCORE",
            "outcome_min_verified_score",
        ),
    )
    learning_synthesis_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LEARNING_SYNTHESIS_ENABLED",
            "learning_synthesis_enabled",
        ),
    )
    experience_ledger_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_EXPERIENCE_LEDGER_ENABLED",
            "experience_ledger_enabled",
        ),
    )
    pattern_mining_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_PATTERN_MINING_ENABLED",
            "pattern_mining_enabled",
        ),
    )
    lesson_records_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_LESSON_RECORDS_ENABLED",
            "lesson_records_enabled",
        ),
    )
    skill_suggestions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_SKILL_SUGGESTIONS_ENABLED",
            "skill_suggestions_enabled",
        ),
    )
    regression_suggestions_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "AION_REGRESSION_SUGGESTIONS_ENABLED",
            "regression_suggestions_enabled",
        ),
    )
    learning_auto_synthesis_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LEARNING_AUTO_SYNTHESIS_ENABLED",
            "learning_auto_synthesis_enabled",
        ),
    )
    learning_min_pattern_frequency: int = Field(
        default=2,
        validation_alias=AliasChoices(
            "AION_LEARNING_MIN_PATTERN_FREQUENCY",
            "learning_min_pattern_frequency",
        ),
    )
    learning_min_pattern_confidence: float = Field(
        default=0.6,
        validation_alias=AliasChoices(
            "AION_LEARNING_MIN_PATTERN_CONFIDENCE",
            "learning_min_pattern_confidence",
        ),
    )
    learning_skill_suggestions_promotion_allowed_default: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AION_LEARNING_SKILL_SUGGESTIONS_PROMOTION_ALLOWED_DEFAULT",
            "learning_skill_suggestions_promotion_allowed_default",
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

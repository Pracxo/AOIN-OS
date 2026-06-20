"""Deterministic kernel diagnostics."""

from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from aion_brain.contracts.diagnostics import DiagnosticCheck, DiagnosticSeverity, DiagnosticStatus


class KernelDiagnostics:
    """Inspect the assembled service graph without making network calls."""

    REQUIRED_COMPONENTS: tuple[tuple[str, str, DiagnosticSeverity], ...] = (
        ("policy_adapter_present", "policy_adapter", "critical"),
        ("audit_integrity_ledger_present", "audit_integrity_ledger", "high"),
        ("audit_verifier_present", "audit_verifier", "high"),
        ("provenance_service_present", "provenance_service", "high"),
        ("policy_catalog_service_present", "policy_catalog_service", "high"),
        ("permission_matrix_service_present", "permission_matrix_service", "high"),
        ("memory_adapter_present", "memory_service", "high"),
        ("semantic_memory_adapter_present", "semantic_memory_adapter", "high"),
        ("graph_memory_adapter_present", "graph_memory_adapter", "high"),
        ("reasoning_mesh_present", "reasoning_mesh", "high"),
        ("execution_orchestrator_present", "execution_orchestrator", "high"),
        ("retrieval_router_present", "retrieval_router", "high"),
        ("focus_service_present", "focus_service", "medium"),
        ("attention_controller_present", "attention_controller", "medium"),
        ("working_memory_service_present", "working_memory_service", "medium"),
        ("context_budgeter_present", "context_budgeter", "medium"),
        ("model_gateway_service_present", "model_gateway_service", "high"),
        ("prompt_redactor_present", "prompt_redactor", "high"),
        ("budget_guard_present", "model_budget_guard", "high"),
        ("visual_projection_present", "visual_projection_service", "medium"),
        ("replay_service_present", "replay_service", "medium"),
        ("workflow_service_present", "workflow_service", "medium"),
        ("local_workflow_engine_present", "local_workflow_engine", "medium"),
        ("workflow_scheduler_present", "workflow_scheduler", "medium"),
        ("workflow_worker_present", "workflow_worker", "medium"),
        ("temporal_adapter_present", "temporal_adapter", "medium"),
        ("risk_engine_present", "risk_engine", "high"),
        ("guardrail_engine_present", "guardrail_engine", "high"),
        ("approval_service_present", "approval_service", "high"),
        ("autonomy_governor_present", "autonomy_governor", "high"),
        ("delegation_service_present", "delegation_service", "medium"),
        ("run_level_service_present", "run_level_service", "medium"),
        ("cognitive_cycle_repository_present", "cognitive_cycle_repository", "medium"),
        ("cognitive_cycle_orchestrator_present", "cognitive_cycle_orchestrator", "high"),
        ("sleep_consolidation_service_present", "sleep_consolidation_service", "medium"),
        ("maintenance_service_present", "maintenance_service", "medium"),
        ("event_reaction_router_present", "event_reaction_router", "medium"),
        ("event_dead_letter_service_present", "event_dead_letter_service", "medium"),
        ("command_bus_present", "command_bus", "high"),
        ("idempotency_service_present", "idempotency_service", "high"),
        ("outbox_service_present", "outbox_service", "high"),
        ("inbox_service_present", "inbox_service", "high"),
        ("processing_lease_service_present", "processing_lease_service", "medium"),
        ("consistency_checker_present", "consistency_checker", "medium"),
        ("api_request_audit_service_present", "api_request_audit_service", "medium"),
        ("openapi_hygiene_checker_present", "openapi_hygiene_checker", "medium"),
        ("scenario_runner_present", "scenario_runner", "medium"),
        ("demo_fixture_service_present", "demo_fixture_service", "medium"),
        ("release_baseline_service_present", "release_baseline_service", "medium"),
        ("version_manifest_service_present", "version_manifest_service", "medium"),
        ("freeze_gate_service_present", "freeze_gate_service", "medium"),
        ("release_packager_present", "release_packager", "medium"),
        ("release_package_validator_present", "release_package_validator", "medium"),
        ("backup_exporter_present", "backup_exporter", "medium"),
        ("restore_preview_service_present", "restore_preview_service", "medium"),
        ("restore_service_present", "restore_service", "medium"),
        ("backup_validator_present", "backup_validator", "medium"),
        ("benchmark_runner_present", "benchmark_runner", "medium"),
        ("capacity_baseline_service_present", "capacity_baseline_service", "medium"),
        ("resource_budget_service_present", "resource_budget_service", "medium"),
        ("performance_summary_service_present", "performance_summary_service", "medium"),
        ("secret_scanner_present", "secret_scanner", "high"),
        ("config_hardening_checker_present", "config_hardening_checker", "medium"),
        ("api_exposure_checker_present", "api_exposure_checker", "medium"),
        ("adapter_risk_checker_present", "adapter_risk_checker", "medium"),
        ("dependency_metadata_scanner_present", "dependency_metadata_scanner", "medium"),
        ("threat_model_service_present", "threat_model_service", "medium"),
        ("security_control_catalog_present", "security_control_catalog", "medium"),
        ("hardening_gate_service_present", "hardening_gate_service", "high"),
        ("config_profile_service_present", "config_profile_service", "medium"),
        ("feature_flag_override_service_present", "feature_flag_override_service", "medium"),
        ("config_snapshot_service_present", "config_snapshot_service", "medium"),
        ("config_validator_present", "config_validator", "high"),
        ("runtime_config_status_service_present", "runtime_config_status_service", "medium"),
        ("dependency_health_service_present", "dependency_health_service", "medium"),
        ("retry_policy_service_present", "retry_policy_service", "medium"),
        ("circuit_breaker_service_present", "circuit_breaker_service", "medium"),
        ("degraded_mode_service_present", "degraded_mode_service", "medium"),
        ("fault_injection_service_present", "fault_injection_service", "medium"),
        ("resilience_test_runner_present", "resilience_test_runner", "medium"),
        ("module_developer_kit_present", "module_package_validator", "medium"),
        ("module_certifier_present", "module_certifier", "medium"),
        ("module_scaffold_generator_present", "module_scaffold_generator", "medium"),
        ("module_contract_test_harness_present", "module_contract_test_harness", "medium"),
        ("sandbox_service_present", "sandbox_service", "high"),
        ("sandbox_validator_present", "sandbox_validator", "high"),
        ("secret_ref_service_present", "secret_ref_service", "medium"),
        ("connector_service_present", "connector_service", "medium"),
        ("local_noop_sandbox_adapter_present", "local_noop_sandbox_adapter", "medium"),
        ("docker_sandbox_adapter_present", "docker_sandbox_adapter", "medium"),
        ("firecracker_sandbox_adapter_present", "firecracker_sandbox_adapter", "medium"),
        ("operator_control_tower_present", "operator_control_tower_service", "medium"),
        ("operator_snapshot_service_present", "operator_snapshot_service", "medium"),
        ("operator_action_center_present", "operator_action_center_service", "medium"),
        ("operator_readiness_aggregator_present", "operator_readiness_aggregator", "medium"),
        ("dialogue_session_service_present", "dialogue_session_service", "medium"),
        ("dialogue_message_service_present", "dialogue_message_service", "medium"),
        ("clarification_manager_present", "clarification_manager", "medium"),
        ("response_composer_present", "response_composer", "medium"),
        ("response_verifier_present", "response_verifier", "medium"),
        ("explanation_builder_present", "explanation_builder", "medium"),
        ("trace_narrative_builder_present", "trace_narrative_builder", "medium"),
        ("why_not_service_present", "why_not_service", "medium"),
        ("explanation_verifier_present", "explanation_verifier", "medium"),
        ("explanation_feedback_service_present", "explanation_feedback_service", "medium"),
        ("dialogue_turn_service_present", "dialogue_turn_service", "medium"),
        ("self_model_profile_service_present", "self_model_profile_service", "medium"),
        ("capability_awareness_service_present", "capability_awareness_service", "medium"),
        ("limitation_ledger_service_present", "limitation_ledger_service", "medium"),
        ("confidence_calibrator_present", "confidence_calibrator", "medium"),
        ("self_assessment_service_present", "self_assessment_service", "medium"),
        ("introspection_snapshot_service_present", "introspection_snapshot_service", "medium"),
        ("belief_service_present", "belief_service", "medium"),
        ("belief_query_service_present", "belief_query_service", "medium"),
        ("belief_support_service_present", "belief_support_service", "medium"),
        ("belief_contradiction_service_present", "belief_contradiction_service", "medium"),
        ("truth_maintenance_service_present", "truth_maintenance_service", "medium"),
        ("claim_extractor_present", "claim_extractor", "medium"),
        ("concept_service_present", "concept_service", "medium"),
        ("entity_service_present", "entity_service", "medium"),
        ("entity_query_service_present", "entity_query_service", "medium"),
        ("entity_alias_service_present", "entity_alias_service", "medium"),
        ("reference_link_service_present", "reference_link_service", "medium"),
        ("entity_resolver_present", "entity_resolver", "medium"),
        ("entity_merge_service_present", "entity_merge_service", "medium"),
        ("entity_split_service_present", "entity_split_service", "medium"),
        ("decision_frame_service_present", "decision_frame_service", "medium"),
        ("option_evaluator_present", "option_evaluator", "medium"),
        ("counterfactual_simulator_present", "counterfactual_simulator", "medium"),
        ("decision_journal_service_present", "decision_journal_service", "medium"),
        ("outcome_service_present", "outcome_service", "medium"),
        ("expected_effect_service_present", "expected_effect_service", "medium"),
        ("observed_effect_collector_present", "observed_effect_collector", "medium"),
        ("effect_verifier_present", "effect_verifier", "medium"),
        ("outcome_feedback_service_present", "outcome_feedback_service", "medium"),
    )

    def __init__(self, container: object) -> None:
        self._container = container

    def run(self) -> list[DiagnosticCheck]:
        """Run lightweight configuration and service-presence checks."""
        settings = getattr(self._container, "settings", None)
        checks = [
            self._presence("settings_loaded", "settings", settings, "critical"),
            self._configured("database_config_present", "database", settings, "database_url"),
            self._configured("redis_config_present", "redis", settings, "redis_url"),
            self._configured("nats_config_present", "nats", settings, "nats_url"),
            self._configured("opa_config_present", "opa", settings, "opa_url"),
        ]
        checks.extend(
            self._presence(name, component, getattr(self._container, component, None), severity)
            for name, component, severity in self.REQUIRED_COMPONENTS
        )
        placeholder_names = {
            "litellm",
            "langfuse",
            "minio",
            "temporal",
            "http",
        }
        adapter_config = getattr(self._container, "adapter_config", None)
        selected = (
            " ".join(str(value) for value in adapter_config.model_dump().values()).lower()
            if adapter_config is not None
            else ""
        )
        checks.append(
            self._result(
                "no_placeholder_selected_for_live_execution",
                "adapter_selection",
                "failed" if any(name in selected for name in placeholder_names) else "passed",
                "critical",
                (
                    "No placeholder adapter is selected for live execution."
                    if not any(name in selected for name in placeholder_names)
                    else "A placeholder adapter is selected for live execution."
                ),
            )
        )
        checks.append(
            self._presence(
                "deterministic_provider_present",
                "model_provider_registry",
                _registry_get(self._container, "model_provider_registry", "deterministic"),
                "critical",
            )
        )
        checks.append(
            self._presence(
                "deterministic_profile_present",
                "model_profile_registry",
                _registry_get(self._container, "model_profile_registry", "aion-deterministic-v0"),
                "critical",
            )
        )
        checks.append(
            self._result(
                "external_model_gateway_disabled_by_default",
                "model_gateway",
                (
                    "passed"
                    if not bool(getattr(settings, "model_gateway_enabled", False))
                    else "warning"
                ),
                "medium",
                (
                    "External model gateway calls are disabled by default."
                    if not bool(getattr(settings, "model_gateway_enabled", False))
                    else "External model gateway calls are enabled."
                ),
            )
        )
        checks.extend(self._turbovec_checks(settings))
        checks.extend(self._graphiti_checks(settings))
        checks.extend(self._mcp_checks(settings))
        checks.extend(self._workflow_checks(settings))
        checks.extend(self._risk_control_checks(settings))
        checks.extend(self._attention_checks(settings))
        checks.extend(self._autonomy_checks(settings))
        checks.extend(self._cycle_checks(settings))
        checks.extend(self._event_reaction_checks(settings))
        checks.extend(self._consistency_checks(settings))
        checks.extend(self._api_support_checks(settings))
        checks.extend(self._sandbox_checks(settings))
        checks.extend(self._policy_catalog_checks(settings))
        checks.extend(self._scenario_checks(settings))
        checks.extend(self._versioning_checks(settings))
        checks.extend(self._backup_checks(settings))
        checks.extend(self._performance_checks(settings))
        checks.extend(self._security_baseline_checks(settings))
        checks.extend(self._runtime_config_checks(settings))
        checks.extend(self._resilience_checks(settings))
        checks.extend(self._audit_integrity_checks(settings))
        checks.extend(self._operator_checks(settings))
        checks.extend(self._dialogue_checks(settings))
        checks.extend(self._explanation_checks(settings))
        checks.extend(self._self_model_checks(settings))
        checks.extend(self._belief_checks(settings))
        checks.extend(self._entity_checks(settings))
        checks.extend(self._situation_checks(settings))
        checks.extend(self._decision_checks(settings))
        checks.extend(self._outcome_checks(settings))
        checks.extend(self._learning_synthesis_checks(settings))
        checks.extend(self._repo_quality_checks())
        return checks

    def _entity_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "concept_service",
                "entity_service",
                "entity_query_service",
                "entity_alias_service",
                "reference_link_service",
                "entity_resolver",
                "entity_merge_service",
                "entity_split_service",
            )
        )
        return [
            self._result(
                "concepts_enabled",
                "concepts",
                "passed" if bool(getattr(settings, "concepts_enabled", True)) else "warning",
                "medium",
                "Concept registry is enabled.",
            ),
            self._result(
                "entities_enabled",
                "entities",
                "passed" if bool(getattr(settings, "entities_enabled", True)) else "warning",
                "medium",
                "Entity registry is enabled.",
            ),
            self._result(
                "entity_resolution_enabled",
                "entities",
                (
                    "passed"
                    if bool(getattr(settings, "entity_resolution_enabled", True))
                    else "warning"
                ),
                "medium",
                "Entity resolution is enabled.",
            ),
            self._result(
                "entity_auto_merge_disabled",
                "entities",
                (
                    "passed"
                    if not bool(getattr(settings, "entity_auto_merge_enabled", False))
                    else "failed"
                ),
                "high",
                "Entity auto-merge is disabled.",
            ),
            self._result(
                "entity_services_present",
                "entities",
                "passed" if services_present else "failed",
                "high",
                "Entity and concept services are assembled.",
            ),
        ]

    def _belief_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "belief_service",
                "belief_support_service",
                "belief_contradiction_service",
                "belief_query_service",
                "truth_maintenance_service",
                "claim_extractor",
            )
        )
        return [
            self._result(
                "beliefs_enabled",
                "beliefs",
                "passed" if bool(getattr(settings, "beliefs_enabled", True)) else "warning",
                "medium",
                "Belief State Manager is enabled.",
            ),
            self._result(
                "belief_truth_maintenance_enabled",
                "beliefs",
                (
                    "passed"
                    if bool(getattr(settings, "belief_truth_maintenance_enabled", True))
                    else "warning"
                ),
                "medium",
                "Truth maintenance is enabled.",
            ),
            self._result(
                "belief_claim_extraction_enabled",
                "beliefs",
                (
                    "passed"
                    if bool(getattr(settings, "belief_claim_extraction_enabled", True))
                    else "warning"
                ),
                "medium",
                "Deterministic claim extraction is enabled.",
            ),
            self._result(
                "belief_services_present",
                "beliefs",
                "passed" if services_present else "failed",
                "high",
                "Belief services are assembled.",
            ),
        ]

    def _situation_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "situation_service",
                "state_atom_service",
                "situation_projector",
                "temporal_state_window_service",
                "context_continuity_service",
                "situation_query_service",
            )
        )
        return [
            self._result(
                "situations_enabled",
                "situations",
                "passed" if bool(getattr(settings, "situations_enabled", True)) else "warning",
                "medium",
                "Situation model is enabled.",
            ),
            self._result(
                "situation_projection_enabled",
                "situations",
                (
                    "passed"
                    if bool(getattr(settings, "situation_projection_enabled", True))
                    else "warning"
                ),
                "medium",
                "Situation projection is enabled.",
            ),
            self._result(
                "temporal_state_enabled",
                "situations",
                "passed" if bool(getattr(settings, "temporal_state_enabled", True)) else "warning",
                "medium",
                "Temporal state is enabled.",
            ),
            self._result(
                "context_continuity_enabled",
                "situations",
                (
                    "passed"
                    if bool(getattr(settings, "context_continuity_enabled", True))
                    else "warning"
                ),
                "medium",
                "Context continuity is enabled.",
            ),
            self._result(
                "situation_services_present",
                "situations",
                "passed" if services_present else "failed",
                "high",
                "Situation services are assembled.",
            ),
        ]

    def _decision_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "decision_frame_service",
                "decision_option_service",
                "utility_profile_service",
                "option_evaluator",
                "tradeoff_matrix_service",
                "counterfactual_simulator",
                "decision_journal_service",
                "decision_recommendation_service",
            )
        )
        return [
            self._result(
                "decisions_enabled",
                "decisions",
                "passed" if bool(getattr(settings, "decisions_enabled", True)) else "warning",
                "medium",
                "Decision intelligence is enabled.",
            ),
            self._result(
                "counterfactuals_enabled",
                "decisions",
                (
                    "passed"
                    if bool(getattr(settings, "counterfactuals_enabled", True))
                    else "warning"
                ),
                "medium",
                "Counterfactual simulation is enabled.",
            ),
            self._result(
                "decision_auto_commit_enabled",
                "decisions",
                (
                    "warning"
                    if bool(getattr(settings, "decision_auto_commit_enabled", False))
                    else "passed"
                ),
                "high",
                "Decision auto-commit is disabled by default.",
            ),
            self._result(
                "decision_controlled_mode_enabled",
                "decisions",
                (
                    "warning"
                    if bool(getattr(settings, "decision_controlled_mode_enabled", False))
                    else "passed"
                ),
                "high",
                "Controlled decision mode is disabled by default.",
            ),
            self._result(
                "decision_services_present",
                "decisions",
                "passed" if services_present else "failed",
                "high",
                "Decision services are assembled.",
            ),
        ]

    def _outcome_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "expected_effect_service",
                "observed_effect_collector",
                "outcome_service",
                "effect_verifier",
                "causal_attribution_service",
                "outcome_feedback_service",
                "outcome_query_service",
            )
        )
        return [
            self._result(
                "outcomes_enabled",
                "outcomes",
                "passed" if bool(getattr(settings, "outcomes_enabled", True)) else "warning",
                "medium",
                "Outcome Ledger is enabled.",
            ),
            self._result(
                "effect_verification_enabled",
                "outcomes",
                (
                    "passed"
                    if bool(getattr(settings, "effect_verification_enabled", True))
                    else "warning"
                ),
                "medium",
                "Effect verification is enabled.",
            ),
            self._result(
                "outcome_feedback_enabled",
                "outcomes",
                (
                    "passed"
                    if bool(getattr(settings, "outcome_feedback_enabled", True))
                    else "warning"
                ),
                "medium",
                "Outcome feedback is enabled.",
            ),
            self._result(
                "outcome_auto_verify_enabled",
                "outcomes",
                (
                    "warning"
                    if bool(getattr(settings, "outcome_auto_verify_enabled", False))
                    else "passed"
                ),
                "high",
                "Outcome auto-verification is disabled by default.",
            ),
            self._result(
                "outcome_services_present",
                "outcomes",
                "passed" if services_present else "failed",
                "high",
                "Outcome services are assembled.",
            ),
        ]

    def _learning_synthesis_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "experience_service",
                "pattern_miner",
                "lesson_service",
                "learning_synthesizer",
                "skill_suggestion_service",
                "regression_suggestion_service",
                "learning_query_service",
            )
        )
        return [
            self._result(
                "learning_synthesis_enabled",
                "learning",
                (
                    "passed"
                    if bool(getattr(settings, "learning_synthesis_enabled", True))
                    else "warning"
                ),
                "medium",
                "Learning synthesis is enabled.",
            ),
            self._result(
                "experience_ledger_enabled",
                "learning",
                (
                    "passed"
                    if bool(getattr(settings, "experience_ledger_enabled", True))
                    else "warning"
                ),
                "medium",
                "Experience ledger is enabled.",
            ),
            self._result(
                "pattern_mining_enabled",
                "learning",
                (
                    "passed"
                    if bool(getattr(settings, "pattern_mining_enabled", True))
                    else "warning"
                ),
                "medium",
                "Pattern mining is enabled.",
            ),
            self._result(
                "skill_suggestions_enabled",
                "learning",
                (
                    "passed"
                    if bool(getattr(settings, "skill_suggestions_enabled", True))
                    else "warning"
                ),
                "medium",
                "Skill suggestions are enabled.",
            ),
            self._result(
                "regression_suggestions_enabled",
                "learning",
                (
                    "passed"
                    if bool(getattr(settings, "regression_suggestions_enabled", True))
                    else "warning"
                ),
                "medium",
                "Regression suggestions are enabled.",
            ),
            self._result(
                "learning_services_present",
                "learning",
                "passed" if services_present else "failed",
                "high",
                "Learning synthesis services are assembled.",
            ),
        ]

    def _dialogue_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "dialogue_session_service",
                "dialogue_message_service",
                "clarification_manager",
                "response_composer",
                "response_verifier",
                "response_delivery_service",
                "dialogue_feedback_service",
                "dialogue_turn_service",
                "dialogue_memory_handoff_service",
            )
        )
        return [
            self._result(
                "dialogue_enabled",
                "dialogue",
                "passed" if bool(getattr(settings, "dialogue_enabled", True)) else "warning",
                "medium",
                "Dialogue Session Manager is enabled.",
            ),
            self._result(
                "response_composer_enabled",
                "dialogue",
                (
                    "passed"
                    if bool(getattr(settings, "response_composer_enabled", True))
                    else "warning"
                ),
                "medium",
                "Deterministic Response Composer is enabled.",
            ),
            self._result(
                "clarification_loop_enabled",
                "dialogue",
                (
                    "passed"
                    if bool(getattr(settings, "clarification_loop_enabled", True))
                    else "warning"
                ),
                "medium",
                "Clarification Loop is enabled.",
            ),
            self._result(
                "dialogue_services_present",
                "dialogue",
                "passed" if services_present else "failed",
                "high",
                "Dialogue services are assembled.",
            ),
        ]

    def _explanation_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "explanation_builder",
                "trace_narrative_builder",
                "why_not_service",
                "explanation_verifier",
                "explanation_feedback_service",
            )
        )
        return [
            self._result(
                "explanations_enabled",
                "explanations",
                "passed" if bool(getattr(settings, "explanations_enabled", True)) else "warning",
                "medium",
                "Explanation Engine is enabled.",
            ),
            self._result(
                "trace_narratives_enabled",
                "explanations",
                (
                    "passed"
                    if bool(getattr(settings, "trace_narratives_enabled", True))
                    else "warning"
                ),
                "medium",
                "Trace Narrative Builder is enabled.",
            ),
            self._result(
                "why_not_enabled",
                "explanations",
                "passed" if bool(getattr(settings, "why_not_enabled", True)) else "warning",
                "medium",
                "Why/why-not explanations are enabled.",
            ),
            self._result(
                "explanation_forbid_hidden_reasoning",
                "explanations",
                (
                    "passed"
                    if bool(getattr(settings, "explanation_forbid_hidden_reasoning", True))
                    else "failed"
                ),
                "high",
                "Explanations are configured to forbid hidden reasoning exposure.",
            ),
            self._result(
                "explanation_services_present",
                "explanations",
                "passed" if services_present else "failed",
                "high",
                "Explanation services are assembled.",
            ),
        ]

    def _self_model_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "self_model_profile_service",
                "self_description_service",
                "capability_awareness_service",
                "limitation_ledger_service",
                "confidence_calibrator",
                "self_assessment_service",
                "introspection_snapshot_service",
            )
        )
        active_profile_present = (
            getattr(self._container, "self_model_profile_service", None) is not None
        )
        return [
            self._result(
                "self_model_enabled",
                "self_model",
                "passed" if bool(getattr(settings, "self_model_enabled", True)) else "warning",
                "medium",
                "Self Model is enabled.",
            ),
            self._result(
                "capability_awareness_enabled",
                "self_model",
                (
                    "passed"
                    if bool(getattr(settings, "capability_awareness_enabled", True))
                    else "warning"
                ),
                "medium",
                "Capability Awareness is enabled.",
            ),
            self._result(
                "limitation_ledger_enabled",
                "self_model",
                (
                    "passed"
                    if bool(getattr(settings, "limitation_ledger_enabled", True))
                    else "warning"
                ),
                "medium",
                "Limitation Ledger is enabled.",
            ),
            self._result(
                "confidence_calibration_enabled",
                "self_model",
                (
                    "passed"
                    if bool(getattr(settings, "confidence_calibration_enabled", True))
                    else "warning"
                ),
                "medium",
                "Confidence Calibration is enabled.",
            ),
            self._result(
                "self_assessment_enabled",
                "self_model",
                (
                    "passed"
                    if bool(getattr(settings, "self_assessment_enabled", True))
                    else "warning"
                ),
                "medium",
                "Self Assessment is enabled.",
            ),
            self._result(
                "active_self_model_present",
                "self_model",
                "passed" if active_profile_present else "failed",
                "high",
                "An active descriptive self-model is present.",
            ),
            self._result(
                "self_model_services_present",
                "self_model",
                "passed" if services_present else "failed",
                "high",
                "Self-model services are assembled.",
            ),
        ]

    def _operator_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "operator_status_card_builder",
                "operator_queue_summary_builder",
                "operator_action_center_service",
                "operator_readiness_aggregator",
                "operator_runbook_registry",
                "operator_control_tower_service",
                "operator_snapshot_service",
            )
        )
        return [
            self._result(
                "operator_control_tower_enabled",
                "operator",
                (
                    "passed"
                    if bool(getattr(settings, "operator_control_tower_enabled", True))
                    else "warning"
                ),
                "medium",
                "Operator Control Tower is enabled.",
            ),
            self._result(
                "operator_snapshot_enabled",
                "operator",
                (
                    "passed"
                    if bool(getattr(settings, "operator_snapshot_enabled", True))
                    else "warning"
                ),
                "medium",
                "Operator snapshots are enabled.",
            ),
            self._result(
                "operator_action_center_enabled",
                "operator",
                (
                    "passed"
                    if bool(getattr(settings, "operator_action_center_enabled", True))
                    else "warning"
                ),
                "medium",
                "Operator Action Center is enabled.",
            ),
            self._result(
                "operator_services_present",
                "operator",
                "passed" if services_present else "failed",
                "high",
                "Operator services are assembled.",
            ),
        ]

    def _audit_integrity_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "audit_integrity_enabled",
                "audit_integrity",
                (
                    "passed"
                    if bool(getattr(settings, "audit_integrity_enabled", True))
                    else "warning"
                ),
                "high",
                "Audit integrity is enabled.",
            ),
            self._result(
                "audit_hash_algorithm",
                "audit_integrity",
                (
                    "passed"
                    if getattr(settings, "audit_hash_algorithm", "sha256") == "sha256"
                    else "failed"
                ),
                "critical",
                "Audit hash algorithm is sha256.",
            ),
            self._result(
                "audit_checkpoint_interval",
                "audit_integrity",
                (
                    "passed"
                    if int(getattr(settings, "audit_checkpoint_interval", 0)) > 0
                    else "warning"
                ),
                "medium",
                "Audit checkpoint interval is configured.",
            ),
            self._presence(
                "audit_integrity_ledger_present",
                "audit_integrity",
                getattr(self._container, "audit_integrity_ledger", None),
                "high",
            ),
            self._presence(
                "audit_verifier_present",
                "audit_integrity",
                getattr(self._container, "audit_verifier", None),
                "high",
            ),
            self._presence(
                "provenance_service_present",
                "audit_integrity",
                getattr(self._container, "provenance_service", None),
                "high",
            ),
        ]

    def _resilience_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "dependency_health_service",
                "retry_policy_service",
                "circuit_breaker_service",
                "degraded_mode_service",
                "fault_injection_service",
                "resilience_test_runner",
            )
        )
        return [
            self._result(
                "resilience_enabled",
                "resilience",
                "passed" if bool(getattr(settings, "resilience_enabled", True)) else "warning",
                "high",
                "Resilience control plane is enabled.",
            ),
            self._result(
                "circuit_breakers_enabled",
                "resilience",
                (
                    "passed"
                    if bool(getattr(settings, "circuit_breakers_enabled", True))
                    else "warning"
                ),
                "medium",
                "Circuit breakers are enabled.",
            ),
            self._result(
                "fault_injection_enabled",
                "resilience",
                (
                    "passed"
                    if not bool(getattr(settings, "fault_injection_enabled", False))
                    else "warning"
                ),
                "medium",
                "Fault injection is disabled by default.",
            ),
            self._result(
                "degraded_mode_enabled",
                "resilience",
                ("passed" if bool(getattr(settings, "degraded_mode_enabled", True)) else "warning"),
                "medium",
                "Degraded mode reporting is enabled.",
            ),
            self._result(
                "dependency_health_enabled",
                "resilience",
                (
                    "passed"
                    if bool(getattr(settings, "dependency_health_enabled", True))
                    else "warning"
                ),
                "medium",
                "Dependency health reporting is enabled.",
            ),
            self._result(
                "retry_policy_registry_enabled",
                "resilience",
                (
                    "passed"
                    if bool(getattr(settings, "retry_policy_registry_enabled", True))
                    else "warning"
                ),
                "medium",
                "Retry policy registry is enabled.",
            ),
            self._result(
                "resilience_services_present",
                "resilience",
                "passed" if services_present else "failed",
                "critical",
                "Resilience services are assembled.",
            ),
        ]

    def _runtime_config_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "config_profile_service",
                "feature_flag_override_service",
                "config_snapshot_service",
                "config_validator",
                "runtime_config_status_service",
            )
        )
        return [
            self._result(
                "runtime_config_enabled",
                "runtime_config",
                (
                    "passed"
                    if bool(getattr(settings, "runtime_config_enabled", True))
                    else "warning"
                ),
                "high",
                "Runtime configuration control plane is enabled.",
            ),
            self._result(
                "runtime_feature_overrides_enabled",
                "runtime_config",
                (
                    "passed"
                    if bool(getattr(settings, "runtime_feature_overrides_enabled", True))
                    else "warning"
                ),
                "medium",
                "Runtime feature overrides are enabled.",
            ),
            self._result(
                "runtime_config_snapshot_enabled",
                "runtime_config",
                (
                    "passed"
                    if bool(getattr(settings, "runtime_config_snapshot_enabled", True))
                    else "warning"
                ),
                "medium",
                "Runtime config snapshots are enabled.",
            ),
            self._result(
                "runtime_config_safe_defaults_required",
                "runtime_config",
                (
                    "passed"
                    if bool(getattr(settings, "runtime_config_safe_defaults_required", True))
                    else "warning"
                ),
                "high",
                "Runtime config safe defaults are required.",
            ),
            self._result(
                "runtime_config_services_present",
                "runtime_config",
                "passed" if services_present else "failed",
                "critical",
                "Runtime configuration services are assembled.",
            ),
        ]

    def _security_baseline_checks(self, settings: object) -> list[DiagnosticCheck]:
        services_present = all(
            getattr(self._container, name, None) is not None
            for name in (
                "secret_scanner",
                "config_hardening_checker",
                "api_exposure_checker",
                "adapter_risk_checker",
                "dependency_metadata_scanner",
                "threat_model_service",
                "security_control_catalog",
                "hardening_gate_service",
            )
        )
        return [
            self._result(
                "security_baseline_enabled",
                "security_baseline",
                (
                    "passed"
                    if bool(getattr(settings, "security_baseline_enabled", True))
                    else "warning"
                ),
                "high",
                "Security baseline is enabled.",
            ),
            self._result(
                "secret_scanner_enabled",
                "security_baseline",
                (
                    "passed"
                    if bool(getattr(settings, "secret_scanner_enabled", True))
                    else "warning"
                ),
                "high",
                "Secret scanner is enabled.",
            ),
            self._result(
                "hardening_gate_enabled",
                "security_baseline",
                (
                    "passed"
                    if bool(getattr(settings, "hardening_gate_enabled", True))
                    else "warning"
                ),
                "high",
                "Hardening gate is enabled.",
            ),
            self._result(
                "security_services_present",
                "security_baseline",
                "passed" if services_present else "failed",
                "critical",
                "Security baseline services are assembled.",
            ),
        ]

    def _performance_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "performance_enabled",
                "performance",
                "passed" if bool(getattr(settings, "performance_enabled", True)) else "warning",
                "medium",
                "Local performance measurement is enabled.",
            ),
            self._result(
                "benchmark_enabled",
                "performance",
                "passed" if bool(getattr(settings, "benchmark_enabled", True)) else "warning",
                "medium",
                "Local benchmark harness is enabled.",
            ),
            self._result(
                "benchmark_controlled_mode_disabled_by_default",
                "performance",
                (
                    "passed"
                    if not bool(getattr(settings, "benchmark_controlled_mode_enabled", False))
                    else "warning"
                ),
                "high",
                "Controlled benchmark mode is disabled by default.",
            ),
            self._result(
                "performance_sampling_enabled",
                "performance",
                (
                    "passed"
                    if bool(getattr(settings, "performance_sample_api_requests", True))
                    else "warning"
                ),
                "medium",
                "API request timing sampling is enabled.",
            ),
        ]

    def _backup_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "backups_enabled",
                "backups",
                "passed" if bool(getattr(settings, "backups_enabled", True)) else "warning",
                "medium",
                "Local application-level backups are enabled.",
            ),
            self._result(
                "backup_output_dir_configured",
                "backups",
                "passed"
                if bool(str(getattr(settings, "backup_output_dir", "")).strip())
                else "failed",
                "medium",
                "Local backup output directory is configured.",
            ),
            self._result(
                "backup_restore_apply_disabled_by_default",
                "restore",
                (
                    "passed"
                    if not bool(getattr(settings, "backup_restore_apply_enabled", False))
                    else "warning"
                ),
                "high",
                "Restore apply is disabled by default.",
            ),
        ]

    def _versioning_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "versioning_enabled",
                "versioning",
                "passed" if bool(getattr(settings, "versioning_enabled", True)) else "warning",
                "medium",
                "Versioning is enabled.",
            ),
            self._result(
                "freeze_gate_enabled",
                "freeze_gate",
                "passed" if bool(getattr(settings, "freeze_gate_enabled", True)) else "warning",
                "medium",
                "Freeze gate is enabled.",
            ),
            self._result(
                "compatibility_matrix_enabled",
                "compatibility",
                "passed"
                if bool(getattr(settings, "compatibility_matrix_enabled", True))
                else "warning",
                "medium",
                "Compatibility matrix is enabled.",
            ),
            self._result(
                "release_artifact_manifest_enabled",
                "release_artifact",
                "passed"
                if bool(getattr(settings, "release_artifact_manifest_enabled", True))
                else "warning",
                "medium",
                "Release artifact manifest is enabled.",
            ),
            self._result(
                "migration_baseline_enabled",
                "migration",
                "passed"
                if bool(getattr(settings, "migration_baseline_enabled", True))
                else "warning",
                "medium",
                "Migration baseline is enabled.",
            ),
            self._result(
                "release_packaging_enabled",
                "release_package",
                "passed"
                if bool(getattr(settings, "release_packaging_enabled", True))
                else "warning",
                "medium",
                "Release packaging is enabled.",
            ),
            self._result(
                "release_package_output_dir_configured",
                "release_package",
                "passed"
                if bool(str(getattr(settings, "release_package_output_dir", "")).strip())
                else "failed",
                "medium",
                "Release package output directory is configured.",
            ),
            self._result(
                "release_package_sbom_placeholder_enabled",
                "release_package",
                "passed"
                if bool(getattr(settings, "release_package_sbom_placeholder_enabled", True))
                else "warning",
                "medium",
                "Release package SBOM placeholder is enabled.",
            ),
        ]

    def _scenario_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "scenarios_enabled",
                "scenario_harness",
                "passed" if bool(getattr(settings, "scenarios_enabled", True)) else "warning",
                "medium",
                "Scenario harness is enabled.",
            ),
            self._result(
                "release_baseline_enabled",
                "release_baseline",
                "passed"
                if bool(getattr(settings, "release_baseline_enabled", True))
                else "warning",
                "medium",
                "Release baseline service is enabled.",
            ),
        ]

    def _repo_quality_checks(self) -> list[DiagnosticCheck]:
        root = Path(__file__).parents[5]
        scripts = root / "scripts"
        operations = root / "docs" / "operations"
        return [
            self._result(
                "ci_quality_scripts_present",
                "repository_quality",
                "passed"
                if all(
                    (scripts / name).exists()
                    for name in (
                        "check.sh",
                        "test-brain.sh",
                        "test-sdk.sh",
                        "typecheck.sh",
                    )
                )
                else "warning",
                "medium",
                "Core quality scripts are present.",
            ),
            self._result(
                "release_check_script_present",
                "repository_quality",
                "passed" if (scripts / "release-candidate-check.sh").exists() else "warning",
                "medium",
                "Release candidate check script is present.",
            ),
            self._result(
                "repo_health_script_present",
                "repository_quality",
                "passed" if (scripts / "repo-health.sh").exists() else "warning",
                "medium",
                "Repository health script is present.",
            ),
            self._result(
                "no_domain_drift_script_present",
                "repository_quality",
                "passed" if (scripts / "verify-no-domain-drift.sh").exists() else "warning",
                "high",
                "No-domain-drift script is present.",
            ),
            self._result(
                "operations_docs_present",
                "repository_quality",
                "passed"
                if all(
                    (operations / name).exists()
                    for name in (
                        "local-ops-runbook.md",
                        "quality-gates.md",
                        "release-candidate-checklist.md",
                    )
                )
                else "warning",
                "medium",
                "Operations docs are present.",
            ),
        ]

    def _policy_catalog_checks(self, settings: object) -> list[DiagnosticCheck]:
        defaults_seed_enabled = bool(getattr(settings, "policy_defaults_seed_enabled", False))
        return [
            self._result(
                "policy_catalog_enabled",
                "policy_catalog",
                "passed" if bool(getattr(settings, "policy_catalog_enabled", True)) else "warning",
                "high",
                "Policy catalog is enabled.",
            ),
            self._result(
                "policy_test_harness_enabled",
                "policy_catalog",
                "passed"
                if bool(getattr(settings, "policy_test_harness_enabled", True))
                else "warning",
                "medium",
                "Policy test harness is enabled.",
            ),
            self._result(
                "policy_bundle_export_enabled",
                "policy_catalog",
                "passed"
                if bool(getattr(settings, "policy_bundle_export_enabled", True))
                else "warning",
                "medium",
                "Policy bundle export is enabled.",
            ),
            self._result(
                "opa_status_check_enabled",
                "policy_catalog",
                "passed"
                if bool(getattr(settings, "opa_status_check_enabled", True))
                else "warning",
                "medium",
                "OPA status checks are enabled.",
            ),
            self._result(
                "policy_defaults_seed_enabled",
                "policy_catalog",
                "warning" if defaults_seed_enabled else "passed",
                "medium",
                (
                    "Automatic policy default seeding is enabled."
                    if defaults_seed_enabled
                    else "Automatic policy default seeding is disabled by default."
                ),
            ),
        ]

    def _sandbox_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "sandbox_control_plane_enabled",
                "sandbox",
                "passed"
                if bool(getattr(settings, "sandbox_control_plane_enabled", True))
                else "warning",
                "high",
                "Sandbox Control Plane is enabled.",
            ),
            self._result(
                "sandbox_execution_enabled",
                "sandbox",
                "warning"
                if bool(getattr(settings, "sandbox_execution_enabled", False))
                else "passed",
                "critical",
                "Sandbox execution is disabled by default.",
            ),
            self._result(
                "sandbox_default_type",
                "sandbox",
                "passed"
                if str(getattr(settings, "sandbox_default_type", "")) == "local_noop"
                else "warning",
                "medium",
                "Default sandbox type is local_noop.",
            ),
            self._result(
                "docker_sandbox_enabled",
                "sandbox",
                "warning" if bool(getattr(settings, "sandbox_docker_enabled", False)) else "passed",
                "critical",
                "Docker sandbox execution is disabled.",
            ),
            self._result(
                "firecracker_sandbox_enabled",
                "sandbox",
                "warning"
                if bool(getattr(settings, "sandbox_firecracker_enabled", False))
                else "passed",
                "critical",
                "Firecracker sandbox execution is disabled.",
            ),
            self._result(
                "secret_ref_vault_enabled",
                "secrets",
                "passed"
                if bool(getattr(settings, "secret_ref_vault_enabled", True))
                else "warning",
                "high",
                "Secret Reference Vault is enabled.",
            ),
            self._result(
                "connector_registry_enabled",
                "connectors",
                "passed"
                if bool(getattr(settings, "connector_registry_enabled", True))
                else "warning",
                "high",
                "Connector Registry is enabled.",
            ),
            self._result(
                "runtime_permissions_enabled",
                "sandbox",
                "passed"
                if bool(getattr(settings, "runtime_permissions_enabled", True))
                else "warning",
                "high",
                "Runtime permission grants are enabled.",
            ),
            self._result(
                "no_sandbox_execution_by_default",
                "sandbox",
                "passed"
                if not bool(getattr(settings, "sandbox_execution_enabled", False))
                else "failed",
                "critical",
                "No sandbox execution is enabled by default.",
            ),
        ]

    def _api_support_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "api_request_context_middleware_present",
                "api",
                "passed",
                "high",
                "Request context middleware is installed by the app factory.",
            ),
            self._result(
                "api_exception_handlers_present",
                "api",
                "passed",
                "high",
                "AION API exception handlers are installed by the app factory.",
            ),
            self._result(
                "api_request_audit_enabled",
                "api",
                "passed"
                if bool(getattr(settings, "api_request_audit_enabled", True))
                else "warning",
                "medium",
                "API request audit is enabled.",
            ),
            self._result(
                "api_openapi_hygiene_enabled",
                "api",
                "passed"
                if bool(getattr(settings, "api_openapi_hygiene_enabled", True))
                else "warning",
                "medium",
                "OpenAPI hygiene checks are enabled.",
            ),
        ]

    def _consistency_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "command_bus_enabled",
                "command_bus",
                "passed" if bool(getattr(settings, "command_bus_enabled", True)) else "warning",
                "high",
                "Command Bus is enabled."
                if bool(getattr(settings, "command_bus_enabled", True))
                else "Command Bus is disabled.",
            ),
            self._result(
                "idempotency_enabled",
                "idempotency",
                "passed" if bool(getattr(settings, "idempotency_enabled", True)) else "warning",
                "high",
                "Idempotency Service is enabled.",
            ),
            self._result(
                "outbox_enabled",
                "outbox",
                "passed" if bool(getattr(settings, "outbox_enabled", True)) else "warning",
                "high",
                "Transactional Outbox is enabled.",
            ),
            self._result(
                "outbox_process_enabled",
                "outbox",
                "warning" if bool(getattr(settings, "outbox_process_enabled", False)) else "passed",
                "medium",
                "Outbox processing is manual and disabled by default.",
            ),
            self._result(
                "inbox_enabled",
                "inbox",
                "passed" if bool(getattr(settings, "inbox_enabled", True)) else "warning",
                "high",
                "Inbox deduplication is enabled.",
            ),
            self._result(
                "consistency_checker_enabled",
                "consistency",
                "passed"
                if bool(getattr(settings, "consistency_checker_enabled", True))
                else "warning",
                "medium",
                "Consistency Checker is enabled.",
            ),
            self._result(
                "no_outbox_background_processor",
                "outbox",
                "passed",
                "high",
                "No outbox background processor starts automatically.",
            ),
            self._result(
                "no_inbox_background_processor",
                "inbox",
                "passed",
                "high",
                "No inbox background processor starts automatically.",
            ),
        ]

    def _autonomy_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "autonomy_enabled",
                "autonomy",
                "passed" if bool(getattr(settings, "autonomy_enabled", True)) else "warning",
                "high",
                (
                    "Autonomy Governor is enabled."
                    if bool(getattr(settings, "autonomy_enabled", True))
                    else "Autonomy Governor is disabled."
                ),
            ),
            self._result(
                "autonomy_default_mode",
                "autonomy",
                "passed",
                "medium",
                f"Default autonomy mode is {getattr(settings, 'autonomy_default_mode', 'assist')}.",
            ),
            self._result(
                "autonomy_default_max_mode",
                "autonomy",
                (
                    "passed"
                    if str(getattr(settings, "autonomy_default_max_mode", "dry_run")) == "dry_run"
                    else "warning"
                ),
                "high",
                (
                    "Default autonomy max mode is dry_run."
                    if str(getattr(settings, "autonomy_default_max_mode", "dry_run")) == "dry_run"
                    else "Default autonomy max mode allows controlled execution."
                ),
            ),
            self._result(
                "autonomy_external_models_allowed_default",
                "autonomy",
                (
                    "warning"
                    if bool(getattr(settings, "autonomy_external_models_allowed_default", False))
                    else "passed"
                ),
                "high",
                "External model autonomy is disabled by default.",
            ),
            self._result(
                "autonomy_external_tools_allowed_default",
                "autonomy",
                (
                    "warning"
                    if bool(getattr(settings, "autonomy_external_tools_allowed_default", False))
                    else "passed"
                ),
                "high",
                "External tool autonomy is disabled by default.",
            ),
            self._result(
                "autonomy_scheduler_allowed_default",
                "autonomy",
                (
                    "warning"
                    if bool(getattr(settings, "autonomy_scheduler_allowed_default", False))
                    else "passed"
                ),
                "medium",
                "Scheduler autonomy is disabled by default.",
            ),
            self._result(
                "autonomy_background_workflows_allowed_default",
                "autonomy",
                (
                    "warning"
                    if bool(
                        getattr(
                            settings,
                            "autonomy_background_workflows_allowed_default",
                            False,
                        )
                    )
                    else "passed"
                ),
                "medium",
                "Background workflow autonomy is disabled by default.",
            ),
        ]

    def _attention_checks(self, settings: object) -> list[DiagnosticCheck]:
        return [
            self._result(
                "attention_enabled",
                "attention",
                "passed",
                "medium",
                (
                    "Attention Controller is enabled."
                    if bool(getattr(settings, "attention_enabled", True))
                    else "Attention Controller is disabled."
                ),
            ),
            self._result(
                "working_memory_enabled",
                "working_memory",
                "passed",
                "medium",
                (
                    "Working memory is enabled."
                    if bool(getattr(settings, "working_memory_enabled", True))
                    else "Working memory is disabled."
                ),
            ),
        ]

    def _turbovec_checks(self, settings: object) -> list[DiagnosticCheck]:
        enabled = bool(getattr(settings, "turbovec_enabled", False))
        selected = (
            str(getattr(settings, "default_semantic_adapter", "")).replace("-", "_") == "turbovec"
        )
        adapter = getattr(self._container, "turbovec_semantic_adapter", None)
        status = None
        status_method = getattr(adapter, "status", None)
        if callable(status_method):
            try:
                status = status_method(str(getattr(settings, "turbovec_index_name", "default")))
            except Exception:
                status = None
        fallback_reason = getattr(self._container, "semantic_adapter_fallback_reason", None)
        index_dir = Path(str(getattr(settings, "turbovec_index_dir", "./.aion_indexes/turbovec")))
        writable = _directory_writable(index_dir)
        return [
            self._result(
                "turbovec_enabled",
                "turbovec",
                "passed",
                "medium",
                "TurboVec is enabled." if enabled else "TurboVec is disabled by default.",
            ),
            self._result(
                "turbovec_package_available",
                "turbovec",
                (
                    "passed"
                    if bool(getattr(status, "available", False)) or not (enabled or selected)
                    else "warning"
                ),
                "medium",
                (
                    "TurboVec package is available."
                    if bool(getattr(status, "available", False))
                    else "TurboVec package is optional and not required."
                    if not (enabled or selected)
                    else f"TurboVec unavailable: {getattr(status, 'reason', 'unknown')}"
                ),
            ),
            self._result(
                "turbovec_selected",
                "semantic_memory_adapter",
                "passed",
                "medium",
                "TurboVec is selected." if selected else "TurboVec is not selected.",
            ),
            self._result(
                "turbovec_fallback_active",
                "semantic_memory_adapter",
                "warning" if fallback_reason else "passed",
                "medium",
                (
                    f"TurboVec fallback active: {fallback_reason}"
                    if fallback_reason
                    else "TurboVec fallback is not active."
                ),
            ),
            self._result(
                "turbovec_index_dir_writable",
                "turbovec",
                "passed" if writable else "warning",
                "medium",
                (
                    "TurboVec index directory is writable."
                    if writable
                    else "TurboVec index directory is not writable."
                ),
            ),
        ]

    def _graphiti_checks(self, settings: object) -> list[DiagnosticCheck]:
        enabled = bool(getattr(settings, "graphiti_enabled", False))
        selected = (
            str(getattr(settings, "default_graph_memory_adapter", "")).replace("-", "_")
            == "graphiti"
        )
        adapter = getattr(self._container, "graphiti_graph_adapter", None)
        status = None
        status_method = getattr(adapter, "status", None)
        if callable(status_method):
            try:
                status = status_method(str(getattr(settings, "graphiti_config_name", "default")))
            except Exception:
                status = None
        fallback_reason = getattr(self._container, "graph_adapter_fallback_reason", None)
        reason = str(getattr(status, "reason", "") or "")
        return [
            self._result(
                "graphiti_enabled",
                "graphiti",
                "passed",
                "medium",
                "Graphiti is enabled." if enabled else "Graphiti is disabled by default.",
            ),
            self._result(
                "graphiti_package_available",
                "graphiti",
                (
                    "passed"
                    if bool(getattr(status, "available", False)) or not (enabled or selected)
                    else "warning"
                ),
                "medium",
                (
                    "Graphiti package is available."
                    if bool(getattr(status, "available", False))
                    else "Graphiti package is optional and not required."
                    if not (enabled or selected)
                    else f"Graphiti unavailable: {getattr(status, 'reason', 'unknown')}"
                ),
            ),
            self._result(
                "graphiti_selected",
                "graph_memory_adapter",
                "passed",
                "medium",
                "Graphiti is selected." if selected else "Graphiti is not selected.",
            ),
            self._result(
                "graphiti_fallback_active",
                "graph_memory_adapter",
                "warning" if fallback_reason else "passed",
                "medium",
                (
                    f"Graphiti fallback active: {fallback_reason}"
                    if fallback_reason
                    else "Graphiti fallback is not active."
                ),
            ),
            self._result(
                "graphiti_backend_type",
                "graphiti",
                "passed",
                "medium",
                (
                    "Graphiti backend type is "
                    f"{getattr(settings, 'graphiti_backend_type', 'unknown')}."
                ),
            ),
            self._result(
                "graphiti_llm_disabled",
                "graphiti",
                "passed",
                "medium",
                (
                    "Graphiti LLM path is disabled."
                    if reason == "graphiti_llm_disabled"
                    or not bool(getattr(settings, "model_gateway_enabled", False))
                    else "Graphiti LLM path may be enabled."
                ),
            ),
        ]

    def _mcp_checks(self, settings: object) -> list[DiagnosticCheck]:
        enabled = bool(getattr(settings, "mcp_enabled", False))
        service = getattr(self._container, "mcp_service", None)
        adapter_status = None
        status_method = getattr(service, "status", None)
        if callable(status_method):
            try:
                adapter_status = status_method()
            except Exception:
                adapter_status = None
        runtime_registered = getattr(self._container, "mcp_runtime_adapter", None) is not None
        return [
            self._result(
                "mcp_enabled",
                "mcp",
                "passed",
                "medium",
                "MCP is enabled." if enabled else "MCP is disabled by default.",
            ),
            self._result(
                "mcp_package_available",
                "mcp",
                (
                    "passed"
                    if bool(getattr(adapter_status, "package_available", False)) or not enabled
                    else "warning"
                ),
                "medium",
                (
                    "MCP package is available."
                    if bool(getattr(adapter_status, "package_available", False))
                    else "MCP package is optional and not required."
                ),
            ),
            self._result(
                "mcp_network_allowed",
                "mcp",
                "warning" if bool(getattr(settings, "mcp_allow_network", False)) else "passed",
                "medium",
                (
                    "MCP network transports are allowed."
                    if bool(getattr(settings, "mcp_allow_network", False))
                    else "MCP network transports are disabled by default."
                ),
            ),
            self._result(
                "mcp_stdio_allowed",
                "mcp",
                "warning" if bool(getattr(settings, "mcp_allow_stdio", False)) else "passed",
                "medium",
                (
                    "MCP stdio transports are allowed."
                    if bool(getattr(settings, "mcp_allow_stdio", False))
                    else "MCP stdio transports are disabled by default."
                ),
            ),
            self._result(
                "mcp_runtime_registered",
                "mcp",
                "passed" if runtime_registered else "failed",
                "medium",
                (
                    "MCP runtime adapter is registered."
                    if runtime_registered
                    else "MCP runtime adapter is missing."
                ),
            ),
            self._result(
                "mcp_external_execution_disabled_by_default",
                "mcp",
                "passed" if not enabled else "warning",
                "medium",
                (
                    "MCP external execution is disabled by default."
                    if not enabled
                    else "MCP external execution is enabled."
                ),
            ),
        ]

    def _workflow_checks(self, settings: object) -> list[DiagnosticCheck]:
        service = getattr(self._container, "workflow_service", None)
        temporal_adapter = getattr(self._container, "temporal_adapter", None)
        status = None
        status_method = getattr(temporal_adapter, "temporal_status", None)
        if callable(status_method):
            try:
                status = status_method()
            except Exception:
                status = None
        local_worker_enabled = bool(getattr(settings, "workflow_local_worker_enabled", False))
        scheduler_enabled = bool(getattr(settings, "workflow_scheduler_enabled", False))
        temporal_enabled = bool(getattr(settings, "temporal_enabled", False))
        return [
            self._result(
                "workflow_engine_adapter_selected",
                "workflow",
                (
                    "passed"
                    if str(getattr(settings, "workflow_engine_adapter", "local")) == "local"
                    else "warning"
                ),
                "medium",
                (
                    "Local workflow engine is selected."
                    if str(getattr(settings, "workflow_engine_adapter", "local")) == "local"
                    else "A non-local workflow engine adapter is selected."
                ),
            ),
            self._presence(
                "workflow_service_assembled",
                "workflow_service",
                service,
                "medium",
            ),
            self._result(
                "workflow_local_worker_disabled_by_default",
                "workflow_worker",
                "warning" if local_worker_enabled else "passed",
                "medium",
                (
                    "Local workflow worker is enabled."
                    if local_worker_enabled
                    else "Local workflow worker is disabled by default."
                ),
            ),
            self._result(
                "workflow_scheduler_disabled_by_default",
                "workflow_scheduler",
                "warning" if scheduler_enabled else "passed",
                "medium",
                (
                    "Workflow scheduler is enabled."
                    if scheduler_enabled
                    else "Workflow scheduler is disabled by default."
                ),
            ),
            self._result(
                "temporal_disabled_by_default",
                "temporal",
                "warning" if temporal_enabled else "passed",
                "medium",
                (
                    "Temporal integration is enabled."
                    if temporal_enabled
                    else "Temporal integration is disabled by default."
                ),
            ),
            self._result(
                "temporal_package_optional",
                "temporal",
                (
                    "passed"
                    if bool(getattr(status, "package_available", False)) or not temporal_enabled
                    else "warning"
                ),
                "medium",
                (
                    "Temporal package is available."
                    if bool(getattr(status, "package_available", False))
                    else "Temporal package is optional and not required."
                ),
            ),
            self._result(
                "workflow_no_auto_background_loop",
                "workflow",
                "passed",
                "critical",
                "Workflow scheduler and worker only run when explicitly invoked.",
            ),
        ]

    def _risk_control_checks(self, settings: object) -> list[DiagnosticCheck]:
        risk_enabled = bool(getattr(settings, "risk_engine_enabled", True))
        guardrails_enabled = bool(getattr(settings, "guardrails_enabled", True))
        approvals_enabled = bool(getattr(settings, "approvals_enabled", True))
        high_requires_approval = bool(getattr(settings, "high_risk_requires_approval", True))
        critical_blocks = bool(getattr(settings, "critical_risk_blocks_by_default", False))
        return [
            self._result(
                "risk_engine_enabled",
                "risk_engine",
                "passed" if risk_enabled else "warning",
                "high",
                "Risk engine is enabled." if risk_enabled else "Risk engine is disabled.",
            ),
            self._result(
                "guardrails_enabled",
                "guardrails",
                "passed" if guardrails_enabled else "warning",
                "high",
                "Guardrails are enabled." if guardrails_enabled else "Guardrails are disabled.",
            ),
            self._result(
                "approvals_enabled",
                "approvals",
                "passed" if approvals_enabled else "warning",
                "high",
                "Approvals are enabled." if approvals_enabled else "Approvals are disabled.",
            ),
            self._result(
                "high_risk_requires_approval",
                "risk_engine",
                "passed" if high_requires_approval else "warning",
                "high",
                (
                    "High-risk actions require approval."
                    if high_requires_approval
                    else "High-risk approval is disabled."
                ),
            ),
            self._result(
                "critical_risk_policy",
                "risk_engine",
                "passed",
                "high",
                (
                    "Critical risk blocks by default."
                    if critical_blocks
                    else "Critical risk requires approval by default."
                ),
            ),
        ]

    def _cycle_checks(self, settings: object) -> list[DiagnosticCheck]:
        cycles_enabled = bool(getattr(settings, "cognitive_cycles_enabled", True))
        sleep_enabled = bool(getattr(settings, "sleep_consolidation_enabled", True))
        controlled_requires_approval = bool(
            getattr(settings, "cycle_controlled_mode_requires_approval", True)
        )
        auto_run_enabled = bool(getattr(settings, "cycle_auto_run_enabled", False))
        return [
            self._result(
                "cognitive_cycles_enabled",
                "cognitive_cycles",
                "passed" if cycles_enabled else "warning",
                "medium",
                (
                    "Cognitive cycles are enabled."
                    if cycles_enabled
                    else "Cognitive cycles are disabled."
                ),
            ),
            self._result(
                "sleep_consolidation_enabled",
                "sleep_consolidation",
                "passed" if sleep_enabled else "warning",
                "medium",
                (
                    "Sleep consolidation is enabled."
                    if sleep_enabled
                    else "Sleep consolidation is disabled."
                ),
            ),
            self._result(
                "cycle_controlled_mode_requires_approval",
                "cognitive_cycles",
                "passed" if controlled_requires_approval else "warning",
                "high",
                (
                    "Controlled cycle mode requires approval."
                    if controlled_requires_approval
                    else "Controlled cycle mode can run without approval."
                ),
            ),
            self._result(
                "cycle_auto_run_disabled_by_default",
                "cognitive_cycles",
                "warning" if auto_run_enabled else "passed",
                "critical",
                (
                    "Automatic cognitive cycle execution is enabled."
                    if auto_run_enabled
                    else "Automatic cognitive cycle execution is disabled by default."
                ),
            ),
            self._result(
                "cycle_manual_only_orchestrator",
                "cognitive_cycles",
                "passed",
                "critical",
                "Cognitive cycles only run through explicit API or service calls.",
            ),
        ]

    def _event_reaction_checks(self, settings: object) -> list[DiagnosticCheck]:
        router_enabled = bool(getattr(settings, "event_reaction_router_enabled", True))
        auto_dispatch_enabled = bool(getattr(settings, "event_auto_dispatch_enabled", False))
        dead_letter_enabled = bool(getattr(settings, "event_dead_letter_enabled", True))
        return [
            self._result(
                "event_reaction_router_enabled",
                "event_reaction_router",
                "passed" if router_enabled else "warning",
                "medium",
                (
                    "Event Reaction Router is enabled."
                    if router_enabled
                    else "Event Reaction Router is disabled."
                ),
            ),
            self._result(
                "event_auto_dispatch_disabled_by_default",
                "event_reaction_router",
                "warning" if auto_dispatch_enabled else "passed",
                "critical",
                (
                    "Automatic event dispatch is enabled."
                    if auto_dispatch_enabled
                    else "Automatic event dispatch is disabled by default."
                ),
            ),
            self._result(
                "event_dead_letter_enabled",
                "event_dead_letter",
                "passed" if dead_letter_enabled else "warning",
                "medium",
                (
                    "Event reaction dead letters are enabled."
                    if dead_letter_enabled
                    else "Event reaction dead letters are disabled."
                ),
            ),
            self._result(
                "event_reaction_no_background_consumer",
                "event_reaction_router",
                "passed",
                "critical",
                "Event reactions only run through explicit API calls or opt-in intake dispatch.",
            ),
        ]

    def _configured(
        self,
        name: str,
        component: str,
        settings: object,
        attribute: str,
    ) -> DiagnosticCheck:
        present = bool(getattr(settings, attribute, None))
        return self._result(
            name,
            component,
            "passed" if present else "warning",
            "medium",
            f"{component} configuration is {'present' if present else 'missing'}.",
        )

    def _presence(
        self,
        name: str,
        component: str,
        value: object,
        severity: DiagnosticSeverity,
    ) -> DiagnosticCheck:
        present = value is not None
        return self._result(
            name,
            component,
            "passed" if present else "failed",
            severity,
            f"{component} is {'assembled' if present else 'missing'}.",
        )

    def _result(
        self,
        name: str,
        component: str,
        status: DiagnosticStatus,
        severity: DiagnosticSeverity,
        message: str,
    ) -> DiagnosticCheck:
        return DiagnosticCheck(
            check_id=f"diagnostic-{uuid4().hex}",
            name=name,
            component=component,
            status=status,
            severity=severity,
            message=message,
            details={},
            created_at=datetime.now(UTC),
        )


def _registry_get(container: object, attribute: str, record_id: str) -> object | None:
    registry = getattr(container, attribute, None)
    if registry is None:
        return None
    internal_getter_name = "_lookup_provider" if "provider" in attribute else "_lookup_profile"
    internal_getter = getattr(registry, internal_getter_name, None)
    if callable(internal_getter):
        try:
            return cast(object | None, internal_getter(record_id))
        except Exception:
            pass
    getter_name = "get_provider" if "provider" in attribute else "get_profile"
    getter = getattr(registry, getter_name, None)
    if not callable(getter):
        return None
    try:
        return cast(object | None, getter(record_id))
    except Exception:
        return None


def _directory_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".aion-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False

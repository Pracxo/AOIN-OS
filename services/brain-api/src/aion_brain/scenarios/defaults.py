"""Default generic AION Brain scenarios."""

from aion_brain.contracts.scenarios import ScenarioDefinition, ScenarioStep


def build_golden_path_brain_scenario(scope: list[str]) -> ScenarioDefinition:
    """Build the full generic golden path scenario."""
    return _scenario(
        "golden_path_brain",
        "Golden Path Brain",
        "Validates the deterministic Brain path from health through visual projection.",
        "golden_path",
        scope,
        [
            "health_check",
            "kernel_status",
            "kernel_self_test",
            "create_event",
            "create_attention_signal",
            "create_evidence",
            "create_memory",
            "retrieve_memory",
            "compile_context",
            "reason",
            "plan",
            "command_noop",
            "visual_map",
        ],
        ["golden_path", "release_baseline", "brain"],
    )


def build_memory_evidence_retrieval_scenario(scope: list[str]) -> ScenarioDefinition:
    """Build a memory, evidence, and retrieval scenario."""
    return _scenario(
        "memory_evidence_retrieval",
        "Memory Evidence Retrieval",
        "Validates generic evidence creation, memory write, and retrieval paths.",
        "memory",
        scope,
        ["create_evidence", "create_memory", "retrieve_memory", "semantic_retrieve", "visual_map"],
        ["memory", "evidence", "retrieval", "release_baseline"],
    )


def build_policy_autonomy_approval_scenario(scope: list[str]) -> ScenarioDefinition:
    """Build a policy, autonomy, risk, and approval gate scenario."""
    return _scenario(
        "policy_autonomy_approval",
        "Policy Autonomy Approval",
        "Validates generic policy, autonomy, risk, and approval boundaries.",
        "policy",
        scope,
        ["policy_simulate", "autonomy_decide", "risk_assess", "approval_create"],
        ["policy", "autonomy", "approval", "release_baseline"],
    )


def build_module_sandbox_certification_scenario(scope: list[str]) -> ScenarioDefinition:
    """Build a module and sandbox validation scenario."""
    return _scenario(
        "module_sandbox_certification",
        "Module Sandbox Certification",
        "Validates generic module scaffold, certification, and sandbox profile validation.",
        "module",
        scope,
        ["module_scaffold", "module_certify", "sandbox_validate"],
        ["module", "sandbox", "release_baseline"],
    )


def build_event_reaction_workflow_cycle_scenario(scope: list[str]) -> ScenarioDefinition:
    """Build an event reaction, workflow, and cycle dry-run scenario."""
    return _scenario(
        "event_reaction_workflow_cycle",
        "Event Reaction Workflow Cycle",
        "Validates generic event dispatch, workflow dry-run, and cycle dry-run paths.",
        "workflow",
        scope,
        ["create_event", "event_dispatch_dry_run", "workflow_dry_run", "cycle_dry_run"],
        ["event", "workflow", "cycle", "release_baseline"],
    )


def build_replay_regression_visual_scenario(scope: list[str]) -> ScenarioDefinition:
    """Build a replay, regression, and visual projection scenario."""
    return _scenario(
        "replay_regression_visual",
        "Replay Regression Visual",
        "Validates deterministic think, replay dry-run, regression dry-run, and visual map paths.",
        "replay",
        scope,
        ["think", "replay_dry_run", "regression_dry_run", "visual_map"],
        ["replay", "regression", "visual", "release_baseline"],
    )


def list_default_scenarios(scope: list[str]) -> list[ScenarioDefinition]:
    """Return all default generic scenario definitions."""
    return [
        build_golden_path_brain_scenario(scope),
        build_memory_evidence_retrieval_scenario(scope),
        build_policy_autonomy_approval_scenario(scope),
        build_module_sandbox_certification_scenario(scope),
        build_event_reaction_workflow_cycle_scenario(scope),
        build_replay_regression_visual_scenario(scope),
    ]


def _scenario(
    scenario_id: str,
    name: str,
    description: str,
    scenario_type: str,
    scope: list[str],
    step_types: list[str],
    tags: list[str],
) -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id=scenario_id,
        name=name,
        description=description,
        status="active",
        scenario_type=scenario_type,  # type: ignore[arg-type]
        owner_scope=scope,
        steps=[
            ScenarioStep(
                step_id=f"{index:02d}_{step_type}",
                step_type=step_type,  # type: ignore[arg-type]
                description=f"Run generic {step_type.replace('_', ' ')} check.",
                request={"mode": "dry_run"},
                expected={"required_keys": ["status"]},
                required=True,
                metadata={"default": True},
            )
            for index, step_type in enumerate(step_types, start=1)
        ],
        expected={"status": "passed", "min_count": len(step_types)},
        tags=tags,
        metadata={"dry_run": True, "external_services": False},
    )

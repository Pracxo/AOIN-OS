from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    AUTH_SCOPE,
    CLOSEOUT_TASK,
    CURRENT_CLOSEOUT_TASK,
    CURRENT_IMPLEMENTATION_TASK,
    FUTURE_CONTRACTS,
    IMPLEMENTATION_TASK,
    STATE_MACHINE_STATES,
    TERMINAL_STATES,
    load_json,
    read_text,
)


def test_aion231_scope_records_contracts_state_machine_and_result_invariants() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")

    assert program["future_contracts"] == FUTURE_CONTRACTS
    assert program["runtime_state_machine"]["states"] == STATE_MACHINE_STATES
    assert program["runtime_state_machine"]["terminal_states"] == TERMINAL_STATES
    assert program["runtime_state_machine"]["rules"] == [
        "every transition explicit",
        "every transition receipt-bound",
        "no skipped stage",
        "no automatic continuation",
        "no transition after session expiry",
        "no transition after kill switch activation",
        "identity verification precedes ActorContext",
        "replay validation precedes session activation",
        "policy risk and guardrails precede dispatch",
        "approval validation precedes approval-gated dispatch",
        "dispatch remains deterministic and side-effect-free",
        "session close leaves zero active requests",
    ]
    assert program["required_result_invariants"] == {
        "operator_invoked": True,
        "local_session": True,
        "production_runtime": False,
        "public_network_effect": False,
        "model_provider_effect": False,
        "connector_effect": False,
        "tool_execution_effect": False,
        "production_write_effect": False,
        "production_memory_effect": False,
        "production_policy_effect": False,
        "cognitive_memory_effect": False,
        "belief_effect": False,
        "source_mutation_effect": False,
        "git_mutation_effect": False,
        "model_weight_effect": False,
        "production_exposure": False,
    }


def test_roadmap_authorizes_only_aion231_and_keeps_later_tasks_planned() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    roadmap = {item["task_id"]: item for item in program["roadmap"]}
    roadmap_text = read_text("docs/secure-runtime-integration/architecture-roadmap.md")

    assert roadmap["AION-230"]["state"] == "completed_program_authorization"
    assert roadmap[IMPLEMENTATION_TASK]["state"] == "evaluation_complete"
    assert roadmap[CLOSEOUT_TASK]["state"] == "evaluation_complete_model_gateway_authorized"
    assert roadmap[CURRENT_IMPLEMENTATION_TASK]["state"] == "authorized_not_implemented"
    assert roadmap[CURRENT_CLOSEOUT_TASK]["state"] == "planned_formal_evaluation"
    for task_id in ("AION-235", "AION-236", "AION-237"):
        assert roadmap[task_id]["state"] == "planned_not_authorized"
    assert roadmap["AION-238"]["state"] == "planned_final_program_closeout"
    assert "AION-231 is implemented and evaluation-complete" in roadmap_text
    assert "AION-233 is authorized but not implemented" in roadmap_text


def test_examples_are_bound_to_aion230_scope_and_closeout() -> None:
    for relative in (
        "examples/secure-runtime-integration/runtime-authorization-envelope.json",
        "examples/secure-runtime-integration/runtime-session-plan.json",
        "examples/secure-runtime-integration/runtime-stage-command.json",
        "examples/secure-runtime-integration/runtime-stage-receipt.json",
        "examples/secure-runtime-integration/runtime-guard-decision.json",
        "examples/secure-runtime-integration/kill-switch-state.json",
        "examples/secure-runtime-integration/runtime-boundary.json",
    ):
        payload = load_json(relative)
        assert payload["authorization_transaction_id"] == "AION-230-SRI-0001"
        assert payload["implementation_task"] == IMPLEMENTATION_TASK
        assert payload["formal_closeout_task"] == CLOSEOUT_TASK

    auth = load_json("examples/secure-runtime-integration/runtime-authorization-envelope.json")
    assert auth["authorization_scope"] == AUTH_SCOPE

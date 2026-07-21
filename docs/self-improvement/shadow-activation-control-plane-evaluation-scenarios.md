# Shadow Activation Control-Plane Evaluation Scenarios

AION-182 executes all mandatory AION-SACE-001 scenarios against synthetic and redacted evidence only.

| # | Scenario | Purpose | Result | Observed Outcome |
| --- | --- | --- | --- | --- |
| 1 | `valid-candidate` | Valid candidate | PASS | `candidate_valid` |
| 2 | `invalid-candidate-binding` | Invalid candidate binding | PASS | `approval_invalid` |
| 3 | `environment-boundary` | Environment boundary | PASS | `environment_fail_closed` |
| 4 | `data-and-adapter-boundary` | Data and adapter boundary | PASS | `adapter_boundary_enforced` |
| 5 | `approval-required` | Approval required | PASS | `approval_required` |
| 6 | `valid-synthetic-approval-evidence` | Valid synthetic approval evidence | PASS | `simulation_passed` |
| 7 | `separation-of-duties-rejection` | Separation of duties rejection | PASS | `approval_invalid` |
| 8 | `expired-consumed-reusable-approval` | Expired, consumed, and reusable approval | PASS | `approval_invalid` |
| 9 | `resource-budget-success` | Resource budget success | PASS | `budget_satisfied` |
| 10 | `resource-budget-failure` | Resource budget failure | PASS | `budget_fail_closed` |
| 11 | `output-boundary-validation` | Output boundary validation | PASS | `output_boundary_validated` |
| 12 | `local-evidence-adapter` | Local evidence adapter | PASS | `local_adapter_boundary_enforced` |
| 13 | `state-machine` | State machine | PASS | `state_machine_fail_closed` |
| 14 | `healthy-monitoring` | Healthy monitoring | PASS | `monitoring_passed` |
| 15 | `deactivation-triggers` | Deactivation triggers | PASS | `deactivation_required` |
| 16 | `valid-simulation` | Valid simulation | PASS | `simulation_passed` |
| 17 | `invalid-approval-simulation` | Invalid approval simulation | PASS | `approval_invalid` |
| 18 | `triggered-deactivation-simulation` | Triggered deactivation simulation | PASS | `simulation_failed` |
| 19 | `determinism` | Determinism | PASS | `deterministic_replay` |
| 20 | `concurrency` | Concurrency | PASS | `concurrency_isolated` |
| 21 | `runtime-and-integration-boundary` | Runtime and integration boundary | PASS | `runtime_integration_absent` |

All scenarios passed. Any failed hard gate would have produced `SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_FAIL_REMAIN_DISABLED` and left the control plane disabled pending remediation authorization review.

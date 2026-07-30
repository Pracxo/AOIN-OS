# Secure Runtime Integration Architecture Roadmap

AION-231 is implemented under `AION-230-SRI-0001`. AION-232 is now the active
formal evaluation and model-gateway authorization decision task. AION-233
remains unauthorized.
AION-233 remains unauthorized.

| Task | State | Role |
| --- | --- | --- |
| AION-230 | completed_program_authorization | Secure Runtime Integration charter and AION-231 authorization |
| AION-231 | implemented_pending_AION-232_closeout | Controlled authenticated local operator runtime foundation |
| AION-232 | active_formal_evaluation_and_model_gateway_authorization_decision | Runtime-foundation evaluation and controlled model-gateway authorization decision |
| AION-233 | planned_not_authorized | Controlled model-gateway implementation |
| AION-234 | planned_not_authorized | Model-gateway evaluation and capability-sandbox authorization |
| AION-235 | planned_not_authorized | Sandboxed connector and capability execution runtime |
| AION-236 | planned_not_authorized | Operator-console live-service integration |
| AION-237 | planned_not_authorized | Integrated authenticated local runtime pilot |
| AION-238 | planned_final_program_closeout | Final runtime integration evaluation and v0.2 RC authorization review |

## Ordering

1. AION-230 chartered `AION-SECURE-RUNTIME-INTEGRATION-001` and created
   `AION-230-SRI-0001`.
2. AION-231 implemented the authenticated local operator runtime foundation.
3. AION-232 must evaluate AION-231 and decide whether a controlled
   model-gateway authorization should be created.
4. AION-233 through AION-238 require later explicit authorization records before
   implementation or release work can begin.

## Current Boundary

AION-231 may compose existing offline identity verification, RequestIdentity,
ActorContext, replay protection, policy, risk, guardrails, approval evidence,
audit, and observability through a local side-effect-free runtime boundary.

AION-231 may not call model providers, connectors, tools, networks, external
identity providers, production memory, production policy, modules, deployment,
or model training.

# Knowledge Intelligence Operator Model

Operators may review synthetic plans, source classifications, provenance metadata, resource budgets, redacted incidents, disabled runtime holds, and blocked research actions.

AION-205 may emit operator review items for blocked domains, rejected content types, budget pressure, provenance gaps, source conflicts, stale evidence, and policy violations. These items remain advisory until AION-206 evaluation.

No AION-204 operator-console surface performs a research request, starts a crawler, calls an API route, submits a form, stores credentials, mutates source, writes Git state, creates a pull request, merges, deploys, or trains model weights.

## AION-205 Controlled Research Acquisition Core

AION-205 implements the controlled research acquisition and immutable source-snapshot core as operator-invoked and runtime-disabled. Acquired content remains untrusted evidence; factual claim verification, knowledge promotion, cognitive belief mutation, public network fetch, crawler execution, search-provider integration, connector integration, source mutation, Git mutation, automatic merge, deployment, and model-weight training remain disabled. AION-204-KI-0001 is closed by AION-206; AION-206-KI-0002 is active for AION-207 source registry authorization.


## AION-206 source registry authorization

AION-206 records `RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION`, closes `AION-204-KI-0001`, and creates `AION-206-KI-0002` for AION-207 only. The source registry core is implemented as immutable in-memory metadata only; runtime, persistent registry writes, network, source body persistence, claim verification, knowledge promotion, and belief mutation remain disabled pending AION-208 formal closeout.


## AION-208 Knowledge Intelligence State

AION-208 completed read-only operator evaluation `AION-SPRE-001` for the AION-207 append-only source provenance registry. The registry remains metadata-only, in-memory, and persistent-write-disabled. `AION-206-KI-0002` is closed and non-reusable. `AION-208-KI-0003` is the sole active Knowledge Intelligence implementation authorization for AION-209. AION-209 may implement the temporal claim-evidence graph, but automatic claim extraction, truth decisions, confidence calculation, knowledge promotion, cognitive belief mutation, persistent graph writes, source-body storage, network access, source mutation, Git mutation, runtime PRs, automatic merge, deployment, and model training remain disabled.

## AION-209 Immutable Temporal Claim-Evidence Graph

AION-209 implements the temporal claim-evidence graph core under `AION-208-KI-0003`. The graph represents explicit unverified claims, source-registry evidence bindings, valid time, transaction time, jurisdiction, version scope, relations, structural conflict candidates, immutable in-memory projection, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

The current state is `implemented_append_only_in_memory_unverified_persistent_write_disabled`. `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `maximum_graph_write_batch=0`, `automatic_claim_extraction_enabled=false`, `claim_verification_enabled=false`, `truth_decision_enabled=false`, `epistemic_confidence_enabled=false`, `contradiction_resolution_enabled=false`, `knowledge_promotion_enabled=false`, and `belief_mutation_enabled=false`. AION-210 is the next formal closeout and evaluation task.

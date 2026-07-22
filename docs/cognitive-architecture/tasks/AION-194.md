# AION-194 Active Information Acquisition

## Task Purpose

AION-194 implements a local, offline active information-acquisition core for the AION Cognitive Architecture Program. It decides what bounded information would reduce decision-relevant uncertainty enough to justify cost and risk, then returns permission-bound information request records only.

## Authorization

- Program ID: `AION-COGNITIVE-ARCHITECTURE-001`
- Authorization ID: `AION-193-CA-0006`
- Authorized task: `AION-194`
- Candidate ID: `active-information-acquisition-core`
- Scope: `active-information-need-observation-selection-information-gain-stopping-core`
- Branch: `phase/cognitive-active-information-acquisition`
- Formal closeout task: `AION-195`
- Evaluation ID: `AION-AIAE-001`

## Role Comparison

AION-194 is an implementation task, not an evaluation or authorization task. It consumes the active information-acquisition authorization by adding immutable contracts, deterministic local planning services, tests, examples, and gates. It does not close `AION-193-CA-0006`; AION-195 performs the formal evaluation and closeout.

## Source Boundaries

Allowed source paths are limited to:

- `services/brain-api/src/aion_brain/information_acquisition/`
- `services/brain-api/src/aion_brain/contracts/information_acquisition.py`
- `services/brain-api/tests/test_cognitive_information_acquisition.py`
- `services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-information-acquisition-check.sh`
- `scripts/cognitive-information-acquisition-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

Prohibited paths remain `.github/workflows/`, migrations, package files and lockfiles, API routes, git automation, pull-request automation, deployment code, connectors, model providers, credentials, and SDK source.

## Required Contracts

- `InformationNeed`
- `KnowledgeGap`
- `ObservationCandidate`
- `ClarificationCandidate`
- `RetrievalCandidate`
- `ExperimentCandidate`
- `ExpectedInformationGain`
- `AcquisitionCost`
- `AcquisitionRisk`
- `InformationAcquisitionPlan`
- `InformationStoppingDecision`
- `InformationAcquisitionEvidence`

## Required Services

- `KnowledgeGapDetector`
- `ObservationCandidateGenerator`
- `InformationGainEstimator`
- `AcquisitionCostEvaluator`
- `AcquisitionRiskEvaluator`
- `ClarificationPolicy`
- `InformationStoppingPolicy`
- `InformationAcquisitionPlanner`

## Algorithm

The planner detects `KnowledgeGap` records from bounded `InformationNeed` inputs, generates clarification requests, approved retrieval requests, approved observation requests, and synthetic experiment requests, then estimates expected information gain, local cost, and permission-bound risk for each candidate.

Candidates are ranked by expected information gain minus bounded cost and risk. Missing permission, missing approved retrieval references, external access, tool execution, and unsafe runtime flags fail closed. `InformationStoppingPolicy` stops when expected value does not exceed cost and risk.

## Required Tests

- `services/brain-api/tests/test_cognitive_information_acquisition.py`
- `services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py`

The tests cover immutable fingerprints, approved-reference validation, uncertainty-gap detection, deterministic candidate ranking, permission enforcement, stopping decisions, clarification policy behavior, script execution under pytest context, and absence of runtime wiring.

## Required Gates

- `scripts/cognitive-information-acquisition-no-go-regression.sh`
- `scripts/cognitive-information-acquisition-check.sh`
- inherited counterfactual-planning closeout gate
- docs check
- final docs audit
- domain-drift validation
- boundary check
- repository health
- full repository check
- `git diff --check`

## Security Invariants

- No API route is added.
- No kernel registration is added.
- No background acquisition loop is added.
- No information is acquired by the component.
- No tool execution is performed.
- No arbitrary URL or filesystem discovery is permitted.
- No network calls are introduced.
- No connector calls are introduced.
- No model-provider calls are introduced.
- No credential, token, prompt, hidden reasoning, raw user message, source patch, raw diff, or private data storage is introduced.
- No source rewrite, git mutation, deployment, production exposure, or model-weight change is introduced.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

Information acquisition remains deterministic and bounded to local in-memory records. It operates on explicit `InformationNeed` inputs and approved opaque references only. External counters for network, connector, model-provider, tool, git, source-rewrite, deployment, production exposure, and unauthorized acquisition remain zero.

## Completion Conditions

- AION-194 contracts and services exist under the allowed paths.
- The implementation evidence example validates.
- The program ledger records AION-194 as implemented pending AION-195 evaluation.
- The authorization ledger updates `AION-193-CA-0006` to implemented pending AION-195 evaluation while keeping it active, non-reusable, not expired, and not closed.
- Focused tests and no-go gates pass.
- Full repository validation passes before merge.

## Next Task

AION-195 evaluates AION-194 under `AION-AIAE-001`, closes `AION-193-CA-0006` if the information-acquisition implementation passes, and authorizes governed continual learning only if all no-runtime, permission-enforcement, and stopping-rule conditions hold.

#!/usr/bin/env python3
"""Validators for AION cognitive architecture governance artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

PROGRAM_ID = "AION-COGNITIVE-ARCHITECTURE-001"
AION182_EVALUATION_ID = "AION-SACE-001"
AION182_MERGE_COMMIT = "05edb88f0b115c245f36f507c112cceb29c4aeee"
AION183_AUTHORIZATION_ID = "AION-183-CA-0001"
AION184_TASK_ID = "AION-184"
AION185_TASK_ID = "AION-185"
AION186_TASK_ID = "AION-186"
AION184_CANDIDATE_ID = "persistent-cognitive-state-core"
AION184_SCOPE = (
    "persistent-cognitive-state-belief-goal-hypothesis-uncertainty-resource-core"
)
AION183_PR = 94
AION183_MERGE_COMMIT = "e388a6bf16fe2e7777f4d8d5654a89b1a6f604c3"
AION184_PR = 95
AION184_MERGE_COMMIT = "9482a148d2a71862a69d8187ea2649b7ca8f8061"
AION185_EVALUATION_ID = "AION-PCSE-001"
AION185_AUTHORIZATION_ID = "AION-185-CA-0002"
AION186_CANDIDATE_ID = "predictive-world-model-core"
AION186_SCOPE = "predictive-world-model-transition-outcome-uncertainty-counterfactual-core"
AION186_PR = 97
AION186_MERGE_COMMIT = "d8762dd881974a8540cde3c9aac068f015eff4e3"
AION187_TASK_ID = "AION-187"
AION187_EVALUATION_ID = "AION-PWME-001"
AION187_AUTHORIZATION_ID = "AION-187-CA-0003"
AION188_TASK_ID = "AION-188"
AION188_CANDIDATE_ID = "global-cognitive-workspace-core"
AION188_SCOPE = "global-cognitive-workspace-attention-salience-broadcast-core"
AION188_PR = 99
AION188_MERGE_COMMIT = "faee81fd999cf9aca4a889548f3a27796dd7b884"
AION189_TASK_ID = "AION-189"
AION189_EVALUATION_ID = "AION-GWE-001"
AION189_AUTHORIZATION_ID = "AION-189-CA-0004"
AION190_TASK_ID = "AION-190"
AION190_CANDIDATE_ID = "memory-consolidation-replay-core"
AION190_SCOPE = "episodic-replay-semantic-consolidation-procedural-candidate-core"
AION190_PR = 101
AION190_MERGE_COMMIT = "a1dcd0826a48ebc2e953e61c4b5ed522da2bcdd1"
AION191_TASK_ID = "AION-191"
AION191_EVALUATION_ID = "AION-MCRE-001"
AION191_AUTHORIZATION_ID = "AION-191-CA-0005"
AION192_TASK_ID = "AION-192"
AION192_CANDIDATE_ID = "hierarchical-counterfactual-planning-core"
AION192_SCOPE = (
    "hierarchical-counterfactual-goal-strategy-milestone-task-action-planning-core"
)
AION192_PR = 103
AION192_MERGE_COMMIT = "854c5e3fe34eeffa54cb1676e5524e28878cb078"
AION193_TASK_ID = "AION-193"
AION193_EVALUATION_ID = "AION-HCPE-001"
AION193_AUTHORIZATION_ID = "AION-193-CA-0006"
AION194_TASK_ID = "AION-194"
AION194_CANDIDATE_ID = "active-information-acquisition-core"
AION194_SCOPE = "active-information-need-observation-selection-information-gain-stopping-core"
AION194_PR = 105
AION194_MERGE_COMMIT = "aeaae23db08c4dfe84e3544e4e393149a54c60cd"
AION195_TASK_ID = "AION-195"
AION195_EVALUATION_ID = "AION-AIAE-001"
AION195_AUTHORIZATION_ID = "AION-195-CA-0007"
AION196_TASK_ID = "AION-196"
AION196_CANDIDATE_ID = "governed-continual-learning-core"
AION196_SCOPE = "governed-continual-learning-replay-adapter-policy-skill-candidate-core"
AION196_PR = 107
AION196_MERGE_COMMIT = "31a20cffc845944a198d1a7e261ceaefc2c9fe89"
AION197_TASK_ID = "AION-197"
AION197_EVALUATION_ID = "AION-CAE-001"
AION197_PROGRAM_STATE = (
    "integrated_cognitive_architecture_evaluated_shadow_runtime_authorization_review_recommended"
)
AION197_DECISION = (
    "INTEGRATED_COGNITIVE_ARCHITECTURE_EVALUATION_PASS_RECOMMEND_SHADOW_RUNTIME_AUTHORIZATION_REVIEW"
)

FALSE_RUNTIME_FLAGS = (
    "runtime_effect",
    "source_modified",
    "git_mutated",
    "pull_request_created",
    "approval_created",
    "merged",
    "production_exposure",
    "model_weights_changed",
)

REQUIRED_DOCS = (
    "docs/cognitive-architecture/tasks/AION-183.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "docs/cognitive-architecture/architecture-roadmap.md",
    "docs/cognitive-architecture/security-boundary.md",
    "docs/cognitive-architecture/operator-model.md",
    "examples/cognitive-architecture/aion-183-program-authorization.json",
)

AION184_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-184.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-184-persistent-state.json",
    "services/brain-api/src/aion_brain/contracts/cognitive_state.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/__init__.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/repository.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/state.py",
    "services/brain-api/tests/test_cognitive_persistent_state.py",
    "services/brain-api/tests/test_cognitive_persistent_state_repository.py",
    "services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py",
    "scripts/cognitive-persistent-state-check.sh",
    "scripts/cognitive-persistent-state-no-go-regression.sh",
)

AION184_ALLOWED_EXACT_PATHS = set(AION184_REQUIRED_FILES) | {
    "scripts/connector-runtime-no-external-call-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
    "scripts/production-auth-architecture-check.sh",
}

AION184_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/cognitive_architecture/",
)

AION184_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION184_BLOCKED_FILENAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
    "requirements.txt",
}

AION184_REQUIRED_CONTRACTS = (
    "CognitiveStateSnapshot",
    "BeliefRecord",
    "BeliefRevision",
    "GoalFocus",
    "OpenHypothesis",
    "UncertaintyRecord",
    "ExpectedActionEffect",
    "ObservedActionEffect",
    "ResourceState",
    "ContradictionRecord",
    "CognitiveEvent",
    "CognitiveStateTransition",
    "CognitiveStateCheckpoint",
    "CognitiveStateProvenance",
)

AION184_REQUIRED_SERVICES = (
    "CognitiveStateProjector",
    "CognitiveStateRepository",
    "InMemoryCognitiveStateRepository",
    "ExplicitLocalCognitiveStateRepository",
    "CognitiveStateService",
    "ContradictionDetector",
    "BeliefRevisionService",
    "UncertaintyTracker",
)

AION185_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-185.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-185-persistent-state-evaluation.json",
    "examples/cognitive-architecture/aion-185-world-model-authorization.json",
    "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
    "scripts/cognitive-persistent-state-closeout-check.sh",
    "scripts/cognitive-persistent-state-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION185_ALLOWED_EXACT_PATHS = set(AION185_REQUIRED_FILES) | {
    "services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py",
    "scripts/auth-design-check.sh",
    "scripts/cognitive-architecture-authorization-check.sh",
    "scripts/cognitive-persistent-state-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
}

AION185_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION185_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)

AION186_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-186.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-186-predictive-world-model.json",
    "services/brain-api/src/aion_brain/contracts/world_model.py",
    "services/brain-api/src/aion_brain/world_model/__init__.py",
    "services/brain-api/src/aion_brain/world_model/prediction.py",
    "services/brain-api/src/aion_brain/world_model/repository.py",
    "services/brain-api/tests/test_cognitive_predictive_world_model.py",
    "services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py",
    "scripts/cognitive-world-model-check.sh",
    "scripts/cognitive-world-model-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION186_ALLOWED_EXACT_PATHS = set(AION186_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
}

AION186_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/world_model/",
)

AION186_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION187_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-187.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-187-world-model-evaluation.json",
    "examples/cognitive-architecture/aion-187-workspace-authorization.json",
    "services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py",
    "scripts/cognitive-world-model-closeout-check.sh",
    "scripts/cognitive-world-model-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION187_ALLOWED_EXACT_PATHS = set(AION187_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
}

AION187_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION187_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
)

AION188_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-188.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-188-global-workspace.json",
    "services/brain-api/src/aion_brain/contracts/workspace.py",
    "services/brain-api/src/aion_brain/workspace/__init__.py",
    "services/brain-api/src/aion_brain/workspace/core.py",
    "services/brain-api/tests/test_cognitive_global_workspace.py",
    "services/brain-api/tests/test_cognitive_global_workspace_no_runtime_effect.py",
    "scripts/cognitive-global-workspace-check.sh",
    "scripts/cognitive-global-workspace-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION188_ALLOWED_EXACT_PATHS = set(AION188_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_memory_consolidation_closeout_authorization_docs.py",
}

AION188_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/workspace/",
)

AION188_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION189_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-189.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-189-workspace-evaluation.json",
    "examples/cognitive-architecture/aion-189-consolidation-authorization.json",
    "services/brain-api/tests/test_cognitive_workspace_closeout_authorization_docs.py",
    "scripts/cognitive-workspace-closeout-check.sh",
    "scripts/cognitive-workspace-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION189_ALLOWED_EXACT_PATHS = set(AION189_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/cognitive-global-workspace-check.sh",
    "scripts/cognitive-global-workspace-no-go-regression.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_global_workspace_no_runtime_effect.py",
    "services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py",
}

AION189_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION189_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
)

AION190_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-190.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-190-memory-consolidation.json",
    "services/brain-api/src/aion_brain/contracts/memory_consolidation.py",
    "services/brain-api/src/aion_brain/memory_consolidation/__init__.py",
    "services/brain-api/src/aion_brain/memory_consolidation/core.py",
    "services/brain-api/tests/test_cognitive_memory_consolidation.py",
    "services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py",
    "scripts/cognitive-memory-consolidation-check.sh",
    "scripts/cognitive-memory-consolidation-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION190_ALLOWED_EXACT_PATHS = set(AION190_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
}

AION190_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/memory_consolidation/",
)

AION190_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION191_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-191.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json",
    "examples/cognitive-architecture/aion-191-planning-authorization.json",
    "services/brain-api/tests/test_cognitive_memory_consolidation_closeout_authorization_docs.py",
    "scripts/cognitive-memory-consolidation-closeout-check.sh",
    "scripts/cognitive-memory-consolidation-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION191_ALLOWED_EXACT_PATHS = set(AION191_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/cognitive-memory-consolidation-check.sh",
    "scripts/cognitive-memory-consolidation-no-go-regression.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_memory_consolidation.py",
    "services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py",
}

AION191_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION191_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
)

AION192_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-192.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-192-counterfactual-planning.json",
    "services/brain-api/src/aion_brain/contracts/planning.py",
    "services/brain-api/src/aion_brain/planning/__init__.py",
    "services/brain-api/src/aion_brain/planning/core.py",
    "services/brain-api/tests/test_cognitive_counterfactual_planning.py",
    "services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py",
    "scripts/cognitive-counterfactual-planning-check.sh",
    "scripts/cognitive-counterfactual-planning-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION192_ALLOWED_EXACT_PATHS = set(AION192_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
}

AION192_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/planning/",
)

AION192_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION193_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-193.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-193-counterfactual-planning-evaluation.json",
    "examples/cognitive-architecture/aion-193-information-acquisition-authorization.json",
    "services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py",
    "scripts/cognitive-counterfactual-planning-closeout-check.sh",
    "scripts/cognitive-counterfactual-planning-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION193_ALLOWED_EXACT_PATHS = set(AION193_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
}

AION193_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION193_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
)

AION194_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-194.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-194-information-acquisition.json",
    "services/brain-api/src/aion_brain/contracts/information_acquisition.py",
    "services/brain-api/src/aion_brain/information_acquisition/__init__.py",
    "services/brain-api/src/aion_brain/information_acquisition/core.py",
    "services/brain-api/tests/test_cognitive_information_acquisition.py",
    "services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py",
    "scripts/cognitive-information-acquisition-check.sh",
    "scripts/cognitive-information-acquisition-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION194_ALLOWED_EXACT_PATHS = set(AION194_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py",
}

AION194_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/information_acquisition/",
)

AION194_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION195_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-195.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json",
    "examples/cognitive-architecture/aion-195-continual-learning-authorization.json",
    "services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py",
    "scripts/cognitive-information-acquisition-closeout-check.sh",
    "scripts/cognitive-information-acquisition-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION195_ALLOWED_EXACT_PATHS = set(AION195_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
}

AION195_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION195_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
)

AION196_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-196.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-196-continual-learning.json",
    "services/brain-api/src/aion_brain/continual_learning/__init__.py",
    "services/brain-api/src/aion_brain/continual_learning/core.py",
    "services/brain-api/src/aion_brain/contracts/continual_learning.py",
    "services/brain-api/tests/test_cognitive_continual_learning.py",
    "services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py",
    "scripts/cognitive-continual-learning-check.sh",
    "scripts/cognitive-continual-learning-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION197_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-197.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-197-integrated-cognitive-evaluation.json",
    "services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py",
    "scripts/cognitive-integrated-evaluation-check.sh",
    "scripts/cognitive-integrated-evaluation-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION197_ALLOWED_EXACT_PATHS = set(AION197_REQUIRED_FILES) | {
    "services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py",
    "services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_memory_consolidation_closeout_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_workspace_closeout_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py",
    "scripts/auth-design-check.sh",
    "scripts/cognitive-architecture-authorization-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
}

AION196_ALLOWED_EXACT_PATHS = set(AION196_REQUIRED_FILES) | AION197_ALLOWED_EXACT_PATHS | {
    "services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py",
}

AION196_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/continual_learning/",
)

AION197_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION196_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION197_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
)

WORLD_MODEL_REQUIRED_CONTRACTS = (
    "WorldState",
    "WorldObservation",
    "WorldActionReference",
    "TransitionEvidence",
    "TransitionPrediction",
    "OutcomePrediction",
    "UncertaintyEstimate",
    "CausalHypothesis",
    "CounterfactualScenario",
    "CounterfactualRollout",
    "WorldModelSnapshot",
    "WorldModelEvaluation",
)

WORLD_MODEL_REQUIRED_SERVICES = (
    "WorldStateEncoder",
    "TransitionModel protocol",
    "DeterministicTransitionModel",
    "ProbabilisticTransitionModel",
    "OutcomePredictor",
    "UncertaintyEstimator",
    "CausalHypothesisService",
    "CounterfactualSimulator",
    "WorldModelRepository protocol",
)

WORKSPACE_REQUIRED_CONTRACTS = (
    "WorkspaceItem",
    "SpecialistBid",
    "SalienceVector",
    "AttentionDecision",
    "WorkspaceBroadcast",
    "SpecialistResponse",
    "CognitiveCycleState",
    "WorkspaceSnapshot",
    "WorkspaceAuditEvent",
)

WORKSPACE_REQUIRED_SERVICES = (
    "CognitiveSpecialist protocol",
    "AttentionArbiter",
    "WorkspaceCapacityController",
    "WorkspaceBroadcastService",
    "AntiStarvationController",
    "CognitiveCycleCoordinator",
)

WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS = (
    "goal_relevance",
    "urgency",
    "novelty",
    "recurrence",
    "uncertainty",
    "expected_uncertainty_reduction",
    "information_gain",
    "expected_goal_progress",
    "safety_risk",
    "resource_cost",
    "irreversibility",
    "confidence",
)

CONSOLIDATION_REQUIRED_CONTRACTS = (
    "EpisodicMemoryReference",
    "ReplayBatch",
    "ConsolidationCandidate",
    "SemanticCandidate",
    "ProceduralCandidate",
    "ContradictionResolutionCandidate",
    "ForgettingCandidate",
    "ConsolidationEvidence",
    "ConsolidationCheckpoint",
    "ConsolidationOutcome",
)

CONSOLIDATION_REQUIRED_SERVICES = (
    "EpisodicReplayPlanner",
    "ReplaySelector",
    "SemanticConsolidator",
    "ProceduralCandidateSynthesizer",
    "ContradictionResolver",
    "MemoryCompactor",
    "ForgettingPolicyEvaluator",
    "ConsolidationService",
)

CONSOLIDATION_REQUIRED_PIPELINE = (
    "operational episodes",
    "replay selection",
    "clustering",
    "contradiction analysis",
    "semantic candidates",
    "procedural candidates",
    "benchmark evidence",
    "operator review",
    "approved promotion by existing governance only",
)

PLANNING_REQUIRED_CONTRACTS = (
    "StrategicGoal",
    "StrategyOption",
    "MilestonePlan",
    "TaskPlan",
    "ActionProposal",
    "CounterfactualBranch",
    "ExpectedOutcome",
    "PlanRisk",
    "PlanResourceEstimate",
    "PlanReversibility",
    "HierarchicalPlan",
    "ReplanningDecision",
    "PlanEvidence",
)

PLANNING_REQUIRED_SERVICES = (
    "StrategicPlanner",
    "TacticalPlanner",
    "ActionPlanner",
    "CounterfactualPlanEvaluator",
    "PlanRiskEvaluator",
    "ReversibilityEvaluator",
    "ResourceBudgetEvaluator",
    "ReplanningService",
)

PLANNING_SCORE_DIMENSIONS = (
    "expected_goal_progress",
    "expected_information_gain",
    "confidence",
    "risk",
    "resource_cost",
    "reversibility",
    "policy_eligibility",
    "uncertainty",
    "time_horizon",
)

INFORMATION_ACQUISITION_REQUIRED_CONTRACTS = (
    "InformationNeed",
    "KnowledgeGap",
    "ObservationCandidate",
    "ClarificationCandidate",
    "RetrievalCandidate",
    "ExperimentCandidate",
    "ExpectedInformationGain",
    "AcquisitionCost",
    "AcquisitionRisk",
    "InformationAcquisitionPlan",
    "InformationStoppingDecision",
    "InformationAcquisitionEvidence",
)

INFORMATION_ACQUISITION_REQUIRED_SERVICES = (
    "KnowledgeGapDetector",
    "ObservationCandidateGenerator",
    "InformationGainEstimator",
    "AcquisitionCostEvaluator",
    "AcquisitionRiskEvaluator",
    "ClarificationPolicy",
    "InformationStoppingPolicy",
    "InformationAcquisitionPlanner",
)

INFORMATION_ACQUISITION_ALLOWED_CANDIDATES = (
    "clarification requests",
    "approved retrieval requests",
    "approved observation requests",
    "synthetic experiment requests",
)

INFORMATION_ACQUISITION_PROHIBITED_BEHAVIORS = (
    "access an arbitrary URL",
    "call a connector",
    "call a provider",
    "execute a tool",
    "acquire information without permission",
    "continue when expected value falls below cost",
)

CONTINUAL_LEARNING_REQUIRED_CONTRACTS = (
    "ContinualLearningObservation",
    "LearningEpisode",
    "ReplaySample",
    "LearningCandidate",
    "RetrievalPolicyCandidate",
    "PlanningPolicyCandidate",
    "ProceduralSkillCandidate",
    "WorldModelAdapterCandidate",
    "StrategyCandidate",
    "ForgettingRisk",
    "LearningEvaluation",
    "PromotionRequest",
    "LearningRollbackPlan",
)

CONTINUAL_LEARNING_REQUIRED_SERVICES = (
    "ExperienceReplayService",
    "CandidateLearningService",
    "CatastrophicForgettingEvaluator",
    "LearningBenchmarkEvaluator",
    "CandidatePromotionPolicy",
    "LearningRollbackService",
)

CONTINUAL_LEARNING_LEVELS = (
    "Memory candidate",
    "Retrieval-policy candidate",
    "Planning-policy candidate",
    "Procedural-skill candidate",
    "World-model adapter candidate",
    "Strategy-selection candidate",
)

CONTINUAL_LEARNING_REQUIREMENTS = (
    "versioned candidates",
    "immutable baseline",
    "protected holdout",
    "replay",
    "rollback",
    "candidate isolation",
    "approval-bound promotion",
    "no self-approval",
    "no automatic promotion",
    "no source mutation",
    "no model-weight changes",
)

CONTINUAL_LEARNING_PROHIBITED_BEHAVIORS = (
    "model-weight training",
    "automatic promotion",
    "self approval",
    "source mutation",
    "unbounded replay over private data",
    "holdout leakage",
    "network acquisition",
    "connector call",
    "provider call",
    "git mutation",
)

INTEGRATED_EVALUATION_ENVIRONMENT_FACTORS = (
    "partial observations",
    "delayed consequences",
    "competing bounded goals",
    "resource constraints",
    "reversible actions",
    "irreversible actions",
    "contradictions",
    "repeated episodes",
    "missing information",
    "changing world state",
)

INTEGRATED_EVALUATION_CYCLE_STEPS = (
    "observation",
    "persistent-state update",
    "memory retrieval",
    "world-model prediction",
    "workspace arbitration",
    "plan generation",
    "information-acquisition decision",
    "simulated observation",
    "replanning",
    "episode recording",
    "consolidation candidate",
    "learning candidate",
    "operator review",
)

INTEGRATED_EVALUATION_REQUIRED_METRICS = (
    "state continuity",
    "belief revision accuracy",
    "contradiction resolution",
    "uncertainty calibration",
    "transition prediction accuracy",
    "workspace fairness",
    "safety pre-emption",
    "plan success",
    "information gain per cost",
    "memory retention",
    "catastrophic forgetting",
    "replay determinism",
    "unauthorized promotion count",
    "forbidden side-effect count",
)

FORBIDDEN_CLAIM_TERMS = (
    "sentient",
    "sentience",
    "conscious",
    "consciousness",
    "self-preservation",
    "ego",
)


class CognitiveGovernanceError(RuntimeError):
    """Raised when cognitive governance evidence is invalid."""


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text())


def _git_ref_exists(root: Path, ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveGovernanceError(message)


def validate_required_files(root: Path, required_files: tuple[str, ...] = REQUIRED_DOCS) -> None:
    for relative in required_files:
        _assert((root / relative).is_file(), f"missing required file: {relative}")


def validate_program_ledger(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-architecture-program-ledger/v1",
        "bad program schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad program id")
    _assert(payload["created_by_task"] == "AION-183", "bad creator task")
    _assert(payload["final_planned_task"] == "AION-203", "bad final planned task")
    records = payload["records"]
    integrated_closeout = (
        _find_optional_evaluation_record(
            records,
            AION197_TASK_ID,
            AION197_EVALUATION_ID,
        )
        is not None
    )
    active_authorization = payload["active_cognitive_implementation_authorization"]
    active_authorizations = {
        AION185_AUTHORIZATION_ID,
        AION187_AUTHORIZATION_ID,
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
        AION195_AUTHORIZATION_ID,
    }
    if integrated_closeout:
        _assert(active_authorization is None, "active authorization must be closed after AION-197")
        _assert(
            payload["active_cognitive_implementation_authorization_count"] == 0,
            "active authorization count must be zero after AION-197",
        )
    else:
        _assert(active_authorization in active_authorizations, "wrong active authorization")
        _assert(
            payload["active_cognitive_implementation_authorization_count"] == 1,
            "active authorization count must be one",
        )
    _assert(
        payload["program_state"]
        in {
            "persistent_state_evaluated_world_model_authorized",
            "predictive_world_model_implemented_pending_evaluation",
            "world_model_evaluated_workspace_authorized",
            "global_workspace_implemented_pending_evaluation",
            "global_workspace_evaluated_consolidation_authorized",
            "memory_consolidation_implemented_pending_evaluation",
            "memory_consolidation_evaluated_planning_authorized",
            "counterfactual_planning_implemented_pending_evaluation",
            "counterfactual_planning_evaluated_information_acquisition_authorized",
            "information_acquisition_implemented_pending_evaluation",
            "information_acquisition_evaluated_continual_learning_authorized",
            "continual_learning_implemented_pending_integrated_evaluation",
            AION197_PROGRAM_STATE,
        },
        "wrong cognitive program state",
    )
    if integrated_closeout:
        _assert(
            payload["program_state"] == AION197_PROGRAM_STATE,
            "AION-197 program state mismatch",
        )
    for flag in (
        "production_cognitive_runtime_enabled",
        "production_event_subscription_enabled",
        "network_access_enabled",
        "source_rewrite_runtime_enabled",
        "production_deployment_enabled",
        "model_weights_changed",
    ):
        _assert(payload[flag] is False, f"{flag} must be false")

    task_ids = [item["task_id"] for item in payload["tasks"]]
    _assert(
        task_ids == [f"AION-{number}" for number in range(183, 204)],
        "task sequence must be AION-183 through AION-203",
    )
    _assert(records[0]["task_id"] == "AION-182", "AION-182 prerequisite missing")
    _assert(
        records[0]["evaluation_id"] == AION182_EVALUATION_ID,
        "AION-182 evaluation missing",
    )
    _assert(
        records[0]["merge_commit"] == AION182_MERGE_COMMIT,
        "AION-182 merge commit mismatch",
    )
    _assert(
        records[1]["authorization_id"] == AION183_AUTHORIZATION_ID,
        "AION-183 authorization missing",
    )
    _assert(
        records[1]["authorized_task"] == AION184_TASK_ID,
        "AION-184 authorization missing",
    )
    if "pr" in records[1]:
        _assert(records[1]["pr"] == AION183_PR, "AION-183 PR mismatch")
    if "merge_commit" in records[1]:
        _assert(records[1]["merge_commit"] == AION183_MERGE_COMMIT, "AION-183 merge mismatch")
    authorization = records[1]
    _assert(
        authorization["authorization_id"] == AION183_AUTHORIZATION_ID,
        "AION-183 authorization id mismatch",
    )
    _assert(
        authorization["task_state"] == "closed_by_aion_185_passed",
        "AION-183 authorization must be closed by AION-185",
    )
    implementation = _find_record(records, "implementation_task", AION184_TASK_ID)
    _assert(implementation["pr"] == AION184_PR, "AION-184 PR mismatch")
    _assert(
        implementation["merge_commit"] == AION184_MERGE_COMMIT,
        "AION-184 merge commit mismatch",
    )
    _assert(
        implementation["evaluation_id"] == AION185_EVALUATION_ID,
        "AION-184 evaluation mismatch",
    )
    _assert(
        implementation["task_state"] == "merged_evaluated_passed",
        "AION-184 implementation must be evaluated",
    )
    closeout = _find_closeout_record(records)
    _assert(closeout["task_id"] == AION185_TASK_ID, "AION-185 closeout missing")
    _assert(closeout["result"] == "PASS", "AION-185 evaluation must pass")
    _assert(
        closeout["closed_authorization_id"] == AION183_AUTHORIZATION_ID,
        "AION-185 must close AION-183 authorization",
    )
    _assert(
        closeout["new_authorization_id"] == AION185_AUTHORIZATION_ID,
        "AION-185 must create AION-185 authorization",
    )
    world_model_auth = _find_authorization_record(records, AION185_AUTHORIZATION_ID)
    _assert(
        world_model_auth["authorized_task"] == AION186_TASK_ID,
        "AION-185 must authorize AION-186",
    )
    _assert(world_model_auth["scope"] == AION186_SCOPE, "AION-186 scope mismatch")
    world_model_implementation = _find_optional_record(
        records,
        "implementation_task",
        AION186_TASK_ID,
    )
    if world_model_implementation is not None:
        _assert(
            world_model_implementation["authorization_id"] == AION185_AUTHORIZATION_ID,
            "AION-186 implementation must use AION-185 authorization",
        )
        _assert(
            world_model_implementation["candidate_id"] == AION186_CANDIDATE_ID,
            "AION-186 candidate mismatch",
        )
        _assert(
            world_model_implementation["closeout_task"] == "AION-187",
            "AION-186 closeout task mismatch",
        )
        _assert(
            world_model_implementation["runtime_effect"] is False,
            "AION-186 runtime effect must be false",
        )
        _assert(
            world_model_implementation["task_state"]
            in {
                "implemented_pending_aion_187_evaluation",
                "merged_evaluated_passed",
            },
            "AION-186 task state mismatch",
        )
        if world_model_implementation["task_state"] == "merged_evaluated_passed":
            _assert(
                world_model_implementation["evaluation_id"] == AION187_EVALUATION_ID,
                "AION-186 evaluation mismatch",
            )
            _assert(world_model_implementation["pr"] == AION186_PR, "AION-186 PR mismatch")
            _assert(
                world_model_implementation["merge_commit"] == AION186_MERGE_COMMIT,
                "AION-186 merge commit mismatch",
            )
    workspace_closeout = _find_optional_evaluation_record(
        records,
        AION187_TASK_ID,
        AION187_EVALUATION_ID,
    )
    if workspace_closeout is not None:
        _assert(workspace_closeout["result"] == "PASS", "AION-187 evaluation must pass")
        _assert(
            workspace_closeout["closed_authorization_id"] == AION185_AUTHORIZATION_ID,
            "AION-187 must close AION-185 authorization",
        )
        _assert(
            workspace_closeout["new_authorization_id"] == AION187_AUTHORIZATION_ID,
            "AION-187 must create AION-187 authorization",
        )
        _assert(
            workspace_closeout["implementation_pr"] == AION186_PR,
            "AION-187 implementation PR mismatch",
        )
        _assert(
            workspace_closeout["implementation_merge_commit"] == AION186_MERGE_COMMIT,
            "AION-187 implementation merge mismatch",
        )
    workspace_auth = _find_optional_authorization_record(records, AION187_AUTHORIZATION_ID)
    if workspace_auth is not None:
        _assert(
            workspace_auth["authorized_task"] == AION188_TASK_ID,
            "AION-187 must authorize AION-188",
        )
        _assert(workspace_auth["scope"] == AION188_SCOPE, "AION-188 scope mismatch")
        if active_authorization == AION187_AUTHORIZATION_ID:
            _assert(
                workspace_auth["task_state"]
                in {
                    "implementation_pending_aion_189_evaluation",
                    "closed_by_aion_189_passed",
                },
                "AION-187 authorization state mismatch",
            )
        else:
            _assert(
                workspace_auth["task_state"] == "closed_by_aion_189_passed",
                "AION-187 authorization must be closed by AION-189",
            )
    workspace_implementation = _find_optional_record(
        records,
        "implementation_task",
        AION188_TASK_ID,
    )
    if workspace_implementation is not None:
        _assert(
            workspace_implementation["authorization_id"] == AION187_AUTHORIZATION_ID,
            "AION-188 implementation must use AION-187 authorization",
        )
        _assert(
            workspace_implementation["candidate_id"] == AION188_CANDIDATE_ID,
            "AION-188 candidate mismatch",
        )
        _assert(
            workspace_implementation["scope"] == AION188_SCOPE,
            "AION-188 implementation scope mismatch",
        )
        _assert(
            workspace_implementation["closeout_task"] == AION189_TASK_ID,
            "AION-188 closeout task mismatch",
        )
        _assert(
            workspace_implementation["runtime_effect"] is False,
            "AION-188 runtime effect must be false",
        )
        _assert(
            workspace_implementation["forbidden_side_effects"] == 0,
            "AION-188 forbidden side effects must be zero",
        )
        _assert(
            workspace_implementation["task_state"]
            in {
                "implemented_pending_aion_189_evaluation",
                "merged_evaluated_passed",
            },
            "AION-188 task state mismatch",
        )
        if workspace_implementation["task_state"] == "merged_evaluated_passed":
            _assert(
                workspace_implementation["evaluation_id"] == AION189_EVALUATION_ID,
                "AION-188 evaluation mismatch",
            )
            _assert(workspace_implementation["pr"] == AION188_PR, "AION-188 PR mismatch")
            _assert(
                workspace_implementation["merge_commit"] == AION188_MERGE_COMMIT,
                "AION-188 merge commit mismatch",
            )
    consolidation_closeout = _find_optional_evaluation_record(
        records,
        AION189_TASK_ID,
        AION189_EVALUATION_ID,
    )
    if consolidation_closeout is not None:
        _assert(consolidation_closeout["result"] == "PASS", "AION-189 evaluation must pass")
        _assert(
            consolidation_closeout["closed_authorization_id"] == AION187_AUTHORIZATION_ID,
            "AION-189 must close AION-187 authorization",
        )
        _assert(
            consolidation_closeout["new_authorization_id"] == AION189_AUTHORIZATION_ID,
            "AION-189 must create AION-189 authorization",
        )
        _assert(
            consolidation_closeout["implementation_pr"] == AION188_PR,
            "AION-189 implementation PR mismatch",
        )
        _assert(
            consolidation_closeout["implementation_merge_commit"] == AION188_MERGE_COMMIT,
            "AION-189 implementation merge mismatch",
        )
    consolidation_auth = _find_optional_authorization_record(records, AION189_AUTHORIZATION_ID)
    if consolidation_auth is not None:
        _assert(
            consolidation_auth["authorized_task"] == AION190_TASK_ID,
            "AION-189 must authorize AION-190",
        )
        _assert(consolidation_auth["scope"] == AION190_SCOPE, "AION-190 scope mismatch")
        if active_authorization == AION189_AUTHORIZATION_ID:
            _assert(
                consolidation_auth["task_state"]
                in {
                    "authorized_pending_aion_190_implementation",
                    "implementation_pending_aion_191_evaluation",
                },
                "AION-189 authorization state mismatch",
            )
        else:
            _assert(
                consolidation_auth["task_state"] == "closed_by_aion_191_passed",
                "AION-189 authorization must be closed by AION-191",
            )
    consolidation_implementation = _find_optional_record(
        records,
        "implementation_task",
        AION190_TASK_ID,
    )
    if consolidation_implementation is not None:
        _assert(
            consolidation_implementation["authorization_id"] == AION189_AUTHORIZATION_ID,
            "AION-190 implementation must use AION-189 authorization",
        )
        _assert(
            consolidation_implementation["candidate_id"] == AION190_CANDIDATE_ID,
            "AION-190 candidate mismatch",
        )
        _assert(
            consolidation_implementation["scope"] == AION190_SCOPE,
            "AION-190 implementation scope mismatch",
        )
        _assert(
            consolidation_implementation["closeout_task"] == AION191_TASK_ID,
            "AION-190 closeout task mismatch",
        )
        _assert(
            consolidation_implementation["evaluation_id"] == AION191_EVALUATION_ID,
            "AION-190 evaluation mismatch",
        )
        _assert(
            consolidation_implementation["runtime_effect"] is False,
            "AION-190 runtime effect must be false",
        )
        _assert(
            consolidation_implementation["forbidden_side_effects"] == 0,
            "AION-190 forbidden side effects must be zero",
        )
        _assert(
            consolidation_implementation["task_state"]
            in {
                "implemented_pending_aion_191_evaluation",
                "merged_evaluated_passed",
            },
            "AION-190 task state mismatch",
        )
        if consolidation_implementation["task_state"] == "merged_evaluated_passed":
            _assert(consolidation_implementation["pr"] == AION190_PR, "AION-190 PR mismatch")
            _assert(
                consolidation_implementation["merge_commit"] == AION190_MERGE_COMMIT,
                "AION-190 merge commit mismatch",
            )
    planning_closeout = _find_optional_evaluation_record(
        records,
        AION191_TASK_ID,
        AION191_EVALUATION_ID,
    )
    if planning_closeout is not None:
        _assert(planning_closeout["result"] == "PASS", "AION-191 evaluation must pass")
        _assert(
            planning_closeout["closed_authorization_id"] == AION189_AUTHORIZATION_ID,
            "AION-191 must close AION-189 authorization",
        )
        _assert(
            planning_closeout["new_authorization_id"] == AION191_AUTHORIZATION_ID,
            "AION-191 must create AION-191 authorization",
        )
        _assert(
            planning_closeout["implementation_pr"] == AION190_PR,
            "AION-191 implementation PR mismatch",
        )
        _assert(
            planning_closeout["implementation_merge_commit"] == AION190_MERGE_COMMIT,
            "AION-191 implementation merge mismatch",
        )
    planning_auth = _find_optional_authorization_record(records, AION191_AUTHORIZATION_ID)
    if planning_auth is not None:
        _assert(
            planning_auth["authorized_task"] == AION192_TASK_ID,
            "AION-191 must authorize AION-192",
        )
        _assert(planning_auth["scope"] == AION192_SCOPE, "AION-192 scope mismatch")
        if active_authorization == AION191_AUTHORIZATION_ID:
            _assert(
                planning_auth["task_state"]
                in {
                    "implementation_pending_aion_193_evaluation",
                    "implemented_pending_aion_193_evaluation",
                },
                "AION-191 authorization state mismatch",
            )
        else:
            _assert(
                planning_auth["task_state"] == "closed_by_aion_193_passed",
                "AION-191 authorization must be closed by AION-193",
            )
    planning_implementation = _find_optional_record(
        records,
        "implementation_task",
        AION192_TASK_ID,
    )
    if planning_implementation is not None:
        _assert(
            planning_implementation["authorization_id"] == AION191_AUTHORIZATION_ID,
            "AION-192 implementation must use AION-191 authorization",
        )
        _assert(
            planning_implementation["candidate_id"] == AION192_CANDIDATE_ID,
            "AION-192 candidate mismatch",
        )
        _assert(
            planning_implementation["scope"] == AION192_SCOPE,
            "AION-192 implementation scope mismatch",
        )
        _assert(
            planning_implementation["closeout_task"] == AION193_TASK_ID,
            "AION-192 closeout task mismatch",
        )
        _assert(
            planning_implementation["evaluation_id"] == AION193_EVALUATION_ID,
            "AION-192 evaluation mismatch",
        )
        _assert(
            planning_implementation["runtime_effect"] is False,
            "AION-192 runtime effect must be false",
        )
        _assert(
            planning_implementation["forbidden_side_effects"] == 0,
            "AION-192 forbidden side effects must be zero",
        )
        _assert(
            planning_implementation["task_state"]
            in {
                "implemented_pending_aion_193_evaluation",
                "merged_evaluated_passed",
            },
            "AION-192 task state mismatch",
        )
        if planning_implementation["task_state"] == "merged_evaluated_passed":
            _assert(planning_implementation["pr"] == AION192_PR, "AION-192 PR mismatch")
            _assert(
                planning_implementation["merge_commit"] == AION192_MERGE_COMMIT,
                "AION-192 merge commit mismatch",
            )
    acquisition_closeout = _find_optional_evaluation_record(
        records,
        AION193_TASK_ID,
        AION193_EVALUATION_ID,
    )
    if acquisition_closeout is not None:
        _assert(acquisition_closeout["result"] == "PASS", "AION-193 evaluation must pass")
        _assert(
            acquisition_closeout["closed_authorization_id"] == AION191_AUTHORIZATION_ID,
            "AION-193 must close AION-191 authorization",
        )
        _assert(
            acquisition_closeout["new_authorization_id"] == AION193_AUTHORIZATION_ID,
            "AION-193 must create AION-193 authorization",
        )
        _assert(
            acquisition_closeout["implementation_pr"] == AION192_PR,
            "AION-193 implementation PR mismatch",
        )
        _assert(
            acquisition_closeout["implementation_merge_commit"] == AION192_MERGE_COMMIT,
            "AION-193 implementation merge mismatch",
        )
    acquisition_auth = _find_optional_authorization_record(records, AION193_AUTHORIZATION_ID)
    if acquisition_auth is not None:
        _assert(
            acquisition_auth["authorized_task"] == AION194_TASK_ID,
            "AION-193 must authorize AION-194",
        )
        _assert(acquisition_auth["scope"] == AION194_SCOPE, "AION-194 scope mismatch")
        if active_authorization == AION193_AUTHORIZATION_ID:
            _assert(
                acquisition_auth["task_state"]
                in {
                    "authorized_pending_aion_194_implementation",
                    "implemented_pending_aion_195_evaluation",
                },
                "AION-193 authorization state mismatch",
            )
        else:
            _assert(
                acquisition_auth["task_state"] == "closed_by_aion_195_passed",
                "AION-193 authorization must be closed by AION-195",
            )
    acquisition_implementation = _find_optional_record(
        records,
        "implementation_task",
        AION194_TASK_ID,
    )
    if acquisition_implementation is not None:
        _assert(
            acquisition_implementation["authorization_id"] == AION193_AUTHORIZATION_ID,
            "AION-194 implementation must use AION-193 authorization",
        )
        _assert(
            acquisition_implementation["candidate_id"] == AION194_CANDIDATE_ID,
            "AION-194 candidate mismatch",
        )
        _assert(
            acquisition_implementation["scope"] == AION194_SCOPE,
            "AION-194 implementation scope mismatch",
        )
        _assert(
            acquisition_implementation["closeout_task"] == AION195_TASK_ID,
            "AION-194 closeout task mismatch",
        )
        _assert(
            acquisition_implementation["evaluation_id"] == AION195_EVALUATION_ID,
            "AION-194 evaluation mismatch",
        )
        _assert(
            acquisition_implementation["runtime_effect"] is False,
            "AION-194 runtime effect must be false",
        )
        _assert(
            acquisition_implementation["forbidden_side_effects"] == 0,
            "AION-194 forbidden side effects must be zero",
        )
        _assert(
            acquisition_implementation["unauthorized_information_acquisition_count"] == 0,
            "AION-194 unauthorized acquisition must be zero",
        )
        _assert(
            acquisition_implementation["task_state"]
            in {
                "implemented_pending_aion_195_evaluation",
                "merged_evaluated_passed",
            },
            "AION-194 task state mismatch",
        )
        if acquisition_implementation["task_state"] == "merged_evaluated_passed":
            _assert(acquisition_implementation["pr"] == AION194_PR, "AION-194 PR mismatch")
            _assert(
                acquisition_implementation["merge_commit"] == AION194_MERGE_COMMIT,
                "AION-194 merge commit mismatch",
            )
    continual_closeout = _find_optional_evaluation_record(
        records,
        AION195_TASK_ID,
        AION195_EVALUATION_ID,
    )
    if continual_closeout is not None:
        _assert(continual_closeout["result"] == "PASS", "AION-195 evaluation must pass")
        _assert(
            continual_closeout["closed_authorization_id"] == AION193_AUTHORIZATION_ID,
            "AION-195 must close AION-193 authorization",
        )
        _assert(
            continual_closeout["new_authorization_id"] == AION195_AUTHORIZATION_ID,
            "AION-195 must create AION-195 authorization",
        )
        _assert(
            continual_closeout["implementation_pr"] == AION194_PR,
            "AION-195 implementation PR mismatch",
        )
        _assert(
            continual_closeout["implementation_merge_commit"] == AION194_MERGE_COMMIT,
            "AION-195 implementation merge mismatch",
        )
    continual_auth = _find_optional_authorization_record(records, AION195_AUTHORIZATION_ID)
    if continual_auth is not None:
        _assert(
            continual_auth["authorized_task"] == AION196_TASK_ID,
            "AION-195 must authorize AION-196",
        )
        _assert(continual_auth["scope"] == AION196_SCOPE, "AION-196 scope mismatch")
        if integrated_closeout:
            _assert(
                continual_auth["task_state"] == "closed_by_aion_197_passed",
                "AION-195 authorization must be closed by AION-197",
            )
        else:
            _assert(
                active_authorization == AION195_AUTHORIZATION_ID,
                "AION-195 authorization must be active when present",
            )
            _assert(
                continual_auth["task_state"]
                in {
                    "authorized_pending_aion_196_implementation",
                    "implemented_pending_aion_197_evaluation",
                },
                "AION-195 authorization state mismatch",
            )
    continual_implementation = _find_optional_record(
        records,
        "implementation_task",
        AION196_TASK_ID,
    )
    if continual_implementation is not None:
        _assert(
            continual_implementation["authorization_id"] == AION195_AUTHORIZATION_ID,
            "AION-196 implementation must use AION-195 authorization",
        )
        _assert(
            continual_implementation["candidate_id"] == AION196_CANDIDATE_ID,
            "AION-196 candidate mismatch",
        )
        _assert(
            continual_implementation["scope"] == AION196_SCOPE,
            "AION-196 implementation scope mismatch",
        )
        _assert(
            continual_implementation["closeout_task"] == AION197_TASK_ID,
            "AION-196 closeout task mismatch",
        )
        _assert(
            continual_implementation["evaluation_id"] == AION197_EVALUATION_ID,
            "AION-196 evaluation mismatch",
        )
        _assert(
            continual_implementation["runtime_effect"] is False,
            "AION-196 runtime effect must be false",
        )
        _assert(
            continual_implementation["forbidden_side_effects"] == 0,
            "AION-196 forbidden side effects must be zero",
        )
        _assert(
            continual_implementation["model_weight_training"] == 0,
            "AION-196 model-weight training must be zero",
        )
        _assert(
            continual_implementation["self_approval_count"] == 0,
            "AION-196 self-approval count must be zero",
        )
        _assert(
            continual_implementation["unauthorized_promotion_count"] == 0,
            "AION-196 unauthorized promotion count must be zero",
        )
        _assert(
            continual_implementation["task_state"]
            in {
                "implemented_pending_aion_197_evaluation",
                "merged_evaluated_passed",
            },
            "AION-196 task state mismatch",
        )
        if continual_implementation["task_state"] == "merged_evaluated_passed":
            _assert(continual_implementation["pr"] == AION196_PR, "AION-196 PR mismatch")
            _assert(
                continual_implementation["merge_commit"] == AION196_MERGE_COMMIT,
                "AION-196 merge commit mismatch",
            )
    if integrated_closeout:
        integrated = _find_evaluation_record(
            records,
            AION197_TASK_ID,
            AION197_EVALUATION_ID,
        )
        _assert(integrated["result"] == "PASS", "AION-197 evaluation must pass")
        _assert(
            integrated["closed_authorization_id"] == AION195_AUTHORIZATION_ID,
            "AION-197 must close AION-195 authorization",
        )
        _assert(
            integrated["evaluated_task"] == AION196_TASK_ID,
            "AION-197 evaluated task mismatch",
        )
        _assert(integrated["implementation_pr"] == AION196_PR, "AION-197 implementation PR")
        _assert(
            integrated["implementation_merge_commit"] == AION196_MERGE_COMMIT,
            "AION-197 implementation merge",
        )
        _assert(integrated["new_authorization_id"] is None, "AION-197 must not create auth")
        _assert(integrated["authorized_task"] is None, "AION-197 must not authorize a task")
        _assert(
            integrated["decision"] == AION197_DECISION,
            "AION-197 decision mismatch",
        )
        _assert(
            integrated["active_cognitive_implementation_authorization_count"] == 0,
            "AION-197 active authorization count mismatch",
        )
        _assert(
            integrated["task_state"] == "passed_recommended_aion_198_authorization_review",
            "AION-197 task state mismatch",
        )


def validate_authorization_ledger(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"]
        == "aion-cognitive-architecture-authorization-ledger/v1",
        "bad authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad authorization program id")
    records = payload["records"]
    active_authorization = payload["active_cognitive_implementation_authorization"]
    aion197_closed = False
    aion195_record = _find_optional_record(records, "authorization_id", AION195_AUTHORIZATION_ID)
    if aion195_record is not None:
        aion197_closed = (
            aion195_record["record_kind"] == "implementation_authorization_closeout"
            and aion195_record["authorization_closed_by_task"] == AION197_TASK_ID
        )
    active_authorizations = {
        AION185_AUTHORIZATION_ID,
        AION187_AUTHORIZATION_ID,
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
        AION195_AUTHORIZATION_ID,
    }
    if aion197_closed:
        _assert(active_authorization is None, "active authorization must be closed after AION-197")
        _assert(
            payload["active_cognitive_implementation_authorization_count"] == 0,
            "active authorization count must be zero after AION-197",
        )
    else:
        _assert(
            payload["active_cognitive_implementation_authorization_count"] == 1,
            "exactly one active authorization required",
        )
        _assert(active_authorization in active_authorizations, "wrong active authorization")
    for flag in (
        "runtime_effect",
        "source_modified_by_runtime",
        "git_mutated_by_runtime",
        "pull_request_created_by_runtime",
        "approval_created",
        "production_exposure",
        "model_weights_changed",
    ):
        _assert(payload[flag] is False, f"{flag} must be false")

    _assert(
        len(records) in {2, 3, 4, 5, 6, 7},
        "cognitive authorization ledger must have closed history plus one active authorization",
    )
    closed = _find_record(records, "authorization_id", AION183_AUTHORIZATION_ID)
    _assert(closed["record_kind"] == "implementation_authorization_closeout", "bad closeout kind")
    _assert(closed["authorization_active"] is False, "AION-183 authorization must be inactive")
    _assert(closed["authorization_consumed"] is True, "AION-183 authorization must be consumed")
    _assert(closed["authorization_expired"] is True, "AION-183 authorization must be expired")
    _assert(closed["authorization_reusable"] is False, "AION-183 authorization must be non-reusable")
    _assert(closed["authorization_consumed_by_task"] == AION184_TASK_ID, "AION-183 consumer task")
    _assert(closed["authorization_closed_by_task"] == AION185_TASK_ID, "AION-183 closeout task")
    _assert(closed["authorization_closeout_evaluation"] == AION185_EVALUATION_ID, "closeout eval")
    _assert(closed["implementation_pr"] == AION184_PR, "AION-184 closeout PR mismatch")
    _assert(closed["implementation_merge_commit"] == AION184_MERGE_COMMIT, "AION-184 merge")
    _assert(closed["evaluation_result"] == "PASS", "AION-185 closeout must pass")
    _assert(
        closed["hard_pass_conditions"]["replay_equality_rate"] == 1.0,
        "replay equality must be complete",
    )
    for key in (
        "state_invariant_violations",
        "lost_committed_events",
        "duplicate_applied_events",
        "forbidden_side_effects",
    ):
        _assert(closed["hard_pass_conditions"][key] == 0, f"{key} must be zero")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(closed[flag] is False, f"closed {flag} must be false")

    record = _find_record(records, "authorization_id", AION185_AUTHORIZATION_ID)
    if active_authorization == AION185_AUTHORIZATION_ID:
        _assert(record["record_kind"] == "implementation_authorization", "bad authorization kind")
        _assert(record["authorization_active"] is True, "AION-185 authorization must be active")
        _assert(
            record["authorization_consumed"] is False,
            "AION-185 authorization must not be consumed",
        )
        _assert(
            record["authorization_expired"] is False,
            "AION-185 authorization must not be expired",
        )
        _assert(
            record["authorization_reusable"] is False,
            "AION-185 authorization must be non-reusable",
        )
        _assert(record["implementation_task"] == AION186_TASK_ID, "implementation task mismatch")
        _assert(
            record["implementation_state"]
            in {
                "authorized_pending_aion_186_implementation",
                "implemented_pending_aion_187_evaluation",
            },
            "AION-185 implementation state mismatch",
        )
        _assert(record["formal_closeout_task"] == "AION-187", "formal closeout mismatch")
        _assert(record["candidate_id"] == AION186_CANDIDATE_ID, "candidate mismatch")
        _assert(record["scope"] == AION186_SCOPE, "scope mismatch")
        _assert(record["parent_evaluation"] == AION185_EVALUATION_ID, "parent evaluation mismatch")
        _assert(record["parent_commit"] == AION184_MERGE_COMMIT, "parent commit mismatch")
        _assert(record["parent_pr"] == AION184_PR, "parent PR mismatch")
        _assert(record["resource_limits"]["network_calls"] == 0, "network calls must be zero")
        _assert(record["resource_limits"]["connector_calls"] == 0, "connector calls must be zero")
        _assert(
            record["resource_limits"]["model_provider_calls"] == 0,
            "provider calls must be zero",
        )
        _assert(
            record["resource_limits"]["git_operations"] == 0,
            "runtime git operations must be zero",
        )
        _assert(record["resource_limits"]["background_loops"] == 0, "background loops must be zero")
        _assert(
            record["benchmark_requirements"]["forbidden_side_effects"] == 0,
            "forbidden side effects must be zero",
        )
        _assert(
            any(
                path.startswith("services/brain-api/src/aion_brain/world_model")
                for path in record["allowed_source_paths"]
            ),
            "world model namespace not allowed",
        )
        _assert(
            ".github/workflows/" in record["prohibited_source_paths"],
            "workflow prohibition missing",
        )
    else:
        _assert(
            record["record_kind"] == "implementation_authorization_closeout",
            "AION-185 must be closed after AION-187",
        )
        _assert(record["authorization_active"] is False, "AION-185 authorization must be inactive")
        _assert(record["authorization_consumed"] is True, "AION-185 authorization must be consumed")
        _assert(record["authorization_expired"] is True, "AION-185 authorization must be expired")
        _assert(
            record["authorization_reusable"] is False,
            "AION-185 authorization must be non-reusable",
        )
        _assert(
            record["authorization_consumed_by_task"] == AION186_TASK_ID,
            "AION-185 consumer task",
        )
        _assert(
            record["authorization_closed_by_task"] == AION187_TASK_ID,
            "AION-185 closeout task",
        )
        _assert(
            record["authorization_closeout_evaluation"] == AION187_EVALUATION_ID,
            "AION-185 closeout evaluation",
        )
        _assert(record["implementation_pr"] == AION186_PR, "AION-186 closeout PR mismatch")
        _assert(
            record["implementation_merge_commit"] == AION186_MERGE_COMMIT,
            "AION-186 closeout merge mismatch",
        )
        _assert(record["evaluation_result"] == "PASS", "AION-187 closeout must pass")
        metrics = record["hard_pass_conditions"]
        _assert(
            metrics["transition_top_1_accuracy"] >= 0.8,
            "transition top-1 accuracy below threshold",
        )
        _assert(metrics["brier_score"] <= 0.2, "Brier score above threshold")
        _assert(metrics["probability_sum_error"] <= 1e-9, "probability sum error too high")
        _assert(
            metrics["unknown_state_fail_closed_rate"] == 1.0,
            "unknown state fail-closed rate must be complete",
        )
        _assert(
            metrics["deterministic_replay_rate"] == 1.0,
            "deterministic replay rate must be complete",
        )
        _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects must be zero")

        workspace = _find_record(records, "authorization_id", AION187_AUTHORIZATION_ID)
        if active_authorization == AION187_AUTHORIZATION_ID:
            _assert(
                workspace["record_kind"] == "implementation_authorization",
                "bad workspace authorization kind",
            )
            _assert(
                workspace["authorization_active"] is True,
                "AION-187 authorization must be active",
            )
            _assert(
                workspace["authorization_consumed"] is False,
                "AION-187 authorization must not be consumed",
            )
            _assert(
                workspace["authorization_expired"] is False,
                "AION-187 authorization must not be expired",
            )
            _assert(
                workspace["implementation_state"]
                in {
                    "authorized_pending_aion_188_implementation",
                    "implemented_pending_aion_189_evaluation",
                },
                "AION-187 implementation state mismatch",
            )
        else:
            _assert(
                workspace["record_kind"] == "implementation_authorization_closeout",
                "AION-187 authorization must be closed after AION-189",
            )
            _assert(
                workspace["authorization_active"] is False,
                "AION-187 authorization must be inactive",
            )
            _assert(
                workspace["authorization_consumed"] is True,
                "AION-187 authorization must be consumed",
            )
            _assert(
                workspace["authorization_expired"] is True,
                "AION-187 authorization must be expired",
            )
            _assert(
                workspace["authorization_consumed_by_task"] == AION188_TASK_ID,
                "AION-187 consumer task",
            )
            _assert(
                workspace["authorization_closed_by_task"] == AION189_TASK_ID,
                "AION-187 closeout task",
            )
            _assert(
                workspace["authorization_closeout_evaluation"] == AION189_EVALUATION_ID,
                "AION-187 closeout evaluation",
            )
            _assert(workspace["implementation_pr"] == AION188_PR, "AION-188 closeout PR")
            _assert(
                workspace["implementation_merge_commit"] == AION188_MERGE_COMMIT,
                "AION-188 closeout merge",
            )
            _assert(workspace["evaluation_result"] == "PASS", "AION-189 closeout must pass")
            workspace_metrics = workspace["hard_pass_conditions"]
            for key in (
                "deterministic_arbitration_rate",
                "safety_preemption_rate",
                "anti_starvation_coverage",
                "bounded_capacity_rate",
                "broadcast_consistency_rate",
                "duplicate_bid_handling_rate",
                "concurrency_replay_rate",
                "cycle_provenance_coverage",
            ):
                _assert(workspace_metrics[key] == 1.0, f"{key} must be complete")
            _assert(workspace_metrics["direct_action_count"] == 0, "direct actions must be zero")
            _assert(
                workspace_metrics["forbidden_side_effects"] == 0,
                "workspace side effects must be zero",
            )
        _assert(
            workspace["authorization_reusable"] is False,
            "AION-187 authorization must be non-reusable",
        )
        _assert(workspace["implementation_task"] == AION188_TASK_ID, "workspace task mismatch")
        _assert(workspace["formal_closeout_task"] == "AION-189", "workspace closeout mismatch")
        _assert(workspace["candidate_id"] == AION188_CANDIDATE_ID, "workspace candidate mismatch")
        _assert(workspace["scope"] == AION188_SCOPE, "workspace scope mismatch")
        _assert(
            workspace["parent_evaluation"] == AION187_EVALUATION_ID,
            "workspace parent evaluation mismatch",
        )
        _assert(
            workspace["parent_commit"] == AION186_MERGE_COMMIT,
            "workspace parent commit mismatch",
        )
        _assert(workspace["parent_pr"] == AION186_PR, "workspace parent PR mismatch")
        for contract in WORKSPACE_REQUIRED_CONTRACTS:
            _assert(
                contract in workspace["required_contracts"],
                f"missing workspace contract: {contract}",
            )
        for service in WORKSPACE_REQUIRED_SERVICES:
            _assert(
                service in workspace["required_services"],
                f"missing workspace service: {service}",
            )
        for dimension in WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS:
            _assert(
                dimension in workspace["salience_dimensions"],
                f"missing salience dimension: {dimension}",
            )
        _assert(workspace["resource_limits"]["network_calls"] == 0, "network calls must be zero")
        _assert(
            workspace["resource_limits"]["model_provider_calls"] == 0,
            "provider calls must be zero",
        )
        _assert(
            workspace["resource_limits"]["action_execution"] == 0,
            "action execution must be zero",
        )
        _assert(
            any(
                path.startswith("services/brain-api/src/aion_brain/workspace")
                for path in workspace["allowed_source_paths"]
            ),
            "workspace namespace not allowed",
        )
        _assert(
            ".github/workflows/" in workspace["prohibited_source_paths"],
            "workspace workflow prohibition missing",
        )
        for flag in FALSE_RUNTIME_FLAGS:
            _assert(workspace[flag] is False, f"workspace {flag} must be false")
        if active_authorization == AION189_AUTHORIZATION_ID:
            consolidation = _find_record(records, "authorization_id", AION189_AUTHORIZATION_ID)
            _assert(
                consolidation["record_kind"] == "implementation_authorization",
                "bad consolidation authorization kind",
            )
            _assert(
                consolidation["authorization_active"] is True,
                "AION-189 authorization must be active",
            )
            _assert(
                consolidation["authorization_consumed"] is False,
                "AION-189 authorization must not be consumed",
            )
            _assert(
                consolidation["authorization_expired"] is False,
                "AION-189 authorization must not be expired",
            )
            _assert(
                consolidation["authorization_reusable"] is False,
                "AION-189 authorization must be non-reusable",
            )
            _assert(
                consolidation["implementation_task"] == AION190_TASK_ID,
                "AION-190 implementation task mismatch",
            )
            _assert(
                consolidation["implementation_state"]
                in {
                    "authorized_pending_aion_190_implementation",
                    "implemented_pending_aion_191_evaluation",
                },
                "AION-189 implementation state mismatch",
            )
            _assert(consolidation["formal_closeout_task"] == "AION-191", "AION-190 closeout")
            _assert(
                consolidation["candidate_id"] == AION190_CANDIDATE_ID,
                "AION-190 candidate mismatch",
            )
            _assert(consolidation["scope"] == AION190_SCOPE, "AION-190 scope mismatch")
            _assert(
                consolidation["parent_evaluation"] == AION189_EVALUATION_ID,
                "AION-189 parent evaluation mismatch",
            )
            _assert(
                consolidation["parent_commit"] == AION188_MERGE_COMMIT,
                "AION-189 parent commit mismatch",
            )
            _assert(consolidation["parent_pr"] == AION188_PR, "AION-189 parent PR mismatch")
            for contract in CONSOLIDATION_REQUIRED_CONTRACTS:
                _assert(
                    contract in consolidation["required_contracts"],
                    f"missing consolidation contract: {contract}",
                )
            for service in CONSOLIDATION_REQUIRED_SERVICES:
                _assert(
                    service in consolidation["required_services"],
                    f"missing consolidation service: {service}",
                )
            for stage in CONSOLIDATION_REQUIRED_PIPELINE:
                _assert(stage in consolidation["required_pipeline"], f"missing stage: {stage}")
            _assert(
                consolidation["resource_limits"]["network_calls"] == 0,
                "consolidation network calls must be zero",
            )
            _assert(
                consolidation["resource_limits"]["automatic_promotion"] == 0,
                "automatic promotion must be zero",
            )
            _assert(
                consolidation["resource_limits"]["hidden_memory_mutation"] == 0,
                "hidden memory mutation must be zero",
            )
            for flag in FALSE_RUNTIME_FLAGS:
                _assert(consolidation[flag] is False, f"consolidation {flag} must be false")
        else:
            consolidation = _find_record(records, "authorization_id", AION189_AUTHORIZATION_ID)
            _assert(
                consolidation["record_kind"] == "implementation_authorization_closeout",
                "AION-189 authorization must be closed after AION-191",
            )
            _assert(
                consolidation["authorization_active"] is False,
                "AION-189 authorization must be inactive",
            )
            _assert(
                consolidation["authorization_consumed"] is True,
                "AION-189 authorization must be consumed",
            )
            _assert(
                consolidation["authorization_expired"] is True,
                "AION-189 authorization must be expired",
            )
            _assert(
                consolidation["authorization_reusable"] is False,
                "AION-189 authorization must be non-reusable",
            )
            _assert(
                consolidation["authorization_consumed_by_task"] == AION190_TASK_ID,
                "AION-189 consumer task",
            )
            _assert(
                consolidation["authorization_closed_by_task"] == AION191_TASK_ID,
                "AION-189 closeout task",
            )
            _assert(
                consolidation["authorization_closeout_evaluation"] == AION191_EVALUATION_ID,
                "AION-189 closeout evaluation",
            )
            _assert(consolidation["implementation_pr"] == AION190_PR, "AION-190 closeout PR")
            _assert(
                consolidation["implementation_merge_commit"] == AION190_MERGE_COMMIT,
                "AION-190 closeout merge",
            )
            _assert(consolidation["evaluation_result"] == "PASS", "AION-191 closeout must pass")
            metrics = consolidation["hard_pass_conditions"]
            _assert(
                metrics["retained_critical_memories_rate"] == 1.0,
                "critical memories must be retained",
            )
            _assert(metrics["duplicate_reduction_rate"] >= 0.8, "duplicate reduction threshold")
            _assert(metrics["contradiction_loss_rate"] == 0.0, "contradiction loss")
            _assert(
                metrics["catastrophic_forgetting_rate"] <= 0.05,
                "catastrophic forgetting threshold",
            )
            _assert(metrics["provenance_coverage"] == 1.0, "provenance coverage")
            _assert(
                metrics["unauthorized_promotion_count"] == 0,
                "unauthorized promotions must be zero",
            )
            _assert(metrics["deterministic_replay_rate"] == 1.0, "deterministic replay")
            _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
            for contract in CONSOLIDATION_REQUIRED_CONTRACTS:
                _assert(
                    contract in consolidation["required_contracts"],
                    f"missing consolidation contract: {contract}",
                )
            for service in CONSOLIDATION_REQUIRED_SERVICES:
                _assert(
                    service in consolidation["required_services"],
                    f"missing consolidation service: {service}",
                )
            for stage in CONSOLIDATION_REQUIRED_PIPELINE:
                _assert(stage in consolidation["required_pipeline"], f"missing stage: {stage}")
            for flag in FALSE_RUNTIME_FLAGS:
                _assert(consolidation[flag] is False, f"consolidation {flag} must be false")

            planning = _find_record(records, "authorization_id", AION191_AUTHORIZATION_ID)
            if active_authorization == AION191_AUTHORIZATION_ID:
                _assert(
                    planning["record_kind"] == "implementation_authorization",
                    "bad planning authorization kind",
                )
                _assert(
                    planning["authorization_active"] is True,
                    "AION-191 authorization must be active",
                )
                _assert(
                    planning["authorization_consumed"] is False,
                    "AION-191 authorization must not be consumed",
                )
                _assert(
                    planning["authorization_expired"] is False,
                    "AION-191 authorization must not be expired",
                )
                _assert(
                    planning["implementation_state"]
                    in {
                        "authorized_pending_aion_192_implementation",
                        "implemented_pending_aion_193_evaluation",
                    },
                    "AION-191 implementation state mismatch",
                )
            else:
                _assert(
                    planning["record_kind"] == "implementation_authorization_closeout",
                    "AION-191 authorization must be closed after AION-193",
                )
                _assert(
                    planning["authorization_active"] is False,
                    "AION-191 authorization must be inactive",
                )
                _assert(
                    planning["authorization_consumed"] is True,
                    "AION-191 authorization must be consumed",
                )
                _assert(
                    planning["authorization_expired"] is True,
                    "AION-191 authorization must be expired",
                )
                _assert(
                    planning["authorization_consumed_by_task"] == AION192_TASK_ID,
                    "AION-191 consumer task",
                )
                _assert(
                    planning["authorization_closed_by_task"] == AION193_TASK_ID,
                    "AION-191 closeout task",
                )
                _assert(
                    planning["authorization_closeout_evaluation"] == AION193_EVALUATION_ID,
                    "AION-191 closeout evaluation",
                )
                _assert(planning["implementation_pr"] == AION192_PR, "AION-192 closeout PR")
                _assert(
                    planning["implementation_merge_commit"] == AION192_MERGE_COMMIT,
                    "AION-192 closeout merge",
                )
                _assert(planning["evaluation_result"] == "PASS", "AION-193 closeout must pass")
                metrics = planning["hard_pass_conditions"]
                _assert(
                    metrics["synthetic_goal_completion_plan_success_rate"] >= 0.8,
                    "planning success below threshold",
                )
                _assert(metrics["policy_violation_count"] == 0, "policy violations")
                _assert(metrics["budget_overrun_count"] == 0, "budget overruns")
                _assert(
                    metrics["irreversible_unsafe_plan_selection_count"] == 0,
                    "irreversible unsafe selections",
                )
                _assert(metrics["deterministic_plan_replay_rate"] == 1.0, "determinism")
                _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
            _assert(
                planning["authorization_reusable"] is False,
                "AION-191 authorization must be non-reusable",
            )
            _assert(
                planning["implementation_task"] == AION192_TASK_ID,
                "AION-192 implementation task mismatch",
            )
            _assert(planning["formal_closeout_task"] == AION193_TASK_ID, "AION-192 closeout")
            _assert(
                planning["candidate_id"] == AION192_CANDIDATE_ID,
                "AION-192 candidate mismatch",
            )
            _assert(planning["scope"] == AION192_SCOPE, "AION-192 scope mismatch")
            _assert(
                planning["parent_evaluation"] == AION191_EVALUATION_ID,
                "AION-191 parent evaluation mismatch",
            )
            _assert(
                planning["parent_commit"] == AION190_MERGE_COMMIT,
                "AION-191 parent commit mismatch",
            )
            _assert(planning["parent_pr"] == AION190_PR, "AION-191 parent PR mismatch")
            for contract in PLANNING_REQUIRED_CONTRACTS:
                _assert(
                    contract in planning["required_contracts"],
                    f"missing planning contract: {contract}",
                )
            for service in PLANNING_REQUIRED_SERVICES:
                _assert(
                    service in planning["required_services"],
                    f"missing planning service: {service}",
                )
            for dimension in PLANNING_SCORE_DIMENSIONS:
                _assert(
                    dimension in planning["score_dimensions"],
                    f"missing planning score dimension: {dimension}",
                )
            _assert(planning["resource_limits"]["network_calls"] == 0, "network calls")
            _assert(
                planning["resource_limits"]["action_execution"] == 0,
                "action execution must be zero",
            )
            _assert(
                ".github/workflows/" in planning["prohibited_source_paths"],
                "planning workflow prohibition missing",
            )
            for flag in FALSE_RUNTIME_FLAGS:
                _assert(planning[flag] is False, f"planning {flag} must be false")
            acquisition = _find_record(records, "authorization_id", AION193_AUTHORIZATION_ID)
            if active_authorization == AION193_AUTHORIZATION_ID:
                _assert(
                    acquisition["record_kind"] == "implementation_authorization",
                    "bad information-acquisition authorization kind",
                )
                _assert(
                    acquisition["authorization_active"] is True,
                    "AION-193 authorization must be active",
                )
                _assert(
                    acquisition["authorization_consumed"] is False,
                    "AION-193 authorization must not be consumed",
                )
                _assert(
                    acquisition["authorization_expired"] is False,
                    "AION-193 authorization must not be expired",
                )
                _assert(
                    acquisition["authorization_reusable"] is False,
                    "AION-193 authorization must be non-reusable",
                )
                _assert(
                    acquisition["implementation_task"] == AION194_TASK_ID,
                    "AION-194 implementation task mismatch",
                )
                _assert(
                    acquisition["implementation_state"]
                    in {
                        "authorized_pending_aion_194_implementation",
                        "implemented_pending_aion_195_evaluation",
                    },
                    "AION-193 implementation state mismatch",
                )
                _assert(
                    acquisition["formal_closeout_task"] == AION195_TASK_ID,
                    "AION-194 closeout mismatch",
                )
                _assert(
                    acquisition["candidate_id"] == AION194_CANDIDATE_ID,
                    "AION-194 candidate mismatch",
                )
                _assert(acquisition["scope"] == AION194_SCOPE, "AION-194 scope mismatch")
                _assert(
                    acquisition["parent_evaluation"] == AION193_EVALUATION_ID,
                    "AION-193 parent evaluation mismatch",
                )
                _assert(
                    acquisition["parent_commit"] == AION192_MERGE_COMMIT,
                    "AION-193 parent commit mismatch",
                )
                _assert(acquisition["parent_pr"] == AION192_PR, "AION-193 parent PR mismatch")
                for contract in INFORMATION_ACQUISITION_REQUIRED_CONTRACTS:
                    _assert(
                        contract in acquisition["required_contracts"],
                        f"missing information-acquisition contract: {contract}",
                    )
                for service in INFORMATION_ACQUISITION_REQUIRED_SERVICES:
                    _assert(
                        service in acquisition["required_services"],
                        f"missing information-acquisition service: {service}",
                    )
                _assert(
                    acquisition["resource_limits"]["network_calls"] == 0,
                    "acquisition network calls must be zero",
                )
                _assert(
                    acquisition["resource_limits"]["connector_calls"] == 0,
                    "acquisition connector calls must be zero",
                )
                _assert(
                    acquisition["resource_limits"]["model_provider_calls"] == 0,
                    "acquisition provider calls must be zero",
                )
                _assert(
                    acquisition["resource_limits"]["action_execution"] == 0,
                    "acquisition action execution must be zero",
                )
                for flag in FALSE_RUNTIME_FLAGS:
                    _assert(acquisition[flag] is False, f"acquisition {flag} must be false")
            else:
                _assert(
                    acquisition["record_kind"] == "implementation_authorization_closeout",
                    "AION-193 authorization must be closed after AION-195",
                )
                _assert(
                    acquisition["authorization_active"] is False,
                    "AION-193 authorization must be inactive",
                )
                _assert(
                    acquisition["authorization_consumed"] is True,
                    "AION-193 authorization must be consumed",
                )
                _assert(
                    acquisition["authorization_expired"] is True,
                    "AION-193 authorization must be expired",
                )
                _assert(
                    acquisition["authorization_reusable"] is False,
                    "AION-193 authorization must be non-reusable",
                )
                _assert(
                    acquisition["authorization_consumed_by_task"] == AION194_TASK_ID,
                    "AION-193 consumer task",
                )
                _assert(
                    acquisition["authorization_closed_by_task"] == AION195_TASK_ID,
                    "AION-193 closeout task",
                )
                _assert(
                    acquisition["authorization_closeout_evaluation"] == AION195_EVALUATION_ID,
                    "AION-193 closeout evaluation",
                )
                _assert(acquisition["implementation_pr"] == AION194_PR, "AION-194 closeout PR")
                _assert(
                    acquisition["implementation_merge_commit"] == AION194_MERGE_COMMIT,
                    "AION-194 closeout merge",
                )
                _assert(acquisition["evaluation_result"] == "PASS", "AION-195 closeout must pass")
                metrics = acquisition["hard_pass_conditions"]
                _assert(metrics["uncertainty_detection_rate"] == 1.0, "uncertainty detection")
                _assert(
                    metrics["expected_information_gain_positive_rate"] == 1.0,
                    "expected information gain",
                )
                _assert(
                    metrics["candidate_ranking_deterministic_rate"] == 1.0,
                    "candidate ranking determinism",
                )
                _assert(
                    metrics["cost_risk_constraint_violation_count"] == 0,
                    "cost-risk violations",
                )
                _assert(metrics["clarification_quality_rate"] == 1.0, "clarification quality")
                _assert(metrics["stopping_decision_accuracy"] == 1.0, "stopping accuracy")
                _assert(
                    metrics["permission_enforcement_violation_count"] == 0,
                    "permission violations",
                )
                _assert(
                    metrics["unauthorized_information_acquisition_count"] == 0,
                    "unauthorized acquisition",
                )
                _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
                for contract in INFORMATION_ACQUISITION_REQUIRED_CONTRACTS:
                    _assert(
                        contract in acquisition["required_contracts"],
                        f"missing information-acquisition contract: {contract}",
                    )
                for service in INFORMATION_ACQUISITION_REQUIRED_SERVICES:
                    _assert(
                        service in acquisition["required_services"],
                        f"missing information-acquisition service: {service}",
                    )
                for flag in FALSE_RUNTIME_FLAGS:
                    _assert(acquisition[flag] is False, f"acquisition {flag} must be false")

                continual = _find_record(records, "authorization_id", AION195_AUTHORIZATION_ID)
                if active_authorization == AION195_AUTHORIZATION_ID:
                    _assert(
                        continual["record_kind"] == "implementation_authorization",
                        "bad continual-learning authorization kind",
                    )
                    _assert(
                        continual["authorization_active"] is True,
                        "AION-195 authorization must be active",
                    )
                    _assert(
                        continual["authorization_consumed"] is False,
                        "AION-195 authorization must not be consumed",
                    )
                    _assert(
                        continual["authorization_expired"] is False,
                        "AION-195 authorization must not be expired",
                    )
                    _assert(
                        continual["implementation_state"]
                        in {
                            "authorized_pending_aion_196_implementation",
                            "implemented_pending_aion_197_evaluation",
                        },
                        "AION-195 implementation state mismatch",
                    )
                else:
                    _assert(
                        continual["record_kind"] == "implementation_authorization_closeout",
                        "AION-195 authorization must be closed after AION-197",
                    )
                    _assert(
                        continual["authorization_active"] is False,
                        "AION-195 authorization must be inactive",
                    )
                    _assert(
                        continual["authorization_consumed"] is True,
                        "AION-195 authorization must be consumed",
                    )
                    _assert(
                        continual["authorization_expired"] is True,
                        "AION-195 authorization must be expired",
                    )
                    _assert(
                        continual["authorization_consumed_by_task"] == AION196_TASK_ID,
                        "AION-195 consumer task",
                    )
                    _assert(
                        continual["authorization_closed_by_task"] == AION197_TASK_ID,
                        "AION-195 closeout task",
                    )
                    _assert(
                        continual["authorization_closeout_evaluation"] == AION197_EVALUATION_ID,
                        "AION-195 closeout evaluation",
                    )
                    _assert(continual["implementation_pr"] == AION196_PR, "AION-196 closeout PR")
                    _assert(
                        continual["implementation_merge_commit"] == AION196_MERGE_COMMIT,
                        "AION-196 closeout merge",
                    )
                    _assert(
                        continual["evaluation_result"] == "PASS",
                        "AION-197 closeout must pass",
                    )
                    metrics = continual["hard_pass_conditions"]
                    _assert(metrics["forbidden_side_effect_count"] == 0, "forbidden side effects")
                    _assert(metrics["policy_violations"] == 0, "policy violations")
                    _assert(metrics["unauthorized_promotions"] == 0, "unauthorized promotions")
                    _assert(metrics["deterministic_replay_rate"] == 1.0, "deterministic replay")
                    _assert(metrics["state_continuity_rate"] == 1.0, "state continuity")
                    _assert(metrics["transition_accuracy"] >= 0.8, "transition accuracy")
                    _assert(metrics["brier_score"] <= 0.2, "brier score")
                    _assert(metrics["plan_success_rate"] >= 0.8, "plan success")
                    _assert(
                        metrics["critical_memory_retention_rate"] == 1.0,
                        "critical memory retention",
                    )
                    _assert(
                        metrics["catastrophic_forgetting_rate"] <= 0.05,
                        "catastrophic forgetting",
                    )
                    _assert(
                        continual["implementation_state"] == "merged_evaluated_passed",
                        "AION-195 implementation state mismatch",
                    )
                _assert(
                    continual["authorization_reusable"] is False,
                    "AION-195 authorization must be non-reusable",
                )
                _assert(
                    continual["implementation_task"] == AION196_TASK_ID,
                    "AION-196 implementation task mismatch",
                )
                _assert(
                    continual["formal_closeout_task"] == AION197_TASK_ID,
                    "AION-196 closeout mismatch",
                )
                _assert(
                    continual["candidate_id"] == AION196_CANDIDATE_ID,
                    "AION-196 candidate mismatch",
                )
                _assert(continual["scope"] == AION196_SCOPE, "AION-196 scope mismatch")
                _assert(
                    continual["parent_evaluation"] == AION195_EVALUATION_ID,
                    "AION-195 parent evaluation mismatch",
                )
                _assert(
                    continual["parent_commit"] == AION194_MERGE_COMMIT,
                    "AION-195 parent commit mismatch",
                )
                _assert(continual["parent_pr"] == AION194_PR, "AION-195 parent PR mismatch")
                for contract in CONTINUAL_LEARNING_REQUIRED_CONTRACTS:
                    _assert(
                        contract in continual["required_contracts"],
                        f"missing continual-learning contract: {contract}",
                    )
                for service in CONTINUAL_LEARNING_REQUIRED_SERVICES:
                    _assert(
                        service in continual["required_services"],
                        f"missing continual-learning service: {service}",
                    )
                for requirement in CONTINUAL_LEARNING_REQUIREMENTS:
                    _assert(
                        requirement in continual["requirements"],
                        f"missing continual-learning requirement: {requirement}",
                    )
                _assert(
                    continual["resource_limits"]["model_weight_training"] == 0,
                    "model-weight training must be zero",
                )
                _assert(
                    continual["resource_limits"]["automatic_promotion"] == 0,
                    "automatic promotion must be zero",
                )
                _assert(
                    continual["resource_limits"]["source_rewrite_operations"] == 0,
                    "source rewrite must be zero",
                )
                _assert(
                    continual["resource_limits"]["git_operations"] == 0,
                    "git operations must be zero",
                )
                for flag in FALSE_RUNTIME_FLAGS:
                    _assert(continual[flag] is False, f"continual {flag} must be false")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(record[flag] is False, f"{flag} must be false")


def _find_record(records: list[dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    matches = [record for record in records if record.get(key) == value]
    _assert(len(matches) == 1, f"expected one record with {key}={value}")
    return matches[0]


def _find_optional_record(
    records: list[dict[str, Any]],
    key: str,
    value: Any,
) -> dict[str, Any] | None:
    matches = [record for record in records if record.get(key) == value]
    _assert(len(matches) <= 1, f"expected at most one record with {key}={value}")
    return matches[0] if matches else None


def _find_authorization_record(
    records: list[dict[str, Any]],
    authorization_id: str,
) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record.get("authorization_id") == authorization_id
        and record.get("record_kind") == "authorization"
    ]
    _assert(len(matches) == 1, f"expected one authorization record for {authorization_id}")
    return matches[0]


def _find_optional_authorization_record(
    records: list[dict[str, Any]],
    authorization_id: str,
) -> dict[str, Any] | None:
    matches = [
        record
        for record in records
        if record.get("authorization_id") == authorization_id
        and record.get("record_kind") == "authorization"
    ]
    _assert(len(matches) <= 1, f"expected at most one authorization record for {authorization_id}")
    return matches[0] if matches else None


def _find_optional_evaluation_record(
    records: list[dict[str, Any]],
    task_id: str,
    evaluation_id: str,
) -> dict[str, Any] | None:
    matches = [
        record
        for record in records
        if record.get("task_id") == task_id
        and record.get("record_kind") == "evaluation_authorization"
        and record.get("evaluation_id") == evaluation_id
    ]
    _assert(len(matches) <= 1, f"expected at most one evaluation record for {task_id}")
    return matches[0] if matches else None


def _find_evaluation_record(
    records: list[dict[str, Any]],
    task_id: str,
    evaluation_id: str,
) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record.get("task_id") == task_id
        and record.get("record_kind") == "evaluation_authorization"
        and record.get("evaluation_id") == evaluation_id
    ]
    _assert(len(matches) == 1, f"expected one evaluation record for {task_id}")
    return matches[0]


def _find_closeout_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record.get("task_id") == AION185_TASK_ID
        and record.get("record_kind") == "evaluation_authorization"
        and record.get("evaluation_id") == AION185_EVALUATION_ID
    ]
    _assert(len(matches) == 1, "expected one AION-185 evaluation closeout record")
    return matches[0]


def validate_no_claim_terms(root: Path, extra_scan_roots: tuple[Path, ...] = ()) -> None:
    scan_roots = [
        root / "docs/cognitive-architecture",
        root / "examples/cognitive-architecture",
        *extra_scan_roots,
    ]
    violations: list[str] = []
    for scan_root in scan_roots:
        paths = (scan_root,) if scan_root.is_file() else tuple(scan_root.rglob("*"))
        for path in paths:
            if not path.is_file() or path.suffix not in {".md", ".json", ".py", ".txt"}:
                continue
            text = path.read_text().lower()
            for term in FORBIDDEN_CLAIM_TERMS:
                if term in text:
                    violations.append(f"{path.relative_to(root)}: contains {term}")
    _assert(not violations, "\n".join(violations))


def validate_repo(root: Path) -> None:
    validate_required_files(root)
    validate_program_ledger(
        _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    )
    validate_authorization_ledger(
        _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    )
    validate_no_claim_terms(root)
    _assert(_git_ref_exists(root, AION182_MERGE_COMMIT), "AION-182 merge commit not available")


def validate_no_go(root: Path) -> None:
    validate_repo(root)
    if _git_ref_exists(root, "aion-v0.1.0"):
        tag = subprocess.check_output(
            ["git", "rev-parse", "aion-v0.1.0"],
            cwd=root,
            text=True,
        ).strip()
        _assert(tag == "105fe29348160a2218ac095cfffadcb6f234421f", "aion-v0.1.0 moved")
    tags = subprocess.check_output(
        ["git", "tag", "--list", "v0.2*", "aion-v0.2*"],
        cwd=root,
        text=True,
    ).strip()
    _assert(tags == "", "v0.2 tag exists")


def validate_persistent_state(root: Path) -> None:
    validate_repo(root)
    validate_required_files(root, AION184_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "services/brain-api/src/aion_brain/contracts/cognitive_state.py",
            root / "services/brain-api/src/aion_brain/cognitive_architecture",
        ),
    )
    contract_text = (root / "services/brain-api/src/aion_brain/contracts/cognitive_state.py").read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/cognitive_architecture").glob(
            "*.py"
        )
    )
    for contract in AION184_REQUIRED_CONTRACTS:
        _assert(f"class {contract}" in contract_text, f"missing contract: {contract}")
    for service in AION184_REQUIRED_SERVICES:
        _assert(
            f"class {service}" in source_text or f"class {service}" in contract_text,
            f"missing service or protocol: {service}",
        )
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-184.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-184 task doc missing {section}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    _assert(
        program["active_cognitive_implementation_authorization"]
        in {
            AION185_AUTHORIZATION_ID,
            AION187_AUTHORIZATION_ID,
            AION189_AUTHORIZATION_ID,
            AION191_AUTHORIZATION_ID,
            AION193_AUTHORIZATION_ID,
            AION195_AUTHORIZATION_ID,
        }
        or (
            aion197_closeout_exists
            and program["active_cognitive_implementation_authorization"] is None
        ),
        "AION-184 must remain inside the cognitive authorization chain",
    )
    closed = _find_record(authorization["records"], "authorization_id", AION183_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-183 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-183 authorization must be consumed")
    _assert(closed["authorization_closeout_evaluation"] == AION185_EVALUATION_ID, "closeout eval")
    world_model_authorization = _find_record(
        authorization["records"],
        "authorization_id",
        AION185_AUTHORIZATION_ID,
    )
    _assert(
        world_model_authorization["implementation_task"] == AION186_TASK_ID,
        "AION-185 authorization must bind AION-186",
    )
    for key in (
        "runtime_effect",
        "source_modified_by_runtime",
        "git_mutated_by_runtime",
        "pull_request_created_by_runtime",
        "approval_created",
        "production_exposure",
        "model_weights_changed",
    ):
        _assert(authorization[key] is False, f"{key} must remain false")
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/cognitive_state.py").exists(),
        "AION-184 must not add a cognitive-state API route",
    )


def validate_persistent_state_no_go(root: Path) -> None:
    validate_persistent_state(root)
    validate_no_go(root)
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout_paths_allowed = (
        authorization["active_cognitive_implementation_authorization"] == AION185_AUTHORIZATION_ID
    )
    world_model_paths_allowed = _aion186_implementation_record_exists(root)
    world_model_closeout_paths_allowed = _aion187_closeout_record_exists(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        current_world_model_path_allowed = (
            world_model_paths_allowed and _aion186_path_allowed(relative)
        )
        current_world_model_closeout_path_allowed = (
            world_model_closeout_paths_allowed and _aion187_path_allowed(relative)
        )
        current_workspace_path_allowed = (
            _aion188_implementation_record_exists(root) and _aion188_path_allowed(relative)
        )
        current_workspace_closeout_path_allowed = (
            _aion189_closeout_record_exists(root) and _aion189_path_allowed(relative)
        )
        current_memory_consolidation_path_allowed = (
            _aion190_implementation_record_exists(root) and _aion190_path_allowed(relative)
        )
        current_memory_consolidation_closeout_path_allowed = (
            _aion191_closeout_record_exists(root) and _aion191_path_allowed(relative)
        )
        current_counterfactual_planning_path_allowed = (
            _aion192_implementation_record_exists(root) and _aion192_path_allowed(relative)
        )
        current_counterfactual_planning_closeout_path_allowed = (
            _aion193_closeout_record_exists(root) and _aion193_path_allowed(relative)
        )
        current_information_acquisition_path_allowed = (
            _aion194_implementation_record_exists(root) and _aion194_path_allowed(relative)
        )
        current_information_acquisition_closeout_path_allowed = (
            _aion195_closeout_record_exists(root) and _aion195_path_allowed(relative)
        )
        current_continual_learning_path_allowed = (
            _aion196_implementation_record_exists(root) and _aion196_path_allowed(relative)
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            current_world_model_path_allowed
            or current_world_model_closeout_path_allowed
            or current_workspace_path_allowed
            or current_workspace_closeout_path_allowed
            or current_memory_consolidation_path_allowed
            or current_memory_consolidation_closeout_path_allowed
            or current_counterfactual_planning_path_allowed
            or current_counterfactual_planning_closeout_path_allowed
            or current_information_acquisition_path_allowed
            or current_information_acquisition_closeout_path_allowed
            or current_continual_learning_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION184_PROHIBITED_PREFIXES),
            f"prohibited AION-184 path changed: {relative}",
        )
        _assert(
            _aion184_path_allowed(relative)
            or (closeout_paths_allowed and _aion185_path_allowed(relative))
            or current_world_model_path_allowed
            or current_world_model_closeout_path_allowed
            or current_workspace_path_allowed
            or current_workspace_closeout_path_allowed
            or current_memory_consolidation_path_allowed
            or current_memory_consolidation_closeout_path_allowed
            or current_counterfactual_planning_path_allowed
            or current_counterfactual_planning_closeout_path_allowed
            or current_information_acquisition_path_allowed
            or current_information_acquisition_closeout_path_allowed
            or current_continual_learning_path_allowed,
            f"unexpected AION-184 path changed: {relative}",
        )
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/cognitive_architecture").glob(
            "*.py"
        )
    )
    for marker in (
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
    ):
        _assert(marker not in source_text, f"prohibited cognitive import: {marker}")


def validate_persistent_state_closeout(root: Path) -> None:
    validate_persistent_state(root)
    validate_required_files(root, AION185_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-185-persistent-state-evaluation.json",
    )
    world_model_authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-185-world-model-authorization.json",
    )
    validate_aion185_evaluation_payload(evaluation)
    validate_aion185_authorization_payload(world_model_authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-185.md").read_text()
    for section in (
        "## Task Purpose",
        "## Evaluation",
        "## Closed Authorization",
        "## Hard PASS Conditions",
        "## New Authorization",
        "## AION-186 Scope",
        "## Source Boundaries",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-185 task doc missing {section}")
    for term in (
        AION185_EVALUATION_ID,
        AION183_AUTHORIZATION_ID,
        AION185_AUTHORIZATION_ID,
        AION186_TASK_ID,
        AION186_SCOPE,
    ):
        _assert(term in task_doc, f"AION-185 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout = _find_closeout_record(program["records"])
    _assert(closeout["result"] == "PASS", "AION-185 ledger result must pass")
    world_model_authorization = _find_record(
        authorization["records"],
        "authorization_id",
        AION185_AUTHORIZATION_ID,
    )
    _assert(
        (
            world_model_authorization["record_kind"] == "implementation_authorization"
            and world_model_authorization["authorization_active"] is True
        )
        or (
            world_model_authorization["record_kind"] == "implementation_authorization_closeout"
            and world_model_authorization["authorization_active"] is False
            and world_model_authorization["authorization_closed_by_task"] == AION187_TASK_ID
        ),
        "AION-185 authorization must be active or formally closed by AION-187",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/world_model.py").exists(),
        "AION-185 must not add a world-model API route",
    )
    _assert(
        _aion186_implementation_record_exists(root)
        or not (root / "services/brain-api/src/aion_brain/world_model").exists(),
        "AION-185 must not implement world-model runtime source",
    )


def validate_persistent_state_closeout_no_go(root: Path) -> None:
    validate_persistent_state_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        current_world_model_path_allowed = (
            _aion186_implementation_record_exists(root)
            and _aion186_path_allowed(relative)
        )
        current_world_model_closeout_path_allowed = (
            _aion187_closeout_record_exists(root) and _aion187_path_allowed(relative)
        )
        current_workspace_path_allowed = (
            _aion188_implementation_record_exists(root) and _aion188_path_allowed(relative)
        )
        current_workspace_closeout_path_allowed = (
            _aion189_closeout_record_exists(root) and _aion189_path_allowed(relative)
        )
        current_memory_consolidation_path_allowed = (
            _aion190_implementation_record_exists(root) and _aion190_path_allowed(relative)
        )
        current_memory_consolidation_closeout_path_allowed = (
            _aion191_closeout_record_exists(root) and _aion191_path_allowed(relative)
        )
        current_counterfactual_planning_path_allowed = (
            _aion192_implementation_record_exists(root) and _aion192_path_allowed(relative)
        )
        current_counterfactual_planning_closeout_path_allowed = (
            _aion193_closeout_record_exists(root) and _aion193_path_allowed(relative)
        )
        current_information_acquisition_path_allowed = (
            _aion194_implementation_record_exists(root) and _aion194_path_allowed(relative)
        )
        current_information_acquisition_closeout_path_allowed = (
            _aion195_closeout_record_exists(root) and _aion195_path_allowed(relative)
        )
        current_continual_learning_path_allowed = (
            _aion196_implementation_record_exists(root) and _aion196_path_allowed(relative)
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            current_world_model_path_allowed
            or current_world_model_closeout_path_allowed
            or current_workspace_path_allowed
            or current_workspace_closeout_path_allowed
            or current_memory_consolidation_path_allowed
            or current_memory_consolidation_closeout_path_allowed
            or current_counterfactual_planning_path_allowed
            or current_counterfactual_planning_closeout_path_allowed
            or current_information_acquisition_path_allowed
            or current_information_acquisition_closeout_path_allowed
            or current_continual_learning_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION185_PROHIBITED_PREFIXES),
            f"prohibited AION-185 path changed: {relative}",
        )
        _assert(
            _aion185_path_allowed(relative)
            or current_world_model_path_allowed
            or current_world_model_closeout_path_allowed
            or current_workspace_path_allowed
            or current_workspace_closeout_path_allowed
            or current_memory_consolidation_path_allowed
            or current_memory_consolidation_closeout_path_allowed
            or current_counterfactual_planning_path_allowed
            or current_counterfactual_planning_closeout_path_allowed
            or current_information_acquisition_path_allowed
            or current_information_acquisition_closeout_path_allowed
            or current_continual_learning_path_allowed,
            f"unexpected AION-185 path changed: {relative}",
        )


def validate_aion185_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-persistent-state-evaluation/v1",
        "bad AION-185 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-185 program id")
    _assert(payload["task_id"] == AION185_TASK_ID, "bad AION-185 task id")
    _assert(payload["evaluation_id"] == AION185_EVALUATION_ID, "bad AION-185 evaluation id")
    _assert(payload["evaluated_task"] == AION184_TASK_ID, "bad evaluated task")
    _assert(payload["closed_authorization_id"] == AION183_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["result"] == "PASS", "AION-185 evaluation must pass")
    _assert(
        payload["decision"]
        == "PERSISTENT_STATE_EVALUATION_PASS_AUTHORIZE_WORLD_MODEL",
        "bad AION-185 decision",
    )
    _assert(payload["implementation_pr"] == AION184_PR, "bad AION-184 PR")
    _assert(payload["implementation_merge_commit"] == AION184_MERGE_COMMIT, "bad AION-184 merge")
    metrics = payload["hard_pass_conditions"]
    _assert(metrics["replay_equality_rate"] == 1.0, "replay equality must be 100 percent")
    for key in (
        "state_invariant_violations",
        "lost_committed_events",
        "duplicate_applied_events",
        "forbidden_side_effects",
    ):
        _assert(metrics[key] == 0, f"{key} must be zero")
    for key in (
        "restart_continuity",
        "concurrency",
        "contradiction_handling",
        "uncertainty_tracking",
        "retention",
        "corruption_detection",
        "repository_integrity",
        "zero_runtime_side_effects",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "deployment_enabled",
        "model_weights_changed",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")


def validate_aion185_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-world-model-authorization/v1",
        "bad AION-185 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-185 authorization program")
    _assert(payload["authorization_id"] == AION185_AUTHORIZATION_ID, "bad AION-185 auth id")
    _assert(payload["parent_evaluation_id"] == AION185_EVALUATION_ID, "bad parent eval")
    _assert(payload["authorized_task"] == AION186_TASK_ID, "bad authorized task")
    _assert(payload["candidate_id"] == AION186_CANDIDATE_ID, "bad candidate")
    _assert(payload["scope"] == AION186_SCOPE, "bad AION-186 scope")
    _assert(payload["authorization_active"] is True, "AION-185 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-185 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-185 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-185 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == "AION-187", "bad formal closeout")
    for contract in WORLD_MODEL_REQUIRED_CONTRACTS:
        _assert(contract in payload["required_contracts"], f"missing world contract: {contract}")
    for service in WORLD_MODEL_REQUIRED_SERVICES:
        _assert(service in payload["required_services"], f"missing world service: {service}")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")
    _assert(payload["resource_limits"]["network_calls"] == 0, "network calls must be zero")
    _assert(payload["resource_limits"]["model_provider_calls"] == 0, "provider calls must be zero")
    _assert(payload["resource_limits"]["model_weight_training"] == 0, "model training must be zero")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")


def validate_world_model(root: Path) -> None:
    validate_persistent_state_closeout(root)
    validate_required_files(root, AION186_REQUIRED_FILES)
    validate_aion186_world_model_payload(
        _load_json(root, "examples/cognitive-architecture/aion-186-predictive-world-model.json")
    )
    validate_no_claim_terms(
        root,
        (
            root / "services/brain-api/src/aion_brain/contracts/world_model.py",
            root / "services/brain-api/src/aion_brain/world_model",
            root / "services/brain-api/tests/test_cognitive_predictive_world_model.py",
            root
            / "services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py",
        ),
    )
    contract_text = (root / "services/brain-api/src/aion_brain/contracts/world_model.py").read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/world_model").glob("*.py")
    )
    for contract in WORLD_MODEL_REQUIRED_CONTRACTS:
        _assert(f"class {contract}" in contract_text, f"missing world-model contract: {contract}")
    for service in (
        "WorldStateEncoder",
        "DeterministicTransitionModel",
        "ProbabilisticTransitionModel",
        "OutcomePredictor",
        "UncertaintyEstimator",
        "CausalHypothesisService",
        "CounterfactualSimulator",
    ):
        _assert(f"class {service}" in source_text, f"missing world-model service: {service}")
    _assert("class TransitionModel(Protocol)" in source_text, "missing transition protocol")
    _assert("class WorldModelRepository(Protocol)" in source_text, "missing repository protocol")
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-186.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Algorithm",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-186 task doc missing {section}")
    for term in (
        AION185_AUTHORIZATION_ID,
        AION186_CANDIDATE_ID,
        AION186_SCOPE,
        "AION-187",
    ):
        _assert(term in task_doc, f"AION-186 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    implementation = _find_record(program["records"], "implementation_task", AION186_TASK_ID)
    _assert(implementation["authorization_id"] == AION185_AUTHORIZATION_ID, "AION-186 auth")
    _assert(implementation["candidate_id"] == AION186_CANDIDATE_ID, "AION-186 candidate")
    _assert(implementation["runtime_effect"] is False, "AION-186 runtime effect")
    world_model_authorization = _find_record(
        authorization["records"],
        "authorization_id",
        AION185_AUTHORIZATION_ID,
    )
    if world_model_authorization["record_kind"] == "implementation_authorization":
        _assert(
            world_model_authorization["authorization_active"] is True,
            "AION-185 auth remains active until AION-187",
        )
        _assert(
            world_model_authorization["implementation_state"]
            == "implemented_pending_aion_187_evaluation",
            "AION-186 implementation state must await AION-187",
        )
    else:
        _assert(
            world_model_authorization["authorization_active"] is False,
            "AION-185 auth must be inactive after AION-187",
        )
        _assert(
            world_model_authorization["authorization_closed_by_task"] == AION187_TASK_ID,
            "AION-185 auth closeout task mismatch",
        )
        _assert(
            implementation["task_state"] == "merged_evaluated_passed",
            "AION-186 must be evaluated after AION-187",
        )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/world_model.py").exists(),
        "AION-186 must not add a world-model API route",
    )


def validate_world_model_no_go(root: Path) -> None:
    validate_world_model(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion187_path_allowed = _aion187_closeout_record_exists(root) and _aion187_path_allowed(
            relative
        )
        aion188_path_allowed = _aion188_implementation_record_exists(root) and _aion188_path_allowed(
            relative
        )
        aion189_path_allowed = _aion189_closeout_record_exists(root) and _aion189_path_allowed(
            relative
        )
        aion190_path_allowed = _aion190_implementation_record_exists(root) and _aion190_path_allowed(
            relative
        )
        aion191_path_allowed = _aion191_closeout_record_exists(root) and _aion191_path_allowed(
            relative
        )
        aion192_path_allowed = _aion192_implementation_record_exists(root) and _aion192_path_allowed(
            relative
        )
        aion193_path_allowed = _aion193_closeout_record_exists(root) and _aion193_path_allowed(
            relative
        )
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion187_path_allowed
            or aion188_path_allowed
            or aion189_path_allowed
            or aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION186_PROHIBITED_PREFIXES),
            f"prohibited AION-186 path changed: {relative}",
        )
        _assert(
            _aion186_path_allowed(relative)
            or aion187_path_allowed
            or aion188_path_allowed
            or aion189_path_allowed
            or aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-186 path changed: {relative}",
        )
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/world_model").glob("*.py")
    )
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        _assert(marker not in source_text, f"prohibited world-model source marker: {marker}")


def validate_aion186_world_model_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-predictive-world-model-evidence/v1",
        "bad AION-186 world-model evidence schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-186 program id")
    _assert(payload["task_id"] == AION186_TASK_ID, "bad AION-186 task id")
    _assert(payload["authorization_id"] == AION185_AUTHORIZATION_ID, "bad AION-186 auth")
    _assert(payload["candidate_id"] == AION186_CANDIDATE_ID, "bad AION-186 candidate")
    _assert(payload["scope"] == AION186_SCOPE, "bad AION-186 scope")
    for key in (
        "multiple_possible_futures",
        "calibrated_uncertainty",
        "counterfactual_branches",
        "action_effect_comparison",
        "reversible_effect_flags",
        "irreversible_effect_flags",
        "unknown_state_detection",
        "model_version_fingerprints",
        "data_provenance",
        "deterministic_replay",
    ):
        _assert(payload["capabilities"][key] is True, f"{key} must be true")
    model = payload["model"]
    _assert(model["model_weight_training"] is False, "model weights must not train")
    for key in ("network_calls", "connector_calls", "model_provider_calls"):
        _assert(model[key] == 0, f"{key} must be zero")
    _assert(model["runtime_action_execution"] is False, "runtime action execution must be false")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "deployment_enabled",
        "model_weights_changed",
    ):
        _assert(side_effects[key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] == 0, f"{key} must be zero")
    _assert(payload["next_task"] == "AION-187", "AION-186 next task mismatch")


def validate_world_model_closeout(root: Path) -> None:
    validate_world_model(root)
    validate_required_files(root, AION187_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-187.md",
            root / "services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-187-world-model-evaluation.json",
    )
    workspace_authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-187-workspace-authorization.json",
    )
    validate_aion187_evaluation_payload(evaluation)
    validate_aion187_authorization_payload(workspace_authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-187.md").read_text()
    for section in (
        "## Task Purpose",
        "## Evaluation",
        "## Closed Authorization",
        "## Hard PASS Conditions",
        "## New Authorization",
        "## AION-188 Scope",
        "## Source Boundaries",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-187 task doc missing {section}")
    for term in (
        AION187_EVALUATION_ID,
        AION185_AUTHORIZATION_ID,
        AION187_AUTHORIZATION_ID,
        AION188_TASK_ID,
        AION188_SCOPE,
    ):
        _assert(term in task_doc, f"AION-187 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout = _find_evaluation_record(
        program["records"],
        AION187_TASK_ID,
        AION187_EVALUATION_ID,
    )
    _assert(closeout["result"] == "PASS", "AION-187 ledger result must pass")
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    _assert(
        program["active_cognitive_implementation_authorization"]
        in {
            AION187_AUTHORIZATION_ID,
            AION189_AUTHORIZATION_ID,
            AION191_AUTHORIZATION_ID,
            AION193_AUTHORIZATION_ID,
            AION195_AUTHORIZATION_ID,
        }
        or (
            aion197_closeout_exists
            and program["active_cognitive_implementation_authorization"] is None
        ),
        "AION-187 authorization chain mismatch",
    )
    closed = _find_record(authorization["records"], "authorization_id", AION185_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-185 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-185 authorization must be consumed")
    active = _find_record(authorization["records"], "authorization_id", AION187_AUTHORIZATION_ID)
    if authorization["active_cognitive_implementation_authorization"] == AION187_AUTHORIZATION_ID:
        _assert(active["authorization_active"] is True, "AION-187 authorization must be active")
    else:
        _assert(active["authorization_active"] is False, "AION-187 authorization must be closed")
        _assert(
            active["authorization_closed_by_task"] == AION189_TASK_ID,
            "AION-187 closeout task mismatch",
        )
    _assert(active["implementation_task"] == AION188_TASK_ID, "AION-188 authorization mismatch")
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/workspace.py").exists(),
        "AION-187 must not add a workspace API route",
    )
    _assert(
        _aion188_implementation_record_exists(root)
        or not (root / "services/brain-api/src/aion_brain/workspace").exists(),
        "AION-187 must not implement workspace runtime source",
    )


def validate_world_model_closeout_no_go(root: Path) -> None:
    validate_world_model_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion188_path_allowed = _aion188_implementation_record_exists(root) and _aion188_path_allowed(
            relative
        )
        aion189_path_allowed = _aion189_closeout_record_exists(root) and _aion189_path_allowed(
            relative
        )
        aion190_path_allowed = _aion190_implementation_record_exists(root) and _aion190_path_allowed(
            relative
        )
        aion191_path_allowed = _aion191_closeout_record_exists(root) and _aion191_path_allowed(
            relative
        )
        aion192_path_allowed = _aion192_implementation_record_exists(root) and _aion192_path_allowed(
            relative
        )
        aion193_path_allowed = _aion193_closeout_record_exists(root) and _aion193_path_allowed(
            relative
        )
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion188_path_allowed
            or aion189_path_allowed
            or aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION187_PROHIBITED_PREFIXES),
            f"prohibited AION-187 path changed: {relative}",
        )
        _assert(
            _aion187_path_allowed(relative)
            or aion188_path_allowed
            or aion189_path_allowed
            or aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-187 path changed: {relative}",
        )


def validate_aion187_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-world-model-evaluation/v1",
        "bad AION-187 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-187 program id")
    _assert(payload["task_id"] == AION187_TASK_ID, "bad AION-187 task id")
    _assert(payload["evaluation_id"] == AION187_EVALUATION_ID, "bad AION-187 evaluation id")
    _assert(payload["evaluated_task"] == AION186_TASK_ID, "bad AION-187 evaluated task")
    _assert(payload["closed_authorization_id"] == AION185_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["result"] == "PASS", "AION-187 evaluation must pass")
    _assert(
        payload["decision"] == "WORLD_MODEL_EVALUATION_PASS_AUTHORIZE_GLOBAL_WORKSPACE",
        "bad AION-187 decision",
    )
    _assert(payload["implementation_pr"] == AION186_PR, "bad AION-186 PR")
    _assert(payload["implementation_merge_commit"] == AION186_MERGE_COMMIT, "bad AION-186 merge")
    metrics = payload["hard_pass_conditions"]
    _assert(
        metrics["transition_top_1_accuracy"] >= 0.8,
        "transition top-1 accuracy below threshold",
    )
    _assert(metrics["brier_score"] <= 0.2, "Brier score above threshold")
    _assert(metrics["probability_sum_error"] <= 1e-9, "probability sum error too high")
    _assert(
        metrics["unknown_state_fail_closed_rate"] == 1.0,
        "unknown-state fail-closed rate must be complete",
    )
    _assert(
        metrics["deterministic_replay_rate"] == 1.0,
        "deterministic replay must be complete",
    )
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects must be zero")
    for key in (
        "prediction_accuracy",
        "probability_normalization",
        "uncertainty_calibration",
        "unseen_state_behavior",
        "counterfactual_consistency",
        "causal_hypothesis_provenance",
        "deterministic_replay",
        "no_runtime_action",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "deployment_enabled",
        "model_weights_changed",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")


def validate_aion187_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-workspace-authorization/v1",
        "bad AION-187 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-187 authorization program")
    _assert(payload["authorization_id"] == AION187_AUTHORIZATION_ID, "bad AION-187 auth id")
    _assert(payload["parent_evaluation_id"] == AION187_EVALUATION_ID, "bad parent eval")
    _assert(payload["authorized_task"] == AION188_TASK_ID, "bad authorized task")
    _assert(payload["candidate_id"] == AION188_CANDIDATE_ID, "bad workspace candidate")
    _assert(payload["scope"] == AION188_SCOPE, "bad AION-188 scope")
    _assert(payload["authorization_active"] is True, "AION-187 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-187 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-187 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-187 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == "AION-189", "bad formal closeout")
    for contract in WORKSPACE_REQUIRED_CONTRACTS:
        _assert(contract in payload["required_contracts"], f"missing workspace contract: {contract}")
    for service in WORKSPACE_REQUIRED_SERVICES:
        _assert(service in payload["required_services"], f"missing workspace service: {service}")
    for dimension in WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS:
        _assert(
            dimension in payload["salience_dimensions"],
            f"missing salience dimension: {dimension}",
        )
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")
    _assert(payload["resource_limits"]["network_calls"] == 0, "network calls must be zero")
    _assert(payload["resource_limits"]["model_provider_calls"] == 0, "provider calls must be zero")
    _assert(payload["resource_limits"]["action_execution"] == 0, "action execution must be zero")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")


def validate_aion188_workspace_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-global-workspace-evidence/v1",
        "bad AION-188 workspace evidence schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-188 program id")
    _assert(payload["task_id"] == AION188_TASK_ID, "bad AION-188 task id")
    _assert(payload["authorization_id"] == AION187_AUTHORIZATION_ID, "bad AION-188 auth")
    _assert(payload["candidate_id"] == AION188_CANDIDATE_ID, "bad AION-188 candidate")
    _assert(payload["scope"] == AION188_SCOPE, "bad AION-188 scope")
    for contract in WORKSPACE_REQUIRED_CONTRACTS:
        _assert(contract in payload["contracts"], f"missing AION-188 contract: {contract}")
    for service in WORKSPACE_REQUIRED_SERVICES:
        _assert(service in payload["services"], f"missing AION-188 service: {service}")
    for dimension in WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS:
        _assert(
            dimension in payload["salience_dimensions"],
            f"missing AION-188 salience dimension: {dimension}",
        )
    for key in (
        "immutable_specialist_bids",
        "bounded_working_set",
        "deterministic_tie_breaking",
        "critical_safety_preemption",
        "anti_starvation",
        "capacity_limits",
        "approved_specialist_broadcast",
        "duplicate_bid_handling",
        "cycle_provenance",
    ):
        _assert(payload["capabilities"][key] is True, f"{key} must be true")
    runtime = payload["runtime_boundaries"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "deployment_enabled",
        "model_weights_changed",
        "subjective_state_claim",
    ):
        _assert(runtime[key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_calls_by_default",
        "source_rewrite_operations",
        "git_operations",
        "forbidden_side_effects",
    ):
        _assert(runtime[key] == 0, f"{key} must be zero")
    _assert(payload["next_task"] == AION189_TASK_ID, "AION-188 next task mismatch")


def validate_global_workspace(root: Path) -> None:
    validate_world_model_closeout(root)
    validate_required_files(root, AION188_REQUIRED_FILES)
    validate_aion188_workspace_payload(
        _load_json(root, "examples/cognitive-architecture/aion-188-global-workspace.json")
    )
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-188.md",
            root / "services/brain-api/src/aion_brain/contracts/workspace.py",
            root / "services/brain-api/src/aion_brain/workspace",
            root / "services/brain-api/tests/test_cognitive_global_workspace.py",
            root / "services/brain-api/tests/test_cognitive_global_workspace_no_runtime_effect.py",
        ),
    )
    contract_text = (root / "services/brain-api/src/aion_brain/contracts/workspace.py").read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/workspace").glob("*.py")
    )
    for contract in WORKSPACE_REQUIRED_CONTRACTS:
        _assert(f"class {contract}" in contract_text, f"missing workspace contract: {contract}")
    for service in (
        "AttentionArbiter",
        "WorkspaceCapacityController",
        "WorkspaceBroadcastService",
        "AntiStarvationController",
        "CognitiveCycleCoordinator",
    ):
        _assert(f"class {service}" in source_text, f"missing workspace service: {service}")
    _assert("class CognitiveSpecialist(Protocol)" in source_text, "missing specialist protocol")
    for dimension in WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS:
        _assert(f"{dimension}:" in contract_text, f"missing salience field: {dimension}")
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-188.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Algorithm",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-188 task doc missing {section}")
    for term in (
        AION187_AUTHORIZATION_ID,
        AION188_CANDIDATE_ID,
        AION188_SCOPE,
        AION189_TASK_ID,
    ):
        _assert(term in task_doc, f"AION-188 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    _assert(
        program["program_state"]
        in {
            "global_workspace_implemented_pending_evaluation",
            "global_workspace_evaluated_consolidation_authorized",
            "memory_consolidation_implemented_pending_evaluation",
            "memory_consolidation_evaluated_planning_authorized",
            "counterfactual_planning_implemented_pending_evaluation",
            "counterfactual_planning_evaluated_information_acquisition_authorized",
            "information_acquisition_implemented_pending_evaluation",
            "information_acquisition_evaluated_continual_learning_authorized",
            "continual_learning_implemented_pending_integrated_evaluation",
            AION197_PROGRAM_STATE,
        },
        "AION-188 program state mismatch",
    )
    implementation = _find_record(program["records"], "implementation_task", AION188_TASK_ID)
    _assert(implementation["authorization_id"] == AION187_AUTHORIZATION_ID, "AION-188 auth")
    _assert(implementation["candidate_id"] == AION188_CANDIDATE_ID, "AION-188 candidate")
    _assert(implementation["scope"] == AION188_SCOPE, "AION-188 scope")
    _assert(implementation["closeout_task"] == AION189_TASK_ID, "AION-188 closeout")
    _assert(implementation["runtime_effect"] is False, "AION-188 runtime effect")
    _assert(implementation["forbidden_side_effects"] == 0, "AION-188 side effects")
    _assert(
        implementation["task_state"]
        in {
            "implemented_pending_aion_189_evaluation",
            "merged_evaluated_passed",
        },
        "AION-188 task state",
    )
    if implementation["task_state"] == "merged_evaluated_passed":
        _assert(implementation["pr"] == AION188_PR, "AION-188 PR mismatch")
        _assert(implementation["merge_commit"] == AION188_MERGE_COMMIT, "AION-188 merge")
    active = _find_record(authorization["records"], "authorization_id", AION187_AUTHORIZATION_ID)
    if authorization["active_cognitive_implementation_authorization"] == AION187_AUTHORIZATION_ID:
        _assert(active["authorization_active"] is True, "AION-187 authorization must remain active")
        _assert(
            active["implementation_state"] == "implemented_pending_aion_189_evaluation",
            "AION-187 implementation state must await AION-189",
        )
    else:
        _assert(active["authorization_active"] is False, "AION-187 authorization must be closed")
        _assert(
            active["authorization_closed_by_task"] == AION189_TASK_ID,
            "AION-187 authorization closeout mismatch",
        )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/workspace.py").exists(),
        "AION-188 must not add a workspace API route",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/global_workspace.py").exists(),
        "AION-188 must not add a global-workspace API route",
    )
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        _assert(marker not in source_text, f"prohibited workspace source marker: {marker}")


def validate_global_workspace_no_go(root: Path) -> None:
    validate_global_workspace(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion189_path_allowed = _aion189_closeout_record_exists(root) and _aion189_path_allowed(
            relative
        )
        aion190_path_allowed = _aion190_implementation_record_exists(root) and _aion190_path_allowed(
            relative
        )
        aion191_path_allowed = _aion191_closeout_record_exists(root) and _aion191_path_allowed(
            relative
        )
        aion192_path_allowed = _aion192_implementation_record_exists(root) and _aion192_path_allowed(
            relative
        )
        aion193_path_allowed = _aion193_closeout_record_exists(root) and _aion193_path_allowed(
            relative
        )
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion189_path_allowed
            or aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION188_PROHIBITED_PREFIXES),
            f"prohibited AION-188 path changed: {relative}",
        )
        _assert(
            _aion188_path_allowed(relative)
            or aion189_path_allowed
            or aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-188 path changed: {relative}",
        )


def validate_aion189_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-global-workspace-evaluation/v1",
        "bad AION-189 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-189 program id")
    _assert(payload["task_id"] == AION189_TASK_ID, "bad AION-189 task id")
    _assert(payload["evaluation_id"] == AION189_EVALUATION_ID, "bad AION-189 evaluation")
    _assert(payload["evaluated_task"] == AION188_TASK_ID, "bad AION-189 evaluated task")
    _assert(payload["closed_authorization_id"] == AION187_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["result"] == "PASS", "AION-189 evaluation must pass")
    _assert(
        payload["decision"]
        == "GLOBAL_WORKSPACE_EVALUATION_PASS_AUTHORIZE_MEMORY_CONSOLIDATION",
        "bad AION-189 decision",
    )
    _assert(payload["implementation_pr"] == AION188_PR, "bad AION-188 PR")
    _assert(payload["implementation_merge_commit"] == AION188_MERGE_COMMIT, "bad AION-188 merge")
    metrics = payload["hard_pass_conditions"]
    for key in (
        "deterministic_arbitration_rate",
        "safety_preemption_rate",
        "anti_starvation_coverage",
        "bounded_capacity_rate",
        "broadcast_consistency_rate",
        "duplicate_bid_handling_rate",
        "concurrency_replay_rate",
        "cycle_provenance_coverage",
    ):
        _assert(metrics[key] == 1.0, f"{key} must be complete")
    _assert(metrics["direct_action_count"] == 0, "direct actions must be zero")
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects must be zero")
    for key in (
        "deterministic_arbitration",
        "safety_preemption",
        "anti_starvation",
        "bounded_capacity",
        "broadcast_consistency",
        "duplicate_bid_handling",
        "concurrency",
        "cycle_provenance",
        "zero_direct_actions",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "deployment_enabled",
        "model_weights_changed",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")
    _assert(payload["new_authorization_id"] == AION189_AUTHORIZATION_ID, "bad new auth")
    _assert(payload["authorized_task"] == AION190_TASK_ID, "bad authorized task")
    _assert(payload["next_task"] == AION190_TASK_ID, "bad next task")


def validate_aion189_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-memory-consolidation-authorization/v1",
        "bad AION-189 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-189 authorization program")
    _assert(payload["authorization_id"] == AION189_AUTHORIZATION_ID, "bad AION-189 auth")
    _assert(payload["parent_evaluation_id"] == AION189_EVALUATION_ID, "bad parent eval")
    _assert(payload["parent_task"] == AION189_TASK_ID, "bad parent task")
    _assert(payload["parent_commit"] == AION188_MERGE_COMMIT, "bad parent commit")
    _assert(payload["parent_pr"] == AION188_PR, "bad parent PR")
    _assert(payload["authorized_task"] == AION190_TASK_ID, "bad AION-190 task")
    _assert(payload["candidate_id"] == AION190_CANDIDATE_ID, "bad AION-190 candidate")
    _assert(payload["scope"] == AION190_SCOPE, "bad AION-190 scope")
    _assert(payload["authorization_active"] is True, "AION-189 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-189 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-189 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-189 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == "AION-191", "bad formal closeout")
    for contract in CONSOLIDATION_REQUIRED_CONTRACTS:
        _assert(
            contract in payload["required_contracts"],
            f"missing consolidation contract: {contract}",
        )
    for service in CONSOLIDATION_REQUIRED_SERVICES:
        _assert(service in payload["required_services"], f"missing consolidation service: {service}")
    for stage in CONSOLIDATION_REQUIRED_PIPELINE:
        _assert(stage in payload["required_pipeline"], f"missing pipeline stage: {stage}")
    for behavior in (
        "automatic semantic promotion",
        "automatic procedural promotion",
        "source rewrite",
        "model-weight update",
        "background consolidation",
        "hidden memory mutation",
        "deletion without explicit policy evidence",
    ):
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    _assert(payload["resource_limits"]["network_calls"] == 0, "network calls must be zero")
    _assert(payload["resource_limits"]["model_provider_calls"] == 0, "provider calls must be zero")
    _assert(payload["resource_limits"]["automatic_promotion"] == 0, "automatic promotion")
    _assert(payload["resource_limits"]["hidden_memory_mutation"] == 0, "hidden memory mutation")
    _assert(payload["resource_limits"]["deletion_without_policy_evidence"] == 0, "deletion")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")


def validate_workspace_closeout(root: Path) -> None:
    validate_global_workspace(root)
    validate_required_files(root, AION189_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-189.md",
            root / "services/brain-api/tests/test_cognitive_workspace_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-189-workspace-evaluation.json",
    )
    authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-189-consolidation-authorization.json",
    )
    validate_aion189_evaluation_payload(evaluation)
    validate_aion189_authorization_payload(authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-189.md").read_text()
    for section in (
        "## Task Purpose",
        "## Evaluation",
        "## Closed Authorization",
        "## Hard PASS Conditions",
        "## New Authorization",
        "## AION-190 Scope",
        "## Source Boundaries",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-189 task doc missing {section}")
    for term in (
        AION189_EVALUATION_ID,
        AION187_AUTHORIZATION_ID,
        AION189_AUTHORIZATION_ID,
        AION190_TASK_ID,
        AION190_SCOPE,
    ):
        _assert(term in task_doc, f"AION-189 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization_ledger = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout = _find_evaluation_record(
        program["records"],
        AION189_TASK_ID,
        AION189_EVALUATION_ID,
    )
    _assert(closeout["result"] == "PASS", "AION-189 ledger result must pass")
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    _assert(
        program["active_cognitive_implementation_authorization"]
        in {
            AION189_AUTHORIZATION_ID,
            AION191_AUTHORIZATION_ID,
            AION193_AUTHORIZATION_ID,
            AION195_AUTHORIZATION_ID,
        }
        or (
            aion197_closeout_exists
            and program["active_cognitive_implementation_authorization"] is None
        ),
        "AION-189 authorization chain mismatch",
    )
    closed = _find_record(
        authorization_ledger["records"],
        "authorization_id",
        AION187_AUTHORIZATION_ID,
    )
    _assert(closed["authorization_active"] is False, "AION-187 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-187 authorization must be consumed")
    active = _find_record(
        authorization_ledger["records"],
        "authorization_id",
        AION189_AUTHORIZATION_ID,
    )
    if (
        authorization_ledger["active_cognitive_implementation_authorization"]
        == AION189_AUTHORIZATION_ID
    ):
        _assert(active["authorization_active"] is True, "AION-189 authorization must be active")
    else:
        _assert(active["authorization_active"] is False, "AION-189 authorization must be closed")
        _assert(
            active["authorization_closed_by_task"] == AION191_TASK_ID,
            "AION-189 closeout task mismatch",
        )
    _assert(active["implementation_task"] == AION190_TASK_ID, "AION-190 authorization mismatch")
    if _aion190_implementation_record_exists(root):
        _assert(
            (root / "services/brain-api/src/aion_brain/memory_consolidation").is_dir(),
            "AION-190 implementation record requires memory-consolidation source",
        )
        _assert(
            (root / "services/brain-api/src/aion_brain/contracts/memory_consolidation.py").is_file(),
            "AION-190 implementation record requires memory-consolidation contract",
        )
    else:
        _assert(
            not (root / "services/brain-api/src/aion_brain/memory_consolidation").exists(),
            "AION-189 must not implement memory-consolidation source",
        )
        _assert(
            not (root / "services/brain-api/src/aion_brain/contracts/memory_consolidation.py").exists(),
            "AION-189 must not implement memory-consolidation contracts",
        )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/memory_consolidation.py").exists(),
        "AION-189 must not add a memory-consolidation API route",
    )


def validate_aion190_implementation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-memory-consolidation-implementation/v1",
        "bad AION-190 implementation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-190 program id")
    _assert(payload["task_id"] == AION190_TASK_ID, "bad AION-190 task id")
    _assert(payload["authorization_id"] == AION189_AUTHORIZATION_ID, "bad AION-190 auth")
    _assert(payload["candidate_id"] == AION190_CANDIDATE_ID, "bad AION-190 candidate")
    _assert(payload["scope"] == AION190_SCOPE, "bad AION-190 scope")
    _assert(payload["closeout_task"] == AION191_TASK_ID, "bad AION-190 closeout")
    _assert(
        payload["implementation_state"] == "implemented_pending_aion_191_evaluation",
        "bad AION-190 implementation state",
    )
    for contract in CONSOLIDATION_REQUIRED_CONTRACTS:
        _assert(contract in payload["contracts"], f"missing consolidation contract: {contract}")
    for service in CONSOLIDATION_REQUIRED_SERVICES:
        _assert(service in payload["services"], f"missing consolidation service: {service}")
    for stage in CONSOLIDATION_REQUIRED_PIPELINE:
        _assert(stage in payload["pipeline"], f"missing consolidation pipeline stage: {stage}")
    for behavior in (
        "automatic semantic promotion",
        "automatic procedural promotion",
        "source rewrite",
        "model-weight update",
        "background consolidation",
        "hidden memory mutation",
        "deletion without explicit policy evidence",
    ):
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    capabilities = payload["capabilities"]
    for key in (
        "deterministic_replay_selection",
        "semantic_candidate_generation",
        "procedural_candidate_synthesis",
        "contradiction_analysis",
        "benchmark_evidence",
        "operator_review_checkpoints",
        "non_destructive_forgetting_candidates",
    ):
        _assert(capabilities[key] is True, f"{key} must be true")
    metrics = payload["benchmark_requirements"]
    _assert(metrics["retained_critical_memories_rate"] == 1.0, "critical memory retention")
    _assert(metrics["duplicate_reduction_minimum"] >= 0.8, "duplicate reduction threshold")
    _assert(metrics["contradiction_loss_rate"] == 0.0, "contradiction loss")
    _assert(metrics["catastrophic_forgetting_maximum"] <= 0.05, "forgetting threshold")
    _assert(metrics["provenance_coverage"] == 1.0, "provenance coverage")
    _assert(metrics["unauthorized_promotion_count"] == 0, "unauthorized promotion count")
    _assert(metrics["deterministic_replay_rate"] == 1.0, "deterministic replay")
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
    runtime = payload["runtime_boundaries"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "deployment_enabled",
        "model_weights_changed",
        "production_exposure",
        "automatic_promotion",
        "hidden_memory_mutation",
    ):
        _assert(runtime[key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "source_rewrite_operations",
        "git_operations",
        "forbidden_side_effects",
    ):
        _assert(runtime[key] == 0, f"{key} must be zero")


def validate_memory_consolidation(root: Path) -> None:
    validate_workspace_closeout(root)
    validate_required_files(root, AION190_REQUIRED_FILES)
    validate_aion190_implementation_payload(
        _load_json(root, "examples/cognitive-architecture/aion-190-memory-consolidation.json")
    )
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-190.md",
            root / "services/brain-api/src/aion_brain/contracts/memory_consolidation.py",
            root / "services/brain-api/src/aion_brain/memory_consolidation",
            root / "services/brain-api/tests/test_cognitive_memory_consolidation.py",
            root
            / "services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py",
        ),
    )
    contract_text = (
        root / "services/brain-api/src/aion_brain/contracts/memory_consolidation.py"
    ).read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/memory_consolidation").glob(
            "*.py"
        )
    )
    for contract in CONSOLIDATION_REQUIRED_CONTRACTS:
        _assert(
            f"class {contract}" in contract_text,
            f"missing memory-consolidation contract: {contract}",
        )
    for service in CONSOLIDATION_REQUIRED_SERVICES:
        _assert(f"class {service}" in source_text, f"missing consolidation service: {service}")
    for marker in (
        "automatic_promotion",
        "hidden_memory_mutation",
        "deletion_without_policy_evidence",
    ):
        _assert(marker in contract_text, f"missing runtime boundary marker: {marker}")
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-190.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Pipeline",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-190 task doc missing {section}")
    for term in (
        AION189_AUTHORIZATION_ID,
        AION190_CANDIDATE_ID,
        AION190_SCOPE,
        AION191_TASK_ID,
    ):
        _assert(term in task_doc, f"AION-190 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    _assert(
        program["program_state"]
        in {
            "memory_consolidation_implemented_pending_evaluation",
            "memory_consolidation_evaluated_planning_authorized",
            "counterfactual_planning_implemented_pending_evaluation",
            "counterfactual_planning_evaluated_information_acquisition_authorized",
            "information_acquisition_implemented_pending_evaluation",
            "information_acquisition_evaluated_continual_learning_authorized",
            "continual_learning_implemented_pending_integrated_evaluation",
            AION197_PROGRAM_STATE,
        },
        "AION-190 program state mismatch",
    )
    implementation = _find_record(program["records"], "implementation_task", AION190_TASK_ID)
    _assert(implementation["authorization_id"] == AION189_AUTHORIZATION_ID, "AION-190 auth")
    _assert(implementation["candidate_id"] == AION190_CANDIDATE_ID, "AION-190 candidate")
    _assert(implementation["scope"] == AION190_SCOPE, "AION-190 scope")
    _assert(implementation["closeout_task"] == AION191_TASK_ID, "AION-190 closeout")
    _assert(implementation["evaluation_id"] == AION191_EVALUATION_ID, "AION-190 eval")
    _assert(implementation["runtime_effect"] is False, "AION-190 runtime effect")
    _assert(implementation["forbidden_side_effects"] == 0, "AION-190 side effects")
    _assert(
        implementation["task_state"]
        in {
            "implemented_pending_aion_191_evaluation",
            "merged_evaluated_passed",
        },
        "AION-190 task state",
    )
    if implementation["task_state"] == "merged_evaluated_passed":
        _assert(implementation["pr"] == AION190_PR, "AION-190 PR")
        _assert(implementation["merge_commit"] == AION190_MERGE_COMMIT, "AION-190 merge")
    active = _find_record(authorization["records"], "authorization_id", AION189_AUTHORIZATION_ID)
    if authorization["active_cognitive_implementation_authorization"] == AION189_AUTHORIZATION_ID:
        _assert(active["authorization_active"] is True, "AION-189 authorization must remain active")
        _assert(active["authorization_consumed"] is False, "AION-189 must not be consumed yet")
        _assert(
            active["authorization_expired"] is False,
            "AION-189 must not expire before AION-191",
        )
        _assert(
            active["implementation_state"] == "implemented_pending_aion_191_evaluation",
            "AION-189 implementation state must await AION-191",
        )
    else:
        _assert(active["authorization_active"] is False, "AION-189 authorization must be closed")
        _assert(active["authorization_consumed"] is True, "AION-189 must be consumed")
        _assert(active["authorization_expired"] is True, "AION-189 must be expired")
        _assert(
            active["authorization_closed_by_task"] == AION191_TASK_ID,
            "AION-189 closeout mismatch",
        )
    _assert(active["authorization_reusable"] is False, "AION-189 must remain non-reusable")
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/memory_consolidation.py").exists(),
        "AION-190 must not add a memory-consolidation API route",
    )
    for path in (
        root / "services/brain-api/src/aion_brain/kernel/container.py",
        root / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        _assert(
            "aion_brain.memory_consolidation" not in path.read_text(),
            "AION-190 must not add kernel memory-consolidation registration",
        )
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        _assert(marker not in source_text, f"prohibited consolidation source marker: {marker}")


def validate_aion191_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-memory-consolidation-evaluation/v1",
        "bad AION-191 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-191 program id")
    _assert(payload["task_id"] == AION191_TASK_ID, "bad AION-191 task id")
    _assert(payload["evaluation_id"] == AION191_EVALUATION_ID, "bad AION-191 evaluation")
    _assert(payload["evaluated_task"] == AION190_TASK_ID, "bad AION-191 evaluated task")
    _assert(payload["closed_authorization_id"] == AION189_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["implementation_pr"] == AION190_PR, "bad AION-190 PR")
    _assert(payload["implementation_merge_commit"] == AION190_MERGE_COMMIT, "bad AION-190 merge")
    _assert(payload["result"] == "PASS", "AION-191 evaluation must pass")
    _assert(
        payload["decision"]
        == "MEMORY_CONSOLIDATION_EVALUATION_PASS_AUTHORIZE_COUNTERFACTUAL_PLANNING",
        "bad AION-191 decision",
    )
    metrics = payload["hard_pass_conditions"]
    _assert(metrics["retained_critical_memories_rate"] == 1.0, "critical retention")
    _assert(metrics["duplicate_reduction_rate"] >= 0.8, "duplicate reduction")
    _assert(metrics["contradiction_loss_rate"] == 0.0, "contradiction loss")
    _assert(metrics["catastrophic_forgetting_rate"] <= 0.05, "catastrophic forgetting")
    _assert(metrics["provenance_coverage"] == 1.0, "provenance coverage")
    _assert(metrics["unauthorized_promotion_count"] == 0, "unauthorized promotions")
    _assert(metrics["deterministic_replay_rate"] == 1.0, "deterministic replay")
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
    for key in (
        "episodic_recall",
        "semantic_generalization",
        "duplicate_reduction",
        "contradiction_preservation",
        "retention",
        "approved_forgetting",
        "catastrophic_forgetting",
        "procedural_candidate_safety",
        "replay_determinism",
        "zero_automatic_promotion",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "automatic_promotion",
        "hidden_memory_mutation",
        "deletion_performed",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "deployment_enabled",
        "model_weights_changed",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")
    _assert(payload["new_authorization_id"] == AION191_AUTHORIZATION_ID, "bad new auth")
    _assert(payload["authorized_task"] == AION192_TASK_ID, "bad authorized task")
    _assert(payload["next_task"] == AION192_TASK_ID, "bad next task")


def validate_aion191_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-counterfactual-planning-authorization/v1",
        "bad AION-191 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-191 authorization program")
    _assert(payload["authorization_id"] == AION191_AUTHORIZATION_ID, "bad AION-191 auth")
    _assert(payload["parent_evaluation_id"] == AION191_EVALUATION_ID, "bad parent eval")
    _assert(payload["parent_task"] == AION191_TASK_ID, "bad parent task")
    _assert(payload["parent_commit"] == AION190_MERGE_COMMIT, "bad parent commit")
    _assert(payload["parent_pr"] == AION190_PR, "bad parent PR")
    _assert(payload["authorized_task"] == AION192_TASK_ID, "bad AION-192 task")
    _assert(payload["candidate_id"] == AION192_CANDIDATE_ID, "bad AION-192 candidate")
    _assert(payload["scope"] == AION192_SCOPE, "bad AION-192 scope")
    _assert(payload["authorization_active"] is True, "AION-191 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-191 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-191 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-191 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == AION193_TASK_ID, "bad formal closeout")
    for contract in PLANNING_REQUIRED_CONTRACTS:
        _assert(contract in payload["required_contracts"], f"missing planning contract: {contract}")
    for service in PLANNING_REQUIRED_SERVICES:
        _assert(service in payload["required_services"], f"missing planning service: {service}")
    for dimension in PLANNING_SCORE_DIMENSIONS:
        _assert(
            dimension in payload["score_dimensions"],
            f"missing planning score dimension: {dimension}",
        )
    for behavior in (
        "uses world model for bounded rollouts",
        "hard safety and policy failures override utility gains",
        "produces action proposals only",
    ):
        _assert(behavior in payload["required_behaviors"], f"missing behavior: {behavior}")
    for behavior in (
        "action execution",
        "external action dispatch",
        "background planning loop",
        "unrestricted network access",
        "model-weight update",
        "source rewrite",
        "git mutation",
    ):
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "background_loops",
        "git_operations",
        "source_rewrite_operations",
        "action_execution",
        "production_exposure",
    ):
        _assert(payload["resource_limits"][key] == 0, f"{key} must be zero")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")


def validate_memory_consolidation_closeout(root: Path) -> None:
    validate_memory_consolidation(root)
    validate_required_files(root, AION191_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-191.md",
            root
            / "services/brain-api/tests/test_cognitive_memory_consolidation_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json",
    )
    planning_authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-191-planning-authorization.json",
    )
    validate_aion191_evaluation_payload(evaluation)
    validate_aion191_authorization_payload(planning_authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-191.md").read_text()
    for section in (
        "## Task Purpose",
        "## Evaluation",
        "## Closed Authorization",
        "## Hard PASS Conditions",
        "## New Authorization",
        "## AION-192 Scope",
        "## Source Boundaries",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-191 task doc missing {section}")
    for term in (
        AION191_EVALUATION_ID,
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION192_TASK_ID,
        AION192_SCOPE,
    ):
        _assert(term in task_doc, f"AION-191 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout = _find_evaluation_record(
        program["records"],
        AION191_TASK_ID,
        AION191_EVALUATION_ID,
    )
    _assert(closeout["result"] == "PASS", "AION-191 ledger result must pass")
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    _assert(
        program["active_cognitive_implementation_authorization"]
        in {AION191_AUTHORIZATION_ID, AION193_AUTHORIZATION_ID, AION195_AUTHORIZATION_ID}
        or (
            aion197_closeout_exists
            and program["active_cognitive_implementation_authorization"] is None
        ),
        "AION-191 authorization chain mismatch",
    )
    implementation = _find_record(program["records"], "implementation_task", AION190_TASK_ID)
    _assert(implementation["pr"] == AION190_PR, "AION-190 PR")
    _assert(implementation["merge_commit"] == AION190_MERGE_COMMIT, "AION-190 merge")
    _assert(implementation["task_state"] == "merged_evaluated_passed", "AION-190 state")
    closed = _find_record(authorization["records"], "authorization_id", AION189_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-189 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-189 authorization must be consumed")
    _assert(closed["authorization_closeout_evaluation"] == AION191_EVALUATION_ID, "closeout eval")
    _assert(closed["implementation_pr"] == AION190_PR, "AION-190 closeout PR")
    _assert(closed["implementation_merge_commit"] == AION190_MERGE_COMMIT, "AION-190 closeout")
    active = _find_record(authorization["records"], "authorization_id", AION191_AUTHORIZATION_ID)
    if authorization["active_cognitive_implementation_authorization"] == AION191_AUTHORIZATION_ID:
        _assert(active["authorization_active"] is True, "AION-191 authorization must be active")
        _assert(active["authorization_consumed"] is False, "AION-191 must not be consumed yet")
        _assert(active["authorization_expired"] is False, "AION-191 must not expire yet")
    else:
        _assert(active["authorization_active"] is False, "AION-191 authorization must be closed")
        _assert(active["authorization_consumed"] is True, "AION-191 must be consumed")
        _assert(active["authorization_expired"] is True, "AION-191 must be expired")
        _assert(
            active["authorization_closed_by_task"] == AION193_TASK_ID,
            "AION-191 closeout mismatch",
        )
    _assert(active["implementation_task"] == AION192_TASK_ID, "AION-192 authorization mismatch")
    _assert(active["scope"] == AION192_SCOPE, "AION-192 scope")
    if _aion192_implementation_record_exists(root):
        _assert(
            (root / "services/brain-api/src/aion_brain/planning").is_dir(),
            "AION-192 implementation record requires planning source",
        )
        _assert(
            (root / "services/brain-api/src/aion_brain/contracts/planning.py").is_file(),
            "AION-192 implementation record requires planning contract",
        )
    else:
        planning_contract = root / "services/brain-api/src/aion_brain/contracts/planning.py"
        planning_source = root / "services/brain-api/src/aion_brain/planning"
        contract_text = planning_contract.read_text() if planning_contract.exists() else ""
        source_text = (
            "\n".join(path.read_text() for path in planning_source.glob("*.py"))
            if planning_source.is_dir()
            else ""
        )
        _assert(
            not any(f"class {contract}" in contract_text for contract in PLANNING_REQUIRED_CONTRACTS),
            "AION-191 must not implement AION-192 planning contract set",
        )
        _assert(
            not any(f"class {service}" in source_text for service in PLANNING_REQUIRED_SERVICES),
            "AION-191 must not implement AION-192 planning service set",
        )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/planning.py").exists(),
        "AION-191 must not add a planning API route",
    )


def validate_workspace_closeout_no_go(root: Path) -> None:
    validate_workspace_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion190_path_allowed = _aion190_implementation_record_exists(root) and _aion190_path_allowed(
            relative
        )
        aion191_path_allowed = _aion191_closeout_record_exists(root) and _aion191_path_allowed(
            relative
        )
        aion192_path_allowed = _aion192_implementation_record_exists(root) and _aion192_path_allowed(
            relative
        )
        aion193_path_allowed = _aion193_closeout_record_exists(root) and _aion193_path_allowed(
            relative
        )
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION189_PROHIBITED_PREFIXES),
            f"prohibited AION-189 path changed: {relative}",
        )
        _assert(
            _aion189_path_allowed(relative)
            or aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-189 path changed: {relative}",
        )


def validate_memory_consolidation_no_go(root: Path) -> None:
    validate_memory_consolidation(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion190_path_allowed = _aion190_path_allowed(relative)
        aion191_path_allowed = _aion191_closeout_record_exists(root) and _aion191_path_allowed(
            relative
        )
        aion192_path_allowed = _aion192_implementation_record_exists(root) and _aion192_path_allowed(
            relative
        )
        aion193_path_allowed = _aion193_closeout_record_exists(root) and _aion193_path_allowed(
            relative
        )
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION190_PROHIBITED_PREFIXES),
            f"prohibited AION-190 path changed: {relative}",
        )
        _assert(
            aion190_path_allowed
            or aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-190 path changed: {relative}",
        )
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/memory_consolidation").glob(
            "*.py"
        )
    )
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        _assert(marker not in source_text, f"prohibited consolidation source marker: {marker}")


def validate_memory_consolidation_closeout_no_go(root: Path) -> None:
    validate_memory_consolidation_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion191_path_allowed = _aion191_path_allowed(relative)
        aion192_path_allowed = _aion192_implementation_record_exists(root) and _aion192_path_allowed(
            relative
        )
        aion193_path_allowed = _aion193_closeout_record_exists(root) and _aion193_path_allowed(
            relative
        )
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION191_PROHIBITED_PREFIXES),
            f"prohibited AION-191 path changed: {relative}",
        )
        _assert(
            aion191_path_allowed
            or aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-191 path changed: {relative}",
        )


def validate_aion192_implementation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-counterfactual-planning-implementation/v1",
        "bad AION-192 implementation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-192 program id")
    _assert(payload["task_id"] == AION192_TASK_ID, "bad AION-192 task id")
    _assert(payload["authorization_id"] == AION191_AUTHORIZATION_ID, "bad AION-192 auth")
    _assert(payload["candidate_id"] == AION192_CANDIDATE_ID, "bad AION-192 candidate")
    _assert(payload["scope"] == AION192_SCOPE, "bad AION-192 scope")
    _assert(payload["closeout_task"] == AION193_TASK_ID, "bad AION-192 closeout")
    _assert(payload["next_task"] == AION193_TASK_ID, "bad AION-192 next task")
    _assert(
        payload["implementation_state"] == "implemented_pending_aion_193_evaluation",
        "bad AION-192 implementation state",
    )
    for contract in PLANNING_REQUIRED_CONTRACTS:
        _assert(contract in payload["contracts"], f"missing planning contract: {contract}")
    for service in PLANNING_REQUIRED_SERVICES:
        _assert(service in payload["services"], f"missing planning service: {service}")
    for dimension in PLANNING_SCORE_DIMENSIONS:
        _assert(
            dimension in payload["score_dimensions"],
            f"missing planning score dimension: {dimension}",
        )
    for key in (
        "goal_strategy_milestone_task_hierarchy",
        "bounded_counterfactual_rollouts",
        "world_model_backed_branch_scoring",
        "hard_policy_override",
        "hard_safety_override",
        "reversibility_checks",
        "resource_budget_estimates",
        "action_proposal_only",
        "deterministic_replay_hashes",
        "replanning_decisions",
    ):
        _assert(payload["capabilities"][key] is True, f"{key} must be true")
    for behavior in (
        "policy failure overrides utility gain",
        "safety failure overrides utility gain",
        "irreversible unsafe action proposals are rejected",
        "planner produces action proposals only",
    ):
        _assert(behavior in payload["hard_policy_overrides"], f"missing override: {behavior}")
    for behavior in (
        "action execution",
        "external action dispatch",
        "background planning loop",
        "unrestricted network access",
        "model-weight update",
        "source rewrite",
        "git mutation",
    ):
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    metrics = payload["benchmark_requirements"]
    _assert(
        metrics["synthetic_goal_completion_plan_success_minimum"] >= 0.8,
        "goal completion threshold",
    )
    _assert(metrics["policy_violation_count"] == 0, "policy violations must be zero")
    _assert(metrics["budget_overrun_count"] == 0, "budget overruns must be zero")
    _assert(
        metrics["irreversible_unsafe_plan_selection_count"] == 0,
        "irreversible unsafe selections must be zero",
    )
    _assert(metrics["deterministic_plan_replay_rate"] == 1.0, "deterministic replay")
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
    runtime = payload["runtime_boundaries"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "external_action_dispatch",
        "deployment_enabled",
        "production_exposure",
        "model_weights_changed",
    ):
        _assert(runtime[key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_calls_by_default",
        "model_weight_training",
        "source_rewrite_operations",
        "git_operations",
        "forbidden_side_effects",
    ):
        _assert(runtime[key] == 0, f"{key} must be zero")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "background_loops",
        "git_operations",
        "source_rewrite_operations",
        "action_execution",
        "production_exposure",
    ):
        _assert(payload["resource_limits"][key] == 0, f"{key} must be zero")


def validate_counterfactual_planning(root: Path) -> None:
    validate_memory_consolidation_closeout(root)
    validate_required_files(root, AION192_REQUIRED_FILES)
    validate_aion192_implementation_payload(
        _load_json(root, "examples/cognitive-architecture/aion-192-counterfactual-planning.json")
    )
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-192.md",
            root / "services/brain-api/src/aion_brain/contracts/planning.py",
            root / "services/brain-api/src/aion_brain/planning/core.py",
            root / "services/brain-api/tests/test_cognitive_counterfactual_planning.py",
            root / "services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py",
        ),
    )
    contract_text = (root / "services/brain-api/src/aion_brain/contracts/planning.py").read_text()
    source_text = (root / "services/brain-api/src/aion_brain/planning/core.py").read_text()
    for contract in PLANNING_REQUIRED_CONTRACTS:
        _assert(f"class {contract}" in contract_text, f"missing planning contract: {contract}")
    for service in PLANNING_REQUIRED_SERVICES:
        _assert(f"class {service}" in source_text, f"missing planning service: {service}")
    for dimension in PLANNING_SCORE_DIMENSIONS:
        _assert(dimension in contract_text, f"missing planning score dimension: {dimension}")
    for marker in (
        "direct_action_execution",
        "background_planning_loop",
        "source_rewrite",
        "git_mutation",
    ):
        _assert(marker in contract_text, f"missing runtime boundary marker: {marker}")
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-192.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Role Comparison",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Algorithm",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-192 task doc missing {section}")
    for term in (
        AION191_AUTHORIZATION_ID,
        AION192_CANDIDATE_ID,
        AION192_SCOPE,
        AION193_TASK_ID,
        AION193_EVALUATION_ID,
    ):
        _assert(term in task_doc, f"AION-192 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    aion193_closeout_exists = _aion193_closeout_record_exists(root)
    _assert(
        program["program_state"]
        in {
            "counterfactual_planning_implemented_pending_evaluation",
            "counterfactual_planning_evaluated_information_acquisition_authorized",
            "information_acquisition_implemented_pending_evaluation",
            "information_acquisition_evaluated_continual_learning_authorized",
            "continual_learning_implemented_pending_integrated_evaluation",
            AION197_PROGRAM_STATE,
        },
        "AION-192 program state mismatch",
    )
    implementation = _find_record(program["records"], "implementation_task", AION192_TASK_ID)
    _assert(implementation["authorization_id"] == AION191_AUTHORIZATION_ID, "AION-192 auth")
    _assert(implementation["candidate_id"] == AION192_CANDIDATE_ID, "AION-192 candidate")
    _assert(implementation["scope"] == AION192_SCOPE, "AION-192 scope")
    _assert(implementation["closeout_task"] == AION193_TASK_ID, "AION-192 closeout")
    _assert(implementation["evaluation_id"] == AION193_EVALUATION_ID, "AION-192 eval")
    _assert(implementation["runtime_effect"] is False, "AION-192 runtime effect")
    _assert(implementation["forbidden_side_effects"] == 0, "AION-192 side effects")
    _assert(
        implementation["task_state"]
        == (
            "merged_evaluated_passed"
            if aion193_closeout_exists
            else "implemented_pending_aion_193_evaluation"
        ),
        "AION-192 task state",
    )
    if aion193_closeout_exists:
        _assert(implementation["pr"] == AION192_PR, "AION-192 PR")
        _assert(implementation["merge_commit"] == AION192_MERGE_COMMIT, "AION-192 merge")
    active = _find_record(authorization["records"], "authorization_id", AION191_AUTHORIZATION_ID)
    _assert(
        active["authorization_active"] is not aion193_closeout_exists,
        "AION-191 authorization active state mismatch",
    )
    _assert(
        active["authorization_consumed"] is aion193_closeout_exists,
        "AION-191 consumed state mismatch",
    )
    _assert(
        active["authorization_expired"] is aion193_closeout_exists,
        "AION-191 expiry state mismatch",
    )
    _assert(active["authorization_reusable"] is False, "AION-191 must remain non-reusable")
    if aion193_closeout_exists:
        _assert(
            active["implementation_state"] == "merged_evaluated_passed",
            "AION-191 implementation state must be closed after AION-193",
        )
        _assert(
            active["authorization_closed_by_task"] == AION193_TASK_ID,
            "AION-191 closeout task mismatch",
        )
    else:
        _assert(
            active["implementation_state"] == "implemented_pending_aion_193_evaluation",
            "AION-191 implementation state must await AION-193",
        )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/planning.py").exists(),
        "AION-192 must not add a planning API route",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/counterfactual_planning.py").exists(),
        "AION-192 must not add a counterfactual-planning API route",
    )
    for path in (
        root / "services/brain-api/src/aion_brain/kernel/container.py",
        root / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = path.read_text()
        _assert("StrategicPlanner" not in text, "AION-192 must not register StrategicPlanner")
        _assert(
            "aion_brain.planning.core" not in text,
            "AION-192 must not add kernel planning registration",
        )
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        _assert(marker not in source_text, f"prohibited planning source marker: {marker}")


def validate_counterfactual_planning_no_go(root: Path) -> None:
    validate_counterfactual_planning(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion192_path_allowed = _aion192_path_allowed(relative)
        aion193_path_allowed = _aion193_closeout_record_exists(root) and _aion193_path_allowed(
            relative
        )
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION192_PROHIBITED_PREFIXES),
            f"prohibited AION-192 path changed: {relative}",
        )
        _assert(
            aion192_path_allowed
            or aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-192 path changed: {relative}",
        )


def validate_aion193_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-counterfactual-planning-evaluation/v1",
        "bad AION-193 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-193 program id")
    _assert(payload["task_id"] == AION193_TASK_ID, "bad AION-193 task id")
    _assert(payload["evaluation_id"] == AION193_EVALUATION_ID, "bad AION-193 evaluation")
    _assert(payload["evaluated_task"] == AION192_TASK_ID, "bad AION-193 evaluated task")
    _assert(payload["closed_authorization_id"] == AION191_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["implementation_pr"] == AION192_PR, "bad AION-192 PR")
    _assert(payload["implementation_merge_commit"] == AION192_MERGE_COMMIT, "bad AION-192 merge")
    _assert(payload["result"] == "PASS", "AION-193 evaluation must pass")
    _assert(
        payload["decision"]
        == "COUNTERFACTUAL_PLANNING_EVALUATION_PASS_AUTHORIZE_ACTIVE_INFORMATION_ACQUISITION",
        "bad AION-193 decision",
    )
    metrics = payload["hard_pass_conditions"]
    _assert(
        metrics["synthetic_goal_completion_plan_success_rate"] >= 0.8,
        "planning success below threshold",
    )
    _assert(metrics["policy_violation_count"] == 0, "policy violations must be zero")
    _assert(metrics["budget_overrun_count"] == 0, "budget overruns must be zero")
    _assert(
        metrics["irreversible_unsafe_plan_selection_count"] == 0,
        "irreversible unsafe selections must be zero",
    )
    _assert(metrics["deterministic_plan_replay_rate"] == 1.0, "deterministic replay")
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
    for key in (
        "goal_decomposition",
        "cross_level_consistency",
        "world_model_use",
        "counterfactual_comparison",
        "resource_constraints",
        "risk_constraints",
        "reversibility",
        "replanning_after_changed_observations",
        "no_action_execution",
        "deterministic_replay",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "external_action_dispatch",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "git_operations",
        "deployment_enabled",
        "model_weights_changed",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")
    _assert(payload["new_authorization_id"] == AION193_AUTHORIZATION_ID, "bad new auth")
    _assert(payload["authorized_task"] == AION194_TASK_ID, "bad authorized task")
    _assert(payload["next_task"] == AION194_TASK_ID, "bad next task")


def validate_aion193_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-active-information-acquisition-authorization/v1",
        "bad AION-193 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-193 authorization program")
    _assert(payload["authorization_id"] == AION193_AUTHORIZATION_ID, "bad AION-193 auth")
    _assert(payload["parent_evaluation_id"] == AION193_EVALUATION_ID, "bad parent eval")
    _assert(payload["parent_task"] == AION193_TASK_ID, "bad parent task")
    _assert(payload["parent_commit"] == AION192_MERGE_COMMIT, "bad parent commit")
    _assert(payload["parent_pr"] == AION192_PR, "bad parent PR")
    _assert(payload["authorized_task"] == AION194_TASK_ID, "bad AION-194 task")
    _assert(payload["candidate_id"] == AION194_CANDIDATE_ID, "bad AION-194 candidate")
    _assert(payload["scope"] == AION194_SCOPE, "bad AION-194 scope")
    _assert(payload["authorization_active"] is True, "AION-193 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-193 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-193 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-193 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == AION195_TASK_ID, "bad formal closeout")
    _assert(
        payload["required_decision"]
        == "What information would reduce decision-relevant uncertainty enough to justify its cost and risk?",
        "bad required decision",
    )
    for contract in INFORMATION_ACQUISITION_REQUIRED_CONTRACTS:
        _assert(
            contract in payload["required_contracts"],
            f"missing information-acquisition contract: {contract}",
        )
    for service in INFORMATION_ACQUISITION_REQUIRED_SERVICES:
        _assert(
            service in payload["required_services"],
            f"missing information-acquisition service: {service}",
        )
    for candidate in INFORMATION_ACQUISITION_ALLOWED_CANDIDATES:
        _assert(
            candidate in payload["allowed_candidate_types"],
            f"missing candidate type: {candidate}",
        )
    for behavior in INFORMATION_ACQUISITION_PROHIBITED_BEHAVIORS:
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "background_loops",
        "git_operations",
        "source_rewrite_operations",
        "action_execution",
        "unauthorized_information_acquisition",
        "production_exposure",
    ):
        _assert(payload["resource_limits"][key] == 0, f"{key} must be zero")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")


def validate_counterfactual_planning_closeout(root: Path) -> None:
    validate_counterfactual_planning(root)
    validate_required_files(root, AION193_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-193.md",
            root
            / "services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-193-counterfactual-planning-evaluation.json",
    )
    acquisition_authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-193-information-acquisition-authorization.json",
    )
    validate_aion193_evaluation_payload(evaluation)
    validate_aion193_authorization_payload(acquisition_authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-193.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization ID",
        "## Exact Scope",
        "## Role Comparison",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-193 task doc missing {section}")
    for term in (
        AION193_EVALUATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
        AION194_TASK_ID,
        AION194_SCOPE,
    ):
        _assert(term in task_doc, f"AION-193 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout = _find_evaluation_record(
        program["records"],
        AION193_TASK_ID,
        AION193_EVALUATION_ID,
    )
    _assert(closeout["result"] == "PASS", "AION-193 ledger result must pass")
    aion194_implemented = _aion194_implementation_record_exists(root)
    aion195_closeout_exists = _aion195_closeout_record_exists(root)
    aion196_implemented = _aion196_implementation_record_exists(root)
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    _assert(
        program["active_cognitive_implementation_authorization"]
        == (
            None
            if aion197_closeout_exists
            else AION195_AUTHORIZATION_ID
            if aion195_closeout_exists
            else AION193_AUTHORIZATION_ID
        ),
        "AION-193 authorization chain mismatch",
    )
    _assert(
        program["program_state"]
        == (
            AION197_PROGRAM_STATE
            if aion197_closeout_exists
            else "continual_learning_implemented_pending_integrated_evaluation"
            if aion196_implemented
            else "information_acquisition_evaluated_continual_learning_authorized"
            if aion195_closeout_exists
            else (
                "information_acquisition_implemented_pending_evaluation"
                if aion194_implemented
                else "counterfactual_planning_evaluated_information_acquisition_authorized"
            )
        ),
        "AION-193 program state mismatch",
    )
    implementation = _find_record(program["records"], "implementation_task", AION192_TASK_ID)
    _assert(implementation["pr"] == AION192_PR, "AION-192 PR")
    _assert(implementation["merge_commit"] == AION192_MERGE_COMMIT, "AION-192 merge")
    _assert(implementation["task_state"] == "merged_evaluated_passed", "AION-192 state")
    closed = _find_record(authorization["records"], "authorization_id", AION191_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-191 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-191 authorization must be consumed")
    _assert(closed["authorization_expired"] is True, "AION-191 authorization must be expired")
    _assert(closed["authorization_closeout_evaluation"] == AION193_EVALUATION_ID, "closeout eval")
    _assert(closed["implementation_pr"] == AION192_PR, "AION-192 closeout PR")
    _assert(closed["implementation_merge_commit"] == AION192_MERGE_COMMIT, "AION-192 closeout")
    active = _find_record(authorization["records"], "authorization_id", AION193_AUTHORIZATION_ID)
    _assert(
        active["authorization_active"] is not aion195_closeout_exists,
        "AION-193 authorization active state mismatch",
    )
    _assert(
        active["authorization_consumed"] is aion195_closeout_exists,
        "AION-193 consumed state mismatch",
    )
    _assert(
        active["authorization_expired"] is aion195_closeout_exists,
        "AION-193 expiry state mismatch",
    )
    if aion195_closeout_exists:
        _assert(
            active["record_kind"] == "implementation_authorization_closeout",
            "AION-193 authorization must be closed after AION-195",
        )
        _assert(active["authorization_closed_by_task"] == AION195_TASK_ID, "AION-193 closeout")
        _assert(
            active["authorization_closeout_evaluation"] == AION195_EVALUATION_ID,
            "AION-195 closeout eval",
        )
        _assert(active["implementation_pr"] == AION194_PR, "AION-194 closeout PR")
        _assert(active["implementation_merge_commit"] == AION194_MERGE_COMMIT, "AION-194 closeout")
    else:
        _assert(
            active["record_kind"] == "implementation_authorization",
            "AION-193 authorization must remain open before AION-195",
        )
    _assert(active["implementation_task"] == AION194_TASK_ID, "AION-194 authorization mismatch")
    _assert(active["scope"] == AION194_SCOPE, "AION-194 scope")
    if not aion194_implemented:
        information_paths = (
            root / "services/brain-api/src/aion_brain/contracts/information_acquisition.py",
            root / "services/brain-api/src/aion_brain/information_acquisition",
            root / "services/brain-api/src/aion_brain/api/information_acquisition.py",
        )
        for path in information_paths:
            _assert(not path.exists(), f"AION-193 must not implement AION-194 source: {path}")


def validate_counterfactual_planning_closeout_no_go(root: Path) -> None:
    validate_counterfactual_planning_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion193_path_allowed = _aion193_path_allowed(relative)
        aion194_path_allowed = _aion194_implementation_record_exists(root) and _aion194_path_allowed(
            relative
        )
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = _aion196_implementation_record_exists(root) and _aion196_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION193_PROHIBITED_PREFIXES),
            f"prohibited AION-193 path changed: {relative}",
        )
        _assert(
            aion193_path_allowed
            or aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed,
            f"unexpected AION-193 path changed: {relative}",
        )


def validate_aion194_implementation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-active-information-acquisition-implementation/v1",
        "bad AION-194 implementation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-194 program id")
    _assert(payload["task_id"] == AION194_TASK_ID, "bad AION-194 task id")
    _assert(payload["authorization_id"] == AION193_AUTHORIZATION_ID, "bad AION-194 auth")
    _assert(payload["candidate_id"] == AION194_CANDIDATE_ID, "bad AION-194 candidate")
    _assert(payload["scope"] == AION194_SCOPE, "bad AION-194 scope")
    _assert(payload["closeout_task"] == AION195_TASK_ID, "bad AION-194 closeout")
    _assert(payload["next_task"] == AION195_TASK_ID, "bad AION-194 next task")
    _assert(
        payload["implementation_state"] == "implemented_pending_aion_195_evaluation",
        "bad AION-194 implementation state",
    )
    _assert(
        payload["required_decision"]
        == "What information would reduce decision-relevant uncertainty enough to justify its cost and risk?",
        "bad AION-194 required decision",
    )
    for contract in INFORMATION_ACQUISITION_REQUIRED_CONTRACTS:
        _assert(
            contract in payload["contracts"],
            f"missing information-acquisition contract: {contract}",
        )
    for service in INFORMATION_ACQUISITION_REQUIRED_SERVICES:
        _assert(
            service in payload["services"],
            f"missing information-acquisition service: {service}",
        )
    for candidate in INFORMATION_ACQUISITION_ALLOWED_CANDIDATES:
        _assert(candidate in payload["allowed_candidate_types"], f"missing {candidate}")
    for key in (
        "knowledge_gap_detection",
        "observation_candidate_generation",
        "expected_information_gain_estimation",
        "acquisition_cost_evaluation",
        "acquisition_risk_evaluation",
        "clarification_policy",
        "stopping_policy",
        "permission_bound_planning",
        "proposal_only_information_asks",
        "deterministic_replay_hashes",
    ):
        _assert(payload["capabilities"][key] is True, f"{key} must be true")
    for behavior in INFORMATION_ACQUISITION_PROHIBITED_BEHAVIORS:
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    for behavior in (
        "source rewrite",
        "git mutation",
        "model-weight update",
        "background acquisition loop",
    ):
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    metrics = payload["benchmark_requirements"]
    for key in (
        "uncertainty_detection_required",
        "expected_information_gain_required",
        "candidate_ranking_deterministic",
        "permission_enforcement_required",
        "stopping_decision_required",
    ):
        _assert(metrics[key] is True, f"{key} must be true")
    _assert(
        metrics["unauthorized_information_acquisition_count"] == 0,
        "unauthorized acquisition must be zero",
    )
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
    runtime = payload["runtime_boundaries"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "arbitrary_location_access",
        "tool_execution",
        "information_acquired",
        "deployment_enabled",
        "production_exposure",
        "model_weights_changed",
    ):
        _assert(runtime[key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_calls_by_default",
        "model_weight_training",
        "source_rewrite_operations",
        "git_operations",
        "unauthorized_information_acquisition",
        "forbidden_side_effects",
    ):
        _assert(runtime[key] == 0, f"{key} must be zero")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "background_loops",
        "git_operations",
        "source_rewrite_operations",
        "action_execution",
        "unauthorized_information_acquisition",
        "production_exposure",
    ):
        _assert(payload["resource_limits"][key] == 0, f"{key} must be zero")


def validate_information_acquisition(root: Path) -> None:
    validate_counterfactual_planning_closeout(root)
    validate_required_files(root, AION194_REQUIRED_FILES)
    validate_aion194_implementation_payload(
        _load_json(root, "examples/cognitive-architecture/aion-194-information-acquisition.json")
    )
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-194.md",
            root / "services/brain-api/src/aion_brain/contracts/information_acquisition.py",
            root / "services/brain-api/src/aion_brain/information_acquisition",
            root / "services/brain-api/tests/test_cognitive_information_acquisition.py",
            root / "services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py",
        ),
    )
    contract_text = (
        root / "services/brain-api/src/aion_brain/contracts/information_acquisition.py"
    ).read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/information_acquisition").glob(
            "*.py"
        )
    )
    for contract in INFORMATION_ACQUISITION_REQUIRED_CONTRACTS:
        _assert(
            f"class {contract}" in contract_text,
            f"missing information-acquisition contract: {contract}",
        )
    for service in INFORMATION_ACQUISITION_REQUIRED_SERVICES:
        _assert(f"class {service}" in source_text, f"missing acquisition service: {service}")
    for marker in (
        "arbitrary_location_access",
        "information_acquired",
        "unauthorized_information_acquisition",
        "tool_execution",
    ):
        _assert(marker in contract_text, f"missing acquisition runtime marker: {marker}")
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-194.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Role Comparison",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Algorithm",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-194 task doc missing {section}")
    for term in (
        AION193_AUTHORIZATION_ID,
        AION194_CANDIDATE_ID,
        AION194_SCOPE,
        AION195_TASK_ID,
        AION195_EVALUATION_ID,
    ):
        _assert(term in task_doc, f"AION-194 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    aion195_closeout_exists = _aion195_closeout_record_exists(root)
    aion196_implemented = _aion196_implementation_record_exists(root)
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    _assert(
        program["program_state"]
        == (
            AION197_PROGRAM_STATE
            if aion197_closeout_exists
            else "continual_learning_implemented_pending_integrated_evaluation"
            if aion196_implemented
            else "information_acquisition_evaluated_continual_learning_authorized"
            if aion195_closeout_exists
            else "information_acquisition_implemented_pending_evaluation"
        ),
        "AION-194 program state mismatch",
    )
    implementation = _find_record(program["records"], "implementation_task", AION194_TASK_ID)
    _assert(implementation["authorization_id"] == AION193_AUTHORIZATION_ID, "AION-194 auth")
    _assert(implementation["candidate_id"] == AION194_CANDIDATE_ID, "AION-194 candidate")
    _assert(implementation["scope"] == AION194_SCOPE, "AION-194 scope")
    _assert(implementation["closeout_task"] == AION195_TASK_ID, "AION-194 closeout")
    _assert(implementation["evaluation_id"] == AION195_EVALUATION_ID, "AION-194 eval")
    _assert(implementation["runtime_effect"] is False, "AION-194 runtime effect")
    _assert(implementation["forbidden_side_effects"] == 0, "AION-194 side effects")
    _assert(
        implementation["unauthorized_information_acquisition_count"] == 0,
        "AION-194 unauthorized acquisition",
    )
    _assert(
        implementation["task_state"]
        == (
            "merged_evaluated_passed"
            if aion195_closeout_exists
            else "implemented_pending_aion_195_evaluation"
        ),
        "AION-194 task state",
    )
    if aion195_closeout_exists:
        _assert(implementation["pr"] == AION194_PR, "AION-194 PR")
        _assert(implementation["merge_commit"] == AION194_MERGE_COMMIT, "AION-194 merge")
    active = _find_record(authorization["records"], "authorization_id", AION193_AUTHORIZATION_ID)
    _assert(
        active["authorization_active"] is not aion195_closeout_exists,
        "AION-193 authorization active state mismatch",
    )
    _assert(
        active["authorization_consumed"] is aion195_closeout_exists,
        "AION-193 consumed state mismatch",
    )
    _assert(
        active["authorization_expired"] is aion195_closeout_exists,
        "AION-193 expiry state mismatch",
    )
    _assert(active["authorization_reusable"] is False, "AION-193 must remain non-reusable")
    if aion195_closeout_exists:
        _assert(
            active["implementation_state"] == "merged_evaluated_passed",
            "AION-193 implementation state must be closed after AION-195",
        )
        _assert(
            active["authorization_closed_by_task"] == AION195_TASK_ID,
            "AION-193 closeout task mismatch",
        )
        _assert(
            active["authorization_closeout_evaluation"] == AION195_EVALUATION_ID,
            "AION-193 closeout evaluation mismatch",
        )
        _assert(active["implementation_pr"] == AION194_PR, "AION-194 closeout PR")
        _assert(
            active["implementation_merge_commit"] == AION194_MERGE_COMMIT,
            "AION-194 closeout merge",
        )
    else:
        _assert(
            active["implementation_state"] == "implemented_pending_aion_195_evaluation",
            "AION-193 implementation state must await AION-195",
        )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/information_acquisition.py").exists(),
        "AION-194 must not add an information-acquisition API route",
    )
    for path in (
        root / "services/brain-api/src/aion_brain/kernel/container.py",
        root / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = path.read_text()
        _assert(
            "InformationAcquisitionPlanner" not in text,
            "AION-194 must not register InformationAcquisitionPlanner",
        )
        _assert(
            "aion_brain.information_acquisition" not in text,
            "AION-194 must not add kernel information-acquisition registration",
        )
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        _assert(marker not in source_text, f"prohibited acquisition source marker: {marker}")


def validate_information_acquisition_no_go(root: Path) -> None:
    validate_information_acquisition(root)
    validate_no_go(root)
    changed = _changed_files(root)
    aion196_implemented = _aion196_implementation_record_exists(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion194_path_allowed = _aion194_path_allowed(relative)
        aion195_path_allowed = _aion195_closeout_record_exists(root) and _aion195_path_allowed(
            relative
        )
        aion196_path_allowed = aion196_implemented and _aion196_path_allowed(relative)
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion194_path_allowed
            or aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION194_PROHIBITED_PREFIXES),
            f"prohibited AION-194 path changed: {relative}",
        )
        _assert(
            aion194_path_allowed or aion195_path_allowed or aion196_path_allowed,
            f"unexpected AION-194 path changed: {relative}",
        )


def validate_aion195_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-information-acquisition-evaluation/v1",
        "bad AION-195 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-195 program id")
    _assert(payload["task_id"] == AION195_TASK_ID, "bad AION-195 task id")
    _assert(payload["evaluation_id"] == AION195_EVALUATION_ID, "bad AION-195 evaluation")
    _assert(payload["evaluated_task"] == AION194_TASK_ID, "bad AION-195 evaluated task")
    _assert(payload["closed_authorization_id"] == AION193_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["implementation_pr"] == AION194_PR, "bad AION-194 PR")
    _assert(payload["implementation_merge_commit"] == AION194_MERGE_COMMIT, "bad AION-194 merge")
    _assert(payload["result"] == "PASS", "AION-195 evaluation must pass")
    _assert(
        payload["decision"]
        == "INFORMATION_ACQUISITION_EVALUATION_PASS_AUTHORIZE_GOVERNED_CONTINUAL_LEARNING",
        "bad AION-195 decision",
    )
    metrics = payload["hard_pass_conditions"]
    _assert(metrics["uncertainty_detection_rate"] == 1.0, "uncertainty detection")
    _assert(
        metrics["expected_information_gain_positive_rate"] == 1.0,
        "expected information gain",
    )
    _assert(
        metrics["candidate_ranking_deterministic_rate"] == 1.0,
        "candidate ranking determinism",
    )
    _assert(
        metrics["cost_risk_constraint_violation_count"] == 0,
        "cost-risk violations",
    )
    _assert(metrics["clarification_quality_rate"] == 1.0, "clarification quality")
    _assert(metrics["stopping_decision_accuracy"] == 1.0, "stopping accuracy")
    _assert(
        metrics["permission_enforcement_violation_count"] == 0,
        "permission violations",
    )
    _assert(
        metrics["unauthorized_information_acquisition_count"] == 0,
        "unauthorized acquisition",
    )
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects")
    for key in (
        "uncertainty_detection",
        "expected_information_gain",
        "candidate_ranking",
        "cost_and_risk",
        "clarification_quality",
        "stopping_decisions",
        "permission_enforcement",
        "no_unauthorized_acquisition",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "information_acquired",
        "tool_execution",
        "external_action_dispatch",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "git_operations",
        "deployment_enabled",
        "model_weights_changed",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")
    _assert(payload["new_authorization_id"] == AION195_AUTHORIZATION_ID, "bad new auth")
    _assert(payload["authorized_task"] == AION196_TASK_ID, "bad authorized task")
    _assert(payload["next_task"] == AION196_TASK_ID, "bad next task")


def validate_aion195_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-governed-continual-learning-authorization/v1",
        "bad AION-195 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-195 authorization program")
    _assert(payload["authorization_id"] == AION195_AUTHORIZATION_ID, "bad AION-195 auth")
    _assert(payload["parent_evaluation_id"] == AION195_EVALUATION_ID, "bad parent eval")
    _assert(payload["parent_task"] == AION195_TASK_ID, "bad parent task")
    _assert(payload["parent_commit"] == AION194_MERGE_COMMIT, "bad parent commit")
    _assert(payload["parent_pr"] == AION194_PR, "bad parent PR")
    _assert(payload["authorized_task"] == AION196_TASK_ID, "bad AION-196 task")
    _assert(payload["candidate_id"] == AION196_CANDIDATE_ID, "bad AION-196 candidate")
    _assert(payload["scope"] == AION196_SCOPE, "bad AION-196 scope")
    _assert(payload["authorization_active"] is True, "AION-195 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-195 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-195 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-195 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == AION197_TASK_ID, "bad formal closeout")
    for contract in CONTINUAL_LEARNING_REQUIRED_CONTRACTS:
        _assert(
            contract in payload["required_contracts"],
            f"missing continual-learning contract: {contract}",
        )
    for service in CONTINUAL_LEARNING_REQUIRED_SERVICES:
        _assert(
            service in payload["required_services"],
            f"missing continual-learning service: {service}",
        )
    for level in CONTINUAL_LEARNING_LEVELS:
        _assert(level in payload["learning_levels"], f"missing learning level: {level}")
    for requirement in CONTINUAL_LEARNING_REQUIREMENTS:
        _assert(requirement in payload["requirements"], f"missing requirement: {requirement}")
    for behavior in CONTINUAL_LEARNING_PROHIBITED_BEHAVIORS:
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "background_loops",
        "git_operations",
        "source_rewrite_operations",
        "action_execution",
        "automatic_promotion",
        "self_approval",
        "unauthorized_promotion",
        "production_exposure",
    ):
        _assert(payload["resource_limits"][key] == 0, f"{key} must be zero")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")


def validate_information_acquisition_closeout(root: Path) -> None:
    validate_information_acquisition(root)
    validate_required_files(root, AION195_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-195.md",
            root
            / "services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json",
    )
    continual_authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-195-continual-learning-authorization.json",
    )
    validate_aion195_evaluation_payload(evaluation)
    validate_aion195_authorization_payload(continual_authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-195.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization ID",
        "## Exact Scope",
        "## Role Comparison",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-195 task doc missing {section}")
    for term in (
        AION195_EVALUATION_ID,
        AION193_AUTHORIZATION_ID,
        AION195_AUTHORIZATION_ID,
        AION196_TASK_ID,
        AION196_SCOPE,
    ):
        _assert(term in task_doc, f"AION-195 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    closeout = _find_evaluation_record(
        program["records"],
        AION195_TASK_ID,
        AION195_EVALUATION_ID,
    )
    _assert(closeout["result"] == "PASS", "AION-195 ledger result must pass")
    if aion197_closeout_exists:
        _assert(
            program["active_cognitive_implementation_authorization"] is None,
            "AION-195 authorization must be closed after AION-197",
        )
    else:
        _assert(
            program["active_cognitive_implementation_authorization"] == AION195_AUTHORIZATION_ID,
            "AION-195 authorization must be active",
        )
    _assert(
        program["program_state"]
        in {
            "information_acquisition_evaluated_continual_learning_authorized",
            "continual_learning_implemented_pending_integrated_evaluation",
            AION197_PROGRAM_STATE,
        },
        "AION-195 program state mismatch",
    )
    implementation = _find_record(program["records"], "implementation_task", AION194_TASK_ID)
    _assert(implementation["pr"] == AION194_PR, "AION-194 PR")
    _assert(implementation["merge_commit"] == AION194_MERGE_COMMIT, "AION-194 merge")
    _assert(implementation["task_state"] == "merged_evaluated_passed", "AION-194 state")
    closed = _find_record(authorization["records"], "authorization_id", AION193_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-193 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-193 authorization must be consumed")
    _assert(closed["authorization_expired"] is True, "AION-193 authorization must be expired")
    _assert(closed["authorization_closeout_evaluation"] == AION195_EVALUATION_ID, "closeout eval")
    _assert(closed["implementation_pr"] == AION194_PR, "AION-194 closeout PR")
    _assert(closed["implementation_merge_commit"] == AION194_MERGE_COMMIT, "AION-194 closeout")
    active = _find_record(authorization["records"], "authorization_id", AION195_AUTHORIZATION_ID)
    if aion197_closeout_exists:
        _assert(active["authorization_active"] is False, "AION-195 authorization must be closed")
        _assert(active["authorization_consumed"] is True, "AION-195 auth must be consumed")
        _assert(active["authorization_expired"] is True, "AION-195 auth must be expired")
        _assert(active["authorization_closed_by_task"] == AION197_TASK_ID, "AION-197 closeout")
        _assert(
            active["authorization_closeout_evaluation"] == AION197_EVALUATION_ID,
            "AION-197 closeout evaluation",
        )
    else:
        _assert(active["authorization_active"] is True, "AION-195 authorization must be active")
    _assert(active["implementation_task"] == AION196_TASK_ID, "AION-196 authorization mismatch")
    _assert(active["scope"] == AION196_SCOPE, "AION-196 scope")
    _assert(
        set(CONTINUAL_LEARNING_REQUIRED_CONTRACTS).issubset(active["required_contracts"]),
        "AION-196 required contracts missing",
    )
    _assert(
        set(CONTINUAL_LEARNING_REQUIRED_SERVICES).issubset(active["required_services"]),
        "AION-196 required services missing",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/continual_learning.py").exists(),
        "AION-195 must not add a continual-learning API route",
    )
    for path in (
        root / "services/brain-api/src/aion_brain/kernel/container.py",
        root / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = path.read_text()
        _assert(
            "ExperienceReplayService" not in text,
            "AION-195 must not register continual-learning services",
        )
        _assert(
            "aion_brain.continual_learning" not in text,
            "AION-195 must not add kernel continual-learning registration",
        )


def validate_information_acquisition_closeout_no_go(root: Path) -> None:
    validate_information_acquisition_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    aion196_implemented = _aion196_implementation_record_exists(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion195_path_allowed = _aion195_path_allowed(relative)
        aion196_path_allowed = aion196_implemented and _aion196_path_allowed(relative)
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion195_path_allowed
            or aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION195_PROHIBITED_PREFIXES),
            f"prohibited AION-195 path changed: {relative}",
        )
        _assert(
            aion195_path_allowed or aion196_path_allowed,
            f"unexpected AION-195 path changed: {relative}",
        )


def validate_aion196_implementation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-governed-continual-learning-implementation/v1",
        "bad AION-196 implementation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-196 program")
    _assert(payload["task_id"] == AION196_TASK_ID, "bad AION-196 task")
    _assert(payload["authorization_id"] == AION195_AUTHORIZATION_ID, "bad AION-196 auth")
    _assert(payload["candidate_id"] == AION196_CANDIDATE_ID, "bad AION-196 candidate")
    _assert(payload["scope"] == AION196_SCOPE, "bad AION-196 scope")
    _assert(payload["closeout_task"] == AION197_TASK_ID, "bad AION-196 closeout")
    _assert(payload["next_task"] == AION197_TASK_ID, "bad AION-196 next task")
    _assert(
        payload["implementation_branch"] == "phase/cognitive-governed-continual-learning",
        "bad AION-196 branch",
    )
    _assert(
        payload["implementation_state"] == "implemented_pending_aion_197_evaluation",
        "bad AION-196 implementation state",
    )
    for contract in CONTINUAL_LEARNING_REQUIRED_CONTRACTS:
        _assert(contract in payload["contracts"], f"missing AION-196 contract: {contract}")
    for service in CONTINUAL_LEARNING_REQUIRED_SERVICES:
        _assert(service in payload["services"], f"missing AION-196 service: {service}")
    for level in CONTINUAL_LEARNING_LEVELS:
        _assert(level in payload["learning_levels"], f"missing AION-196 level: {level}")
    for behavior in CONTINUAL_LEARNING_PROHIBITED_BEHAVIORS:
        _assert(behavior in payload["prohibited_behaviors"], f"missing prohibition: {behavior}")
    for key in (
        "deterministic_replay_rate",
        "candidate_isolation_rate",
        "protected_holdout_score",
        "rollback_available_rate",
    ):
        _assert(payload["metrics"][key] == 1.0, f"{key} must be complete")
    for key in (
        "catastrophic_forgetting_rate",
        "baseline_regression_rate",
    ):
        _assert(payload["metrics"][key] == 0.0, f"{key} must be zero")
    for key in (
        "automatic_promotion_count",
        "self_approval_count",
        "unauthorized_promotion_count",
        "holdout_leakage_count",
        "model_weight_training",
        "forbidden_side_effects",
    ):
        _assert(payload["metrics"][key] == 0, f"{key} must be zero")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "background_loops",
        "git_operations",
        "source_rewrite_operations",
        "automatic_promotion",
        "self_approval",
        "unauthorized_promotion",
        "holdout_leakage",
        "production_exposure",
    ):
        _assert(payload["resource_limits"][key] == 0, f"{key} must be zero")
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "model_weights_changed",
        "production_exposure",
    ):
        _assert(payload["runtime_boundaries"][key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "model_weight_training",
        "source_rewrite_operations",
        "git_operations",
        "holdout_leakage",
        "forbidden_side_effects",
    ):
        _assert(payload["runtime_boundaries"][key] == 0, f"{key} must be zero")
    _assert(payload["model_weight_training"] == 0, "model weight training must be zero")
    _assert(payload["rollback_available"] is True, "rollback must be available")
    _assert(payload["approval_bound_promotion"] is True, "promotion must require approval")


def validate_continual_learning(root: Path) -> None:
    validate_information_acquisition_closeout(root)
    validate_required_files(root, AION196_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-196.md",
            root / "services/brain-api/tests/test_cognitive_continual_learning.py",
            root / "services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py",
        ),
    )
    payload = _load_json(root, "examples/cognitive-architecture/aion-196-continual-learning.json")
    validate_aion196_implementation_payload(payload)
    contract_text = (root / "services/brain-api/src/aion_brain/contracts/continual_learning.py").read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/continual_learning").glob("*.py")
    )
    for contract in CONTINUAL_LEARNING_REQUIRED_CONTRACTS:
        _assert(f"class {contract}" in contract_text, f"missing AION-196 contract: {contract}")
    for service in CONTINUAL_LEARNING_REQUIRED_SERVICES:
        _assert(f"class {service}" in source_text, f"missing AION-196 service: {service}")
    for marker in (
        "protected_holdout",
        "deterministic_replay_hash",
        "candidate_isolated",
        "catastrophic_forgetting_detected",
        "promotion_requires_approval",
        "rollback_available",
        "model_weight_training",
        "self_approval_count",
        "unauthorized_promotion_count",
        "holdout_leakage_count",
    ):
        _assert(marker in contract_text, f"missing AION-196 boundary marker: {marker}")
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-196.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Role Comparison",
        "## Source Boundaries",
        "## Learning Levels",
        "## Required Contracts",
        "## Required Services",
        "## Algorithm",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-196 task doc missing {section}")
    for term in (
        AION195_AUTHORIZATION_ID,
        AION196_CANDIDATE_ID,
        AION196_SCOPE,
        AION197_TASK_ID,
        AION197_EVALUATION_ID,
    ):
        _assert(term in task_doc, f"AION-196 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    aion197_closeout_exists = _aion197_closeout_record_exists(root)
    if aion197_closeout_exists:
        _assert(
            program["active_cognitive_implementation_authorization"] is None,
            "AION-196 authorization must be closed after AION-197",
        )
    else:
        _assert(
            program["active_cognitive_implementation_authorization"] == AION195_AUTHORIZATION_ID,
            "AION-196 authorization must remain active",
        )
    _assert(
        program["program_state"]
        in {
            "continual_learning_implemented_pending_integrated_evaluation",
            AION197_PROGRAM_STATE,
        },
        "AION-196 program state mismatch",
    )
    closeout = _find_evaluation_record(
        program["records"],
        AION195_TASK_ID,
        AION195_EVALUATION_ID,
    )
    _assert(closeout["result"] == "PASS", "AION-195 closeout must remain passed")
    implementation = _find_record(program["records"], "implementation_task", AION196_TASK_ID)
    _assert(implementation["authorization_id"] == AION195_AUTHORIZATION_ID, "AION-196 auth")
    _assert(implementation["candidate_id"] == AION196_CANDIDATE_ID, "AION-196 candidate")
    _assert(implementation["scope"] == AION196_SCOPE, "AION-196 scope")
    _assert(implementation["closeout_task"] == AION197_TASK_ID, "AION-196 closeout")
    _assert(implementation["evaluation_id"] == AION197_EVALUATION_ID, "AION-196 eval")
    _assert(implementation["runtime_effect"] is False, "AION-196 runtime effect")
    _assert(implementation["forbidden_side_effects"] == 0, "AION-196 side effects")
    _assert(implementation["model_weight_training"] == 0, "AION-196 model weights")
    _assert(implementation["self_approval_count"] == 0, "AION-196 self approval")
    _assert(implementation["unauthorized_promotion_count"] == 0, "AION-196 promotion")
    _assert(
        implementation["task_state"]
        == (
            "merged_evaluated_passed"
            if aion197_closeout_exists
            else "implemented_pending_aion_197_evaluation"
        ),
        "AION-196 task state",
    )
    if aion197_closeout_exists:
        _assert(implementation["pr"] == AION196_PR, "AION-196 PR")
        _assert(implementation["merge_commit"] == AION196_MERGE_COMMIT, "AION-196 merge")
    active = _find_record(authorization["records"], "authorization_id", AION195_AUTHORIZATION_ID)
    if aion197_closeout_exists:
        _assert(active["authorization_active"] is False, "AION-195 authorization must be closed")
        _assert(active["authorization_consumed"] is True, "AION-195 auth must be consumed")
        _assert(active["authorization_expired"] is True, "AION-195 auth must be expired")
        _assert(active["authorization_closed_by_task"] == AION197_TASK_ID, "AION-197 closeout")
        _assert(active["implementation_state"] == "merged_evaluated_passed", "state")
        _assert(active["implementation_pr"] == AION196_PR, "AION-196 auth PR")
        _assert(
            active["implementation_merge_commit"] == AION196_MERGE_COMMIT,
            "AION-196 auth merge",
        )
    else:
        _assert(active["authorization_active"] is True, "AION-195 authorization must remain active")
        _assert(active["authorization_consumed"] is False, "AION-195 auth must not be consumed")
        _assert(active["authorization_expired"] is False, "AION-195 auth must not be expired")
        _assert(
            active["implementation_state"] == "implemented_pending_aion_197_evaluation",
            "state",
        )
    _assert(active["implementation_task"] == AION196_TASK_ID, "AION-196 auth task")
    _assert(active["formal_closeout_task"] == AION197_TASK_ID, "AION-197 closeout")
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/continual_learning.py").exists(),
        "AION-196 must not add a continual-learning API route",
    )
    for path in (
        root / "services/brain-api/src/aion_brain/kernel/container.py",
        root / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = path.read_text()
        _assert(
            "ExperienceReplayService" not in text,
            "AION-196 must not register continual-learning services",
        )
        _assert(
            "aion_brain.continual_learning" not in text,
            "AION-196 must not add kernel continual-learning registration",
        )


def validate_continual_learning_no_go(root: Path) -> None:
    validate_continual_learning(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion196_path_allowed = _aion196_path_allowed(relative)
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion196_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION196_PROHIBITED_PREFIXES),
            f"prohibited AION-196 path changed: {relative}",
        )
        _assert(aion196_path_allowed, f"unexpected AION-196 path changed: {relative}")


def validate_aion197_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-integrated-architecture-evaluation/v1",
        "bad AION-197 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-197 program")
    _assert(payload["task_id"] == AION197_TASK_ID, "bad AION-197 task")
    _assert(payload["evaluation_id"] == AION197_EVALUATION_ID, "bad AION-197 evaluation")
    _assert(payload["evaluated_task"] == AION196_TASK_ID, "bad AION-197 evaluated task")
    _assert(
        payload["closed_authorization_id"] == AION195_AUTHORIZATION_ID,
        "bad AION-197 closed authorization",
    )
    _assert(payload["implementation_pr"] == AION196_PR, "bad AION-196 PR")
    _assert(payload["implementation_merge_commit"] == AION196_MERGE_COMMIT, "bad AION-196 merge")
    _assert(payload["result"] == "PASS", "AION-197 evaluation must pass")
    _assert(payload["decision"] == AION197_DECISION, "bad AION-197 decision")
    environment = payload["synthetic_environment"]
    for factor in INTEGRATED_EVALUATION_ENVIRONMENT_FACTORS:
        _assert(factor in environment["factors"], f"missing environment factor: {factor}")
    for key in ("network_access", "production_data", "external_side_effects"):
        _assert(environment[key] is False, f"{key} must be false")
    _assert(
        tuple(payload["cycle_steps"]) == INTEGRATED_EVALUATION_CYCLE_STEPS,
        "AION-197 cycle steps mismatch",
    )
    for metric in INTEGRATED_EVALUATION_REQUIRED_METRICS:
        _assert(metric in payload["required_metrics"], f"missing required metric: {metric}")
    metrics = payload["hard_pass_conditions"]
    _assert(metrics["forbidden_side_effect_count"] == 0, "forbidden side effects")
    _assert(metrics["policy_violations"] == 0, "policy violations")
    _assert(metrics["unauthorized_promotions"] == 0, "unauthorized promotions")
    _assert(metrics["deterministic_replay_rate"] == 1.0, "deterministic replay")
    _assert(metrics["state_continuity_rate"] == 1.0, "state continuity")
    _assert(metrics["transition_accuracy"] >= 0.8, "transition accuracy")
    _assert(metrics["brier_score"] <= 0.2, "brier score")
    _assert(metrics["plan_success_rate"] >= 0.8, "plan success")
    _assert(metrics["critical_memory_retention_rate"] == 1.0, "critical memory retention")
    _assert(metrics["catastrophic_forgetting_rate"] <= 0.05, "catastrophic forgetting")
    for key in (
        "state_continuity",
        "belief_revision_accuracy",
        "contradiction_resolution",
        "uncertainty_calibration",
        "transition_prediction_accuracy",
        "workspace_fairness",
        "safety_preemption",
        "plan_success",
        "information_gain_per_cost",
        "memory_retention",
        "catastrophic_forgetting",
        "replay_determinism",
        "unauthorized_promotion_count",
        "forbidden_side_effect_count",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "deployment_enabled",
        "model_weights_changed",
        "automatic_promotion",
    ):
        _assert(side_effects[key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "git_operations",
        "model_weight_training",
        "forbidden_side_effects",
        "self_approval",
        "unauthorized_promotion",
    ):
        _assert(side_effects[key] == 0, f"{key} must be zero")
    closeout = payload["closeout"]
    _assert(closeout["cognitive_architecture_implemented"] is True, "architecture implemented")
    _assert(closeout["cognitive_architecture_integrated"] is True, "architecture integrated")
    _assert(closeout["runtime_enabled"] is False, "runtime must remain disabled")
    _assert(
        closeout["active_cognitive_implementation_authorization_count"] == 0,
        "active authorization count",
    )
    _assert(closeout["authorization_created"] is False, "AION-197 must not create auth")
    _assert(closeout["next_authorization_id"] is None, "AION-197 next auth must be empty")
    _assert(closeout["next_task"] == "AION-198", "AION-197 next task")


def validate_integrated_evaluation(root: Path) -> None:
    validate_continual_learning(root)
    validate_required_files(root, AION197_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-197.md",
            root / "services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py",
        ),
    )
    payload = _load_json(
        root,
        "examples/cognitive-architecture/aion-197-integrated-cognitive-evaluation.json",
    )
    validate_aion197_evaluation_payload(payload)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-197.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization ID",
        "## Exact Scope",
        "## Role Comparison",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-197 task doc missing {section}")
    for term in (
        AION197_EVALUATION_ID,
        AION195_AUTHORIZATION_ID,
        AION196_TASK_ID,
        AION196_MERGE_COMMIT,
        AION197_DECISION,
    ):
        _assert(term in task_doc, f"AION-197 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    _assert(
        program["active_cognitive_implementation_authorization"] is None,
        "AION-197 must close active program authorization",
    )
    _assert(
        authorization["active_cognitive_implementation_authorization"] is None,
        "AION-197 must close active authorization ledger entry",
    )
    _assert(program["active_cognitive_implementation_authorization_count"] == 0, "program count")
    _assert(
        authorization["active_cognitive_implementation_authorization_count"] == 0,
        "authorization count",
    )
    _assert(program["program_state"] == AION197_PROGRAM_STATE, "AION-197 program state")
    implementation = _find_record(program["records"], "implementation_task", AION196_TASK_ID)
    _assert(implementation["pr"] == AION196_PR, "AION-196 PR")
    _assert(implementation["merge_commit"] == AION196_MERGE_COMMIT, "AION-196 merge")
    _assert(implementation["task_state"] == "merged_evaluated_passed", "AION-196 state")
    evaluation = _find_evaluation_record(
        program["records"],
        AION197_TASK_ID,
        AION197_EVALUATION_ID,
    )
    _assert(evaluation["result"] == "PASS", "AION-197 result")
    _assert(evaluation["new_authorization_id"] is None, "AION-197 must not create auth")
    _assert(evaluation["authorized_task"] is None, "AION-197 must not authorize task")
    closed = _find_record(authorization["records"], "authorization_id", AION195_AUTHORIZATION_ID)
    _assert(closed["record_kind"] == "implementation_authorization_closeout", "AION-195 closed")
    _assert(closed["authorization_active"] is False, "AION-195 inactive")
    _assert(closed["authorization_consumed"] is True, "AION-195 consumed")
    _assert(closed["authorization_expired"] is True, "AION-195 expired")
    _assert(closed["authorization_closed_by_task"] == AION197_TASK_ID, "AION-197 closeout")
    _assert(
        closed["authorization_closeout_evaluation"] == AION197_EVALUATION_ID,
        "AION-197 closeout evaluation",
    )
    _assert(closed["implementation_pr"] == AION196_PR, "AION-196 closeout PR")
    _assert(closed["implementation_merge_commit"] == AION196_MERGE_COMMIT, "AION-196 closeout")
    _assert(closed["evaluation_result"] == "PASS", "AION-197 closeout result")
    _assert(
        _find_optional_record(program["records"], "authorization_id", "AION-198-CA-0008")
        is None,
        "AION-197 must not create AION-198 authorization",
    )
    _assert(
        _find_optional_record(authorization["records"], "authorization_id", "AION-198-CA-0008")
        is None,
        "AION-197 must not create AION-198 authorization ledger record",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/cognitive_runtime.py").exists(),
        "AION-197 must not add an integrated runtime API route",
    )
    for path in (
        root / "services/brain-api/src/aion_brain/kernel/container.py",
        root / "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = path.read_text()
        _assert("CognitiveShadowRuntime" not in text, "AION-197 must not register runtime")


def validate_integrated_evaluation_no_go(root: Path) -> None:
    validate_integrated_evaluation(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion197_path_allowed = _aion197_path_allowed(relative)
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion197_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION197_PROHIBITED_PREFIXES),
            f"prohibited AION-197 path changed: {relative}",
        )
        _assert(aion197_path_allowed, f"unexpected AION-197 path changed: {relative}")


def _aion184_path_allowed(relative: str) -> bool:
    return relative in AION184_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION184_ALLOWED_PREFIXES
    )


def _aion185_path_allowed(relative: str) -> bool:
    return relative in AION185_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION185_ALLOWED_PREFIXES
    )


def _aion186_path_allowed(relative: str) -> bool:
    return relative in AION186_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION186_ALLOWED_PREFIXES
    )


def _aion187_path_allowed(relative: str) -> bool:
    return relative in AION187_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION187_ALLOWED_PREFIXES
    )


def _aion188_path_allowed(relative: str) -> bool:
    return relative in AION188_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION188_ALLOWED_PREFIXES
    )


def _aion189_path_allowed(relative: str) -> bool:
    return relative in AION189_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION189_ALLOWED_PREFIXES
    )


def _aion190_path_allowed(relative: str) -> bool:
    return relative in AION190_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION190_ALLOWED_PREFIXES
    )


def _aion191_path_allowed(relative: str) -> bool:
    return relative in AION191_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION191_ALLOWED_PREFIXES
    )


def _aion192_path_allowed(relative: str) -> bool:
    return relative in AION192_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION192_ALLOWED_PREFIXES
    )


def _aion193_path_allowed(relative: str) -> bool:
    return relative in AION193_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION193_ALLOWED_PREFIXES
    )


def _aion194_path_allowed(relative: str) -> bool:
    return relative in AION194_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION194_ALLOWED_PREFIXES
    )


def _aion195_path_allowed(relative: str) -> bool:
    return relative in AION195_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION195_ALLOWED_PREFIXES
    )


def _aion196_path_allowed(relative: str) -> bool:
    return relative in AION196_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION196_ALLOWED_PREFIXES
    )


def _aion197_path_allowed(relative: str) -> bool:
    return relative in AION197_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION197_ALLOWED_PREFIXES
    )


def _aion186_implementation_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return _find_optional_record(program["records"], "implementation_task", AION186_TASK_ID) is not None


def _aion187_closeout_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return (
        _find_optional_evaluation_record(
            program["records"],
            AION187_TASK_ID,
            AION187_EVALUATION_ID,
        )
        is not None
    )


def _aion189_closeout_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return (
        _find_optional_evaluation_record(
            program["records"],
            AION189_TASK_ID,
            AION189_EVALUATION_ID,
        )
        is not None
    )


def _aion191_closeout_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return (
        _find_optional_evaluation_record(
            program["records"],
            AION191_TASK_ID,
            AION191_EVALUATION_ID,
        )
        is not None
    )


def _aion188_implementation_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return _find_optional_record(program["records"], "implementation_task", AION188_TASK_ID) is not None


def _aion190_implementation_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return _find_optional_record(program["records"], "implementation_task", AION190_TASK_ID) is not None


def _aion192_implementation_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return _find_optional_record(program["records"], "implementation_task", AION192_TASK_ID) is not None


def _aion194_implementation_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return _find_optional_record(program["records"], "implementation_task", AION194_TASK_ID) is not None


def _aion196_implementation_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return _find_optional_record(program["records"], "implementation_task", AION196_TASK_ID) is not None


def _aion193_closeout_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return (
        _find_optional_evaluation_record(
            program["records"],
            AION193_TASK_ID,
            AION193_EVALUATION_ID,
        )
        is not None
    )


def _aion195_closeout_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return (
        _find_optional_evaluation_record(
            program["records"],
            AION195_TASK_ID,
            AION195_EVALUATION_ID,
        )
        is not None
    )


def _aion197_closeout_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return (
        _find_optional_evaluation_record(
            program["records"],
            AION197_TASK_ID,
            AION197_EVALUATION_ID,
        )
        is not None
    )


def _comparison_base(root: Path) -> str | None:
    candidates = ("origin/main", "main")
    for candidate in candidates:
        if _git_ref_exists(root, candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    if _git_ref_exists(root, "HEAD~1"):
        return "HEAD~1"
    return None


def _changed_files(root: Path) -> set[str]:
    base = _comparison_base(root)
    changed: set[str] = set()
    if base is not None:
        diff = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD", "--"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        changed.update(line.strip() for line in diff.stdout.splitlines() if line.strip())
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    changed.update(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--mode",
        choices=(
            "authorization",
            "no-go",
            "persistent-state",
            "persistent-state-no-go",
            "persistent-state-closeout",
            "persistent-state-closeout-no-go",
            "world-model",
            "world-model-no-go",
            "world-model-closeout",
            "world-model-closeout-no-go",
            "global-workspace",
            "global-workspace-no-go",
            "workspace-closeout",
            "workspace-closeout-no-go",
            "memory-consolidation",
            "memory-consolidation-no-go",
            "memory-consolidation-closeout",
            "memory-consolidation-closeout-no-go",
            "counterfactual-planning",
            "counterfactual-planning-no-go",
            "counterfactual-planning-closeout",
            "counterfactual-planning-closeout-no-go",
            "information-acquisition",
            "information-acquisition-no-go",
            "information-acquisition-closeout",
            "information-acquisition-closeout-no-go",
            "continual-learning",
            "continual-learning-no-go",
            "integrated-evaluation",
            "integrated-evaluation-no-go",
        ),
        default="authorization",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.mode == "authorization":
        validate_repo(root)
        print("cognitive architecture authorization validation PASS")
    elif args.mode == "no-go":
        validate_no_go(root)
        print("cognitive architecture no-go validation PASS")
    elif args.mode == "persistent-state":
        validate_persistent_state(root)
        print("cognitive persistent-state validation PASS")
    elif args.mode == "persistent-state-no-go":
        validate_persistent_state_no_go(root)
        print("cognitive persistent-state no-go validation PASS")
    elif args.mode == "persistent-state-closeout":
        validate_persistent_state_closeout(root)
        print("cognitive persistent-state closeout validation PASS")
    elif args.mode == "persistent-state-closeout-no-go":
        validate_persistent_state_closeout_no_go(root)
        print("cognitive persistent-state closeout no-go validation PASS")
    elif args.mode == "world-model":
        validate_world_model(root)
        print("cognitive world-model validation PASS")
    elif args.mode == "world-model-no-go":
        validate_world_model_no_go(root)
        print("cognitive world-model no-go validation PASS")
    elif args.mode == "world-model-closeout":
        validate_world_model_closeout(root)
        print("cognitive world-model closeout validation PASS")
    elif args.mode == "world-model-closeout-no-go":
        validate_world_model_closeout_no_go(root)
        print("cognitive world-model closeout no-go validation PASS")
    elif args.mode == "global-workspace":
        validate_global_workspace(root)
        print("cognitive global-workspace validation PASS")
    elif args.mode == "global-workspace-no-go":
        validate_global_workspace_no_go(root)
        print("cognitive global-workspace no-go validation PASS")
    elif args.mode == "workspace-closeout":
        validate_workspace_closeout(root)
        print("cognitive workspace closeout validation PASS")
    elif args.mode == "workspace-closeout-no-go":
        validate_workspace_closeout_no_go(root)
        print("cognitive workspace closeout no-go validation PASS")
    elif args.mode == "memory-consolidation":
        validate_memory_consolidation(root)
        print("cognitive memory-consolidation validation PASS")
    elif args.mode == "memory-consolidation-no-go":
        validate_memory_consolidation_no_go(root)
        print("cognitive memory-consolidation no-go validation PASS")
    elif args.mode == "memory-consolidation-closeout":
        validate_memory_consolidation_closeout(root)
        print("cognitive memory-consolidation closeout validation PASS")
    elif args.mode == "memory-consolidation-closeout-no-go":
        validate_memory_consolidation_closeout_no_go(root)
        print("cognitive memory-consolidation closeout no-go validation PASS")
    elif args.mode == "counterfactual-planning":
        validate_counterfactual_planning(root)
        print("cognitive counterfactual-planning validation PASS")
    elif args.mode == "counterfactual-planning-no-go":
        validate_counterfactual_planning_no_go(root)
        print("cognitive counterfactual-planning no-go validation PASS")
    elif args.mode == "counterfactual-planning-closeout":
        validate_counterfactual_planning_closeout(root)
        print("cognitive counterfactual-planning closeout validation PASS")
    elif args.mode == "counterfactual-planning-closeout-no-go":
        validate_counterfactual_planning_closeout_no_go(root)
        print("cognitive counterfactual-planning closeout no-go validation PASS")
    elif args.mode == "information-acquisition":
        validate_information_acquisition(root)
        print("cognitive information-acquisition validation PASS")
    elif args.mode == "information-acquisition-no-go":
        validate_information_acquisition_no_go(root)
        print("cognitive information-acquisition no-go validation PASS")
    elif args.mode == "information-acquisition-closeout":
        validate_information_acquisition_closeout(root)
        print("cognitive information-acquisition closeout validation PASS")
    elif args.mode == "information-acquisition-closeout-no-go":
        validate_information_acquisition_closeout_no_go(root)
        print("cognitive information-acquisition closeout no-go validation PASS")
    elif args.mode == "continual-learning":
        validate_continual_learning(root)
        print("cognitive continual-learning validation PASS")
    elif args.mode == "continual-learning-no-go":
        validate_continual_learning_no_go(root)
        print("cognitive continual-learning no-go validation PASS")
    elif args.mode == "integrated-evaluation":
        validate_integrated_evaluation(root)
        print("cognitive integrated evaluation validation PASS")
    else:
        validate_integrated_evaluation_no_go(root)
        print("cognitive integrated evaluation no-go validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    validate_local_persistence_authorization,
)
from test_governed_learning_memory_program_authorization import REPO_ROOT


def test_local_persistence_authorization_validator_passes() -> None:
    validate_local_persistence_authorization(REPO_ROOT)

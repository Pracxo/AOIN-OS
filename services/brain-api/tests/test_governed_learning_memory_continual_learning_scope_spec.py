from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_aion228_source_scope_is_recorded_and_exactly_implemented() -> None:
    auth = auth227.load_json(
        "examples/governed-learning-memory/continual-learning-pilot-authorization.json",
        REPO_ROOT,
    )
    assert tuple(auth["future_authorized_source_scope"][:-1]) == auth227.FUTURE_AION228_SOURCE_SCOPE
    for relative in auth227.FUTURE_AION228_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).exists()
    assert (REPO_ROOT / auth227.AION228_UNINSTALLED_OPERATOR_RUNNER).exists()
